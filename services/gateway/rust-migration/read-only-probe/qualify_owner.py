"""Independent native Python MCP producer -> Rust read-only recipient fixture."""

from __future__ import annotations

import asyncio
import json
import socket
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import uvicorn
from mcp.server import MCPServer

from ordivon_gateway.logic.routing import default_routes


async def observe_fixture(
    binary: Path,
    case: str,
    *,
    legacy: bool = False,
    query: str | None = None,
    include: bool = False,
) -> dict:
    server = MCPServer("runtime-readonly-fixture")
    calls: list[int] = []
    wire: list[dict] = []

    @server.tool(name="runtime.describe", structured_output=case != "text")
    async def runtime_describe(schemaVersion: int = 1) -> dict[str, Any]:
        calls.append(schemaVersion)
        if case == "error":
            raise ValueError("synthetic Owner error")
        if case == "slow":
            await asyncio.sleep(4)
        value = {
            "schemaVersion": 1,
            "node": {"nodeId": "fixture-linux", "platform": "linux", "native": True},
            "targets": [
                {"target": "local_linux", "configured": True, "available": case != "false"}
            ],
        }
        if case == "version":
            value["schemaVersion"] = True
        elif case == "node":
            value["node"]["nodeId"] = "other"
        elif case == "duplicate":
            value["targets"].append(value["targets"][0])
        elif case == "contradiction":
            value["targets"][0]["configured"] = False
        elif case == "typed":
            value["targets"][0]["available"] = "true"
        elif case == "absent":
            value["targets"] = []
        elif case == "oversize":
            value["padding"] = "x" * (1024 * 1024 + 1)
        return value

    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=not legacy,
        json_response=True,
        host="127.0.0.1",
    )

    async def capture(scope, receive, send):
        if scope["type"] == "http" and scope.get("method") == "POST":
            chunks = []

            async def observed_receive():
                part = await receive()
                if part["type"] == "http.request":
                    chunks.append(part.get("body", b""))
                    if not part.get("more_body"):
                        wire.append(json.loads(b"".join(chunks)))
                return part

            await app(scope, observed_receive, send)
        else:
            await app(scope, receive, send)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        endpoint = f"http://127.0.0.1:{sock.getsockname()[1]}/mcp"
        uv = uvicorn.Server(uvicorn.Config(capture, log_level="critical"))
        serving = asyncio.create_task(uv.serve(sockets=[sock]))
        try:
            for _ in range(250):
                if uv.started:
                    break
                await asyncio.sleep(0.02)
            assert uv.started
            with tempfile.TemporaryDirectory(prefix="native-discovery-") as tmp:
                if query is None:
                    args = [
                        "observe-runtime-fixture",
                        endpoint,
                        "fixture-linux",
                        "legacy" if legacy else "auto",
                    ]
                else:
                    route = asdict(default_routes()["execution.linux"])
                    metadata = {
                        key: route[key]
                        for key in ("capability", "category", "owner_id", "description", "tags")
                    }
                    path = Path(tmp) / "search.json"
                    path.write_text(
                        json.dumps(
                            {
                                "metadata": metadata,
                                "query": query,
                                "limit": 10,
                                "include_unavailable": include,
                            }
                        ),
                        encoding="utf-8",
                    )
                    args = ["discover-runtime-fixture", str(path), endpoint, "fixture-linux"]
                proc = await asyncio.create_subprocess_exec(
                    str(binary),
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    out, err = await asyncio.wait_for(proc.communicate(), 8)
                finally:
                    if proc.returncode is None:
                        proc.kill()
                        await proc.wait()
                assert proc.returncode == 0, err.decode()
                result = json.loads(out)
            tool_calls = [item for item in wire if item.get("method") == "tools/call"]
            if query == "zz-no-such-route-xyz":
                assert wire == [] and calls == [], (wire, calls)
                return result
            assert len(tool_calls) == 1, (case, wire)
            assert tool_calls[0]["params"]["name"] == "runtime.describe"
            assert tool_calls[0]["params"]["arguments"] == {"schemaVersion": 1}
            assert calls == [1], (case, calls)
            if legacy:
                assert any(item.get("method") == "initialize" for item in wire), wire
            return result
        finally:
            uv.should_exit = True
            await asyncio.wait_for(serving, 10)


async def qualify_owner(binary: Path) -> None:
    expected = {
        "true": {"standing": "reported", "configured": True, "available": True},
        "false": {"standing": "reported", "configured": True, "available": False},
        "version": {"standing": "unobserved", "reason": "invalid_status_envelope"},
        "node": {"standing": "unobserved", "reason": "unqualified_node"},
        "duplicate": {"standing": "unobserved", "reason": "invalid_target_inventory"},
        "contradiction": {"standing": "unobserved", "reason": "invalid_target_inventory"},
        "typed": {"standing": "unobserved", "reason": "invalid_target_inventory"},
        "absent": {"standing": "unobserved", "reason": "target_not_observed"},
        "error": {"standing": "unobserved", "reason": "owner_tool_error"},
        "text": {"standing": "unobserved", "reason": "structured_result_absent"},
    }
    for case, result in expected.items():
        observed = await observe_fixture(binary, case)
        assert observed == result, (case, observed, result)
        print("NATIVE_OWNER_FIXTURE_PASS", case, observed, flush=True)
    for case in ("slow", "oversize"):
        observed = await observe_fixture(binary, case)
        assert observed["standing"] == "unobserved", (case, observed)
        assert observed["reason"] in ("observation_deadline", "protocol_or_transport_failed")
        print("NATIVE_OWNER_FIXTURE_PASS", case, observed, flush=True)
    observed = await observe_fixture(binary, "true", legacy=True)
    assert observed == expected["true"]
    print("NATIVE_OWNER_LEGACY_PASS", observed, flush=True)

    empty = {"total_matches": 0, "matches": []}
    match = {
        "total_matches": 1,
        "matches": [{"capability": "execution.linux", "match_kind": "exact"}],
    }
    for case, include, expected_projection, expected_observation in (
        ("true", False, match, expected["true"]),
        ("false", False, empty, expected["false"]),
        ("false", True, match, expected["false"]),
        ("duplicate", False, match, expected["duplicate"]),
    ):
        result = await observe_fixture(binary, case, query="execution.linux", include=include)
        assert result == {"projection": expected_projection, "observation": expected_observation}, (
            case,
            result,
        )
        print("NATIVE_DISCOVERY_COMPOSITION_PASS", case, include, result, flush=True)
    result = await observe_fixture(binary, "true", query="zz-no-such-route-xyz")
    assert result == {"projection": empty, "observation": None}, result
    print("NATIVE_DISCOVERY_ZERO_RPC_PASS", result, flush=True)
