"""One Host natural owner, optional separately authenticated read transport."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from ordivon_gateway.capabilities.host.dispatch import HostContinuityAdapter
from ordivon_gateway.logic.host_tool_contracts import HOST_READ_TOOLS, SOCIAL_WORK_HOST_TOOLS
from ordivon_gateway.security.authorization_targets import (
    _HOST_READ_ONLY_TOOLS,
    _HOST_READ_SELECTORS,
)
from ordivon_gateway.service import GatewayService
from ordivon_gateway.transport.upstream import McpOwnerCaller, OwnerCallError


class Owner:
    def __init__(self, *, protected_read: bool) -> None:
        self.protected_read = protected_read
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.fail_read = False

    def has_route(self, route: str) -> bool:
        return self.protected_read and route == "host.read"

    def is_configured(self, route: str) -> bool:
        return route in {"host", "host.read"} if self.protected_read else route == "host"

    def configuration_error(self, route: str) -> str | None:
        return None if self.is_configured(route) else "owner endpoint not configured"

    async def call_tool(self, route: str, name: str, arguments: dict[str, Any]) -> dict:
        self.calls.append((route, name, dict(arguments)))
        if route == "host.read" and self.fail_read:
            raise OwnerCallError("protected read endpoint unavailable", owner_id=route)
        if name == "host.status":
            return {"schemaVersion": 3, "kind": "ordivon.host-status"}
        return {"owner": "host", "sourceRoute": route, "echo": arguments}


def test_read_write_classification_is_one_canonical_tool_contract() -> None:
    assert _HOST_READ_ONLY_TOOLS == HOST_READ_TOOLS == frozenset(_HOST_READ_SELECTORS)
    assert HOST_READ_TOOLS <= SOCIAL_WORK_HOST_TOOLS
    assert "work.get" in HOST_READ_TOOLS
    assert "topic.resume" in HOST_READ_TOOLS
    assert "message.post" not in HOST_READ_TOOLS
    assert "work.snapshot.commit" not in HOST_READ_TOOLS


def test_legacy_host_owner_remains_exact_read_write_behavior() -> None:
    owner = Owner(protected_read=False)
    adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
    read = asyncio.run(adapter.call("work.get", {"workRef": "work:one"}))
    write = asyncio.run(adapter.call("message.post", {"messageRef": "message:one"}))
    assert read["sourceRoute"] == "host"
    assert write["sourceRoute"] == "host"
    assert [item[0] for item in owner.calls] == ["host", "host"]


def test_explicit_protected_host_read_routes_without_redirecting_writes() -> None:
    owner = Owner(protected_read=True)
    adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
    for name in ("work.get", "topic.resume", "attention.delta"):
        result = asyncio.run(adapter.call(name, {"test": name}))
        assert result["sourceRoute"] == "host.read"
    result = asyncio.run(adapter.call("message.post", {"test": "write"}))
    assert result["sourceRoute"] == "host"
    assert [item[0] for item in owner.calls] == ["host.read"] * 3 + ["host"]


def test_failed_explicit_protected_read_never_falls_back_to_legacy() -> None:
    owner = Owner(protected_read=True)
    owner.fail_read = True
    adapter = HostContinuityAdapter(owner)  # type: ignore[arg-type]
    with pytest.raises(OwnerCallError, match="protected read"):
        asyncio.run(adapter.call("work.get", {"workRef": "work:one"}))
    assert owner.calls == [("host.read", "work.get", {"workRef": "work:one"})]


def test_host_status_discovery_follows_the_read_endpoint_with_distinct_write_fact() -> None:
    owner = Owner(protected_read=True)
    service = GatewayService(owner)  # type: ignore[arg-type]
    inquiry = asyncio.run(service.capability_inquire(capability="continuity.external"))
    assert inquiry.readiness_state == "ready"
    assert owner.calls == [("host.read", "host.status", {"detail": "summary"})]
    assert service.system_describe().owners[3].owner_id == "host"
    assert service.system_describe().owners[3].configured is True
    facts = {f.predicate: f.state for f in inquiry.inquiry.facts}
    assert facts["gateway.host_write_endpoint_qualified"] == "supported"
    assert facts["host.specific_work_read_authorized"] == "unobserved"


def test_read_route_without_machine_identity_remains_declared_but_unqualified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ORDIVON_GATEWAY_HOST_URL", "http://127.0.0.1:8898/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_HOST_READ_URL", "http://127.0.0.1:19008/mcp")
    monkeypatch.delenv("ORDIVON_GATEWAY_HOST_READ_BEARER_TOKEN_FILE", raising=False)
    caller = McpOwnerCaller.from_env()
    assert caller.has_route("host.read")
    assert caller.configuration_error("host.read") == "owner authentication is not configured"
    adapter = HostContinuityAdapter(caller)
    with pytest.raises(OwnerCallError, match="owner authentication is not configured"):
        asyncio.run(adapter.call("work.get", {"workRef": "work:one"}))
    # No fallback to the legacy Host even though it is declared in the config.
    assert caller.has_route("host")


def test_full_private_credentials_can_qualify_optional_host_read_route(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bearer = tmp_path / "host-read-credential"
    bearer.write_text("test-only-secret-12345678901234567890", encoding="utf-8")
    bearer.chmod(0o600)
    monkeypatch.setenv("ORDIVON_GATEWAY_HOST_READ_URL", "http://127.0.0.1:19008/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_HOST_READ_BEARER_TOKEN_FILE", str(bearer))
    caller = McpOwnerCaller.from_env()
    assert caller.has_route("host.read")
    assert caller.is_configured("host.read")
    # Configuration is not network health or a Host permission grant.
