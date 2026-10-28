from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ordivon_gateway.access_auth import CloudflareAccessMiddleware
from ordivon_gateway.capability_authz import (
    GatewayCapabilityAuthorizationMiddleware,
    resolve_authorization_target,
)
from ordivon_gateway.mcp_server import build_server


class FakeAuthorizer:
    def __init__(self, decision: dict[str, Any] | None = None, *, fail: bool = False) -> None:
        self.decision = decision
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    async def authorize(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(dict(kwargs))
        if self.fail:
            raise RuntimeError("security unavailable")
        if self.decision is None:
            resource = kwargs["requested_resource"]
            return _decision(resource=resource)
        return dict(self.decision)


def _resource(
    operation_ref: str = "ordivon-exec:v1:runtime.linux:job-1",
    artifact_id: str = "artifact-1",
) -> dict[str, Any]:
    target = resolve_authorization_target(
        "artifact.read", {"operationRef": operation_ref, "artifactId": artifact_id}
    )
    assert target is not None
    return target.authzen_resource()


def _decision(
    *,
    outcome: str = "ALLOW",
    principal: str = "principal:local-service:harness",
    resource: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schemaVersion": 2,
        "kind": "ordivon.security.gateway-capability-authz",
        "principalId": principal,
        "issuer": "ordivon-local-service",
        "requestedCapability": "artifact.runtime",
        "requestedResource": resource or _resource(),
        "qualificationTarget": True,
        "outcome": outcome,
        "reason": "admitted" if outcome == "ALLOW" else "test-policy",
        "authorityProjection": {"authorityId": "grant:test"} if outcome == "ALLOW" else None,
        "effectAdmission": {"admitted": True} if outcome == "ALLOW" else None,
    }


def _ctx(
    *,
    tool: str = "artifact.read",
    state: dict[str, Any] | None = None,
    arguments: dict[str, Any] | None = None,
):
    return SimpleNamespace(
        request=SimpleNamespace(scope={"state": state or {}}),
        method="tools/call",
        params={
            "name": tool,
            "arguments": arguments
            if arguments is not None
            else {
                "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
                "artifactId": "artifact-1",
            },
        },
    )


async def _next(_ctx: Any) -> dict[str, Any]:
    return {"structuredContent": {"ok": True}, "content": [], "isError": False}


def _verified_state() -> dict[str, Any]:
    return {
        "ordivon_access_principal": "principal:local-service:harness",
        "ordivon_access_issuer": "ordivon-local-service",
    }


def test_pep_uses_verified_request_state_and_server_derived_resource() -> None:
    authorizer = FakeAuthorizer()
    arguments = {
        "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
        "artifactId": "artifact:one/with-delimiters",
        "ordivon_access_principal": "principal:forged",
        "agentAdmission": {"outcome": "ALLOW"},
    }
    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(authorizer)(
            _ctx(state=_verified_state(), arguments=arguments), _next
        )
    )
    assert result["structuredContent"]["ok"] is True
    call = authorizer.calls[0]
    assert call["principal_id"] == "principal:local-service:harness"
    assert call["issuer"] == "ordivon-local-service"
    assert call["requested_capability"] == "artifact.runtime"
    resource = call["requested_resource"]
    assert resource["type"] == "ordivon.runtime.artifact"
    assert resource["properties"]["ownerId"] == "runtime.linux"
    assert resource["properties"]["jobId"] == "job-1"
    assert resource["properties"]["artifactId"] == "artifact:one/with-delimiters"
    assert resource["properties"]["operationRef"] == arguments["operationRef"]
    assert call["arguments"]["ordivon_access_principal"] == "principal:forged"


def test_artifact_resource_identity_is_job_scoped_and_delimiter_safe() -> None:
    first = _resource("ordivon-exec:v1:runtime.linux:job-1", "same:artifact/id")
    second = _resource("ordivon-exec:v1:runtime.linux:job-2", "same:artifact/id")
    third = _resource("ordivon-exec:v1:runtime.linux:job-1", "same/artifact:id")
    assert first["id"] != second["id"]
    assert first["id"] != third["id"]
    assert first["id"].startswith("runtime-artifact:v1:")


