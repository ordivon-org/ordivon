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


# Host R18 read target is produced by the existing Gateway AuthZEN PEP, not by
# the caller. This independent Security fixture verifies the wire contract.
def read_payload(*, tool: str, selectors: dict | None = None, sha: str = "f" * 64) -> dict:
    selectors = selectors or {}
    return base_payload(
        capability="host.legacy-read",
        tool=tool,
        resource={
            "type": "ordivon.host.legacy-read-request",
            "id": f"host-legacy-read:v1:{enc(tool)}.{sha}",
            "properties": {
                "identityContract": "ordivon.host-legacy-read-resource.v1",
                "toolName": tool,
                "requestSha256": sha,
                "requestedSelectors": selectors,
                "unscoped": not selectors,
            },
        },
    )


def set_read_grant(policy_endpoint, *, global_reads: bool = False):
    _, _, path = policy_endpoint
    grant = policy_grant()
    grant["allowedTools"] += [
        "work.get",
        "work.list",
        "space.get",
        "space.list",
        "topic.resume",
        "topic.cursor.get",
        "message.search",
        "attention.reentry",
        "subscription.list",
    ]
    if global_reads:
        grant["allowUnscopedReads"] = True
    path.write_text(json.dumps(grant_data([grant])))
    return grant


@pytest.mark.parametrize(
    "tool,selectors",
    [
        ("work.get", {"workRef": "work:project:one"}),
        ("work.get", {"workRef": "work:project:two"}),
        ("topic.resume", {"topicRef": "topic:project:one"}),
        (
            "topic.cursor.get",
            {"topicRef": "topic:project:one", "actorRef": "actor:project:delegate"},
        ),
        ("message.search", {"topicRef": "topic:project:one"}),
        ("attention.reentry", {"actorRef": "actor:project:delegate"}),
        ("subscription.list", {"actorRef": "actor:project:delegate"}),
        ("space.list", {"actorRef": "actor:project:delegate"}),
    ],
)
def test_host_read_valid_principal_actor_and_scoped_resource_allow(
    policy_endpoint, tool, selectors
) -> None:
    set_read_grant(policy_endpoint)
    assert evaluate(policy_endpoint, read_payload(tool=tool, selectors=selectors)) is True


@pytest.mark.parametrize(
    "tool,selectors",
    [
        ("work.get", {"workRef": "work:outside:one"}),
        ("topic.resume", {"topicRef": "topic:outside:one"}),
        ("attention.reentry", {"actorRef": "actor:other:claim"}),
        (
            "topic.cursor.get",
            {"topicRef": "topic:outside:one", "actorRef": "actor:project:delegate"},
        ),
        ("message.search", {"topicRef": "topic:project:one", "spaceRef": "space:outside:one"}),
        ("work.get", {"actorRef": "actor:project:delegate"}),
        ("work.list", {}),
        ("message.search", {}),
    ],
)
def test_host_read_rejects_foreign_scope_actor_spoof_or_global_scan(
    policy_endpoint, tool, selectors
) -> None:
    set_read_grant(policy_endpoint)
    assert evaluate(policy_endpoint, read_payload(tool=tool, selectors=selectors)) is False


def test_host_global_read_requires_explicit_active_operator_grant(policy_endpoint) -> None:
    set_read_grant(policy_endpoint, global_reads=True)
    for tool in ("work.list", "message.search"):
        assert evaluate(policy_endpoint, read_payload(tool=tool)) is True
    _, _, path = policy_endpoint
    bad = policy_grant()
    bad["allowUnscopedReads"] = True
    bad["allowedTools"] += ["work.list"]
    bad["active"] = False
    path.write_text(json.dumps(grant_data([bad])))
    assert evaluate(policy_endpoint, read_payload(tool="work.list")) is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["resource"]["properties"].update(unscoped=True),
        lambda p: p["resource"]["properties"].update(requestSha256="not-sha"),
        lambda p: p["resource"].update(id="host-legacy-read:v1:wrong-tool.f"),
        lambda p: p["resource"]["properties"].update(
            requestedSelectors={"unknownRef": "work:project:one"}
        ),
        lambda p: p["action"]["properties"].update(gatewayTool="topic.resume"),
    ],
)
def test_host_read_forgeries_cannot_be_authorized(policy_endpoint, mutate) -> None:
    set_read_grant(policy_endpoint)
    payload = read_payload(tool="work.get", selectors={"workRef": "work:project:one"})
    mutate(payload)
    assert evaluate(policy_endpoint, payload) is False


