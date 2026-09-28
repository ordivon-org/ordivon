from __future__ import annotations

import base64
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp_types import CallToolResult, TextContent

from .service import GatewayError, parse_execution_ref


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


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationTarget:
    """Server-derived authorization target, distinct from caller-authored Tool arguments."""

    capability: str
    resource_type: str
    resource_id: str
    operation_ref: str
    owner_id: str
    job_id: str
    artifact_id: str

    def authzen_resource(self) -> dict[str, Any]:
        return {
            "type": self.resource_type,
            "id": self.resource_id,
            "properties": {
                "identityContract": "ordivon.runtime-artifact-resource-key.v1",
                "operationRef": self.operation_ref,
                "ownerId": self.owner_id,
                "jobId": self.job_id,
                "artifactId": self.artifact_id,
            },
        }


class CapabilityAuthorizationTargetError(ValueError):
    def __init__(self, code: str, message: str, *, capability: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.capability = capability


AuthorizationTargetResolver = Callable[
    [str, Mapping[str, Any]], CapabilityAuthorizationTarget | None
]

_RUNTIME_ARTIFACT_OWNERS = frozenset({"runtime.linux", "runtime.windows"})


def _base64url_text(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _artifact_resource_id(operation_ref: str, artifact_id: str) -> str:
    """Collision-free public object id from two already-validated UTF-8 coordinates.

    RFC 4648 base64url segments avoid delimiter ambiguity while preserving useful prefixes:
    all Runtime artifacts share ``runtime-artifact:v1:`` and all artifacts for one operation
    share the encoded operationRef segment.
    """

    return (
        "runtime-artifact:v1:" + _base64url_text(operation_ref) + "." + _base64url_text(artifact_id)
    )


def _validate_artifact_id(value: object) -> str:
    if not isinstance(value, str):
        raise CapabilityAuthorizationTargetError(
            "CAPABILITY_AUTHZ_TARGET_INVALID",
            "artifact.read requires a string artifactId before authorization.",
            capability="artifact.runtime",
        )
    encoded = value.encode("utf-8")
    if (
        not value.strip()
        or len(encoded) > 256
        or "\x00" in value
        or any(unicodedata.category(ch) == "Cc" for ch in value)
    ):
        raise CapabilityAuthorizationTargetError(
            "CAPABILITY_AUTHZ_TARGET_INVALID",
            "artifact.read artifactId is outside the Runtime identifier contract.",
            capability="artifact.runtime",
        )
    return value


def resolve_authorization_target(
    tool_name: str, arguments: Mapping[str, Any]
) -> CapabilityAuthorizationTarget | None:
    """Resolve the protected natural-owner object from trusted Gateway semantics.

    Tool name alone is intentionally insufficient: ``artifact.read`` also routes external.pull
    artifacts. Until Security defines an external-artifact policy target, those calls fail closed
    whenever this PEP is enabled instead of being mislabeled as ``artifact.runtime``.
    """

    if tool_name != "artifact.read":
        return None

    operation_ref = arguments.get("operationRef")
    if not isinstance(operation_ref, str) or not operation_ref:
        raise CapabilityAuthorizationTargetError(
            "CAPABILITY_AUTHZ_TARGET_INVALID",
            "artifact.read requires a valid operationRef before authorization.",
            capability="artifact.runtime",
        )
    try:
        owner_id, native_id = parse_execution_ref(operation_ref)
    except GatewayError as exc:
        raise CapabilityAuthorizationTargetError(
            "CAPABILITY_AUTHZ_TARGET_INVALID",
            "artifact.read operationRef is not a valid Gateway execution reference.",
            capability="artifact.runtime",
        ) from exc

    if owner_id not in _RUNTIME_ARTIFACT_OWNERS:
        raise CapabilityAuthorizationTargetError(
            "CAPABILITY_AUTHZ_TARGET_UNQUALIFIED",
            "No Security authorization target is qualified for this artifact owner.",
        )

    artifact_id = _validate_artifact_id(arguments.get("artifactId"))
    return CapabilityAuthorizationTarget(
        capability="artifact.runtime",
        resource_type="ordivon.runtime.artifact",
        resource_id=_artifact_resource_id(operation_ref, artifact_id),
        operation_ref=operation_ref,
        owner_id=owner_id,
        job_id=native_id,
        artifact_id=artifact_id,
    )


def _request_state(ctx: ServerRequestContext[Any, Any]) -> dict[str, Any]:
    request = ctx.request
    scope = getattr(request, "scope", None)
    if not isinstance(scope, dict):
        return {}
    state = scope.get("state")
    return state if isinstance(state, dict) else {}


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
    """Fail-closed PEP for a deliberately narrow set of Gateway owner objects.

    Identity comes only from trusted request state populated by ingress middleware. Tool
    arguments and MCP ``_meta`` are never identity/admission authorities. Protected targets
    are resolved server-side from the Gateway's own routing/reference semantics before the
    Security adapter is called.
    """

    def __init__(
        self,
        authorizer: CapabilityAuthorizer,
        *,
        target_resolver: AuthorizationTargetResolver = resolve_authorization_target,
    ) -> None:
        self._authorizer = authorizer
        self._target_resolver = target_resolver

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
        if (
            decision.get("schemaVersion") != 2
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
