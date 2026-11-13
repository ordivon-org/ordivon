"""Native TCP MCP consumer for authenticated versus unverified HTTP ingress."""

from __future__ import annotations

import asyncio
import socket

import httpx2
import pytest
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from ordivon_gateway.mcp_server import build_http_app, build_server
from ordivon_gateway.service import GatewayService
from ordivon_gateway.tool_visibility import CORE_PUBLIC_TOOLS


class HostStatusOwner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def is_configured(self, owner: str) -> bool:
        return owner == "host"

    def configuration_error(self, owner: str) -> str | None:
        return None if owner == "host" else "unconfigured"

    async def call_tool(self, owner: str, tool: str, args: dict) -> dict:
        self.calls.append((owner, tool))
        if (owner, tool) == ("host", "work.get"):
            return {"schemaVersion": 3, "kind": "ordivon.host-work", "workRef": args["workRef"]}
        assert (owner, tool) == ("host", "host.status")
        return {"schemaVersion": 3, "kind": "ordivon.host-status"}


class SourceAuthZenStub:
    """Test-only PDP response, never evidence of an installed Security grant."""

    outcome = "ALLOW"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def authorize(self, **kwargs):
        self.calls.append(kwargs)
        if self.outcome == "UNAVAILABLE":
            raise RuntimeError("test-PDP unavailable")
        permitted = self.outcome == "ALLOW"
        return {
            "schemaVersion": 3,
            "kind": "ordivon.security.gateway-capability-authz",
            "principalId": kwargs["principal_id"],
            "issuer": kwargs["issuer"],
            "requestedCapability": kwargs["requested_capability"],
            "requestedResource": kwargs["requested_resource"],
            "qualificationTarget": True,
            "authorizationProfile": "interactive-principal-authzen",
            "outcome": self.outcome,
            "reason": "test-PDP",
            "authorizationEvidence": {
                "standard": "openid-authzen-authorization-api-1.0",
                "requestId": "test-trace",
                "responseRequestId": "test-trace",
                "decision": permitted,
            },
            "authorityProjection": None,
            "effectAdmission": None,
        }


@pytest.mark.parametrize(
    ("surface", "tool_name", "tool_args"),
    [
        ("full", "host.status", {}),
        ("core", "work.get", {"workRef": "work:core-tcp"}),
    ],
)
def test_tcp_mcp_requires_real_http_service_identity_before_host_owner_call(
    tmp_path, surface: str, tool_name: str, tool_args: dict
) -> None:
    """A transport-authenticated local Principal, not Tool args, gates Host forwarding."""
    secret = tmp_path / "gateway-bearer"
    secret.write_text("X" * 64, encoding="utf-8")
    secret.chmod(0o600)

    async def verify() -> None:
        owner = HostStatusOwner()
        policy = SourceAuthZenStub()
        app = build_http_app(
            build_server(
                service=GatewayService(owner),
                capability_authorizer=policy,
                require_http_execution_identity=True,
                protect_artifact_reads=True,
                surface=surface,
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
                    advertised = {item.name for item in listed.tools}
                    if surface == "core":
                        assert advertised == CORE_PUBLIC_TOOLS
                        assert "host.status" not in advertised
                        hidden = await client.call_tool("host.status", {})
                        assert hidden.is_error is True
                        assert owner.calls == []
                        assert policy.calls == [], "hidden Core Tool must not probe PDP"
                    else:
                        assert "host.status" in advertised
                    result = await client.call_tool(tool_name, tool_args)
                    assert result.is_error is False
                    assert result.structured_content["kind"] == (
                        "ordivon.host-work" if surface == "core" else "ordivon.host-status"
                    )
                    assert owner.calls == [("host", tool_name)]
                    assert policy.calls[0]["requested_capability"] == "host.legacy-read"
                    resource = policy.calls[0]["requested_resource"]["properties"]
                    assert resource["unscoped"] is (surface == "full")
                    if surface == "core":
                        assert resource["requestedSelectors"] == {"workRef": "work:core-tcp"}
                    assert policy.calls[0]["principal_id"] == ("principal:local-service:harness")

                    # A valid HTTP service bearer is not enough to bypass PDP.
                    policy.outcome = "DENY"
                    denied = await client.call_tool(tool_name, tool_args)
                    assert denied.is_error is True
                    assert denied.structured_content["error"]["code"] == ("CAPABILITY_AUTHZ_DENIED")
                    assert owner.calls == [("host", tool_name)]

                    policy.outcome = "UNAVAILABLE"
                    missing = await client.call_tool(tool_name, tool_args)
                    assert missing.is_error is True
                    assert missing.structured_content["error"]["code"] == (
                        "CAPABILITY_AUTHZ_UNAVAILABLE"
                    )
                    assert owner.calls == [("host", tool_name)]
        finally:
            server.should_exit = True
            await asyncio.wait_for(serving, timeout=12)

    asyncio.run(verify())
