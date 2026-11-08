"""Process-scoped Owner HTTP pooling without persistent MCP session authority."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from types import SimpleNamespace

import httpx2
import pytest

from ordivon_gateway import upstream
from ordivon_gateway.upstream import McpOwnerCaller, OwnerEndpoint, OwnerEndpointAuth


def test_http_pool_auth_refreshes_rotated_owner_token(tmp_path: Path) -> None:
    """Pooled sockets must never freeze an obsolete identity secret."""
    token_path = tmp_path / "bearer"
    token_path.write_text("token-before-rotation", encoding="utf-8")
    os.chmod(token_path, 0o600)
    observations: list[str | None] = []

    def response(request: httpx2.Request) -> httpx2.Response:
        observations.append(request.headers.get("authorization"))
        return httpx2.Response(200, json={"ok": True})

    async def verify() -> None:
        async with httpx2.AsyncClient(
            transport=httpx2.MockTransport(response),
            auth=OwnerEndpointAuth(
                OwnerEndpoint("http://owner.test/mcp", bearer_token_file=str(token_path))
            ),
        ) as client:
            assert (await client.get("http://owner.test/a")).status_code == 200
            token_path.write_text("token-after-rotation", encoding="utf-8")
            assert (await client.get("http://owner.test/b")).status_code == 200

    asyncio.run(verify())
    assert observations == ["Bearer token-before-rotation", "Bearer token-after-rotation"]


def test_owner_rpc_uses_one_http_pool_for_concurrent_sessions_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each call negotiates its own MCP session; only HTTP sockets are shared."""
    created: list[object] = []
    handed: list[object] = []

    class HTTPPool:
        def __init__(self) -> None:
            self.closed = 0

        async def aclose(self) -> None:
            self.closed += 1

    def create_client(**kwargs):
        assert isinstance(kwargs["auth"], OwnerEndpointAuth)
        client = HTTPPool()
        created.append(client)
        return client

    def make_transport(url: str, *, http_client):
        assert url == "http://owner.test/mcp"
        handed.append(http_client)
        return object()

    class MCPClient:
        def __init__(self, transport, *, mode, raise_exceptions):
            assert mode == "auto"
            assert raise_exceptions is False
            self.transport = transport

        async def __aenter__(self):
            return self

        async def __aexit__(self, *unused):
            return False

        async def call_tool(self, name, arguments, *, meta=None):
            assert name == "host.status"
            await asyncio.sleep(0)
            return SimpleNamespace(
                is_error=False, structured_content={"ok": arguments["n"]}, content=[]
            )

    monkeypatch.setattr(upstream, "create_mcp_http_client", create_client)
    monkeypatch.setattr(upstream, "streamable_http_client", make_transport)
    monkeypatch.setattr(upstream, "Client", MCPClient)
    caller = McpOwnerCaller({"host": OwnerEndpoint("http://owner.test/mcp")})

    async def verify() -> None:
        result = await asyncio.gather(
            *(caller.call_tool("host", "host.status", {"n": i}) for i in range(12))
        )
        assert result == [{"ok": i} for i in range(12)]
        assert len(created) == 1
        assert len(handed) == 12
        assert all(client is created[0] for client in handed)
        await caller.aclose()
        await caller.aclose()
        assert created[0].closed == 1
        with pytest.raises(upstream.OwnerCallError, match="Owner transport is closed"):
            await caller.call_tool("host", "host.status", {"n": 20})

    asyncio.run(verify())
