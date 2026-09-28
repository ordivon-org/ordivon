from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp_types import CallToolResult, TextContent


class CapabilityAuthorizer(Protocol):
    """Trusted Security adapter used by Gateway only as a policy-enforcement dependency.

    Implementations own neither Gateway routing nor provider effects. They must return the
    existing Security `ordivon.security.gateway-capability-authz` decision shape after
    verifying/normalizing their own evidence provenance.
    """

    async def authorize(
        self,
        *,
        principal_id: str,
        issuer: str,
        requested_capability: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        request_state: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...


def _request_state(ctx: ServerRequestContext[Any, Any]) -> dict[str, Any]:
    request = ctx.request
    scope = getattr(request, "scope", None)
    if not isinstance(scope, dict):
        return {}
    state = scope.get("state")
    return state if isinstance(state, dict) else {}


def _error(code: str, message: str, *, capability: str) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        structuredContent={
            "error": {
                "code": code,
                "message": message,
                "origin": "gateway_capability_authz",
                "capability": capability,
            }
        },
        isError=True,
    )


class GatewayCapabilityAuthorizationMiddleware:
    """Fail-closed PEP for a deliberately narrow set of Gateway tools.

    Identity comes only from trusted request state populated by ingress middleware. Tool
    arguments and MCP `_meta` are never identity/admission authorities. The authorizer is an
    injected Security adapter; Gateway validates the returned decision bindings but does not
    mint Grant/Effect evidence or implement policy semantics.
    """

    DEFAULT_TOOL_CAPABILITIES = {"artifact.read": "artifact.runtime"}

    def __init__(
        self,
        authorizer: CapabilityAuthorizer,
        *,
        tool_capabilities: Mapping[str, str] | None = None,
    ) -> None:
        self._authorizer = authorizer
        self._tool_capabilities = dict(tool_capabilities or self.DEFAULT_TOOL_CAPABILITIES)

    async def __call__(
        self,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        if ctx.method != "tools/call" or not isinstance(ctx.params, dict):
            return await call_next(ctx)

        tool_name = ctx.params.get("name")
        if not isinstance(tool_name, str):
            return await call_next(ctx)
        capability = self._tool_capabilities.get(tool_name)
        if capability is None:
            return await call_next(ctx)

        state = _request_state(ctx)
        principal = state.get("ordivon_access_principal")
        issuer = state.get("ordivon_access_issuer")
        if (
            not isinstance(principal, str)
            or not principal
            or not isinstance(issuer, str)
            or not issuer
        ):
            return _error(
                "CAPABILITY_AUTHZ_INGRESS_IDENTITY_MISSING",
                "Protected capability requires verified ingress identity.",
                capability=capability,
            )

        raw_arguments = ctx.params.get("arguments")
        arguments = dict(raw_arguments) if isinstance(raw_arguments, dict) else {}
        try:
            decision = await self._authorizer.authorize(
                principal_id=principal,
                issuer=issuer,
                requested_capability=capability,
                tool_name=tool_name,
                arguments=arguments,
                request_state=state,
            )
        except Exception:
            return _error(
                "CAPABILITY_AUTHZ_UNAVAILABLE",
                "Security capability authorization did not return a valid decision.",
                capability=capability,
            )

        if not isinstance(decision, Mapping):
            return _error(
                "CAPABILITY_AUTHZ_INVALID",
                "Security capability authorization returned an invalid decision.",
                capability=capability,
            )
        if (
            decision.get("kind") != "ordivon.security.gateway-capability-authz"
            or decision.get("principalId") != principal
            or decision.get("issuer") != issuer
            or decision.get("requestedCapability") != capability
            or decision.get("qualificationTarget") is not True
        ):
            return _error(
                "CAPABILITY_AUTHZ_BINDING_MISMATCH",
                "Security authorization decision does not bind the verified request.",
                capability=capability,
            )

        outcome = decision.get("outcome")
        reason = decision.get("reason")
        if outcome == "ALLOW":
            authority = decision.get("authorityProjection")
            effect = decision.get("effectAdmission")
            if (
                not isinstance(authority, Mapping)
                or not isinstance(effect, Mapping)
                or effect.get("admitted") is not True
            ):
                return _error(
                    "CAPABILITY_AUTHZ_ALLOW_INCOMPLETE",
                    "Security ALLOW decision omitted admitted authority/effect evidence.",
                    capability=capability,
                )
            return await call_next(ctx)
        if outcome == "STEP_UP":
            return _error(
                "CAPABILITY_AUTHZ_STEP_UP_REQUIRED",
                f"Security requires Principal step-up: {reason or 'unspecified'}.",
                capability=capability,
            )
        if outcome == "DENY":
            return _error(
                "CAPABILITY_AUTHZ_DENIED",
                f"Security denied capability: {reason or 'unspecified'}.",
                capability=capability,
            )
        return _error(
            "CAPABILITY_AUTHZ_INVALID_OUTCOME",
            "Security capability authorization returned an unknown outcome.",
            capability=capability,
        )
