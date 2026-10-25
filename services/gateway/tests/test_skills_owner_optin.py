from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ordivon_gateway.upstream import McpOwnerCaller, OwnerCallError, OwnerEndpoint


def test_skills_unset_remains_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ORDIVON_GATEWAY_SKILLS_URL", raising=False)
    monkeypatch.delenv("ORDIVON_GATEWAY_SKILLS_BEARER_TOKEN_FILE", raising=False)
    caller = McpOwnerCaller.from_env()
    assert caller.configuration_error("skills") == "owner endpoint is not configured"


def test_skills_url_without_bearer_identity_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORDIVON_GATEWAY_SKILLS_URL", "http://127.0.0.1:8895/mcp")
    monkeypatch.delenv("ORDIVON_GATEWAY_SKILLS_BEARER_TOKEN_FILE", raising=False)
    caller = McpOwnerCaller.from_env()
    assert caller.configuration_error("skills") == "owner authentication is not configured"
    with pytest.raises(OwnerCallError) as failure:
        asyncio.run(
            caller.call_tool("skills", "skills.resolve", {"ref": "recursive-lego-calculus"})
        )
    assert failure.value.error == {
        "code": "OWNER_AUTH_NOT_CONFIGURED",
        "message": "owner authentication is not configured",
        "origin": "gateway_adapter",
    }


def test_skills_bearer_file_enables_existing_mcp_owner_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "bearer"
    path.write_text("not-a-real-secret\\n", encoding="utf-8")
    path.chmod(0o600)
    monkeypatch.setenv("ORDIVON_GATEWAY_SKILLS_URL", "http://127.0.0.1:8895/mcp")
    monkeypatch.setenv("ORDIVON_GATEWAY_SKILLS_BEARER_TOKEN_FILE", str(path))
    caller = McpOwnerCaller.from_env()
    assert caller.configuration_error("skills") is None
    assert caller._owners["skills"] == OwnerEndpoint(
        "http://127.0.0.1:8895/mcp", bearer_token_file=str(path)
    )


def test_skills_activation_is_explicit_optional_systemd_credential() -> None:
    root = Path(__file__).resolve().parents[1]
    unit = (root / "systemd/ordivon-gateway.service").read_text(encoding="utf-8")
    example = (root / "systemd/ordivon-gateway.service.d/35-skills-owner.example.conf").read_text(
        encoding="utf-8"
    )
    assert "ORDIVON_GATEWAY_SKILLS_URL" not in unit
    assert "LoadCredential=skills-owner-bearer:/etc/ordivon/skills-mcp.token" in example
    assert "ORDIVON_GATEWAY_SKILLS_URL=http://127.0.0.1:8895/mcp" in example
    assert "ORDIVON_GATEWAY_SKILLS_BEARER_TOKEN_FILE=%d/skills-owner-bearer" in example
    assert "After=ordivon-skills-mcp.service" in example
