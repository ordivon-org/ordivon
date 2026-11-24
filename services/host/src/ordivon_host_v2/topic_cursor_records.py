"""Single PostgreSQL authority for Topic-consumption cursor semantics.

The Social command owns transaction/receipts, while Attention re-entry shares
only the read projection under its *existing* REPEATABLE READ snapshot.
No second state, event bus, Actor IAM, or acknowledgement of semantic acceptance.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import psycopg

from .errors import ConflictError
from .postgres_bounds import HOST_WIRE_INT_MAX


def topic_high_sequence_in_tx(
    conn: psycopg.Connection[dict[str, Any]], topic_ref: str
) -> int:
    """Read the committed Topic message horizon in the caller's PG transaction."""
    return int(
        conn.execute(
            "SELECT COALESCE(MAX(sequence),0) AS high FROM messages WHERE topic_ref=%s",
            (topic_ref,),
        ).fetchone()["high"]
    )


def get_topic_cursor_in_tx(
    conn: psycopg.Connection[dict[str, Any]], *, actor_ref: str, topic_ref: str
) -> dict[str, Any]:
    """Return one actor/topic cursor without opening a second PG snapshot."""
    row = conn.execute(
        "SELECT cursor FROM topic_consumption_cursors WHERE actor_ref=%s AND topic_ref=%s",
        (actor_ref, topic_ref),
    ).fetchone()
    high = topic_high_sequence_in_tx(conn, topic_ref)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-topic-cursor",
        "actorRef": actor_ref,
        "topicRef": topic_ref,
        "cursor": 0 if row is None else int(row["cursor"]),
        "topicHighSequence": high,
        "truthBoundary": "topic navigation cursor only; not evidence of semantic acceptance",
    }


def ack_topic_cursor_in_tx(
    conn: psycopg.Connection[dict[str, Any]], *, actor_ref: str, topic_ref: str, cursor: int
) -> dict[str, Any]:
    """Advance exactly one Topic cursor monotonically, in the owner's transaction.

    Caller checks ActorRef and TopicRef before invoking this helper and holds the
    same transaction for durable receipt registration. The unique-key UPSERT and SQL update predicate enforce monotonicity;
    PostgreSQL 18 returns the actual old/new row in that same statement.
    """
    if type(cursor) is not int or not 0 <= cursor <= HOST_WIRE_INT_MAX:
        raise ValueError("cursor must be non-negative within JSON safe integer range")
    high = topic_high_sequence_in_tx(conn, topic_ref)
    if cursor > high:
        raise ConflictError("topic cursor cannot acknowledge beyond current topic horizon")
    # The PG18 UPSERT returns the actual predecessor at its linearization
    # point, including concurrent first inserts; no pre-read is authoritative.
    updated = conn.execute(
        "INSERT INTO topic_consumption_cursors(actor_ref,topic_ref,cursor) VALUES (%s,%s,%s) "
        "ON CONFLICT (actor_ref,topic_ref) DO UPDATE "
        "SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp() "
        "WHERE topic_consumption_cursors.cursor<=EXCLUDED.cursor "
        "RETURNING COALESCE(OLD.cursor,0) AS previous_cursor, NEW.cursor AS cursor",
        (actor_ref, topic_ref, cursor),
    ).fetchone()
    if updated is None:
        raise ConflictError("topic cursor cannot move backwards")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-topic-cursor-ack",
        "actorRef": actor_ref,
        "topicRef": topic_ref,
        "previousCursor": int(updated["previous_cursor"]),
        "cursor": int(updated["cursor"]),
        "topicHighSequence": high,
        "truthBoundary": "topic navigation acknowledgement only; not semantic acceptance",
    }


def list_topic_cursors_in_tx(
    conn: psycopg.Connection[dict[str, Any]],
    *,
    actor_ref: str,
    topic_refs: Sequence[str],
) -> dict[str, int]:
    """Bulk Actor/Topic cursor projection for Attention, without changing its snapshot.

    Missing rows intentionally mean an unconsumed cursor 0 to the caller.
    Caller must only supply references from its validated navigation events.
    """
    if not topic_refs:
        return {}
    rows = conn.execute(
        "SELECT topic_ref,cursor FROM topic_consumption_cursors "
        "WHERE actor_ref=%s AND topic_ref=ANY(%s)",
        (actor_ref, list(topic_refs)),
    ).fetchall()
    return {row["topic_ref"]: int(row["cursor"]) for row in rows}
