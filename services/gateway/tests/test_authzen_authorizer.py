from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from ordivon_gateway.authzen_authorizer import (
    AuthZenAuthorizerError,
    AuthZenPrincipalAuthorizer,
)
from ordivon_gateway.capability_authz import GatewayCapabilityAuthorizationMiddleware


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        decision: object = True,
        request_id: str | None = None,
        json_error: bool = False,
    ) -> None:
        self.status_code = status_code
        self._decision = decision
        self._request_id = request_id
        self._json_error = json_error
        self.headers: dict[str, str] = {}

    def bind_request_id(self, request_id: str) -> None:
        self.headers["X-Request-ID"] = self._request_id or request_id

    def json(self) -> dict[str, object]:
        if self._json_error:
            raise ValueError("invalid json")
        return {"decision": self._decision}


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def post(self, endpoint: str, **kwargs: Any) -> FakeResponse:
        call = {"endpoint": endpoint, **kwargs}
        self.calls.append(call)
        self.response.bind_request_id(kwargs["headers"]["X-Request-ID"])
        return self.response


def _resource() -> dict[str, Any]:
    return {
        "type": "ordivon.runtime.artifact",
        "id": "runtime-artifact:v1:test",
        "properties": {
            "identityContract": "ordivon.runtime-artifact-resource-key.v1",
            "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
            "ownerId": "runtime.linux",
            "jobId": "job-1",
            "artifactId": "artifact-1",
        },
    }


def _authorizer(
    response: FakeResponse,
    *,
    endpoint: str = "https://pdp.example.test/access/v1/evaluation",
) -> tuple[AuthZenPrincipalAuthorizer, FakeSession]:
    session = FakeSession(response)
    authorizer = AuthZenPrincipalAuthorizer(
        endpoint,
        bearer_token_provider=lambda: "test-token-material-1234567890",
        session=session,  # type: ignore[arg-type]
        allow_insecure_loopback=endpoint.startswith("http://127.0.0.1"),
    )
    return authorizer, session


def _authorize(authorizer: AuthZenPrincipalAuthorizer) -> dict[str, Any]:
    result = asyncio.run(
        authorizer.authorize(
            principal_id="principal:cf-access:test",
            issuer="https://team.cloudflareaccess.com",
            requested_capability="artifact.runtime",
            requested_resource=_resource(),
            tool_name="artifact.read",
            arguments={"forged": "must-not-be-exported"},
            request_state={"untrusted": "must-not-be-exported"},
        )
    )
    return dict(result)


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(
        request=SimpleNamespace(
            scope={
                "state": {
                    "ordivon_access_principal": "principal:cf-access:test",
                    "ordivon_access_issuer": "https://team.cloudflareaccess.com",
                }
            }
        ),
        method="tools/call",
        params={
            "name": "artifact.read",
            "arguments": {
                "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
                "artifactId": "artifact-1",
                "agentAdmission": {"outcome": "ALLOW"},
            },
        },
    )


async def _next(_ctx: Any) -> dict[str, Any]:
    return {"structuredContent": {"ownerReached": True}, "content": [], "isError": False}


def test_authzen_principal_authorizer_emits_exact_standard_request_and_bound_evidence() -> None:
    authorizer, session = _authorizer(FakeResponse(decision=True))
    result = _authorize(authorizer)

    assert result["schemaVersion"] == 3
    assert result["authorizationProfile"] == "interactive-principal-authzen"
    assert result["outcome"] == "ALLOW"
    assert result["authorityProjection"] is None
    assert result["effectAdmission"] is None
    assert result["authorizationEvidence"]["decision"] is True
    assert (
        result["authorizationEvidence"]["requestId"]
        == result["authorizationEvidence"]["responseRequestId"]
    )

    call = session.calls[0]
    assert call["endpoint"] == "https://pdp.example.test/access/v1/evaluation"
    assert call["json"] == {
        "subject": {
            "type": "user",
            "id": "principal:cf-access:test",
            "properties": {"issuer": "https://team.cloudflareaccess.com"},
        },
        "resource": _resource(),
        "action": {"name": "artifact.runtime"},
    }
    assert "forged" not in repr(call["json"])
    assert "agentAdmission" not in repr(call["json"])
    assert "gatewayTool" not in repr(call["json"])
    assert call["headers"]["Authorization"] == "Bearer test-token-material-1234567890"
    assert "test-token-material" not in repr(result)


