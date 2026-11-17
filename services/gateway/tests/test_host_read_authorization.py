from __future__ import annotations

import asyncio
import importlib.util
import json
import secrets
import shutil
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from starlette.testclient import TestClient

from ordivon_gateway.authorization_targets import (
    _HOST_READ_ONLY_TOOLS,
    CapabilityAuthorizationTargetError,
    resolve_authorization_target,
)
from ordivon_gateway.authzen_authorizer import AuthZenPrincipalAuthorizer
from ordivon_gateway.capability_authz import GatewayCapabilityAuthorizationMiddleware

# These are the existing Gateway Host read routes, not an extra API surface.
READ_REQUESTS = {
    "host.status": {"detail": "history"},
    "work.get": {"workRef": "work:demo:one", "revision": 3},
    "work.list": {"state": "open", "limit": 10},
    "space.get": {"spaceRef": "space:demo:one"},
    "space.list": {"actorRef": "actor:demo:one", "limit": 10},
    "space.participation.list": {"spaceRef": "space:demo:one"},
    "space.subject.list": {"spaceRef": "space:demo:one"},
    "topic.cursor.get": {"topicRef": "topic:demo:one", "actorRef": "actor:demo:one"},
    "topic.list": {"spaceRef": "space:demo:one"},
    "topic.resume": {"topicRef": "topic:demo:one", "afterSequence": 5},
    "message.get": {"messageRef": "message:demo:one", "expectedDigest": "sha256:" + "a" * 64},
    "message.search": {"spaceRef": "space:demo:one", "query": "hello"},
    "message.relation.list": {"messageRef": "message:demo:one"},
    "subscription.list": {"actorRef": "actor:demo:one"},
    "attention.get": {"actorRef": "actor:demo:one"},
    "attention.delta": {"actorRef": "actor:demo:one", "afterSequence": 10},
    "attention.reentry": {"actorRef": "actor:demo:one", "afterSequence": 10},
}
VERIFIED = {
    "ordivon_access_principal": "principal:local-service:harness",
    "ordivon_access_issuer": "ordivon-local-service",
}


def _ctx(tool: str, arguments: dict[str, Any]):
    return SimpleNamespace(
        method="tools/call",
        params={"name": tool, "arguments": arguments},
        request=SimpleNamespace(scope={"state": VERIFIED}),
    )


def _decision(resource: dict[str, Any], outcome: str):
    allowed = outcome == "ALLOW"
    return {
        "schemaVersion": 3,
        "kind": "ordivon.security.gateway-capability-authz",
        "principalId": VERIFIED["ordivon_access_principal"],
        "issuer": VERIFIED["ordivon_access_issuer"],
        "requestedCapability": "host.legacy-read",
        "requestedResource": resource,
        "qualificationTarget": True,
        "authorizationProfile": "interactive-principal-authzen",
        "outcome": outcome,
        "reason": "test-PDP",
        "authorizationEvidence": {
            "standard": "openid-authzen-authorization-api-1.0",
            "requestId": "test-request",
            "responseRequestId": "test-request",
            "decision": allowed,
        },
        "authorityProjection": None,
        "effectAdmission": None,
    }


class FixedAuthorizer:
    def __init__(self, decision):
        self.decision = decision
        self.calls: list[dict[str, Any]] = []

    async def authorize(self, **kwargs):
        self.calls.append(kwargs)
        return self.decision


@pytest.mark.parametrize("tool", sorted(READ_REQUESTS))
def test_every_host_read_has_an_authzen_object_target(tool: str) -> None:
    assert set(READ_REQUESTS) == _HOST_READ_ONLY_TOOLS
    target = resolve_authorization_target(tool, READ_REQUESTS[tool])
    assert target is not None
    assert target.capability == "host.legacy-read"
    resource = target.authzen_resource()
    assert resource["type"] == "ordivon.host.legacy-read-request"
    assert resource["properties"]["toolName"] == tool


@pytest.mark.parametrize("tool", sorted(READ_REQUESTS))
def test_verified_gateway_host_reads_deny_without_security_pdp(tool: str) -> None:
    reached: list[str] = []

    async def owner(_ctx):
        reached.append(tool)
        return {"structuredContent": {"ok": True}}

    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(None)(_ctx(tool, READ_REQUESTS[tool]), owner)
    )
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_UNAVAILABLE"
    assert reached == []


