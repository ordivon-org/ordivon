"""Real OPA + real AuthZEN HTTP: operator-provisioned Principal-to-Actor grants.

This test config exists only in disposable pytest directories; it is never an
installed production Agent or delegation. Original Runtime Artifact grants must
remain compatible with the Security service's existing policy.
"""

from __future__ import annotations

import base64
import copy
import json
import secrets
import shutil
import time
import uuid
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from ordivon_security_gateway_authzen.server import make_app

ROOT = Path(__file__).resolve().parents[1]
OPA = shutil.which("opa")
pytestmark = pytest.mark.skipif(OPA is None, reason="requires native OPA")


def policy_grant() -> dict:
    now = int(time.time())
    return {
        "active": True,
        "principalId": "principal:local-service:harness",
        "issuer": "ordivon-local-service",
        "actorRef": "actor:project:delegate",
        "notBeforeEpochSeconds": now - 30,
        "expiresAtEpochSeconds": now + 3600,
        "allowedTools": [
            "work.create",
            "work.engagement.advance",
            "work.engagement.list",
            "message.post",
        ],
        "allowedActions": ["submit", "review"],
        "exactRefs": ["work:project:one", "topic:project:one"],
        "namespacePrefixes": ["work:project:"],
    }


def grant_data(grants: list[dict]) -> dict:
    return {
        "ordivon": {
            "security": {
                "gateway_artifact_config": {"cf_issuer": "https://example-issuer.test"},
                "gateway_host_actor_grants": grants,
            }
        }
    }


@pytest.fixture
def policy_endpoint(tmp_path: Path):
    token_path = tmp_path / "pdp-token"
    token = secrets.token_hex(32)
    token_path.write_text(token)
    token_path.chmod(0o600)
    policy_path = tmp_path / "trusted-policy-data.json"
    policy_path.write_text(json.dumps(grant_data([policy_grant()])))
    policy_path.chmod(0o600)
    with TestClient(
        make_app(
            token_path=str(token_path),
            policy=str(ROOT / "policies" / "gateway_artifact.rego"),
            policy_data=str(policy_path),
            opa=str(OPA),
        )
    ) as client:
        yield client, token, policy_path


def enc(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def base_payload(*, capability: str, tool: str, resource: dict) -> dict:
    return {
        "subject": {
            "type": "user",
            "id": "principal:local-service:harness",
            "properties": {"issuer": "ordivon-local-service"},
        },
        "action": {"name": capability, "properties": {"gatewayTool": tool}},
        "resource": resource,
    }


def legacy_payload(*, tool: str = "work.create", ref: str = "work:project:one") -> dict:
    props = {
        "identityContract": "ordivon.host-legacy-write-resource.v1",
        "toolName": tool,
        "requestSha256": "f" * 64,
        "claimedActorRef": "actor:project:delegate",
        "workRef": ref if tool in {"work.create", "work.snapshot.commit"} else None,
        "topicRef": ref if tool == "message.post" else None,
    }
    return base_payload(
        capability="host.legacy-write",
        tool=tool,
        resource={
            "type": "ordivon.host.legacy-write-request",
            "id": f"host-legacy-write:v1:{enc(tool)}." + "f" * 64,
            "properties": props,
        },
    )


def engagement_payload(
    *,
    action: str = "submit",
    work: str = "work:project:one",
    actor: str = "actor:project:delegate",
) -> dict:
    return base_payload(
        capability="host.work.engagement.advance",
        tool="work.engagement.advance",
        resource={
            "type": "ordivon.host.work-engagement",
            "id": "host-engagement:v1:" + enc(work),
            "properties": {
                "identityContract": "ordivon.host-engagement-request-resource.v1",
                "workRef": work,
                "claimedActorRef": actor,
                "expectedRevision": 2,
                "actionType": action,
                "requestedConsumerActorRef": None,
                "reviewDecision": "accepted" if action == "review" else None,
            },
        },
    )


def inbox_payload(
    *, assignee: str | None = None, consumer: str | None = "actor:project:delegate"
) -> dict:
    return base_payload(
        capability="host.work.engagement.list",
        tool="work.engagement.list",
        resource={
            "type": "ordivon.host.work-engagement-inbox",
            "id": "host-engagement-inbox:v1:" + enc(assignee or "*") + "." + enc(consumer or "*"),
            "properties": {
                "identityContract": "ordivon.host-engagement-request-resource.v1",
                "requestedAssigneeActorRef": assignee,
                "requestedConsumerActorRef": consumer,
                "requestedPhase": "submitted",
            },
        },
    )


def evaluate(endpoint, payload: dict) -> bool:
    client, token, _ = endpoint
    request_id = str(uuid.uuid4())
    response = client.post(
        "/access/v1/evaluation",
        json=payload,
        headers={
            "Authorization": "Bearer " + token,
            "X-Request-ID": request_id,
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["x-request-id"] == request_id
    assert response.json() in ({"decision": True}, {"decision": False})
    return response.json()["decision"]


def test_real_opa_authzen_operator_grant_allows_legitimate_host_work(policy_endpoint) -> None:
    for request in (
        legacy_payload(),
        legacy_payload(ref="work:project:two"),
        legacy_payload(tool="message.post", ref="topic:project:one"),
        engagement_payload(action="submit"),
        engagement_payload(action="review"),
        inbox_payload(),
        inbox_payload(consumer=None, assignee="actor:project:delegate"),
    ):
        assert evaluate(policy_endpoint, request) is True


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p["subject"].update(id="principal:other"),
        lambda p: p["subject"]["properties"].update(issuer="wrong-issuer"),
        lambda p: p["resource"]["properties"].update(claimedActorRef="actor:another"),
        lambda p: p["resource"]["properties"].update(workRef="work:other:outside"),
        lambda p: p["action"].update(name="not-host-capability"),
        lambda p: p["action"]["properties"].update(gatewayTool="topic.state.set"),
        lambda p: p["resource"].update(type="ordivon.runtime.artifact"),
        lambda p: p["resource"]["properties"].update(identityContract="forged"),
    ],
)
def test_opa_rejects_wrong_principal_actor_resource_tool_and_contract(
    policy_endpoint, mutation
) -> None:
    req = legacy_payload()
    mutation(req)
    assert evaluate(policy_endpoint, req) is False


@pytest.mark.parametrize(
    "action,expected",
    [("submit", True), ("review", True), ("offer", False), ("cancel", False)],
)
def test_opa_limits_versioned_work_actions(policy_endpoint, action: str, expected: bool) -> None:
    assert evaluate(policy_endpoint, engagement_payload(action=action)) is expected


@pytest.mark.parametrize(
    "assignee,consumer,expected",
    [
        (None, None, False),
        ("actor:other", None, False),
        (None, "actor:other", False),
        ("actor:project:delegate", "actor:other", False),
        ("actor:project:delegate", "actor:project:delegate", True),
    ],
)
def test_opa_does_not_disclose_global_or_other_actor_inbox(
    policy_endpoint, assignee, consumer, expected
) -> None:
    assert (
        evaluate(policy_endpoint, inbox_payload(assignee=assignee, consumer=consumer)) is expected
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda g: g.update(active=False),
        lambda g: g.update(expiresAtEpochSeconds=int(time.time()) - 1),
        lambda g: g.update(notBeforeEpochSeconds=int(time.time()) + 3600),
        lambda g: g.update(actorRef="actor:other"),
        lambda g: g.update(allowedTools=["message.post"]),
        lambda g: g.update(namespacePrefixes=["work:other:"]),
        lambda g: g.update(exactRefs=["work:other:one"], namespacePrefixes=[]),
    ],
)
def test_operator_data_controls_principal_grant_lifetime_and_scope(policy_endpoint, change) -> None:
    client, token, path = policy_endpoint
    del client, token
    grant = policy_grant()
    # Exact scope to test requires namespace when ref is work:project:two.
    change(grant)
    path.write_text(json.dumps(grant_data([grant])))
    assert evaluate(policy_endpoint, legacy_payload(ref="work:project:two")) is False


