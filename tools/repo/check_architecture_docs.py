from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "docs" / "architecture" / "CURRENT_ARCHITECTURE.md"
DEPLOYED = ROOT / "docs" / "architecture" / "deployed-architecture-r1.json"
PLUGIN = ROOT / "extensions" / "ordivon-control-plane" / "mcp.json"
ROUTES = ROOT / "services" / "gateway" / "src" / "ordivon_gateway" / "routes.py"
GATEWAY_MCP = ROOT / "services" / "gateway" / "src" / "ordivon_gateway" / "mcp_server.py"
HOST_NORTHBOUND_ACCEPTANCE = ROOT / "docs" / "architecture" / "gateway-host-northbound-acceptance-20260922.json"
METHOD_ROUTER = ROOT / ".agents" / "skills" / "method-router" / "SKILL.md"
README = ROOT / "README.md"

TEMPO_CONFIG = ROOT / "platform" / "workstation" / "observability" / "tempo.yaml"
VECTOR_CONFIG = ROOT / "platform" / "workstation" / "observability" / "vector.yaml"
GRAFANA_DATASOURCES = ROOT / "platform" / "workstation" / "observability" / "grafana-datasources.yaml"
HEAVY_TARGET = ROOT / "platform" / "workstation" / "systemd" / "ordivon-observability-heavy.target"
TRACE_ACCEPTANCE = ROOT / "docs" / "architecture" / "persistent-trace-backend-acceptance-20260921.json"
TEMPO_QUADLET = ROOT / "platform" / "workstation" / "tempo" / "ordivon-tempo.container"

HISTORICAL = {
    ROOT / "docs" / "architecture" / "ARCHITECTURE_CONVERGENCE_A01R2.md":
        "Historical standing: SUPERSEDED FOR CURRENT DEPLOYMENT STATUS",
    ROOT / "docs" / "architecture" / "ORDIVON_COMPOSITION_ARCHITECTURE_EXECUTION_PLAN_R1.md":
        "Historical standing: EXECUTED / SUPERSEDED FOR CURRENT STATE",
    ROOT / "docs" / "architecture" / "AGENT_PLUGIN_R4_ACCEPTANCE_20260921.md":
        "Historical standing: SUPERSEDED BY C02/D01 FOR CURRENT ENDPOINT TOPOLOGY",
}

EXPECTED_CAPABILITIES = {
    "artifact.runtime",
    "continuity.external",
    "execution.linux",
    "execution.windows",
}

EXPECTED_GATEWAY_TOOLS = {
    "system.describe",
    "capability.describe",
    "execution.submit",
    "execution.resolve",
    "execution.get",
    "execution.cancel",
    "artifact.read",
    "continuity.get",
    "continuity.list",
    "continuity.find",
    "continuity.observe",
    "continuity.adopt",
    "continuity.checkpoint",
    "continuity.changes",
    "continuity.attention",
    "collaboration.list",
    "collaboration.search",
    "collaboration.post",
    "collaboration.publish",
}

EXPECTED_HOST_NORTHBOUND_TOOLS = {
    "continuity.get",
    "continuity.list",
    "continuity.find",
    "continuity.observe",
    "continuity.adopt",
    "continuity.checkpoint",
    "continuity.changes",
    "continuity.attention",
    "collaboration.list",
    "collaboration.search",
    "collaboration.post",
    "collaboration.publish",
}


class ArchitectureDocsError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ArchitectureDocsError(f"{path} root must be an object")
    return value


