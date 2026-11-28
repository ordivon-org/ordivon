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
    # Observe the original Host dispatch contract in the Gateway environment,
    # rather than introducing a second copied Tool registry.
    if owner == "gateway-dispatch":
        from ordivon_gateway.logic.host_tool_contracts import (
            SOCIAL_WORK_HOST_TOOLS as _SOCIAL_WORK_HOST_TOOLS,
        )

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


# This intentionally small fragment is not a general JSON Schema solver.
# Compare only advertised integer points and null, not SDK coercion or Owner
# business constraints. Unrecognized constraints remain UNKNOWN.
_ANNOTATIONS = {"title", "description", "examples"}


def _mentions_integer(schema: Any) -> bool:
    if not isinstance(schema, dict):
        return False
    branches = schema.get("anyOf")
    return schema.get("type") == "integer" or (
        isinstance(branches, list) and any(_mentions_integer(item) for item in branches)
    )


def _integer_interval(schema: Any) -> tuple[int | None, int | None, bool] | None:
    if not isinstance(schema, dict):
        return None
    nullable = "anyOf" in schema
    if nullable:
        if schema.keys() - (_ANNOTATIONS | {"anyOf", "default"}):
            return None
        branches = schema["anyOf"]
        if not isinstance(branches, list) or len(branches) != 2:
            return None
        integers = [
            b for b in branches if isinstance(b, dict) and b.get("type") == "integer"
        ]
        nulls = [
            b
            for b in branches
            if isinstance(b, dict)
            and b.get("type") == "null"
            and not b.keys() - (_ANNOTATIONS | {"type"})
        ]
        if len(integers) != 1 or len(nulls) != 1 or "default" in integers[0]:
            return None
        value = integers[0]
    else:
        value = schema
    if value.get("type") != "integer" or value.keys() - (
        _ANNOTATIONS | {"type", "minimum", "maximum", "default"}
    ):
        return None
    low, high = value.get("minimum"), value.get("maximum")
    if any(k in value and type(value[k]) is not int for k in ("minimum", "maximum")):
        return None
    if low is not None and high is not None and low > high:
        return None
    if "default" in schema:
        default = schema["default"]
        if not (
            (default is None and nullable)
            or (
                type(default) is int
                and (low is None or low <= default)
                and (high is None or default <= high)
            )
        ):
            return None
    return low, high, nullable


def _difference_witness(
    a: tuple[int | None, int | None, bool], b: tuple[int | None, int | None, bool]
) -> tuple[bool, int | None]:
    lo, hi, nullable = a
    other_lo, other_hi, other_nullable = b
    if nullable and not other_nullable:
        return True, None
    if other_lo is not None and (lo is None or lo < other_lo):
        return True, min(other_lo - 1, hi) if hi is not None else other_lo - 1
    if other_hi is not None and (hi is None or hi > other_hi):
        return True, max(other_hi + 1, lo) if lo is not None else other_hi + 1
    return False, None


def compare_integer_input(host: Any, gateway: Any) -> dict[str, Any]:
    a, b = _integer_interval(host), _integer_interval(gateway)
    if a is None or b is None:
        return {
            "relation": "UNKNOWN",
            "defaultRelation": "UNKNOWN",
            "hasHostOnlyWitness": None,
            "hostOnlyWitness": None,
            "hasGatewayOnlyWitness": None,
            "gatewayOnlyWitness": None,
        }
    left, x = _difference_witness(a, b)
    right, y = _difference_witness(b, a)
    relation = (
        "INCOMPARABLE"
        if left and right
        else "GATEWAY_STRICTER"
        if left
        else "GATEWAY_WIDER"
        if right
        else "EQUAL"
    )
    same_default = ("default" in host) == ("default" in gateway) and (
        host.get("default") == gateway.get("default")
    )
    return {
        "relation": relation,
        "defaultRelation": "EQUAL" if same_default else "DIFFERENT",
        "hasHostOnlyWitness": left,
        "hostOnlyWitness": x,
        "hasGatewayOnlyWitness": right,
        "gatewayOnlyWitness": y,
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
    integer_comparisons: list[dict[str, Any]] = []
    for name in common:
        host_input = host[name]["inputSchema"]
        gateway_input = gateway[name]["inputSchema"]
        if set(host_input.get("properties", {})) != set(
            gateway_input.get("properties", {})
        ) or set(host_input.get("required", [])) != set(
            gateway_input.get("required", [])
        ):
            input_name_required_drift.append(name)
        host_properties = host_input.get("properties", {})
        gateway_properties = gateway_input.get("properties", {})
        for prop in sorted(host_properties.keys() | gateway_properties.keys()):
            left, right = host_properties.get(prop), gateway_properties.get(prop)
            if _mentions_integer(left) or _mentions_integer(right):
                integer_comparisons.append(
                    {
                        "tool": name,
                        "property": prop,
                        **compare_integer_input(left, right),
                    }
                )
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
        "sourceIntegerInputComparisons": integer_comparisons,
        "sourceIntegerInputTruthBoundary": (
            "Advertised integer intervals and null only; defaults separately compared. "
            "Not SDK behavior, general schema inclusion, installed authority or migration proof."
        ),
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
            # Fresh worktrees are a supported source-observation entrypoint.
            # Keep dependency identity frozen by the lockfile, but do not
            # require an unrelated pre-populated global uv cache.
            "--project",
            str(
                ROOT
                / "services"
                / ("gateway" if owner == "gateway-dispatch" else owner)
            ),
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
