"""Host owner-side HTTP authentication falsifiers with native MCP/Starlette components."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx2
import pytest

from ordivon_host_v2.http_identity import (
    HOST_MCP_SCOPE,
    HostServiceTokenVerifier,
    protect_host_http_app,
)


async def responder(scope, receive, send):
    await send({"type": "http.response.start", "status": 204, "headers": []})
    await send({"type": "http.response.body", "body": b""})


async def request(app, headers=None):
    async with httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=app),
        base_url="http://127.0.0.1:8898",
    ) as client:
        return await client.post("/mcp", headers=headers or {}, json={"method": "tools/list"})


def provision(tmp_path: Path):
    file = tmp_path / "service.token"
    file.write_text("s" * 48, encoding="utf-8")
    file.chmod(0o600)
    resource = "http://127.0.0.1:8898/mcp"
    return file, resource


def test_actual_native_mcp_http_gate_rejects_unauthorized_and_accepts_service(tmp_path):
    file, resource = provision(tmp_path)
    app = protect_host_http_app(responder, credential_file=str(file), resource_url=resource)
    for headers in (
        {},
        {"Authorization": "Bearer " + "x" * 48},
        {"cf-access-jwt-assertion": "forged", "X-Principal": "service:gateway"},
        {"Authorization": "Bearer " + "s" * 47},
    ):
        response = asyncio.run(request(app, headers))
        assert response.status_code == 401
        assert response.headers["www-authenticate"].startswith("Bearer ")
    allowed = asyncio.run(request(app, {"Authorization": "Bearer " + "s" * 48}))
    assert allowed.status_code == 204
    # Rotation revokes the old credential immediately, without process restart.
    file.write_text("t" * 48, encoding="utf-8")
    assert asyncio.run(request(app, {"Authorization": "Bearer " + "s" * 48})).status_code == 401
    assert asyncio.run(request(app, {"Authorization": "Bearer " + "t" * 48})).status_code == 204


def test_native_token_verifier_preserves_resource_and_scope(tmp_path):
    file, resource = provision(tmp_path)
    verifier = HostServiceTokenVerifier(str(file), resource)
    token = asyncio.run(verifier.verify_token("s" * 48))
    assert token is not None
    assert token.resource == resource
    assert token.scopes == [HOST_MCP_SCOPE]
    assert token.subject == "service:ordivon-gateway"
    assert asyncio.run(verifier.verify_token("forged")) is None


def test_host_credential_source_rejects_unsafe_paths_and_file_modes(tmp_path):
    file, resource = provision(tmp_path)
    with pytest.raises(ValueError, match="absolute"):
        HostServiceTokenVerifier("relative.file", resource)
    alias = tmp_path / "alias"
    alias.symlink_to(file)
    with pytest.raises(OSError):
        HostServiceTokenVerifier(str(alias), resource)
    file.chmod(0o644)
    with pytest.raises(ValueError, match="permissive"):
        HostServiceTokenVerifier(str(file), resource)
    file.chmod(0o600)
    file.write_text("too-short", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid"):
        HostServiceTokenVerifier(str(file), resource)


def test_missing_host_credential_fails_startup_without_anonymous_fallback(tmp_path):
    with pytest.raises(FileNotFoundError):
        protect_host_http_app(
            responder,
            credential_file=str(tmp_path / "missing"),
            resource_url="http://127.0.0.1:8898/mcp",
        )


def test_actual_host_mcp_sdk_tools_list_requires_workload_bearer(tmp_path: Path):
    """Exercise native SDK sessions, not only a fake ASGI downstream."""
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client
    from mcp.server.transport_security import TransportSecuritySettings

    from ordivon_host_v2.mcp_server import build_server

    token_file, resource = provision(tmp_path)
    server = build_server("postgresql://invalid-host-test-dsn")
    app = server.streamable_http_app(
        host="127.0.0.1",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["127.0.0.1:*"],
            allowed_origins=["http://127.0.0.1:*"],
        ),
    )
    protected = protect_host_http_app(app, credential_file=str(token_file), resource_url=resource)

    async def exercise():
        async with app.router.lifespan_context(app):
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=protected),
                base_url="http://127.0.0.1:8898",
                headers={"Authorization": "Bearer " + "s" * 48},
            ) as http:
                async with Client(
                    streamable_http_client(resource, http_client=http),
                    raise_exceptions=True,
                ) as client:
                    discovered = await client.list_tools()
                    names = {tool.name for tool in discovered.tools}
                    assert len(names) == 30
                    assert "work.create" in names and "message.post" in names
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=protected),
                base_url="http://127.0.0.1:8898",
            ) as http:
                rejected = await http.post(
                    "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
                )
                assert rejected.status_code == 401
                # Complete direct-Owner surface: every actually discovered
                # Host MCP Tool is behind the same HTTP identity boundary.
                for name in sorted(names):
                    denied = await http.post(
                        "/mcp",
                        json={
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/call",
                            "params": {
                                "name": name,
                                "arguments": {"actorRef": "actor:forged"},
                                "_meta": {"ordivon_access_principal": "forged"},
                            },
                        },
                    )
                    assert denied.status_code == 401, name

    asyncio.run(exercise())


def test_http_cli_refuses_missing_credential_before_network_bind(
    monkeypatch: pytest.MonkeyPatch,
):
    from ordivon_host_v2.mcp_server import main

    monkeypatch.setenv("ORDIVON_HOST_V2_TRANSPORT", "streamable-http")
    monkeypatch.setenv("ORDIVON_HOST_V2_DSN", "postgresql://invalid-host-test-dsn")
    monkeypatch.delenv("ORDIVON_HOST_V2_BEARER_TOKEN_FILE", raising=False)
    with pytest.raises(RuntimeError, match="ORDIVON_HOST_V2_BEARER_TOKEN_FILE"):
        main()


def test_systemd_credential_group_read_is_supported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    directory = tmp_path / "credentials"
    directory.mkdir(mode=0o750)
    credential = directory / "host-mcp-bearer"
    credential.write_text("n" * 48, encoding="utf-8")
    credential.chmod(0o440)
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(directory))
    verifier = HostServiceTokenVerifier(str(credential), "http://127.0.0.1:8898/mcp")
    assert asyncio.run(verifier.verify_token("n" * 48)) is not None
    monkeypatch.delenv("CREDENTIALS_DIRECTORY")
    with pytest.raises(ValueError, match="permissive"):
        HostServiceTokenVerifier(str(credential), "http://127.0.0.1:8898/mcp")
