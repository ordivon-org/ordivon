"""Bounded Attention change projection in one caller-owned PostgreSQL snapshot."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

import psycopg

from .attention_sql import ATTENTION_DELTA_SQL
from .collection_pagination import DEFAULT_COLLECTION_MAX_BYTES, bounded_prefix, validate_max_bytes
from .errors import ConflictError
from .postgres_bounds import HOST_WIRE_INT_MAX
from .references.actor_refs import ActorReferenceLookup


class AttentionDeltaQueries:
    """Single-snapshot cursor and delta reads; never semantic acceptance."""

    def __init__(
        self,
        connect: Callable[[], AbstractContextManager[psycopg.Connection[dict[str, Any]]]],
    ) -> None:
        self._connect = connect

    def get(
        self,
        actor_ref: str,
        *,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        self._validate_delta_page(limit=limit, max_bytes=max_bytes)
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            ActorReferenceLookup._require_actor(conn, actor_ref)
            row = conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s", (actor_ref,)
            ).fetchone()
            cursor = 0 if row is None else int(row["cursor"])
            return self._delta_in_tx(
                conn, actor_ref, after_sequence=cursor, limit=limit, max_bytes=max_bytes
            )

    @staticmethod
    def _validate_delta_page(*, limit: int, max_bytes: int) -> None:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)

    def delta(
        self,
        actor_ref: str,
        *,
        after_sequence: int,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(after_sequence) is not int or not 0 <= after_sequence <= HOST_WIRE_INT_MAX:
            raise ValueError(
                "after_sequence must be non-negative integer within JSON safe integer range"
            )
        self._validate_delta_page(limit=limit, max_bytes=max_bytes)
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            ActorReferenceLookup._require_actor(conn, actor_ref)
            return self._delta_in_tx(
                conn, actor_ref, after_sequence=after_sequence, limit=limit, max_bytes=max_bytes
            )

    def _delta_in_tx(
        self,
        conn: psycopg.Connection[dict[str, Any]],
        actor_ref: str,
        *,
        after_sequence: int,
        limit: int,
        max_bytes: int,
    ) -> dict[str, Any]:
        """Exact delta projection under the caller's one repeatable-read snapshot."""
        high = int(
            conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()["value"]
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

        def envelope(last: dict[str, Any]) -> dict[str, Any]:
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-attention-delta-r1",
                "actorRef": actor_ref,
                "afterSequence": after_sequence,
                "snapshotHighSequence": high,
                "hasMore": True,
                "nextAfterSequence": last["changeSequence"],
                "rankingApplied": False,
                "truthBoundary": "rebuildable actor-scoped navigation over owner rows; not inbox truth, priority, assignment, or authority",
            }

        page, byte_more = bounded_prefix(
            candidates, max_bytes=max_bytes, collection_key="events", envelope=envelope
        )
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
