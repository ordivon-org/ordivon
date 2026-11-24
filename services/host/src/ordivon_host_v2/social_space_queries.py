"""PostgreSQL-owned read projections for the Host Social Graph.

The SocialStore owns write transactions, command receipts and the PostgreSQL
identity. This non-authoritative query facet uses the same DSN and canonical
row validation; it does not introduce separate persistence or route policy.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

import psycopg

from .collection_pagination import (
    DEFAULT_COLLECTION_MAX_BYTES,
    DEFAULT_SPACE_MAX_BYTES,
    MIN_SPACE_MAX_BYTES,
    bounded_prefix,
    validate_max_bytes,
)
from .references.actor_refs import ActorReferenceLookup
from .references.record_refs import RecordReferenceLookup
from .social_space_records import read_space_in_tx


class SocialSpaceReadQueries:
    """Read-only PostgreSQL projections; SocialStore remains the sole write authority."""

    def __init__(
        self, connect: Callable[[], AbstractContextManager[psycopg.Connection[dict[str, Any]]]]
    ) -> None:
        self._connect = connect

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
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            return read_space_in_tx(
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
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            RecordReferenceLookup._require_space(conn, space_ref)
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
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            RecordReferenceLookup._require_space(conn, space_ref)
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
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            if actor_ref is not None:
                ActorReferenceLookup._require_actor(conn, actor_ref)
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
