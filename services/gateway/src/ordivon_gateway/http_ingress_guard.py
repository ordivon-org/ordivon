"""A small reference-monitor boundary for HTTP MCP calls.

This checks authenticated ingress identity, not resource authorization.  The
natural Owner still enforces its own operations and Security owns PDP truth.
An unrecognized Tool is *protected* by default, never silently made public.
"""

from __future__ import annotations

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp_types import CallToolResult, TextContent

from .capability_authz import _request_state

# Only explicitly reviewed non-sensitive discovery functions are anonymous.
# This is NOT a permission list for executable or Host objects.
PUBLIC_METADATA_TOOLS = frozenset({"system.describe", "capability.describe", "capability.search"})


def needs_verified_ingress(tool_name: str) -> bool:
    return tool_name not in PUBLIC_METADATA_TOOLS


class GatewayHTTPIngressGuard:
    """Enforce verified HTTP Principal state before any protected Owner call."""

    async def __call__(
        self,
        ctx: ServerRequestContext,
        call_next: CallNext,
    ) -> HandlerResult:
        if ctx.method != "tools/call":
            return await call_next(ctx)
        params = ctx.params
        tool_name = params.get("name") if isinstance(params, dict) else None
        if isinstance(tool_name, str) and not needs_verified_ingress(tool_name):
            return await call_next(ctx)

        # Ingress middleware owns these request-local coordinates. Caller Tool
        # arguments, _meta, headers echoed inside the Tool, etc. are not proof.
        state = _request_state(ctx)
        principal = state.get("ordivon_access_principal")
        issuer = state.get("ordivon_access_issuer")
        if not (isinstance(principal, str) and principal and isinstance(issuer, str) and issuer):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Protected HTTP tool requires verified ingress Principal identity.",
                    )
                ],
                structuredContent={
                    "error": {
                        "code": "HTTP_INGRESS_IDENTITY_MISSING",
                        "origin": "gateway_http_ingress_guard",
                        "message": "Protected HTTP tool requires verified ingress Principal identity.",
                    }
                },
                isError=True,
            )
        return await call_next(ctx)
