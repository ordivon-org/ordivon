from __future__ import annotations

from datetime import UTC, datetime

import pytest

import ordivon_host_v2.social_store as social_store
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.social_store import SocialStore


class _Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _Tx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _Conn:
    def __init__(self, row):
        self.row = row
        self.queries: list[tuple[str, object]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def transaction(self):
        return _Tx()

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        if sql.startswith("SET TRANSACTION"):
            return _Result(None)
        return _Result(self.row)


def _row():
    return {
        "sequence": 42,
        "message_ref": "message:test:42",
        "space_ref": "space:test",
        "topic_ref": "topic:test",
        "author_actor_ref": "actor:agent:test",
        "message_kind": "finding",
        "body": "{\"decision\":\"ADMIT\"}",
        "message_digest": "sha256:" + ("a" * 64),
        "recorded_at_ms": 1234,
        "created_at": datetime(2026, 10, 16, tzinfo=UTC),
    }


def test_get_message_projects_exact_record_and_checks_expected_digest(monkeypatch) -> None:
    conn = _Conn(_row())
    monkeypatch.setattr(social_store.psycopg, "connect", lambda *args, **kwargs: conn)
    store = SocialStore("postgresql://unused")

    result = store.get_message(
        "message:test:42", expected_digest="sha256:" + ("a" * 64)
    )

    assert result["messageRef"] == "message:test:42"
    assert result["messageDigest"] == "sha256:" + ("a" * 64)
    assert result["body"] == "{\"decision\":\"ADMIT\"}"
    assert result["kind"] == "ordivon.host-message-read"
    assert result["truthBoundary"].startswith("exact durable Host message projection")
    assert any("WHERE message_ref=%s" in sql for sql, _ in conn.queries)

    with pytest.raises(ConflictError, match="message digest mismatch"):
        store.get_message("message:test:42", expected_digest="sha256:" + ("b" * 64))
