from __future__ import annotations

from typing import Any

import psycopg

from .coordination_intent_commands import CoordinationIntentCommands
from .errors import ActorRefNotFound, WorkNotFound
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
):
    """Durable Social Graph records without IAM, scheduling, ranking, or effect authority."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

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
    def _require_topic(
        conn: psycopg.Connection[dict[str, Any]], topic_ref: str, *, for_no_key_update: bool = False
    ) -> dict[str, Any]:
        row = conn.execute(
            "SELECT topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at "
            "FROM topics WHERE topic_ref=%s" + (" FOR NO KEY UPDATE" if for_no_key_update else ""),
            (topic_ref,),
        ).fetchone()
        if row is None:
            raise TopicNotFound(topic_ref)
        return row
