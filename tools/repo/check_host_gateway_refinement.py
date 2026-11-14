"""Prove one Host→Gateway MCP tool-argument refinement using the real SDKs.

This is a repo-level migration/release gate, NOT an installed connector probe.
Do not infer live usage from source-tool absence or fill missing output types.
It reuses the Host Rust migration's existing SDK schema comparison helper.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "services/host"
GATEWAY = ROOT / "services/gateway"
AUDITOR = HOST / "rust/tools/audit_mcp_surface.py"
HOST_OMISSIONS = frozenset({"host.pool.stats", "message.get"})
HOST_NAMESPACES = ("actor.", "attention.", "host.", "message.", "space.",
                   "subscription.", "topic.", "work.")
# An upstream Host-external extension needs its own explicit release review.
REVIEWED_GATEWAY_EXTENSIONS: frozenset[str] = frozenset()


SDK_DUMP = """
import asyncio, json
from {module}.mcp_server import build_server
server = {builder}
items = asyncio.run(server.list_tools())
print(json.dumps(
  [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in items],
  sort_keys=True, ensure_ascii=False, separators=(",", ":"),
))
"""


def sdk_registry(project: Path, *, module: str, builder: str) -> dict[str, dict]:
    result = subprocess.run(
        ["uv", "run", "--locked", "python", "-c", SDK_DUMP.format(
            module=module, builder=builder,
        )],
        cwd=project, text=True, capture_output=True, check=True,
        timeout=120,
    )
    items = json.loads(result.stdout)
    names = [tool["name"] for tool in items]
    if len(names) != len(set(names)):
        raise RuntimeError(f"{module} SDK declared duplicate MCP tool names")
    return {tool["name"]: tool for tool in items}


def compare_source_to_gateway(host: dict[str, dict], gateway: dict[str, dict]) -> dict:
    spec = importlib.util.spec_from_file_location("host_mcp_schema_compare", AUDITOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("Host MCP SDK schema comparer unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_manifest = json.loads((HOST / "mcp-surface.json").read_text())
    gateway_manifest = json.loads((GATEWAY / "mcp-surface.json").read_text())
    if sorted(host) != original_manifest["tools"]:
        raise RuntimeError("Original Host actual SDK differs from its source manifest")
    if sorted(gateway) != gateway_manifest["tools"]:
        raise RuntimeError("Gateway actual SDK differs from its source manifest")
    common = set(host) & set(gateway)
    unreviewed_gateway_tools = {
        name for name in gateway
        if name.startswith(HOST_NAMESPACES)
        and name not in host
        and name not in REVIEWED_GATEWAY_EXTENSIONS
    }
    if unreviewed_gateway_tools:
        raise RuntimeError(
            "Gateway exposed Host-namespaced tools without an owner contract: "
            + repr(sorted(unreviewed_gateway_tools))
        )
    omitted = set(host) - common
    if omitted != HOST_OMISSIONS:
        raise RuntimeError(f"Unexpected northbound Gateway Host omissions: {sorted(omitted)}")
    input_differences: dict[str, dict[str, Any]] = {}
    output_differences: list[str] = []
    for name in sorted(common):
        differences = module.compare(host[name], gateway[name])
        output_keys = {"hasOutputSchema", "outputSchemaContent"}
        input_part = {key: val for key, val in differences.items() if key not in output_keys}
        if input_part:
            input_differences[name] = input_part
        if host[name].get("outputSchema") != gateway[name].get("outputSchema"):
            output_differences.append(name)
    return {
        "kind": "ordivon.host-gateway-mcp-refinement-observation",
        "schemaVersion": 1,
        "hostSourceTools": len(host),
        "gatewaySharedHostTools": len(common),
        "gatewayOmittedHostTools": sorted(omitted),
        "inputDifferences": input_differences,
        "outputSchemaNotPreserved": output_differences,
        "truthBoundary": (
            "Compares both actual Python MCP SDK source registries; cannot prove "
            "installed connectors, live tool usage, Gateway forwarding effects "
            "or production Rust release readiness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-output-refinement", action="store_true",
        help="Fail for production cutover if Gateway weakens any Host outputSchema",
    )
    args = parser.parse_args()
    host = sdk_registry(
        HOST, module="ordivon_host_v2",
        builder='build_server("host=127.0.0.1 port=1 user=unused dbname=unused")',
    )
    gateway = sdk_registry(
        GATEWAY, module="ordivon_gateway", builder="build_server()",
    )
    report = compare_source_to_gateway(host, gateway)
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    if report["inputDifferences"]:
        raise RuntimeError(
            "Host→Gateway MCP input-schema refinement violation: "
            + repr(report["inputDifferences"])
        )
    if args.require_output_refinement and report["outputSchemaNotPreserved"]:
        raise RuntimeError(
            "Gateway cannot claim typed Host output refinement; "
            f"{len(report['outputSchemaNotPreserved'])} upstream schemas weakened"
        )
    print(
        "HOST_GATEWAY_MCP_INPUT_REFINEMENT_PASS"
        f" host={len(host)} shared={report['gatewaySharedHostTools']}"
        f" weakened_outputs={len(report['outputSchemaNotPreserved'])}"
        " installed_proof=UNKNOWN",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
