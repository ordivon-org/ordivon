from __future__ import annotations

import asyncio
import json

from mcp import Client

from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.mcp_server import build_server
from ordivon_host_v2.work_store import WorkNotFound, WorkStore


def _error_text(result) -> str:
    return "".join(getattr(item, "text", "") for item in result.content)


def _domain_payload(result) -> dict[str, object]:
    text = _error_text(result)
    prefix = "Error executing tool "
    assert text.startswith(prefix), text
    marker = text.find(": ")
    assert marker > 0, text
    return json.loads(text[marker + 2 :])


def test_work_not_found_is_expected_typed_tool_error(monkeypatch) -> None:
    def missing(self, work_ref, revision=None):
        _ = self, revision
        raise WorkNotFound(work_ref)

    monkeypatch.setattr(WorkStore, "get_work", missing)

    async def scenario() -> None:
        async with Client(build_server("postgresql://unused.invalid/unused"), raise_exceptions=False) as client:
            result = await client.call_tool("work.get", {"workRef": "work:missing"})
            assert result.is_error is True
            payload = _domain_payload(result)
            assert payload == {
                "code": "NOT_FOUND",
                "kind": "ordivon.host-domain-error",
                "resourceKind": "work",
                "resourceRef": "work:missing",
                "retryable": False,
                "schemaVersion": 1,
                "suggestedAction": "discover-before-create",
            }

    asyncio.run(scenario())


def test_conflict_is_expected_typed_tool_error(monkeypatch) -> None:
    def conflict(self, work_ref, **kwargs):
        _ = self, work_ref, kwargs
        raise ConflictError("expected revision 6, current revision is 7")

    monkeypatch.setattr(WorkStore, "commit_snapshot", conflict)

    async def scenario() -> None:
        async with Client(build_server("postgresql://unused.invalid/unused"), raise_exceptions=False) as client:
            result = await client.call_tool(
                "work.snapshot.commit",
                {
                    "workRef": "work:conflict",
                    "expectedRevision": 6,
                    "snapshot": {
                        "objective": "preserve semantic continuity",
                        "frontier": "r6",
                        "established": [],
                        "unresolved": [],
                        "rejected": [],
                        "constraints": [],
                        "nextActions": [],
                        "referenceRefs": [],
                    },
                    "actorRef": "actor:agent:test",
                },
            )
            assert result.is_error is True
            payload = _domain_payload(result)
            assert payload["code"] == "CONFLICT"
            assert payload["detail"] == "expected revision 6, current revision is 7"
            assert payload["suggestedAction"] == "reread-current-state-and-reconcile"

    asyncio.run(scenario())


def test_model_validation_is_expected_invalid_argument_without_store_call(monkeypatch) -> None:
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("store must not be called for invalid model input")

    from ordivon_host_v2.social_store import SocialStore

    monkeypatch.setattr(SocialStore, "create_space", forbidden)

    async def scenario() -> None:
        async with Client(build_server("postgresql://unused.invalid/unused"), raise_exceptions=False) as client:
            result = await client.call_tool(
                "space.create",
                {
                    "spaceRef": "space:valid",
                    "purpose": "test validation",
                    "actorRef": "x",
                },
            )
            assert result.is_error is True
            payload = _domain_payload(result)
            assert payload["code"] == "INVALID_ARGUMENT"
            assert payload["suggestedAction"] == "correct-request"
            assert called is False

    asyncio.run(scenario())


def test_unexpected_internal_failure_remains_generic_crash(monkeypatch) -> None:
    def crash(self, work_ref, revision=None):
        _ = self, work_ref, revision
        raise RuntimeError("sensitive internal detail")

    monkeypatch.setattr(WorkStore, "get_work", crash)

    async def scenario() -> None:
        async with Client(build_server("postgresql://unused.invalid/unused"), raise_exceptions=False) as client:
            result = await client.call_tool("work.get", {"workRef": "work:boom"})
            assert result.is_error is True
            text = _error_text(result)
            assert text == "Error executing tool work.get"
            assert "sensitive internal detail" not in text

    asyncio.run(scenario())
