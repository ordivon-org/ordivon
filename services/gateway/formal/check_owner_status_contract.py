"""Bounded conformance of Gateway's Runtime status observation boundary.

Specification:
  - Only literal JSON booleans are admissible Owner availability flags.
  - available=True implies configured=True.
  - Malformed/contradictory flags are UNKNOWN, never positive availability.
  - Source Owner target inventory must be a list with exactly one matching
    identity; explicitly supplied context inventories must be lists.
  - Gateway does not create physical Owner truth.

This enumerates a finite adversarial input domain. It is not a universal
Python-to-model refinement proof or a live Runtime/Host observation.
Run under the exact Gateway environment:
  uv run python formal/check_owner_status_contract.py
"""

from __future__ import annotations

import asyncio
from itertools import product
from typing import Any

from ordivon_gateway.capability_projection import project_execution_capability
from ordivon_gateway.routing import default_routes
from ordivon_gateway.service import GatewayService

VALUES: tuple[Any, ...] = (
    True,
    False,
    0,
    1,
    "true",
    "false",
    "",
    None,
    [],
    {},
)


class SyntheticRuntime:
    """Read-only synthetic Owner, never a physical execution or RPC."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response

    def is_configured(self, owner_id: str) -> bool:
        return owner_id == "runtime.windows"

    def configuration_error(self, owner_id: str) -> str | None:
        if self.is_configured(owner_id):
            return None
        return "unconfigured"

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        assert owner_id == "runtime.windows"
        assert tool_name == "runtime.describe"
        assert arguments == {"schemaVersion": 1}
        return self.response


async def check() -> dict[str, int]:
    route = default_routes()["execution.windows"]
    examined = invalid = available = 0

    for configured, offered in product(VALUES, repeat=2):
        admissible = (
            type(configured) is bool
            and type(offered) is bool
            and not (configured is False and offered is True)
        )
        target = {
            "target": "windows_native",
            "configured": configured,
            "available": offered,
            "windowsAuthorities": ["limited"],
        }
        observed = {"node": {"nodeId": "windows-native"}, "targets": [target]}
        projected = project_execution_capability(
            route, configured_at_gateway=True, owner_response=observed
        )
        expected_available = admissible and configured is True and offered is True
        assert projected.available is expected_available
        if admissible:
            assert projected.observation_error is None
            assert projected.configured is configured
        else:
            assert projected.observation_error is not None
            assert projected.configured is False
            invalid += 1
        available += int(projected.available)

        service = GatewayService(SyntheticRuntime(observed))
        artifact_projection = await service.capability_describe("artifact.runtime")
        artifact = artifact_projection.capabilities[0]
        assert artifact.available is expected_available
        malformed_reported = "invalid Runtime target status" in (artifact.observation_error or "")
        assert malformed_reported is (not admissible)
        if expected_available:
            assert artifact.owner_node_ids == ["windows-native"]
        else:
            assert artifact.owner_node_ids == []
        examined += 1

    assert examined == len(VALUES) ** 2
    assert available == 1

    # Source-refinement witnesses for the extended B03 TLA inventory/context
    # abstraction. These are actual projection calls, not duplicated truth.
    qualified: dict[str, Any] = {
        "target": "windows_native",
        "configured": True,
        "available": True,
        "windowsAuthorities": ["limited"],
    }
    inventory_cases: list[tuple[dict[str, Any], bool]] = [
        ({}, False),  # Missing targets container.
        ({"targets": None}, False),
        ({"targets": {"target": qualified}}, False),
        ({"targets": []}, False),  # No matching route.
        ({"targets": [qualified, qualified]}, False),  # Ambiguous match.
        ({"targets": [{**qualified, "windowsAuthorities": None}]}, False),
        ({"targets": [{**qualified, "windowsContexts": None}]}, False),
        ({"targets": [{"target": "windows_native", "configured": True, "available": True}]}, True),
        ({"targets": [{**qualified, "windowsContexts": []}]}, True),
    ]
    malformed_inventories = 0
    for response, should_be_available in inventory_cases:
        projected = project_execution_capability(
            route, configured_at_gateway=True, owner_response=response
        )
        assert projected.available is should_be_available
        assert projected.readiness_state == ("ready" if should_be_available else "unknown")
        assert (projected.observation_error is None) is should_be_available
        malformed_inventories += int(not should_be_available)
        service = GatewayService(SyntheticRuntime(response))
        described = await service.capability_describe("execution.windows")
        actual = described.capabilities[0]
        assert actual.available is should_be_available
        assert actual.readiness_state == projected.readiness_state

    return {
        "status_pairs": examined,
        "invalid_or_contradictory": invalid,
        "positively_available": available,
        "inventory_cases": len(inventory_cases),
        "invalid_or_ambiguous_inventories": malformed_inventories,
    }


if __name__ == "__main__":
    print("GATEWAY_OWNER_STATUS_BOUND_CONFORMANCE", asyncio.run(check()))
