"""PostgreSQL-backed referential integrity for Host semantic records.

One Host database, one caller-owned transaction. These checks only establish
whether Social Work Fabric records exist; ActorRef is NOT an authenticated
Principal and existence never grants access, ownership, or effect authority.

The topic row lock is a consistency primitive: acquiring FOR NO KEY UPDATE
before allocating a Message sequence preserves committed same-Topic ordering.
"""

from __future__ import annotations

from typing import Any, Literal

import psycopg

from ..errors import ActorRefNotFound, WorkNotFound
from ..social_errors import SpaceNotFound, TopicNotFound

TargetKind = Literal["work", "space", "topic"]


class PostgresReferenceIntegrity:
    """Reference-check capability reused by Work, Social, and Attention stores.

    This mixin owns no connection, no transactions, and no authority decisions.
    Each domain command retains its own operation-specific invariants.
    """

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
        conn: psycopg.Connection[dict[str, Any]],
        topic_ref: str,
        *,
        for_no_key_update: bool = False,
    ) -> dict[str, Any]:
        row = conn.execute(
            "SELECT topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at "
            "FROM topics WHERE topic_ref=%s" + (" FOR NO KEY UPDATE" if for_no_key_update else ""),
            (topic_ref,),
        ).fetchone()
        if row is None:
            raise TopicNotFound(topic_ref)
        return row

    @staticmethod
    def _require_target(
        conn: psycopg.Connection[dict[str, Any]],
        target_kind: TargetKind,
        target_ref: str,
    ) -> None:
        # Literal-only mapping: caller input never becomes executable SQL text.
        targets: dict[str, tuple[str, str, type[Exception]]] = {
            "work": ("works", "work_ref", WorkNotFound),
            "space": ("spaces", "space_ref", SpaceNotFound),
            "topic": ("topics", "topic_ref", TopicNotFound),
        }
        if target_kind not in targets:
            raise ValueError(f"unsupported Host attention target kind: {target_kind}")
        table, column, missing = targets[target_kind]
        if (
            conn.execute(f"SELECT 1 FROM {table} WHERE {column}=%s", (target_ref,)).fetchone()
            is None
        ):
            raise missing(target_ref)
