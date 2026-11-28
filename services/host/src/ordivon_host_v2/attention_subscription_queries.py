"""Actor-scoped subscription listing, not priority, assignment or authorization."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Literal

import psycopg

from .collection_pagination import DEFAULT_COLLECTION_MAX_BYTES, bounded_page, validate_max_bytes
from .errors import InvalidArgumentError
from .references.actor_refs import ActorReferenceLookup

TargetKind = Literal["work", "space", "topic"]


class AttentionSubscriptionQueries:
    """Only the subscription-list read contract."""

    def __init__(
        self,
        connect: Callable[[], AbstractContextManager[psycopg.Connection[dict[str, Any]]]],
    ) -> None:
        self._connect = connect

    def list_subscriptions(
        self,
        actor_ref: str,
        *,
        target_kind: TargetKind | None = None,
        after_target_kind: str | None = None,
        after_target_ref: str | None = None,
        limit: int = 200,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise InvalidArgumentError("limit must be in [1,500]")
        if (after_target_kind is None) != (after_target_ref is None):
            raise InvalidArgumentError("after_target_kind and after_target_ref must be supplied together")
        validate_max_bytes(max_bytes)
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            ActorReferenceLookup._require_actor(conn, actor_ref)
            rows = conn.execute(
                "SELECT target_kind,target_ref,created_at,change_sequence FROM subscriptions "
                "WHERE actor_ref=%s AND (%s::text IS NULL OR target_kind=%s) "
                "AND (%s::text IS NULL OR (target_kind,target_ref)>(%s,%s)) "
                "ORDER BY target_kind,target_ref LIMIT %s",
                (
                    actor_ref,
                    target_kind,
                    target_kind,
                    after_target_kind,
                    after_target_kind,
                    after_target_ref,
                    limit + 1,
                ),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [
                {
                    "targetKind": row["target_kind"],
                    "targetRef": row["target_ref"],
                    "createdAt": row["created_at"].isoformat(),
                    "changeSequence": int(row["change_sequence"]),
                }
                for row in rows[:limit]
            ]

            def envelope(last: dict[str, Any] | None, has_more: bool) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-subscription-list",
                    "actorRef": actor_ref,
                    "hasMore": has_more,
                    "truncated": has_more,
                    "nextAfterTargetKind": last["targetKind"]
                    if has_more and last is not None
                    else None,
                    "nextAfterTargetRef": last["targetRef"]
                    if has_more and last is not None
                    else None,
                    "rankingApplied": False,
                    "truthBoundary": "actor attention-routing preferences only; not assignment, priority, ownership, or authorization",
                }

            return bounded_page(
                candidates,
                max_bytes=max_bytes,
                collection_key="subscriptions",
                envelope=envelope,
                source_has_more=sql_more,
            )
