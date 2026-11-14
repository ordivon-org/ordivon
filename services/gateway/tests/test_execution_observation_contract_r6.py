"""R6: one strict Runtime JSON truth rule across execution receipts and observations.

A malformed Owner field must not be coerced into an Agent-visible claimed state.
Runtime owns vocabulary and physical effect; Gateway only projects valid typed text.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ordivon_gateway.service import GatewayError, GatewayService


class ObservationOwner:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[str] = []

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        assert owner_id == "runtime.linux"
        self.calls.append(tool_name)
        if tool_name == "job.observe":
            return dict(self.payload)
        raise AssertionError(f"unexpected Owner call: {tool_name}")


def observe(owner: ObservationOwner):
    return asyncio.run(
        GatewayService(owner).execution_get(
            "ordivon-exec:v1:runtime.linux:job-r6-type-observe",
            wait_ms=0,
        )
    )


@pytest.mark.parametrize(
    "corrupt",
    [
        {"status": True},
        {"status": ["succeeded"]},
        {"status": None},
        {"status": ""},
        {"deliveryDisposition": True},
        {"deliveryDisposition": {"status": "committed"}},
        {"deliveryDisposition": ""},
        {"executionDisposition": False},
        {"executionDisposition": ["succeeded"]},
        {"executionDisposition": ""},
    ],
)
def test_observation_rejects_malformed_owner_wire_text(corrupt: dict[str, Any]) -> None:
    result: dict[str, Any] = {
        "jobId": "job-r6-type-observe",
        "executionTerminal": False,
        "artifactsAvailable": False,
        "status": "working",
        "deliveryDisposition": "in_progress",
        "executionDisposition": "running",
    }
    result.update(corrupt)
    caller = ObservationOwner(result)
    with pytest.raises(GatewayError, match="Runtime owner response"):
        observe(caller)
    assert caller.calls == ["job.observe"]


@pytest.mark.parametrize("bad_value", [False, 0, [], None, ""])
def test_observation_invalid_attempt_state_must_not_become_fake_text(bad_value: Any) -> None:
    caller = ObservationOwner(
        {
            "jobId": "job-r6-type-observe",
            "executionTerminal": False,
            "artifactsAvailable": False,
            "attemptState": bad_value,
        }
    )
    with pytest.raises(GatewayError, match="Runtime owner response"):
        observe(caller)
    assert caller.calls == ["job.observe"]


def test_observation_future_owner_string_vocab_remains_opaque() -> None:
    caller = ObservationOwner(
        {
            "jobId": "job-r6-type-observe",
            "executionTerminal": False,
            "artifactsAvailable": False,
            "status": "unknown_future_native_state",
            "deliveryDisposition": "unknown_future_delivery",
            "executionDisposition": "unknown_future_execution",
        }
    )
    result = observe(caller)
    assert result.state == "unknown_future_native_state"
    assert result.delivery_disposition == "unknown_future_delivery"
    assert result.execution_disposition == "unknown_future_execution"
    assert result.terminal is False


def test_observation_absent_wire_fields_preserve_unknown_not_success() -> None:
    caller = ObservationOwner(
        {
            "jobId": "job-r6-type-observe",
            "executionTerminal": False,
        }
    )
    result = observe(caller)
    assert result.state == "unknown"
    assert result.delivery_disposition is None
    assert result.execution_disposition is None
    assert result.artifacts_available is None
    assert result.terminal is False
