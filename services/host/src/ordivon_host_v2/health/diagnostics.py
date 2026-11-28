"""Read-only consistency and status projection over existing Host PostgreSQL facts.

This is an observation interface, not Work or Social mutation authority,
a scheduler, a Security policy, or proof of external Runtime/domain completion.
"""

from __future__ import annotations

import time
from typing import Any

import psycopg
from rfc8785 import CanonicalizationError

from ..canonical_json import canonical_digest
from ..errors import InvalidArgumentError
from ..postgres_connections import HostPostgresConnections
from .receipt_roots import count_invalid_work_receipt_roots


def _snapshot_payload_matches(row: dict[str, Any]) -> bool:
    """Invalid persisted canonical content is a diagnostic error, not healthy or a crash."""
    payload = row["payload"]
    if not isinstance(payload, dict):
        return False
    try:
        return canonical_digest(payload) == row["snapshot_digest"]
    except CanonicalizationError:
        return False


def _read_authority(conn: psycopg.Connection[dict[str, Any]]) -> dict[str, Any]:
    """One exact aggregate projection under the caller's read-only MVCC cut."""
    row = conn.execute(
        "SELECT schema_version,"
        "(SELECT count(*) FROM actor_refs) AS actors,"
        "(SELECT COALESCE(jsonb_object_agg(state,n),'{}'::jsonb) "
        "FROM (SELECT state,count(*) AS n FROM works GROUP BY state) w) AS work_states,"
        "(SELECT count(*) FROM work_snapshots) AS snapshots,"
        "(SELECT count(*) FROM spaces) AS spaces,"
        "(SELECT count(*) FROM topics) AS topics,"
        "(SELECT count(*) FROM messages) AS messages,"
        "(SELECT count(*) FROM subscriptions) AS subscriptions,"
        "(SELECT value FROM swf_change_clock WHERE singleton) AS change_high "
        "FROM host_v2_schema WHERE singleton"
    ).fetchone()
    if row is None:
        raise RuntimeError("Host v2 schema is not initialized")
    works_by_state = {state: int(count) for state, count in row["work_states"].items()}
    return {
        "journalBackend": "postgresql",
        "journalSchema": int(row["schema_version"]),
        "actorRefs": int(row["actors"]),
        "works": sum(works_by_state.values()),
        "worksByState": works_by_state,
        "workSnapshots": int(row["snapshots"]),
        "spaces": int(row["spaces"]),
        "topics": int(row["topics"]),
        "messages": int(row["messages"]),
        "subscriptions": int(row["subscriptions"]),
        "changeHighSequence": int(row["change_high"]),
    }


