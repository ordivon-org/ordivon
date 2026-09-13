#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from ordivon_host_v2.board import board_message_digest
from ordivon_host_v2.canonical import canonical_digest
from ordivon_host_v2.news import news_edition_digest

BUNDLE_VERSION = 1
EXTERNAL_CONTINUITY = "ordivon.host.external-continuity.v1"
STATE_MAP = {"ready": "open", "completed": "completed", "cancelled": "abandoned"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _object(objects: Path, digest: str) -> dict[str, Any]:
    if not digest.startswith("sha256:"):
        raise ValueError(f"invalid object digest: {digest}")
    path = objects / f"{digest.removeprefix('sha256:')}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    if canonical_digest(raw) != digest:
        raise ValueError(f"CAS object digest mismatch: {digest}")
    if not isinstance(raw, dict) or "payload" not in raw:
        raise ValueError(f"invalid CAS envelope: {digest}")
    return raw


def _write_record(handle: Any, record: dict[str, Any]) -> None:
    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    handle.write("\n")


def export_bundle(db: Path, objects: Path, out: Path) -> dict[str, Any]:
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    records = out / "records.ndjson"
    con = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    con.row_factory = sqlite3.Row

    extension_count = int(con.execute("SELECT count(*) FROM task_extension_state").fetchone()[0])
    if extension_count:
        raise ValueError(
            "v1 extension state exists; migration requires an explicit extension-history policy"
        )

    counts: dict[str, int] = defaultdict(int)
    task_ids: list[str] = []
    with records.open("w", encoding="utf-8", newline="\n") as handle:
        created_rows = con.execute(
            "SELECT stream_id,payload_digest FROM events WHERE stream_revision=1 "
            "AND event_kind='task.created' ORDER BY stream_id"
        ).fetchall()
        for created in created_rows:
            env = _object(objects, created["payload_digest"])["payload"]
            descriptor_digest = env["data"]["descriptorObjectDigest"]
            descriptor = _object(objects, descriptor_digest)["payload"]
            if descriptor.get("workloadId") != EXTERNAL_CONTINUITY:
                raise ValueError(
                    f"unsupported v1 workload for {created['stream_id']}: {descriptor.get('workloadId')}"
                )
            task_ids.append(created["stream_id"])

        legacy_seed_omitted = 0
        for task_id in task_ids:
            recoverable: list[tuple[sqlite3.Row, dict[str, Any], dict[str, Any]]] = []
            for event in con.execute(
                "SELECT event_id,stream_revision,event_kind,payload_digest,recorded_at_ms "
                "FROM events WHERE stream_id=? ORDER BY stream_revision",
                (task_id,),
            ):
                envelope = _object(objects, event["payload_digest"])["payload"]
                data = envelope["data"]
                if "checkpointObjectDigest" not in data:
                    if int(event["stream_revision"]) != 1:
                        raise ValueError(
                            f"non-adoption v1 revision lacks checkpoint: {task_id}@{event['stream_revision']}"
                        )
                    legacy_seed_omitted += 1
                    continue
                recoverable.append((event, envelope, data))
            if not recoverable:
                raise ValueError(f"Task has no recoverable WorkingCheckpoint: {task_id}")

            for target_revision, (event, envelope, data) in enumerate(recoverable, start=1):
                projection = envelope["projection"]
                cp_object_digest = data["checkpointObjectDigest"]
                cp_envelope = _object(objects, cp_object_digest)
                if cp_envelope.get("kind") != "host-working-checkpoint":
                    raise ValueError(f"unexpected checkpoint object kind: {cp_object_digest}")
                checkpoint = cp_envelope["payload"]
                digest = canonical_digest(checkpoint)
                if digest != data["checkpointDigest"]:
                    raise ValueError(
                        f"checkpoint digest mismatch: {task_id}@{event['stream_revision']}"
                    )
                state = STATE_MAP.get(projection["state"])
                if state is None:
                    raise ValueError(f"unsupported v1 task state: {projection['state']}")
                _write_record(
                    handle,
                    {
                        "recordType": "task_revision",
                        "taskId": task_id,
                        "goalId": projection["goalId"],
                        "revision": target_revision,
                        "sourceRevision": int(event["stream_revision"]),
                        "eventType": "adopt" if target_revision == 1 else "checkpoint",
                        "checkpointDigest": digest,
                        "checkpoint": checkpoint,
                        "writerLabel": data.get("writerLabel"),
                        "resultingState": state,
                        "recordedAtMs": int(event["recorded_at_ms"]),
                        "sourceEventId": event["event_id"],
                        "sourcePayloadDigest": event["payload_digest"],
                    },
                )
                counts["task_revision"] += 1

        for row in con.execute("SELECT * FROM board_messages ORDER BY sequence"):
            envelope = _object(objects, row["message_digest"])
            payload = envelope["payload"]
            value = {
                "clientMessageId": payload["clientMessageId"],
                "authorLabel": payload["authorLabel"],
                "messageKind": payload["messageKind"],
                "topic": payload.get("topic"),
                "message": payload["message"],
                "replyToClientMessageId": payload.get("replyToClientMessageId"),
            }
            if board_message_digest(value) != row["message_digest"]:
                raise ValueError(f"board digest mismatch at sequence {row['sequence']}")
            _write_record(
                handle,
                {
                    "recordType": "board_message",
                    "sequence": int(row["sequence"]),
                    **value,
                    "messageDigest": row["message_digest"],
                    "recordedAtMs": int(row["recorded_at_ms"]),
                },
            )
            counts["board_message"] += 1

        for row in con.execute("SELECT * FROM news_publications ORDER BY sequence"):
            envelope = _object(objects, row["edition_digest"])
            edition = envelope["payload"]
            if news_edition_digest(edition) != row["edition_digest"]:
                raise ValueError(f"news digest mismatch at sequence {row['sequence']}")
            _write_record(
                handle,
                {
                    "recordType": "news_publication",
                    "sequence": int(row["sequence"]),
                    "clientPublishId": row["client_publish_id"],
                    "editionId": row["edition_id"],
                    "editionDate": row["edition_date"],
                    "expectedRevision": int(row["expected_revision"]),
                    "revision": int(row["revision"]),
                    "editionDigest": row["edition_digest"],
                    "edition": edition,
                    "recordedAtMs": int(row["recorded_at_ms"]),
                },
            )
            counts["news_publication"] += 1

    manifest = {
        "schemaVersion": BUNDLE_VERSION,
        "kind": "ordivon.host-v1-semantic-export",
        "sourceDatabaseSha256": _sha256_file(db),
        "recordsSha256": _sha256_file(records),
        "counts": dict(sorted(counts.items())),
        "taskCount": len(task_ids),
        "extensionStateCount": extension_count,
        "legacyDescriptorOnlySeedRevisionsOmitted": legacy_seed_omitted,
        "truthBoundary": (
            "frozen v1 semantic export; no v1 Journal/CAS implementation is migrated. "
            "Descriptor-only adoption seeds without a WorkingCheckpoint are intentionally omitted; "
            "sourceRevision remains recorded per migrated revision."
        ),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def _records(bundle: Path) -> list[dict[str, Any]]:
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    path = bundle / "records.ndjson"
    if _sha256_file(path) != manifest["recordsSha256"]:
        raise ValueError("bundle records digest mismatch")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def import_bundle(bundle: Path, dsn: str) -> dict[str, Any]:
    records = _records(bundle)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["recordType"]].append(record)
    task_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in grouped["task_revision"]:
        task_rows[record["taskId"]].append(record)

    with psycopg.connect(dsn, row_factory=dict_row) as conn, conn.transaction():
        required = conn.execute(
            "SELECT schema_version FROM host_v2_schema WHERE singleton"
        ).fetchone()
        if required is None or int(required["schema_version"]) != 3:
            raise ValueError("target is not an initialized Host v2 schemaVersion 3 database")
        occupied = {}
        for table in (
            "tasks",
            "checkpoints",
            "task_events",
            "board_messages",
            "news_publications",
            "extension_states",
            "extension_history",
            "activity_log",
            "command_receipts",
        ):
            occupied[table] = int(
                conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
            )
        if any(occupied.values()):
            raise ValueError(f"target Host v2 database is not empty: {occupied}")

        task_params: list[tuple[Any, ...]] = []
        checkpoint_params: list[tuple[Any, ...]] = []
        event_params: list[tuple[Any, ...]] = []
        for task_id, history in sorted(task_rows.items()):
            history.sort(key=lambda r: int(r["revision"]))
            revisions = [int(r["revision"]) for r in history]
            if revisions != list(range(1, len(history) + 1)):
                raise ValueError(f"non-contiguous source Task history: {task_id}")
            first, last = history[0], history[-1]
            task_params.append(
                (
                    task_id,
                    last["goalId"],
                    last["revision"],
                    last["resultingState"],
                    last["checkpointDigest"],
                    _dt(first["recordedAtMs"]),
                    _dt(last["recordedAtMs"]),
                )
            )
            for record in history:
                checkpoint_params.append(
                    (
                        task_id,
                        record["revision"],
                        record["checkpointDigest"],
                        json.dumps(record["checkpoint"], ensure_ascii=False, separators=(",", ":")),
                        record.get("writerLabel"),
                        _dt(record["recordedAtMs"]),
                    )
                )
                request_digest = canonical_digest(
                    {
                        "migration": "ordivon.host-v1-semantic-export.v1",
                        "sourceEventId": record["sourceEventId"],
                        "sourcePayloadDigest": record["sourcePayloadDigest"],
                    }
                )
                event_params.append(
                    (
                        task_id,
                        record["revision"],
                        record["eventType"],
                        request_digest,
                        record["checkpointDigest"],
                        record["resultingState"],
                        _dt(record["recordedAtMs"]),
                    )
                )

        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO tasks(task_id,goal_id,revision,state,current_checkpoint_digest,created_at,updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                task_params,
            )
            cur.executemany(
                "INSERT INTO checkpoints(task_id,revision,checkpoint_digest,payload,writer_label,created_at) "
                "VALUES (%s,%s,%s,%s::jsonb,%s,%s)",
                checkpoint_params,
            )
            cur.executemany(
                "INSERT INTO task_events(task_id,revision,event_type,request_digest,checkpoint_digest,resulting_state,created_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                event_params,
            )

            board_params = [
                (
                    record["sequence"],
                    record["clientMessageId"],
                    record["authorLabel"],
                    record["messageKind"],
                    record.get("topic"),
                    record["message"],
                    record.get("replyToClientMessageId"),
                    record["messageDigest"],
                    record["recordedAtMs"],
                    _dt(record["recordedAtMs"]),
                )
                for record in grouped["board_message"]
            ]
            cur.executemany(
                "INSERT INTO board_messages(sequence,client_message_id,author_label,message_kind,topic,message,"
                "reply_to_client_message_id,message_digest,recorded_at_ms,created_at) OVERRIDING SYSTEM VALUE "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                board_params,
            )

            news_params = [
                (
                    record["sequence"],
                    record["clientPublishId"],
                    record["editionId"],
                    record["editionDate"],
                    record["expectedRevision"],
                    record["revision"],
                    record["editionDigest"],
                    json.dumps(record["edition"], ensure_ascii=False, separators=(",", ":")),
                    record["recordedAtMs"],
                    _dt(record["recordedAtMs"]),
                )
                for record in grouped["news_publication"]
            ]
            cur.executemany(
                "INSERT INTO news_publications(sequence,client_publish_id,edition_id,edition_date,expected_revision,revision,"
                "edition_digest,edition,recorded_at_ms,created_at) OVERRIDING SYSTEM VALUE "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)",
                news_params,
            )

        if grouped["board_message"]:
            conn.execute(
                "SELECT setval(pg_get_serial_sequence('board_messages','sequence'), "
                "(SELECT max(sequence) FROM board_messages), true)"
            )
        if grouped["news_publication"]:
            conn.execute(
                "SELECT setval(pg_get_serial_sequence('news_publications','sequence'), "
                "(SELECT max(sequence) FROM news_publications), true)"
            )

    return verify_bundle(bundle, dsn)


