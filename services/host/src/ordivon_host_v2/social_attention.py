from __future__ import annotations

from typing import Any, Literal

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .canonical import canonical_digest
from .errors import ConflictError
from .social_store import SpaceNotFound, TopicNotFound
from .work_store import ActorRefNotFound, WorkNotFound

TargetKind = Literal["work", "space", "topic"]


class AttentionStore:
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
        request = {
            "operation": "subscription.follow",
            "actorRef": actor_ref,
            "targetKind": target_kind,
            "targetRef": target_ref,
        }
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(
                conn, client_request_id, "subscription.follow", request_digest
            )
            if replay is not None:
                return replay
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
            self._record_receipt(
                conn, client_request_id, "subscription.follow", request_digest, result
            )
            return result

    def unfollow(
        self,
        *,
        actor_ref: str,
        target_kind: TargetKind,
        target_ref: str,
        client_request_id: str,
    ) -> dict[str, Any]:
        request = {
            "operation": "subscription.unfollow",
            "actorRef": actor_ref,
            "targetKind": target_kind,
            "targetRef": target_ref,
        }
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(
                conn, client_request_id, "subscription.unfollow", request_digest
            )
            if replay is not None:
                return replay
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
            self._record_receipt(
                conn, client_request_id, "subscription.unfollow", request_digest, result
            )
            return result

    def list_subscriptions(
        self, actor_ref: str, *, target_kind: TargetKind | None = None, limit: int = 200
    ) -> dict[str, Any]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_actor(conn, actor_ref)
            rows = conn.execute(
                "SELECT target_kind,target_ref,created_at,change_sequence FROM subscriptions "
                "WHERE actor_ref=%s AND (%s::text IS NULL OR target_kind=%s) "
                "ORDER BY target_kind,target_ref LIMIT %s",
                (actor_ref, target_kind, target_kind, limit + 1),
            ).fetchall()
            has_more = len(rows) > limit
            page = rows[:limit]
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-subscription-list",
                "actorRef": actor_ref,
                "subscriptions": [
                    {
                        "targetKind": row["target_kind"],
                        "targetRef": row["target_ref"],
                        "createdAt": row["created_at"].isoformat(),
                        "changeSequence": int(row["change_sequence"]),
                    }
                    for row in page
                ],
                "hasMore": has_more,
                "truncated": has_more,
                "rankingApplied": False,
                "truthBoundary": "actor attention-routing preferences only; not assignment, priority, ownership, or authorization",
            }

    def get(self, actor_ref: str, *, limit: int = 100) -> dict[str, Any]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_actor(conn, actor_ref)
            row = conn.execute(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=%s", (actor_ref,)
            ).fetchone()
            cursor = 0 if row is None else int(row["cursor"])
        return self.delta(actor_ref, after_sequence=cursor, limit=limit)

    def delta(self, actor_ref: str, *, after_sequence: int, limit: int = 100) -> dict[str, Any]:
        if after_sequence < 0:
            raise ValueError("after_sequence must be non-negative")
        if not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_actor(conn, actor_ref)
            high = int(
                conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[
                    "value"
                ]
            )
            rows = conn.execute(
                self._delta_sql(),
                {
                    "actor_ref": actor_ref,
                    "after_sequence": after_sequence,
                    "high": high,
                    "limit": limit + 1,
                },
            ).fetchall()
            has_more = len(rows) > limit
            page = rows[:limit]
            next_sequence = after_sequence if not page else int(page[-1]["change_sequence"])
            return {
                "schemaVersion": 1,
                "kind": "ordivon.host-attention-delta-r1",
                "actorRef": actor_ref,
                "afterSequence": after_sequence,
                "snapshotHighSequence": high,
                "events": [
                    {
                        "changeSequence": int(row["change_sequence"]),
                        "eventKind": row["event_kind"],
                        "sourceRef": row["source_ref"],
                        "contextRef": row["context_ref"],
                    }
                    for row in page
                ],
                "hasMore": has_more,
                "nextAfterSequence": next_sequence,
                "rankingApplied": False,
                "truthBoundary": "rebuildable actor-scoped navigation over owner rows; not inbox truth, priority, assignment, or authority",
            }

    def ack(self, actor_ref: str, *, cursor: int, client_request_id: str) -> dict[str, Any]:
        if cursor < 0:
            raise ValueError("cursor must be non-negative")
        request = {"operation": "attention.ack", "actorRef": actor_ref, "cursor": cursor}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = self._claim_receipt(conn, client_request_id, "attention.ack", request_digest)
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
            conn.execute(
                "INSERT INTO attention_cursors(actor_ref,cursor) VALUES (%s,%s) "
                "ON CONFLICT (actor_ref) DO UPDATE SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp()",
                (actor_ref, cursor),
            )
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-attention-ack",
                "actorRef": actor_ref,
                "previousCursor": previous,
                "cursor": cursor,
                "truthBoundary": "navigation acknowledgement only; not evidence that message content was semantically accepted",
            }
            self._record_receipt(conn, client_request_id, "attention.ack", request_digest, result)
            return result

    @staticmethod
    def _delta_sql() -> str:
        # Every branch reads the source-of-record row directly. There is intentionally no
        # copied attention_events table or custom event bus.
        return """
        WITH relevant AS (
            SELECT ws.change_sequence, 'work_snapshot'::text AS event_kind,
                   ws.work_ref::text AS source_ref, ws.revision::text AS context_ref
            FROM work_snapshots ws
            WHERE ws.change_sequence > %(after_sequence)s AND ws.change_sequence <= %(high)s
              AND EXISTS (
                SELECT 1 FROM subscriptions s
                WHERE s.actor_ref=%(actor_ref)s AND s.target_kind='work'
                  AND s.target_ref=ws.work_ref AND ws.change_sequence > s.change_sequence
              )
            UNION ALL
            SELECT wr.change_sequence, 'work_relation',
                   wr.source_work_ref || ':' || wr.relation || ':' || wr.target_work_ref,
                   wr.relation
            FROM work_relations wr
            WHERE wr.change_sequence > %(after_sequence)s AND wr.change_sequence <= %(high)s
              AND EXISTS (
                SELECT 1 FROM subscriptions s
                WHERE s.actor_ref=%(actor_ref)s AND s.target_kind='work'
                  AND s.target_ref IN (wr.source_work_ref,wr.target_work_ref)
                  AND wr.change_sequence > s.change_sequence
              )
            UNION ALL
            SELECT t.change_sequence, 'topic_change', t.topic_ref, t.space_ref
            FROM topics t
            WHERE t.change_sequence > %(after_sequence)s AND t.change_sequence <= %(high)s
              AND EXISTS (
                SELECT 1 FROM subscriptions s
                WHERE s.actor_ref=%(actor_ref)s
                  AND ((s.target_kind='topic' AND s.target_ref=t.topic_ref)
                    OR (s.target_kind='space' AND s.target_ref=t.space_ref))
                  AND t.change_sequence > s.change_sequence
              )
            UNION ALL
            SELECT m.change_sequence, 'message', m.message_ref, m.topic_ref
            FROM messages m
            WHERE m.change_sequence > %(after_sequence)s AND m.change_sequence <= %(high)s
              AND (
                EXISTS (
                  SELECT 1 FROM subscriptions s
                  WHERE s.actor_ref=%(actor_ref)s
                    AND ((s.target_kind='topic' AND s.target_ref=m.topic_ref)
                      OR (s.target_kind='space' AND s.target_ref=m.space_ref))
                    AND m.change_sequence > s.change_sequence
                )
                OR EXISTS (
                  SELECT 1 FROM message_relations mr
                  WHERE mr.source_message_ref=m.message_ref
                    AND mr.relation='mentions' AND mr.target_ref=%(actor_ref)s
                )
                OR EXISTS (
                  SELECT 1 FROM message_relations reply
                  JOIN messages parent ON parent.message_ref=reply.target_ref
                  WHERE reply.source_message_ref=m.message_ref AND reply.relation='reply_to'
                    AND parent.author_actor_ref=%(actor_ref)s
                )
              )
            UNION ALL
            SELECT mr.change_sequence, 'message_relation',
                   mr.source_message_ref || ':' || mr.relation || ':' || mr.target_ref,
                   mr.relation
            FROM message_relations mr
            JOIN messages source_message ON source_message.message_ref=mr.source_message_ref
            LEFT JOIN messages target_message ON target_message.message_ref=mr.target_ref
            WHERE mr.change_sequence > %(after_sequence)s AND mr.change_sequence <= %(high)s
              AND (
                (mr.relation='mentions' AND mr.target_ref=%(actor_ref)s)
                OR (mr.relation='reply_to' AND target_message.author_actor_ref=%(actor_ref)s)
                OR EXISTS (
                  SELECT 1 FROM subscriptions s
                  WHERE s.actor_ref=%(actor_ref)s
                    AND ((s.target_kind='topic' AND s.target_ref=source_message.topic_ref)
                      OR (s.target_kind='space' AND s.target_ref=source_message.space_ref))
                    AND mr.change_sequence > s.change_sequence
                )
              )
            UNION ALL
            SELECT p.change_sequence, 'participation_change',
                   p.space_ref || ':' || p.actor_ref, p.standing
            FROM participations p
            WHERE p.change_sequence > %(after_sequence)s AND p.change_sequence <= %(high)s
              AND p.actor_ref=%(actor_ref)s
            UNION ALL
            SELECT ci.change_sequence, 'coordination_intent', ci.intent_ref, ci.subject_ref
            FROM coordination_intents ci
            WHERE ci.change_sequence > %(after_sequence)s AND ci.change_sequence <= %(high)s
              AND (
                ci.actor_ref=%(actor_ref)s
                OR (ci.work_ref IS NOT NULL AND EXISTS (
                  SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                    AND s.target_kind='work' AND s.target_ref=ci.work_ref
                    AND ci.change_sequence > s.change_sequence
                ))
                OR (ci.space_ref IS NOT NULL AND EXISTS (
                  SELECT 1 FROM subscriptions s WHERE s.actor_ref=%(actor_ref)s
                    AND s.target_kind='space' AND s.target_ref=ci.space_ref
                    AND ci.change_sequence > s.change_sequence
                ))
              )
        )
        SELECT change_sequence,event_kind,source_ref,context_ref
        FROM relevant
        ORDER BY change_sequence,event_kind,source_ref
        LIMIT %(limit)s
        """

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
            "UPDATE command_receipts SET response=%s WHERE client_request_id=%s AND operation=%s "
            "AND request_digest=%s AND response IS NULL RETURNING client_request_id",
            (Jsonb(result), client_request_id, operation, request_digest),
        ).fetchone()
        if updated is None:
            raise RuntimeError("idempotency claim could not be finalized")