def test_malformed_or_external_artifact_target_fails_closed_before_authorizer() -> None:
    for operation_ref, code in (
        ("not-an-operation", "CAPABILITY_AUTHZ_TARGET_INVALID"),
        ("ordivon-exec:v1:external.pull:operation-1", "CAPABILITY_AUTHZ_TARGET_UNQUALIFIED"),
    ):
        authorizer = FakeAuthorizer()
        reached = False

        async def forbidden_next(_ctx: Any):
            nonlocal reached
            reached = True
            return {}

        result = asyncio.run(
            GatewayCapabilityAuthorizationMiddleware(authorizer)(
                _ctx(
                    state=_verified_state(),
                    arguments={"operationRef": operation_ref, "artifactId": "artifact-1"},
                ),
                forbidden_next,
            )
        )
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == code
        assert authorizer.calls == []
        assert reached is False


def test_protected_capability_without_verified_ingress_fails_closed() -> None:
    authorizer = FakeAuthorizer()
    result = asyncio.run(GatewayCapabilityAuthorizationMiddleware(authorizer)(_ctx(), _next))
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_INGRESS_IDENTITY_MISSING"
    assert authorizer.calls == []


def test_security_deny_and_step_up_do_not_reach_owner() -> None:
    for outcome, code in (
        ("DENY", "CAPABILITY_AUTHZ_DENIED"),
        ("STEP_UP", "CAPABILITY_AUTHZ_STEP_UP_REQUIRED"),
    ):
        authorizer = FakeAuthorizer(_decision(outcome=outcome))
        reached = False

        async def forbidden_next(_ctx: Any):
            nonlocal reached
            reached = True
            return {}

        result = asyncio.run(
            GatewayCapabilityAuthorizationMiddleware(authorizer)(
                _ctx(state=_verified_state()), forbidden_next
            )
        )
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == code
        assert reached is False


def test_security_principal_or_resource_binding_mismatch_fails_closed() -> None:
    wrong_principal = FakeAuthorizer(_decision(principal="principal:other"))
    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(wrong_principal)(
            _ctx(state=_verified_state()), _next
        )
    )
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_BINDING_MISMATCH"

    wrong_resource = _resource("ordivon-exec:v1:runtime.linux:job-other", "artifact-1")
    authorizer = FakeAuthorizer(_decision(resource=wrong_resource))
    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(authorizer)(_ctx(state=_verified_state()), _next)
    )
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_BINDING_MISMATCH"


def test_security_unavailable_fails_closed() -> None:
    unavailable = FakeAuthorizer(fail=True)
    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(unavailable)(_ctx(state=_verified_state()), _next)
    )
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_UNAVAILABLE"


def test_unprotected_tools_bypass_capability_authorizer() -> None:
    authorizer = FakeAuthorizer()
    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(authorizer)(_ctx(tool="capability.search"), _next)
    )
    assert result["structuredContent"]["ok"] is True
    assert authorizer.calls == []