def test_host_read_exact_object_filter_and_requested_revision_are_both_bound() -> None:
    one = resolve_authorization_target("work.get", {"workRef": "work:demo:one", "revision": 2})
    other = resolve_authorization_target("work.get", {"workRef": "work:demo:other", "revision": 2})
    newer = resolve_authorization_target("work.get", {"workRef": "work:demo:one", "revision": 3})
    spoof = resolve_authorization_target(
        "work.get",
        {"workRef": "work:demo:one", "revision": 2, "actorRef": "actor:spoof"},
    )
    assert all((one, other, newer, spoof))
    assert len({item.resource_id for item in (one, other, newer, spoof)}) == 4
    selector = one.authzen_resource()["properties"]["requestedSelectors"]
    assert selector == {"workRef": "work:demo:one"}
    assert spoof.authzen_resource()["properties"]["requestedSelectors"] == selector
    assert one.authzen_resource()["properties"]["unscoped"] is False


def test_unfiltered_list_is_an_explicitly_global_read_target() -> None:
    target = resolve_authorization_target("work.list", {"limit": 20})
    assert target is not None
    assert target.authzen_resource()["properties"]["unscoped"] is True
    assert target.authzen_resource()["properties"]["requestedSelectors"] == {}
    assert resolve_authorization_target("work.get", {}) is not None


@pytest.mark.parametrize(
    "invalid",
    [{"workRef": {"forged": "work:demo:one"}}, {"workRef": "invalid"}],
)
def test_invalid_object_selector_is_rejected_before_security_pdp(invalid) -> None:
    with pytest.raises(CapabilityAuthorizationTargetError, match="qualified"):
        resolve_authorization_target("work.get", invalid)


def test_real_authzen_positive_and_negative_object_read_consumer() -> None:
    request = READ_REQUESTS["topic.resume"]
    target = resolve_authorization_target("topic.resume", request)
    assert target is not None
    resource = target.authzen_resource()

    async def run(decision, arguments=request):
        entered: list[str] = []
        authorizer = FixedAuthorizer(decision)

        async def owner(_ctx):
            entered.append("owner")
            return {"structuredContent": {"ok": True}}

        observed = await GatewayCapabilityAuthorizationMiddleware(authorizer)(
            _ctx("topic.resume", arguments), owner
        )
        return observed, entered, authorizer.calls

    allow, entered, calls = asyncio.run(run(_decision(resource, "ALLOW")))
    assert allow["structuredContent"]["ok"] is True
    assert entered == ["owner"]
    assert calls[0]["principal_id"] == VERIFIED["ordivon_access_principal"]
    assert calls[0]["requested_resource"] == resource

    deny, entered, _ = asyncio.run(run(_decision(resource, "DENY")))
    assert deny.is_error is True
    assert deny.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_DENIED"
    assert entered == []

    changed = {**request, "afterSequence": 6}
    mismatch, entered, _ = asyncio.run(run(_decision(resource, "ALLOW"), arguments=changed))
    assert mismatch.is_error is True
    assert mismatch.structured_content["error"]["code"] == ("CAPABILITY_AUTHZ_BINDING_MISMATCH")
    assert entered == []


def test_exact_message_digest_is_part_of_host_read_pdp_target() -> None:
    one = resolve_authorization_target(
        "message.get", {"messageRef": "message:demo:one", "expectedDigest": "sha256:" + "a" * 64}
    )
    changed_digest = resolve_authorization_target(
        "message.get", {"messageRef": "message:demo:one", "expectedDigest": "sha256:" + "b" * 64}
    )
    other_message = resolve_authorization_target(
        "message.get", {"messageRef": "message:demo:two", "expectedDigest": "sha256:" + "a" * 64}
    )
    assert all((one, changed_digest, other_message))
    assert len({one.resource_id, changed_digest.resource_id, other_message.resource_id}) == 3
    assert one.authzen_resource()["properties"]["requestedSelectors"] == {
        "messageRef": "message:demo:one"
    }
    assert one.authzen_resource()["properties"]["unscoped"] is False


@pytest.mark.parametrize(
    "invalid", [{"messageRef": {"forged": "message:demo:one"}}, {"messageRef": "no-colon"}]
)
def test_exact_message_read_rejects_invalid_selector_before_pdp(invalid) -> None:
    with pytest.raises(CapabilityAuthorizationTargetError):
        resolve_authorization_target("message.get", invalid)


