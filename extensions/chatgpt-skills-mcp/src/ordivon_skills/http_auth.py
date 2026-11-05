from __future__ import annotations

import asyncio
import hmac
import json

import jwt
from jwt import PyJWKClient


async def _drain(receive, *, max_bytes: int) -> bool:
    total = 0
    while True:
        message = await receive()
        if message.get("type") == "http.disconnect":
            return True
        if message.get("type") != "http.request":
            continue
        body = message.get("body", b"")
        if not isinstance(body, bytes):
            return False
        total += len(body)
        if total > max_bytes:
            return False
        if message.get("more_body") is not True:
            return True


async def _problem(send, status: int, detail: str, *, authenticate: bool = False) -> None:
    value = {"type": "about:blank", "status": status, "detail": detail[:1000]}
    raw = json.dumps(value, separators=(",", ":")).encode()
    headers = [(b"content-type", b"application/problem+json"), (b"content-length", str(len(raw)).encode())]
    if authenticate:
        headers.append((b"www-authenticate", b"Bearer"))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": raw})


class CloudflareAccessVerifier:
    """Validate Access assertions injected by Cloudflare Managed OAuth.

    Cloudflare owns the OAuth authorization-code/refresh flow. The origin never
    accepts the client's opaque OAuth token as identity; it accepts only a
    signature-verified Access assertion with the configured issuer/audience.
    """

    def __init__(self, *, issuer: str, audience: str, jwks_url: str) -> None:
        if not issuer.startswith("https://") or not jwks_url.startswith("https://"):
            raise ValueError("Cloudflare Access issuer/JWKS must use https")
        if not audience.strip():
            raise ValueError("Cloudflare Access audience must not be empty")
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.jwks_url = jwks_url
        self._keys = PyJWKClient(
            jwks_url,
            cache_keys=True,
            cache_jwk_set=True,
            lifespan=300,
            timeout=8,
        )

    def _verify_sync(self, token: str) -> bool:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256":
                return False
            signing_key = self._keys.get_signing_key_from_jwt(token)
            jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                leeway=30,
                options={"require": ["exp", "iss", "aud"]},
            )
            return True
        except Exception:
            # Authentication is fail-closed. Details are intentionally not
            # surfaced because JWT/JWKS errors may disclose identity metadata.
            return False

    async def verify(self, token: str) -> bool:
        if not token or len(token) > 65536:
            return False
        return await asyncio.to_thread(self._verify_sync, token)


class HybridAuthApp:
    """Accept local operator Bearer OR a verified Cloudflare Access assertion.

    The local token remains a loopback recovery/readiness credential. Public
    OAuth is owned by Cloudflare Access; the origin verifies the assertion that
    Access injects after completing that OAuth flow.
    """

    def __init__(
        self,
        app,
        token: str,
        *,
        body_limit_bytes: int,
        access_verifier: CloudflareAccessVerifier | None = None,
    ) -> None:
        self.app = app
        self.expected = f"Bearer {token}".encode()
        self.body_limit_bytes = body_limit_bytes
        self.access_verifier = access_verifier

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        authorization = b""
        access_assertion = b""
        for name, value in scope.get("headers", []):
            lower = name.lower()
            if lower == b"authorization":
                authorization = value
            elif lower == b"cf-access-jwt-assertion":
                access_assertion = value
        if hmac.compare_digest(authorization, self.expected):
            return await self.app(scope, receive, send)
        if self.access_verifier is not None and access_assertion:
            try:
                encoded = access_assertion.decode("ascii")
            except UnicodeDecodeError:
                encoded = ""
            if encoded and await self.access_verifier.verify(encoded):
                return await self.app(scope, receive, send)
        if not await _drain(receive, max_bytes=self.body_limit_bytes):
            return await _problem(send, 413, "request body exceeds configured limit")
        return await _problem(send, 401, "valid local or Cloudflare Access credential required", authenticate=True)