def test_verified_ingress_to_authorization_real_request_state_contract(tmp_path) -> None:
    """One actual G07->G06 consumption, not merely a Plan or a forged Tool arg.

    The loopback bearer authenticates ONLY through the G07 ingress middleware.
    G06 reads the resulting request state, and a Security decision still gates
    the protected owner call. Neither an unverified principal nor an explicit
    DENY can reach the next handler.
    """
    plan_path = Path(__file__).resolve().parents[1] / "planning/lego-plan-r1.json"
    plan = json.loads(plan_path.read_text())
    nodes = {item["id"]: item for item in plan["nodes"]}
    assert "G07" in nodes["G06"]["dependencies"]
    assert any(
        item["path"] == "src/ordivon_gateway/capability_authz.py"
        and "SOURCE_REQUEST_STATE_CONSUMER" in item["standing"]
        for item in nodes["G07"]["consumerBindings"]
    )
    assert any(
        item["path"] == "src/ordivon_gateway/mcp_server.py"
        and "SOURCE_MCP_MIDDLEWARE_CONSUMER" in item["standing"]
        for item in nodes["G06"]["consumerBindings"]
    )

    private_bearer = tmp_path / "local-bearer"
    private_bearer.write_text("a" * 64)
    private_bearer.chmod(0o600)

    class MustNotVerifyCloudflare:
        def verify_identity(self, token: str):
            raise AssertionError("local service bearer must not invoke Cloudflare verifier")

    async def scenario(token: str, authorizer: FakeAuthorizer, *, client_host: str = "127.0.0.1"):
        effects = []
        messages = []
        pep = GatewayCapabilityAuthorizationMiddleware(authorizer)

        async def downstream(scope, receive, send):
            ctx = _ctx(
                state=scope["state"],
                arguments={
                    "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
                    "artifactId": "artifact-1",
                    "ordivon_access_principal": "principal:forged",
                },
            )

            async def owner_handler(_context):
                effects.append("owner_invoked")
                return await _next(_context)

            outcome = await pep(ctx, owner_handler)
            effects.append(outcome)
            await send({"type": "http.response.start", "status": 204, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        ingress = CloudflareAccessMiddleware(
            downstream,
            MustNotVerifyCloudflare(),
            local_bearer_token_file=str(private_bearer),
        )

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await ingress(
            {
                "type": "http",
                "path": "/mcp",
                "method": "POST",
                "client": (client_host, 23456),
                "headers": [(b"authorization", f"Bearer {token}".encode())],
                "state": {},
            },
            receive,
            send,
        )
        return (
            next(m["status"] for m in messages if m["type"] == "http.response.start"),
            effects,
            authorizer.calls,
        )

    allowed = FakeAuthorizer()
    status, effects, calls = asyncio.run(scenario("a" * 64, allowed))
    assert status == 204
    assert effects[0] == "owner_invoked"
    assert effects[1]["structuredContent"]["ok"] is True
    assert calls[0]["principal_id"] == "principal:local-service:harness"
    assert calls[0]["issuer"] == "ordivon-local-service"
    assert calls[0]["arguments"]["ordivon_access_principal"] == "principal:forged"

    invalid = FakeAuthorizer()
    status, effects, calls = asyncio.run(scenario("not-the-secret", invalid))
    assert status == 403
    assert effects == []
    assert calls == []

    remote = FakeAuthorizer()
    status, effects, calls = asyncio.run(scenario("a" * 64, remote, client_host="203.0.113.7"))
    assert status == 403  # Loopback credential is not accepted remotely.
    assert effects == []
    assert calls == []

    rejected = FakeAuthorizer(_decision(outcome="DENY"))
    status, effects, calls = asyncio.run(scenario("a" * 64, rejected))
    assert status == 204  # HTTP middleware passed; protected MCP Tool returned DENY.
    assert len(effects) == 1
    assert effects[0].is_error is True
    assert effects[0].structured_content["error"]["code"] == "CAPABILITY_AUTHZ_DENIED"
    assert len(calls) == 1


def test_build_server_adds_pep_only_when_trusted_authorizer_is_injected() -> None:
    plain = build_server(service=object())  # type: ignore[arg-type]
    assert "GatewayCapabilityAuthorizationMiddleware" not in [
        type(value).__name__ for value in plain.middleware
    ]

    protected = build_server(
        service=object(),  # type: ignore[arg-type]
        capability_authorizer=FakeAuthorizer(),
    )
    names = [type(value).__name__ for value in protected.middleware]
    assert "GatewayCapabilityAuthorizationMiddleware" in names
    assert names.index("GatewayCapabilityAuthorizationMiddleware") > names.index(
        "GatewayAuditMiddleware"
    )
