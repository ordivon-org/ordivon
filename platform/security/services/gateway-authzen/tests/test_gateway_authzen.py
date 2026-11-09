"""Real OPA plus AuthZEN HTTP evaluations including adversarial requests."""

from __future__ import annotations

import base64
import json
import shutil
import uuid
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from ordivon_security_gateway_authzen.server import make_app

ROOT = Path(__file__).resolve().parents[1]
OPA = shutil.which("opa")
pytestmark = pytest.mark.skipif(OPA is None, reason="requires OPA policy engine")


def _resource(
    *, owner: str = "runtime.linux", job: str = "job-test-0123", artifact: str = "attempt-0.stdout"
) -> dict:
    ref = f"ordivon-exec:v1:{owner}:{job}"

    def enc(value: str) -> str:
        return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")

    return {
        "type": "ordivon.runtime.artifact",
        "id": f"runtime-artifact:v1:{enc(ref)}.{enc(artifact)}",
        "properties": {
            "identityContract": "ordivon.runtime-artifact-resource-key.v1",
            "operationRef": ref,
            "ownerId": owner,
            "jobId": job,
            "artifactId": artifact,
        },
    }


def _payload(
    *,
    principal: str = "principal:local-service:harness",
    issuer: str = "ordivon-local-service",
    resource: dict | None = None,
) -> dict:
    return {
        "subject": {"type": "user", "id": principal, "properties": {"issuer": issuer}},
        "action": {"name": "artifact.runtime", "properties": {"gatewayTool": "artifact.read"}},
        "resource": resource if resource is not None else _resource(),
    }


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    token_file = tmp_path / "token"
    token_file.write_text("fixture-secret-token-a01b02c03d04e05f06g07h08", encoding="utf-8")
    policy_data = tmp_path / "issuer.json"
    policy_data.write_text(
        json.dumps(
            {
                "ordivon": {
                    "security": {
                        "gateway_artifact_config": {"cf_issuer": "https://real-issuer.example.test"}
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return TestClient(
        make_app(
            token_path=str(token_file),
            policy=str(ROOT / "policies" / "gateway_artifact.rego"),
            policy_data=str(policy_data),
            opa=str(OPA),
        )
    )


def _request(
    client: TestClient,
    payload: object,
    *,
    token: str = "fixture-secret-token-a01b02c03d04e05f06g07h08",
):
    request_id = str(uuid.uuid4())
    result = client.post(
        "/access/v1/evaluation",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "X-Request-ID": request_id},
    )
    return result, request_id


def test_real_opa_authzen_allows_only_bound_artifact_principal(client: TestClient):
    r, req = _request(client, _payload())
    assert r.status_code == 200 and r.json() == {"decision": True}
    assert r.headers["x-request-id"] == req
    cf_principal = "principal:cf-access:" + ("a" * 64)
    r, _ = _request(
        client, _payload(principal=cf_principal, issuer="https://real-issuer.example.test")
    )
    assert r.status_code == 200 and r.json() == {"decision": True}


@pytest.mark.parametrize(
    "mutator",
    [
        lambda p: p["subject"].update(id="attacker"),
        lambda p: p["subject"].update(id="principal:cf-access:" + "b" * 64),
        lambda p: p["action"].update(name="finance.trade"),
        lambda p: p["action"]["properties"].update(gatewayTool="job.cancel"),
        lambda p: p["resource"]["properties"].update(ownerId="host"),
        lambda p: p["resource"]["properties"].update(artifactId="another-stdout"),
        lambda p: p["resource"].update(id="runtime-artifact:v1:forged"),
        lambda p: p["resource"]["properties"].update(jobId="job-wrong"),
        lambda p: p["resource"]["properties"].update(identityContract="untrusted"),
    ],
)
def test_real_opa_deny_malformed_or_untrusted_binding(client: TestClient, mutator):
    p = _payload()
    mutator(p)
    r, _ = _request(client, p)
    assert r.status_code == 200 and r.json() == {"decision": False}


def test_real_opa_denies_nonmatching_cf_issuer(client: TestClient):
    p = _payload(principal="principal:cf-access:" + ("b" * 64), issuer="https://imposter.example")
    r, _ = _request(client, p)
    assert r.status_code == 200 and r.json() == {"decision": False}


def test_endpoint_rejects_bad_workload_identity(client: TestClient):
    r, _ = _request(client, _payload(), token="invalid")
    assert r.status_code == 401


def test_endpoint_rejects_missing_correlation(client: TestClient):
    r = client.post(
        "/access/v1/evaluation",
        json=_payload(),
        headers={"Authorization": "Bearer fixture-secret-token-a01b02c03d04e05f06g07h08"},
    )
    assert r.status_code == 400


def test_health_reports_narrow_security_owner(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["policyEngine"] == "opa"
