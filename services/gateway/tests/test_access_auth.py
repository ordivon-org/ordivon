from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from ordivon_gateway.access_auth import (
    AccessAuthError,
    CloudflareAccessConfig,
    CloudflareAccessMiddleware,
    CloudflareAccessVerifier,
)


@dataclass
class StaticKeyResolver:
    key: Any

    def __call__(self, token: str) -> Any:
        assert token
        return self.key


def _token(private_key: Any, *, issuer: str, audience: str, subject: str = "user-1") -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": issuer,
            "aud": [audience],
            "sub": subject,
            "iat": now - 1,
            "exp": now + 300,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def test_verifier_requires_signature_issuer_audience_expiry_and_subject() -> None:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key()
    config = CloudflareAccessConfig(
        issuer="https://team.cloudflareaccess.com",
        audience="aud-1",
        jwks_url="https://team.cloudflareaccess.com/cdn-cgi/access/certs",
    )
    verifier = CloudflareAccessVerifier(config, key_resolver=StaticKeyResolver(public))

    identity = verifier.verify_identity(
        _token(private, issuer=config.issuer, audience=config.audience, subject="agent-7")
    )
    assert identity.issuer == config.issuer
    assert identity.subject == "agent-7"
    assert identity.principal.startswith("principal:cf-access:")

    for token in [
        _token(private, issuer="https://wrong.cloudflareaccess.com", audience=config.audience),
        _token(private, issuer=config.issuer, audience="wrong-audience"),
    ]:
        try:
            verifier.verify_identity(token)
        except AccessAuthError:
            pass
        else:
            raise AssertionError("invalid Cloudflare Access token must fail closed")


def test_middleware_rejects_missing_assertion_and_projects_verified_identity() -> None:
    class Verifier:
        def verify_identity(self, token: str):
            assert token == "good"
            return type(
                "Identity",
                (),
                {
                    "issuer": "https://team.cloudflareaccess.com",
                    "subject": "subject-1",
                    "principal": "principal:cf-access:test",
                },
            )()

    seen: list[dict[str, Any]] = []

    async def app(scope, receive, send):
        seen.append(scope)
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = CloudflareAccessMiddleware(app, Verifier())

    async def call(headers: list[tuple[bytes, bytes]], path: str = "/mcp") -> int:
        messages: list[dict[str, Any]] = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await middleware(
            {
                "type": "http",
                "path": path,
                "method": "POST",
                "headers": headers,
                "state": {},
            },
            receive,
            send,
        )
        return next(m["status"] for m in messages if m["type"] == "http.response.start")

    assert asyncio.run(call([])) == 403
    assert seen == []

    assert asyncio.run(call([(b"cf-access-jwt-assertion", b"good")])) == 204
    assert seen[-1]["state"]["ordivon_access_principal"] == "principal:cf-access:test"

    # Health is intentionally not a business-authority path.
    assert asyncio.run(call([], path="/health")) == 204


def test_loopback_bearer_is_authenticated_without_weakening_remote_cloudflare(tmp_path) -> None:
    credential = tmp_path / "gateway-local-bearer"
    credential.write_text("x" * 64, encoding="utf-8")
    credential.chmod(0o600)
    seen: list[dict[str, Any]] = []

    async def app(scope, receive, send):
        seen.append(scope)
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    class NeverCloudflare:
        def verify_identity(self, token: str):
            raise AssertionError("local service identity must not invoke Cloudflare verification")

    middleware = CloudflareAccessMiddleware(
        app, NeverCloudflare(), local_bearer_token_file=str(credential)
    )

    async def call(client_host: str, token: str) -> int:
        messages: list[dict[str, Any]] = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await middleware(
            {
                "type": "http",
                "path": "/mcp",
                "method": "POST",
                "headers": [(b"authorization", f"Bearer {token}".encode())],
                "state": {},
                "client": (client_host, 12345),
            },
            receive,
            send,
        )
        return next(m["status"] for m in messages if m["type"] == "http.response.start")

    assert asyncio.run(call("127.0.0.1", "x" * 64)) == 204
    assert seen[-1]["state"]["ordivon_access_principal"] == "principal:local-service:harness"
    assert seen[-1]["state"]["ordivon_access_issuer"] == "ordivon-local-service"
    assert asyncio.run(call("192.0.2.10", "x" * 64)) == 403
    assert asyncio.run(call("127.0.0.1", "wrong" * 16)) == 403


def test_cloudflare_service_token_signed_empty_sub_maps_to_distinct_workload_principal() -> None:
    """Cloudflare service tokens have empty signed sub and signed common_name."""
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    config = CloudflareAccessConfig(
        issuer="https://team.cloudflareaccess.com",
        audience="aud-1",
        jwks_url="https://team.cloudflareaccess.com/cdn-cgi/access/certs",
    )
    verifier = CloudflareAccessVerifier(
        config, key_resolver=StaticKeyResolver(private.public_key())
    )

    def issue(
        *, subject: str = "", kind: str = "app", common_name: object = "agent-a.access"
    ) -> str:
        claims: dict[str, Any] = {
            "iss": config.issuer,
            "aud": [config.audience],
            "sub": subject,
            "type": kind,
            "iat": int(time.time()) - 1,
            "exp": int(time.time()) + 300,
        }
        if common_name is not None:
            claims["common_name"] = common_name
        return jwt.encode(claims, private, algorithm="RS256", headers={"kid": "test-key"})

    first = verifier.verify_identity(issue())
    same = verifier.verify_identity(issue())
    different = verifier.verify_identity(issue(common_name="agent-b.access"))
    human = verifier.verify_identity(issue(subject="service-token:agent-a.access"))
    assert first.issuer == config.issuer
    assert first.principal.startswith("principal:cf-access:")
    assert first.principal == same.principal
    assert first.principal != different.principal
    # Domain separation prevents signed human sub strings colliding with service identity.
    assert first.principal != human.principal
    assert first.subject == "service-token:agent-a.access"

    # A CF Access human subject keeps the preexisting principal derivation.
    legacy = hashlib.sha256(
        b"ordivon-gateway-cf-access-principal-v1\0" + config.issuer.encode() + b"\0" + b"human-7"
    ).hexdigest()
    assert verifier.verify_identity(issue(subject="human-7")).principal == (
        f"principal:cf-access:{legacy}"
    )

    for invalid in (
        issue(common_name=None),
        issue(common_name=""),
        issue(common_name="bad id"),
        issue(common_name="x"),
        issue(common_name=9),
        issue(kind="org"),
        issue(subject="  "),
    ):
        try:
            verifier.verify_identity(invalid)
        except AccessAuthError:
            pass
        else:
            raise AssertionError("unqualified service-token identity must be denied")

    # Signature and audience checks are required for service identities as for humans.
    hostile = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    claims = {
        "iss": config.issuer,
        "aud": [config.audience],
        "sub": "",
        "type": "app",
        "common_name": "agent-a.access",
        "iat": int(time.time()) - 1,
        "exp": int(time.time()) + 300,
    }
    signed_wrong_key = jwt.encode(claims, hostile, algorithm="RS256", headers={"kid": "test-key"})
    try:
        verifier.verify_identity(signed_wrong_key)
    except AccessAuthError:
        pass
    else:
        raise AssertionError("untrusted service-token signing key must be denied")
