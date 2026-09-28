from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from ordivon_gateway.capability_authz import GatewayCapabilityAuthorizationMiddleware
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
        assert self.decision is not None
        return dict(self.decision)


def _decision(
    *, outcome: str = "ALLOW", principal: str = "principal:local-service:harness"
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.gateway-capability-authz",
        "principalId": principal,
        "issuer": "ordivon-local-service",
        "requestedCapability": "artifact.runtime",
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
        params={"name": tool, "arguments": arguments or {}},
    )


async def _next(_ctx: Any) -> dict[str, Any]:
    return {"structuredContent": {"ok": True}, "content": [], "isError": False}


def test_pep_uses_verified_request_state_and_ignores_forged_identity_arguments() -> None:
    principal = "principal:local-service:harness"
    authorizer = FakeAuthorizer(_decision(principal=principal))
    middleware = GatewayCapabilityAuthorizationMiddleware(authorizer)
    ctx = _ctx(
        state={
            "ordivon_access_principal": principal,
            "ordivon_access_issuer": "ordivon-local-service",
        },
        arguments={
            "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
            "artifactId": "artifact-1",
            "ordivon_access_principal": "principal:forged",
            "agentAdmission": {"outcome": "ALLOW"},
        },
    )
    result = asyncio.run(middleware(ctx, _next))
    assert result["structuredContent"]["ok"] is True
    call = authorizer.calls[0]
    assert call["principal_id"] == principal
    assert call["issuer"] == "ordivon-local-service"
    assert call["requested_capability"] == "artifact.runtime"
    assert call["arguments"]["ordivon_access_principal"] == "principal:forged"


def test_protected_capability_without_verified_ingress_fails_closed() -> None:
    authorizer = FakeAuthorizer(_decision())
    result = asyncio.run(GatewayCapabilityAuthorizationMiddleware(authorizer)(_ctx(), _next))
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_INGRESS_IDENTITY_MISSING"
    assert authorizer.calls == []


def test_security_deny_and_step_up_do_not_reach_owner() -> None:
    state = {
        "ordivon_access_principal": "principal:local-service:harness",
        "ordivon_access_issuer": "ordivon-local-service",
    }
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
            GatewayCapabilityAuthorizationMiddleware(authorizer)(_ctx(state=state), forbidden_next)
        )
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == code
        assert reached is False


def test_security_binding_mismatch_and_unavailable_fail_closed() -> None:
    state = {
        "ordivon_access_principal": "principal:local-service:harness",
        "ordivon_access_issuer": "ordivon-local-service",
    }
    wrong = FakeAuthorizer(_decision(principal="principal:other"))
    result = asyncio.run(GatewayCapabilityAuthorizationMiddleware(wrong)(_ctx(state=state), _next))
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_BINDING_MISMATCH"

    unavailable = FakeAuthorizer(fail=True)
    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(unavailable)(_ctx(state=state), _next)
    )
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_UNAVAILABLE"


def test_unprotected_tools_bypass_capability_authorizer() -> None:
    authorizer = FakeAuthorizer(_decision())
    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(authorizer)(_ctx(tool="capability.search"), _next)
    )
    assert result["structuredContent"]["ok"] is True
    assert authorizer.calls == []


def test_build_server_adds_pep_only_when_trusted_authorizer_is_injected() -> None:
    plain = build_server(service=object())  # type: ignore[arg-type]
    assert "GatewayCapabilityAuthorizationMiddleware" not in [
        type(value).__name__ for value in plain.middleware
    ]

    protected = build_server(
        service=object(),  # type: ignore[arg-type]
        capability_authorizer=FakeAuthorizer(_decision()),
    )
    names = [type(value).__name__ for value in protected.middleware]
    assert "GatewayCapabilityAuthorizationMiddleware" in names
    assert names.index("GatewayCapabilityAuthorizationMiddleware") > names.index(
        "GatewayAuditMiddleware"
    )
