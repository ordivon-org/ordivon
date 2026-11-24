"""Exact MCP cursor input: no bool, float or string alias reaches a Host Store.

The native MCP/Pydantic ingress previously normalized True, 1.0, and "1"
into integer 1. Those are not the same typed consumer cursor identity.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from mcp import Client
from pydantic import TypeAdapter

from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.mcp_server import build_server
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.wire_common import ExactCursorWire


@pytest.mark.parametrize("alias", [True, False, 1.0, 0.0, "1", "0"])
@pytest.mark.parametrize(
    ("tool", "params"),
    [
        ("attention.ack", {"actorRef": "actor:cursor", "cursor": None}),
        ("attention.delta", {"actorRef": "actor:cursor", "afterSequence": None}),
        ("attention.reentry", {"actorRef": "actor:cursor", "afterSequence": None}),
        (
            "topic.cursor.ack",
            {"actorRef": "actor:cursor", "topicRef": "topic:cursor", "cursor": None},
        ),
        ("topic.resume", {"topicRef": "topic:cursor", "afterSequence": None}),
    ],
)
def test_invalid_mcp_cursor_alias_rejected_before_store(
    monkeypatch, alias: object, tool: str, params: dict[str, Any]
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("a coerced cursor must never reach Host Store")

    for owner, name in (
        (AttentionStore, "ack"),
        (AttentionStore, "delta"),
        (AttentionStore, "reentry"),
        (SocialStore, "ack_topic_cursor"),
        (SocialStore, "resume_topic"),
    ):
        monkeypatch.setattr(owner, name, forbidden)

    arguments = {key: (alias if value is None else value) for key, value in params.items()}

    async def scenario() -> None:
        async with Client(
            build_server("postgresql://unused.invalid/host"), raise_exceptions=False
        ) as client:
            result = await client.call_tool(tool, arguments)
            assert result.is_error is True

    asyncio.run(scenario())


@pytest.mark.parametrize("cursor", [True, False, 1.0, 0.0, "1", "0", -1])
def test_direct_attention_ack_rejects_non_exact_or_negative_cursor(cursor: object) -> None:
    store = AttentionStore("postgresql://unused.invalid/host")
    with pytest.raises(ValueError, match="exact integer"):
        store.ack("actor:cursor", cursor=cursor, client_request_id="ack:invalid")


def test_exact_cursor_wire_advertises_actual_safe_integer_domain() -> None:
    assert TypeAdapter(ExactCursorWire).json_schema() == {"type": "integer", "minimum": 0, "maximum": (1 << 53) - 1}
    for cursor in (0, 1, (1 << 53) - 1):
        assert TypeAdapter(ExactCursorWire).validate_python(cursor) == cursor