def test_authzen_deny_is_preserved_and_does_not_claim_effect_admission() -> None:
    authorizer, _ = _authorizer(FakeResponse(decision=False))
    result = _authorize(authorizer)
    assert result["outcome"] == "DENY"
    assert result["authorizationEvidence"]["decision"] is False
    assert result["authorityProjection"] is None
    assert result["effectAdmission"] is None


def test_authzen_transport_and_binding_fail_closed() -> None:
    wrong_echo, _ = _authorizer(FakeResponse(decision=True, request_id="different-request"))
    with pytest.raises(AuthZenAuthorizerError, match="echo"):
        _authorize(wrong_echo)

    bad_status, _ = _authorizer(FakeResponse(status_code=503, decision=True))
    with pytest.raises(AuthZenAuthorizerError, match="HTTP status 503"):
        _authorize(bad_status)

    invalid_decision, _ = _authorizer(FakeResponse(decision="yes"))
    with pytest.raises(AuthZenAuthorizerError, match="invalid evaluation response"):
        _authorize(invalid_decision)

    invalid_json, _ = _authorizer(FakeResponse(json_error=True))
    with pytest.raises(AuthZenAuthorizerError, match="invalid JSON"):
        _authorize(invalid_json)


def test_authzen_endpoint_requires_https_except_explicit_loopback_canary() -> None:
    with pytest.raises(AuthZenAuthorizerError, match="HTTPS"):
        AuthZenPrincipalAuthorizer(
            "http://pdp.example.test/access/v1/evaluation",
            bearer_token_provider=lambda: "test-token-material-1234567890",
        )

    AuthZenPrincipalAuthorizer(
        "http://127.0.0.1:18080/access/v1/evaluation",
        bearer_token_provider=lambda: "test-token-material-1234567890",
        allow_insecure_loopback=True,
    )


def test_gateway_middleware_accepts_bound_h2_authzen_allow() -> None:
    authorizer, _ = _authorizer(FakeResponse(decision=True))
    result = asyncio.run(GatewayCapabilityAuthorizationMiddleware(authorizer)(_ctx(), _next))
    assert result["structuredContent"]["ownerReached"] is True


def test_gateway_middleware_blocks_h2_authzen_deny_and_invalid_evidence() -> None:
    reached = False

    async def forbidden_next(_ctx: Any) -> dict[str, Any]:
        nonlocal reached
        reached = True
        return {"structuredContent": {"ownerReached": True}}

    denied, _ = _authorizer(FakeResponse(decision=False))
    result = asyncio.run(GatewayCapabilityAuthorizationMiddleware(denied)(_ctx(), forbidden_next))
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_DENIED"
    assert reached is False

    class InvalidEvidenceAuthorizer:
        async def authorize(self, **kwargs: Any) -> dict[str, Any]:
            resource = kwargs["requested_resource"]
            return {
                "schemaVersion": 3,
                "kind": "ordivon.security.gateway-capability-authz",
                "principalId": kwargs["principal_id"],
                "issuer": kwargs["issuer"],
                "requestedCapability": kwargs["requested_capability"],
                "requestedResource": resource,
                "qualificationTarget": True,
                "authorizationProfile": "interactive-principal-authzen",
                "outcome": "ALLOW",
                "reason": "authzen-permit",
                "authorizationEvidence": {
                    "standard": "openid-authzen-authorization-api-1.0",
                    "requestId": "request-a",
                    "responseRequestId": "request-b",
                    "decision": True,
                },
                "authorityProjection": None,
                "effectAdmission": None,
            }

    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(InvalidEvidenceAuthorizer())(
            _ctx(), forbidden_next
        )
    )
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_ALLOW_INCOMPLETE"
    assert reached is False
