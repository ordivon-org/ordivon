"""Host Social Message typed content digest: readback is not merely a DB pointer."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime

import pytest

from ordivon_host_v2 import social_store
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
