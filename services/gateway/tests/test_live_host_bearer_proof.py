"""Real Host workload bearer admission: the path alone is not a proof.

Covers only the existing Gateway-to-Host Owner MCP transport. Does not issue
Principal/Actor grants or authorize production deployment.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "packaging" / "check_live_host_admission.py"
KNOWN_TOKEN = "p" * 48
MCP_INIT_ID = "gateway-host-anonymous-release-negative"
VALID_RESULT = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": MCP_INIT_ID,
        "result": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "serverInfo": {"name": "ordivon-host-v2", "version": "0.8.0"},
        },
    }
).encode()


@pytest.fixture(scope="module")
def preflight() -> Any:
    spec = importlib.util.spec_from_file_location("host_live_bearer_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _private_credential(tmp_path: Path) -> Path:
    path = tmp_path / "owner-token"
    path.write_text(KNOWN_TOKEN, encoding="utf-8")
    os.chmod(path, 0o600)
    return path


@pytest.mark.parametrize(
    ("status", "response", "accepted"),
    [
        (200, VALID_RESULT, True),
        (200, b'{"jsonrpc":"2.0","id":"other","result":{}}', False),
        (
            200,
            b'{"jsonrpc":"2.0","id":"gateway-host-anonymous-release-negative","error":{"code":-1}}',
            False,
        ),
        (200, b"<html>ok</html>", False),
        (401, VALID_RESULT, False),
        (403, VALID_RESULT, False),
        (302, VALID_RESULT, False),
        (503, VALID_RESULT, False),
    ],
)
def test_live_host_bearer_positive_requires_exact_authenticated_mcp_initialize(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    status: int,
    response: bytes,
    accepted: bool,
) -> None:
    credential = _private_credential(tmp_path)
    seen: list[tuple[str, str, dict[str, str]]] = []

    class Connection:
        def __init__(self, host: str, port: int, timeout: int):
            assert (host, port, timeout) == ("127.0.0.1", 8898, 4)

        def request(self, method: str, url: str, *, body: bytes, headers: dict[str, str]):
            assert body == preflight.MCP_INITIALIZE
            seen.append((method, url, headers))

        def getresponse(self):
            return type("Response", (), {"status": status, "read": lambda _self, _size: response})()

        def close(self):
            pass

    monkeypatch.setattr(preflight.http.client, "HTTPConnection", Connection)
    environment = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        f"ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE={credential}"
    )
    assert (
        preflight._authenticated_host_initialize_accepted(environment, anonymous_denied=True)
        is accepted
    )
    assert len(seen) == 1
    assert seen[0][0:2] == ("POST", "/mcp")
    assert seen[0][2]["Authorization"] == f"Bearer {KNOWN_TOKEN}"


@pytest.mark.parametrize(
    ("anonymous_denied", "owner_url", "credential_relative"),
    [
        (False, "http://127.0.0.1:8898/mcp", False),
        (True, "http://127.0.0.1:9000/mcp", False),
        (True, "http://127.0.0.1:8898/mcp", True),
    ],
)
def test_host_bearer_never_sent_before_anonymous_denial_or_to_unqualified_route(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    anonymous_denied: bool,
    owner_url: str,
    credential_relative: bool,
) -> None:
    path = _private_credential(tmp_path)
    credential = "relative/file" if credential_relative else str(path)

    class DoNotConnect:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("bearer must not be sent to this Host")

    monkeypatch.setattr(preflight.http.client, "HTTPConnection", DoNotConnect)
    env = (
        f"ORDIVON_GATEWAY_HOST_URL={owner_url} ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE={credential}"
    )
    assert (
        preflight._authenticated_host_initialize_accepted(env, anonymous_denied=anonymous_denied)
        is False
    )


def test_host_bearer_systemd_credential_expansion_is_unit_scoped(preflight: Any) -> None:
    env = "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    assert preflight._declared_owner_credential_path(env) == (
        "/run/credentials/ordivon-gateway.service/host-mcp-bearer"
    )
    assert (
        preflight._declared_owner_credential_path(
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/../other-service/secret"
        )
        is None
    )


def test_live_release_standing_requires_positive_owner_bearer_proof(preflight: Any) -> None:
    positive = {
        "status": "NECESSARY_PRECONDITIONS_PRESENT",
        "reasons": [],
    }
    denied = preflight._apply_authenticated_host_canary(positive.copy(), qualified=False)
    assert denied["status"] == "NO_GO"
    assert denied["reasons"] == ["HOST_OWNER_AUTHENTICATED_MCP_NOT_PROVEN"]
    assert denied["hostOwnerAuthenticatedInitializeAccepted"] is False
    # A separate result object matters: a shallow copy would reuse the
    # negative case's mutable reasons and test the fixture, not the product.
    allowed = preflight._apply_authenticated_host_canary(
        {"status": "NECESSARY_PRECONDITIONS_PRESENT", "reasons": []}, qualified=True
    )
    assert allowed["status"] == "NECESSARY_PRECONDITIONS_PRESENT"
    assert allowed["reasons"] == []
    assert allowed["hostOwnerAuthenticatedInitializeAccepted"] is True


def test_official_main_requires_live_bearer_canary_not_only_config_declaration(
    preflight: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test the actual installer-called main, not an isolated unconsumed helper."""
    import subprocess
    import sys

    grant = {
        "active": True,
        "principalId": "principal:cf-access:" + "a" * 64,
        "issuer": "https://issuer.test",
        "actorRef": "actor:ordivon:agent",
        "notBeforeEpochSeconds": 1000,
        "expiresAtEpochSeconds": 9000,
        "allowedTools": ["topic.resume"],
    }
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )
    seen: list[bool] = []
    monkeypatch.setattr(sys, "argv", ["check_live_host_admission.py"])
    monkeypatch.setattr(
        preflight,
        "_policy_data",
        lambda _path: {"ordivon": {"security": {"gateway_host_actor_grants": [grant]}}},
    )
    monkeypatch.setattr(preflight, "_qualified_systemd_environment", lambda _unit: env)
    monkeypatch.setattr(preflight, "_rejects_unauthenticated_host_initialize", lambda: True)
    monkeypatch.setattr(preflight, "_observed_non_gateway_host_tcp_clients", lambda: [])
    monkeypatch.setattr(
        preflight, "_unqualified_active_peer_host_consumers", lambda *, anonymous_denied: ()
    )
    monkeypatch.setattr(preflight, "_installed_security_host_read_surface_qualified", lambda: True)
    monkeypatch.setattr(preflight.time, "time", lambda: 1500)

    def fake_auth(_env: str, *, anonymous_denied: bool) -> bool:
        assert _env == env
        seen.append(anonymous_denied)
        return False

    monkeypatch.setattr(preflight, "_authenticated_host_initialize_accepted", fake_auth)
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(["systemctl"], 0, stdout="active\n"),
    )
    assert preflight.main() == 3
    verdict = json.loads(capsys.readouterr().out)
    assert verdict["status"] == "NO_GO"
    assert verdict["reasons"] == ["HOST_OWNER_AUTHENTICATED_MCP_NOT_PROVEN"]
    assert verdict["hostOwnerAuthenticatedInitializeAccepted"] is False
    assert seen == [True]


