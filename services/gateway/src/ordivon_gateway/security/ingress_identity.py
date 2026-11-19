"""One request-local identity view shared by Gateway ingress consumers.

Only the configured HTTP ingress middleware can populate these scope.state
coordinates with *verified* identity. This pure reader neither authenticates
a caller nor accepts identity from MCP Tool arguments, _meta or JWT claims.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from mcp.server.context import ServerRequestContext
from mcp.server.mcpserver import Context


@dataclass(frozen=True, slots=True)
class IngressIdentity:
    principal: str
    issuer: str


def _state_from_scope(scope: object) -> dict[str, Any]:
    if not isinstance(scope, dict):
        return {}
    state = scope.get("state")
    return state if isinstance(state, dict) else {}


def request_state(ctx: ServerRequestContext[Any, Any]) -> dict[str, Any]:
    """Normal MCP Middleware request; no fallback to caller parameters."""
    return _state_from_scope(getattr(getattr(ctx, "request", None), "scope", None))


def tool_context_state(context: Context | None) -> dict[str, Any]:
    """MCP Tool callback Context, whose SDK request_context may be unavailable."""
    try:
        request = context.request_context.request
    except AttributeError, ValueError:
        return {}
    return _state_from_scope(getattr(request, "scope", None))


def identity_from_state(state: Mapping[str, Any]) -> IngressIdentity | None:
    """Qualify ingress-produced coordinates, not a user-authentication decision."""
    principal = state.get("ordivon_access_principal")
    issuer = state.get("ordivon_access_issuer")
    if (
        not isinstance(principal, str)
        or not principal.strip()
        or not isinstance(issuer, str)
        or not issuer.strip()
    ):
        return None
    return IngressIdentity(principal=principal, issuer=issuer)
