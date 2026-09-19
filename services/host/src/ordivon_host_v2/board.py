from __future__ import annotations

import time
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical import canonical_digest
from .errors import ConflictError

_MESSAGE_KINDS = {"note", "question", "proposal", "warning", "reply"}

_LEGACY_TASK_ROUTE_ANCHOR_ID_PREFIX = "task-route-anchor-v1:"


def _validate_optional_filter(value: str | None, label: str, max_length: int = 256) -> None:
    if value is not None and (
        not isinstance(value, str) or not value or value != value.strip() or len(value) > max_length
    ):
        raise ValueError(f"{label} must be null or 1-{max_length} trimmed characters")


def is_legacy_task_route_anchor(row: dict[str, Any]) -> bool:
    """Recognize historical infrastructure rows without using them for active routing."""
    return (
        isinstance(row.get("client_message_id"), str)
        and row["client_message_id"].startswith(_LEGACY_TASK_ROUTE_ANCHOR_ID_PREFIX)
        and row.get("author_label") == "task-routing-anchor-v1"
        and row.get("message_kind") == "note"
        and row.get("topic") == "agent-native-collaboration-routing"
        and row.get("reply_to_client_message_id") is None
    )


def _validate_task_id(value: str | None) -> None:
    if value is not None and (
        not isinstance(value, str)
        or not value.startswith("task:")
        or value != value.strip()
        or len(value) > 4096
    ):
        raise ValueError("taskId must be null or one trimmed task: identity")

