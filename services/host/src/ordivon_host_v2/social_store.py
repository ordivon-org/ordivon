from __future__ import annotations

# Legacy test/tool import surface: this is the same shared psycopg module used
# by HostPostgresConnections; never a second DB adapter.
import psycopg as psycopg

from .capabilities.postgres_references import PostgresReferenceIntegrity
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
from .social_read_queries import SocialReadQueries
from .social_space_commands import SocialSpaceCommands
from .social_topic_commands import SocialTopicCommands


class SocialStore(
    SocialSpaceCommands,
    SocialTopicCommands,
    SocialMessageCommands,
    CoordinationIntentCommands,
    SocialReadQueries,
    PostgresReferenceIntegrity,
    HostPostgresConnections,
):
    """Durable Social Graph records without IAM, scheduling, ranking, or effect authority."""
