"""Signed Cloudflare Access operator path vs second-object PDP and local bearers.

Production AuthZEN denied a valid ChatGPT Cloudflare Principal on host.status.
This protects the actual ingress/security boundary, not a forged Tool argument.
"""

from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from mcp.server.mcpserver.exceptions import ToolError

from ordivon_gateway.security.access_auth import (
    CloudflareAccessConfig,
    CloudflareAccessMiddleware,
    CloudflareAccessVerifier,
)
from ordivon_gateway.security.capability_authz import GatewayCapabilityAuthorizationMiddleware
from ordivon_gateway.security.entrypoint import (
    require_release_access,
    trusted_operator_from_env,
)
from ordivon_gateway.security.trusted_operator import TrustedCloudflareOperator

ISSUER = "https://team.cloudflareaccess.com"
AUDIENCE = "trusted-operator-only-app"
PRINCIPAL = "principal:cf-access:" + "a" * 64

VALID = {
    "ordivon_access_principal": PRINCIPAL,
    "ordivon_access_issuer": ISSUER,
    "ordivon_access_verified_by_gateway": "cloudflare_access_jwt",
}
LOCAL = {
    "ordivon_access_principal": "principal:local-service:harness",
    "ordivon_access_issuer": "ordivon-local-service",
    "ordivon_access_verified_by_gateway": "local_service_bearer",
}


class DenyAuthorizer:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def authorize(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "schemaVersion": 3,
            "kind": "ordivon.security.gateway-capability-authz",
            "principalId": kwargs["principal_id"],
            "issuer": kwargs["issuer"],
            "requestedCapability": kwargs["requested_capability"],
            "requestedResource": kwargs["requested_resource"],
            "qualificationTarget": True,
            "outcome": "DENY",
            "reason": "authzen-deny",
        }


def _ctx(tool: str, args: dict[str, Any], state: dict[str, Any]):
    return SimpleNamespace(
        method="tools/call",
        params={"name": tool, "arguments": args},
        request=SimpleNamespace(scope={"state": state}),
    )


def _run(
    tool: str,
    args: dict[str, Any],
    state: dict[str, Any],
    operator: TrustedCloudflareOperator | None,
) -> tuple[Any, list[str], list]:
    authorizer = DenyAuthorizer()
    calls: list[str] = []

    async def owner(_ctx: Any):
        calls.append("real-owner")
        return {"structuredContent": {"ok": True}}

    result = asyncio.run(
        GatewayCapabilityAuthorizationMiddleware(
            authorizer,
            trusted_operator=operator,
        )(_ctx(tool, args, state), owner)
    )
    return result, calls, authorizer.calls


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("host.status", {"detail": "summary"}),
        ("work.get", {"workRef": "work:verified:one"}),
        ("message.post", {"authorActorRef": "agent:chatgpt:gpt-6", "messageRef": "message:one:1"}),
        (
            "artifact.read",
            {
                "operationRef": "ordivon-exec:v1:runtime.linux:job-1",
                "artifactId": "attempt-1.stdout",
            },
        ),
        (
            "runtime.release.apply",
            {
                "requestId": "release-1",
                "workspaceId": "ws-test",
                "commit": "a" * 40,
                "candidateManifestDigest": "sha256:" + "b" * 64,
                "expectedToolCount": 42,
            },
        ),
    ],
)
def test_verified_cloudflare_operator_reaches_original_owner_without_pdp(
    tool: str, args: dict[str, Any]
) -> None:
    result, reached, pdp_calls = _run(tool, args, VALID, TrustedCloudflareOperator(ISSUER))
    assert result["structuredContent"]["ok"] is True
    assert reached == ["real-owner"]
    assert pdp_calls == []


@pytest.mark.parametrize(
    "mutation",
    [
        {"ordivon_access_verified_by_gateway": None},
        {"ordivon_access_verified_by_gateway": "local_service_bearer"},
        {"ordivon_access_issuer": "https://evil.cloudflareaccess.com"},
        {"ordivon_access_principal": "principal:cf-access:spoof"},
        {"ordivon_access_principal": "principal:cf-access:" + "Z" * 64},
        {"ordivon_access_principal": "principal:local-service:harness"},
    ],
)
def test_no_cf_signature_marker_or_wrong_issuer_never_gets_operator_path(
    mutation: dict[str, Any],
) -> None:
    state = {**VALID, **mutation}
    result, reached, pdp_calls = _run(
        "host.status", {"detail": "summary"}, state, TrustedCloudflareOperator(ISSUER)
    )
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_DENIED"
    assert reached == [] and len(pdp_calls) == 1


def test_local_harness_and_unverified_http_identity_cannot_inherit_cf_operator() -> None:
    local, reached, pdp_calls = _run(
        "host.status", {"detail": "summary"}, LOCAL, TrustedCloudflareOperator(ISSUER)
    )
    assert local.is_error is True
    assert local.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_DENIED"
    assert reached == [] and len(pdp_calls) == 1
    missing, reached, pdp_calls = _run(
        "host.status",
        {"ordivon_access_principal": PRINCIPAL},
        {},
        TrustedCloudflareOperator(ISSUER),
    )
    assert missing.is_error is True
    assert missing.structured_content["error"]["code"] == (
        "CAPABILITY_AUTHZ_INGRESS_IDENTITY_MISSING"
    )
    assert reached == [] and pdp_calls == []


def test_default_security_mode_preserves_authzen_policy() -> None:
    result, reached, calls = _run("host.status", {"detail": "summary"}, VALID, None)
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_DENIED"
    assert reached == [] and len(calls) == 1