def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def board_message_digest(value: dict[str, Any]) -> str:
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.host-board-message",
        "clientMessageId": value["clientMessageId"],
        "authorLabel": value["authorLabel"],
        "messageKind": value["messageKind"],
        "topic": value["topic"],
        "message": value["message"],
        "replyToClientMessageId": value["replyToClientMessageId"],
        "truthRole": "coordination-message-not-domain-truth",
    }
    return canonical_digest({"schemaVersion": 1, "kind": "host-board-message", "payload": payload})



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
        task_id: str | None = None,
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
        _validate_optional_filter(reply_to_client_message_id, "replyToClientMessageId")
        _validate_task_id(task_id)
        if client_message_id.startswith(_LEGACY_TASK_ROUTE_ANCHOR_ID_PREFIX):
            raise ValueError("legacy task-route-anchor-v1 namespace is retired")
        value = {
            "clientMessageId": client_message_id,
            "authorLabel": author_label,
            "messageKind": message_kind,
            "topic": topic,
            "message": message,
            "replyToClientMessageId": reply_to_client_message_id,
            "taskId": task_id,
        }
        digest = board_message_digest(value)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            resolved_task_id = task_id
            if reply_to_client_message_id is not None:
                parent = conn.execute(
                    "SELECT task_id FROM board_messages WHERE client_message_id=%s",
                    (reply_to_client_message_id,),
                ).fetchone()
                if parent is None:
                    raise ConflictError("board reply target does not exist")
                parent_task_id = parent["task_id"]
                if (
                    resolved_task_id is not None
                    and parent_task_id is not None
                    and resolved_task_id != parent_task_id
                ):
                    raise ConflictError("board reply taskId conflicts with parent taskId")
                if resolved_task_id is None:
                    resolved_task_id = parent_task_id
            if resolved_task_id is not None:
                exists = conn.execute(
                    "SELECT 1 FROM tasks WHERE task_id=%s", (resolved_task_id,)
                ).fetchone()
                if exists is None:
                    raise ConflictError("board taskId does not reference an existing Task")
            row = conn.execute(
                "INSERT INTO board_messages(client_message_id,author_label,message_kind,topic,message,reply_to_client_message_id,task_id,message_digest,recorded_at_ms) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (client_message_id) DO NOTHING "
                "RETURNING sequence,recorded_at_ms",
                (
                    client_message_id,
                    author_label,
                    message_kind,
                    topic,
                    message,
                    reply_to_client_message_id,
                    resolved_task_id,
                    digest,
                    _now_ms(),
                ),
            ).fetchone()
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT sequence,recorded_at_ms,message_digest,task_id FROM board_messages WHERE client_message_id=%s",
                    (client_message_id,),
                ).fetchone()
                assert row is not None
                if row["message_digest"] != digest:
                    raise ConflictError(
                        "board clientMessageId is already bound to different content"
                    )
                if row["task_id"] != resolved_task_id:
                    raise ConflictError(
                        "board clientMessageId is already bound to a different Task route"
                    )
                admission = "existing"
            message_row = self._by_id(conn, client_message_id)
            return {
                "schemaVersion": 3,
                "kind": "ordivon.host-board-post-receipt",
                "admission": admission,
                "message": self._wire(message_row),
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
        if after_sequence is not None and (type(after_sequence) is not int or after_sequence < 0):
            raise ValueError("afterSequence must be null or non-negative")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be in [1,100]")
        _validate_optional_filter(topic, "topic")
        _validate_optional_filter(client_message_id, "clientMessageId")
        _validate_optional_filter(reply_to_client_message_id, "replyToClientMessageId")
        _validate_optional_filter(reply_to_author_label, "replyToAuthorLabel")

        filtered = any(
            value is not None
            for value in (
                topic,
                client_message_id,
                reply_to_client_message_id,
                reply_to_author_label,
            )
        )
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

        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            high_row = conn.execute(
                "SELECT COALESCE(max(sequence),0) AS value FROM board_messages"
            ).fetchone()
            assert high_row is not None
            high = int(high_row["value"])
            if filtered:
                clauses.append("m.sequence <= %s")
                params.append(high)
            where = "WHERE " + " AND ".join(clauses) if clauses else ""
            direction = "ASC" if after_sequence is not None else "DESC"
            requested_limit = limit + 1 if after_sequence is not None else limit
            rows = conn.execute(
                "SELECT m.* FROM board_messages m LEFT JOIN board_messages p "
                "ON p.client_message_id=m.reply_to_client_message_id "
                f"{where} ORDER BY m.sequence {direction} LIMIT %s",
                [*params, requested_limit],
            ).fetchall()

            if after_sequence is not None:
                has_more = len(rows) > limit
                visible = rows[:limit]
                next_after = (
                    int(visible[-1]["sequence"])
                    if has_more and visible
                    else max(after_sequence, high)
                )
            else:
                visible = list(reversed(rows))
                has_more = False
                next_after = high

            result = {
                "schemaVersion": 3,
                "kind": "ordivon.host-board-list",
                "scope": "host-global-coordination-messages",
                "selectionMode": "latest-window" if after_sequence is None else "incremental-page",
                "requestedAfterSequence": after_sequence,
                "requestedLimit": limit,
                "messages": [self._wire(row) for row in visible],
                "lastSequence": high,
                "nextAfterSequence": next_after,
                "hasMore": has_more,
                "truthBoundary": "durable collaboration records only; not priority, authority, owner standing, or domain truth",
            }
            if topic is not None:
                result["topic"] = topic
            if client_message_id is not None:
                result["clientMessageId"] = client_message_id
            if reply_to_client_message_id is not None:
                result["replyToClientMessageId"] = reply_to_client_message_id
            if reply_to_author_label is not None:
                result["replyToAuthorLabel"] = reply_to_author_label
            return result

    def search(self, *, query: str, limit: int = 20) -> dict[str, Any]:
        if not query.strip() or len(query) > 512:
            raise ValueError("query must be 1-512 characters")
        if not 1 <= limit <= 50:
            raise ValueError("limit must be in [1,50]")
        pattern = f"%{query}%"
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.transaction():
                conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                high_row = conn.execute(
                    "SELECT COALESCE(max(sequence),0) AS value FROM board_messages"
                ).fetchone()
                assert high_row is not None
                high = int(high_row["value"])
                rows = conn.execute(
                    "SELECT sequence,client_message_id FROM board_messages "
                    "WHERE sequence<=%s AND ("
                    "to_tsvector('simple', coalesce(author_label,'') || ' ' || coalesce(topic,'') || ' ' || message) @@ plainto_tsquery('simple', %s) "
                    "OR client_message_id ILIKE %s OR author_label ILIKE %s OR coalesce(topic,'') ILIKE %s OR message ILIKE %s) "
                    "ORDER BY sequence DESC LIMIT %s",
                    (high, query, pattern, pattern, pattern, pattern, limit),
                ).fetchall()
            live_row = conn.execute(
                "SELECT COALESCE(max(sequence),0) AS value FROM board_messages"
            ).fetchone()
            assert live_row is not None
            live_high = int(live_row["value"])
        return {
            "schemaVersion": 2,
            "kind": "ordivon.host-board-search",
            "scope": "host-global-coordination-messages",
            "truthRole": "search-navigation-candidates-not-domain-truth",
            "sourceSnapshotHighWater": high,
            "liveHighWater": live_high,
            "negativeResultAuthoritative": False,
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
            "taskId": row.get("task_id"),
            "recordedAtMs": int(row["recorded_at_ms"]),
            "messageDigest": row["message_digest"],
            "truthRole": "coordination-message-not-domain-truth",
        }
