from __future__ import annotations

from typing import Any

# Existing tests/tool consumers monkeypatch the shared psycopg module here.
import psycopg as psycopg
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from .canonical_json import canonical_digest
from .collection_pagination import DEFAULT_COLLECTION_MAX_BYTES
from .errors import ConflictError, InvalidArgumentError, WorkNotFound
from .postgres_bounds import HOST_WIRE_INT_MAX
from .postgres_connections import HostPostgresConnections
from .references.actor_refs import ActorReferenceLookup
from .work_inputs import (
    WorkCreateInput,
    WorkRelationInput,
    WorkSnapshotInput,
    WorkState,
)
from .work_queries import WorkReadQueries, read_work_in_tx
from .work_receipt_roots import claim_work_receipt
from .work_receipt_writer import record_work_receipt
from .work_relation_commands import WorkRelationCommands
from .work_revision_logic import next_work_revision


class WorkStore(HostPostgresConnections):
    """Greenfield Social Work Fabric Work Graph authority.

    This store owns durable Host semantic work continuity only. It deliberately does not
    inspect Runtime, Git, domain truth, social priority, assignment, or EffectAuthority.
    """

    def __init__(
        self,
        dsn: str,
        *,
        pool: ConnectionPool | None = None,
        compact_work_receipts: bool = False,
    ) -> None:
        super().__init__(dsn, pool=pool)
        if type(compact_work_receipts) is not bool:
            raise ValueError("compact_work_receipts must be boolean")
        self._compact_work_receipts = compact_work_receipts

    def _record_work_receipt(
        self,
        conn: psycopg.Connection[dict[str, Any]],
        client_request_id: str,
        operation: str,
        request_digest: str,
        result: dict[str, Any],
    ) -> None:
        record_work_receipt(
            conn,
            client_request_id,
            operation,
            request_digest,
            result,
            compact_requested=self._compact_work_receipts,
        )

    def get_work(self, work_ref: str, revision: int | None = None) -> dict[str, Any]:
        return WorkReadQueries(self._connect).get_work(work_ref, revision)

    def list_works(
        self,
        *,
        state: str | None = None,
        limit: int = 50,
        before_updated_at: str | None = None,
        before_work_ref: str | None = None,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        return WorkReadQueries(self._connect).list_works(
            state=state,
            limit=limit,
            before_updated_at=before_updated_at,
            before_work_ref=before_work_ref,
            max_bytes=max_bytes,
        )

    def add_relation(self, value: WorkRelationInput, *, client_request_id: str) -> dict[str, Any]:
        """Internal Work graph command, not an extra public MCP route."""
        return WorkRelationCommands(self._connect).add_relation(
            value, client_request_id=client_request_id
        )

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
        with self._connect() as conn, conn.transaction():
            replay = claim_work_receipt(
                conn,
                client_request_id,
                "work.create",
                request_digest,
                work_ref=value.work_ref,
                work_kind=value.kind,
            )
            if replay is not None:
                return replay
            ActorReferenceLookup._require_actor(conn, value.actor_ref)
            # PostgreSQL's unique WorkRef arbiter is the creation linearization
            # point. SELECT-before-INSERT cannot arbitrate concurrent identical
            # requests: both can observe absence and leak UniqueViolation.
            # ON CONFLICT waits for the winning transaction and returns no row
            # only after its complete work+revision-one snapshot is visible.
            inserted = conn.execute(
                "INSERT INTO works(work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref) "
                "VALUES (%s,%s,'open',1,%s,%s) "
                "ON CONFLICT (work_ref) DO NOTHING RETURNING work_ref",
                (value.work_ref, value.kind, snapshot_digest, value.actor_ref),
            ).fetchone()
            admission = "committed"
            if inserted is not None:
                conn.execute(
                    "INSERT INTO work_snapshots(work_ref,revision,snapshot_digest,payload,writer_actor_ref) "
                    "VALUES (%s,1,%s,%s,%s)",
                    (value.work_ref, snapshot_digest, Jsonb(payload), value.actor_ref),
                )
            else:
                # A conflicting creator may have just committed revision one.
                # A new READ COMMITTED statement must re-read under row lock;
                # the first SELECT is not evidence of absence across writers.
                current = conn.execute(
                    "SELECT work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref,created_at,updated_at "
                    "FROM works WHERE work_ref=%s FOR UPDATE",
                    (value.work_ref,),
                ).fetchone()
                if current is None:
                    raise RuntimeError("work_ref disappeared after insert conflict")
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
            result = read_work_in_tx(conn, value.work_ref, None)
            result["admission"] = admission
            self._record_work_receipt(
                conn, client_request_id, "work.create", request_digest, result
            )
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
        # Revision is a typed CAS identity, not Python numeric equality:
        # bool is an int subclass, and 1.0 compares equal to 1.
        if type(expected_revision) is not int or not 1 <= expected_revision < HOST_WIRE_INT_MAX:
            raise InvalidArgumentError(
                "expected_revision must be a positive PostgreSQL BIGINT predecessor within JSON safe integer range"
            )
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
        with self._connect() as conn, conn.transaction():
            replay = claim_work_receipt(
                conn,
                client_request_id,
                "work.snapshot.commit",
                request_digest,
                work_ref=work_ref,
                revision=expected_revision + 1,
                snapshot_digest=snapshot_digest,
                actor_ref=actor_ref,
                state=state.value,
            )
            if replay is not None:
                return replay
            ActorReferenceLookup._require_actor(conn, actor_ref)
            current = conn.execute(
                "SELECT work_ref,state,current_revision FROM works WHERE work_ref=%s FOR UPDATE",
                (work_ref,),
            ).fetchone()
            if current is None:
                raise WorkNotFound(work_ref)
            current_revision = int(current["current_revision"])
            next_revision = next_work_revision(expected_revision)
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
                    result = read_work_in_tx(conn, work_ref, next_revision)
                    result["admission"] = "existing"
                    self._record_work_receipt(
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
            result = read_work_in_tx(conn, work_ref, next_revision)
            result["admission"] = "committed"
            self._record_work_receipt(
                conn, client_request_id, "work.snapshot.commit", request_digest, result
            )
            return result
