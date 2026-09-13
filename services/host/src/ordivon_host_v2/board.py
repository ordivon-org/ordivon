from __future__ import annotations

import hashlib
import time
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical import canonical_digest
from .errors import ConflictError

_MESSAGE_KINDS = {"note", "question", "proposal", "warning", "reply"}

_TASK_ROUTE_ANCHOR_ID_PREFIX = "task-route-anchor-v1:"
_TASK_ROUTE_ANCHOR_AUTHOR_LABEL = "task-routing-anchor-v1"
_TASK_ROUTE_ANCHOR_TOPIC = "agent-native-collaboration-routing"
_TASK_ROUTE_ANCHOR_MESSAGE_PREFIX = "TASK COORDINATION ANCHOR v1 / exact Task identity `"
_TASK_ROUTE_ANCHOR_MESSAGE_SUFFIX = (
    "`. This Board root is a deterministic navigation coordinate only. It is not Task standing, "
    "priority, ownership, delegation, delivery, unread state, execution authority, or proof that "
    "any reply was consumed. Callers targeting this Task may post direct replies while preserving "
    "their own domain topic."
)


def _validate_optional_filter(value: str | None, label: str, max_length: int = 256) -> None:
    if value is not None and (
        not isinstance(value, str) or not value or value != value.strip() or len(value) > max_length
    ):
        raise ValueError(f"{label} must be null or 1-{max_length} trimmed characters")


def validate_task_route_anchor(
    *,
    client_message_id: str,
    author_label: str,
    message_kind: str,
    message: str,
    topic: str | None,
    reply_to_client_message_id: str | None,
) -> None:
    """Protect the deterministic Board→Task routing namespace from first-writer squatting."""
    if not client_message_id.startswith(_TASK_ROUTE_ANCHOR_ID_PREFIX):
        return
    suffix = client_message_id[len(_TASK_ROUTE_ANCHOR_ID_PREFIX) :]
    if len(suffix) != 64 or any(ch not in "0123456789abcdef" for ch in suffix):
        raise ValueError(
            "reserved task-route-anchor-v1 clientMessageId must end in 64 lowercase hex digits"
        )
    if (
        author_label != _TASK_ROUTE_ANCHOR_AUTHOR_LABEL
        or message_kind != "note"
        or topic != _TASK_ROUTE_ANCHOR_TOPIC
        or reply_to_client_message_id is not None
    ):
        raise ValueError("reserved task-route-anchor-v1 fields differ from canonical v1")
    if not message.startswith(_TASK_ROUTE_ANCHOR_MESSAGE_PREFIX) or not message.endswith(
        _TASK_ROUTE_ANCHOR_MESSAGE_SUFFIX
    ):
        raise ValueError("reserved task-route-anchor-v1 message differs from canonical v1")
    task_id = message[
        len(_TASK_ROUTE_ANCHOR_MESSAGE_PREFIX) : -len(_TASK_ROUTE_ANCHOR_MESSAGE_SUFFIX)
    ]
    if not task_id.startswith("task:"):
        raise ValueError("reserved task-route-anchor-v1 message must embed one exact Task identity")
    if suffix != hashlib.sha256(task_id.encode("utf-8")).hexdigest():
        raise ValueError(
            "reserved task-route-anchor-v1 digest does not match embedded Task identity"
        )


