"""Isolated candidate qualification against the real Python Gateway source."""

from __future__ import annotations

import asyncio
import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import asdict, replace
from pathlib import Path

from mcp import Client, MCPError
from qualify_abi import add_abi_cases
from qualify_artifact import add_artifact_cases
from qualify_chunk import add_chunk_cases, qualify_legacy_abi
from qualify_owner import qualify_owner
from qualify_principal import qualify_principal
from qualify_provenance import add_provenance_cases
from qualify_receipt import add_receipt_cases
from qualify_resolution import qualify_resolution
from qualify_semantics import add_descriptor_cases, add_error_cases, qualify_error_transport
from qualify_stateful import qualify_stateful
from qualify_stream import add_stream_cases, qualify_harness_source, qualify_stream_transport

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


class StatusCaller(InertCaller):
    """Deterministic read-only fixture; never a live Owner or grant."""

    async def call_tool(self, owner, tool, args):
        if tool == "host.status":
            return {"schemaVersion": 3, "kind": "ordivon.host-status"}
        assert tool == "runtime.describe"
        linux = owner == "runtime.linux"
        return {
            "schemaVersion": 1,
            "node": {
                "nodeId": "linux-pg" if linux else "windows-pg",
                "platform": "linux" if linux else "windows",
                "native": True,
            },
            "targets": [
                {
                    "target": "local_linux" if linux else "windows_native",
                    "configured": True,
                    "available": linux,
                    "executionProfiles": ["trusted_local"],
                    "windowsAuthorities": ["limited"],
                }
            ],
            "structuredReleaseConfigured": False,
        }


def qualify_unicode():
    h = hashlib.sha256()
    count = 0
    for scalar in range(0x110000):
        if 0xD800 <= scalar <= 0xDFFF:
            continue
        char = chr(scalar)
        h.update(char.encode() + bytes(1) + char.casefold().encode() + bytes(1))
        count += 1
    expected = h.hexdigest()
    observed = subprocess.check_output([BINARY, "casefold-digest"], text=True).strip()
    assert observed == expected, (unicodedata.unidata_version, expected, observed)
    print("UNICODE_SCALAR_CASEFOLD_EQUAL", count, unicodedata.unidata_version, expected, flush=True)


async def add_search_cases(add):
    routes = default_routes()
    template = routes["research.citation.metadata"]
    for name, description, tags in (
        ("test.Straße", "中文检索 ς", ("CAFÉ", "İstanbul")),
        ("test.K", "Unicode alpha beta", ("a-b", "ß")),
        ("test.Σ", "Greek σ ς", ("Ångström", "é")),
        ("test.꟝", "unassigned Unicode17", ("𝾕",)),
    ):
        routes[name] = replace(template, capability=name, description=description, tags=tags)
    svc = GatewayService(
        StatusCaller({"runtime.linux": True, "runtime.windows": True, "host": True}, False),
        routes,
    )
    full = await svc.capability_describe()
    rows = [
        {
            "metadata": {
                field: getattr(item, field)
                for field in ("capability", "category", "owner_id", "description", "tags")
            },
            "available": item.available,
            "observation_error": item.observation_error,
        }
        for item in full.capabilities
    ]
    queries = (
        "execution",
        "runtime",
        "host",
        "artifact",
        "research",
        "search",
        "execution.linux",
        "read",
        "中文",
        "检索",
        "strasse",
        "TEST.STRASSE",
        "σ",
        "Σ",
        "k",
        "café",
        "i",
        "i̇stanbul",
        "ß",
        "a-b",
        "beta alpha",
        "!!!",
        "unfindable",
        "é",
        "é",
        "ÅNGSTRÖM",
        "꟝",
        "ɷ",
        "𝾕",
    )
    batch_queries = []
    batch_expected = []
    observations = [
        dict(
            capability=row["metadata"]["capability"],
            available=row["available"],
            observation_error=row["observation_error"],
        )
        for row in rows
    ]
    for query, category, owner_id, limit, include in itertools.product(
        queries,
        (None, "execution", "research"),
        (None, "runtime.linux", "research.composition"),
        (1, 50),
        (False, True),
    ):
        kwargs = dict(
            query=query,
            category=category,
            owner_id=owner_id,
            limit=limit,
            include_unavailable=include,
        )
        result = await svc.capability_search(**kwargs)
        expected = {
            "total_matches": result.total_matches,
            "matches": [
                {"capability": m.capability.capability, "match_kind": m.match_kind}
                for m in result.matches
            ],
        }
        add("search", dict(**kwargs, rows=rows), expected)
        batch_queries.append(dict(**kwargs, observations=observations))
        batch_expected.append(expected)
    metadata = [row["metadata"] for row in rows]
    add("search_batch", {"metadata": metadata, "queries": batch_queries}, batch_expected)
    print("NATIVE_BATCH_PYTHON_ORACLE", len(batch_expected), flush=True)
    bad = [dict(obs) for obs in observations]
    bad[0], bad[1] = bad[1], bad[0]
    add(
        "search_batch",
        {"metadata": metadata, "queries": [dict(batch_queries[0], observations=bad)]},
        {"error": "observation identity mismatch"},
    )
    add(
        "search_batch",
        {"metadata": metadata, "queries": [dict(batch_queries[0], observations=observations[:-1])]},
        {"error": "observation identity mismatch"},
    )
    add(
        "search_batch",
        {"metadata": [*metadata, metadata[0]], "queries": []},
        {"error": "duplicate metadata identity"},
    )
    # A later request's negative or unknown evidence must not inherit a prior
    # positive observation from the shared lexical index.
    sample = metadata[0]

    def obs(available, error):
        return [
            {"capability": sample["capability"], "available": available, "observation_error": error}
        ]

    params = dict(
        query=sample["capability"], category=None, owner_id=None, limit=1, include_unavailable=False
    )
    match = {
        "total_matches": 1,
        "matches": [{"capability": sample["capability"], "match_kind": "exact"}],
    }
    add(
        "search_batch",
        {
            "metadata": [sample],
            "queries": [
                dict(params, observations=obs(True, None)),
                dict(params, observations=obs(False, None)),
                dict(params, observations=obs(False, "unobserved")),
            ],
        },
        [match, {"total_matches": 0, "matches": []}, match],
    )


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

    qualify_unicode()
    await add_search_cases(add)
    add_artifact_cases(add)
    add_descriptor_cases(add)
    add_error_cases(add)
    add_receipt_cases(add)
    add_chunk_cases(add)
    add_stream_cases(add)
    add_abi_cases(add)
    add_provenance_cases(add)
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
        for op in (
            "status",
            "inventory",
            "reference",
            "describe",
            "search",
            "search_batch",
            "artifact_inventory",
            "artifact_descriptor",
            "owner_error",
            "owner_receipt",
            "artifact_chunk",
            "artifact_stream",
            "artifact_v1",
            "artifact_provenance",
        )
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
    asyncio.run(qualify_owner(BINARY))
    asyncio.run(qualify_error_transport(BINARY))
    asyncio.run(qualify_legacy_abi())
    qualify_harness_source()
    asyncio.run(qualify_stream_transport(BINARY))
    asyncio.run(qualify_stateful(BINARY))
    asyncio.run(qualify_resolution(BINARY))
    asyncio.run(qualify_principal(BINARY))
