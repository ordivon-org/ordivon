"""Migration-only Python <-> Rust Work compatibility oracle.

Use only with a *disposable loopback* PostgreSQL 18 database prepared by the
explicitly selected Host Alembic schema13 (historical) or schema17 (current)
fixture. This does not change Rust service admission.

First run work_pg --ignored --test-threads=1 against the disposable fixture
to create the Rust writer samples. Then seed the Python oracle on the same DB,
run work_python_parity --ignored with HOST_RUST_PYTHON_ORACLE_PATH pointing to
the saved JSON, and finally run this script with 'verify'. No fixture writes
may intervene between Python oracle capture and the Rust comparison:
they would change the list cursor/hasMore observations.
Set HOST_RUST_TEST_SCHEMA=17 for the current schema17 Python profile;
the default remains the historical schema13 profile.

The script is explicitly a temporary *old implementation oracle*, not a new
Host production dependency or a second database authority.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import psycopg

from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkSnapshotInput,
    WorkState,
)
from ordivon_host_v2.work_store import WorkStore

ACTOR = "actor:test:python-rust-parity"
WORK = "work:test:python:rust-parity"


def _dsn() -> str:
    dsn = os.environ.get("HOST_RUST_TEST_DSN", "")
    parsed = urlsplit(dsn)
    if (
        parsed.scheme != "postgresql"
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or not parsed.port
        or parsed.path in {"", "/", "/ordivon", "/ordivon_host"}
    ):
        raise RuntimeError("Python/Rust oracle requires explicit disposable loopback PG DSN")
    with psycopg.connect(dsn) as conn:
        version = int(conn.execute("SHOW server_version_num").fetchone()[0])
        if version // 10000 != 18:
            raise RuntimeError("Python/Rust oracle requires PostgreSQL 18")
        schema = conn.execute(
            "SELECT schema_version FROM host_v2_schema WHERE singleton"
        ).fetchone()
        expected_schema = os.environ.get("HOST_RUST_TEST_SCHEMA", "13")
        if expected_schema not in {"13", "17"}:
            raise RuntimeError("unsupported Python/Rust fixture schema")
        if schema is None or schema[0] != int(expected_schema):
            raise RuntimeError("Python/Rust oracle fixture schema differs from explicit expected schema")
    return dsn


def _first_snapshot() -> WorkSnapshotInput:
    return WorkSnapshotInput(
        objective="跨语言 Work 语义",
        frontier="Python 首次提交",
        established=["Python 源校验"],
        nextActions=["审查 Rust Work"],
    )


def _second_snapshot() -> WorkSnapshotInput:
    return WorkSnapshotInput(
        objective="跨语言 Work 语义",
        frontier="Python 第二修订",
        established=["Python 源校验", "事务 CAS"],
        nextActions=["审查 Rust Work"],
    )


def seed(dsn: str, path: Path) -> None:
    store = WorkStore(dsn)
    if os.environ.get("HOST_RUST_TEST_SCHEMA", "13") == "17":
        from ordivon_host_v2.references.actor_store import ActorReferenceStore

        actor_store = ActorReferenceStore(dsn)
    else:
        actor_store = store
    actor_store.declare_actor(
        ActorRefInput(actor_ref=ACTOR, actor_kind=ActorKind.AGENT),
        client_request_id="request:test:python:declare-parity",
    )
    created = store.create_work(
        WorkCreateInput(
            work_ref=WORK,
            kind="python-rust-wire",
            actor_ref=ACTOR,
            initial_snapshot=_first_snapshot(),
        ),
        client_request_id="request:test:python:create-parity",
    )
    committed = store.commit_snapshot(
        WORK,
        expected_revision=1,
        snapshot=_second_snapshot(),
        actor_ref=ACTOR,
        state=WorkState.COMPLETED,
        client_request_id="request:test:python:commit-parity",
    )
    # Force a stable, future ranking so concurrent independent test fixtures
    # cannot replace this Work as the first completed page item.
    with psycopg.connect(dsn) as conn:
        conn.execute(
            "UPDATE works SET updated_at=%s::timestamptz WHERE work_ref=%s",
            ("2099-03-01T05:06:07+00:00", WORK),
        )
    output = {
        "create": created,
        "commit": committed,
        "current": store.get_work(WORK),
        "revisionOne": store.get_work(WORK, revision=1),
        "list": store.list_works(state="completed", limit=1),
    }
    path.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print("PYTHON_ORACLE_CREATED")


def verify(dsn: str) -> None:
    store = WorkStore(dsn)
    current = store.get_work("work:test:rust:cas-sequential")
    assert current["state"] == "completed"
    assert current["revision"] == 2
    assert current["snapshot"]["frontier"] == "revision-two"
    result = store.create_work(
        WorkCreateInput(
            work_ref="work:test:rust:create-replay",
            kind="rust-migration-test",
            actor_ref="actor:test:rust-migration",
            initial_snapshot=WorkSnapshotInput(
                objective="Rust Host CAS integration",
                frontier="create-first",
                established=["已验证的事实 🌍"],
                nextActions=["检查提交回执"],
            ),
        ),
        client_request_id="request:test:python:read-rust",
    )
    assert result["admission"] == "existing"
    print("PYTHON_READ_RUST_WRITER_OK")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in {"seed", "verify"}:
        raise SystemExit("usage: python_oracle.py seed <oracle.json> | verify")
    dsn = _dsn()
    if sys.argv[1] == "seed":
        if len(sys.argv) != 3:
            raise SystemExit("seed needs one output JSON pathname")
        seed(dsn, Path(sys.argv[2]))
    else:
        if len(sys.argv) != 2:
            raise SystemExit("verify takes no additional arguments")
        verify(dsn)


if __name__ == "__main__":
    main()