@pytest.mark.parametrize(
    "tool,selectors",
    [
        ("host.status", {}),
        ("work.get", {"workRef": "work:project:one"}),
        ("work.list", {}),
        ("space.get", {"spaceRef": "space:project:one"}),
        ("space.list", {"actorRef": "actor:project:delegate"}),
        ("space.participation.list", {"spaceRef": "space:project:one"}),
        ("space.subject.list", {"spaceRef": "space:project:one"}),
        (
            "topic.cursor.get",
            {"topicRef": "topic:project:one", "actorRef": "actor:project:delegate"},
        ),
        ("topic.list", {"spaceRef": "space:project:one"}),
        ("topic.resume", {"topicRef": "topic:project:one"}),
        ("message.search", {"topicRef": "topic:project:one"}),
        ("message.relation.list", {"messageRef": "message:project:one"}),
        ("subscription.list", {"actorRef": "actor:project:delegate"}),
        ("attention.get", {"actorRef": "actor:project:delegate"}),
        ("attention.delta", {"actorRef": "actor:project:delegate"}),
        ("attention.reentry", {"actorRef": "actor:project:delegate"}),
    ],
)
def test_operator_grants_cover_entire_real_host_read_surface(policy_endpoint, tool, selectors):
    grant = set_read_grant(policy_endpoint, global_reads=True)
    _, _, path = policy_endpoint
    grant["allowedTools"].append(tool)
    grant["exactRefs"] += ["space:project:one", "message:project:one"]
    path.write_text(json.dumps(grant_data([grant])))
    assert evaluate(policy_endpoint, read_payload(tool=tool, selectors=selectors)) is True

    # Removing this one tool's authority must deny even a perfectly scoped read.
    grant["allowedTools"] = [name for name in grant["allowedTools"] if name != tool]
    path.write_text(json.dumps(grant_data([grant])))
    assert evaluate(policy_endpoint, read_payload(tool=tool, selectors=selectors)) is False


def provisioned_operator_grant() -> dict:
    """A named trusted Principal managing a bounded Agent namespace."""
    grant = policy_grant()
    grant.update(
        {
            "role": "operator",
            "delegatedActorPrefixes": ["agent:chatgpt:", "actor:agent:"],
            "allowedTools": grant["allowedTools"]
            + [
                "topic.resume",
                "host.status",
                "work.list",
                "attention.reentry",
                "subscription.list",
            ],
            "namespacePrefixes": grant["namespacePrefixes"]
            + ["topic:project:", "agent:chatgpt:", "actor:agent:"],
            "allowUnscopedReads": True,
        }
    )
    return grant


@pytest.mark.parametrize(
    "tool,actor,ref",
    [
        ("work.create", "agent:chatgpt:gpt6-one", "work:project:two"),
        ("message.post", "actor:agent:gpt6-other", "topic:project:one"),
        ("work.create", "actor:agent:gpt6-other", "work:project:one"),
    ],
)
def test_provisioned_operator_grant_accepts_multiple_agent_actors(
    policy_endpoint, tool, actor, ref
) -> None:
    _, _, path = policy_endpoint
    path.write_text(json.dumps(grant_data([provisioned_operator_grant()])))
    request = legacy_payload(tool=tool, ref=ref)
    request["resource"]["properties"]["claimedActorRef"] = actor
    assert evaluate(policy_endpoint, request) is True


