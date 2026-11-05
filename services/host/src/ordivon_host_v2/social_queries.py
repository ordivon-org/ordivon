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
    DEFAULT_SPACE_MAX_BYTES,
    MIN_MESSAGE_COLLECTION_MAX_BYTES,
    MIN_SPACE_MAX_BYTES,
    bounded_prefix,
    validate_max_bytes,
)
from .errors import ConflictError
from .social_errors import MessageNotFound


class SocialReadQueries:
    """Read-only SQL projections inherited by the authoritative SocialStore."""

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

    def get_space(
        self,
        space_ref: str,
        *,
        participant_limit: int = 200,
        topic_limit: int = 200,
        max_bytes: int = DEFAULT_SPACE_MAX_BYTES,
    ) -> dict[str, Any]:
        if (
            type(participant_limit) is not int
            or type(topic_limit) is not int
            or not 1 <= participant_limit <= 200
            or not 1 <= topic_limit <= 200
        ):
            raise ValueError("embedded participant/topic limits must be in [1,200]")
        validate_max_bytes(max_bytes, minimum=MIN_SPACE_MAX_BYTES)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            return self._get_space_in_tx(
                conn,
                space_ref,
                participant_limit=participant_limit,
                topic_limit=topic_limit,
                max_bytes=max_bytes,
            )

    def list_space_subjects(
        self,
        space_ref: str,
        *,
        after_subject_ref: str | None = None,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_space(conn, space_ref)
            rows = conn.execute(
                "SELECT subject_ref FROM space_subjects WHERE space_ref=%s "
                "AND (%s::text IS NULL OR subject_ref>%s) ORDER BY subject_ref LIMIT %s",
                (space_ref, after_subject_ref, after_subject_ref, limit + 1),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [str(row["subject_ref"]) for row in rows[:limit]]

            def envelope(page: list[str]) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-space-subject-list",
                    "spaceRef": space_ref,
                    "subjectRefs": page,
                    "hasMore": True,
                    "nextAfterSubjectRef": None if not page else page[-1],
                    "rankingApplied": False,
                    "truthBoundary": "social subject navigation only; references do not transfer foreign authority",
                }

            page, byte_more = bounded_prefix(candidates, max_bytes=max_bytes, envelope=envelope)
            has_more = sql_more or byte_more
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-space-subject-list",
                "spaceRef": space_ref,
                "subjectRefs": page,
                "hasMore": has_more,
                "nextAfterSubjectRef": page[-1] if has_more and page else None,
                "rankingApplied": False,
                "truthBoundary": "social subject navigation only; references do not transfer foreign authority",
            }

    def list_participations(
        self,
        space_ref: str,
        *,
        after_actor_ref: str | None = None,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_space(conn, space_ref)
            rows = conn.execute(
                "SELECT actor_ref,standing,updated_at FROM participations WHERE space_ref=%s "
                "AND (%s::text IS NULL OR actor_ref>%s) ORDER BY actor_ref LIMIT %s",
                (space_ref, after_actor_ref, after_actor_ref, limit + 1),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [
                {
                    "actorRef": row["actor_ref"],
                    "standing": row["standing"],
                    "updatedAt": row["updated_at"].isoformat(),
                }
                for row in rows[:limit]
            ]

            def envelope(page: list[dict[str, Any]]) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-participation-list",
                    "spaceRef": space_ref,
                    "participants": page,
                    "hasMore": True,
                    "nextAfterActorRef": None if not page else page[-1]["actorRef"],
                    "rankingApplied": False,
                    "truthBoundary": "social participation only; not IAM, ownership, assignment, or authorization",
                }

            page, byte_more = bounded_prefix(candidates, max_bytes=max_bytes, envelope=envelope)
            has_more = sql_more or byte_more
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-participation-list",
                "spaceRef": space_ref,
                "participants": page,
                "hasMore": has_more,
                "nextAfterActorRef": page[-1]["actorRef"] if has_more and page else None,
                "rankingApplied": False,
                "truthBoundary": "social participation only; not IAM, ownership, assignment, or authorization",
            }

    def list_topics(
        self,
        space_ref: str,
        *,
        after_topic_ref: str | None = None,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_space(conn, space_ref)
            rows = conn.execute(
                "SELECT topic_ref,title,state,created_by_actor_ref,created_at,updated_at FROM topics "
                "WHERE space_ref=%s AND (%s::text IS NULL OR topic_ref>%s) "
                "ORDER BY topic_ref LIMIT %s",
                (space_ref, after_topic_ref, after_topic_ref, limit + 1),
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

            def envelope(page: list[dict[str, Any]]) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-topic-list",
                    "spaceRef": space_ref,
                    "topics": page,
                    "hasMore": True,
                    "nextAfterTopicRef": None if not page else page[-1]["topicRef"],
                    "rankingApplied": False,
                    "truthBoundary": "conversation-axis inventory only; not Work lifecycle or priority",
                }

            page, byte_more = bounded_prefix(candidates, max_bytes=max_bytes, envelope=envelope)
            has_more = sql_more or byte_more
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-topic-list",
                "spaceRef": space_ref,
                "topics": page,
                "hasMore": has_more,
                "nextAfterTopicRef": page[-1]["topicRef"] if has_more and page else None,
                "rankingApplied": False,
                "truthBoundary": "conversation-axis inventory only; not Work lifecycle or priority",
            }

    def list_spaces(
        self,
        *,
        actor_ref: str | None = None,
        subject_ref: str | None = None,
        limit: int = 50,
        before_created_at: str | None = None,
        before_space_ref: str | None = None,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("limit must be in [1,200]")
        if (before_created_at is None) != (before_space_ref is None):
            raise ValueError("before_created_at and before_space_ref must be supplied together")
        validate_max_bytes(max_bytes)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            if actor_ref is not None:
                self._require_actor(conn, actor_ref)
            rows = conn.execute(
                "SELECT s.space_ref,s.purpose,s.created_at,"
                "(SELECT count(*) FROM topics t WHERE t.space_ref=s.space_ref AND t.state='open') AS open_topics,"
                "(SELECT count(*) FROM participations p WHERE p.space_ref=s.space_ref AND p.standing IN ('joined','observer')) AS active_participants "
                "FROM spaces s WHERE "
                "(%s::text IS NULL OR EXISTS (SELECT 1 FROM participations p WHERE p.space_ref=s.space_ref AND p.actor_ref=%s AND p.standing IN ('joined','observer'))) "
                "AND (%s::text IS NULL OR EXISTS (SELECT 1 FROM space_subjects ss WHERE ss.space_ref=s.space_ref AND ss.subject_ref=%s)) "
                "AND (%s::timestamptz IS NULL OR (s.created_at,s.space_ref) < (%s::timestamptz,%s)) "
                "ORDER BY s.created_at DESC,s.space_ref DESC LIMIT %s",
                (
                    actor_ref,
                    actor_ref,
                    subject_ref,
                    subject_ref,
                    before_created_at,
                    before_created_at,
                    before_space_ref,
                    limit + 1,
                ),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [
                {
                    "spaceRef": row["space_ref"],
                    "purpose": row["purpose"],
                    "openTopicCount": int(row["open_topics"]),
                    "activeParticipantCount": int(row["active_participants"]),
                    "createdAt": row["created_at"].isoformat(),
                }
                for row in rows[:limit]
            ]

            def envelope(page: list[dict[str, Any]]) -> dict[str, Any]:
                cursor = (
                    None
                    if not page
                    else {
                        "beforeCreatedAt": page[-1]["createdAt"],
                        "beforeSpaceRef": page[-1]["spaceRef"],
                    }
                )
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-space-list",
                    "spaces": page,
                    "hasMore": True,
                    "nextCursor": cursor,
                    "rankingApplied": False,
                    "truthBoundary": "compact social-space locator only; participation is not ownership, authority, or assignment",
                }

            page, byte_more = bounded_prefix(candidates, max_bytes=max_bytes, envelope=envelope)
            has_more = sql_more or byte_more
            cursor = None
            if has_more and page:
                cursor = {
                    "beforeCreatedAt": page[-1]["createdAt"],
                    "beforeSpaceRef": page[-1]["spaceRef"],
                }
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-space-list",
                "spaces": page,
                "hasMore": has_more,
                "nextCursor": cursor,
                "rankingApplied": False,
                "truthBoundary": "compact social-space locator only; participation is not ownership, authority, or assignment",
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
        search_predicate = (
            "strpos(body,%s)>0"
            if cjk_literal
            else "to_tsvector('simple',body) @@ websearch_to_tsquery('simple',%s)"
        )
        search_boundary = (
            "PostgreSQL CJK literal substring locator"
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