class HostStatusQueries(HostPostgresConnections):
    """Check existing Work, Social and Attention invariants at a consistent cut."""

    required_schema_version: int  # Bound by the serving HostV2 schema-readiness façade.

    def status(self, detail: str = "summary") -> dict[str, Any]:
        if detail not in {"summary", "integrity", "history"}:
            raise InvalidArgumentError("detail must be summary, integrity, or history")
        observed_at_ms = time.time_ns() // 1_000_000
        with self._connect() as conn:
            # Every detail mode is a read-only observation of one native cut.
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            authority = _read_authority(conn)
            schema_version = authority["journalSchema"]
            change_high = authority["changeHighSequence"]

            doctor = None
            if detail != "summary":
                checks: list[dict[str, Any]] = []

                def add_check(name: str, ok: bool, detail_value: str) -> None:
                    checks.append(
                        {"name": name, "status": "ok" if ok else "error", "detail": detail_value}
                    )

                add_check(
                    "postgres.schema",
                    schema_version == self.required_schema_version,
                    str(schema_version),
                )
                current_snapshot_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM works w LEFT JOIN work_snapshots s "
                        "ON s.work_ref=w.work_ref AND s.revision=w.current_revision "
                        "WHERE s.work_ref IS NULL OR s.snapshot_digest<>w.current_snapshot_digest"
                    ).fetchone()["value"]
                )
                add_check(
                    "work.current_snapshot",
                    current_snapshot_bad == 0,
                    f"invalid={current_snapshot_bad}",
                )
                message_topic_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM messages m JOIN topics t USING(topic_ref) "
                        "WHERE m.space_ref<>t.space_ref"
                    ).fetchone()["value"]
                )
                add_check(
                    "social.message_topic_space",
                    message_topic_bad == 0,
                    f"invalid={message_topic_bad}",
                )
                reply_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM message_relations r "
                        "JOIN messages s ON s.message_ref=r.source_message_ref "
                        "LEFT JOIN messages t ON t.message_ref=r.target_ref "
                        "WHERE r.relation='reply_to' AND "
                        "(t.message_ref IS NULL OR s.space_ref<>t.space_ref OR s.topic_ref<>t.topic_ref)"
                    ).fetchone()["value"]
                )
                add_check("social.reply_integrity", reply_bad == 0, f"invalid={reply_bad}")
                cursor_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM attention_cursors WHERE cursor>%s",
                        (change_high,),
                    ).fetchone()["value"]
                )
                add_check(
                    "attention.cursor_bounds",
                    cursor_bad == 0,
                    f"invalid={cursor_bad};high={change_high}",
                )
                receipt_bad = int(
                    conn.execute(
                        "SELECT count(*) AS value FROM command_receipts WHERE response IS NULL"
                    ).fetchone()["value"]
                )
                add_check(
                    "command_receipts.complete",
                    receipt_bad == 0,
                    f"incomplete={receipt_bad}",
                )

                # A Work is healthy when its CURRENT revision and bytes are valid.
                # Unreferenced historical revisions are optional; compact receipt
                # roots are checked separately in history detail.
                current_payload_bad = 0
                with conn.cursor(name="host_current_snapshot_digest_scan") as cursor:
                    cursor.itersize = 128
                    cursor.execute(
                        "SELECT s.snapshot_digest,s.payload FROM works w JOIN work_snapshots s "
                        "ON s.work_ref=w.work_ref AND s.revision=w.current_revision"
                    )
                    for row in cursor:
                        if not _snapshot_payload_matches(row):
                            current_payload_bad += 1
                add_check(
                    "work.current_snapshot_payload_digest",
                    current_payload_bad == 0,
                    f"invalid={current_payload_bad}",
                )
                if detail == "history":
                    # Retained reply edges may predate the strict writer rank.
                    # General references may be cyclic; only replies require
                    # an earlier target. This audit does not rewrite history.
                    rank_bad = int(
                        conn.execute(
                            "SELECT count(*) AS value FROM message_relations r "
                            "JOIN messages s ON s.message_ref=r.source_message_ref "
                            "JOIN messages t ON t.message_ref=r.target_ref "
                            "WHERE r.relation='reply_to' AND t.sequence>=s.sequence"
                        ).fetchone()["value"]
                    )
                    add_check(
                        "social.reply_history_rank",
                        rank_bad == 0,
                        f"invalid={rank_bad}",
                    )
                    digest_bad = 0
                    # Stream history through Psycopg's native server cursor.
                    # A full fetchall() would retain every JSONB payload in RAM.
                    with conn.cursor(name="host_history_digest_scan") as cursor:
                        cursor.itersize = 128
                        cursor.execute("SELECT snapshot_digest,payload FROM work_snapshots")
                        for row in cursor:
                            if not _snapshot_payload_matches(row):
                                digest_bad += 1
                    add_check(
                        "work.snapshot_history_digest",
                        digest_bad == 0,
                        f"invalid={digest_bad}",
                    )
                    # Native typed roots are available only after schema 0017.
                    if schema_version >= 17:
                        root_bad = count_invalid_work_receipt_roots(conn)
                        add_check(
                            "work.receipt_history_roots", root_bad == 0, f"invalid={root_bad}"
                        )
                    else:
                        add_check("work.receipt_history_roots", False, "unavailable=typed roots")
                doctor = {
                    "healthy": all(item["status"] == "ok" for item in checks),
                    "checks": checks,
                }

            return {
                "schemaVersion": 3,
                "kind": "ordivon.host-status",
                "observedAtMs": observed_at_ms,
                "detail": detail,
                "authority": authority,
                "doctor": doctor,
                "truthBoundary": {
                    "host": (
                        "authoritative only for Host Social Work Fabric semantic continuity and "
                        "collaboration records; Runtime, Git, Identity/Security, effect, and domain "
                        "truth are not checked"
                    )
                },
            }
