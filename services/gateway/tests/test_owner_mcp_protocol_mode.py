"""SDK-native Owner mode selection with fail-closed version pinning."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from ordivon_gateway import upstream
from ordivon_gateway.upstream import McpOwnerCaller, OwnerCallError, OwnerEndpoint


def _private(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    os.chmod(path, 0o600)
    return str(path)


def test_modern_pin_is_windows_only_explicit_and_preserves_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = _private(tmp_path / "id", "client.access")
    secret = _private(tmp_path / "secret", "opaque-value")
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL", "https://windows.test/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_ID_FILE", identity)
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_SECRET_FILE", secret)
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE", "2026-07-28")
    monkeypatch.setenv("ORDIVON_GATEWAY_HOST_URL", "http://host.test/mcp")

    caller = McpOwnerCaller.from_env()
    windows = caller._owners["runtime.windows"]
    assert windows.mcp_mode == "2026-07-28"
    assert windows.access_client_id_file == identity
    assert windows.access_client_secret_file == secret
    assert windows.bearer_token_file is None
    assert caller._owners["host"].mcp_mode == "auto"

    observed: list[str] = []

    class FakePool:
        async def aclose(self) -> None:
            pass

    class FakeClient:
        def __init__(self, transport, *, mode, raise_exceptions):
            observed.append(mode)
            assert raise_exceptions is False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *unused):
            return False

        async def call_tool(self, tool, args, *, meta=None):
            assert tool == "runtime.describe"
            assert args == {"schemaVersion": 1}
            return SimpleNamespace(
                is_error=False, structured_content={"schemaVersion": 1}, content=[]
            )

    monkeypatch.setattr(upstream, "create_mcp_http_client", lambda **kwargs: FakePool())
    monkeypatch.setattr(upstream, "streamable_http_client", lambda url, http_client: object())
    monkeypatch.setattr(upstream, "Client", FakeClient)

    async def verify() -> None:
        assert await caller.call_tool(
            "runtime.windows", "runtime.describe", {"schemaVersion": 1}
        ) == {"schemaVersion": 1}
        await caller.aclose()

    asyncio.run(verify())
    assert observed == ["2026-07-28"]


@pytest.mark.parametrize("mode", ["modern", "2025-11-25", "", " AUTO ", "0"])
def test_invalid_protocol_mode_fails_before_remote_work(mode: str) -> None:
    with pytest.raises(OwnerCallError, match="unsupported MCP SDK protocol mode"):
        McpOwnerCaller(
            {"runtime.windows": OwnerEndpoint("https://windows.test/mcp", mcp_mode=mode)}
        )


def test_opt_in_is_never_implicitly_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL", "https://windows.test/mcp")
    monkeypatch.delenv("ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE", raising=False)
    assert McpOwnerCaller.from_env()._owners["runtime.windows"].mcp_mode == "auto"
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE", "legacy")
    assert McpOwnerCaller.from_env()._owners["runtime.windows"].mcp_mode == "legacy"


def test_pinned_incompatible_server_fails_without_automatic_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = []

    class FakePool:
        async def aclose(self) -> None:
            pass

    class RejectingClient:
        def __init__(self, transport, *, mode, raise_exceptions):
            assert mode == "2026-07-28"
            attempts.append("connect")

        async def __aenter__(self):
            raise RuntimeError("unsupported pinned MCP protocol")

        async def __aexit__(self, *unused):
            return False

    monkeypatch.setattr(upstream, "create_mcp_http_client", lambda **kwargs: FakePool())
    monkeypatch.setattr(upstream, "streamable_http_client", lambda url, http_client: object())
    monkeypatch.setattr(upstream, "Client", RejectingClient)
    caller = McpOwnerCaller(
        {
            "host": OwnerEndpoint("http://host.test/mcp", mcp_mode="2026-07-28"),
        }
    )

    async def verify() -> None:
        with pytest.raises(OwnerCallError, match="owner transport/protocol call failed"):
            await caller.call_tool("host", "host.status", {"detail": "summary"})
        await caller.aclose()

    asyncio.run(verify())
    assert attempts == ["connect"]


def test_sdk_list_after_completed_owner_call_preserves_observation_uncertainty(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Real MCP HTTP: an SDK validation timeout is not a wire tools/call failure."""
    import socket

    import uvicorn
    from mcp.server import MCPServer

    from ordivon_gateway.service import GatewayService

    private_token = _private(tmp_path / "fake-owner-token", "fixture-only-token")
    wire_methods: list[str] = []
    completed_tool_responses: list[int] = []
    server = MCPServer("fixture-windows", version="fixture")

    @server.tool(name="runtime.describe")
    async def runtime_describe(schemaVersion: int = 1) -> dict:
        return {
            "schemaVersion": schemaVersion,
            "node": {"nodeId": "fixture-windows"},
            "targets": [{"target": "windows_native", "configured": True, "available": True}],
        }

    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        host="127.0.0.1",
    )

    async def instrument(scope, receive, send):
        if scope.get("type") != "http" or scope.get("method") != "POST":
            await app(scope, receive, send)
            return
        method = dict(scope.get("headers", [])).get(b"mcp-method", b"").decode()
        wire_methods.append(method)
        if method == "tools/list":
            # The SDK issues this validation request after tools/call returned.
            await asyncio.sleep(0.4)

        async def send_with_evidence(message):
            if method == "tools/call" and message["type"] == "http.response.start":
                completed_tool_responses.append(message["status"])
            await send(message)

        await app(scope, receive, send_with_evidence)

    async def scenario():
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        uv = uvicorn.Server(
            uvicorn.Config(instrument, host="127.0.0.1", port=port, log_level="critical")
        )
        serving = asyncio.create_task(uv.serve())
        try:
            for _ in range(150):
                if uv.started:
                    break
                await asyncio.sleep(0.02)
            assert uv.started
            caller = McpOwnerCaller(
                {
                    "runtime.windows": OwnerEndpoint(
                        f"http://127.0.0.1:{port}/mcp",
                        bearer_token_file=private_token,
                        mcp_mode="2026-07-28",
                    )
                }
            )
            try:
                return await GatewayService(
                    caller, projection_timeout_seconds=0.08
                ).capability_describe("execution.windows")
            finally:
                await caller.aclose()
        finally:
            uv.should_exit = True
            await asyncio.wait_for(serving, timeout=12)

    caplog.set_level("WARNING", logger="ordivon_gateway.upstream")
    projection = asyncio.run(scenario())
    item = projection.capabilities[0]
    assert completed_tool_responses == [200]
    assert wire_methods == ["tools/call", "tools/list"]
    assert item.readiness_state == "unknown"
    assert item.observation_error is not None
    assert any(
        "gateway_owner_rpc_cancelled" in rec.message
        and "phase=sdk_client_call_cancelled" in rec.message
        for rec in caplog.records
    )
