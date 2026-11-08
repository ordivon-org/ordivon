"""Native TCP MCP consumer for authenticated versus unverified HTTP ingress."""

from __future__ import annotations

import asyncio
import socket

import httpx2
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from ordivon_gateway.mcp_server import build_http_app, build_server
from ordivon_gateway.service import GatewayService


class HostStatusOwner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def is_configured(self, owner: str) -> bool:
        return owner == "host"

    def configuration_error(self, owner: str) -> str | None:
        return None if owner == "host" else "unconfigured"

    async def call_tool(self, owner: str, tool: str, args: dict) -> dict:
        self.calls.append((owner, tool))
        assert (owner, tool) == ("host", "host.status")
        return {"schemaVersion": 3, "kind": "ordivon.host-status"}


def test_tcp_mcp_requires_real_http_service_identity_before_host_owner_call(tmp_path) -> None:
    """A transport-authenticated local Principal, not Tool args, gates Host forwarding."""
    secret = tmp_path / "gateway-bearer"
    secret.write_text("X" * 64, encoding="utf-8")
    secret.chmod(0o600)

    async def verify() -> None:
        owner = HostStatusOwner()
        app = build_http_app(
            build_server(
                service=GatewayService(owner),
                require_http_execution_identity=True,
                protect_artifact_reads=True,
            ),
            host="127.0.0.1",
            path="/mcp",
            public_origin=None,
            access_verifier=None,
            local_bearer_token_file=str(secret),
        )
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="on")
        )
        serving = asyncio.create_task(server.serve())
        try:
            for _ in range(200):
                if server.started:
                    break
                await asyncio.sleep(0.02)
            assert server.started
            url = f"http://127.0.0.1:{port}/mcp"

            async with httpx2.AsyncClient(
                timeout=httpx2.Timeout(15, read=30), trust_env=False
            ) as anonymous:
                forbidden = await anonymous.post(
                    url, json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
                )
                assert forbidden.status_code == 403
                assert owner.calls == []

            async with httpx2.AsyncClient(
                headers={"Authorization": "Bearer " + "X" * 64},
                timeout=httpx2.Timeout(15, read=30),
                trust_env=False,
            ) as authorized:
                async with Client(
                    streamable_http_client(url, http_client=authorized),
                    mode="2026-07-28",
                    raise_exceptions=False,
                ) as client:
                    listed = await client.list_tools()
                    assert len(listed.tools) == 38
                    result = await client.call_tool("host.status", {})
                    assert result.is_error is False
                    assert result.structured_content == {
                        "schemaVersion": 3,
                        "kind": "ordivon.host-status",
                    }
                    assert owner.calls == [("host", "host.status")]
        finally:
            server.should_exit = True
            await asyncio.wait_for(serving, timeout=12)

    asyncio.run(verify())
