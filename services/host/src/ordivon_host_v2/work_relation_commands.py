from __future__ import annotations

from typing import Any

import psycopg

from .canonical_json import canonical_digest
from .command_receipts import claim_command_receipt, record_command_receipt
from .errors import ConflictError
from .work_inputs import WorkRelationInput, WorkRelationKind


class WorkRelationCommands:
    """Work relation mutations in the owning WorkStore transaction boundary.

    WorkStore supplies dsn, _require_actor and _require_work. This unit adds
    no second datastore, MCP surface, or scheduling/assignment authority.
    """

    def add_relation(self, value: WorkRelationInput, *, client_request_id: str) -> dict[str, Any]:
        value.validate_not_self_relation()
        request = {"operation": "work.relation.add", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with self._connect() as conn, conn.transaction():
            replay = claim_command_receipt(
                conn, client_request_id, "work.relation.add", request_digest
            )
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            self._require_work(conn, value.source_work_ref)
            self._require_work(conn, value.target_work_ref)
            if value.relation in {WorkRelationKind.PARENT_OF, WorkRelationKind.DEPENDS_ON}:
                # The reachability check and INSERT must be one serialized
                # transaction per DAG relation kind. Under READ COMMITTED, two
                # concurrent opposite edges could each validate an empty graph.
                # PostgreSQL releases this native transaction lock on commit
                # and rollback; unrelated relation kinds remain independent.
                relation_lock = 1 if value.relation == WorkRelationKind.PARENT_OF else 2
                conn.execute("SELECT pg_advisory_xact_lock(%s,%s)", (0x4F524456, relation_lock))
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
            record_command_receipt(
                conn, client_request_id, "work.relation.add", request_digest, result
            )
            return result

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
