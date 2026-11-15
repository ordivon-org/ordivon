"""Exact native Linux Runtime release forwarding, no generic execution fallback."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any

import pytest

from ordivon_gateway.capability_authz import (
    GatewayCapabilityAuthorizationMiddleware,
    resolve_authorization_target,
)
from ordivon_gateway.mcp_server import _verified_execution_request_id, build_server
from ordivon_gateway.service import GatewayError, GatewayService


class FakeOwner:
    def __init__(self, description: dict[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.description = description or {
            "node": {"nodeId": "linux-pg", "platform": "linux", "native": True},
            "structuredReleaseConfigured": True,
            "targets": [{"target": "local_linux", "configured": True, "available": True}],
        }
        self.observation = {
            "contract": "runtime_release_v1",
            "effectId": "effect-1",
            "clientRequestId": "qualified-r1",
            "jobId": "job-1",
            "workspaceId": "ws-1",
            "commit": "a" * 40,
            "candidateManifestDigest": "sha256:" + "b" * 64,
            "expectedToolCount": 26,
            "effectDisposition": "admitted",
            "effectTerminal": False,
            "receiptAvailable": False,
            "executionTerminal": False,
            "deliveryDisposition": "in_progress",
            "recoveryRequired": False,
            "semanticCompletionEvaluated": False,
        }
        self.fail_apply = False

    async def call_tool(self, owner_id: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((owner_id, tool, args))
        assert owner_id == "runtime.linux", "no Windows or synthetic release Owner"
        if tool == "runtime.describe":
            return deepcopy(self.description)
        if tool == "release.apply":
            if self.fail_apply:
                raise TimeoutError("Owner admission response lost after possible PG commit")
            return {
                "replayed": False,
                "release": {**self.observation, "clientRequestId": args["clientRequestId"]},
            }
        if tool == "release.get":
            return {**self.observation, "clientRequestId": args["clientRequestId"]}
        raise AssertionError(f"unexpected Owner tool: {tool}")


def _apply(svc: GatewayService, *, request_id: str = "qualified-r1"):
    return svc.runtime_release_apply(
        request_id=request_id,
        workspace_id="ws-1",
        commit="a" * 40,
        candidate_manifest_digest="sha256:" + "b" * 64,
        expected_tool_count=26,
    )


def test_release_reuses_native_owner_apply_and_no_generic_job() -> None:
    caller = FakeOwner()
    result = asyncio.run(_apply(GatewayService(caller)))
    assert result.replayed is False
    assert result.release.client_request_id == "qualified-r1"
    assert result.release.effect_disposition == "admitted"
    assert [(o, t) for o, t, _ in caller.calls] == [
        ("runtime.linux", "runtime.describe"),
        ("runtime.linux", "release.apply"),
    ]
    assert caller.calls[1][2] == {
        "schemaVersion": 1,
        "clientRequestId": "qualified-r1",
        "workspaceId": "ws-1",
        "commit": "a" * 40,
        "candidateManifestDigest": "sha256:" + "b" * 64,
        "expectedToolCount": 26,
    }


def test_original_replay_not_blocked_by_mutable_owner_release_configuration() -> None:
    caller = FakeOwner()
    caller.description["structuredReleaseConfigured"] = False
    assert asyncio.run(_apply(GatewayService(caller))).release.client_request_id == "qualified-r1"
    assert caller.calls[-1][1] == "release.apply"  # Runtime owns the qualification.


def test_response_loss_get_original_without_apply_retry_or_preflight() -> None:
    caller = FakeOwner()
    caller.fail_apply = True
    svc = GatewayService(caller)

    async def scenario():
        with pytest.raises(TimeoutError, match="response lost"):
            await _apply(svc)
        return await svc.runtime_release_get(request_id="qualified-r1")

    restored = asyncio.run(scenario())
    assert restored.client_request_id == "qualified-r1"
    assert [(o, t) for o, t, _ in caller.calls] == [
        ("runtime.linux", "runtime.describe"),
        ("runtime.linux", "release.apply"),
        ("runtime.linux", "release.get"),
    ]


@pytest.mark.parametrize(
    "change",
    [
        {"node": {"nodeId": "windows-runtime", "platform": "windows", "native": True}},
        {"node": {"nodeId": "linux-pg", "platform": "linux", "native": "true"}},
        {"targets": [{"target": "local_linux", "configured": True, "available": "true"}]},
    ],
)
def test_wrong_node_or_unqualified_release_never_forwards(change: dict[str, Any]) -> None:
    caller = FakeOwner()
    caller.description.update(change)
    with pytest.raises(GatewayError, match="not qualified"):
        asyncio.run(_apply(GatewayService(caller)))
    assert [t for _, t, _ in caller.calls] == ["runtime.describe"]


def test_wrong_owner_effect_payload_never_qualifies_as_our_release() -> None:
    for field, value in (
        ("workspaceId", "ws-other"),
        ("commit", "c" * 40),
        ("candidateManifestDigest", "sha256:" + "d" * 64),
        ("expectedToolCount", 27),
        ("clientRequestId", "other-request"),
    ):

        class WrongOwner(FakeOwner):
            async def call_tool(self, owner_id, tool, args):
                value = await super().call_tool(owner_id, tool, args)
                if tool == "release.apply":
                    value["release"][field] = value_for_field
                return value

        value_for_field = value
        with pytest.raises(GatewayError, match="different original effect"):
            asyncio.run(_apply(GatewayService(WrongOwner())))


def test_malformed_boolean_from_owner_is_not_truthy_released_fact() -> None:
    from pydantic import ValidationError

    class MalformedOwner(FakeOwner):
        async def call_tool(self, owner_id, tool, args):
            value = await super().call_tool(owner_id, tool, args)
            if tool == "release.get":
                value["receiptAvailable"] = "false"
            return value

    with pytest.raises(ValidationError):
        asyncio.run(GatewayService(MalformedOwner()).runtime_release_get(request_id="qualified-r1"))


def test_owner_get_wrong_original_request_fails_closed() -> None:
    class WrongOwner(FakeOwner):
        async def call_tool(self, owner_id, tool, args):
            value = await super().call_tool(owner_id, tool, args)
            if tool == "release.get":
                value["clientRequestId"] = "different-principal-original"
            return value

    with pytest.raises(GatewayError, match="different original request"):
        asyncio.run(GatewayService(WrongOwner()).runtime_release_get(request_id="qualified-r1"))


def test_release_authzen_target_binds_exact_effect_and_does_not_reuse_artifact_pep() -> None:
    args = {
        "requestId": "release-1",
        "workspaceId": "ws-1",
        "commit": "a" * 40,
        "candidateManifestDigest": "sha256:" + "b" * 64,
        "expectedToolCount": 26,
    }
    first = resolve_authorization_target("runtime.release.apply", args)
    assert first is not None
    resource = first.authzen_resource()
    assert first.capability == "runtime.release.linux"
    assert resource["properties"]["ownerId"] == "runtime.linux"
    assert resource["properties"]["nodeId"] == "linux-pg"
    assert resolve_authorization_target("runtime.release.get", {"requestId": "release-1"}) is None
    for field, replacement in (
        ("requestId", "another"),
        ("workspaceId", "ws-2"),
        ("commit", "c" * 40),
        ("candidateManifestDigest", "sha256:" + "c" * 64),
        ("expectedToolCount", 25),
    ):
        changed = resolve_authorization_target(
            "runtime.release.apply", {**args, field: replacement}
        )
        assert changed is not None and changed.resource_id != first.resource_id


def test_release_does_not_gain_execution_identity_from_user_supplied_arguments() -> None:
    from types import SimpleNamespace

    ctx = SimpleNamespace(
        method="tools/call",
        params={
            "name": "runtime.release.apply",
            "arguments": {
                "requestId": "r",
                "workspaceId": "ws",
                "commit": "a" * 40,
                "candidateManifestDigest": "sha256:" + "b" * 64,
                "expectedToolCount": 26,
                "ordivon_access_principal": "forged",
            },
        },
        request=SimpleNamespace(scope={"state": {}}),
    )
    forwarded = False

    async def owner(_ctx):
        nonlocal forwarded
        forwarded = True
        return {}

    result = asyncio.run(GatewayCapabilityAuthorizationMiddleware(None)(ctx, owner))
    assert result.is_error is True
    assert not forwarded


def test_verified_request_id_scopes_release_readback_by_principal() -> None:
    from types import SimpleNamespace

    def context(principal: str):
        return SimpleNamespace(
            request_context=SimpleNamespace(
                request=SimpleNamespace(
                    scope={
                        "state": {
                            "ordivon_access_principal": principal,
                            "ordivon_access_issuer": "issuer.test",
                        }
                    }
                )
            )
        )

    first = _verified_execution_request_id("r", "runtime.release.linux", context("agent-A"))
    second = _verified_execution_request_id("r", "runtime.release.linux", context("agent-B"))
    execution = _verified_execution_request_id("r", "execution.linux", context("agent-A"))
    assert first != second and first != execution
    assert first == _verified_execution_request_id("r", "runtime.release.linux", context("agent-A"))


def test_release_mcp_surface_stays_blocked_without_http_security_pep() -> None:
    async def scenario():
        from mcp import Client

        async with Client(
            build_server(service=GatewayService(FakeOwner())), raise_exceptions=False
        ) as client:
            result = await client.call_tool(
                "runtime.release.apply",
                {
                    "requestId": "r",
                    "workspaceId": "ws-1",
                    "commit": "a" * 40,
                    "candidateManifestDigest": "sha256:" + "b" * 64,
                    "expectedToolCount": 26,
                },
            )
            return result

    result = asyncio.run(scenario())
    assert result.is_error is True


def test_release_pep_exact_security_decision_required_before_owner() -> None:
    from types import SimpleNamespace

    args = {
        "requestId": "release-1",
        "workspaceId": "ws-1",
        "commit": "a" * 40,
        "candidateManifestDigest": "sha256:" + "b" * 64,
        "expectedToolCount": 26,
    }
    target = resolve_authorization_target("runtime.release.apply", args)
    assert target is not None
    required_resource = target.authzen_resource()
    state = {
        "ordivon_access_principal": "principal:test:verified-operator",
        "ordivon_access_issuer": "https://issuer.example",
    }
    ctx = SimpleNamespace(
        method="tools/call",
        params={"name": "runtime.release.apply", "arguments": args},
        request=SimpleNamespace(scope={"state": state}),
    )

    class Decision:
        def __init__(self, outcome: str = "DENY", wrong_resource: bool = False):
            self.outcome = outcome
            self.wrong_resource = wrong_resource
            self.calls = []

        async def authorize(self, **kwargs):
            self.calls.append(kwargs)
            resource = (
                {**required_resource, "id": "forged-other-request"}
                if self.wrong_resource
                else required_resource
            )
            return {
                "schemaVersion": 3,
                "kind": "ordivon.security.gateway-capability-authz",
                "principalId": kwargs["principal_id"],
                "issuer": kwargs["issuer"],
                "requestedCapability": "runtime.release.linux",
                "requestedResource": resource,
                "qualificationTarget": True,
                "outcome": self.outcome,
                "reason": "test-policy",
                "authorizationProfile": "interactive-principal-authzen",
                "authorizationEvidence": {
                    "standard": "openid-authzen-authorization-api-1.0",
                    "decision": True,
                    "requestId": "authzen-test-1",
                    "responseRequestId": "authzen-test-1",
                },
                "authorityProjection": None,
                "effectAdmission": None,
            }

    for decision, expected in (
        (Decision("DENY"), "CAPABILITY_AUTHZ_DENIED"),
        (Decision("ALLOW", wrong_resource=True), "CAPABILITY_AUTHZ_BINDING_MISMATCH"),
        (Decision("STEP_UP"), "CAPABILITY_AUTHZ_STEP_UP_REQUIRED"),
    ):
        reached = False

        async def next_owner(_ctx):
            nonlocal reached
            reached = True
            return {"ok": True}

        result = asyncio.run(GatewayCapabilityAuthorizationMiddleware(decision)(ctx, next_owner))
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == expected
        assert not reached and len(decision.calls) == 1
        assert decision.calls[0]["requested_resource"] == required_resource
    approved = Decision("ALLOW")
    forwarded = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(approved)(ctx, lambda _ctx: _approved_result())
    )
    assert forwarded["ok"] is True


async def _approved_result():
    return {"ok": True}


def test_native_tcp_gateway_release_needs_real_ingress_and_per_request_pdp(tmp_path) -> None:
    """Actual MCP HTTP + v3 Security PEP + release Owner lookup; no live installation."""
    import socket

    import httpx2
    import uvicorn
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client

    from ordivon_gateway.mcp_server import build_http_app

    secret = tmp_path / "bearer"
    secret.write_text("S" * 64, encoding="utf-8")
    secret.chmod(0o600)

    class TestSecurity:
        outcome = "ALLOW"

        def __init__(self) -> None:
            self.calls: list[dict] = []

        async def authorize(self, **kwargs):
            self.calls.append(kwargs)
            allowed = self.outcome == "ALLOW"
            return {
                "schemaVersion": 3,
                "kind": "ordivon.security.gateway-capability-authz",
                "principalId": kwargs["principal_id"],
                "issuer": kwargs["issuer"],
                "requestedCapability": kwargs["requested_capability"],
                "requestedResource": kwargs["requested_resource"],
                "qualificationTarget": True,
                "outcome": self.outcome,
                "reason": "test-only-policy",
                "authorizationProfile": "interactive-principal-authzen",
                "authorizationEvidence": {
                    "standard": "openid-authzen-authorization-api-1.0",
                    "decision": allowed,
                    "requestId": "test-authzen-1",
                    "responseRequestId": "test-authzen-1",
                },
                "authorityProjection": None,
                "effectAdmission": None,
            }

    async def run():
        owner = FakeOwner()
        policy = TestSecurity()
        app = build_http_app(
            build_server(
                service=GatewayService(owner),
                capability_authorizer=policy,
                require_http_execution_identity=True,
                protect_artifact_reads=True,
            ),
            host="127.0.0.1",
            path="/mcp",
            public_origin=None,
            access_verifier=None,
            local_bearer_token_file=str(secret),
        )
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="on")
        )
        serving = asyncio.create_task(server.serve())
        try:
            for _ in range(200):
                if server.started:
                    break
                await asyncio.sleep(0.02)
            assert server.started
            url = f"http://127.0.0.1:{port}/mcp"
            async with httpx2.AsyncClient(timeout=10, trust_env=False) as unauth:
                rejected = await unauth.post(
                    url, json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
                )
                assert rejected.status_code == 403
                assert owner.calls == []
            async with httpx2.AsyncClient(
                headers={"Authorization": "Bearer " + "S" * 64},
                timeout=httpx2.Timeout(15, read=30),
                trust_env=False,
            ) as http:
                async with Client(
                    streamable_http_client(url, http_client=http),
                    mode="2026-07-28",
                    raise_exceptions=False,
                ) as client:
                    args = {
                        "requestId": "public-release-1",
                        "workspaceId": "ws-1",
                        "commit": "a" * 40,
                        "candidateManifestDigest": "sha256:" + "b" * 64,
                        "expectedToolCount": 26,
                    }
                    applied = await client.call_tool("runtime.release.apply", args)
                    assert applied.is_error is False, applied
                    qualified_request = owner.calls[-1][2]["clientRequestId"]
                    assert qualified_request.startswith("request:gw-principal:")
                    assert policy.calls[-1]["requested_capability"] == "runtime.release.linux"
                    assert (
                        policy.calls[-1]["requested_resource"]["properties"]["nodeId"] == "linux-pg"
                    )
                    assert (
                        applied.structured_content["release"]["clientRequestId"]
                        == qualified_request
                    )
                    before = len(owner.calls)
                    got = await client.call_tool(
                        "runtime.release.get", {"requestId": args["requestId"]}
                    )
                    assert got.is_error is False, got
                    assert owner.calls[-1] == (
                        "runtime.linux",
                        "release.get",
                        {"schemaVersion": 1, "clientRequestId": qualified_request},
                    )
                    assert len(owner.calls) == before + 1  # NO describe or apply again
                    assert got.structured_content["effectDisposition"] == "admitted"
                    policy.outcome = "DENY"
                    declined = await client.call_tool("runtime.release.apply", args)
                    assert declined.is_error is True
                    assert declined.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_DENIED"
                    assert all(item[1] != "release.apply" for item in owner.calls[before:])
        finally:
            server.should_exit = True
            await asyncio.wait_for(serving, timeout=12)

    asyncio.run(run())
