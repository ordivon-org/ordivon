from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "docs" / "architecture" / "CURRENT_ARCHITECTURE.md"
DEPLOYED = ROOT / "docs" / "architecture" / "deployed-architecture-r1.json"
PLUGIN = ROOT / "meta" / "next" / "plugins" / "ordivon-control-plane" / "mcp.json"
ROUTES = ROOT / "services" / "gateway" / "src" / "ordivon_gateway" / "routes.py"
METHOD_ROUTER = ROOT / "meta" / "next" / ".agents" / "skills" / "method-router" / "SKILL.md"
README = ROOT / "README.md"

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


def validate_plugin(value: dict[str, Any]) -> None:
    servers = value.get("mcpServers")
    if not isinstance(servers, dict) or set(servers) != {"ordivon-gateway"}:
        raise ArchitectureDocsError("default Plugin must declare exactly one Gateway MCP server")
    gateway = servers["ordivon-gateway"]
    if not isinstance(gateway, dict) or gateway.get("url") != "https://gateway-mcp.ordivon.com/mcp":
        raise ArchitectureDocsError("default Plugin Gateway endpoint drifted")


def route_capabilities(source: str) -> set[str]:
    return set(re.findall(r'capability="([^"]+)"', source))


def validate_current_document(text: str) -> None:
    required = [
        "Status: **CURRENT CANONICAL / DEPLOYED BASELINE**",
        "Method Router ≠ Capability Router",
        "Harness is not currently a routed Gateway owner",
        "historical Ordivon Agent Service is **RETIRED**",
        "OTEL_TRACES_EXPORTER=none",
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

    if not method_router.is_file():
        raise ArchitectureDocsError("canonical Method Router Skill is missing")
    if "docs/architecture/CURRENT_ARCHITECTURE.md" not in readme.read_text(encoding="utf-8"):
        raise ArchitectureDocsError("root README must point to canonical current architecture")

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
