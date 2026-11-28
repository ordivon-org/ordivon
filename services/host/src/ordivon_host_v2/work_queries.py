"""PostgreSQL read projections for Host Work continuity.

WorkStore is the sole mutation/receipt authority.  These queries use exactly
the existing Host transaction boundaries, stored snapshot digests and typed
pagination semantics; no alternative Work state or event log is introduced.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

import psycopg

from .canonical_json import canonical_digest
from .collection_pagination import DEFAULT_COLLECTION_MAX_BYTES, bounded_page, validate_max_bytes
from .errors import InvalidArgumentError, WorkNotFound, WorkRevisionUnavailable
from .postgres_bounds import HOST_WIRE_INT_MAX
from .work_inputs import WorkState


def read_work_in_tx(
    conn: psycopg.Connection[dict[str, Any]],
    work_ref: str,
    revision: int | None,
) -> dict[str, Any]:
    work = conn.execute(
        "SELECT work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref,created_at,updated_at "
        "FROM works WHERE work_ref=%s",
        (work_ref,),
    ).fetchone()
    if work is None:
        raise WorkNotFound(work_ref)
    current_revision = int(work["current_revision"])
    target_revision = current_revision if revision is None else revision
    # A snapshot row above the committed Work pointer is not a committed
    # Work revision, even if a damaged/imported database happens to hold it.
    # Reject before reading its contents; no positive data row can overrule
    # the authoritative revision frontier.
    if target_revision > current_revision:
        raise WorkRevisionUnavailable(work_ref, target_revision, current_revision)
    snapshot = conn.execute(
        "SELECT snapshot_digest,payload,writer_actor_ref,created_at FROM work_snapshots "
        "WHERE work_ref=%s AND revision=%s",
        (work_ref, target_revision),
    ).fetchone()
    if snapshot is None:
        raise WorkRevisionUnavailable(work_ref, target_revision, current_revision)
    payload = snapshot["payload"]
    if not isinstance(payload, dict):
        raise RuntimeError("work snapshot payload is not a PostgreSQL jsonb object")
    # Runtime Work readback is a consumer of the durable digest contract.
    # Doctor's whole-history audit cannot justify returning a stale or
    # corrupted snapshot between audits: bind content to its stored digest.
    if canonical_digest(payload) != snapshot["snapshot_digest"]:
        raise RuntimeError("durable Work snapshot payload digest differs")
    if (
        target_revision == int(work["current_revision"])
        and snapshot["snapshot_digest"] != work["current_snapshot_digest"]
    ):
        raise RuntimeError("current Work snapshot pointer digest differs")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-work",
        "workRef": work["work_ref"],
        "workKind": work["kind"],
        "state": work["state"]
        if revision is None
        else _state_at_revision(conn, work_ref, target_revision),
        "revision": target_revision,
        "snapshotDigest": snapshot["snapshot_digest"],
        "snapshot": payload,
        "writerActorRef": snapshot["writer_actor_ref"],
        "createdByActorRef": work["created_by_actor_ref"],
        "createdAt": work["created_at"].isoformat(),
        "updatedAt": work["updated_at"].isoformat(),
        "truthBoundary": "Host semantic Work continuity only; Runtime/Git/domain truth must be revalidated",
    }


def _state_at_revision(
    conn: psycopg.Connection[dict[str, Any]], work_ref: str, revision: int
) -> str:
    current = conn.execute(
        "SELECT state,current_revision FROM works WHERE work_ref=%s", (work_ref,)
    ).fetchone()
    if current is None:
        raise WorkNotFound(work_ref)
    # Historical snapshots deliberately do not pretend to reconstruct lifecycle state
    # until a dedicated work-event history is earned. Only the current revision has a
    # durable lifecycle standing.
    if int(current["current_revision"]) == revision:
        return str(current["state"])
    return "historical_state_unknown"


class WorkReadQueries:
    """Read-only Work projections with an explicit native session dependency."""

    def __init__(
        self, connect: Callable[[], AbstractContextManager[psycopg.Connection[dict[str, Any]]]]
    ) -> None:
        self._connect = connect

    def get_work(self, work_ref: str, revision: int | None = None) -> dict[str, Any]:
        if revision is not None and (
            type(revision) is not int or not 1 <= revision <= HOST_WIRE_INT_MAX
        ):
            raise InvalidArgumentError(
                "revision must be a positive PostgreSQL BIGINT within JSON safe integer range"
            )
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            return read_work_in_tx(conn, work_ref, revision)

    def list_works(
        self,
        *,
        state: str | None = None,
        limit: int = 50,
        before_updated_at: str | None = None,
        before_work_ref: str | None = None,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        # A pagination budget is a typed integer, not numeric equality:
        # True == 1 and 1.0 == 1 must not cross the PostgreSQL boundary.
        if type(limit) is not int or not 1 <= limit <= 200:
            raise InvalidArgumentError("limit must be in [1,200]")
        if state is not None and state not in {item.value for item in WorkState}:
            raise InvalidArgumentError("unknown Work state")
        if (before_updated_at is None) != (before_work_ref is None):
            raise InvalidArgumentError("before_updated_at and before_work_ref must be supplied together")
        validate_max_bytes(max_bytes)
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            rows = conn.execute(
                "SELECT work_ref,kind,state,current_revision,current_snapshot_digest,updated_at "
                "FROM works WHERE (%s::text IS NULL OR state=%s) "
                "AND (%s::timestamptz IS NULL OR (updated_at,work_ref) < (%s::timestamptz,%s)) "
                "ORDER BY updated_at DESC,work_ref DESC LIMIT %s",
                (state, state, before_updated_at, before_updated_at, before_work_ref, limit + 1),
            ).fetchall()
            sql_more = len(rows) > limit
            candidates = [
                {
                    "workRef": row["work_ref"],
                    "workKind": row["kind"],
                    "state": row["state"],
                    "revision": int(row["current_revision"]),
                    "snapshotDigest": row["current_snapshot_digest"],
                    "updatedAt": row["updated_at"].isoformat(),
                }
                for row in rows[:limit]
            ]

            def envelope(last: dict[str, Any] | None, has_more: bool) -> dict[str, Any]:
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-work-list",
                    "hasMore": has_more,
                    "nextCursor": {
                        "beforeUpdatedAt": last["updatedAt"],
                        "beforeWorkRef": last["workRef"],
                    }
                    if has_more and last is not None
                    else None,
                    "rankingApplied": False,
                    "truthBoundary": "compact point-in-time Work inventory; not priority, assignment, Runtime activity, or domain currentness",
                }

            return bounded_page(
                candidates,
                max_bytes=max_bytes,
                collection_key="works",
                envelope=envelope,
                source_has_more=sql_more,
            )
