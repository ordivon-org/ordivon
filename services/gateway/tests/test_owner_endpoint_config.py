"""Owner transport configuration is a projection, not authentication."""

from __future__ import annotations

import asyncio

import pytest

from ordivon_gateway.logic.owner_protocol import OwnerCallError
from ordivon_gateway.transport.owner_endpoint_config import owner_endpoints_from_env
from ordivon_gateway.transport.upstream import McpOwnerCaller


def test_configured_owner_file_refs_pass_through_unchanged(monkeypatch):
    for key in (
        "ORDIVON_GATEWAY_LINUX_RUNTIME_URL",
        "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE",
        "ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL",
        "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_ID_FILE",
        "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_SECRET_FILE",
        "ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ORDIVON_GATEWAY_LINUX_RUNTIME_URL", "http://127.0.0.1:8897/mcp")
    monkeypatch.setenv(
        "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE", "/tmp/nonexistent-auth-file"
    )
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL", "https://win.example.test/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_ID_FILE", "/tmp/access-id")
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_SECRET_FILE", "/tmp/access-secret")
    monkeypatch.setenv("ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE", "2026-07-28")
    owners = owner_endpoints_from_env()
    assert owners["runtime.linux"].bearer_token_file == "/tmp/nonexistent-auth-file"
    assert owners["runtime.windows"].access_client_id_file == "/tmp/access-id"
    assert owners["runtime.windows"].mcp_mode == "2026-07-28"
    # Loading references is not an authentication grant or a network call.
    caller = McpOwnerCaller.from_env()
    assert caller.is_configured("runtime.linux") is True
    assert caller.is_configured("runtime.windows") is True


@pytest.mark.parametrize(
    ("url", "bearer"),
    [
        ("http://127.0.0.1:8897/mcp", "/tmp/harness-auth"),
        ("http://127.0.0.1:8897/harness/mcp", "/tmp/ordinary-auth"),
        ("http://127.0.0.1:8897/harness/mcp?profile=ordinary", "/tmp/harness-auth"),
        ("http://127.0.0.1:8897/harness/mcp", ""),
    ],
)
def test_protected_harness_route_cannot_alias_ordinary_runtime(monkeypatch, url, bearer):
    monkeypatch.setenv("ORDIVON_GATEWAY_LINUX_RUNTIME_URL", "http://127.0.0.1:8897/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE", "/tmp/ordinary-auth")
    monkeypatch.setenv("ORDIVON_GATEWAY_HARNESS_RUNTIME_URL", url)
    monkeypatch.setenv("ORDIVON_GATEWAY_HARNESS_RUNTIME_BEARER_TOKEN_FILE", bearer)
    caller = McpOwnerCaller.from_env()
    assert caller.is_configured("runtime.linux")
    assert not caller.is_configured("runtime.harness")


def test_protected_harness_route_accepts_distinct_profile(monkeypatch):
    monkeypatch.setenv("ORDIVON_GATEWAY_LINUX_RUNTIME_URL", "http://127.0.0.1:8897/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE", "/tmp/ordinary-auth")
    monkeypatch.setenv("ORDIVON_GATEWAY_HARNESS_RUNTIME_URL", "http://127.0.0.1:8897/harness/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_HARNESS_RUNTIME_BEARER_TOKEN_FILE", "/tmp/harness-auth")
    caller = McpOwnerCaller.from_env()
    assert caller.is_configured("runtime.linux")
    assert caller.is_configured("runtime.harness")


def test_invalid_harness_profile_is_denied_before_transport(monkeypatch):
    monkeypatch.setenv("ORDIVON_GATEWAY_LINUX_RUNTIME_URL", "http://127.0.0.1:8897/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE", "/tmp/ordinary-auth")
    monkeypatch.setenv("ORDIVON_GATEWAY_HARNESS_RUNTIME_URL", "http://127.0.0.1:8897/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_HARNESS_RUNTIME_BEARER_TOKEN_FILE", "/tmp/harness-auth")
    caller = McpOwnerCaller.from_env()

    def unexpected(*args, **kwargs):
        pytest.fail("misconfigured protected profile must never reach HTTP transport")

    monkeypatch.setattr(caller, "_http_client", unexpected)
    with pytest.raises(OwnerCallError) as exc:
        asyncio.run(caller.call_tool("runtime.harness", "workspace.exec", {}))
    assert "dedicated /harness/mcp endpoint" in str(exc.value)