def validate_deployed_graph(value: dict[str, Any]) -> None:
    if value.get("schemaVersion") != 1:
        raise ArchitectureDocsError("deployed architecture schemaVersion must be 1")
    if value.get("kind") != "ordivon.deployed-architecture":
        raise ArchitectureDocsError("unexpected deployed architecture kind")
    if value.get("status") != "CURRENT_DEPLOYED_BASELINE":
        raise ArchitectureDocsError("deployed architecture must be CURRENT_DEPLOYED_BASELINE")

    northbound = value.get("defaultNorthbound")
    if not isinstance(northbound, dict):
        raise ArchitectureDocsError("defaultNorthbound must be an object")
    if northbound.get("endpoint") != "https://gateway-mcp.ordivon.com/mcp":
        raise ArchitectureDocsError("default northbound must be Gateway MCP")
    if northbound.get("authoritative") is not False:
        raise ArchitectureDocsError("Gateway must remain non-authoritative")
    if northbound.get("directRuntimeHostAreDefault") is not False:
        raise ArchitectureDocsError("direct Runtime/Host must not be default northbound")

    routers = value.get("routers")
    if not isinstance(routers, dict):
        raise ArchitectureDocsError("routers must be an object")
    method = routers.get("methodRouter")
    capability = routers.get("capabilityRouter")
    if not isinstance(method, dict) or not isinstance(capability, dict):
        raise ArchitectureDocsError("both Method Router and Capability Router are required")
    if method.get("kind") != "agent-skill":
        raise ArchitectureDocsError("Method Router must be an Agent Skill")
    if capability.get("kind") != "gateway-static-owner-projection":
        raise ArchitectureDocsError("Capability Router must be a Gateway projection")
    if method.get("path") == capability.get("path"):
        raise ArchitectureDocsError("Method Router and Capability Router must remain distinct")

    capabilities = capability.get("capabilities")
    if not isinstance(capabilities, list) or set(capabilities) != EXPECTED_CAPABILITIES:
        raise ArchitectureDocsError("deployed Gateway capability set drifted")

    retired = value.get("retired")
    if not isinstance(retired, list) or not any(
        isinstance(item, dict)
        and item.get("id") == "agent-service"
        and item.get("standing") == "RETIRED_DO_NOT_RECONSTRUCT"
        for item in retired
    ):
        raise ArchitectureDocsError("retired Agent Service standing is missing")

    observability = value.get("observability")
    if not isinstance(observability, dict):
        raise ArchitectureDocsError("deployed observability projection is missing")
    if observability.get("status") != "deployed-on-demand":
        raise ArchitectureDocsError("trace backend must remain deployed-on-demand")
    ingress = observability.get("ingress")
    backend = observability.get("traceBackend")
    export = observability.get("gatewayExport")
    if not isinstance(ingress, dict) or ingress.get("preserveOtlpTraces") is not True:
        raise ArchitectureDocsError("Vector must preserve OTLP trace envelopes")
    if not isinstance(backend, dict) or backend.get("owner") != "tempo":
        raise ArchitectureDocsError("Tempo must own trace persistence/query semantics")
    if backend.get("queryApi") != "127.0.0.1:3200":
        raise ArchitectureDocsError("Tempo query API must remain loopback")
    if not isinstance(export, dict) or export.get("base") != "OTEL_TRACES_EXPORTER=none":
        raise ArchitectureDocsError("Gateway base trace exporter must remain disabled")
    if export.get("requiredForProductCorrectness") is not False:
        raise ArchitectureDocsError("observability must not become a product correctness dependency")
    if observability.get("defaultPosture") != "cold-inactive":
        raise ArchitectureDocsError("heavy observability must remain cold by default")
    if "always-on-mandatory-trace-backend" not in value.get("notAdmitted", []):
        raise ArchitectureDocsError("always-on mandatory tracing must remain not-admitted")
    if "persistent-queryable-trace-backend" in value.get("notAdmitted", []):
        raise ArchitectureDocsError("persistent trace backend cannot remain not-admitted")

    host_northbound = value.get("hostNorthbound")
    if not isinstance(host_northbound, dict) or host_northbound.get("status") != "deployed":
        raise ArchitectureDocsError("Host northbound seam must remain deployed")
    if host_northbound.get("semanticOwner") != "host" or host_northbound.get("gatewayAuthority") != "projection-only":
        raise ArchitectureDocsError("Gateway must not absorb Host semantic authority")
    if host_northbound.get("checkpointSchemaOwner") != "host":
        raise ArchitectureDocsError("Host must remain WorkingCheckpoint schema owner")
    if set(host_northbound.get("normalTools", [])) != EXPECTED_HOST_NORTHBOUND_TOOLS:
        raise ArchitectureDocsError("normal Host northbound Tool set drifted")
    if host_northbound.get("adminOnlyDirect") != ["host.status"]:
        raise ArchitectureDocsError("Host status/Doctor must remain direct admin/recovery only")
    if host_northbound.get("connectorCatalogOwner") != "mcp-client-connector":
        raise ArchitectureDocsError("connector catalog freshness owner drifted")


def validate_plugin(value: dict[str, Any]) -> None:
    servers = value.get("mcpServers")
    if not isinstance(servers, dict) or set(servers) != {"ordivon-gateway"}:
        raise ArchitectureDocsError("default Plugin must declare exactly one Gateway MCP server")
    gateway = servers["ordivon-gateway"]
    if not isinstance(gateway, dict) or gateway.get("url") != "https://gateway-mcp.ordivon.com/mcp":
        raise ArchitectureDocsError("default Plugin Gateway endpoint drifted")


def route_capabilities(source: str) -> set[str]:
    return set(re.findall(r'capability="([^"]+)"', source))


def gateway_tools(source: str) -> set[str]:
    return set(re.findall(r'@server\.tool\(name="([^"]+)"\)', source))


