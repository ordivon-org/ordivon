"""Golden Road consumer: preserve the recoverable Host topic-cursor error in MCP text.

The connected MCP client may collapse structuredContent into a plain failure.
Only a narrow verified Host navigation error may expose public nonsecret fields;
unknown Owner errors must remain opaque. This is not an authorization change.
"""

from __future__ import annotations

import asyncio

from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.security import OwnerCallError, owner_error_result
from ordivon_gateway.service import GatewayService

HOST_CURSOR_ERROR = {
    "code": "CONFLICT",
    "kind": "ordivon.host-domain-error",
    "schemaVersion": 1,
    "retryable": False,
    "reason": "topic_resume_cursor_ahead",
    "resourceKind": "topic",
    "resourceRef": "topic:consumer-r65",
    "requestedAfterSequence": 10_000_000,
    "observedTopicHighSequence": 30394,
    "suggestedAction": "reread-topic-horizon-and-check-cursor-domain",
    "detail": "private diagnostic text which MUST NEVER appear in public text",
}


def test_host_typed_cursor_error_survives_public_mcp_text_only_consumer() -> None:
    class FailingOwner:
        def is_configured(self, owner_id: str) -> bool:
            return owner_id == "host"

        async def call_tool(self, owner_id: str, tool_name: str, arguments: dict):
            assert owner_id == "host" and tool_name == "topic.resume"
            assert arguments["afterSequence"] == 10_000_000
            raise OwnerCallError(
                "owner tool returned error: host/topic.resume",
                owner_id=owner_id,
                tool_name=tool_name,
                error=HOST_CURSOR_ERROR,
            )

    async def run() -> None:
        async with Client(
            build_server(GatewayService(FailingOwner())), raise_exceptions=False
        ) as client:
            result = await client.call_tool(
                "topic.resume",
                {"topicRef": "topic:consumer-r65", "afterSequence": 10_000_000},
            )
            assert result.is_error is True
            assert result.structured_content is not None
            assert result.structured_content["error"] == HOST_CURSOR_ERROR
            visible = result.content[0].text
            assert "CONFLICT" in visible
            assert "topic_resume_cursor_ahead" in visible
            assert "requestedAfterSequence=10000000" in visible
            assert "observedTopicHighSequence=30394" in visible
            assert "reread-topic-horizon-and-check-cursor-domain" in visible
            assert "private diagnostic" not in visible
            assert "resourceRef" not in visible

    asyncio.run(run())


def test_host_error_text_projection_refuses_unauthorized_and_untrusted_claims() -> None:
    invalids = [
        ({**HOST_CURSOR_ERROR, "code": "UNAUTHORIZED"}, "host", "topic.resume"),
        ({**HOST_CURSOR_ERROR, "schemaVersion": 2}, "host", "topic.resume"),
        ({**HOST_CURSOR_ERROR, "kind": "attacker"}, "host", "topic.resume"),
        ({**HOST_CURSOR_ERROR, "retryable": True}, "host", "topic.resume"),
        ({**HOST_CURSOR_ERROR, "requestedAfterSequence": True}, "host", "topic.resume"),
        ({**HOST_CURSOR_ERROR, "observedTopicHighSequence": -1}, "host", "topic.resume"),
        ({**HOST_CURSOR_ERROR, "suggestedAction": "leak-secrets"}, "host", "topic.resume"),
        (HOST_CURSOR_ERROR, "host", "work.get"),
        (HOST_CURSOR_ERROR, "runtime.linux", "topic.resume"),
        (None, "host", "topic.resume"),
    ]
    for error, owner, tool in invalids:
        public = owner_error_result(
            OwnerCallError(
                f"owner tool returned error: {owner}/{tool}",
                owner_id=owner,
                tool_name=tool,
                error=error,
            )
        )
        assert public.is_error is True
        assert public.content[0].text == f"owner tool returned error: {owner}/{tool}"
        assert public.structured_content["gatewayOwnerId"] == owner


def test_safe_text_projections_have_bounded_size_and_no_arbitrary_owner_text() -> None:
    error = {**HOST_CURSOR_ERROR, "detail": "secret=" + "X" * 300_000}
    public = owner_error_result(
        OwnerCallError(
            "owner tool returned error: host/topic.resume",
            owner_id="host",
            tool_name="topic.resume",
            error=error,
        )
    )
    assert public.is_error is True
    visible = public.content[0].text
    assert len(visible) < 350
    assert "secret=" not in visible
    assert "X" * 10 not in visible
