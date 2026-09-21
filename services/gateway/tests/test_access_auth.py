from __future__ import annotations

import asyncio
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