@pytest.mark.parametrize(
    ("bearer_accepted", "expected_unqualified"),
    [
        (False, True),
        (True, False),
    ],
)
def test_active_peer_bearer_must_authenticate_with_host_not_just_be_declared(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    bearer_accepted: bool,
    expected_unqualified: bool,
) -> None:
    """Peer configuration alone cannot prove its active Agent Host path works."""
    import subprocess

    unit = "ordivon-gateway-local-r21.service"
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )
    observations: list[tuple[str, bool, str]] = []

    def observe(command: list[str], **_kwargs):
        if "list-units" in command:
            return subprocess.CompletedProcess(
                command, 0, stdout=f"{unit} loaded active running peer\n"
            )
        assert command[:4] == ["/usr/bin/systemctl", "show", unit, "-p"]
        return subprocess.CompletedProcess(
            command, 0, stdout="" if command[4] == "EnvironmentFiles" else env
        )

    def peer_canary(environment: str, *, anonymous_denied: bool, unit: str = "") -> bool:
        observations.append((environment, anonymous_denied, unit))
        return bearer_accepted

    monkeypatch.setattr(preflight.subprocess, "run", observe)
    monkeypatch.setattr(preflight, "_authenticated_host_initialize_accepted", peer_canary)
    candidates = preflight._unqualified_active_peer_host_consumers(anonymous_denied=True)
    assert candidates == ((unit,) if expected_unqualified else ())
    assert observations == [(env, True, unit)]


def test_active_peer_never_sends_bearer_if_host_anonymous_access_not_denied(
    preflight: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real Host listener must be protected before peer credential use."""
    import subprocess

    unit = "ordivon-gateway-local-r21.service"
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    )

    def observe(command: list[str], **_kwargs):
        if "list-units" in command:
            return subprocess.CompletedProcess(
                command, 0, stdout=f"{unit} loaded active running peer\n"
            )
        return subprocess.CompletedProcess(
            command, 0, stdout="" if command[4] == "EnvironmentFiles" else env
        )

    def never_send(*_args, **_kwargs):
        raise AssertionError("peer must not receive credential probe before Host protects MCP")

    monkeypatch.setattr(preflight.subprocess, "run", observe)
    monkeypatch.setattr(preflight, "_authenticated_host_initialize_accepted", never_send)
    assert preflight._unqualified_active_peer_host_consumers(anonymous_denied=False) == (unit,)


def test_peer_credential_directory_is_independent_of_primary_gateway(preflight: Any) -> None:
    declaration = "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
    assert preflight._declared_owner_credential_path(declaration) == (
        "/run/credentials/ordivon-gateway.service/host-mcp-bearer"
    )
    assert (
        preflight._declared_owner_credential_path(
            declaration, unit="ordivon-gateway-local-r21.service"
        )
        == "/run/credentials/ordivon-gateway-local-r21.service/host-mcp-bearer"
    )
    assert preflight._declared_owner_credential_path(declaration + " " + declaration) is None
