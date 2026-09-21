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


def test_persistent_trace_backend_cannot_regress_to_not_admitted() -> None:
    value = graph()
    value["notAdmitted"].append("persistent-queryable-trace-backend")
    with pytest.raises(module.ArchitectureDocsError, match="cannot remain not-admitted"):
        module.validate_deployed_graph(value)


def test_vector_trace_preservation_is_architecture_contract() -> None:
    value = graph()
    value["observability"]["ingress"]["preserveOtlpTraces"] = False
    with pytest.raises(module.ArchitectureDocsError, match="preserve OTLP trace"):
        module.validate_deployed_graph(value)


def test_tempo_remains_on_demand_non_semantic_backend() -> None:
    value = graph()
    value["observability"]["status"] = "semantic-authority"
    with pytest.raises(module.ArchitectureDocsError, match="deployed-on-demand"):
        module.validate_deployed_graph(value)


def test_gateway_trace_export_remains_opt_in_by_default() -> None:
    value = graph()
    value["observability"]["gatewayExport"]["base"] = "OTEL_TRACES_EXPORTER=otlp_proto_http"
    with pytest.raises(module.ArchitectureDocsError, match="base trace exporter"):
        module.validate_deployed_graph(value)


def test_trace_storage_never_becomes_product_correctness_authority() -> None:
    value = graph()
    value["observability"]["gatewayExport"]["requiredForProductCorrectness"] = True
    with pytest.raises(module.ArchitectureDocsError, match="product correctness"):
        module.validate_deployed_graph(value)


def test_heavy_observability_default_posture_stays_cold() -> None:
    value = graph()
    value["observability"]["defaultPosture"] = "always-on"
    with pytest.raises(module.ArchitectureDocsError, match="cold by default"):
        module.validate_deployed_graph(value)


def test_gateway_normal_host_surface_cannot_drop_actions() -> None:
    value = graph()
    value["hostNorthbound"]["normalTools"].remove("continuity.checkpoint")
    with pytest.raises(module.ArchitectureDocsError, match="normal Host northbound Tool set"):
        module.validate_deployed_graph(value)


def test_gateway_cannot_absorb_host_admin_surface() -> None:
    value = graph()
    value["hostNorthbound"]["adminOnlyDirect"] = []
    with pytest.raises(module.ArchitectureDocsError, match="status/Doctor"):
        module.validate_deployed_graph(value)


def test_connector_catalog_owner_stays_external() -> None:
    value = graph()
    value["hostNorthbound"]["connectorCatalogOwner"] = "gateway"
    with pytest.raises(module.ArchitectureDocsError, match="catalog freshness owner"):
        module.validate_deployed_graph(value)
