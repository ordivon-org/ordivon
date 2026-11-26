"""Behavior-first request context and stable Host compatibility regression."""

from __future__ import annotations

import asyncio

import pytest

from ordivon_gateway.logic.host_tool_contracts import (
    bind_public_tool_call as legacy_bind,
)
from ordivon_gateway.logic.host_tool_contracts import (
    current_public_tool_call as legacy_current,
)
from ordivon_gateway.logic.public_tool_binding import (
    bind_public_tool_call,
    current_public_tool_call,
)


def test_host_compat_exports_same_function() -> None:
    assert legacy_bind is bind_public_tool_call
    assert legacy_current is current_public_tool_call


def test_nested_binding_restores_prior_context_even_on_error() -> None:
    assert current_public_tool_call() is None
    with bind_public_tool_call("work.get", {"workRef": "work:source:one"}):
        assert current_public_tool_call() == (
            "work.get",
            {"workRef": "work:source:one"},
        )
        with pytest.raises(RuntimeError, match="canary"):
            with bind_public_tool_call("topic.resume", {"topicRef": "topic:source:two"}):
                assert current_public_tool_call()[0] == "topic.resume"
                raise RuntimeError("canary")
        assert current_public_tool_call()[0] == "work.get"
    assert current_public_tool_call() is None


def test_async_task_contexts_are_isolated() -> None:
    async def task(action: str) -> str:
        with bind_public_tool_call(action, {"actorRef": f"actor:{action}"}):
            await asyncio.sleep(0)
            assert current_public_tool_call()[1]["actorRef"] == f"actor:{action}"
            return current_public_tool_call()[0]

    async def check() -> list[str]:
        return await asyncio.gather(task("work.get"), task("message.post"))

    assert asyncio.run(check()) == [
        "work.get",
        "message.post",
    ]
    assert current_public_tool_call() is None
