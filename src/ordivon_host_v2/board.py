from __future__ import annotations

import json
import time
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical import canonical_digest
from .errors import ConflictError

_MESSAGE_KINDS = {"note", "question", "proposal", "warning", "reply"}


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


class BoardStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def post(
        self,
        *,
        client_message_id: str,
        author_label: str,
        message: str,
        message_kind: str = "note",
        topic: str | None = None,
        reply_to_client_message_id: str | None = None,
    ) -> dict[str, Any]:
        if (
            not client_message_id
            or client_message_id != client_message_id.strip()
            or len(client_message_id) > 256
        ):
            raise ValueError("clientMessageId must be 1-256 trimmed characters")
        if not author_label or author_label != author_label.strip() or len(author_label) > 128:
            raise ValueError("authorLabel must be 1-128 trimmed characters")
        if message_kind not in _MESSAGE_KINDS:
            raise ValueError("messageKind is invalid")
        if not message.strip() or len(message) > 4096:
            raise ValueError("message must contain 1-4096 characters")
        if topic is not None and (not topic or topic != topic.strip() or len(topic) > 256):
            raise ValueError("topic is invalid")
        value = {
            "clientMessageId": client_message_id,
            "authorLabel": author_label,
            "messageKind": message_kind,
            "topic": topic,
            "message": message,
            "replyToClientMessageId": reply_to_client_message_id,
        }
        digest = canonical_digest(value)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            if reply_to_client_message_id is not None:
                parent = conn.execute(
                    "SELECT 1 FROM board_messages WHERE client_message_id=%s",
                    (reply_to_client_message_id,),
                ).fetchone()
                if parent is None:
                    raise ConflictError("board reply target does not exist")
            row = conn.execute(
                "INSERT INTO board_messages(client_message_id,author_label,message_kind,topic,message,reply_to_client_message_id,message_digest,recorded_at_ms) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (client_message_id) DO NOTHING "
                "RETURNING sequence,recorded_at_ms",
                (
                    client_message_id,
                    author_label,
                    message_kind,
                    topic,
                    message,
                    reply_to_client_message_id,
                    digest,
                    _now_ms(),
                ),
            ).fetchone()
            created = row is not None
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT sequence,recorded_at_ms,message_digest FROM board_messages WHERE client_message_id=%s",
                    (client_message_id,),
                ).fetchone()
                assert row is not None
                if row["message_digest"] != digest:
                    raise ConflictError(
                        "board clientMessageId is already bound to different content"
                    )
                admission = "existing"
            if created:
                conn.execute(
                    "INSERT INTO activity_log(activity_kind,subject_id,payload) VALUES ('board.post',%s,%s::jsonb)",
                    (client_message_id, json.dumps({"topic": topic}, separators=(",", ":"))),
                )
            message_row = self._by_id(conn, client_message_id)
            occupancy = None
            if reply_to_client_message_id is not None:
                count_row = conn.execute(
                    "SELECT count(*) AS value FROM board_messages WHERE reply_to_client_message_id=%s AND sequence<=%s",
                    (reply_to_client_message_id, message_row["sequence"]),
                ).fetchone()
                assert count_row is not None
                count = count_row["value"]
                occupancy = {
                    "parentClientMessageId": reply_to_client_message_id,
                    "throughSequence": message_row["sequence"],
                    "priorDirectReplyCount": int(count) - 1,
                    "currentDirectReplyCount": int(count),
                    "truthRole": "mechanical-direct-reply-admission-density-not-active-standing",
                }
            return {
                "schemaVersion": 2,
                "kind": "ordivon.host-board-post-receipt",
                "admission": admission,
                "message": self._wire(message_row),
                "replyOccupancy": occupancy,
                "truthBoundary": "message persistence only; not Task priority, execution authority, owner standing, or domain truth",
            }

    def list(
        self,
        *,
        after_sequence: int | None = None,
        limit: int = 50,
        topic: str | None = None,
        client_message_id: str | None = None,
        reply_to_client_message_id: str | None = None,
        reply_to_author_label: str | None = None,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be in [1,100]")
        clauses: list[str] = []
        params: list[Any] = []
        if after_sequence is not None:
            clauses.append("m.sequence > %s")
            params.append(after_sequence)
        if topic is not None:
            clauses.append("m.topic = %s")
            params.append(topic)
        if client_message_id is not None:
            clauses.append("m.client_message_id = %s")
            params.append(client_message_id)
        if reply_to_client_message_id is not None:
            clauses.append("m.reply_to_client_message_id = %s")
            params.append(reply_to_client_message_id)
        if reply_to_author_label is not None:
            clauses.append("p.author_label = %s")
            params.append(reply_to_author_label)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        direction = "ASC" if after_sequence is not None else "DESC"
        query = (
            "SELECT m.* FROM board_messages m LEFT JOIN board_messages p ON p.client_message_id=m.reply_to_client_message_id "
            f"{where} ORDER BY m.sequence {direction} LIMIT %s"
        )
        params.append(limit)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(query, params).fetchall()
            if after_sequence is None:
                rows = list(reversed(rows))
            high_row = conn.execute(
                "SELECT COALESCE(max(sequence),0) AS value FROM board_messages"
            ).fetchone()
            assert high_row is not None
            high = int(high_row["value"])
            next_after = rows[-1]["sequence"] if rows else (after_sequence or high)
            return {
                "schemaVersion": 2,
                "kind": "ordivon.host-board-list",
                "scope": "host-global-coordination-messages",
                "selectionMode": "latest-window" if after_sequence is None else "incremental-page",
                "requestedAfterSequence": after_sequence,
                "requestedLimit": limit,
                "messages": [self._wire(row) for row in rows],
                "lastSequence": high,
                "nextAfterSequence": next_after,
                "hasMore": next_after < high,
                "truthBoundary": "durable collaboration records only; not priority, authority, owner standing, or domain truth",
            }

    def search(self, *, query: str, limit: int = 20) -> dict[str, Any]:
        if not query.strip() or len(query) > 512:
            raise ValueError("query must be 1-512 characters")
        if not 1 <= limit <= 50:
            raise ValueError("limit must be in [1,50]")
        pattern = f"%{query}%"
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            high_row = conn.execute(
                "SELECT COALESCE(max(sequence),0) AS value FROM board_messages"
            ).fetchone()
            assert high_row is not None
            high = int(high_row["value"])
            rows = conn.execute(
                "SELECT sequence,client_message_id FROM board_messages "
                "WHERE to_tsvector('simple', coalesce(author_label,'') || ' ' || coalesce(topic,'') || ' ' || message) @@ plainto_tsquery('simple', %s) "
                "OR client_message_id ILIKE %s OR author_label ILIKE %s OR coalesce(topic,'') ILIKE %s OR message ILIKE %s "
                "ORDER BY sequence DESC LIMIT %s",
                (query, pattern, pattern, pattern, pattern, limit),
            ).fetchall()
            return {
                "schemaVersion": 2,
                "kind": "ordivon.host-board-search",
                "scope": "host-global-coordination-messages",
                "truthRole": "search-navigation-candidates-not-domain-truth",
                "sourceSnapshotHighWater": high,
                "liveHighWater": high,
                "negativeResultAuthoritative": True,
                "requiresExactSourceReentry": True,
                "results": [
                    {"sequence": int(row["sequence"]), "clientMessageId": row["client_message_id"]}
                    for row in rows
                ],
            }

    @staticmethod
    def _by_id(conn: psycopg.Connection[dict[str, Any]], client_message_id: str) -> dict[str, Any]:
        row = conn.execute(
            "SELECT * FROM board_messages WHERE client_message_id=%s", (client_message_id,)
        ).fetchone()
        if row is None:
            raise ConflictError("board message disappeared after admission")
        return row

    @staticmethod
    def _wire(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "sequence": int(row["sequence"]),
            "clientMessageId": row["client_message_id"],
            "authorLabel": row["author_label"],
            "authorIdentityRole": "self-asserted-label",
            "messageKind": row["message_kind"],
            "topic": row["topic"],
            "message": row["message"],
            "replyToClientMessageId": row["reply_to_client_message_id"],
            "recordedAtMs": int(row["recorded_at_ms"]),
            "messageDigest": row["message_digest"],
            "truthRole": "coordination-message-not-domain-truth",
        }
