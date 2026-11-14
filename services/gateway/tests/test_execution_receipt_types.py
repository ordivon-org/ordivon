"""Owner receipt text must preserve JSON types, not Python truthiness.

These tests exercise Agent-facing result projection using the already existing
GatewayService/Runtime Owner boundary, without a second gateway protocol.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ordivon_gateway.service import GatewayError, GatewayService


class OwnerReceiptCaller:
    def __init__(self, owner_response: dict[str, Any]) -> None:
        self.owner_response = owner_response
        self.calls: list[tuple[str, str]] = []

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_id, tool_name))
        return self.owner_response


def submit(caller: OwnerReceiptCaller):
    return asyncio.run(
        GatewayService(caller).execution_submit(
            capability="execution.linux",
            request_id="gateway-owner-receipt-contract-r1",
            workspace_id="ws-receipt-contract",
            executable="/usr/bin/true",
            args=[],
            context="trusted_local",
        )
    )


def cancel(caller: OwnerReceiptCaller):
    return asyncio.run(
        GatewayService(caller).execution_cancel(
            "ordivon-exec:v1:runtime.linux:job-receipt-contract"
        )
    )


@pytest.mark.parametrize(
    "mutation",
    [
        {"status": True},
        {"status": ["succeeded"]},
        {"status": None},
        {"status": ""},
        {"deliveryDisposition": True},
        {"deliveryDisposition": {"state": "committed"}},
        {"deliveryDisposition": ""},
    ],
)
@pytest.mark.parametrize("method", [submit, cancel])
def test_agent_receipt_rejects_malformed_owner_text(method, mutation: dict[str, Any]) -> None:
    response: dict[str, Any] = {
        "jobId": "job-receipt-contract",
        "status": "succeeded",
        "executionTerminal": True,
        "deliveryDisposition": "committed",
    }
    response.update(mutation)
    caller = OwnerReceiptCaller(response)
    with pytest.raises(GatewayError, match="Runtime owner response"):
        method(caller)
    assert len(caller.calls) == 1


@pytest.mark.parametrize("method", [submit, cancel])
def test_agent_receipt_requires_typed_fallback_attempt_state(method) -> None:
    caller = OwnerReceiptCaller(
        {
            "jobId": "job-receipt-contract",
            "attemptState": False,
            "executionTerminal": True,
        }
    )
    with pytest.raises(GatewayError, match="Runtime owner response"):
        method(caller)
    assert len(caller.calls) == 1


@pytest.mark.parametrize("method", [submit, cancel])
def test_agent_receipt_preserves_open_owner_state_vocabulary(method) -> None:
    caller = OwnerReceiptCaller(
        {
            "jobId": "job-receipt-contract",
            "status": "future_native_state",
            "executionTerminal": False,
            "deliveryDisposition": "future_disposition",
        }
    )
    receipt = method(caller)
    assert receipt.state == "future_native_state"
    assert receipt.delivery_disposition == "future_disposition"
    assert receipt.terminal is False


def test_agent_receipt_absent_optional_text_is_unknown_not_success() -> None:
    caller = OwnerReceiptCaller(
        {
            "jobId": "job-receipt-contract",
            "executionTerminal": False,
        }
    )
    receipt = submit(caller)
    assert receipt.state == "unknown"
    assert receipt.delivery_disposition is None