def verify_bundle(bundle: Path, dsn: str) -> dict[str, Any]:
    records = _records(bundle)
    expected: dict[str, int] = defaultdict(int)
    task_latest: dict[str, dict[str, Any]] = {}
    for record in records:
        expected[record["recordType"]] += 1
        if record["recordType"] == "task_revision":
            task_latest[record["taskId"]] = record

    failures: list[str] = []
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        counts = {
            "task_revision": int(
                conn.execute("SELECT count(*) AS n FROM task_events").fetchone()["n"]
            ),
            "board_message": int(
                conn.execute("SELECT count(*) AS n FROM board_messages").fetchone()["n"]
            ),
            "news_publication": int(
                conn.execute("SELECT count(*) AS n FROM news_publications").fetchone()["n"]
            ),
        }
        for key, value in expected.items():
            if counts.get(key) != value:
                failures.append(f"count:{key}:expected={value}:observed={counts.get(key)}")
        observed_tasks = int(conn.execute("SELECT count(*) AS n FROM tasks").fetchone()["n"])
        if observed_tasks != len(task_latest):
            failures.append(f"task_count:expected={len(task_latest)}:observed={observed_tasks}")

        for task_id, expected_task in task_latest.items():
            row = conn.execute(
                "SELECT goal_id,revision,state,current_checkpoint_digest FROM tasks WHERE task_id=%s",
                (task_id,),
            ).fetchone()
            if row is None:
                failures.append(f"missing_task:{task_id}")
                continue
            actual = (
                row["goal_id"],
                int(row["revision"]),
                row["state"],
                row["current_checkpoint_digest"],
            )
            wanted = (
                expected_task["goalId"],
                int(expected_task["revision"]),
                expected_task["resultingState"],
                expected_task["checkpointDigest"],
            )
            if actual != wanted:
                failures.append(f"task_head:{task_id}")

        bad_checkpoints = 0
        for row in conn.execute("SELECT checkpoint_digest,payload FROM checkpoints"):
            payload = row["payload"]
            if canonical_digest(payload) != row["checkpoint_digest"]:
                bad_checkpoints += 1
        if bad_checkpoints:
            failures.append(f"checkpoint_digest:{bad_checkpoints}")

        bad_board = 0
        for row in conn.execute("SELECT * FROM board_messages"):
            value = {
                "clientMessageId": row["client_message_id"],
                "authorLabel": row["author_label"],
                "messageKind": row["message_kind"],
                "topic": row["topic"],
                "message": row["message"],
                "replyToClientMessageId": row["reply_to_client_message_id"],
            }
            if board_message_digest(value) != row["message_digest"]:
                bad_board += 1
        if bad_board:
            failures.append(f"board_digest:{bad_board}")

        bad_news = 0
        for row in conn.execute("SELECT edition_digest,edition FROM news_publications"):
            if news_edition_digest(row["edition"]) != row["edition_digest"]:
                bad_news += 1
        if bad_news:
            failures.append(f"news_digest:{bad_news}")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.host-v1-to-v2-semantic-equivalence",
        "passed": not failures,
        "expectedCounts": dict(sorted(expected.items())),
        "observedCounts": counts,
        "taskCount": len(task_latest),
        "failures": failures,
    }
    if failures:
        raise RuntimeError(json.dumps(result, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--db", type=Path, required=True)
    export.add_argument("--objects", type=Path, required=True)
    export.add_argument("--out", type=Path, required=True)
    imp = sub.add_parser("import")
    imp.add_argument("--bundle", type=Path, required=True)
    imp.add_argument("--dsn", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--bundle", type=Path, required=True)
    verify.add_argument("--dsn", required=True)
    args = parser.parse_args()
    if args.command == "export":
        result = export_bundle(args.db, args.objects, args.out)
    elif args.command == "import":
        result = import_bundle(args.bundle, args.dsn)
    else:
        result = verify_bundle(args.bundle, args.dsn)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
