from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient
from starlette.responses import JSONResponse

logger = logging.getLogger("ordivon_gateway.access_auth")


class AccessAuthError(RuntimeError):
    pass


@dataclass(frozen=True)
class CloudflareAccessConfig:
    issuer: str
    audience: str
    jwks_url: str
    leeway_seconds: int = 30

    def __post_init__(self) -> None:
        if not self.issuer.startswith("https://"):
            raise AccessAuthError("Cloudflare Access issuer must use https")
        if not self.jwks_url.startswith("https://"):
            raise AccessAuthError("Cloudflare Access JWKS URL must use https")
        if not self.audience.strip():
            raise AccessAuthError("Cloudflare Access audience must not be empty")
        if self.leeway_seconds < 0 or self.leeway_seconds > 300:
            raise AccessAuthError("Cloudflare Access leeway must be between 0 and 300 seconds")


@dataclass(frozen=True)
class VerifiedAccessIdentity:
    issuer: str
    subject: str
    principal: str


def _principal(issuer: str, subject: str) -> str:
    digest = hashlib.sha256()
    digest.update(b"ordivon-gateway-cf-access-principal-v1\0")
    digest.update(issuer.encode("utf-8"))
    digest.update(b"\0")
    digest.update(subject.encode("utf-8"))
    return f"principal:cf-access:{digest.hexdigest()}"


class CloudflareAccessVerifier:
    def __init__(
        self,
        config: CloudflareAccessConfig,
        *,
        key_resolver: Callable[[str], Any] | None = None,
    ) -> None:
        self._config = config
        if key_resolver is None:
            client = PyJWKClient(config.jwks_url, cache_jwk_set=True, lifespan=300)

            def resolve_key(token: str) -> Any:
                return client.get_signing_key_from_jwt(token).key

            key_resolver = resolve_key
        self._key_resolver = key_resolver

    def verify_identity(self, token: str) -> VerifiedAccessIdentity:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not header.get("kid"):
                raise AccessAuthError("Cloudflare Access assertion must use RS256 and a key id")
            key = self._key_resolver(token)
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self._config.issuer,
                audience=self._config.audience,
                leeway=self._config.leeway_seconds,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except AccessAuthError:
            raise
        except Exception as exc:
            raise AccessAuthError("invalid Cloudflare Access assertion") from exc

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise AccessAuthError("Cloudflare Access assertion has no usable subject")
        subject = subject.strip()
        return VerifiedAccessIdentity(
            issuer=self._config.issuer,
            subject=subject,
            principal=_principal(self._config.issuer, subject),
        )


class CloudflareAccessMiddleware:
    """Protect MCP business traffic with a verified Cloudflare Access assertion."""

    def __init__(
        self,
        app: Any,
        verifier: Any,
        *,
        protected_path_prefix: str = "/mcp",
    ) -> None:
        self._app = app
        self._verifier = verifier
        self._protected_path_prefix = protected_path_prefix

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http" or not str(scope.get("path", "")).startswith(
            self._protected_path_prefix
        ):
            await self._app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        assertion = headers.get("cf-access-jwt-assertion")
        if not assertion:
            logger.warning(
                "Cloudflare Access assertion missing on protected path=%s",
                scope.get("path"),
            )
            await JSONResponse(
                {"error": "cloudflare_access_required"},
                status_code=403,
            )(scope, receive, send)
            return

        try:
            identity = await asyncio.to_thread(self._verifier.verify_identity, assertion)
        except AccessAuthError as exc:
            cause = type(exc.__cause__).__name__ if exc.__cause__ is not None else "AccessAuthError"
            logger.warning(
                "Cloudflare Access assertion rejected on protected path=%s reason=%s",
                scope.get("path"),
                cause,
            )
            await JSONResponse(
                {"error": "cloudflare_access_invalid"},
                status_code=403,
            )(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        state["ordivon_access_principal"] = identity.principal
        state["ordivon_access_issuer"] = identity.issuer
        await self._app(scope, receive, send)
