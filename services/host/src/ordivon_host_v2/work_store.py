from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .canonical import canonical_digest
from .errors import ConflictError
from .social_work import (
    ActorRefInput,
    WorkCreateInput,
    WorkRelationInput,
    WorkRelationKind,
    WorkSnapshotInput,
    WorkState,
)


class WorkNotFound(RuntimeError):
    pass


class ActorRefNotFound(RuntimeError):
    pass


class WorkStore:
    """Greenfield Social Work Fabric Work Graph authority.

    This store owns durable Host semantic work continuity only. It deliberately does not
    inspect Runtime, Git, domain truth, social priority, assignment, or EffectAuthority.
    """

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def declare_actor(self, value: ActorRefInput, *, client_request_id: str) -> dict[str, Any]:
        request = {"operation": "actor.declare", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "actor.declare", request_digest)
            if replay is not None:
                return replay
            row = conn.execute(
                "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES (%s,%s) "
                "ON CONFLICT (actor_ref) DO NOTHING RETURNING actor_ref,actor_kind,created_at",
                (value.actor_ref, value.actor_kind.value),
            ).fetchone()
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT actor_ref,actor_kind,created_at FROM actor_refs WHERE actor_ref=%s",
                    (value.actor_ref,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("actor declaration disappeared")
                if row["actor_kind"] != value.actor_kind.value:
                    raise ConflictError("actor_ref already exists with a different actor_kind")
                admission = "existing"
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-actor-ref",
                "admission": admission,
                "actorRef": row["actor_ref"],
                "actorKind": row["actor_kind"],
                "createdAt": row["created_at"].isoformat(),
                "truthBoundary": "Host-stored stable actor reference only; not authenticated identity or authorization",
            }
            self._record_receipt(conn, client_request_id, "actor.declare", request_digest, result)
            return result

    def create_work(self, value: WorkCreateInput, *, client_request_id: str) -> dict[str, Any]:
        payload = value.initial_snapshot.canonical_payload()
        snapshot_digest = canonical_digest(payload)
        request = {
            "operation": "work.create",
            "workRef": value.work_ref,
            "kind": value.kind,
            "actorRef": value.actor_ref,
            "initialSnapshot": payload,
        }
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "work.create", request_digest)
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            current = conn.execute(
                "SELECT work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref,created_at,updated_at "
                "FROM works WHERE work_ref=%s FOR UPDATE",
                (value.work_ref,),
            ).fetchone()
            admission = "committed"
            if current is None:
                conn.execute(
                    "INSERT INTO works(work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref) "
                    "VALUES (%s,%s,'open',1,%s,%s)",
                    (value.work_ref, value.kind, snapshot_digest, value.actor_ref),
                )
                conn.execute(
                    "INSERT INTO work_snapshots(work_ref,revision,snapshot_digest,payload,writer_actor_ref) "
                    "VALUES (%s,1,%s,%s,%s)",
                    (value.work_ref, snapshot_digest, Jsonb(payload), value.actor_ref),
                )
            else:
                initial = conn.execute(
                    "SELECT snapshot_digest,writer_actor_ref FROM work_snapshots WHERE work_ref=%s AND revision=1",
                    (value.work_ref,),
                ).fetchone()
                if (
                    current["kind"] != value.kind
                    or initial is None
                    or initial["snapshot_digest"] != snapshot_digest
                    or initial["writer_actor_ref"] != value.actor_ref
                ):
                    raise ConflictError("work_ref already exists with different initial semantics")
                admission = "existing"
            result = self._get_work_in_tx(conn, value.work_ref, None)
            result["admission"] = admission
            self._record_receipt(conn, client_request_id, "work.create", request_digest, result)
            return result

    def commit_snapshot(
        self,
        work_ref: str,
        *,
        expected_revision: int,
        snapshot: WorkSnapshotInput,
        actor_ref: str,
        state: WorkState = WorkState.OPEN,
        client_request_id: str,
    ) -> dict[str, Any]:
        payload = snapshot.canonical_payload()
        snapshot_digest = canonical_digest(payload)
        request = {
            "operation": "work.snapshot.commit",
            "workRef": work_ref,
            "expectedRevision": expected_revision,
            "snapshot": payload,
            "actorRef": actor_ref,
            "state": state.value,
        }
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(
                conn, client_request_id, "work.snapshot.commit", request_digest
            )
            if replay is not None:
                return replay
            self._require_actor(conn, actor_ref)
            current = conn.execute(
                "SELECT work_ref,state,current_revision FROM works WHERE work_ref=%s FOR UPDATE",
                (work_ref,),
            ).fetchone()
            if current is None:
                raise WorkNotFound(work_ref)
            current_revision = int(current["current_revision"])
            next_revision = expected_revision + 1
            if current_revision == next_revision:
                prior = conn.execute(
                    "SELECT snapshot_digest,writer_actor_ref FROM work_snapshots "
                    "WHERE work_ref=%s AND revision=%s",
                    (work_ref, next_revision),
                ).fetchone()
                if (
                    prior is not None
                    and prior["snapshot_digest"] == snapshot_digest
                    and prior["writer_actor_ref"] == actor_ref
                    and current["state"] == state.value
                ):
                    result = self._get_work_in_tx(conn, work_ref, next_revision)
                    result["admission"] = "existing"
                    self._record_receipt(
                        conn,
                        client_request_id,
                        "work.snapshot.commit",
                        request_digest,
                        result,
                    )
                    return result
            if current_revision != expected_revision:
                raise ConflictError(
                    f"expected revision {expected_revision}, current revision is {current_revision}"
                )
            if current["state"] != WorkState.OPEN.value:
                raise ConflictError("terminal work cannot be checkpointed or reopened")
            updated = conn.execute(
                "UPDATE works SET state=%s,current_revision=%s,current_snapshot_digest=%s,updated_at=clock_timestamp() "
                "WHERE work_ref=%s AND current_revision=%s AND state='open' RETURNING work_ref",
                (state.value, next_revision, snapshot_digest, work_ref, expected_revision),
            ).fetchone()
            if updated is None:
                raise ConflictError("same-revision transition lost concurrency race")
            conn.execute(
                "INSERT INTO work_snapshots(work_ref,revision,snapshot_digest,payload,writer_actor_ref) "
                "VALUES (%s,%s,%s,%s,%s)",
                (work_ref, next_revision, snapshot_digest, Jsonb(payload), actor_ref),
            )
            result = self._get_work_in_tx(conn, work_ref, next_revision)
            result["admission"] = "committed"
            self._record_receipt(
                conn, client_request_id, "work.snapshot.commit", request_digest, result
            )
            return result

    def get_work(self, work_ref: str, revision: int | None = None) -> dict[str, Any]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            return self._get_work_in_tx(conn, work_ref, revision)

    def list_works(
        self,
        *,
        state: str | None = None,
        limit: int = 50,
        before_updated_at: str | None = None,
        before_work_ref: str | None = None,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be in [1,200]")
        if state is not None and state not in {item.value for item in WorkState}:
            raise ValueError("unknown Work state")
        if (before_updated_at is None) != (before_work_ref is None):
            raise ValueError("before_updated_at and before_work_ref must be supplied together")
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            rows = conn.execute(
                "SELECT work_ref,kind,state,current_revision,current_snapshot_digest,updated_at "
                "FROM works WHERE (%s::text IS NULL OR state=%s) "
                "AND (%s::timestamptz IS NULL OR (updated_at,work_ref) < (%s::timestamptz,%s)) "
                "ORDER BY updated_at DESC,work_ref DESC LIMIT %s",
                (
                    state,
                    state,
                    before_updated_at,
                    before_updated_at,
                    before_work_ref,
                    limit + 1,
                ),
            ).fetchall()
            has_more = len(rows) > limit
            page = rows[:limit]
            cursor = None
            if has_more and page:
                cursor = {
                    "beforeUpdatedAt": page[-1]["updated_at"].isoformat(),
                    "beforeWorkRef": page[-1]["work_ref"],
                }
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-work-list",
                "works": [
                    {
                        "workRef": row["work_ref"],
                        "workKind": row["kind"],
                        "state": row["state"],
                        "revision": int(row["current_revision"]),
                        "snapshotDigest": row["current_snapshot_digest"],
                        "updatedAt": row["updated_at"].isoformat(),
                    }
                    for row in page
                ],
                "hasMore": has_more,
                "nextCursor": cursor,
                "rankingApplied": False,
                "truthBoundary": "compact point-in-time Work inventory; not priority, assignment, Runtime activity, or domain currentness",
            }

    def add_relation(self, value: WorkRelationInput, *, client_request_id: str) -> dict[str, Any]:
        value.validate_not_self_relation()
        request = {"operation": "work.relation.add", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(
                conn, client_request_id, "work.relation.add", request_digest
            )
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            self._require_work(conn, value.source_work_ref)
            self._require_work(conn, value.target_work_ref)
            if value.relation in {WorkRelationKind.PARENT_OF, WorkRelationKind.DEPENDS_ON}:
                self._reject_cycle(conn, value)
            row = conn.execute(
                "INSERT INTO work_relations(source_work_ref,relation,target_work_ref,created_by_actor_ref) "
                "VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING created_at",
                (
                    value.source_work_ref,
                    value.relation.value,
                    value.target_work_ref,
                    value.actor_ref,
                ),
            ).fetchone()
            admission = "committed" if row is not None else "existing"
            existing = conn.execute(
                "SELECT source_work_ref,relation,target_work_ref,created_by_actor_ref,created_at "
                "FROM work_relations WHERE source_work_ref=%s AND relation=%s AND target_work_ref=%s",
                (value.source_work_ref, value.relation.value, value.target_work_ref),
            ).fetchone()
            if existing is None:
                raise RuntimeError("work relation disappeared")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-work-relation",
                "admission": admission,
                "sourceWorkRef": existing["source_work_ref"],
                "relation": existing["relation"],
                "targetWorkRef": existing["target_work_ref"],
                "createdByActorRef": existing["created_by_actor_ref"],
                "createdAt": existing["created_at"].isoformat(),
                "truthBoundary": "Host semantic work relation only; no priority, scheduling, ownership, or EffectAuthority",
            }
            self._record_receipt(
                conn, client_request_id, "work.relation.add", request_digest, result
            )
            return result

    def list_relations(self, work_ref: str) -> dict[str, Any]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_work(conn, work_ref)
            rows = conn.execute(
                "SELECT source_work_ref,relation,target_work_ref,created_by_actor_ref,created_at "
                "FROM work_relations WHERE source_work_ref=%s OR target_work_ref=%s "
                "ORDER BY relation,source_work_ref,target_work_ref",
                (work_ref, work_ref),
            ).fetchall()
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-work-relations",
                "workRef": work_ref,
                "relations": [
                    {
                        "sourceWorkRef": row["source_work_ref"],
                        "relation": row["relation"],
                        "targetWorkRef": row["target_work_ref"],
                        "createdByActorRef": row["created_by_actor_ref"],
                        "createdAt": row["created_at"].isoformat(),
                    }
                    for row in rows
                ],
                "truthBoundary": "Host semantic relations only; foreign owner truth is not evaluated",
            }

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

    def _reject_cycle(
        self, conn: psycopg.Connection[dict[str, Any]], value: WorkRelationInput
    ) -> None:
        # Adding source -> target creates a cycle iff target can already reach source
        # through edges of the same relation kind.
        found = conn.execute(
            "WITH RECURSIVE reachable(work_ref) AS ("
            " SELECT target_work_ref FROM work_relations WHERE source_work_ref=%s AND relation=%s"
            " UNION"
            " SELECT r.target_work_ref FROM work_relations r JOIN reachable x "
            " ON r.source_work_ref=x.work_ref WHERE r.relation=%s"
            ") SELECT 1 FROM reachable WHERE work_ref=%s LIMIT 1",
            (
                value.target_work_ref,
                value.relation.value,
                value.relation.value,
                value.source_work_ref,
            ),
        ).fetchone()
        if found is not None:
            raise ConflictError(f"{value.relation.value} relation would create a cycle")

    def _get_work_in_tx(
        self,
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
        target_revision = int(work["current_revision"]) if revision is None else revision
        snapshot = conn.execute(
            "SELECT snapshot_digest,payload,writer_actor_ref,created_at FROM work_snapshots "
            "WHERE work_ref=%s AND revision=%s",
            (work_ref, target_revision),
        ).fetchone()
        if snapshot is None:
            raise ConflictError(f"work {work_ref} has no revision {target_revision}")
        payload = snapshot["payload"]
        if not isinstance(payload, dict):
            raise RuntimeError("work snapshot payload is not a PostgreSQL jsonb object")
        return {
            "schemaVersion": 1,
            "kind": "ordivon.host-work",
            "workRef": work["work_ref"],
            "workKind": work["kind"],
            "state": work["state"]
            if revision is None
            else self._state_at_revision(conn, work_ref, target_revision),
            "revision": target_revision,
            "snapshotDigest": snapshot["snapshot_digest"],
            "snapshot": payload,
            "writerActorRef": snapshot["writer_actor_ref"],
            "createdByActorRef": work["created_by_actor_ref"],
            "createdAt": work["created_at"].isoformat(),
            "updatedAt": work["updated_at"].isoformat(),
            "truthBoundary": "Host semantic Work continuity only; Runtime/Git/domain truth must be revalidated",
        }

    @staticmethod
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
            "UPDATE command_receipts SET response=%s "
            "WHERE client_request_id=%s AND operation=%s AND request_digest=%s AND response IS NULL "
            "RETURNING client_request_id",
            (Jsonb(result), client_request_id, operation, request_digest),
        ).fetchone()
        if updated is None:
            raise RuntimeError("idempotency claim could not be finalized")
