"""Windows MCP status observation: SDK-typed single RPC, never an effect shortcut."""

from __future__ import annotations

import asyncio
import os
import socket
from pathlib import Path

import pytest

from ordivon_gateway.service import GatewayService
from ordivon_gateway.upstream import McpOwnerCaller, OwnerEndpoint


async def _real_http_owner_scenario(
    token_path: Path,
    *,
    status: object = True,
    slow: bool = False,
) -> tuple[object, list[tuple[str, str]], list[str]]:
    import uvicorn
    from mcp.server import MCPServer

    server = MCPServer("typed-readonly-fixture", version="1.0.0")
    completed: list[str] = []
    wire: list[tuple[str, str]] = []

    @server.tool(name="runtime.describe")
    async def runtime_describe(schemaVersion: int = 1) -> dict:
        if slow:
            await asyncio.sleep(0.3)
        completed.append("runtime.describe")
        if status == "missing_targets":
            return {"schemaVersion": schemaVersion, "node": {"nodeId": "fixture-windows"}}
        if status == "bad_version":
            return {
                "schemaVersion": "1",
                "node": {"nodeId": "fixture-windows"},
                "targets": [{"target": "windows_native", "configured": True, "available": True}],
            }
        return {
            "schemaVersion": schemaVersion,
            "node": {"nodeId": "fixture-windows"},
            "targets": [{"target": "windows_native", "configured": True, "available": status}],
        }

    @server.tool(name="job.get")
    async def job_get(jobId: str) -> dict:
        completed.append("job.get")
        return {"jobId": jobId, "status": "synthetic"}

    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        host="127.0.0.1",
    )

    async def traced_app(scope, receive, send):
        if scope["type"] == "http" and scope.get("method") == "POST":
            headers = dict(scope.get("headers", []))
            wire.append(
                (
                    headers.get(b"mcp-method", b"").decode(),
                    headers.get(b"mcp-name", b"").decode(),
                )
            )
            if wire[-1][0] == "tools/list":
                # Prove a slow post-tool schema listing is not on the fast path.
                await asyncio.sleep(0.25)
        await app(scope, receive, send)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    uv = uvicorn.Server(
        uvicorn.Config(traced_app, host="127.0.0.1", port=port, log_level="critical")
    )
    serving = asyncio.create_task(uv.serve())
    try:
        for _ in range(100):
            if uv.started:
                break
            await asyncio.sleep(0.02)
        assert uv.started
        caller = McpOwnerCaller(
            {
                "runtime.windows": OwnerEndpoint(
                    f"http://127.0.0.1:{port}/mcp",
                    bearer_token_file=str(token_path),
                    mcp_mode="2026-07-28",
                )
            }
        )
        try:
            projection = await GatewayService(
                caller, projection_timeout_seconds=0.07 if slow else 1.5
            ).capability_describe("execution.windows")
            if not slow:
                assert projection.capabilities[0].available is (status is True)
                assert wire == [("tools/call", "runtime.describe")]
                assert completed == ["runtime.describe"]

                # Non-status and non-exact-version calls stay in the SDK's
                # high-level path and still request tool schema discovery.
                wire.clear()
                other = await caller.call_tool("runtime.windows", "job.get", {"jobId": "synthetic"})
                assert other["jobId"] == "synthetic"
                assert wire == [("tools/call", "job.get"), ("tools/list", "")]

                wire.clear()
                value = await caller.call_tool(
                    "runtime.windows", "runtime.describe", {"schemaVersion": 2}
                )
                assert value["schemaVersion"] == ("1" if status == "bad_version" else 2)
                assert wire == [("tools/call", "runtime.describe"), ("tools/list", "")]
            else:
                assert completed == []
                assert wire == [("tools/call", "runtime.describe")]
            return projection, wire, completed
        finally:
            await caller.aclose()
    finally:
        uv.should_exit = True
        await asyncio.wait_for(serving, timeout=8)


def _token(tmp_path: Path) -> Path:
    path = tmp_path / "owner-credential-fixture"
    path.write_text("local-fixture-not-real-credential", encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def test_typed_status_read_over_real_tcp_and_normal_high_level_tools(
    tmp_path: Path,
) -> None:
    projection, _wire, _completed = asyncio.run(_real_http_owner_scenario(_token(tmp_path)))
    assert projection.capabilities[0].readiness_state == "ready"


def test_typed_status_read_preserves_strict_unknown_on_invalid_status(
    tmp_path: Path,
) -> None:
    projection, _wire, _completed = asyncio.run(
        _real_http_owner_scenario(_token(tmp_path), status="true")
    )
    item = projection.capabilities[0]
    assert item.readiness_state == "unknown"
    assert item.available is False
    assert item.observation_error == "owner returned invalid execution-target status"


def test_typed_status_cancellation_reports_sdk_boundary_without_owner_failure_claim(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("WARNING", logger="ordivon_gateway.upstream")
    projection, wire, _completed = asyncio.run(
        _real_http_owner_scenario(_token(tmp_path), slow=True)
    )
    item = projection.capabilities[0]
    assert item.readiness_state == "unknown"
    assert "TimeoutError" in (item.observation_error or "")
    assert wire == [("tools/call", "runtime.describe")]
    assert any("phase=typed_readonly_call_cancelled" in rec.message for rec in caplog.records)


@pytest.mark.parametrize("status", ["missing_targets", "bad_version"])
def test_typed_status_read_rejects_invalid_envelope_without_claiming_unavailable(
    tmp_path: Path,
    status: str,
) -> None:
    projection, wire, completed = asyncio.run(
        _real_http_owner_scenario(_token(tmp_path), status=status)
    )
    item = projection.capabilities[0]
    assert item.readiness_state == "unknown"
    assert item.observation_error is not None
    assert "invalid runtime.describe status envelope" in item.observation_error
    assert wire == [("tools/call", "runtime.describe"), ("tools/list", "")]
    assert completed == ["runtime.describe", "job.get", "runtime.describe"]
