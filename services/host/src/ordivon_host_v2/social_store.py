from __future__ import annotations

# Existing tests/tool consumers monkeypatch the shared psycopg module here.
import psycopg as psycopg

from .coordination_intent_commands import CoordinationIntentCommands
from .postgres_connections import HostPostgresConnections
from .references.actor_refs import ActorReferenceLookup
from .references.record_refs import RecordReferenceLookup
from .social_errors import MessageNotFound as MessageNotFound
from .social_errors import SpaceNotFound as SpaceNotFound
from .social_errors import TopicNotFound as TopicNotFound
from .social_message_commands import (
    SocialMessageCommands,
)
from .social_message_commands import (
    _reply_target_precedes_source as _reply_target_precedes_source,
)
from .social_read_queries import SocialReadQueries
from .social_space_commands import SocialSpaceCommands
from .social_topic_commands import SocialTopicCommands


class SocialStore(
    SocialSpaceCommands,
    SocialTopicCommands,
    SocialMessageCommands,
    CoordinationIntentCommands,
    SocialReadQueries,
    ActorReferenceLookup,
    RecordReferenceLookup,
    HostPostgresConnections,
):
    """Durable Social Graph records without IAM, scheduling, ranking, or effect authority."""
