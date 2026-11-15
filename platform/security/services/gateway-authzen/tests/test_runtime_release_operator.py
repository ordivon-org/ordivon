"""Native Security OPA/AuthZEN consumer for Gateway Linux Runtime release.

Fixtures are local and short-lived. No real Operator grant or deployment occurs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import time
import uuid
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from ordivon_security_gateway_authzen.server import make_app

ROOT = Path(__file__).resolve().parents[1]
OPA = shutil.which("opa")
pytestmark = pytest.mark.skipif(OPA is None, reason="native OPA required")
PRINCIPAL = "principal:cf-access:" + "a" * 64
ISSUER = "https://operator-issuer.test"
TOKEN = "test-fixture-owner-release-bearer-" + "c" * 40


def grant() -> dict:
    now = int(time.time())
    return {
        "active": True,
        "role": "operator",
        "principalId": PRINCIPAL,
        "issuer": ISSUER,
        "ownerId": "runtime.linux",
        "nodeId": "linux-pg",
        "allowQualifiedCandidates": True,
        "allowedTools": ["runtime.release.apply"],
        "notBeforeEpochSeconds": now - 10,
        "expiresAtEpochSeconds": now + 1200,
    }


def data(grants: list[dict]) -> dict:
    return {
        "ordivon": {
            "security": {
                "gateway_artifact_config": {"cf_issuer": ISSUER},
                "gateway_runtime_release_grants": grants,
            }
        }
    }


def target(**changes) -> dict:
    identity = {
        "requestId": "release-prod-20261115",
        "workspaceId": "ws-gateway-native-linux-r1",
        "commit": "a" * 40,
        "candidateManifestDigest": "sha256:" + "b" * 64,
        "expectedToolCount": 26,
    }
    identity.update(changes)
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return {
        "type": "ordivon.runtime.native-release-request",
        "id": "runtime-release:v1:" + digest,
        "properties": {
            "identityContract": "ordivon.gateway-native-runtime-release-request.v1",
            "ownerId": "runtime.linux",
            "nodeId": "linux-pg",
            "requestSha256": digest,
            **identity,
        },
    }


def payload(resource: dict | None = None) -> dict:
    return {
        "subject": {"type": "user", "id": PRINCIPAL, "properties": {"issuer": ISSUER}},
        "action": {
            "name": "runtime.release.linux",
            "properties": {"gatewayTool": "runtime.release.apply"},
        },
        "resource": target() if resource is None else resource,
    }


@pytest.fixture
def endpoint(tmp_path: Path):
    token_path = tmp_path / "test-token"
    token_path.write_text(TOKEN, encoding="utf-8")
    token_path.chmod(0o600)
    policy_path = tmp_path / "policy-data"
    policy_path.write_text(json.dumps(data([])), encoding="utf-8")
    policy_path.chmod(0o600)
    with TestClient(
        make_app(
            token_path=str(token_path),
            policy=str(ROOT / "policies" / "gateway_artifact.rego"),
            policy_data=str(policy_path),
            opa=str(OPA),
        )
    ) as client:
        yield client, policy_path


def set_grants(path: Path, grants: list[dict]) -> None:
    path.write_text(json.dumps(data(grants)), encoding="utf-8")
    path.chmod(0o600)


def decide(client: TestClient, request: dict) -> bool:
    uid = str(uuid.uuid4())
    response = client.post(
        "/access/v1/evaluation",
        json=request,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "X-Request-ID": uid,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["X-Request-ID"] == uid
    answer = response.json()["decision"]
    assert type(answer) is bool
    return answer


def test_no_grant_then_operator_allow_then_revoke_without_restarting_pdp(endpoint) -> None:
    client, path = endpoint
    assert decide(client, payload()) is False
    set_grants(path, [grant()])
    assert decide(client, payload()) is True
    revoked = grant()
    revoked["active"] = False
    set_grants(path, [revoked])
    assert decide(client, payload()) is False


@pytest.mark.parametrize(
    "change",
    [
        {"active": False},
        {"role": "agent"},
        {"principalId": "principal:cf-access:" + "c" * 64},
        {"issuer": "https://foreign-issuer.test"},
        {"nodeId": "windows-runtime"},
        {"ownerId": "runtime.windows"},
        {"allowQualifiedCandidates": False},
        {"allowQualifiedCandidates": "true"},
        {"allowedTools": ["execution.submit"]},
        {"allowedTools": "runtime.release.apply"},
        {"notBeforeEpochSeconds": int(time.time()) + 3600},
        {"expiresAtEpochSeconds": int(time.time()) - 1},
        {"expiresAtEpochSeconds": "forever"},
    ],
)
def test_opa_denies_unqualified_operator_grants(endpoint, change: dict) -> None:
    client, path = endpoint
    set_grants(path, [{**grant(), **change}])
    assert decide(client, payload()) is False


@pytest.mark.parametrize(
    "selectors, replacement",
    [
        (("subject", "id"), "principal:cf-access:" + "c" * 64),
        (("subject", "properties", "issuer"), "https://foreign.test"),
        (("action", "name"), "artifact.runtime"),
        (("action", "properties", "gatewayTool"), "execution.submit"),
        (("action", "properties", "gatewayTool"), "runtime.release.get"),
        (("resource", "type"), "ordivon.runtime.artifact"),
        (("resource", "properties", "identityContract"), "old-contract"),
        (("resource", "properties", "ownerId"), "runtime.windows"),
        (("resource", "properties", "nodeId"), "windows-pg"),
        (("resource", "properties", "requestSha256"), "c" * 64),
        (("resource", "id"), "runtime-release:v1:" + "c" * 64),
        (("resource", "properties", "workspaceId"), "ws-modified"),
        (("resource", "properties", "commit"), "c" * 40),
        (("resource", "properties", "candidateManifestDigest"), "sha256:" + "c" * 64),
        (("resource", "properties", "expectedToolCount"), 25),
        (("resource", "properties", "expectedToolCount"), True),
        (("resource", "properties", "requestId"), "changed-release-id"),
        (("resource", "properties", "requestId"), "nonascii-\u4e2d"),
    ],
)
def test_opa_rejects_resource_or_action_substitution(endpoint, selectors, replacement) -> None:
    client, path = endpoint
    set_grants(path, [grant()])
    q = copy.deepcopy(payload())
    cur = q
    for segment in selectors[:-1]:
        cur = cur[segment]
    cur[selectors[-1]] = replacement
    assert decide(client, q) is False


@pytest.mark.parametrize(
    "change",
    [
        {"requestId": "other-release-2"},
        {"workspaceId": "ws-other-r2"},
        {"commit": "c" * 40},
        {"candidateManifestDigest": "sha256:" + "c" * 64},
        {"expectedToolCount": 27},
    ],
)
def test_recomputed_identity_can_vary_but_old_digest_cannot_be_reused(endpoint, change) -> None:
    client, path = endpoint
    set_grants(path, [grant()])
    signed = target(**change)
    assert decide(client, payload(signed)) is True
    tampered = copy.deepcopy(signed)
    tampered["properties"]["requestSha256"] = target()["properties"]["requestSha256"]
    assert decide(client, payload(tampered)) is False


def test_untrusted_payload_cannot_create_operator_grant(endpoint) -> None:
    client, _ = endpoint
    forged = payload()
    forged["authorization"] = {"gateway_runtime_release_grants": [grant()]}
    forged["resource"]["properties"]["operatorGrant"] = grant()
    assert decide(client, forged) is False


def test_authenticated_pdp_bearer_alone_does_not_bypass_operator_grant(endpoint) -> None:
    client, path = endpoint
    set_grants(path, [grant()])
    response = client.post(
        "/access/v1/evaluation",
        json=payload(),
        headers={
            "Authorization": "Bearer invalid-workload-token",
            "X-Request-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401


def test_rejects_extra_resource_fields_even_with_valid_operator_grant(endpoint) -> None:
    client, path = endpoint
    set_grants(path, [grant()])
    extra = payload()
    extra["resource"]["properties"]["ignoredOperatorGrant"] = grant()
    assert decide(client, extra) is False
