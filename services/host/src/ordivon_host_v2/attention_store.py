from __future__ import annotations

from typing import Any

import psycopg

from .attention_delta_queries import AttentionDeltaQueries
from .attention_reentry_queries import AttentionReentryQueries
from .attention_subscription_queries import AttentionSubscriptionQueries
from .attention_subscription_queries import TargetKind as TargetKind
from .canonical_json import canonical_digest
from .collection_pagination import DEFAULT_COLLECTION_MAX_BYTES
from .command_receipts import claim_command_receipt, record_command_receipt
from .errors import ActorRefNotFound, ConflictError
from .postgres_bounds import HOST_WIRE_INT_MAX
from .postgres_connections import HostPostgresConnections
from .references.actor_refs import ActorReferenceLookup
from .references.record_refs import RecordReferenceLookup


class AttentionStore(HostPostgresConnections):
    """Actor-scoped navigation compiled directly from owner rows, not a second event bus."""

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
        return AttentionSubscriptionQueries(self._connect).list_subscriptions(
            actor_ref, target_kind=target_kind, after_target_kind=after_target_kind,
            after_target_ref=after_target_ref, limit=limit, max_bytes=max_bytes,
        )

    def get(
        self, actor_ref: str, *, limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        return AttentionDeltaQueries(self._connect).get(
            actor_ref, limit=limit, max_bytes=max_bytes,
        )

    def delta(
        self, actor_ref: str, *, after_sequence: int, limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        return AttentionDeltaQueries(self._connect).delta(
            actor_ref, after_sequence=after_sequence, limit=limit, max_bytes=max_bytes,
        )

    def reentry(
        self, actor_ref: str, *, after_sequence: int | None = None,
        limit: int = 100, max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        return AttentionReentryQueries(self._connect).reentry(
            actor_ref, after_sequence=after_sequence, limit=limit, max_bytes=max_bytes,
        )

    def follow(
        self,
        *,
        actor_ref: str,
        target_kind: TargetKind,
        target_ref: str,
        client_request_id: str,
    ) -> dict[str, Any]:
        # Desired-state command: natural-key membership is the replay contract. A later
        # unfollow must not make a same-payload follow replay an obsolete historical receipt.
        _ = client_request_id
        with self._connect() as conn, conn.transaction():
            # Serialize opposing desired-state commands for the same actor.
            # Without this arbiter, a competing unfollow can remove the row
            # between INSERT ... ON CONFLICT DO NOTHING and its fallback SELECT.
            self._lock_actor(conn, actor_ref)
            RecordReferenceLookup._require_target(conn, target_kind, target_ref)
            row = conn.execute(
                "INSERT INTO subscriptions(actor_ref,target_kind,target_ref) VALUES (%s,%s,%s) "
                "ON CONFLICT DO NOTHING RETURNING actor_ref,target_kind,target_ref,created_at,change_sequence",
                (actor_ref, target_kind, target_ref),
            ).fetchone()
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT actor_ref,target_kind,target_ref,created_at,change_sequence FROM subscriptions "
                    "WHERE actor_ref=%s AND target_kind=%s AND target_ref=%s",
                    (actor_ref, target_kind, target_ref),
                ).fetchone()
                if row is None:
                    raise RuntimeError("subscription disappeared")
                admission = "existing"
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-subscription",
                "admission": admission,
                "actorRef": row["actor_ref"],
                "targetKind": row["target_kind"],
                "targetRef": row["target_ref"],
                "createdAt": row["created_at"].isoformat(),
                "changeSequence": int(row["change_sequence"]),
                "truthBoundary": "attention routing preference only; not assignment, priority, ownership, or authorization",
            }
            return result

    def unfollow(
        self,
        *,
        actor_ref: str,
        target_kind: TargetKind,
        target_ref: str,
        client_request_id: str,
    ) -> dict[str, Any]:
        # Desired-state command; deleting an absent natural key is already replay-safe.
        _ = client_request_id
        with self._connect() as conn, conn.transaction():
            self._lock_actor(conn, actor_ref)
            deleted = conn.execute(
                "DELETE FROM subscriptions WHERE actor_ref=%s AND target_kind=%s AND target_ref=%s "
                "RETURNING actor_ref",
                (actor_ref, target_kind, target_ref),
            ).fetchone()
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-subscription-unfollow",
                "admission": "committed" if deleted is not None else "existing",
                "actorRef": actor_ref,
                "targetKind": target_kind,
                "targetRef": target_ref,
                "truthBoundary": "attention routing preference only",
            }
            return result

    def ack(self, actor_ref: str, *, cursor: int, client_request_id: str) -> dict[str, Any]:
        if type(cursor) is not int or not 0 <= cursor <= HOST_WIRE_INT_MAX:
            raise ValueError("cursor must be a non-negative exact integer within JSON safe integer range")
        request = {"operation": "attention.ack", "actorRef": actor_ref, "cursor": cursor}
        request_digest = canonical_digest(request)
        with self._connect() as conn, conn.transaction():
            replay = claim_command_receipt(conn, client_request_id, "attention.ack", request_digest)
            if replay is not None:
                return replay
            ActorReferenceLookup._require_actor(conn, actor_ref)
            high = int(
                conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[
                    "value"
                ]
            )
            if cursor > high:
                raise ConflictError(
                    "attention cursor cannot acknowledge beyond current change horizon"
                )
            # PG18 returns the actual predecessor at the unique-key UPSERT
            # linearization point, even when a concurrent first ACK was invisible
            # to a preceding SELECT. The monotonic predicate remains authoritative.
            updated = conn.execute(
                "INSERT INTO attention_cursors(actor_ref,cursor) VALUES (%s,%s) "
                "ON CONFLICT (actor_ref) DO UPDATE "
                "SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp() "
                "WHERE attention_cursors.cursor <= EXCLUDED.cursor "
                "RETURNING COALESCE(OLD.cursor,0) AS previous_cursor, NEW.cursor AS cursor",
                (actor_ref, cursor),
            ).fetchone()
            if updated is None:
                raise ConflictError("attention cursor cannot move backwards")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-attention-ack",
                "actorRef": actor_ref,
                "previousCursor": int(updated["previous_cursor"]),
                "cursor": int(updated["cursor"]),
                "truthBoundary": "navigation acknowledgement only; not evidence that message content was semantically accepted",
            }
            record_command_receipt(conn, client_request_id, "attention.ack", request_digest, result)
            return result

    @staticmethod
    def _lock_actor(conn: psycopg.Connection[dict[str, Any]], actor_ref: str) -> None:
        """Order follow/unfollow for one ActorRef using an existing PostgreSQL row.

        Neither a synthetic advisory-lock key nor a subscription tombstone table
        is required. Different actors may still update concurrently.
        """
        if (
            conn.execute(
                "SELECT 1 FROM actor_refs WHERE actor_ref=%s FOR UPDATE", (actor_ref,)
            ).fetchone()
            is None
        ):
            raise ActorRefNotFound(actor_ref)
