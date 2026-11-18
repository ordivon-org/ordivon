"""Provider observation states must not be confused with executable truth."""

from __future__ import annotations

import asyncio

import pytest

from ordivon_gateway.capability_projection import project_execution_capability
from ordivon_gateway.contracts import CapabilityDescriptor
from ordivon_gateway.routing import default_routes
from ordivon_gateway.service import GatewayService


def _descriptor(
    *, configured: bool, available: bool, observation_error: str | None = None
) -> CapabilityDescriptor:
    return CapabilityDescriptor(
        capability="execution.windows",
        owner_id="runtime.windows",
        category="execution",
        configured=configured,
        available=available,
        context_mode="provider-defined-json",
        observation_error=observation_error,
        truth_boundary="Runtime-owned",
    )


@pytest.mark.parametrize(
    ("configured", "available", "error", "expected"),
    [
        (True, True, None, "ready"),
        (False, False, None, "not_ready"),
        (False, False, "not configured", "unknown"),
        (True, False, None, "not_ready"),
        (True, False, "TimeoutError: observation UNKNOWN", "unknown"),
        (True, True, "another owner failed", "ready"),
    ],
)
def test_readiness_is_derived_and_serialized_without_duplicate_authority(
    configured: bool, available: bool, error: str | None, expected: str
) -> None:
    item = _descriptor(configured=configured, available=available, observation_error=error)
    assert item.readiness_state == expected
    payload = item.model_dump(mode="json")
    assert payload["readiness_state"] == expected
    assert CapabilityDescriptor.model_validate(payload).readiness_state == expected
    # A caller-supplied contradictory discriminator is normalized, not trusted.
    payload["readiness_state"] = "ready" if expected != "ready" else "unknown"
    assert CapabilityDescriptor.model_validate(payload).readiness_state == expected


def test_invalid_runtime_status_preserves_configured_gateway_route_but_unknown_readiness() -> None:
    route = default_routes()["execution.windows"]
    item = project_execution_capability(
        route,
        configured_at_gateway=True,
        owner_response={
            "targets": [{"target": "windows_native", "configured": "true", "available": True}]
        },
    )
    assert item.configured is False
    assert item.available is False
    assert item.readiness_state == "unknown"
    assert "invalid" in (item.observation_error or "")


class _NoOwners:
    def is_configured(self, owner_id: str) -> bool:
        return False

    def configuration_error(self, owner_id: str) -> str | None:
        return "owner endpoint is not configured"

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict) -> dict:
        raise AssertionError("metadata discovery must not run owner effects")


def test_research_route_is_discoverable_but_never_implicitly_ready() -> None:
    svc = GatewayService(_NoOwners())
    item = asyncio.run(svc.capability_describe("research.statistical.analysis")).capabilities[0]
    assert item.configured is True
    assert item.available is False
    assert item.readiness_state == "unknown"
    matching = asyncio.run(
        svc.capability_search(query="research.statistical.analysis", include_unavailable=False)
    )
    assert matching.matches[0].capability.readiness_state == "unknown"


def test_actual_mcp_tool_output_contract_accepts_readiness_discriminator() -> None:
    """Protect the deployed tool schema, not only internal Pydantic model tests."""
    from mcp import Client

    from ordivon_gateway.mcp_server import build_server

    async def invoke() -> None:
        async with Client(build_server(), raise_exceptions=True) as client:
            result = await client.call_tool(
                "capability.describe", {"capability": "research.statistical.analysis"}
            )
            assert not result.is_error
            assert result.structured_content is not None
            descriptor = result.structured_content["capabilities"][0]
            assert descriptor["available"] is False
            assert descriptor["readiness_state"] == "unknown"

    asyncio.run(invoke())
