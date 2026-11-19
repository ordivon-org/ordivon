"""One wiring point for Gateway ingress identity and capability policy.

Only this module interprets authorization environment variables or installs
permission middlewares. Business MCP tools do not select their own security
implementation. Behavior is intentionally unchanged by the extraction.
"""

from __future__ import annotations

import os

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

from .access_auth import (
    CloudflareAccessConfig,
    CloudflareAccessMiddleware,
    CloudflareAccessVerifier,
)
from .authzen_authorizer import AuthZenPrincipalAuthorizer
from .capability_authz import CapabilityAuthorizer, GatewayCapabilityAuthorizationMiddleware
from .execution_access import require_http_execution_identity
from .http_ingress_guard import GatewayHTTPIngressGuard
from .owner_identity import _read_private_secret_file


def install_tool_security(
    server: MCPServer,
    *,
    capability_authorizer: CapabilityAuthorizer | None,
    protect_artifact_reads: bool,
    require_http_execution_identity: bool,
) -> None:
    """Order access identity before target authorization; deny if PDP absent."""
    if require_http_execution_identity:
        server.middleware.append(GatewayHTTPIngressGuard())
    if (
        capability_authorizer is not None
        or protect_artifact_reads
        or require_http_execution_identity
    ):
        server.middleware.append(GatewayCapabilityAuthorizationMiddleware(capability_authorizer))


def require_release_access(
    context: Context | None,
    require_verified_http: bool,
    authorizer: CapabilityAuthorizer | None,
) -> None:
    """Do not release Runtime from an unauthenticated/stdio-only request."""
    require_http_execution_identity(context)
    if not require_verified_http or authorizer is None:
        raise ToolError("Runtime release requires a configured HTTP Security PEP")


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise RuntimeError(f"{name} must be true or false")


def access_verifier_from_env() -> CloudflareAccessVerifier | None:
    if not _bool_env("ORDIVON_GATEWAY_TRUST_CF_ACCESS"):
        return None
    issuer = os.environ.get("ORDIVON_GATEWAY_CF_ACCESS_ISSUER", "").strip().rstrip("/")
    audience = os.environ.get("ORDIVON_GATEWAY_CF_ACCESS_AUDIENCE", "").strip()
    if not issuer or not audience:
        raise RuntimeError("Gateway Cloudflare Access trust requires issuer and audience")
    jwks_url = os.environ.get(
        "ORDIVON_GATEWAY_CF_ACCESS_JWKS_URL",
        f"{issuer}/cdn-cgi/access/certs",
    ).strip()
    return CloudflareAccessVerifier(
        CloudflareAccessConfig(
            issuer=issuer,
            audience=audience,
            jwks_url=jwks_url,
        )
    )


def capability_authorizer_from_env() -> CapabilityAuthorizer | None:
    endpoint = os.environ.get("ORDIVON_GATEWAY_AUTHZEN_EVALUATION_ENDPOINT", "").strip()
    token_file = os.environ.get("ORDIVON_GATEWAY_AUTHZEN_BEARER_TOKEN_FILE", "").strip()
    if bool(endpoint) != bool(token_file):
        raise RuntimeError(
            "Gateway AuthZEN requires both evaluation endpoint and private token file"
        )
    if not endpoint:
        return None
    return AuthZenPrincipalAuthorizer(
        endpoint,
        bearer_token_provider=lambda: _read_private_secret_file(
            token_file, "Gateway AuthZEN bearer token"
        ),
    )


def protect_http_app(
    app: object,
    *,
    access_verifier: CloudflareAccessVerifier | None,
    path: str,
    local_bearer_token_file: str | None,
) -> object:
    if access_verifier is not None or local_bearer_token_file is not None:
        return CloudflareAccessMiddleware(
            app,
            access_verifier,
            protected_path_prefix=path,
            local_bearer_token_file=local_bearer_token_file,
        )
    return app
