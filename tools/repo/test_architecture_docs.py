from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "repo" / "check_architecture_docs.py"
GRAPH = ROOT / "docs" / "architecture" / "deployed-architecture-r1.json"

spec = importlib.util.spec_from_file_location("check_architecture_docs", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def graph():
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def test_current_repository_architecture_docs_are_converged() -> None:
    module.validate_repository(ROOT)


def test_gateway_cannot_become_authoritative() -> None:
    value = graph()
    value["defaultNorthbound"]["authoritative"] = True
    with pytest.raises(module.ArchitectureDocsError, match="non-authoritative"):
        module.validate_deployed_graph(value)


def test_method_router_cannot_become_gateway_router() -> None:
    value = graph()
    value["routers"]["methodRouter"]["kind"] = "gateway-static-owner-projection"
    with pytest.raises(module.ArchitectureDocsError, match="Method Router"):
        module.validate_deployed_graph(value)


def test_deployed_capability_set_is_exact() -> None:
    value = graph()
    value["routers"]["capabilityRouter"]["capabilities"].append("harness.run")
    with pytest.raises(module.ArchitectureDocsError, match="capability set"):
        module.validate_deployed_graph(value)


def test_default_plugin_rejects_direct_owner_servers() -> None:
    value = {
        "mcpServers": {
            "ordivon-gateway": {
                "url": "https://gateway-mcp.ordivon.com/mcp"
            },
            "ordivonRuntime": {
                "url": "https://mcp.ordivon.com/mcp"
            },
        }
    }
    with pytest.raises(module.ArchitectureDocsError, match="exactly one Gateway"):
        module.validate_plugin(value)
