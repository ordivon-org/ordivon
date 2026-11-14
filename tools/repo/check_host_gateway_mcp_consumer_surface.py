"""Read native Host/Gateway MCP SDK source tool schemas without adding a mirror.

Source-only, read-only consumer surface reconnaissance. No Cloudflare, Host PG,
Security grant, Runtime effect or production installed status is asserted.
Run from monorepo root with:
  python3 tools/repo/check_host_gateway_mcp_consumer_surface.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
# The original Host exposes this operator-local diagnostic, never an Agent action.
# Reuse the two native MCP SDK tool registries for all business tool names;
# this is the one documented Host-only exception, not a copied tool catalog.
_HOST_OPERATOR_ONLY = frozenset({"host.pool.stats"})


async def _emit_source(owner: str) -> dict[str, Any]:
    # Observe the original GatewayService allowlist in the Gateway environment,
    # rather than introducing a second copied Tool registry.
    if owner == "gateway-dispatch":
        from ordivon_gateway.service import _SOCIAL_WORK_HOST_TOOLS

        return {"dispatchHostToolNames": sorted(_SOCIAL_WORK_HOST_TOOLS)}

    from mcp import Client

    if owner == "host":
        from ordivon_host_v2.mcp_server import build_server

        server = build_server("postgresql://source-schema-observation.invalid/test")
    elif owner == "gateway":
        from ordivon_gateway.mcp_server import build_server

        server = build_server()
    else:
        raise ValueError("unsupported natural Owner")
    # Native MCP SDK tools/list from the original Owner build, no Host PG/RPC.
    async with Client(server, raise_exceptions=True) as client:
        tools = (await client.list_tools()).tools
    return {
        item.name: item.model_dump(mode="json", by_alias=True, exclude_none=True)
        for item in tools
    }


def summarize(
    host: dict[str, dict[str, Any]],
    gateway: dict[str, dict[str, Any]],
    *,
    dispatcher_host_tools: set[str] | None = None,
) -> dict[str, Any]:
    host_names, gateway_names = set(host), set(gateway)
    common = sorted(host_names & gateway_names)
    missing_business = sorted((host_names - gateway_names) - _HOST_OPERATOR_ONLY)
    excluded_operator = sorted((host_names - gateway_names) & _HOST_OPERATOR_ONLY)
    exposed_operator = sorted(gateway_names & _HOST_OPERATOR_ONLY)
    input_name_required_drift: list[str] = []
    input_schema_different: list[str] = []
    output_schema_different: list[str] = []
    for name in common:
        host_input = host[name]["inputSchema"]
        gateway_input = gateway[name]["inputSchema"]
        if set(host_input.get("properties", {})) != set(
            gateway_input.get("properties", {})
        ) or set(host_input.get("required", [])) != set(
            gateway_input.get("required", [])
        ):
            input_name_required_drift.append(name)
        if host_input != gateway_input:
            input_schema_different.append(name)
        if host[name].get("outputSchema") != gateway[name].get("outputSchema"):
            output_schema_different.append(name)
    input_names_match = bool(common) and not input_name_required_drift
    business_surface_covered = (
        bool(common) and not missing_business and not exposed_operator
    )
    # A public Gateway MCP Tool can exist while GatewayService rejects the
    # forwarded name. Host->Gateway migration needs both public Tool coverage
    # and the existing internal dispatch allowlist to match natural Host Tools.
    expected_dispatch = host_names - _HOST_OPERATOR_ONLY
    missing_dispatch = (
        sorted(expected_dispatch - dispatcher_host_tools)
        if dispatcher_host_tools is not None
        else []
    )
    unexpected_dispatch = (
        sorted(dispatcher_host_tools - expected_dispatch)
        if dispatcher_host_tools is not None
        else []
    )
    dispatch_qualified = (
        None
        if dispatcher_host_tools is None
        else not missing_dispatch and not unexpected_dispatch
    )
    public_surface_qualified = input_names_match and business_surface_covered
    end_to_end_source_qualified = (
        None
        if dispatch_qualified is None
        else public_surface_qualified and dispatch_qualified
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-gateway-source-mcp-consumer-surface",
        "hostToolCount": len(host),
        "gatewayToolCount": len(gateway),
        "sharedToolCount": len(common),
        "hostOnlyTools": sorted(host_names - gateway_names),
        "gatewayOnlyTools": sorted(gateway_names - host_names),
        "missingHostBusinessTools": missing_business,
        "operatorDiagnosticsExcluded": excluded_operator,
        "exposedHostOperatorDiagnostics": exposed_operator,
        "sourceHostBusinessSurfaceCovered": business_surface_covered,
        "sourceConsumerSurfaceQualified": public_surface_qualified,
        "sourceGatewayDispatcherQualified": dispatch_qualified,
        "sourceEndToEndSourceQualified": end_to_end_source_qualified,
        "missingGatewayDispatcherTools": missing_dispatch,
        "unexpectedGatewayDispatcherTools": unexpected_dispatch,
        "inputPropertyOrRequiredDrift": input_name_required_drift,
        "inputSchemaDifferentTools": input_schema_different,
        "outputSchemaDifferentTools": output_schema_different,
        "sourceInputNameRequiredParity": input_names_match,
        "installedConsumersQualified": None,
        "securityAuthorized": None,
        "domainConsumerMigrated": None,
        "migrationStanding": "UNKNOWN_REQUIRES_INSTALLED_AUTH_AND_CONSUMER_CANARIES",
        "truthBoundary": (
            "MCP SDK source introspection only; input parity does not prove "
            "Gateway accepts all Host argument values, output-schema typing, "
            "real Owner authorization, installed Plugin shape or domain success. "
            "The source dispatch witness comes from the original GatewayService "
            "allowlist, not from installed HTTP or external Agent consumers"
        ),
    }


def _child_source(owner: str) -> dict[str, dict[str, Any]]:
    uv = shutil.which("uv")
    if uv is None:
        raise FileNotFoundError("mature uv source runner unavailable")
    program = str(Path(__file__).resolve())
    result = subprocess.run(
        [
            uv,
            "run",
            "--locked",
            "--offline",
            "--project",
            str(ROOT / "services" / ("gateway" if owner == "gateway-dispatch" else owner)),
            "python",
            program,
            "--emit",
            owner,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise TypeError("native MCP SDK source result is not a tool map")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit", choices=["host", "gateway", "gateway-dispatch"])
    args = parser.parse_args()
    if args.emit:
        print(json.dumps(asyncio.run(_emit_source(args.emit)), sort_keys=True))
        return 0

    try:
        host = _child_source("host")
        gateway = _child_source("gateway")
        dispatch = _child_source("gateway-dispatch")
        raw_dispatch = dispatch.get("dispatchHostToolNames")
        if (
            not isinstance(raw_dispatch, list)
            or not all(isinstance(name, str) and bool(name) for name in raw_dispatch)
            or len(set(raw_dispatch)) != len(raw_dispatch)
        ):
            raise TypeError("native GatewayService Host dispatcher source is malformed")
        result = summarize(host, gateway, dispatcher_host_tools=set(raw_dispatch))
        source = subprocess.run(
            ["/usr/bin/git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=8,
        )
        result["sourceCut"] = source.stdout.strip()
    except (
        TypeError,
        ValueError,
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        print(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "kind": "ordivon.host-gateway-source-mcp-consumer-surface",
                    "migrationStanding": "UNKNOWN_SOURCE_OBSERVATION_FAILED",
                    "errorType": type(exc).__name__,
                    "installedConsumersQualified": None,
                },
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0 if result["sourceEndToEndSourceQualified"] is True else 3


if __name__ == "__main__":
    raise SystemExit(main())
