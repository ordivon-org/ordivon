"""Preserve strict observation wait semantics across the native SDK."""

from __future__ import annotations

import asyncio

import pytest
from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService


class _ObservationOwner:
    def __init__(self):
        self.calls = []

    def is_configured(self, owner_id):
        return owner_id == "runtime.linux"

    async def call_tool(self, owner_id, tool_name, arguments):
        self.calls.append((owner_id, tool_name, arguments))
        assert owner_id == "runtime.linux" and tool_name == "job.observe"
        return {
            "jobId": arguments["jobId"],
            "status": "starting",
            "attemptState": "starting",
            "executionTerminal": False,
            "deliveryDisposition": "reconciliation_required",
            "executionDisposition": None,
            "recoveryRequired": True,
            "artifactsAvailable": False,
            "resultAvailable": False,
        }


@pytest.mark.parametrize("value", [True, False, "1", 1.0, 1.5, -1, 30_001])
def test_execution_get_native_wire_rejects_invalid_wait(value):
    owner = _ObservationOwner()

    async def run():
        async with Client(build_server(GatewayService(owner)), raise_exceptions=False) as client:
            result = await client.call_tool(
                "execution.get",
                {"operationRef": "ordivon-exec:v1:runtime.linux:job-fixture", "waitMs": value},
            )
            assert result.is_error

    asyncio.run(run())
    assert owner.calls == []


@pytest.mark.parametrize("value", [0, 1, 30_000])
def test_execution_get_native_wire_preserves_valid_wait(value):
    owner = _ObservationOwner()

    async def run():
        async with Client(build_server(GatewayService(owner)), raise_exceptions=False) as client:
            result = await client.call_tool(
                "execution.get",
                {"operationRef": "ordivon-exec:v1:runtime.linux:job-fixture", "waitMs": value},
            )
            assert not result.is_error
            record = result.structured_content
            assert record["delivery_disposition"] == "reconciliation_required"
            assert record["recovery_required"] is True

    asyncio.run(run())
    assert len(owner.calls) == 1
    assert owner.calls[0][2]["waitMs"] == value
