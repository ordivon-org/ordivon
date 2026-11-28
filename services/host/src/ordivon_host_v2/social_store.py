from __future__ import annotations

from typing import Any, Literal

# Existing tests/tool consumers monkeypatch the shared psycopg module here.
import psycopg as psycopg

from .collaboration_inputs import (
    MessageInput,
    MessageRelationInput,
    MessageRelationKind,
    ParticipationStanding,
    SpaceInput,
    TopicInput,
)
from .collection_pagination import (
    DEFAULT_COLLECTION_MAX_BYTES,
    DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    DEFAULT_SPACE_MAX_BYTES,
)
from .coordination_inputs import CoordinationIntentInput
from .coordination_intent_commands import CoordinationIntentCommands
from .postgres_connections import HostPostgresConnections
from .social_errors import MessageNotFound as MessageNotFound
from .social_errors import SpaceNotFound as SpaceNotFound
from .social_errors import TopicNotFound as TopicNotFound
from .social_message_commands import (
    SocialMessageCommands,
)
from .social_message_commands import (
    _reply_target_precedes_source as _reply_target_precedes_source,
)
from .social_message_queries import SocialMessageReadQueries
from .social_space_commands import SocialSpaceCommands
from .social_space_queries import SocialSpaceReadQueries
from .social_topic_commands import SocialTopicCommands
from .social_topic_queries import SocialTopicReadQueries


class SocialStore(HostPostgresConnections):
    """Durable Social Graph records without IAM, scheduling, ranking, or effect authority."""

    def create_space(self, value: SpaceInput, *, client_request_id: str) -> dict[str, Any]:
        return SocialSpaceCommands(self._connect).create_space(
            value, client_request_id=client_request_id
        )

    def set_participation(
        self,
        *,
        space_ref: str,
        actor_ref: str,
        standing: ParticipationStanding,
        client_request_id: str,
    ) -> dict[str, Any]:
        return SocialSpaceCommands(self._connect).set_participation(
            space_ref=space_ref,
            actor_ref=actor_ref,
            standing=standing,
            client_request_id=client_request_id,
        )

    def create_topic(self, value: TopicInput, *, client_request_id: str) -> dict[str, Any]:
        return SocialTopicCommands(self._connect).create_topic(
            value, client_request_id=client_request_id
        )

    def set_topic_state(
        self,
        *,
        topic_ref: str,
        actor_ref: str,
        state: Literal["open", "closed", "archived"],
        expected_state: Literal["open", "closed", "archived"],
        expected_high_sequence: int,
        expected_change_sequence: int,
        client_request_id: str,
    ) -> dict[str, Any]:
        return SocialTopicCommands(self._connect).set_topic_state(
            topic_ref=topic_ref,
            actor_ref=actor_ref,
            state=state,
            expected_state=expected_state,
            expected_high_sequence=expected_high_sequence,
            expected_change_sequence=expected_change_sequence,
            client_request_id=client_request_id,
        )

    def ack_topic_cursor(
        self,
        *,
        actor_ref: str,
        topic_ref: str,
        cursor: int,
        client_request_id: str,
    ) -> dict[str, Any]:
        return SocialTopicCommands(self._connect).ack_topic_cursor(
            actor_ref=actor_ref,
            topic_ref=topic_ref,
            cursor=cursor,
            client_request_id=client_request_id,
        )

    def post_message(self, value: MessageInput) -> dict[str, Any]:
        return SocialMessageCommands(self._connect).post_message(value)

    def add_message_relation(
        self,
        value: MessageRelationInput,
        *,
        client_request_id: str,
    ) -> dict[str, Any]:
        return SocialMessageCommands(self._connect).add_message_relation(
            value, client_request_id=client_request_id
        )

    def declare_intent(
        self, value: CoordinationIntentInput, *, client_request_id: str
    ) -> dict[str, Any]:
        return CoordinationIntentCommands(self._connect).declare_intent(
            value, client_request_id=client_request_id
        )

    def get_space(
        self,
        space_ref: str,
        *,
        participant_limit: int = 200,
        topic_limit: int = 200,
        max_bytes: int = DEFAULT_SPACE_MAX_BYTES,
    ) -> dict[str, Any]:
        return SocialSpaceReadQueries(self._connect).get_space(
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
        return SocialSpaceReadQueries(self._connect).list_space_subjects(
            space_ref,
            after_subject_ref=after_subject_ref,
            limit=limit,
            max_bytes=max_bytes,
        )

    def list_participations(
        self,
        space_ref: str,
        *,
        after_actor_ref: str | None = None,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        return SocialSpaceReadQueries(self._connect).list_participations(
            space_ref,
            after_actor_ref=after_actor_ref,
            limit=limit,
            max_bytes=max_bytes,
        )

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
        return SocialSpaceReadQueries(self._connect).list_spaces(
            actor_ref=actor_ref,
            subject_ref=subject_ref,
            limit=limit,
            before_created_at=before_created_at,
            before_space_ref=before_space_ref,
            max_bytes=max_bytes,
        )

    def list_topics(
        self,
        space_ref: str,
        *,
        after_topic_ref: str | None = None,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        return SocialTopicReadQueries(self._connect).list_topics(
            space_ref,
            after_topic_ref=after_topic_ref,
            limit=limit,
            max_bytes=max_bytes,
            include_archived=include_archived,
        )

    def resume_topic(
        self,
        topic_ref: str,
        *,
        after_sequence: int = 0,
        limit: int = 50,
        max_bytes: int = DEFAULT_MESSAGE_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        return SocialTopicReadQueries(self._connect).resume_topic(
            topic_ref,
            after_sequence=after_sequence,
            limit=limit,
            max_bytes=max_bytes,
        )

    def get_topic_cursor(self, *, actor_ref: str, topic_ref: str) -> dict[str, Any]:
        return SocialTopicReadQueries(self._connect).get_topic_cursor(
            actor_ref=actor_ref, topic_ref=topic_ref
        )

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
        return SocialMessageReadQueries(self._connect).list_message_relations(
            message_ref,
            direction=direction,
            relation=relation,
            after_change_sequence=after_change_sequence,
            limit=limit,
            max_bytes=max_bytes,
        )

    def get_message(
        self,
        message_ref: str,
        *,
        expected_digest: str | None = None,
    ) -> dict[str, Any]:
        return SocialMessageReadQueries(self._connect).get_message(
            message_ref, expected_digest=expected_digest
        )

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
        return SocialMessageReadQueries(self._connect).search_messages(
            query,
            space_ref=space_ref,
            topic_ref=topic_ref,
            before_sequence=before_sequence,
            limit=limit,
            max_bytes=max_bytes,
        )
