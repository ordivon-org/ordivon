from __future__ import annotations

import time
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical import canonical_digest

REQUIRED_SCHEMA_VERSION = 9


class HostV2:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def initialize(self) -> None:
        """Verify that Alembic already initialized the authority schema.

        Schema creation and migration are deliberately not owned by the running Host service.
        Production and tests must run ``alembic upgrade head`` before Host opens authority.
        """
        try:
            with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
                row = conn.execute(
                    "SELECT schema_version FROM host_v2_schema WHERE singleton"
                ).fetchone()
        except psycopg.errors.UndefinedTable as exc:
            raise RuntimeError(
                "Host v2 schema is not initialized; run alembic upgrade head"
            ) from exc
        if row is None or int(row["schema_version"]) != REQUIRED_SCHEMA_VERSION:
            observed = None if row is None else int(row["schema_version"])
            raise RuntimeError(
                f"Host v2 schema is not at required version {REQUIRED_SCHEMA_VERSION} (observed={observed}); "
                "run alembic upgrade head"
            )

    def status(self, detail: str = "summary") -> dict[str, Any]:
        if detail not in {"summary", "integrity", "history"}:
            raise ValueError("detail must be summary, integrity, or history")
        observed_at_ms = time.time_ns() // 1_000_000
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            schema_row = conn.execute(
                "SELECT schema_version FROM host_v2_schema WHERE singleton"
            ).fetchone()
            if schema_row is None:
                raise RuntimeError("Host v2 schema is not initialized")
            schema_version = int(schema_row["schema_version"])

            actor_count = int(
                conn.execute("SELECT count(*) AS value FROM actor_refs").fetchone()["value"]
            )
            work_state_rows = conn.execute(
                "SELECT state,count(*) AS value FROM works GROUP BY state"
            ).fetchall()
            works_by_state = {row["state"]: int(row["value"]) for row in work_state_rows}
            work_count = sum(works_by_state.values())
            snapshot_count = int(
                conn.execute("SELECT count(*) AS value FROM work_snapshots").fetchone()["value"]
            )
            space_count = int(
                conn.execute("SELECT count(*) AS value FROM spaces").fetchone()["value"]
            )
            topic_count = int(
                conn.execute("SELECT count(*) AS value FROM topics").fetchone()["value"]
            )
            message_count = int(
                conn.execute("SELECT count(*) AS value FROM messages").fetchone()["value"]
            )
            subscription_count = int(
                conn.execute("SELECT count(*) AS value FROM subscriptions").fetchone()["value"]
            )
            change_high = int(
                conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[
                    "value"
                ]
            )

            doctor = None
            if detail != "summary":
                checks: list[dict[str, Any]] = []

                def add_check(name: str, ok: bool, detail_value: str) -> None:
                    checks.append(
                        {"name": name, "status": "ok" if ok else "error", "detail": detail_value}
                    )

                add_check(
                    "postgres.schema",
                    schema_version == REQUIRED_SCHEMA_VERSION,
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

                if detail == "history":
                    history_bad = int(
                        conn.execute(
                            "SELECT count(*) AS value FROM ("
                            "SELECT w.work_ref,w.current_revision,count(s.revision) AS snapshots,"
                            "min(s.revision) AS rmin,max(s.revision) AS rmax "
                            "FROM works w LEFT JOIN work_snapshots s USING(work_ref) "
                            "GROUP BY w.work_ref,w.current_revision"
                            ") x WHERE snapshots<>current_revision OR rmin<>1 OR rmax<>current_revision"
                        ).fetchone()["value"]
                    )
                    add_check(
                        "work.snapshot_history_contiguous",
                        history_bad == 0,
                        f"invalidWorks={history_bad}",
                    )
                    digest_bad = 0
                    for row in conn.execute(
                        "SELECT snapshot_digest,payload FROM work_snapshots ORDER BY work_ref,revision"
                    ).fetchall():
                        payload = row["payload"]
                        if (
                            not isinstance(payload, dict)
                            or canonical_digest(payload) != row["snapshot_digest"]
                        ):
                            digest_bad += 1
                    add_check(
                        "work.snapshot_history_digest",
                        digest_bad == 0,
                        f"invalid={digest_bad}",
                    )
                doctor = {
                    "healthy": all(item["status"] == "ok" for item in checks),
                    "checks": checks,
                }

            return {
                "schemaVersion": 3,
                "kind": "ordivon.host-status",
                "observedAtMs": observed_at_ms,
                "detail": detail,
                "authority": {
                    "journalBackend": "postgresql",
                    "journalSchema": schema_version,
                    "actorRefs": actor_count,
                    "works": work_count,
                    "worksByState": works_by_state,
                    "workSnapshots": snapshot_count,
                    "spaces": space_count,
                    "topics": topic_count,
                    "messages": message_count,
                    "subscriptions": subscription_count,
                    "changeHighSequence": change_high,
                },
                "doctor": doctor,
                "truthBoundary": {
                    "host": (
                        "authoritative only for Host Social Work Fabric semantic continuity and "
                        "collaboration records; Runtime, Git, Identity/Security, effect, and domain "
                        "truth are not checked"
                    )
                },
            }