def task_route_anchor_task_id(row: dict[str, Any]) -> str | None:
    client_message_id = row.get("client_message_id")
    message = row.get("message")
    if not isinstance(client_message_id, str) or not client_message_id.startswith(
        _TASK_ROUTE_ANCHOR_ID_PREFIX
    ):
        return None
    if (
        not isinstance(message, str)
        or not message.startswith(_TASK_ROUTE_ANCHOR_MESSAGE_PREFIX)
        or not message.endswith(_TASK_ROUTE_ANCHOR_MESSAGE_SUFFIX)
    ):
        return None
    task_id = message[
        len(_TASK_ROUTE_ANCHOR_MESSAGE_PREFIX) : -len(_TASK_ROUTE_ANCHOR_MESSAGE_SUFFIX)
    ]
    expected = _TASK_ROUTE_ANCHOR_ID_PREFIX + hashlib.sha256(task_id.encode("utf-8")).hexdigest()
    if (
        not task_id.startswith("task:")
        or client_message_id != expected
        or row.get("author_label") != _TASK_ROUTE_ANCHOR_AUTHOR_LABEL
        or row.get("message_kind") != "note"
        or row.get("topic") != _TASK_ROUTE_ANCHOR_TOPIC
        or row.get("reply_to_client_message_id") is not None
    ):
        return None
    return task_id


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def board_message_digest(value: dict[str, Any]) -> str:
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.host-board-message",
        **value,
        "truthRole": "coordination-message-not-domain-truth",
    }
    return canonical_digest({"schemaVersion": 1, "kind": "host-board-message", "payload": payload})


def canonical_task_route_anchor(task_id: str) -> dict[str, Any]:
    if not isinstance(task_id, str) or not task_id.startswith("task:"):
        raise ValueError("task route anchor requires one exact task: identity")
    suffix = hashlib.sha256(task_id.encode("utf-8")).hexdigest()
    return {
        "clientMessageId": _TASK_ROUTE_ANCHOR_ID_PREFIX + suffix,
        "authorLabel": _TASK_ROUTE_ANCHOR_AUTHOR_LABEL,
        "messageKind": "note",
        "topic": _TASK_ROUTE_ANCHOR_TOPIC,
        "message": _TASK_ROUTE_ANCHOR_MESSAGE_PREFIX + task_id + _TASK_ROUTE_ANCHOR_MESSAGE_SUFFIX,
        "replyToClientMessageId": None,
    }


def ensure_task_route_anchor_in_tx(
    conn: psycopg.Connection[dict[str, Any]], task_id: str
) -> dict[str, Any]:
    value = canonical_task_route_anchor(task_id)
    digest = board_message_digest(value)
    row = conn.execute(
        "INSERT INTO board_messages(client_message_id,author_label,message_kind,topic,message,reply_to_client_message_id,message_digest,recorded_at_ms) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (client_message_id) DO NOTHING "
        "RETURNING sequence,recorded_at_ms",
        (
            value["clientMessageId"],
            value["authorLabel"],
            value["messageKind"],
            value["topic"],
            value["message"],
            value["replyToClientMessageId"],
            digest,
            _now_ms(),
        ),
    ).fetchone()
    if row is not None:
        return {
            "admission": "committed",
            "clientMessageId": value["clientMessageId"],
            "sequence": int(row["sequence"]),
        }
    existing = conn.execute(
        "SELECT * FROM board_messages WHERE client_message_id=%s",
        (value["clientMessageId"],),
    ).fetchone()
    if existing is None:
        raise RuntimeError("task route anchor disappeared after conflict arbitration")
    if task_route_anchor_task_id(existing) != task_id or existing["message_digest"] != digest:
        raise ConflictError("deterministic task route anchor is bound to non-canonical content")
    return {
        "admission": "existing",
        "clientMessageId": value["clientMessageId"],
        "sequence": int(existing["sequence"]),
    }


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
        _validate_optional_filter(reply_to_client_message_id, "replyToClientMessageId")
        validate_task_route_anchor(
            client_message_id=client_message_id,
            author_label=author_label,
            message_kind=message_kind,
            message=message,
            topic=topic,
            reply_to_client_message_id=reply_to_client_message_id,
        )
        value = {
            "clientMessageId": client_message_id,
            "authorLabel": author_label,
            "messageKind": message_kind,
            "topic": topic,
            "message": message,
            "replyToClientMessageId": reply_to_client_message_id,
        }
        digest = board_message_digest(value)
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
                "schemaVersion": 2,
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
            "recordedAtMs": int(row["recorded_at_ms"]),
            "messageDigest": row["message_digest"],
            "truthRole": "coordination-message-not-domain-truth",
        }
