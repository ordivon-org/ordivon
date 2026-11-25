"""Isolated candidate qualification against the real Python Gateway source."""

from __future__ import annotations

import asyncio
import itertools
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from mcp import Client, MCPError

from ordivon_gateway.logic.execution_refs import GatewayError, parse_execution_ref
from ordivon_gateway.logic.routing import default_routes
from ordivon_gateway.logic.runtime_status import (
    valid_runtime_status_envelope,
    valid_runtime_target_inventory,
)
from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService

ROOT = Path(__file__).resolve().parent


def binary_path():
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    metadata = subprocess.check_output(
        ["cargo", "metadata", "--offline", "--locked", "--no-deps", "--format-version", "1"],
        cwd=ROOT,
        text=True,
    )
    return Path(json.loads(metadata)["target_directory"]) / "debug/ordivon-gateway-read-only-probe"


BINARY = binary_path()
OWNERS = ("runtime.linux", "runtime.windows", "runtime.harness", "host", "host.read", "skills")


class InertCaller:
    def __init__(self, configured, host_read_route):
        self.configured = configured
        self.host_read_route = host_read_route

    def is_configured(self, owner):
        return self.configured.get(owner, False)

    def has_route(self, owner):
        return owner == "host.read" and self.host_read_route

    async def call_tool(self, *args, **kwargs):
        raise AssertionError("metadata probe must not contact any Owner")


def tool_contract(tool):
    return tool.model_dump(mode="json", by_alias=True, exclude_none=True)


async def main():
    routes = default_routes()
    base = GatewayService(InertCaller({}, False))
    async with Client(build_server(base)) as client:
        tools = (await client.list_tools()).tools
        tool = next(tool_contract(t) for t in tools if t.name == "system.describe")
        result = await client.call_tool("system.describe", {})
        assert result.structured_content == base.system_describe().model_dump(mode="json")
    cases = []

    def add(operation, value, expected):
        cases.append(({"operation": operation, "input": value}, expected))

    vals = (None, True, False, 0, 1, 1.0, 2, "1", [], {})
    for value in vals:
        for row in (value, {"schemaVersion": value}):
            add("status", row, valid_runtime_status_envelope(row))
    for c, a in itertools.product(vals, repeat=2):
        row = [{"target": "local_linux", "configured": c, "available": a}]
        add("inventory", row, valid_runtime_target_inventory(row))
    good = {"target": "local_linux", "configured": True, "available": True}
    for value in (
        None,
        {},
        "x",
        1,
        [],
        [good, good],
        [good, None],
        [good, dict(good, target="other", configured=False)],
    ):
        add("inventory", value, valid_runtime_target_inventory(value))
    for name in (
        "",
        " ",
        "\u001c",
        "\u001d",
        "\u001e",
        "\u001f",
        "\u0085",
        "\u00a0",
        "\u3000",
        "\u200b",
        "Linux",
        " Linux ",
    ):
        row = [dict(good, target=name)]
        add("inventory", row, valid_runtime_target_inventory(row))
    for ref in (
        "",
        "ordivon-exec:v1:",
        "ordivon-exec:v1:runtime.linux:",
        "ordivon-exec:v1:runtime.linux:id",
        "ordivon-exec:v1:runtime.windows: ",
        "ordivon-exec:v1:runtime.harness:中文",
        "ordivon-exec:v1:runtime.linux:id:2",
        "ordivon-exec:v1:host:id",
        "ordivon-exec:v2:runtime.linux:id",
    ):
        try:
            expected = list(parse_execution_ref(ref))
        except GatewayError:
            expected = None
        add("reference", ref, expected)

    fixture = None
    for values in itertools.product((False, True), repeat=len(OWNERS) + 1):
        config = dict(zip(OWNERS, values[:-1], strict=True))
        service = GatewayService(InertCaller(config, values[-1]))
        expected = service.system_describe().model_dump(mode="json")
        fixture = {
            "gateway_version": expected["gateway_version"],
            "routes": {k: asdict(v) for k, v in routes.items()},
            "configured": config,
            "host_read_route": values[-1],
        }
        add("describe", fixture, expected)
    assert fixture
    invalid = dict(fixture, routes={"wrong-key": next(iter(fixture["routes"].values()))})
    try:
        GatewayService(InertCaller({}, False), {"wrong-key": next(iter(routes.values()))})
    except GatewayError:
        add("describe", invalid, {"error": "route identity mismatch"})
    else:
        raise AssertionError("Python accepted invalid route identity")

    data = "".join(json.dumps(case, ensure_ascii=False) + "\n" for case, _ in cases)
    proc = subprocess.run(
        [BINARY, "eval"], input=data, encoding="utf-8", capture_output=True, check=True
    )
    actual = [json.loads(row) for row in proc.stdout.splitlines()]
    assert len(actual) == len(cases)
    for index, ((case, expected), observed) in enumerate(zip(cases, actual, strict=True)):
        assert observed == expected, (index, case["operation"], expected, observed)
    counts = {
        op: sum(case["operation"] == op for case, _ in cases)
        for op in ("status", "inventory", "reference", "describe")
    }
    print("PURE_DIFFERENTIAL_PASS", len(cases), counts, flush=True)

    with tempfile.TemporaryDirectory(prefix="gateway-rust-native-") as tmp:
        path = Path(tmp) / "fixture.json"
        path.write_text(
            json.dumps({"description": fixture, "tool": tool}, ensure_ascii=False), encoding="utf-8"
        )
        server = subprocess.Popen([BINARY, "serve", path], stdout=subprocess.PIPE, text=True)
        try:
            address = server.stdout.readline().strip()
            assert address.startswith("127.0.0.1:"), address
            endpoint = f"http://{address}/mcp"
            expected = (
                GatewayService(InertCaller(fixture["configured"], fixture["host_read_route"]))
                .system_describe()
                .model_dump(mode="json")
            )
            for mode in ("auto", "2026-07-28", "legacy"):
                async with Client(endpoint, mode=mode, read_timeout_seconds=5) as client:
                    got = (await client.list_tools()).tools
                    assert [t.name for t in got] == ["system.describe"]
                    observed = tool_contract(got[0])
                    for field in ("name", "inputSchema", "outputSchema"):
                        assert observed.get(field) == tool.get(field), (
                            field,
                            observed.get(field),
                            tool.get(field),
                        )
                    result = await client.call_tool("system.describe", {})
                    assert not result.is_error and result.structured_content == expected
                    for name, arguments in (
                        ("system.describe", {"unexpected": True}),
                        ("execution.submit", {}),
                    ):
                        try:
                            result = await client.call_tool(name, arguments)
                        except MCPError as exc:
                            print("MCP_NEGATIVE", mode, name, type(exc).__name__, flush=True)
                        else:
                            assert result.is_error, (name, result)
                    print(
                        "MCP_SCHEMA_RESULT_PASS",
                        mode,
                        client.protocol_version,
                        expected["route_digest"],
                        flush=True,
                    )
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    asyncio.run(main())
