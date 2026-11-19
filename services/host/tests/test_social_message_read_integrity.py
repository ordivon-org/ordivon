"""Host Social Message typed content digest: readback is not merely a DB pointer."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime

import pytest

from ordivon_host_v2 import social_store
from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.social_errors import MessageNotFound
from ordivon_host_v2.social_message_records import require_message, verify_message_content_digest
from ordivon_host_v2.social_store import SocialStore


class _MessageConnection:
    def __init__(self) -> None:
        self.row = {
            "sequence": 1,
            "message_ref": "message:source",
            "space_ref": "space:source",
            "topic_ref": "topic:source",
            "author_actor_ref": "actor:agent:source",
            "message_kind": "finding",
            "body": "forged after durable admission",
            "message_digest": "sha256:" + "0" * 64,
            "recorded_at_ms": 1,
            "created_at": datetime(2026, 10, 25, tzinfo=UTC),
        }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def transaction(self):
        return nullcontext()

    def execute(self, sql, params=None):
        return self

    def fetchone(self):
        return self.row


def test_message_get_cannot_return_body_inconsistent_with_durable_digest(monkeypatch):
    conn = _MessageConnection()
    monkeypatch.setattr(social_store.psycopg, "connect", lambda *a, **kw: conn)
    with pytest.raises(RuntimeError, match="message.*content digest"):
        SocialStore("postgresql://unused.invalid").get_message("message:source")


def test_caller_supplied_expected_digest_cannot_launder_corrupted_message(monkeypatch):
    conn = _MessageConnection()
    monkeypatch.setattr(social_store.psycopg, "connect", lambda *a, **kw: conn)
    with pytest.raises(RuntimeError, match="message.*content digest"):
        SocialStore("postgresql://unused.invalid").get_message(
            "message:source", expected_digest=conn.row["message_digest"]
        )


def test_shared_message_digest_helper_accepts_original_and_rejects_corrupt_row() -> None:
    conn = _MessageConnection()
    row = conn.row
    row["message_digest"] = canonical_digest(
        {
            "messageRef": row["message_ref"],
            "spaceRef": row["space_ref"],
            "topicRef": row["topic_ref"],
            "authorActorRef": row["author_actor_ref"],
            "messageKind": row["message_kind"],
            "body": row["body"],
            "recordedAtMs": row["recorded_at_ms"],
        }
    )
    verify_message_content_digest(row)
    row["body"] = "tampered after original commit"
    with pytest.raises(RuntimeError, match="Host message content digest differs from stored claim"):
        verify_message_content_digest(row)


def test_shared_message_lookup_uses_supplied_pg_transaction_conn() -> None:
    class _LookupConn:
        def __init__(self, row):
            self.row = row
            self.statements = []

        def execute(self, sql, params):
            self.statements.append((sql, params))
            return self

        def fetchone(self):
            return self.row

    record = {"message_ref": "message:source", "sequence": 3}
    conn = _LookupConn(record)
    assert require_message(conn, "message:source") is record
    assert len(conn.statements) == 1
    assert conn.statements[0][1] == ("message:source",)
    assert "FROM messages WHERE message_ref=%s" in conn.statements[0][0]

    missing = _LookupConn(None)
    with pytest.raises(MessageNotFound):
        require_message(missing, "message:missing")