def validate_current_document(text: str) -> None:
    required = [
        "Status: **CURRENT CANONICAL / DEPLOYED BASELINE**",
        "Method Router ≠ Capability Router",
        "Harness is not currently a routed Gateway owner",
        "historical Ordivon Agent Service is **RETIRED**",
        "OTEL_TRACES_EXPORTER=none",
        "Vector OTLP → Tempo",
        "deployed on demand",
        "cold/inactive by default",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise ArchitectureDocsError(f"current architecture document missing: {missing}")
    for forbidden in (
        "planned thin Gateway",
        "Gateway: **BUILD THIN",
        "Method Router: **BUILD AS SKILL",
        "default Agent Plugin still points directly",
    ):
        if forbidden in text:
            raise ArchitectureDocsError(f"stale current-state wording present: {forbidden}")


def validate_repository(root: Path = ROOT) -> None:
    current = root / CURRENT.relative_to(ROOT)
    deployed = root / DEPLOYED.relative_to(ROOT)
    plugin = root / PLUGIN.relative_to(ROOT)
    routes = root / ROUTES.relative_to(ROOT)
    gateway_mcp = root / GATEWAY_MCP.relative_to(ROOT)
    host_northbound_acceptance = root / HOST_NORTHBOUND_ACCEPTANCE.relative_to(ROOT)
    method_router = root / METHOD_ROUTER.relative_to(ROOT)
    readme = root / README.relative_to(ROOT)

    validate_current_document(current.read_text(encoding="utf-8"))
    graph = _load_json(deployed)
    validate_deployed_graph(graph)
    validate_plugin(_load_json(plugin))

    observed = route_capabilities(routes.read_text(encoding="utf-8"))
    if observed != EXPECTED_CAPABILITIES:
        raise ArchitectureDocsError(
            f"Gateway route source differs from deployed graph: {sorted(observed)}"
        )

    observed_tools = gateway_tools(gateway_mcp.read_text(encoding="utf-8"))
    if observed_tools != EXPECTED_GATEWAY_TOOLS:
        raise ArchitectureDocsError(
            f"Gateway public Tool surface drifted: {sorted(observed_tools)}"
        )
    host_acceptance = _load_json(host_northbound_acceptance)
    if host_acceptance.get("status") != "SERVER_DEPLOYED_LIVE_OWNER_PATH_ACCEPTED_CLIENT_REFRESH_PENDING":
        raise ArchitectureDocsError("Gateway Host northbound acceptance status drifted")

    if not method_router.is_file():
        raise ArchitectureDocsError("canonical Method Router Skill is missing")
    if "docs/architecture/CURRENT_ARCHITECTURE.md" not in readme.read_text(encoding="utf-8"):
        raise ArchitectureDocsError("root README must point to canonical current architecture")

    tempo = (root / TEMPO_CONFIG.relative_to(ROOT)).read_text(encoding="utf-8")
    vector = (root / VECTOR_CONFIG.relative_to(ROOT)).read_text(encoding="utf-8")
    datasources = (root / GRAFANA_DATASOURCES.relative_to(ROOT)).read_text(encoding="utf-8")
    target = (root / HEAVY_TARGET.relative_to(ROOT)).read_text(encoding="utf-8")
    quadlet = (root / TEMPO_QUADLET.relative_to(ROOT)).read_text(encoding="utf-8")
    trace_acceptance = _load_json(root / TRACE_ACCEPTANCE.relative_to(ROOT))
    if "http_listen_address: 127.0.0.1" not in tempo or 'endpoint: "127.0.0.1:14318"' not in tempo:
        raise ArchitectureDocsError("Tempo trace endpoints must remain loopback")
    if "backend: local" not in tempo:
        raise ArchitectureDocsError("Tempo local backend contract drifted")
    if "traces: true" not in vector or "otel_traces_tempo:" not in vector:
        raise ArchitectureDocsError("Vector OTLP trace preservation/Tempo sink drifted")
    if "http://127.0.0.1:14318/v1/traces" not in vector:
        raise ArchitectureDocsError("Vector Tempo OTLP sink endpoint drifted")
    if "uid: operations-tempo" not in datasources or "type: tempo" not in datasources:
        raise ArchitectureDocsError("Grafana Tempo datasource drifted")
    if "ordivon-tempo.service" not in target:
        raise ArchitectureDocsError("heavy observability profile lost Tempo")
    if "StopTimeout=60" not in quadlet or "TimeoutStopSec=75" not in quadlet:
        raise ArchitectureDocsError("Tempo graceful cold-stop budget drifted")
    if trace_acceptance.get("status") != "ACCEPTED_DEPLOYED_ON_DEMAND":
        raise ArchitectureDocsError("persistent trace backend lacks accepted live evidence")

    for path, marker in HISTORICAL.items():
        candidate = root / path.relative_to(ROOT)
        if marker not in candidate.read_text(encoding="utf-8"):
            raise ArchitectureDocsError(f"historical architecture file lacks supersession marker: {candidate}")


def main() -> int:
    try:
        validate_repository()
    except (OSError, json.JSONDecodeError, ArchitectureDocsError) as exc:
        print(f"architecture documentation drift check failed: {exc}")
        return 2
    print("architecture documentation drift check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
