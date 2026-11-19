"""Shared PostgreSQL record-reference checks used by Work, Social and Attention.

ActorRef is owned separately by references.actor_refs. These methods check
existing Host semantic records within the caller's existing PG transaction;
they neither authenticate callers nor grant permissions or acquire work leases.
"""

from __future__ import annotations

from typing import Any, Literal

import psycopg

from ..errors import WorkNotFound
from ..social_errors import SpaceNotFound, TopicNotFound

TargetKind = Literal["work", "space", "topic"]


class RecordReferenceLookup:
    """No connection/transaction ownership; no second registry or IAM policy."""

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
        # Only these three literals may become SQL identifiers; caller input is bound.
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
