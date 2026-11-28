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


def test_systemd_uses_native_credentials_for_private_config_and_tls_cert() -> None:
    unit = (
        Path(__file__).resolve().parents[1] / "systemd" / "ordivon-security-gateway-authzen.service"
    ).read_text()
    assert (
        "LoadCredential=trusted-issuer:/etc/ordivon/security/gateway-authzen/trusted-issuer.json"
        in unit
    )
    assert "LoadCredential=tls-cert:/etc/ordivon/security/gateway-authzen/server.pem" in unit
    assert "ORDIVON_SECURITY_AUTHZEN_POLICY_DATA_FILE=%d/trusted-issuer" in unit
    assert "--ssl-certfile %d/tls-cert" in unit


def _raw_request(client: TestClient, raw: bytes, **extra_headers: str):
    return client.post(
        "/access/v1/evaluation",
        content=raw,
        headers={
            "Authorization": "Bearer fixture-secret-token-a01b02c03d04e05f06g07h08",
            "X-Request-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
            **extra_headers,
        },
    )


def test_wire_rejects_ambiguous_duplicate_fields(client: TestClient):
    valid = json.dumps(_payload())
    nested = valid.replace('"type": "user"', '"type": "unknown", "type": "user"', 1)
    top = '{"action":{"name":"unknown"},' + valid[1:]
    for raw in (nested, top):
        response = _raw_request(client, raw.encode())
        assert response.status_code == 400
        assert "decision" not in response.json()


@pytest.mark.parametrize("length", ["invalid", "-1", "+1"])
def test_wire_rejects_invalid_declared_length(client: TestClient, length: str):
    response = _raw_request(client, json.dumps(_payload()).encode(), **{"Content-Length": length})
    assert response.status_code == 400
    assert "decision" not in response.json()


def test_wire_rejects_non_json_numeric_constants(client: TestClient):
    raw = json.dumps(_payload())[:-1] + ', "context": {"value": NaN}}'
    response = _raw_request(client, raw.encode())
    assert response.status_code == 400
    assert "decision" not in response.json()


def test_wire_length_mismatch_and_overflow(client: TestClient):
    raw = json.dumps(_payload()).encode()
    for value in ("1", str(len(raw) + 1)):
        assert _raw_request(client, raw, **{"Content-Length": value}).status_code == 400
    assert _raw_request(client, raw, **{"Content-Length": "9" * 5000}).status_code == 413


def test_wire_exact_size_limit_and_valid_allow(client: TestClient):
    raw = json.dumps(_payload()).encode()
    valid = raw + b" " * (8192 - len(raw))
    r = _raw_request(client, valid)
    assert r.status_code == 200 and r.json() == {"decision": True}
    assert _raw_request(client, valid + b" ").status_code == 413


def test_wire_rejects_overflow_and_deeply_nested_input(client: TestClient):
    raw = json.dumps(_payload())[:-1] + ', "context": {"value": 1e999}}'
    assert _raw_request(client, raw.encode()).status_code == 400
    assert _raw_request(client, b"[" * 2000 + b"]" * 2000).status_code == 400


def test_streaming_body_rejected_before_reading_remaining_chunks(client: TestClient):
    import asyncio

    calls = 0
    sent = []

    async def receive():
        nonlocal calls
        calls += 1
        if calls > 2:
            raise AssertionError("oversize request continued reading")
        return {"type": "http.request", "body": b"x" * 4097, "more_body": True}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/access/v1/evaluation",
        "root_path": "",
        "query_string": b"",
        "headers": [
            (b"authorization", b"Bearer fixture-secret-token-a01b02c03d04e05f06g07h08"),
            (b"x-request-id", str(uuid.uuid4()).encode()),
            (b"content-type", b"application/json"),
        ],
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
    }
    asyncio.run(client.app(scope, receive, send))
    assert calls == 2
    assert sent[0]["status"] == 413


@pytest.mark.parametrize("encoding", ["utf-16", "utf-32"])
def test_wire_requires_utf8_json(client: TestClient, encoding: str):
    assert _raw_request(client, json.dumps(_payload()).encode(encoding)).status_code == 400


def test_wire_rejects_non_scalar_unicode(client: TestClient):
    raw = json.dumps(_payload())[:-1] + r', "context": {"value": "\ud800"}}'
    assert _raw_request(client, raw.encode()).status_code == 400


def test_invalid_representation_never_calls_policy(client: TestClient, monkeypatch):
    from ordivon_security_gateway_authzen import server

    def forbidden_call(*args, **kwargs):
        pytest.fail("unqualified representation reached the policy engine")

    monkeypatch.setattr(server, "_opa_decision", forbidden_call)
    invalid = [
        b'{"subject":{}, "subject":{}}',
        b'{"context":{"x":1,"x":2}}',
        b'{"context":{"x":NaN}}',
        b'{"context":{"x":1e999}}',
        b'{"context":{"x":"\\ud800"}}',
        b'{"context":{"x":"\xff"}}',
        b"[" * 2000 + b"]" * 2000,
        b" " * 8193,
    ]
    for raw in invalid:
        response = _raw_request(client, raw)
        assert response.status_code in (400, 413)
        assert "decision" not in response.json()
