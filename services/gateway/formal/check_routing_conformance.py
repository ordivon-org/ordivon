"""Bounded implementation-conformance check for Gateway B01 route admission.

This is executable finite exploration of *Python source behavior*, not a
mathematical proof of all Python executions, the TLA+ model, installed service
identity, owner liveness, Security authorization or physical side effects.

Run: python services/gateway/formal/check_routing_conformance.py
"""

from __future__ import annotations

import sys
from dataclasses import replace
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ordivon_gateway.execution_refs import (  # noqa: E402
    GatewayError,
    format_execution_ref,
    parse_execution_ref,
)
from ordivon_gateway.routing import CapabilityRoute, default_routes  # noqa: E402
from ordivon_gateway.service import GatewayService  # noqa: E402


class NoOwner:
    """No Owner is ever contacted by this local, constructor-only check."""

    async def call_tool(self, *_args: object, **_kw: object) -> None:
        raise AssertionError("Gateway attempted a physical Owner effect")


def explore() -> dict[str, int]:
    default = default_routes()
    assert default["execution.linux"].owner_id == "runtime.linux"
    assert default["execution.windows"].owner_id == "runtime.windows"
    assert all(
        isinstance(value, CapabilityRoute) and key == value.capability
        for key, value in default.items()
    )

    caller = NoOwner()
    # None means default; {} must never silently fall back to the default.
    assert set(GatewayService(caller)._routes) == set(default)
    explicit_empty = GatewayService(caller, routes={})
    assert explicit_empty._routes == {}
    assert explicit_empty._catalog._routes == {}

    keys = ("execution.linux", "execution.windows")
    linux = default[keys[0]]
    windows = default[keys[1]]
    # Include exact routes, wrong-key routes and invalid record types.
    choices = (linux, windows, replace(linux, capability="wrong.name"), None)
    explored = 0
    rejected = 0
    admitted = 0
    for left, right in product(choices, repeat=2):
        proposals = ({keys[0]: left, keys[1]: right}, {keys[0]: left}, {keys[1]: right})
        for proposal in proposals:
            expected = all(
                isinstance(value, CapabilityRoute) and key == value.capability
                for key, value in proposal.items()
            )
            explored += 1
            try:
                service = GatewayService(caller, routes=proposal)
            except GatewayError:
                assert not expected, "valid route rejected"
                rejected += 1
            else:
                assert expected, "mismatched route admitted"
                assert service._routes == proposal
                assert service._catalog._routes == proposal
                admitted += 1

    for value in (False, True, 0.0, -1.0, float("nan"), float("inf")):
        try:
            GatewayService(caller, routes={}, projection_timeout_seconds=value)
        except ValueError:
            pass
        else:
            raise AssertionError("nonpositive/nonfinite/bool budget admitted")

    references = 0
    for owner, native in product(
        ("runtime.linux", "runtime.windows"),
        ("job-1", "job-abc", "ws-9", "a"),
    ):
        assert parse_execution_ref(format_execution_ref(owner, native)) == (owner, native)
        references += 1
    for malformed in (
        "",
        "ordivon-exec:v0:runtime.linux:job-1",
        "ordivon-exec:v1:runtime.linux:",
        "ordivon-exec:v1:invalid:job-1",
        "ordivon-exec:v1:runtime.linux:x:y",
    ):
        try:
            parse_execution_ref(malformed)
        except GatewayError:
            pass
        else:
            raise AssertionError(f"malformed reference admitted: {malformed!r}")

    assert rejected > 0 and admitted > 0
    return {
        "route_maps": explored,
        "admitted": admitted,
        "rejected": rejected,
        "roundtrips": references,
    }


if __name__ == "__main__":
    print("GATEWAY_B01_BOUND_CONFORMANCE", explore())