def test_operator_can_read_agent_scoped_attention_and_engagement_without_global_inbox(
    policy_endpoint,
) -> None:
    _, _, path = policy_endpoint
    grant = provisioned_operator_grant()
    path.write_text(json.dumps(grant_data([grant])))
    assert evaluate(
        policy_endpoint,
        read_payload(tool="attention.reentry", selectors={"actorRef": "agent:chatgpt:gpt6-one"}),
    )
    assert evaluate(policy_endpoint, inbox_payload(consumer="actor:agent:gpt6-other"))
    assert evaluate(policy_endpoint, read_payload(tool="host.status"))
    grant["allowUnscopedReads"] = False
    path.write_text(json.dumps(grant_data([grant])))
    assert evaluate(policy_endpoint, read_payload(tool="host.status")) is False


@pytest.mark.parametrize(
    "mutate_grant,actor,ref",
    [
        (lambda g: g.pop("role"), "agent:chatgpt:gpt6-one", "work:project:two"),
        (lambda g: g.update(role="viewer"), "agent:chatgpt:gpt6-one", "work:project:two"),
        (
            lambda g: g.update(delegatedActorPrefixes=[]),
            "agent:chatgpt:gpt6-one",
            "work:project:two",
        ),
        (
            lambda g: g.update(delegatedActorPrefixes=["agent:chatgpt"]),
            "agent:chatgpt:gpt6-one",
            "work:project:two",
        ),
        (
            lambda g: g.update(delegatedActorPrefixes=[""]),
            "agent:chatgpt:gpt6-one",
            "work:project:two",
        ),
        (lambda g: g.update(active=False), "agent:chatgpt:gpt6-one", "work:project:two"),
        (
            lambda g: g.update(expiresAtEpochSeconds=int(time.time()) - 1),
            "agent:chatgpt:gpt6-one",
            "work:project:two",
        ),
        (lambda g: g.update(namespacePrefixes=[]), "agent:chatgpt:gpt6-one", "work:project:two"),
        (lambda g: None, "agent:unrelated:other", "work:project:two"),
        (lambda g: None, "agent:chatgptx:fake", "work:project:two"),
        (lambda g: None, "agent:chatgpt:gpt6-one", "work:foreign:secret"),
    ],
)
def test_operator_delegation_remains_bound_to_trusted_role_actor_tool_resource_and_time(
    policy_endpoint, mutate_grant, actor, ref
) -> None:
    _, _, path = policy_endpoint
    grant = provisioned_operator_grant()
    mutate_grant(grant)
    path.write_text(json.dumps(grant_data([grant])))
    request = legacy_payload(tool="work.create", ref=ref)
    request["resource"]["properties"]["claimedActorRef"] = actor
    assert evaluate(policy_endpoint, request) is False


def test_operator_claim_injected_into_mcp_request_does_not_upgrade_normal_grant(
    policy_endpoint,
) -> None:
    _, _, path = policy_endpoint
    path.write_text(json.dumps(grant_data([policy_grant()])))
    req = legacy_payload()
    req["resource"]["properties"]["claimedActorRef"] = "agent:chatgpt:gpt6-one"
    req["resource"]["properties"]["role"] = "operator"
    req["resource"]["properties"]["delegatedActorPrefixes"] = ["agent:chatgpt:"]
    assert evaluate(policy_endpoint, req) is False


def test_cf_access_operator_delegation_is_verified_issuer_and_exact_principal_bound(
    policy_endpoint,
) -> None:
    _, _, path = policy_endpoint
    grant = provisioned_operator_grant()
    principal = "principal:cf-access:" + ("b" * 64)
    issuer = "https://example-issuer.test"
    grant.update(principalId=principal, issuer=issuer)
    path.write_text(json.dumps(grant_data([grant])))
    request = legacy_payload(ref="work:project:two")
    request["subject"]["id"] = principal
    request["subject"]["properties"]["issuer"] = issuer
    request["resource"]["properties"]["claimedActorRef"] = "agent:chatgpt:gpt6-one"
    assert evaluate(policy_endpoint, request) is True
    request["subject"]["id"] = "principal:cf-access:" + ("c" * 64)
    assert evaluate(policy_endpoint, request) is False
    request["subject"]["id"] = principal
    request["subject"]["properties"]["issuer"] = "https://imposter.test"
    assert evaluate(policy_endpoint, request) is False
