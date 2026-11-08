"""PostgreSQL-owned read projections for the Host Social Graph.

The SocialStore owns write transactions, command receipts and the PostgreSQL
identity. This non-authoritative query facet uses the same DSN and canonical
row validation; it does not introduce separate persistence or route policy.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical_json import canonical_digest
from .collaboration_inputs import MessageRelationKind
from .collection_pagination import (
    DEFAULT_COLLECTION_MAX_BYTES,
    DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    MIN_MESSAGE_COLLECTION_MAX_BYTES,
    bounded_prefix,
    validate_max_bytes,
)
from .errors import ConflictError
from .social_errors import MessageNotFound


class SocialMessageReadQueries:
    """Read-only PostgreSQL projections; SocialStore remains the sole write authority."""

    dsn: str

    def list_message_relations(
        self,
        message_ref: str,
        *,
        direction: str = "both",
        relation: MessageRelationKind | None = None,
        after_change_sequence: int = 0,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if direction not in {"outgoing", "incoming", "both"}:
            raise ValueError("direction must be outgoing, incoming, or both")
        if type(after_change_sequence) is not int or after_change_sequence < 0:
            raise ValueError("after_change_sequence must be non-negative")
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_message(conn, message_ref)
            rows = conn.execute(
                "SELECT change_sequence,source_message_ref,relation,target_ref,created_by_actor_ref,created_at "
                "FROM message_relations WHERE change_sequence>%s "
                "AND (%s::text IS NULL OR relation=%s) "
                "AND ((%s IN ('outgoing','both') AND source_message_ref=%s) "
                "OR (%s IN ('incoming','both') AND target_ref=%s)) "
                "ORDER BY change_sequence,source_message_ref,relation,target_ref LIMIT %s",
                (
                    after_change_sequence,
                    None if relation is None else relation.value,
                    None if relation is None else relation.value,
                    direction,
                    message_ref,
                    direction,
                    message_ref,
                    limit + 1,
                ),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [
                {
                    "changeSequence": int(row["change_sequence"]),
                    "sourceMessageRef": row["source_message_ref"],
                    "relation": row["relation"],
                    "targetRef": row["target_ref"],
                    "createdByActorRef": row["created_by_actor_ref"],
                    "createdAt": row["created_at"].isoformat(),
                }
                for row in rows[:limit]
            ]

            def envelope(page: list[dict[str, Any]]) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-message-relation-list",
                    "messageRef": message_ref,
                    "direction": direction,
                    "relations": page,
                    "hasMore": True,
                    "nextAfterChangeSequence": after_change_sequence
                    if not page
                    else page[-1]["changeSequence"],
                    "rankingApplied": False,
                    "truthBoundary": "explicit collaboration relations only; opaque targets are references, not existence or authority proof",
                }

            page, byte_more = bounded_prefix(candidates, max_bytes=max_bytes, envelope=envelope)
            has_more = sql_more or byte_more
            next_sequence = after_change_sequence if not page else int(page[-1]["changeSequence"])
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-message-relation-list",
                "messageRef": message_ref,
                "direction": direction,
                "relations": page,
                "hasMore": has_more,
                "nextAfterChangeSequence": next_sequence,
                "rankingApplied": False,
                "truthBoundary": "explicit collaboration relations only; opaque targets are references, not existence or authority proof",
            }

    @staticmethod
    def _verify_message_content_digest(row: dict[str, Any]) -> None:
        # Digest is a claim about all immutable message fields, not an
        # authoritative pointer by itself. Every consumer-visible read must
        # bind the stored claim to the actual PostgreSQL row bytes/values.
        actual = canonical_digest(
            {
                "messageRef": row["message_ref"],
                "spaceRef": row["space_ref"],
                "topicRef": row["topic_ref"],
                "authorActorRef": row["author_actor_ref"],
                "messageKind": row["message_kind"],
                "body": row["body"],
                "recordedAtMs": row["recorded_at_ms"],
            }
        )
        if actual != row["message_digest"]:
            raise RuntimeError("Host message content digest differs from stored claim")

    def get_message(
        self,
        message_ref: str,
        *,
        expected_digest: str | None = None,
    ) -> dict[str, Any]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            row = conn.execute(
                "SELECT sequence,message_ref,space_ref,topic_ref,author_actor_ref,message_kind,"
                "body,message_digest,recorded_at_ms,created_at FROM messages WHERE message_ref=%s",
                (message_ref,),
            ).fetchone()
            if row is None:
                raise MessageNotFound(message_ref)
            self._verify_message_content_digest(row)
            if expected_digest is not None and row["message_digest"] != expected_digest:
                raise ConflictError(
                    f"message digest mismatch: expected {expected_digest}, "
                    f"actual {row['message_digest']}"
                )
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-message-read",
                "sequence": int(row["sequence"]),
                "messageRef": row["message_ref"],
                "spaceRef": row["space_ref"],
                "topicRef": row["topic_ref"],
                "authorActorRef": row["author_actor_ref"],
                "messageKind": row["message_kind"],
                "body": row["body"],
                "messageDigest": row["message_digest"],
                "recordedAtMs": int(row["recorded_at_ms"]),
                "createdAt": row["created_at"].isoformat(),
                "truthBoundary": (
                    "exact durable Host message projection only; message content remains "
                    "collaboration evidence until interpreted by the owning domain"
                ),
            }

    def search_messages(
        self,
        query: str,
        *,
        space_ref: str | None = None,
        topic_ref: str | None = None,
        before_sequence: int | None = None,
        limit: int = 50,
        max_bytes: int = DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("query must be non-empty")
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("limit must be in [1,200]")
        if before_sequence is not None and (
            type(before_sequence) is not int or before_sequence < 1
        ):
            raise ValueError("before_sequence must be positive")
        validate_max_bytes(max_bytes, minimum=MIN_MESSAGE_COLLECTION_MAX_BYTES)
        # PostgreSQL 'simple' FTS does not segment Chinese words. Match a
        # single unspaced CJK phrase literally so it can occur within a
        # longer Chinese token; preserve historical FTS for other queries.
        # The predicate is fixed SQL and query bytes stay parameter-bound.
        cjk_literal = any("\u3400" <= char <= "\u9fff" for char in query) and not any(
            char.isspace() for char in query.strip()
        )
        unicode_gram_candidate = cjk_literal and sum(
            "\u3400" <= char <= "\u9fff" for char in query
        ) >= 3
        search_predicate = (
            "host_unicode_ngrams3(body) @> host_unicode_ngrams3(%s) "
            "AND strpos(body,%s)>0"
            if unicode_gram_candidate
            else "strpos(body,%s)>0"
            if cjk_literal
            else "to_tsvector('simple',body) @@ websearch_to_tsquery('simple',%s)"
        )
        search_boundary = (
            "PostgreSQL CJK indexed Unicode-gram locator"
            if unicode_gram_candidate
            else "PostgreSQL CJK literal substring locator"
            if cjk_literal
            else "PostgreSQL full-text locator"
        )
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            if space_ref is not None:
                self._require_space(conn, space_ref)
            if topic_ref is not None:
                topic = self._require_topic(conn, topic_ref)
                if space_ref is not None and topic["space_ref"] != space_ref:
                    raise ConflictError("topic does not belong to supplied space")
            rows = conn.execute(
                "SELECT sequence,message_ref,space_ref,topic_ref,author_actor_ref,message_kind,body,message_digest,recorded_at_ms,created_at "
                "FROM messages WHERE " + search_predicate + " "
                "AND (%s::text IS NULL OR space_ref=%s) AND (%s::text IS NULL OR topic_ref=%s) "
                "AND (%s::bigint IS NULL OR sequence<%s) ORDER BY sequence DESC LIMIT %s",
                (
                    query,
                    *((query,) if unicode_gram_candidate else ()),
                    space_ref,
                    space_ref,
                    topic_ref,
                    topic_ref,
                    before_sequence,
                    before_sequence,
                    limit + 1,
                ),
            ).fetchall()
            sql_more = len(rows) > limit
            for row in rows[:limit]:
                self._verify_message_content_digest(row)
            candidates = [
                {
                    "sequence": int(row["sequence"]),
                    "messageRef": row["message_ref"],
                    "spaceRef": row["space_ref"],
                    "topicRef": row["topic_ref"],
                    "authorActorRef": row["author_actor_ref"],
                    "messageKind": row["message_kind"],
                    "body": row["body"],
                    "messageDigest": row["message_digest"],
                    "recordedAtMs": int(row["recorded_at_ms"]),
                    "createdAt": row["created_at"].isoformat(),
                }
                for row in rows[:limit]
            ]

            def envelope(page: list[dict[str, Any]]) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-message-search",
                    "query": query,
                    "messages": page,
                    "hasMore": True,
                    "nextBeforeSequence": None if not page else int(page[-1]["sequence"]),
                    "rankingApplied": False,
                    "ordering": "sequence_desc",
                    "truthBoundary": search_boundary
                    + " ordered by message sequence, not relevance/priority; message claims require owner-native verification",
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
                "kind": "ordivon.host-message-search",
                "query": query,
                "messages": page,
                "hasMore": has_more,
                "nextBeforeSequence": int(page[-1]["sequence"]) if has_more and page else None,
                "rankingApplied": False,
                "ordering": "sequence_desc",
                "truthBoundary": search_boundary
                + " ordered by message sequence, not relevance/priority; message claims require owner-native verification",
            }

    @staticmethod
    def _require_message(
        conn: psycopg.Connection[dict[str, Any]], message_ref: str
    ) -> dict[str, Any]:
        row = conn.execute(
            "SELECT message_ref,sequence,space_ref,topic_ref,author_actor_ref "
            "FROM messages WHERE message_ref=%s",
            (message_ref,),
        ).fetchone()
        if row is None:
            raise MessageNotFound(message_ref)
        return row
