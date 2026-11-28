"""An ordinary native MCP client must see a typed Host cursor error.

Test the entire Gateway tool registration/boundary, not only the formatting
helper, with a fake downstream Owner and no live Host database or credentials.
"""

from __future__ import annotations

import asyncio

from mcp import Client

from ordivon_gateway.logic.owner_protocol import OwnerCallError
from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService


class CursorErrorOwner:
    def is_configured(self, owner_id: str) -> bool:
        return True

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict):
        assert owner_id == "host"
        assert tool_name == "topic.resume"
        assert arguments["afterSequence"] == 100_000_000
        raise OwnerCallError(
            "owner tool returned error: host/topic.resume",
            owner_id="host",
            tool_name="topic.resume",
            error={
                "kind": "ordivon.host-domain-error",
                "schemaVersion": 1,
                "code": "CONFLICT",
                "reason": "topic_resume_cursor_ahead",
                "resourceKind": "topic",
                "retryable": False,
                "requestedAfterSequence": 100_000_000,
                "observedTopicHighSequence": 30399,
                "evidenceBoundary": "same-transaction-topic-message-horizon",
                "suggestedAction": "reread-topic-horizon-and-check-cursor-domain",
                "detail": "SECRET_DO_NOT_ECHO",
            },
        )


def test_original_native_sdk_gateway_tool_preserves_safe_host_error():
    async def scenario() -> None:
        server = build_server(GatewayService(CursorErrorOwner()))
        async with Client(server, raise_exceptions=False) as client:
            result = await client.call_tool(
                "topic.resume",
                {"topicRef": "topic:fixture", "afterSequence": 100_000_000},
            )
            assert result.is_error is True
            assert result.structured_content is not None
            assert result.structured_content["error"]["reason"] == "topic_resume_cursor_ahead"
            assert result.structured_content["error"]["observedTopicHighSequence"] == 30399
            text = " ".join(str(getattr(item, "text", "")) for item in result.content)
            assert "reason=topic_resume_cursor_ahead" in text, text
            assert "observedTopicHighSequence=30399" in text, text
            assert "SECRET_DO_NOT_ECHO" not in text

    asyncio.run(scenario())