def test_no_grant_and_tool_injected_grant_never_create_authority(policy_endpoint) -> None:
    _, _, path = policy_endpoint
    path.write_text(json.dumps(grant_data([])))
    req = legacy_payload()
    req["grant"] = policy_grant()
    req["resource"]["properties"]["grant"] = policy_grant()
    assert evaluate(policy_endpoint, req) is False


def test_existing_artifact_policy_keeps_its_bounded_runtime_read(policy_endpoint) -> None:
    ref = "ordivon-exec:v1:runtime.linux:job-test-0123"
    art = "attempt-0.stdout"
    req = base_payload(
        capability="artifact.runtime",
        tool="artifact.read",
        resource={
            "type": "ordivon.runtime.artifact",
            "id": "runtime-artifact:v1:" + enc(ref) + "." + enc(art),
            "properties": {
                "identityContract": "ordivon.runtime-artifact-resource-key.v1",
                "operationRef": ref,
                "ownerId": "runtime.linux",
                "jobId": "job-test-0123",
                "artifactId": art,
            },
        },
    )
    assert evaluate(policy_endpoint, req) is True


def test_real_http_invalid_security_credential_fails_before_opa(policy_endpoint) -> None:
    client, _, _ = policy_endpoint
    result = client.post(
        "/access/v1/evaluation",
        json=engagement_payload(),
        headers={
            "Authorization": "Bearer invalid",
            "X-Request-ID": str(uuid.uuid4()),
        },
    )
    assert result.status_code == 401


def test_real_host_relation_and_subscription_wire_scopes_not_ignored_fields(
    policy_endpoint,
) -> None:
    """Policy keys must be the fields that original Host truly persists."""
    _, _, path = policy_endpoint
    grant = policy_grant()
    grant["allowedTools"] += [
        "subscription.follow",
        "subscription.unfollow",
        "message.relation.add",
    ]
    grant["exactRefs"] += ["topic:project:one", "message:project:source"]
    grant["namespacePrefixes"] += ["message:project:"]
    path.write_text(json.dumps(grant_data([grant])))

    follow = legacy_payload(tool="subscription.follow")
    follow["resource"]["properties"].update(
        targetRef="topic:project:one",
        targetKind="topic",
        topicRef=None,
    )
    assert evaluate(policy_endpoint, follow) is True
    wrong_subscription = copy.deepcopy(follow)
    wrong_subscription["resource"]["properties"]["targetRef"] = "topic:foreign:outside"
    assert evaluate(policy_endpoint, wrong_subscription) is False

    relation = legacy_payload(tool="message.relation.add")
    relation["resource"]["properties"].update(
        sourceMessageRef="message:project:source",
        targetRef="message:project:target",
        messageRef=None,
    )
    assert evaluate(policy_endpoint, relation) is True
    wrong_relation = copy.deepcopy(relation)
    wrong_relation["resource"]["properties"]["targetRef"] = "message:foreign:outside"
    assert evaluate(policy_endpoint, wrong_relation) is False
    wrong_relation = copy.deepcopy(relation)
    wrong_relation["resource"]["properties"]["sourceMessageRef"] = "message:foreign:outside"
    assert evaluate(policy_endpoint, wrong_relation) is False
