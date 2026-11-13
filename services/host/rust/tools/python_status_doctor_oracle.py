"""Isolated Python Host Doctor oracle for Rust status(summary/integrity/history).

Seed deliberate historical corruption *only* inside the temporary PG18 database
created by Host's native integration harness. CURRENT health is independent of missing revisions and corrupted retained
noncurrent history; optional history scans still report corrupt retained bytes.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import psycopg

from ordivon_host_v2.service import HostV2
from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkSnapshotInput,
)
from ordivon_host_v2.work_store import WorkStore

ACTOR = "actor:test:rust-doctor-r5"
GAP = "work:test:rust-doctor-r5-gap"
CORRUPT = "work:test:rust-doctor-r5-digest"


def check_disposable() -> str:
    dsn = os.environ.get("HOST_RUST_TEST_DSN", "")
    parsed = urlsplit(dsn)
    if (
        not dsn
        or dsn != os.environ.get("ORDIVON_HOST_V2_DSN")
        or parsed.scheme != "postgresql"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or not parsed.port
        or parsed.path != "/host_rust_r2"
    ):
        raise RuntimeError("REFUSE_NON_DISPOSABLE_R5_DOCTOR_PG18")
    with psycopg.connect(dsn) as connection:
        version = int(connection.execute("SHOW server_version_num").fetchone()[0])
        schema = connection.execute(
            "SELECT schema_version FROM host_v2_schema WHERE singleton"
        ).fetchone()
        if version // 10000 != 18 or schema != (13,):
            raise RuntimeError("DOCTOR_REQUIRES_POSTGRES18_SCHEMA13")
    return dsn


def check(doctor: dict, mode: str) -> None:
    assert doctor["healthy"] is (mode == "integrity"), doctor
    names = [item["name"] for item in doctor["checks"]]
    assert names == [
        "postgres.schema", "work.current_snapshot", "social.message_topic_space",
        "social.reply_integrity", "attention.cursor_bounds",
        "command_receipts.complete", "work.current_snapshot_payload_digest",
    ] + (["work.snapshot_history_digest"] if mode == "history" else []), names
    observed = {item["name"]: item for item in doctor["checks"]}
    for key in ("work.current_snapshot", "work.current_snapshot_payload_digest"):
        assert observed[key] == {
            "name": key, "status": "ok", "detail": "invalid=0"
        }, observed
    if mode == "history":
        assert observed["work.snapshot_history_digest"] == {
            "name": "work.snapshot_history_digest", "status": "error", "detail": "invalid=1"
        }, observed


def seed(dsn: str, output: Path) -> None:
    store = WorkStore(dsn)
    store.declare_actor(
        ActorRefInput(actor_ref=ACTOR, actor_kind=ActorKind.AGENT),
        client_request_id="request:test:rust-doctor-r5-actor",
    )
    for work_ref, kind in ((GAP, "history-gap"), (CORRUPT, "digest-corruption")):
        store.create_work(
            WorkCreateInput(
                work_ref=work_ref,
                kind=kind,
                actor_ref=ACTOR,
                initial_snapshot=WorkSnapshotInput(
                    objective="Historical Doctor Rust/Python parity", frontier="revision-one"
                ),
            ),
            client_request_id=f"request:test:rust-doctor-create:{kind}",
        )
        store.commit_snapshot(
            work_ref,
            expected_revision=1,
            snapshot=WorkSnapshotInput(
                objective="Historical Doctor Rust/Python parity", frontier="revision-two"
            ),
            actor_ref=ACTOR,
            client_request_id=f"request:test:rust-doctor-commit:{kind}",
        )
    # Do not fabricate a repair for revision-one history. Deliberately retain
    # current revision-two so current pointers are still valid.
    with psycopg.connect(dsn) as connection:
        connection.execute(
            "DELETE FROM work_snapshots WHERE work_ref=%s AND revision=1", (GAP,)
        )
        connection.execute(
            "UPDATE work_snapshots SET snapshot_digest=%s "
            "WHERE work_ref=%s AND revision=1",
            ("sha256:" + "0" * 64, CORRUPT),
        )
    for ref in (GAP, CORRUPT):
        assert store.get_work(ref)["revision"] == 2
    source = HostV2(dsn)
    expected = {
        mode: {key: value for key, value in source.status(mode).items()
               if key != "observedAtMs"}
        for mode in ("summary", "integrity", "history")
    }
    assert expected["summary"]["doctor"] is None
    check(expected["integrity"]["doctor"], "integrity")
    check(expected["history"]["doctor"], "history")
    output.write_text(
        json.dumps(expected, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("PYTHON_DOCTOR_ORACLE_CURRENT_ONLY_SEED_PASS current=OK gap=OPTIONAL retained_digest=1")


def verify(dsn: str) -> None:
    host = HostV2(dsn)
    for mode in ("integrity", "history"):
        observed = host.status(mode)
        check(observed["doctor"], mode)
    print("PYTHON_DOCTOR_ORACLE_CURRENT_ONLY_VERIFY_PASS current=OK gap=OPTIONAL retained_digest=1")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"seed", "verify"}:
        raise SystemExit("usage: python_status_doctor_oracle.py seed PATH | verify")
    dsn = check_disposable()
    if sys.argv[1] == "seed" and len(sys.argv) == 3:
        seed(dsn, Path(sys.argv[2]))
    elif sys.argv[1] == "verify" and len(sys.argv) == 2:
        verify(dsn)
    else:
        raise SystemExit("invalid argument count")


if __name__ == "__main__":
    main()
