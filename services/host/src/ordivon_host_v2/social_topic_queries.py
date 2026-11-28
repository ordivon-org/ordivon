"""PostgreSQL-owned read projections for the Host Social Graph.

The SocialStore owns write transactions, command receipts and the PostgreSQL
identity. This non-authoritative query facet uses the same DSN and canonical
row validation; it does not introduce separate persistence or route policy.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

import psycopg

from .collection_pagination import (
    DEFAULT_COLLECTION_MAX_BYTES,
    DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    MIN_MESSAGE_COLLECTION_MAX_BYTES,
    bounded_page,
    validate_max_bytes,
)
from .errors import InvalidArgumentError
from .postgres_bounds import HOST_WIRE_INT_MAX
from .references.actor_refs import ActorReferenceLookup
from .references.record_refs import RecordReferenceLookup
from .social_errors import TopicResumeCursorAhead
from .social_message_records import verified_message_wire
from .topic_cursor_records import get_topic_cursor_in_tx, topic_high_sequence_in_tx


class SocialTopicReadQueries:
    """Read-only PostgreSQL projections; SocialStore remains the sole write authority."""

    def __init__(
        self, connect: Callable[[], AbstractContextManager[psycopg.Connection[dict[str, Any]]]]
    ) -> None:
        self._connect = connect

    def list_topics(
        self,
        space_ref: str,
        *,
        after_topic_ref: str | None = None,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise InvalidArgumentError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)
        if type(include_archived) is not bool:
            raise InvalidArgumentError("include_archived must be a boolean")
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            RecordReferenceLookup._require_space(conn, space_ref)
            rows = conn.execute(
                "SELECT topic_ref,title,state,created_by_actor_ref,created_at,updated_at FROM topics "
                "WHERE space_ref=%s AND (%s OR state <> 'archived') "
                "AND (%s::text IS NULL OR topic_ref>%s) "
                "ORDER BY topic_ref LIMIT %s",
                (space_ref, include_archived, after_topic_ref, after_topic_ref, limit + 1),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [
                {
                    "topicRef": row["topic_ref"],
                    "title": row["title"],
                    "state": row["state"],
                    "createdByActorRef": row["created_by_actor_ref"],
                    "createdAt": row["created_at"].isoformat(),
                    "updatedAt": row["updated_at"].isoformat(),
                }
                for row in rows[:limit]
            ]

            def envelope(last: dict[str, Any] | None, has_more: bool) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-topic-list",
                    "spaceRef": space_ref,
                    "hasMore": has_more,
                    "nextAfterTopicRef": last["topicRef"]
                    if has_more and last is not None
                    else None,
                    "rankingApplied": False,
                    "truthBoundary": "conversation-axis inventory only; not Work lifecycle or priority",
                }

            return bounded_page(
                candidates,
                max_bytes=max_bytes,
                collection_key="topics",
                envelope=envelope,
                source_has_more=sql_more,
            )

    def resume_topic(
        self,
        topic_ref: str,
        *,
        after_sequence: int = 0,
        limit: int = 50,
        max_bytes: int = DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise InvalidArgumentError("limit must be in [1,500]")
        if type(after_sequence) is not int or not 0 <= after_sequence <= HOST_WIRE_INT_MAX:
            raise InvalidArgumentError("after_sequence must be non-negative within JSON safe integer range")
        validate_max_bytes(max_bytes, minimum=MIN_MESSAGE_COLLECTION_MAX_BYTES)
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            topic = RecordReferenceLookup._require_topic(conn, topic_ref)
            # A cursor from Attention's global change clock (or a different
            # Topic) can be numerically ahead of this Topic's message horizon.
            # Returning an empty hasMore=false page would conceal that mistake.
            # Read the Topic high in the same MVCC cut as the message page.
            topic_high = topic_high_sequence_in_tx(conn, topic_ref)
            if after_sequence > topic_high:
                raise TopicResumeCursorAhead(topic_ref, after_sequence, topic_high)
            rows = conn.execute(
                "SELECT sequence,message_ref,space_ref,topic_ref,author_actor_ref,"
                "message_kind,body,message_digest,recorded_at_ms,created_at "
                "FROM messages WHERE topic_ref=%s AND sequence>%s "
                "ORDER BY sequence LIMIT %s",
                (topic_ref, after_sequence, limit + 1),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [verified_message_wire(row, include_scope=False) for row in rows[:limit]]
            topic_wire = {
                "topicRef": topic["topic_ref"],
                "spaceRef": topic["space_ref"],
                "title": topic["title"],
                "state": topic["state"],
            }

            def envelope(last: dict[str, Any] | None, has_more: bool) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-topic-resume",
                    "topic": topic_wire,
                    "hasMore": has_more,
                    "nextAfterSequence": after_sequence if last is None else int(last["sequence"]),
                    "truthBoundary": "bounded topic conversation only; message claims require owner-native verification",
                }

            return bounded_page(
                candidates,
                max_bytes=max_bytes,
                collection_key="messages",
                envelope=envelope,
                minimum=MIN_MESSAGE_COLLECTION_MAX_BYTES,
                source_has_more=sql_more,
            )

    def get_topic_cursor(self, *, actor_ref: str, topic_ref: str) -> dict[str, Any]:
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            ActorReferenceLookup._require_actor(conn, actor_ref)
            RecordReferenceLookup._require_topic(conn, topic_ref)
            return get_topic_cursor_in_tx(conn, actor_ref=actor_ref, topic_ref=topic_ref)
