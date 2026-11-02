from __future__ import annotations

from typing import Any, Literal

import psycopg
from psycopg.rows import dict_row

from .attention_queries import ATTENTION_DELTA_SQL
from .canonical_json import canonical_bytes, canonical_digest
from .collection_pagination import DEFAULT_COLLECTION_MAX_BYTES, bounded_prefix, validate_max_bytes
from .command_receipts import claim_command_receipt, record_command_receipt
from .errors import ConflictError
from .social_store import SpaceNotFound, TopicNotFound
from .work_store import ActorRefNotFound, WorkNotFound

TargetKind = Literal["work", "space", "topic"]


class AttentionStore:
    """Actor-scoped navigation compiled directly from owner rows, not a second event bus."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def follow(
        self,
        *,
        actor_ref: str,
        target_kind: TargetKind,
        target_ref: str,
        client_request_id: str,
    ) -> dict[str, Any]:
        # Desired-state command: natural-key membership is the replay contract. A later
        # unfollow must not make a same-payload follow replay an obsolete historical receipt.
        _ = client_request_id
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            self._require_actor(conn, actor_ref)
            self._require_target(conn, target_kind, target_ref)
            row = conn.execute(
                "INSERT INTO subscriptions(actor_ref,target_kind,target_ref) VALUES (%s,%s,%s) "
                "ON CONFLICT DO NOTHING RETURNING actor_ref,target_kind,target_ref,created_at,change_sequence",
                (actor_ref, target_kind, target_ref),
            ).fetchone()
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT actor_ref,target_kind,target_ref,created_at,change_sequence FROM subscriptions "
                    "WHERE actor_ref=%s AND target_kind=%s AND target_ref=%s",
                    (actor_ref, target_kind, target_ref),
                ).fetchone()
                if row is None:
                    raise RuntimeError("subscription disappeared")
                admission = "existing"
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-subscription",
                "admission": admission,
                "actorRef": row["actor_ref"],
                "targetKind": row["target_kind"],
                "targetRef": row["target_ref"],
                "createdAt": row["created_at"].isoformat(),
                "changeSequence": int(row["change_sequence"]),
                "truthBoundary": "attention routing preference only; not assignment, priority, ownership, or authorization",
            }
            return result

    def unfollow(
        self,
        *,
        actor_ref: str,
        target_kind: TargetKind,
        target_ref: str,
        client_request_id: str,
    ) -> dict[str, Any]:
        # Desired-state command; deleting an absent natural key is already replay-safe.
        _ = client_request_id
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            self._require_actor(conn, actor_ref)
            deleted = conn.execute(
                "DELETE FROM subscriptions WHERE actor_ref=%s AND target_kind=%s AND target_ref=%s "
                "RETURNING actor_ref",
                (actor_ref, target_kind, target_ref),
            ).fetchone()
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-subscription-unfollow",
                "admission": "committed" if deleted is not None else "existing",
                "actorRef": actor_ref,
                "targetKind": target_kind,
                "targetRef": target_ref,
                "truthBoundary": "attention routing preference only",
            }
            return result

    def list_subscriptions(
        self,
        actor_ref: str,
        *,
        target_kind: TargetKind | None = None,
        after_target_kind: str | None = None,
        after_target_ref: str | None = None,
        limit: int = 200,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        if (after_target_kind is None) != (after_target_ref is None):
            raise ValueError("after_target_kind and after_target_ref must be supplied together")
        validate_max_bytes(max_bytes)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_actor(conn, actor_ref)
            rows = conn.execute(
                "SELECT target_kind,target_ref,created_at,change_sequence FROM subscriptions "
                "WHERE actor_ref=%s AND (%s::text IS NULL OR target_kind=%s) "
                "AND (%s::text IS NULL OR (target_kind,target_ref)>(%s,%s)) "
                "ORDER BY target_kind,target_ref LIMIT %s",
                (
                    actor_ref,
                    target_kind,
                    target_kind,
                    after_target_kind,
                    after_target_kind,
                    after_target_ref,
                    limit + 1,
                ),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [
                {
                    "targetKind": row["target_kind"],
                    "targetRef": row["target_ref"],
                    "createdAt": row["created_at"].isoformat(),
                    "changeSequence": int(row["change_sequence"]),
                }
                for row in rows[:limit]
            ]

            def envelope(page: list[dict[str, Any]]) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-subscription-list",
                    "actorRef": actor_ref,
                    "subscriptions": page,
                    "hasMore": True,
                    "truncated": True,
                    "nextAfterTargetKind": None if not page else page[-1]["targetKind"],
                    "nextAfterTargetRef": None if not page else page[-1]["targetRef"],
                    "rankingApplied": False,
                    "truthBoundary": "actor attention-routing preferences only; not assignment, priority, ownership, or authorization",
                }

            page, byte_more = bounded_prefix(candidates, max_bytes=max_bytes, envelope=envelope)
            has_more = sql_more or byte_more
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-subscription-list",
                "actorRef": actor_ref,
                "subscriptions": page,
                "hasMore": has_more,
                "truncated": has_more,
                "nextAfterTargetKind": page[-1]["targetKind"] if has_more and page else None,
                "nextAfterTargetRef": page[-1]["targetRef"] if has_more and page else None,
                "rankingApplied": False,
                "truthBoundary": "actor attention-routing preferences only; not assignment, priority, ownership, or authorization",
            }

    def get(
        self,
        actor_ref: str,
        *,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_actor(conn, actor_ref)
            row = conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s", (actor_ref,)
            ).fetchone()
            cursor = 0 if row is None else int(row["cursor"])
        return self.delta(actor_ref, after_sequence=cursor, limit=limit, max_bytes=max_bytes)

    def delta(
        self,
        actor_ref: str,
        *,
        after_sequence: int,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(after_sequence) is not int or after_sequence < 0:
            raise ValueError("after_sequence must be non-negative integer")
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_actor(conn, actor_ref)
            high = int(
                conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[
                    "value"
                ]
            )
            if after_sequence > high:
                raise ConflictError("after_sequence cannot exceed current change horizon")
            if after_sequence == high:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-attention-delta-r1",
                    "actorRef": actor_ref,
                    "afterSequence": after_sequence,
                    "snapshotHighSequence": high,
                    "events": [],
                    "hasMore": False,
                    "nextAfterSequence": high,
                    "rankingApplied": False,
                    "truthBoundary": "rebuildable actor-scoped navigation over owner rows; not inbox truth, priority, assignment, or authority",
                }
            rows = conn.execute(
                ATTENTION_DELTA_SQL,
                {
                    "actor_ref": actor_ref,
                    "after_sequence": after_sequence,
                    "high": high,
                    "limit": limit + 1,
                },
            ).fetchall()
            sql_more = len(rows) > limit
            reason_columns = (
                ("followed_work", "followed_work"),
                ("followed_space", "followed_space"),
                ("followed_topic", "followed_topic"),
                ("mentioned", "mentioned"),
                ("replied_to_me", "replied_to_me"),
                ("own_participation", "own_participation"),
                ("own_coordination_intent", "own_coordination_intent"),
            )
            candidates = []
            for row in rows[:limit]:
                reasons = sorted(reason for column, reason in reason_columns if bool(row[column]))
                candidates.append(
                    {
                        "changeSequence": int(row["change_sequence"]),
                        "eventKind": row["event_kind"],
                        "sourceRef": row["source_ref"],
                        "contextRef": row["context_ref"],
                        "reasons": reasons,
                        "navigationKind": row["navigation_kind"],
                        "navigationRef": row["navigation_ref"],
                    }
                )

            def envelope(page: list[dict[str, Any]]) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-attention-delta-r1",
                    "actorRef": actor_ref,
                    "afterSequence": after_sequence,
                    "snapshotHighSequence": high,
                    "events": page,
                    "hasMore": True,
                    "nextAfterSequence": after_sequence if not page else page[-1]["changeSequence"],
                    "rankingApplied": False,
                    "truthBoundary": "rebuildable actor-scoped navigation over owner rows; not inbox truth, priority, assignment, or authority",
                }

            page, byte_more = bounded_prefix(candidates, max_bytes=max_bytes, envelope=envelope)
            has_more = sql_more or byte_more
            next_sequence = int(page[-1]["changeSequence"]) if has_more and page else high
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-attention-delta-r1",
                "actorRef": actor_ref,
                "afterSequence": after_sequence,
                "snapshotHighSequence": high,
                "events": page,
                "hasMore": has_more,
                "nextAfterSequence": next_sequence,
                "rankingApplied": False,
                "truthBoundary": "rebuildable actor-scoped navigation over owner rows; not inbox truth, priority, assignment, or authority",
            }

    def reentry(
        self,
        actor_ref: str,
        *,
        after_sequence: int | None = None,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)
        if after_sequence is None:
            with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
                conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                self._require_actor(conn, actor_ref)
                row = conn.execute(
                    "SELECT cursor FROM attention_cursors WHERE actor_ref=%s", (actor_ref,)
                ).fetchone()
                after_sequence = 0 if row is None else int(row["cursor"])
        if type(after_sequence) is not int or after_sequence < 0:
            raise ValueError("after_sequence must be non-negative integer")

        effective_limit = limit
        while True:
            delta = self.delta(
                actor_ref,
                after_sequence=after_sequence,
                limit=effective_limit,
                max_bytes=max_bytes,
            )
            groups: dict[tuple[str, str], dict[str, Any]] = {}
            for event in delta["events"]:
                key = (event["navigationKind"], event["navigationRef"])
                item = groups.get(key)
                if item is None:
                    item = {
                        "navigationKind": key[0],
                        "navigationRef": key[1],
                        "latestChangeSequence": int(event["changeSequence"]),
                        "eventKinds": [],
                        "reasons": [],
                        "eventCount": 0,
                    }
                    groups[key] = item
                item["latestChangeSequence"] = max(
                    int(item["latestChangeSequence"]), int(event["changeSequence"])
                )
                item["eventKinds"] = sorted(set(item["eventKinds"]) | {event["eventKind"]})
                item["reasons"] = sorted(set(item["reasons"]) | set(event["reasons"]))
                item["eventCount"] = int(item["eventCount"]) + 1

            items = list(groups.values())
            topic_refs = [
                str(item["navigationRef"]) for item in items if item["navigationKind"] == "topic"
            ]
            cursors: dict[str, int] = {}
            if topic_refs:
                with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
                    conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                    rows = conn.execute(
                        "SELECT topic_ref,cursor FROM topic_consumption_cursors "
                        "WHERE actor_ref=%s AND topic_ref=ANY(%s)",
                        (actor_ref, topic_refs),
                    ).fetchall()
                    cursors = {row["topic_ref"]: int(row["cursor"]) for row in rows}
            for item in items:
                if item["navigationKind"] == "topic":
                    item["resumeAfterSequence"] = cursors.get(str(item["navigationRef"]), 0)

            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-attention-reentry-r1",
                "actorRef": actor_ref,
                "afterSequence": after_sequence,
                "snapshotHighSequence": delta["snapshotHighSequence"],
                "items": items,
                "rawEventCount": len(delta["events"]),
                "hasMore": delta["hasMore"],
                "nextAfterSequence": delta["nextAfterSequence"],
                "rankingApplied": False,
                "truthBoundary": "rebuildable re-entry navigation only; no score, priority, assignment, scheduling, or foreign truth ownership",
            }
            if len(canonical_bytes(result)) <= max_bytes:
                return result
            if effective_limit == 1:
                raise ValueError("max_bytes cannot fit one re-entry navigation item")
            effective_limit = max(1, effective_limit // 2)

    def ack(self, actor_ref: str, *, cursor: int, client_request_id: str) -> dict[str, Any]:
        if cursor < 0:
            raise ValueError("cursor must be non-negative")
        request = {"operation": "attention.ack", "actorRef": actor_ref, "cursor": cursor}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = claim_command_receipt(conn, client_request_id, "attention.ack", request_digest)
            if replay is not None:
                return replay
            self._require_actor(conn, actor_ref)
            high = int(
                conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[
                    "value"
                ]
            )
            if cursor > high:
                raise ConflictError(
                    "attention cursor cannot acknowledge beyond current change horizon"
                )
            current = conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s FOR UPDATE", (actor_ref,)
            ).fetchone()
            previous = 0 if current is None else int(current["cursor"])
            if cursor < previous:
                raise ConflictError("attention cursor cannot move backwards")
            updated = conn.execute(
                "INSERT INTO attention_cursors(actor_ref,cursor) VALUES (%s,%s) "
                "ON CONFLICT (actor_ref) DO UPDATE "
                "SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp() "
                "WHERE attention_cursors.cursor <= EXCLUDED.cursor "
                "RETURNING cursor",
                (actor_ref, cursor),
            ).fetchone()
            if updated is None:
                raise ConflictError("attention cursor cannot move backwards")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-attention-ack",
                "actorRef": actor_ref,
                "previousCursor": previous,
                "cursor": cursor,
                "truthBoundary": "navigation acknowledgement only; not evidence that message content was semantically accepted",
            }
            record_command_receipt(conn, client_request_id, "attention.ack", request_digest, result)
            return result

    @staticmethod
    def _require_actor(conn: psycopg.Connection[dict[str, Any]], actor_ref: str) -> None:
        if (
            conn.execute("SELECT 1 FROM actor_refs WHERE actor_ref=%s", (actor_ref,)).fetchone()
            is None
        ):
            raise ActorRefNotFound(actor_ref)

    @staticmethod
    def _require_target(
        conn: psycopg.Connection[dict[str, Any]], target_kind: TargetKind, target_ref: str
    ) -> None:
        table = {"work": "works", "space": "spaces", "topic": "topics"}[target_kind]
        column = {"work": "work_ref", "space": "space_ref", "topic": "topic_ref"}[target_kind]
        if (
            conn.execute(f"SELECT 1 FROM {table} WHERE {column}=%s", (target_ref,)).fetchone()
            is None
        ):
            if target_kind == "work":
                raise WorkNotFound(target_ref)
            if target_kind == "space":
                raise SpaceNotFound(target_ref)
            raise TopicNotFound(target_ref)
