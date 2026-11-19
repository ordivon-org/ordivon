"""MCP negative control: a Topic cursor from another sequence domain is not an empty page."""

from __future__ import annotations

import asyncio
import json

from mcp import Client

from ordivon_host_v2.mcp_domain_errors import _domain_error_payload
from ordivon_host_v2.mcp_server import build_server
from ordivon_host_v2.social_errors import TopicResumeCursorAhead
from ordivon_host_v2.social_store import SocialStore


def test_invalid_topic_resume_cursor_has_actionable_host_proof() -> None:
    exc = TopicResumeCursorAhead("topic:source", 123, 7)
    payload = _domain_error_payload(exc)
    assert payload == {
        "schemaVersion": 1,
        "kind": "ordivon.host-domain-error",
        "retryable": False,
        "code": "CONFLICT",
        "detail": "topic resume cursor 123 exceeds topic message high 7",
        "reason": "topic_resume_cursor_ahead",
        "resourceKind": "topic",
        "resourceRef": "topic:source",
        "requestedAfterSequence": 123,
        "observedTopicHighSequence": 7,
        "evidenceBoundary": "same-transaction-topic-message-horizon",
        "suggestedAction": "reread-topic-horizon-and-check-cursor-domain",
    }


def test_native_mcp_preserves_conflict_class_and_never_claims_no_messages(monkeypatch) -> None:
    def wrong(self, topic_ref, *, after_sequence=0, **kwargs):
        _ = self, kwargs
        raise TopicResumeCursorAhead(topic_ref, after_sequence, 7)

    monkeypatch.setattr(SocialStore, "resume_topic", wrong)

    async def scenario() -> None:
        async with Client(
            build_server("postgresql://unused.invalid/host"), raise_exceptions=False
        ) as client:
            result = await client.call_tool(
                "topic.resume", {"topicRef": "topic:source", "afterSequence": 123}
            )
            assert result.is_error is True
            wire = "".join(getattr(item, "text", "") for item in result.content)
            assert wire.startswith("Error executing tool topic.resume: ")
            payload = json.loads(wire.split(": ", 1)[1])
            assert payload["code"] == "CONFLICT"
            assert payload["reason"] == "topic_resume_cursor_ahead"
            assert payload["requestedAfterSequence"] == 123
            assert payload["observedTopicHighSequence"] == 7
            assert payload["retryable"] is False

    asyncio.run(scenario())