def test_real_opa_gateway_pep_consumer_rejects_cross_principal_and_revocation(
    tmp_path: Path,
) -> None:
    """Refine the current Host PEP contract against the existing Security OPA implementation.

    This is an isolated test-owned policy and token, not a production Principal
    or an authenticated Cloudflare ingress test. The guarded Owner callback
    proves that a PDP DENY never dispatches an Owner operation.
    """
    opa = shutil.which("opa")
    if opa is None:
        pytest.skip("requires existing native OPA tool")

    root = Path(__file__).resolve().parents[3]
    policy_root = root / "platform/security/services/gateway-authzen"
    server_file = policy_root / "src/ordivon_security_gateway_authzen/server.py"
    policy = policy_root / "policies/gateway_artifact.rego"
    assert server_file.is_file() and policy.is_file()
    spec = importlib.util.spec_from_file_location(
        "ordivon_security_gateway_authzen_test_adapter", server_file
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    token = secrets.token_hex(32)
    token_path = tmp_path / "pdp-token"
    token_path.write_text(token, encoding="utf-8")
    token_path.chmod(0o600)
    policy_data = tmp_path / "trusted-policy-data.json"

    now = int(time.time())
    grant = {
        "active": True,
        "principalId": VERIFIED["ordivon_access_principal"],
        "issuer": VERIFIED["ordivon_access_issuer"],
        "actorRef": "actor:project:delegate",
        "notBeforeEpochSeconds": now - 60,
        "expiresAtEpochSeconds": now + 1800,
        "allowedTools": ["work.get"],
        "allowedActions": [],
        "exactRefs": ["work:project:one"],
        "namespacePrefixes": [],
    }

    def save_policy() -> None:
        policy_data.write_text(
            json.dumps(
                {
                    "ordivon": {
                        "security": {
                            "gateway_artifact_config": {"cf_issuer": "https://test-issuer.invalid"},
                            "gateway_host_actor_grants": [grant],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        policy_data.chmod(0o600)

    save_policy()
    app = module.make_app(
        token_path=str(token_path),
        policy=str(policy),
        policy_data=str(policy_data),
        opa=opa,
    )
    with TestClient(app) as pdp:

        class TestOwnedPdpSession:
            def post(
                self,
                url: str,
                *,
                json: dict[str, Any],
                headers: dict[str, str],
                timeout: float,
                allow_redirects: bool,
            ) -> Any:
                assert url == "https://127.0.0.1:18787/access/v1/evaluation"
                assert timeout > 0 and allow_redirects is False
                return pdp.post("/access/v1/evaluation", json=json, headers=headers)

        middleware = GatewayCapabilityAuthorizationMiddleware(
            AuthZenPrincipalAuthorizer(
                "https://127.0.0.1:18787/access/v1/evaluation",
                bearer_token_provider=lambda: token,
                session=TestOwnedPdpSession(),  # type: ignore[arg-type]
            )
        )

        async def call(work_ref: str, principal: str, issuer: str, *, permitted: bool) -> None:
            owner_calls: list[str] = []

            async def owner(_ctx: Any) -> dict[str, Any]:
                owner_calls.append("actual-owner")
                return {"structuredContent": {"source": "isolated-test-only"}}

            ctx = SimpleNamespace(
                method="tools/call",
                params={"name": "work.get", "arguments": {"workRef": work_ref}},
                request=SimpleNamespace(
                    scope={
                        "state": {
                            "ordivon_access_principal": principal,
                            "ordivon_access_issuer": issuer,
                        }
                    }
                ),
            )
            result = await middleware(ctx, owner)
            if permitted:
                assert not getattr(result, "is_error", False), (
                    f"test-owned PDP unexpectedly rejected ALLOW: {getattr(result, 'structured_content', None)!r}"
                )
                content = (
                    result["structuredContent"]
                    if isinstance(result, dict)
                    else result.structured_content
                )
                assert content["source"] == "isolated-test-only"
                assert owner_calls == ["actual-owner"]
            else:
                assert result.is_error is True
                assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_DENIED"
                assert owner_calls == []

        async def scenarios() -> None:
            principal = VERIFIED["ordivon_access_principal"]
            issuer = VERIFIED["ordivon_access_issuer"]
            await call("work:project:one", principal, issuer, permitted=True)
            await call("work:other:outside", principal, issuer, permitted=False)
            await call("work:project:one", "principal:other", issuer, permitted=False)
            await call("work:project:one", principal, "wrong-issuer", permitted=False)

            grant["active"] = False
            save_policy()
            await call("work:project:one", principal, issuer, permitted=False)

        asyncio.run(scenarios())
