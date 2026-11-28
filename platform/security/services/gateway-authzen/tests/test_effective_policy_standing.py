"""Exact decision evidence, not a grant inventory or deployment attestation."""

import hashlib
import json
import shutil
import uuid

import pytest
from starlette.testclient import TestClient

from ordivon_security_gateway_authzen.server import make_app

OPA = shutil.which("opa")
pytestmark = pytest.mark.skipif(OPA is None, reason="requires native OPA")
TOKEN = "isolated-test-token-not-a-production-secret-1234"
POLICY = """package ordivon.security.gateway_artifact
default allow := false
allow if {
    input.subject.id == data.fixture.allowed
}
"""


@pytest.fixture
def endpoint(tmp_path):
    policy, data, token = (tmp_path / name for name in ("policy.rego", "data.json", "token"))
    policy.write_text(POLICY, encoding="utf-8")
    data.write_text(json.dumps({"fixture": {"allowed": "fixture-actor"}}), encoding="utf-8")
    token.write_text(TOKEN, encoding="utf-8")
    with TestClient(
        make_app(token_path=str(token), policy=str(policy), policy_data=str(data), opa=str(OPA))
    ) as client:
        yield client, policy, data


def call(client, actor="fixture-actor", *, standing=True, token=TOKEN):
    request_id = str(uuid.uuid4())
    headers = {"Authorization": "Bearer " + token, "X-Request-ID": request_id}
    if standing:
        headers["X-Ordivon-Policy-Standing"] = "v1"
    payload = {"subject": {"id": actor}}
    response = client.post("/access/v1/evaluation", json=payload, headers=headers)
    return response, payload, request_id


def test_bound_allow_and_deny_without_exposing_data(endpoint):
    client, policy, data = endpoint
    first, payload, request_id = call(client)
    assert first.status_code == 200
    body = first.json()
    assert body["decision"] is True
    witness = body["context"]["ordivonPolicyStanding"]
    assert witness["standing"] == "OBSERVED_FOR_DECISION"
    assert witness["requestId"] == request_id == first.headers["x-request-id"]
    assert witness["policySha256"] == "sha256:" + hashlib.sha256(policy.read_bytes()).hexdigest()
    assert (
        witness["inputSha256"]
        == "sha256:"
        + hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()
    )
    second, _, _ = call(client, "foreign")
    assert second.json()["decision"] is False
    other = second.json()["context"]["ordivonPolicyStanding"]
    assert other["policyDataCommitment"] == witness["policyDataCommitment"]
    assert other["instanceId"] == witness["instanceId"]
    assert other["inputSha256"] != witness["inputSha256"]
    assert "fixture-actor" not in json.dumps(witness)
    assert (
        witness["policyDataCommitment"] != "sha256:" + hashlib.sha256(data.read_bytes()).hexdigest()
    )
    assert call(client, standing=False)[0].json() == {"decision": True}
    denied, _, _ = call(client, token="invalid")
    assert denied.status_code == 401 and "context" not in denied.json()


def test_data_change_is_observed_by_the_decision(endpoint):
    client, _, data = endpoint
    before, _, _ = call(client)
    data.write_text(json.dumps({"fixture": {"allowed": "different"}}), encoding="utf-8")
    after, _, _ = call(client)
    assert before.json()["decision"] is True and after.json()["decision"] is False
    left = before.json()["context"]["ordivonPolicyStanding"]
    right = after.json()["context"]["ordivonPolicyStanding"]
    assert left["policyDataCommitment"] != right["policyDataCommitment"]
    assert left["policySha256"] == right["policySha256"]
    data.unlink()
    unavailable, _, _ = call(client)
    assert unavailable.status_code == 503 and "context" not in unavailable.json()


def test_snapshot_identity_survives_source_replacement_during_native_eval(endpoint, monkeypatch):
    from ordivon_security_gateway_authzen import policy_evaluation

    client, policy, data = endpoint
    original_policy = policy.read_bytes()
    original_run = policy_evaluation.subprocess.run

    def replace_sources_before_opa(*args, **kwargs):
        policy.write_text(
            POLICY.replace("default allow := false", "default allow := true"), encoding="utf-8"
        )
        data.write_text(json.dumps({"fixture": {"allowed": "different"}}), encoding="utf-8")
        return original_run(*args, **kwargs)

    # A denied subject must remain denied despite source file replacement.
    with monkeypatch.context() as m:
        m.setattr(policy_evaluation.subprocess, "run", replace_sources_before_opa)
        response, _, _ = call(client, "foreign")
    witness = response.json()["context"]["ordivonPolicyStanding"]
    assert response.json()["decision"] is False
    assert witness["policySha256"] == "sha256:" + hashlib.sha256(original_policy).hexdigest()
    assert policy.read_bytes() != original_policy
    next_response, _, _ = call(client, "foreign")
    assert next_response.json()["decision"] is True
    next_witness = next_response.json()["context"]["ordivonPolicyStanding"]
    assert next_witness["policySha256"] != witness["policySha256"]
    assert next_witness["policyDataCommitment"] != witness["policyDataCommitment"]


def test_invalid_standing_version_rejected(endpoint):
    client, _, _ = endpoint
    response = client.post(
        "/access/v1/evaluation",
        json={"subject": {"id": "fixture-actor"}},
        headers={
            "Authorization": "Bearer " + TOKEN,
            "X-Request-ID": str(uuid.uuid4()),
            "X-Ordivon-Policy-Standing": "v2",
        },
    )
    assert response.status_code == 400 and "decision" not in response.json()


def test_distinct_instance_commitments_are_not_comparable(endpoint, tmp_path):
    client, policy, data = endpoint
    first = call(client)[0].json()["context"]["ordivonPolicyStanding"]
    with TestClient(
        make_app(
            token_path=str(tmp_path / "token"),
            policy=str(policy),
            policy_data=str(data),
            opa=str(OPA),
        )
    ) as fresh:
        second = call(fresh)[0].json()["context"]["ordivonPolicyStanding"]
    assert first["instanceId"] != second["instanceId"]
    assert first["policyDataCommitment"] != second["policyDataCommitment"]
    assert first["policySha256"] == second["policySha256"]


def test_declared_release_label_is_not_a_generic_path_claim(tmp_path):
    revision = "a" * 40
    release = tmp_path / "releases" / revision / "policies"
    release.mkdir(parents=True)
    policy = release / "gateway_artifact.rego"
    policy.write_text(POLICY, encoding="utf-8")
    data = tmp_path / "data.json"
    data.write_text(json.dumps({"fixture": {"allowed": "fixture-actor"}}))
    token = tmp_path / "token"
    token.write_text(TOKEN)
    current = tmp_path / "current"
    current.symlink_to(release.parent, target_is_directory=True)
    with TestClient(
        make_app(
            token_path=str(token),
            policy=str(current / "policies" / policy.name),
            policy_data=str(data),
            opa=str(OPA),
        )
    ) as client:
        result = call(client)[0].json()["context"]["ordivonPolicyStanding"]
    assert result["declaredReleaseRevision"] == revision
    assert result["policySha256"] == "sha256:" + hashlib.sha256(policy.read_bytes()).hexdigest()
