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
    result = preflight.assess(_operator_data([]), "", now=1_500)
    assert result["status"] == "NO_GO"
    assert result["activeHostDelegationCount"] == 0
    assert result["hostOwnerCredentialDeclared"] is False
    assert result["reasons"] == [
        "HOST_OPERATOR_DELEGATIONS_ABSENT_OR_INACTIVE",
        "GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED",
    ]


def test_bounded_promotion_prerequisites_are_distinct_from_authorization(preflight: Any) -> None:
    result = preflight.assess(
        _operator_data([_grant()]),
        "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=%d/host-mcp-bearer",
        now=1_500,
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
            "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE=/run/credentials/gateway/host",
            now=1_500,
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
