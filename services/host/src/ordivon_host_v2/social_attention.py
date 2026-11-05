from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from .attention_projections import AttentionReadProjections
from .attention_projections import TargetKind as TargetKind
from .canonical_json import canonical_digest
from .command_receipts import claim_command_receipt, record_command_receipt
from .errors import ConflictError
from .social_store import SpaceNotFound, TopicNotFound
from .work_store import ActorRefNotFound, WorkNotFound


class AttentionStore(AttentionReadProjections):
    """Actor-scoped navigation compiled directly from owner rows, not a second event bus."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

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
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            self._require_actor(conn, actor_ref)
            self._require_target(conn, target_kind, target_ref)
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
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            self._require_actor(conn, actor_ref)
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
        if cursor < 0:
            raise ValueError("cursor must be non-negative")
        request = {"operation": "attention.ack", "actorRef": actor_ref, "cursor": cursor}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = claim_command_receipt(conn, client_request_id, "attention.ack", request_digest)
            if replay is not None:
                return replay
            self._require_actor(conn, actor_ref)
            high = int(
                conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[
                    "value"
                ]
            )
            if cursor > high:
                raise ConflictError(
                    "attention cursor cannot acknowledge beyond current change horizon"
                )
            current = conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s FOR UPDATE", (actor_ref,)
            ).fetchone()
            previous = 0 if current is None else int(current["cursor"])
            if cursor < previous:
                raise ConflictError("attention cursor cannot move backwards")
            updated = conn.execute(
                "INSERT INTO attention_cursors(actor_ref,cursor) VALUES (%s,%s) "
                "ON CONFLICT (actor_ref) DO UPDATE "
                "SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp() "
                "WHERE attention_cursors.cursor <= EXCLUDED.cursor "
                "RETURNING cursor",
                (actor_ref, cursor),
            ).fetchone()
            if updated is None:
                raise ConflictError("attention cursor cannot move backwards")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-attention-ack",
                "actorRef": actor_ref,
                "previousCursor": previous,
                "cursor": cursor,
                "truthBoundary": "navigation acknowledgement only; not evidence that message content was semantically accepted",
            }
            record_command_receipt(conn, client_request_id, "attention.ack", request_digest, result)
            return result

    @staticmethod
    def _require_actor(conn: psycopg.Connection[dict[str, Any]], actor_ref: str) -> None:
        if (
            conn.execute("SELECT 1 FROM actor_refs WHERE actor_ref=%s", (actor_ref,)).fetchone()
            is None
        ):
            raise ActorRefNotFound(actor_ref)

    @staticmethod
    def _require_target(
        conn: psycopg.Connection[dict[str, Any]], target_kind: TargetKind, target_ref: str
    ) -> None:
        table = {"work": "works", "space": "spaces", "topic": "topics"}[target_kind]
        column = {"work": "work_ref", "space": "space_ref", "topic": "topic_ref"}[target_kind]
        if (
            conn.execute(f"SELECT 1 FROM {table} WHERE {column}=%s", (target_ref,)).fetchone()
            is None
        ):
            if target_kind == "work":
                raise WorkNotFound(target_ref)
            if target_kind == "space":
                raise SpaceNotFound(target_ref)
            raise TopicNotFound(target_ref)
