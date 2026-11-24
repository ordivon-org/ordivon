"""Stable Social ActorRef declarations and existence checks, never IAM.

ActorRefs are references in Host's semantic graph. Authentication/authorization
remains at the actual HTTP/Owner/Security boundary; no ownership or role grant
is inferred from registration or presence of a reference.
"""

from __future__ import annotations

from typing import Any

import psycopg

from ..canonical_json import canonical_digest
from ..command_receipts import claim_command_receipt, record_command_receipt
from ..errors import ActorRefNotFound, ConflictError
from .actor_inputs import ActorRefInput


class ActorReferenceLookup:
    """Shared existing-actor precondition, not an access-control decision."""

    @staticmethod
    def _require_actor(conn: psycopg.Connection[dict[str, Any]], actor_ref: str) -> None:
        if (
            conn.execute("SELECT 1 FROM actor_refs WHERE actor_ref=%s", (actor_ref,)).fetchone()
            is None
        ):
            raise ActorRefNotFound(actor_ref)


class ActorReferenceRegistry(ActorReferenceLookup):
    """Original idempotent actor.declare implementation without Work ownership."""

    def declare_actor(self, value: ActorRefInput, *, client_request_id: str) -> dict[str, Any]:
        request = {"operation": "actor.declare", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with self._connect() as conn, conn.transaction():
            replay = claim_command_receipt(conn, client_request_id, "actor.declare", request_digest)
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
            record_command_receipt(conn, client_request_id, "actor.declare", request_digest, result)
            return result
