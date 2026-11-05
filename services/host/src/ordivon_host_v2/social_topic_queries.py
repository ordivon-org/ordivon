"""PostgreSQL-owned read projections for the Host Social Graph.

The SocialStore owns write transactions, command receipts and the PostgreSQL
identity. This non-authoritative query facet uses the same DSN and canonical
row validation; it does not introduce separate persistence or route policy.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from .collection_pagination import (
    DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    MIN_MESSAGE_COLLECTION_MAX_BYTES,
    bounded_prefix,
    validate_max_bytes,
)


class SocialTopicReadQueries:
    """Read-only PostgreSQL projections; SocialStore remains the sole write authority."""

    dsn: str

    def resume_topic(
        self,
        topic_ref: str,
        *,
        after_sequence: int = 0,
        limit: int = 50,
        max_bytes: int = DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        if type(after_sequence) is not int or after_sequence < 0:
            raise ValueError("after_sequence must be non-negative")
        validate_max_bytes(max_bytes, minimum=MIN_MESSAGE_COLLECTION_MAX_BYTES)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            topic = self._require_topic(conn, topic_ref)
            rows = conn.execute(
                "SELECT sequence,message_ref,space_ref,topic_ref,author_actor_ref,"
                "message_kind,body,message_digest,recorded_at_ms,created_at "
                "FROM messages WHERE topic_ref=%s AND sequence>%s "
                "ORDER BY sequence LIMIT %s",
                (topic_ref, after_sequence, limit + 1),
            ).fetchall()
            sql_more = len(rows) > limit
            for row in rows[:limit]:
                self._verify_message_content_digest(row)
            candidates = [
                {
                    "sequence": int(row["sequence"]),
                    "messageRef": row["message_ref"],
                    "authorActorRef": row["author_actor_ref"],
                    "messageKind": row["message_kind"],
                    "body": row["body"],
                    "messageDigest": row["message_digest"],
                    "recordedAtMs": int(row["recorded_at_ms"]),
                    "createdAt": row["created_at"].isoformat(),
                }
                for row in rows[:limit]
            ]
            topic_wire = {
                "topicRef": topic["topic_ref"],
                "spaceRef": topic["space_ref"],
                "title": topic["title"],
                "state": topic["state"],
            }

            def envelope(page: list[dict[str, Any]]) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-topic-resume",
                    "topic": topic_wire,
                    "messages": page,
                    "hasMore": True,
                    "nextAfterSequence": after_sequence if not page else int(page[-1]["sequence"]),
                    "truthBoundary": "bounded topic conversation only; message claims require owner-native verification",
                }

            page, byte_more = bounded_prefix(
                candidates,
                max_bytes=max_bytes,
                envelope=envelope,
                minimum=MIN_MESSAGE_COLLECTION_MAX_BYTES,
            )
            has_more = sql_more or byte_more
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-topic-resume",
                "topic": topic_wire,
                "messages": page,
                "hasMore": has_more,
                "nextAfterSequence": after_sequence if not page else int(page[-1]["sequence"]),
                "truthBoundary": "bounded topic conversation only; message claims require owner-native verification",
            }

    def get_topic_cursor(self, *, actor_ref: str, topic_ref: str) -> dict[str, Any]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_actor(conn, actor_ref)
            self._require_topic(conn, topic_ref)
            row = conn.execute(
                "SELECT cursor FROM topic_consumption_cursors WHERE actor_ref=%s AND topic_ref=%s",
                (actor_ref, topic_ref),
            ).fetchone()
            high = int(
                conn.execute(
                    "SELECT COALESCE(MAX(sequence),0) AS high FROM messages WHERE topic_ref=%s",
                    (topic_ref,),
                ).fetchone()["high"]
            )
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-topic-cursor",
                "actorRef": actor_ref,
                "topicRef": topic_ref,
                "cursor": 0 if row is None else int(row["cursor"]),
                "topicHighSequence": high,
                "truthBoundary": "topic navigation cursor only; not evidence of semantic acceptance",
            }
