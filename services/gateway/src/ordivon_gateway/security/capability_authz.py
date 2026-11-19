"""Gateway Security policy enforcement over separately projected Owner targets."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp_types import CallToolResult, TextContent

from .authorization_targets import (
    AuthorizationTargetResolver,
    CapabilityAuthorizationTargetError,
    resolve_authorization_target,
)
from .ingress_identity import identity_from_state, request_state
from .trusted_operator import TrustedCloudflareOperator


class CapabilityAuthorizer(Protocol):
    """Trusted Security adapter used by Gateway only as a policy-enforcement dependency.

    Implementations own neither Gateway routing nor provider effects. They must return the
    Security ``ordivon.security.gateway-capability-authz`` decision shape after
    verifying/normalizing their own evidence provenance. ``requested_resource`` is a
    Gateway-derived object coordinate; callers may not replace it with parallel identity or
    admission claims in Tool arguments.
    """

    async def authorize(
        self,
        *,
        principal_id: str,
        issuer: str,
        requested_capability: str,
        requested_resource: Mapping[str, Any],
        tool_name: str,
        arguments: Mapping[str, Any],
        request_state: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...


def _error(code: str, message: str, *, capability: str | None) -> CallToolResult:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "origin": "gateway_capability_authz",
    }
    if capability is not None:
        error["capability"] = capability
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        structuredContent={"error": error},
        isError=True,
    )


class GatewayCapabilityAuthorizationMiddleware:
    """Verified Cloudflare operator or delegated AuthZEN object PEP.

    Identity comes only from trusted request state populated by ingress middleware. Tool
    arguments and MCP ``_meta`` are never identity/admission authorities. Protected targets
    are resolved server-side from the Gateway's own routing/reference semantics before the
    Security adapter is called.
    """

    def __init__(
        self,
        authorizer: CapabilityAuthorizer | None,
        *,
        target_resolver: AuthorizationTargetResolver = resolve_authorization_target,
        trusted_operator: TrustedCloudflareOperator | None = None,
    ) -> None:
        self._authorizer = authorizer
        self._target_resolver = target_resolver
        self._trusted_operator = trusted_operator

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
        raw_arguments = ctx.params.get("arguments")
        arguments = dict(raw_arguments) if isinstance(raw_arguments, dict) else {}
        try:
            target = self._target_resolver(tool_name, arguments)
        except CapabilityAuthorizationTargetError as exc:
            return _error(exc.code, str(exc), capability=exc.capability)
        if target is None:
            return await call_next(ctx)

        capability = target.capability
        resource = target.authzen_resource()
        state = request_state(ctx)
        identity = identity_from_state(state)
        if identity is None:
            return _error(
                "CAPABILITY_AUTHZ_INGRESS_IDENTITY_MISSING",
                "Protected capability requires verified ingress identity.",
                capability=capability,
            )

        principal, issuer = identity.principal, identity.issuer
        # The verified Cloudflare App policy is the operator's entitlement
        # boundary when explicitly selected. A second object-by-object PDP
        # must not deny an already verified trusted operator. Host/Runtime
        # native owner checks and the canonical request target still apply.
        if self._trusted_operator is not None and self._trusted_operator.allows(state):
            return await call_next(ctx)
        if self._authorizer is None:
            return _error(
                "CAPABILITY_AUTHZ_UNAVAILABLE",
                "Protected capability requires an installed Security authorizer.",
                capability=capability,
            )

        try:
            decision = await self._authorizer.authorize(
                principal_id=principal,
                issuer=issuer,
                requested_capability=capability,
                requested_resource=resource,
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
        schema_version = decision.get("schemaVersion")
        if (
            type(schema_version) is not int
            or schema_version not in {2, 3}
            or decision.get("kind") != "ordivon.security.gateway-capability-authz"
            or decision.get("principalId") != principal
            or decision.get("issuer") != issuer
            or decision.get("requestedCapability") != capability
            or decision.get("requestedResource") != resource
            or decision.get("qualificationTarget") is not True
        ):
            return _error(
                "CAPABILITY_AUTHZ_BINDING_MISMATCH",
                "Security authorization decision does not bind the verified request object.",
                capability=capability,
            )

        outcome = decision.get("outcome")
        reason = decision.get("reason")
        if outcome == "ALLOW":
            if schema_version == 2:
                authority = decision.get("authorityProjection")
                effect = decision.get("effectAdmission")
                if (
                    not isinstance(authority, Mapping)
                    or not isinstance(effect, Mapping)
                    or effect.get("admitted") is not True
                ):
                    return _error(
                        "CAPABILITY_AUTHZ_ALLOW_INCOMPLETE",
                        "Delegated-Agent ALLOW omitted admitted authority/effect evidence.",
                        capability=capability,
                    )
            else:
                evidence = decision.get("authorizationEvidence")
                if (
                    decision.get("authorizationProfile") != "interactive-principal-authzen"
                    or not isinstance(evidence, Mapping)
                    or evidence.get("standard") != "openid-authzen-authorization-api-1.0"
                    or evidence.get("decision") is not True
                    or not isinstance(evidence.get("requestId"), str)
                    or not evidence["requestId"].strip()
                    or evidence.get("responseRequestId") != evidence.get("requestId")
                    or decision.get("authorityProjection") is not None
                    or decision.get("effectAdmission") is not None
                ):
                    return _error(
                        "CAPABILITY_AUTHZ_ALLOW_INCOMPLETE",
                        "Interactive Principal ALLOW omitted valid AuthZEN evidence.",
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