def test_security_target_still_rejects_malformed_artifact_before_operator() -> None:
    result, reached, pdp_calls = _run(
        "artifact.read",
        {"operationRef": "not-valid", "artifactId": "a"},
        VALID,
        TrustedCloudflareOperator(ISSUER),
    )
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "CAPABILITY_AUTHZ_TARGET_INVALID"
    assert reached == [] and pdp_calls == []


def test_trusted_operator_mode_must_be_explicit_and_cf_verified(monkeypatch) -> None:
    for name in (
        "ORDIVON_GATEWAY_TRUSTED_CF_OPERATOR",
        "ORDIVON_GATEWAY_TRUST_CF_ACCESS",
        "ORDIVON_GATEWAY_CF_ACCESS_ISSUER",
        "ORDIVON_GATEWAY_CF_ACCESS_AUDIENCE",
    ):
        monkeypatch.delenv(name, raising=False)
    assert trusted_operator_from_env() is None
    monkeypatch.setenv("ORDIVON_GATEWAY_TRUSTED_CF_OPERATOR", "true")
    with pytest.raises(RuntimeError, match="JWT-verifying"):
        trusted_operator_from_env()
    monkeypatch.setenv("ORDIVON_GATEWAY_TRUST_CF_ACCESS", "true")
    with pytest.raises(RuntimeError, match="issuer and audience"):
        trusted_operator_from_env()
    monkeypatch.setenv("ORDIVON_GATEWAY_CF_ACCESS_ISSUER", ISSUER)
    monkeypatch.setenv("ORDIVON_GATEWAY_CF_ACCESS_AUDIENCE", AUDIENCE)
    assert trusted_operator_from_env() == TrustedCloudflareOperator(ISSUER)
    monkeypatch.setenv("ORDIVON_GATEWAY_TRUSTED_CF_OPERATOR", "bananas")
    with pytest.raises(RuntimeError, match="must be true or false"):
        trusted_operator_from_env()


def test_native_runtime_release_trust_is_still_verified_http_and_owner_qualified() -> None:
    def ctx(state: dict):
        return SimpleNamespace(
            request_context=SimpleNamespace(request=SimpleNamespace(scope={"state": state}))
        )

    trust = TrustedCloudflareOperator(ISSUER)
    require_release_access(ctx(VALID), True, None, trust)
    with pytest.raises(ToolError, match="configured HTTP Security PEP"):
        require_release_access(ctx(LOCAL), True, None, trust)
    with pytest.raises(ToolError, match="authenticated HTTP ingress"):
        require_release_access(ctx(VALID), False, None, trust)
    with pytest.raises(ToolError, match="verified ingress"):
        require_release_access(ctx({}), True, None, trust)


def test_actual_signed_jwt_ingress_to_owner_and_bad_signatures_are_denied() -> None:
    """Actual RS256 JWT verification -> Gateway-owned marker -> object PEP -> Host."""
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    wrong_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    config = CloudflareAccessConfig(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url=ISSUER + "/cdn-cgi/access/certs",
    )
    verifier = CloudflareAccessVerifier(config, key_resolver=lambda _token: private.public_key())
    authorization = DenyAuthorizer()
    owner_calls: list[str] = []
    observed_markers: list[str] = []

    async def owner(_ctx: Any) -> dict[str, Any]:
        owner_calls.append("Host")
        return {"structuredContent": {"ok": True}}

    pep = GatewayCapabilityAuthorizationMiddleware(
        authorization,
        trusted_operator=TrustedCloudflareOperator(ISSUER),
    )

    async def downstream(scope: dict, _receive: Any, send: Any) -> None:
        observed_markers.append(scope["state"]["ordivon_access_verified_by_gateway"])
        result = await pep(_ctx("host.status", {"detail": "summary"}, scope["state"]), owner)
        assert result["structuredContent"]["ok"] is True
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    ingress = CloudflareAccessMiddleware(downstream, verifier)

    def token(key: Any, *, iss: str = ISSUER, aud: str = AUDIENCE) -> str:
        now = int(time.time())
        claims = {
            "iss": iss,
            "aud": [aud],
            "sub": "signed-operator",
            "iat": now - 1,
            "exp": now + 180,
        }
        return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test-kid"})

    async def call(assertion: str | None) -> int:
        messages: list[dict[str, Any]] = []
        headers = (
            [(b"cf-access-jwt-assertion", assertion.encode())] if assertion is not None else []
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
                "client": ("127.0.0.1", 50000),
                "headers": headers,
                "state": {},
            },
            receive,
            send,
        )
        return next(m["status"] for m in messages if m["type"] == "http.response.start")

    assert asyncio.run(call(token(private))) == 204

    # ChatGPT/automation may present a Cloudflare signed service-token App JWT
    # with an empty sub. It is the SAME verified Access App trust boundary,
    # not a loopback Harness bearer or a claimed Agent Actor.
    now = int(time.time())
    service_assertion = jwt.encode(
        {
            "iss": ISSUER,
            "aud": [AUDIENCE],
            "sub": "",
            "type": "app",
            "common_name": "chatgpt-integration.access",
            "iat": now - 1,
            "exp": now + 180,
        },
        private,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    assert asyncio.run(call(service_assertion)) == 204
    assert observed_markers == ["cloudflare_access_jwt"] * 2
    assert owner_calls == ["Host"] * 2
    assert authorization.calls == []
    for bad in (
        None,
        token(wrong_private),
        token(private, iss="https://other.cloudflareaccess.com"),
        token(private, aud="wrong-audience"),
    ):
        assert asyncio.run(call(bad)) == 403
    assert observed_markers == ["cloudflare_access_jwt"] * 2
    assert owner_calls == ["Host"] * 2
    assert authorization.calls == []
