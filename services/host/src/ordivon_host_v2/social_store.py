from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .canonical import canonical_bytes, canonical_digest
from .errors import ConflictError
from .social_bounds import (
    DEFAULT_COLLECTION_MAX_BYTES,
    DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    DEFAULT_SPACE_MAX_BYTES,
    MIN_MESSAGE_COLLECTION_MAX_BYTES,
    MIN_SPACE_MAX_BYTES,
    bounded_prefix,
    validate_max_bytes,
)
from .social_graph import (
    CoordinationIntentInput,
    IntentStanding,
    MessageInput,
    MessageRelationInput,
    MessageRelationKind,
    ParticipationStanding,
    SpaceInput,
    TopicInput,
)
from .work_store import ActorRefNotFound, WorkNotFound


class SpaceNotFound(RuntimeError):
    pass


class TopicNotFound(RuntimeError):
    pass


class MessageNotFound(RuntimeError):
    pass


class SocialStore:
    """Durable Social Graph records without IAM, scheduling, ranking, or effect authority."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def create_space(self, value: SpaceInput, *, client_request_id: str) -> dict[str, Any]:
        request = {"operation": "space.create", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "space.create", request_digest)
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            current = conn.execute(
                "SELECT space_ref,purpose,created_by_actor_ref,created_at FROM spaces "
                "WHERE space_ref=%s FOR UPDATE",
                (value.space_ref,),
            ).fetchone()
            admission = "committed"
            if current is None:
                conn.execute(
                    "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES (%s,%s,%s)",
                    (value.space_ref, value.purpose, value.actor_ref),
                )
                for subject_ref in sorted(value.subject_refs):
                    conn.execute(
                        "INSERT INTO space_subjects(space_ref,subject_ref) VALUES (%s,%s)",
                        (value.space_ref, subject_ref),
                    )
            else:
                subjects = [
                    row["subject_ref"]
                    for row in conn.execute(
                        "SELECT subject_ref FROM space_subjects WHERE space_ref=%s "
                        "ORDER BY subject_ref",
                        (value.space_ref,),
                    ).fetchall()
                ]
                if (
                    current["purpose"] != value.purpose
                    or current["created_by_actor_ref"] != value.actor_ref
                    or subjects != sorted(value.subject_refs)
                ):
                    raise ConflictError("space_ref already exists with different initial semantics")
                admission = "existing"
            result = self._get_space_in_tx(conn, value.space_ref)
            result["admission"] = admission
            self._record_receipt(conn, client_request_id, "space.create", request_digest, result)
            return result

    def set_participation(
        self,
        *,
        space_ref: str,
        actor_ref: str,
        standing: ParticipationStanding,
        client_request_id: str,
    ) -> dict[str, Any]:
        # Desired-state command: the (space, actor) natural key plus standing owns
        # idempotency. Historical request receipts must not block joined→left→joined.
        _ = client_request_id
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            self._require_space(conn, space_ref)
            self._require_actor(conn, actor_ref)
            row = conn.execute(
                "INSERT INTO participations(space_ref,actor_ref,standing) VALUES (%s,%s,%s) "
                "ON CONFLICT (space_ref,actor_ref) DO UPDATE SET standing=EXCLUDED.standing,"
                "updated_at=clock_timestamp(),change_sequence=swf_next_change_sequence() "
                "WHERE participations.standing IS DISTINCT FROM EXCLUDED.standing "
                "RETURNING space_ref,actor_ref,standing,updated_at",
                (space_ref, actor_ref, standing.value),
            ).fetchone()
            if row is None:
                row = conn.execute(
                    "SELECT space_ref,actor_ref,standing,updated_at FROM participations "
                    "WHERE space_ref=%s AND actor_ref=%s",
                    (space_ref, actor_ref),
                ).fetchone()
            if row is None:
                raise RuntimeError("participation update disappeared")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-participation",
                "spaceRef": row["space_ref"],
                "actorRef": row["actor_ref"],
                "standing": row["standing"],
                "updatedAt": row["updated_at"].isoformat(),
                "truthBoundary": "social participation only; not ownership, authentication, authorization, assignment, or EffectAuthority",
            }
            return result

    def create_topic(self, value: TopicInput, *, client_request_id: str) -> dict[str, Any]:
        request = {"operation": "topic.create", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "topic.create", request_digest)
            if replay is not None:
                return replay
            self._require_space(conn, value.space_ref)
            self._require_actor(conn, value.actor_ref)
            row = conn.execute(
                "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) "
                "VALUES (%s,%s,%s,'open',%s) ON CONFLICT (topic_ref) DO NOTHING "
                "RETURNING topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at",
                (value.topic_ref, value.space_ref, value.title, value.actor_ref),
            ).fetchone()
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at "
                    "FROM topics WHERE topic_ref=%s",
                    (value.topic_ref,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("topic declaration disappeared")
                if (
                    row["space_ref"] != value.space_ref
                    or row["title"] != value.title
                    or row["created_by_actor_ref"] != value.actor_ref
                ):
                    raise ConflictError("topic_ref already exists with different initial semantics")
                admission = "existing"
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-topic",
                "admission": admission,
                "topicRef": row["topic_ref"],
                "spaceRef": row["space_ref"],
                "title": row["title"],
                "state": row["state"],
                "createdByActorRef": row["created_by_actor_ref"],
                "createdAt": row["created_at"].isoformat(),
                "updatedAt": row["updated_at"].isoformat(),
                "truthBoundary": "named asynchronous conversation axis only; not Work lifecycle or authority",
            }
            self._record_receipt(conn, client_request_id, "topic.create", request_digest, result)
            return result

    def post_message(self, value: MessageInput) -> dict[str, Any]:
        request = {"operation": "message.post", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        message_digest = canonical_digest(
            {
                "messageRef": value.message_ref,
                "spaceRef": value.space_ref,
                "topicRef": value.topic_ref,
                "authorActorRef": value.author_actor_ref,
                "messageKind": value.message_kind.value,
                "body": value.body,
                "recordedAtMs": value.recorded_at_ms,
            }
        )
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(
                conn, value.client_request_id, "message.post", request_digest
            )
            if replay is not None:
                return replay
            self._require_actor(conn, value.author_actor_ref)
            self._require_space(conn, value.space_ref)
            topic = self._require_topic(conn, value.topic_ref)
            if topic["space_ref"] != value.space_ref:
                raise ConflictError("topic does not belong to the supplied space")
            if topic["state"] != "open":
                raise ConflictError("closed topic does not accept new messages")
            row = conn.execute(
                "INSERT INTO messages(message_ref,client_request_id,space_ref,topic_ref,author_actor_ref,"
                "message_kind,body,message_digest,recorded_at_ms) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (message_ref) DO NOTHING RETURNING sequence,message_ref,space_ref,topic_ref,"
                "author_actor_ref,message_kind,body,message_digest,recorded_at_ms,created_at",
                (
                    value.message_ref,
                    value.client_request_id,
                    value.space_ref,
                    value.topic_ref,
                    value.author_actor_ref,
                    value.message_kind.value,
                    value.body,
                    message_digest,
                    value.recorded_at_ms,
                ),
            ).fetchone()
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT sequence,message_ref,client_request_id,space_ref,topic_ref,author_actor_ref,"
                    "message_kind,body,message_digest,recorded_at_ms,created_at FROM messages "
                    "WHERE message_ref=%s",
                    (value.message_ref,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("message declaration disappeared")
                if row["message_digest"] != message_digest:
                    raise ConflictError("message_ref already exists with different content")
                admission = "existing"
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-message",
                "admission": admission,
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
                "truthBoundary": "durable collaboration message only; participation is not authorization and message content is not Work/domain truth",
            }
            self._record_receipt(
                conn, value.client_request_id, "message.post", request_digest, result
            )
            return result

    def add_message_relation(
        self, value: MessageRelationInput, *, client_request_id: str
    ) -> dict[str, Any]:
        request = {"operation": "message.relation.add", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(
                conn, client_request_id, "message.relation.add", request_digest
            )
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            source = self._require_message(conn, value.source_message_ref)
            self._validate_relation_target(conn, source, value)
            row = conn.execute(
                "INSERT INTO message_relations(source_message_ref,relation,target_ref,created_by_actor_ref) "
                "VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING created_at",
                (
                    value.source_message_ref,
                    value.relation.value,
                    value.target_ref,
                    value.actor_ref,
                ),
            ).fetchone()
            admission = "committed" if row is not None else "existing"
            existing = conn.execute(
                "SELECT source_message_ref,relation,target_ref,created_by_actor_ref,created_at "
                "FROM message_relations WHERE source_message_ref=%s AND relation=%s AND target_ref=%s",
                (value.source_message_ref, value.relation.value, value.target_ref),
            ).fetchone()
            if existing is None:
                raise RuntimeError("message relation disappeared")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-message-relation",
                "admission": admission,
                "sourceMessageRef": existing["source_message_ref"],
                "relation": existing["relation"],
                "targetRef": existing["target_ref"],
                "createdByActorRef": existing["created_by_actor_ref"],
                "createdAt": existing["created_at"].isoformat(),
                "truthBoundary": "collaboration relation only; acknowledgement is not vote/acceptance and mention is not assignment",
            }
            self._record_receipt(
                conn, client_request_id, "message.relation.add", request_digest, result
            )
            return result

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
        if after_change_sequence < 0:
            raise ValueError("after_change_sequence must be non-negative")
        if not 1 <= limit <= 500:
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
                    "nextAfterChangeSequence": after_change_sequence if not page else page[-1]["changeSequence"],
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

    def declare_intent(
        self, value: CoordinationIntentInput, *, client_request_id: str
    ) -> dict[str, Any]:
        value.validate_window()
        request = {"operation": "intent.declare", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "intent.declare", request_digest)
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            if value.work_ref is not None:
                self._require_work(conn, value.work_ref)
            if value.space_ref is not None:
                self._require_space(conn, value.space_ref)
            current = conn.execute(
                "SELECT * FROM coordination_intents WHERE intent_ref=%s FOR UPDATE",
                (value.intent_ref,),
            ).fetchone()
            immutable = (
                value.actor_ref,
                value.subject_ref,
                value.work_ref,
                value.space_ref,
                value.operation,
            )
            if current is None:
                conn.execute(
                    "INSERT INTO coordination_intents(intent_ref,actor_ref,subject_ref,work_ref,space_ref,"
                    "operation,standing,observed_at_ms,expires_at_ms) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        value.intent_ref,
                        value.actor_ref,
                        value.subject_ref,
                        value.work_ref,
                        value.space_ref,
                        value.operation,
                        value.standing.value,
                        value.observed_at_ms,
                        value.expires_at_ms,
                    ),
                )
                admission = "committed"
            else:
                existing_immutable = (
                    current["actor_ref"],
                    current["subject_ref"],
                    current["work_ref"],
                    current["space_ref"],
                    current["operation"],
                )
                if existing_immutable != immutable:
                    raise ConflictError(
                        "intent_ref already exists with different immutable semantics"
                    )
                if (
                    current["standing"] == IntentStanding.RELEASED.value
                    and value.standing == IntentStanding.ACTIVE
                ):
                    raise ConflictError("released coordination intent cannot be resurrected")
                conn.execute(
                    "UPDATE coordination_intents SET standing=%s,observed_at_ms=%s,expires_at_ms=%s,"
                    "updated_at=clock_timestamp(),change_sequence=swf_next_change_sequence() "
                    "WHERE intent_ref=%s",
                    (
                        value.standing.value,
                        value.observed_at_ms,
                        value.expires_at_ms,
                        value.intent_ref,
                    ),
                )
                admission = (
                    "existing" if current["standing"] == value.standing.value else "committed"
                )
            row = conn.execute(
                "SELECT * FROM coordination_intents WHERE intent_ref=%s", (value.intent_ref,)
            ).fetchone()
            if row is None:
                raise RuntimeError("coordination intent disappeared")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-coordination-intent",
                "admission": admission,
                "intentRef": row["intent_ref"],
                "actorRef": row["actor_ref"],
                "subjectRef": row["subject_ref"],
                "workRef": row["work_ref"],
                "spaceRef": row["space_ref"],
                "operation": row["operation"],
                "standing": row["standing"],
                "observedAtMs": int(row["observed_at_ms"]),
                "expiresAtMs": None if row["expires_at_ms"] is None else int(row["expires_at_ms"]),
                "updatedAt": row["updated_at"].isoformat(),
                "truthBoundary": "coordination intent only; not assignment, reservation, lock, lease, scheduler decision, or EffectAuthority",
            }
            self._record_receipt(conn, client_request_id, "intent.declare", request_digest, result)
            return result

    def get_space(
        self,
        space_ref: str,
        *,
        participant_limit: int = 200,
        topic_limit: int = 200,
        max_bytes: int = DEFAULT_SPACE_MAX_BYTES,
    ) -> dict[str, Any]:
        if not 1 <= participant_limit <= 200 or not 1 <= topic_limit <= 200:
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
        if not 1 <= limit <= 500:
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
        if not 1 <= limit <= 500:
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
        if not 1 <= limit <= 500:
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

    def ack_topic_cursor(
        self,
        *,
        actor_ref: str,
        topic_ref: str,
        cursor: int,
        client_request_id: str,
    ) -> dict[str, Any]:
        if cursor < 0:
            raise ValueError("cursor must be non-negative")
        request = {
            "operation": "topic.cursor.ack",
            "actorRef": actor_ref,
            "topicRef": topic_ref,
            "cursor": cursor,
        }
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "topic.cursor.ack", request_digest)
            if replay is not None:
                return replay
            self._require_actor(conn, actor_ref)
            self._require_topic(conn, topic_ref)
            high = int(
                conn.execute(
                    "SELECT COALESCE(MAX(sequence),0) AS high FROM messages WHERE topic_ref=%s",
                    (topic_ref,),
                ).fetchone()["high"]
            )
            if cursor > high:
                raise ConflictError("topic cursor cannot acknowledge beyond current topic horizon")
            current = conn.execute(
                "SELECT cursor FROM topic_consumption_cursors "
                "WHERE actor_ref=%s AND topic_ref=%s FOR UPDATE",
                (actor_ref, topic_ref),
            ).fetchone()
            previous = 0 if current is None else int(current["cursor"])
            if cursor < previous:
                raise ConflictError("topic cursor cannot move backwards")
            updated = conn.execute(
                "INSERT INTO topic_consumption_cursors(actor_ref,topic_ref,cursor) VALUES (%s,%s,%s) "
                "ON CONFLICT (actor_ref,topic_ref) DO UPDATE SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp() "
                "WHERE topic_consumption_cursors.cursor<=EXCLUDED.cursor RETURNING cursor",
                (actor_ref, topic_ref, cursor),
            ).fetchone()
            if updated is None:
                raise ConflictError("topic cursor cannot move backwards")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-topic-cursor-ack",
                "actorRef": actor_ref,
                "topicRef": topic_ref,
                "previousCursor": previous,
                "cursor": cursor,
                "topicHighSequence": high,
                "truthBoundary": "topic navigation acknowledgement only; not semantic acceptance",
            }
            self._record_receipt(conn, client_request_id, "topic.cursor.ack", request_digest, result)
            return result

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
        if not 1 <= limit <= 200:
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
                (actor_ref, actor_ref, subject_ref, subject_ref, before_created_at, before_created_at, before_space_ref, limit + 1),
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
                cursor = None if not page else {
                    "beforeCreatedAt": page[-1]["createdAt"],
                    "beforeSpaceRef": page[-1]["spaceRef"],
                }
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
        if not 1 <= limit <= 200:
            raise ValueError("limit must be in [1,200]")
        if before_sequence is not None and before_sequence < 1:
            raise ValueError("before_sequence must be positive")
        validate_max_bytes(max_bytes, minimum=MIN_MESSAGE_COLLECTION_MAX_BYTES)
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
                "FROM messages WHERE to_tsvector('simple',body) @@ websearch_to_tsquery('simple',%s) "
                "AND (%s::text IS NULL OR space_ref=%s) AND (%s::text IS NULL OR topic_ref=%s) "
                "AND (%s::bigint IS NULL OR sequence<%s) ORDER BY sequence DESC LIMIT %s",
                (query, space_ref, space_ref, topic_ref, topic_ref, before_sequence, before_sequence, limit + 1),
            ).fetchall()
            sql_more = len(rows) > limit
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
                    "truthBoundary": "PostgreSQL full-text locator ordered by message sequence, not relevance/priority; message claims require owner-native verification",
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
                "truthBoundary": "PostgreSQL full-text locator ordered by message sequence, not relevance/priority; message claims require owner-native verification",
            }

    def resume_topic(
        self,
        topic_ref: str,
        *,
        after_sequence: int = 0,
        limit: int = 50,
        max_bytes: int = DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        if after_sequence < 0:
            raise ValueError("after_sequence must be non-negative")
        validate_max_bytes(max_bytes, minimum=MIN_MESSAGE_COLLECTION_MAX_BYTES)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            topic = self._require_topic(conn, topic_ref)
            rows = conn.execute(
                "SELECT sequence,message_ref,author_actor_ref,message_kind,body,message_digest,"
                "recorded_at_ms,created_at FROM messages WHERE topic_ref=%s AND sequence>%s "
                "ORDER BY sequence LIMIT %s",
                (topic_ref, after_sequence, limit + 1),
            ).fetchall()
            sql_more = len(rows) > limit
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

    def _get_space_in_tx(
        self,
        conn: psycopg.Connection[dict[str, Any]],
        space_ref: str,
        *,
        participant_limit: int = 200,
        topic_limit: int = 200,
        max_bytes: int = DEFAULT_SPACE_MAX_BYTES,
    ) -> dict[str, Any]:
        validate_max_bytes(max_bytes, minimum=MIN_SPACE_MAX_BYTES)
        space = conn.execute(
            "SELECT space_ref,purpose,created_by_actor_ref,created_at FROM spaces WHERE space_ref=%s",
            (space_ref,),
        ).fetchone()
        if space is None:
            raise SpaceNotFound(space_ref)
        subject_count = int(conn.execute("SELECT count(*) AS n FROM space_subjects WHERE space_ref=%s", (space_ref,)).fetchone()["n"])
        participant_count = int(conn.execute("SELECT count(*) AS n FROM participations WHERE space_ref=%s", (space_ref,)).fetchone()["n"])
        topic_count = int(conn.execute("SELECT count(*) AS n FROM topics WHERE space_ref=%s", (space_ref,)).fetchone()["n"])
        subject_rows = conn.execute(
            "SELECT subject_ref FROM space_subjects WHERE space_ref=%s ORDER BY subject_ref LIMIT 129",
            (space_ref,),
        ).fetchall()
        participant_rows = conn.execute(
            "SELECT actor_ref,standing,updated_at FROM participations WHERE space_ref=%s ORDER BY actor_ref LIMIT %s",
            (space_ref, participant_limit + 1),
        ).fetchall()
        topic_rows = conn.execute(
            "SELECT topic_ref,title,state,created_by_actor_ref,created_at,updated_at FROM topics "
            "WHERE space_ref=%s ORDER BY topic_ref LIMIT %s",
            (space_ref, topic_limit + 1),
        ).fetchall()
        subjects = [row["subject_ref"] for row in subject_rows[:128]]
        participants = [
            {
                "actorRef": row["actor_ref"],
                "standing": row["standing"],
                "updatedAt": row["updated_at"].isoformat(),
            }
            for row in participant_rows[:participant_limit]
        ]
        topics = [
            {
                "topicRef": row["topic_ref"],
                "title": row["title"],
                "state": row["state"],
                "createdByActorRef": row["created_by_actor_ref"],
                "createdAt": row["created_at"].isoformat(),
                "updatedAt": row["updated_at"].isoformat(),
            }
            for row in topic_rows[:topic_limit]
        ]

        def build() -> dict[str, Any]:
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-space",
                "spaceRef": space["space_ref"],
                "purpose": space["purpose"],
                "createdByActorRef": space["created_by_actor_ref"],
                "createdAt": space["created_at"].isoformat(),
                "subjectRefs": subjects,
                "subjectCount": subject_count,
                "subjectHasMore": len(subjects) < subject_count,
                "participants": participants,
                "participantCount": participant_count,
                "participantHasMore": len(participants) < participant_count,
                "topics": topics,
                "topicCount": topic_count,
                "topicHasMore": len(topics) < topic_count,
                "truthBoundary": "social organization record only; participation does not imply identity, authority, ownership, or assignment",
            }

        result = build()
        while len(canonical_bytes(result)) > max_bytes:
            if topics:
                topics.pop()
            elif participants:
                participants.pop()
            elif subjects:
                subjects.pop()
            else:
                raise ValueError("max_bytes cannot fit the Space response envelope")
            result = build()
        return result

    @staticmethod
    def _require_actor(conn: psycopg.Connection[dict[str, Any]], actor_ref: str) -> None:
        if (
            conn.execute("SELECT 1 FROM actor_refs WHERE actor_ref=%s", (actor_ref,)).fetchone()
            is None
        ):
            raise ActorRefNotFound(actor_ref)

    @staticmethod
    def _require_work(conn: psycopg.Connection[dict[str, Any]], work_ref: str) -> None:
        if conn.execute("SELECT 1 FROM works WHERE work_ref=%s", (work_ref,)).fetchone() is None:
            raise WorkNotFound(work_ref)

    @staticmethod
    def _require_space(conn: psycopg.Connection[dict[str, Any]], space_ref: str) -> None:
        if conn.execute("SELECT 1 FROM spaces WHERE space_ref=%s", (space_ref,)).fetchone() is None:
            raise SpaceNotFound(space_ref)

    @staticmethod
    def _require_topic(conn: psycopg.Connection[dict[str, Any]], topic_ref: str) -> dict[str, Any]:
        row = conn.execute(
            "SELECT topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at "
            "FROM topics WHERE topic_ref=%s",
            (topic_ref,),
        ).fetchone()
        if row is None:
            raise TopicNotFound(topic_ref)
        return row

    @staticmethod
    def _require_message(
        conn: psycopg.Connection[dict[str, Any]], message_ref: str
    ) -> dict[str, Any]:
        row = conn.execute(
            "SELECT message_ref,space_ref,topic_ref,author_actor_ref FROM messages WHERE message_ref=%s",
            (message_ref,),
        ).fetchone()
        if row is None:
            raise MessageNotFound(message_ref)
        return row

    def _validate_relation_target(
        self,
        conn: psycopg.Connection[dict[str, Any]],
        source: dict[str, Any],
        value: MessageRelationInput,
    ) -> None:
        if value.relation in {
            MessageRelationKind.REPLY_TO,
            MessageRelationKind.ACKNOWLEDGES,
            MessageRelationKind.SUPERSEDES,
        }:
            target = self._require_message(conn, value.target_ref)
            if target["space_ref"] != source["space_ref"]:
                raise ConflictError(f"{value.relation.value} cannot cross spaces")
            if (
                value.relation == MessageRelationKind.REPLY_TO
                and target["topic_ref"] != source["topic_ref"]
            ):
                raise ConflictError("reply_to cannot cross topics")
            if (
                value.relation == MessageRelationKind.SUPERSEDES
                and value.target_ref == value.source_message_ref
            ):
                raise ConflictError("message cannot supersede itself")
        elif value.relation == MessageRelationKind.MENTIONS:
            self._require_actor(conn, value.target_ref)
        # references/about intentionally accept opaque external refs; presence is not existence proof.

    @staticmethod
    def _claim_receipt(
        conn: psycopg.Connection[dict[str, Any]],
        client_request_id: str,
        operation: str,
        request_digest: str,
    ) -> dict[str, Any] | None:
        claimed = conn.execute(
            "INSERT INTO command_receipts(client_request_id,operation,request_digest,response) "
            "VALUES (%s,%s,%s,NULL) ON CONFLICT (client_request_id) DO NOTHING RETURNING client_request_id",
            (client_request_id, operation, request_digest),
        ).fetchone()
        if claimed is not None:
            return None
        row = conn.execute(
            "SELECT operation,request_digest,response FROM command_receipts WHERE client_request_id=%s",
            (client_request_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("idempotency claim disappeared")
        if row["operation"] != operation or row["request_digest"] != request_digest:
            raise ConflictError("client_request_id was already used for different content")
        response = row["response"]
        if response is None:
            raise RuntimeError("committed idempotency claim is missing its response")
        if not isinstance(response, dict):
            raise RuntimeError("idempotency response is not a PostgreSQL jsonb object")
        replay = dict(response)
        replay["admission"] = "existing"
        return replay

    @staticmethod
    def _record_receipt(
        conn: psycopg.Connection[dict[str, Any]],
        client_request_id: str,
        operation: str,
        request_digest: str,
        result: dict[str, Any],
    ) -> None:
        updated = conn.execute(
            "UPDATE command_receipts SET response=%s WHERE client_request_id=%s AND operation=%s "
            "AND request_digest=%s AND response IS NULL RETURNING client_request_id",
            (Jsonb(result), client_request_id, operation, request_digest),
        ).fetchone()
        if updated is None:
            raise RuntimeError("idempotency claim could not be finalized")
