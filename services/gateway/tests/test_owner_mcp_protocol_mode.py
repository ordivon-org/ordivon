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
