from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

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
