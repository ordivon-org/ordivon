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


async def _emit_source(owner: str) -> dict[str, dict[str, Any]]:
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
    host: dict[str, dict[str, Any]], gateway: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    common = sorted(set(host) & set(gateway))
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
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-gateway-source-mcp-consumer-surface",
        "hostToolCount": len(host),
        "gatewayToolCount": len(gateway),
        "sharedToolCount": len(common),
        "hostOnlyTools": sorted(set(host) - set(gateway)),
        "gatewayOnlyTools": sorted(set(gateway) - set(host)),
        "inputPropertyOrRequiredDrift": input_name_required_drift,
        "inputSchemaDifferentTools": input_schema_different,
        "outputSchemaDifferentTools": output_schema_different,
        "sourceInputNameRequiredParity": bool(common) and not input_name_required_drift,
        "installedConsumersQualified": None,
        "securityAuthorized": None,
        "domainConsumerMigrated": None,
        "migrationStanding": "UNKNOWN_REQUIRES_INSTALLED_AUTH_AND_CONSUMER_CANARIES",
        "truthBoundary": (
            "MCP SDK source introspection only; input parity does not prove "
            "Gateway accepts all Host argument values, output-schema typing, "
            "real Owner authorization, installed Plugin shape or domain success"
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
            str(ROOT / "services" / owner),
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
    parser.add_argument("--emit", choices=["host", "gateway"])
    args = parser.parse_args()
    if args.emit:
        print(json.dumps(asyncio.run(_emit_source(args.emit)), sort_keys=True))
        return 0

    try:
        host = _child_source("host")
        gateway = _child_source("gateway")
        result = summarize(host, gateway)
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
                    "installedConsumersQualified": False,
                },
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0 if result["sourceInputNameRequiredParity"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
