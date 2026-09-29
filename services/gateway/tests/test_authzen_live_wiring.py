from __future__ import annotations

import os
from pathlib import Path

import pytest

from ordivon_gateway.authzen_authorizer import AuthZenPrincipalAuthorizer
from ordivon_gateway.mcp_server import _authzen_authorizer_from_env


def _clear(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT",
        "ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE",
        "ORDIVON_GATEWAY_AUTHZEN_TIMEOUT_SECONDS",
        "ORDIVON_GATEWAY_AUTHZEN_ALLOW_INSECURE_LOOPBACK",
    ):
        monkeypatch.delenv(name, raising=False)


def test_authzen_live_wiring_is_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear(monkeypatch)
    assert _authzen_authorizer_from_env() is None


def test_authzen_live_wiring_requires_endpoint_and_credential_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv(
        "ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT",
        "https://pdp.example.test/access/v1/evaluation",
    )
    with pytest.raises(RuntimeError, match="requires both"):
        _authzen_authorizer_from_env()


def test_authzen_live_wiring_is_explicit_and_reversible(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear(monkeypatch)
    credential = tmp_path / "authzen-bearer"
    credential.write_text("test-token-material-1234567890", encoding="utf-8")
    os.chmod(credential, 0o600)
    monkeypatch.setenv(
        "ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT",
        "https://pdp.example.test/access/v1/evaluation",
    )
    monkeypatch.setenv("ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE", str(credential))
    assert isinstance(_authzen_authorizer_from_env(), AuthZenPrincipalAuthorizer)
    monkeypatch.delenv("ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT")
    monkeypatch.delenv("ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE")
    assert _authzen_authorizer_from_env() is None


def test_authzen_live_wiring_rejects_insecure_remote_endpoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear(monkeypatch)
    credential = tmp_path / "authzen-bearer"
    credential.write_text("test-token-material-1234567890", encoding="utf-8")
    os.chmod(credential, 0o600)
    monkeypatch.setenv(
        "ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT",
        "http://pdp.example.test/access/v1/evaluation",
    )
    monkeypatch.setenv("ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE", str(credential))
    with pytest.raises(RuntimeError, match="HTTPS"):
        _authzen_authorizer_from_env()
