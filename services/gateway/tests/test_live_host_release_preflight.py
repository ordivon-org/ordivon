"""Physical deployment prerequisite check for the *existing* release installer.

These are bounded negative tests. They do not create actual Security grants or
replace an Owner AuthZEN decision, actual Host canary, or production activation.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging" / "check_live_host_admission.py"
INSTALLER = ROOT / "packaging" / "install_release.sh"


@pytest.fixture(scope="module")
def preflight() -> Any:
    spec = importlib.util.spec_from_file_location("gateway_release_security_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _operator_data(grants: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ordivon": {
            "security": {
                "gateway_artifact_config": {"cf_issuer": "https://issuer.test"},
                "gateway_host_actor_grants": grants,
            }
        }
    }


def _grant() -> dict[str, Any]:
    return {
        "active": True,
        "principalId": "principal:cf-access:" + "a" * 64,
        "issuer": "https://issuer.test",
        "actorRef": "actor:ordivon:agent",
        "notBeforeEpochSeconds": 1_000,
        "expiresAtEpochSeconds": 9_000,
        "allowedTools": ["topic.resume", "message.post"],
        "exactRefs": ["topic:ordivon:test"],
    }


def test_real_missing_operator_grants_and_owner_credential_are_blocked(preflight: Any) -> None:
    result = preflight.assess(
        _operator_data([]), "", now=1_500, anonymous_host_initialize_denied=True
    )
    assert result["status"] == "NO_GO"
    assert result["activeHostDelegationCount"] == 0
    assert result["hostOwnerCredentialDeclared"] is False
    assert result["reasons"] == [
        "HOST_OPERATOR_DELEGATIONS_ABSENT_OR_INACTIVE",
        "GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED",
        "HOST_OWNER_ROUTE_NOT_QUALIFIED_FOR_LOCAL_CANARY",
    ]


def test_bounded_promotion_prerequisites_are_distinct_from_authorization(preflight: Any) -> None:
    result = preflight.assess(
        _operator_data([_grant()]),
        (
            "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer"
        ),
        now=1_500,
        anonymous_host_initialize_denied=True,
    )
    assert result["status"] == "NECESSARY_PRECONDITIONS_PRESENT"
    assert result["activeHostDelegationCount"] == 1
    assert result["hostOwnerCredentialDeclared"] is True
    assert "actual Principal-to-Actor and resource authorization" in result["unverified"]
    assert "direct Host MCP connector migration" in result["unverified"]


@pytest.mark.parametrize(
    "mutation",
    [
        {"active": False},
        {"principalId": ""},
        {"issuer": ""},
        {"actorRef": ""},
        {"notBeforeEpochSeconds": 2_000},
        {"expiresAtEpochSeconds": 1_499},
        {"expiresAtEpochSeconds": True},
        {"allowedTools": ["unrelated.capability"]},
        {"allowedTools": "message.post"},
    ],
)
def test_nonqualified_grants_cannot_unblock_live_release(
    preflight: Any, mutation: dict[str, Any]
) -> None:
    grant = {**_grant(), **mutation}
    assert (
        preflight.assess(
            _operator_data([grant]),
            (
                "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
                "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=/run/credentials/gateway/host"
            ),
            now=1_500,
            anonymous_host_initialize_denied=True,
        )["status"]
        == "NO_GO"
    )


@pytest.mark.parametrize(
    "environment",
    [
        "",
        "OTHER_SERVICE_BEARER_TOKEN_FILE=/run/credentials/other",
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=",
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=relative/path",
        'ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=broken\\"',
    ],
)
def test_missing_or_unqualified_owner_identity_remains_no_go(
    preflight: Any, environment: str
) -> None:
    assert not preflight._declares_host_owner_identity(environment)
    result = preflight.assess(_operator_data([_grant()]), environment, now=1_500)
    assert "GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED" in result["reasons"]


def test_operator_data_file_has_no_symlink_fallback(preflight: Any, tmp_path: Path) -> None:
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(_operator_data([_grant()])))
    symlink = tmp_path / "alias.json"
    symlink.symlink_to(path)
    assert preflight._policy_data(path) == _operator_data([_grant()])
    with pytest.raises(ValueError, match="unavailable"):
        preflight._policy_data(symlink)
    path.write_text("[]")
    with pytest.raises(ValueError, match="object"):
        preflight._policy_data(path)


def test_official_production_promotion_consumer_checks_before_atomic_switch() -> None:
    installer = INSTALLER.read_text(encoding="utf-8")
    needle = '"$RELEASE/.venv/bin/python" "$RELEASE/packaging/check_live_host_admission.py"'
    assert needle in installer
    assert '"$(realpath -m "$PREFIX")" = "/opt/ordivon/gateway"' in installer
    assert "/run/credentials/ordivon-security-gateway-authzen.service/trusted-issuer" in installer
    assert installer.index(needle) < installer.index('ln -sfn "releases/$COMMIT"')
    assert installer.index(needle) > installer.index("service_user_preflight=pass")


@pytest.mark.parametrize(
    ("http_status", "qualifies_denial"),
    [
        (200, False),
        (201, False),
        (302, False),
        (400, False),
        (401, True),
        (403, True),
        (404, False),
        (503, False),
    ],
)
def test_local_host_initialize_negative_requires_http_auth_denial(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
    http_status: int,
    qualifies_denial: bool,
) -> None:
    requests: list[tuple[str, str, dict[str, str]]] = []

    class FakeConnection:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            assert (host, port, timeout) == ("127.0.0.1", 8898, 4)

        def request(
            self,
            method: str,
            path: str,
            *,
            body: bytes,
            headers: dict[str, str],
        ) -> None:
            assert b'"method":"initialize"' in body
            assert "Authorization" not in headers
            requests.append((method, path, headers))

        def getresponse(self) -> Any:
            return type("Response", (), {"status": http_status})()

        def close(self) -> None:
            pass

    monkeypatch.setattr(preflight.http.client, "HTTPConnection", FakeConnection)
    assert preflight._rejects_unauthenticated_host_initialize() is qualifies_denial
    assert len(requests) == 1
    assert requests[0][0:2] == ("POST", "/mcp")


def test_host_anonymous_network_failure_is_not_proof(
    preflight: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingConnection:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def request(self, *_args: Any, **_kwargs: Any) -> None:
            raise ConnectionRefusedError("fixture-only")

        def close(self) -> None:
            pass

    monkeypatch.setattr(preflight.http.client, "HTTPConnection", FailingConnection)
    assert preflight._rejects_unauthenticated_host_initialize() is False


@pytest.mark.parametrize(
    "host_owner_url",
    [
        "",
        "http://127.0.0.1:8898/",
        "http://localhost:8898/mcp",
        "https://host-mcp.ordivon.com/mcp",
        "http://127.0.0.1:9999/mcp",
    ],
)
def test_gateway_must_route_to_exact_negatively_probed_host(
    preflight: Any,
    host_owner_url: str,
) -> None:
    env = f"ORDIVON_GATEWAY_HOST_URL={host_owner_url} "
    env += "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=/run/gateway/host"
    result = preflight.assess(
        _operator_data([_grant()]),
        env,
        now=1_500,
        anonymous_host_initialize_denied=True,
    )
    assert result["status"] == "NO_GO"
    assert result["hostOwnerRouteQualified"] is False
    assert "HOST_OWNER_ROUTE_NOT_QUALIFIED_FOR_LOCAL_CANARY" in result["reasons"]


def test_host_direct_anonymous_denial_cannot_be_inferred_from_grants(
    preflight: Any,
) -> None:
    env = (
        "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp "
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=/run/gateway/host"
    )
    for observed in (None, False):
        result = preflight.assess(
            _operator_data([_grant()]),
            env,
            now=1_500,
            anonymous_host_initialize_denied=observed,
        )
        assert result["status"] == "NO_GO"
        assert result["activeHostDelegationCount"] == 1
        assert result["hostOwnerCredentialDeclared"] is True
        assert result["hostOwnerRouteQualified"] is True
        assert result["anonymousHostInitializeDenied"] is False
        assert "HOST_DIRECT_ANONYMOUS_MCP_NOT_PROVEN_DENIED" in result["reasons"]
