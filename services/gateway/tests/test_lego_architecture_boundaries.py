"""Architecture regression: thoughts guide logic, logic contracts drive Owner adapters.

The tests guard *dependency direction*, not style/approval/identity policy.
"""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from typing import Any

import pytest

from ordivon_gateway.capabilities.host.dispatch import HostContinuityAdapter
from ordivon_gateway.logic.execution_refs import GatewayError
from ordivon_gateway.logic.host_tool_contracts import SOCIAL_WORK_HOST_TOOLS
from ordivon_gateway.logic.routing import default_routes

ROOT = Path(__file__).resolve().parents[1] / "src" / "ordivon_gateway"


def test_business_root_is_composition_and_public_schema_only() -> None:
    assert {p.name for p in ROOT.glob("*.py")} == {
        "__init__.py",
        "contracts.py",
        "mcp_server.py",
        "service.py",
    }
    assert (ROOT / "transport/http.py").exists()
    assert (ROOT / "transport/upstream.py").exists()


def test_logic_representation_never_imports_owner_adapters_or_security() -> None:
    for file in (ROOT / "logic").rglob("*.py"):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for forbidden in ("capabilities", "transport", "security", "service", "mcp_server"):
                    assert forbidden not in module.split("."), (file.name, module)
            elif isinstance(node, ast.Import):
                for imported in node.names:
                    assert not imported.name.startswith("ordivon_gateway.capabilities"), file.name


def test_effectful_abilities_depend_on_owner_protocol_not_concrete_mcp_transport() -> None:
    for file in (ROOT / "capabilities").rglob("*.py"):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert "transport" not in node.module.split("."), file.name
                assert "authzen_authorizer" not in node.module.split("."), file.name


def test_route_table_is_an_exact_capability_to_natural_owner_mapping() -> None:
    routes = default_routes()
    assert all(key == route.capability for key, route in routes.items())
    assert routes["execution.linux"].owner_id == "runtime.linux"
    assert routes["execution.windows"].owner_id == "runtime.windows"
    assert routes["continuity.external"].owner_id == "host"
    assert routes["artifact.runtime"].owner_id == "runtime.dynamic"


def test_host_ability_forwards_exactly_one_owner_request_no_domain_claim() -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []

    class Caller:
        async def call_tool(
            self, owner_id: str, tool_name: str, arguments: dict[str, Any]
        ) -> dict[str, Any]:
            calls.append((owner_id, tool_name, arguments))
            return {"kind": "host-owner-response", "status": "unknown"}

    adapter = HostContinuityAdapter(Caller())  # type: ignore[arg-type]
    payload = {"workRef": "work:some:actual"}
    result = asyncio.run(adapter.call("work.get", payload))
    assert calls == [("host", "work.get", payload)]
    assert result == {"kind": "host-owner-response", "status": "unknown"}


def test_host_ability_rejects_unknown_tool_before_owner_effect() -> None:
    class NeverCalled:
        async def call_tool(self, *_args: Any) -> dict[str, Any]:
            raise AssertionError("unqualified Host tool must not reach the Owner")

    adapter = HostContinuityAdapter(NeverCalled())  # type: ignore[arg-type]
    assert "work.get" in SOCIAL_WORK_HOST_TOOLS
    with pytest.raises(GatewayError, match="unsupported Host Social Work tool"):
        asyncio.run(adapter.call("host.pool.stats", {}))
