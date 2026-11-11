from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp_types import CallToolResult, TextContent

from .execution_refs import GatewayError, parse_execution_ref
from .service import _SOCIAL_WORK_HOST_TOOLS


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


@dataclass(frozen=True, slots=True)
class HostAccountabilityAuthorizationTarget:
    """A claim about an accountable Actor, NOT proof that a Principal owns it.

    Security alone decides whether a verified Principal may make that claim.
    The resource includes each authorization-relevant untrusted coordinate,
    so a valid decision for one actor/action/filter cannot authorize another.
    """

    capability: str
    resource_type: str
    resource_id: str
    attributes: Mapping[str, Any]

    def authzen_resource(self) -> dict[str, Any]:
        return {
            "type": self.resource_type,
            "id": self.resource_id,
            "properties": dict(self.attributes),
        }


_ACCOUNTABILITY_ACTIONS = frozenset({"offer", "claim", "release", "submit", "review", "cancel"})


def _qualified_host_reference(
    value: object, field: str, *, capability: str = "host.work.engagement"
) -> str:
    if (
        not isinstance(value, str)
        or not 3 <= len(value.encode("utf-8")) <= 512
        or ":" not in value
        or not value.strip()
        or any(unicodedata.category(char) == "Cc" for char in value)
    ):
        raise CapabilityAuthorizationTargetError(
            "CAPABILITY_AUTHZ_TARGET_INVALID",
            f"Work accountability requires a qualified {field}.",
            capability=capability,
        )
    return value


def _resolve_work_engagement_target(
    tool_name: str,
    arguments: Mapping[str, Any],
) -> HostAccountabilityAuthorizationTarget | None:
    """Project a versioned Host write/read onto the existing AuthZEN PEP.

    Unlike a Work Snapshot or caller Tool metadata, none of these fields is
    authorization evidence. No installed Security policy means no admission.
    """
    if tool_name == "work.engagement.advance":
        work_ref = _qualified_host_reference(arguments.get("workRef"), "workRef")
        actor_ref = _qualified_host_reference(arguments.get("actorRef"), "actorRef")
        revision = arguments.get("expectedRevision")
        action = arguments.get("action")
        action_type = action.get("type") if isinstance(action, dict) else None
        if (
            type(revision) is not int
            or not 1 <= revision <= 9_007_199_254_740_991
            or not isinstance(action_type, str)
            or action_type not in _ACCOUNTABILITY_ACTIONS
        ):
            raise CapabilityAuthorizationTargetError(
                "CAPABILITY_AUTHZ_TARGET_INVALID",
                "Work accountability needs a valid expectedRevision and action.type.",
                capability="host.work.engagement.advance",
            )
        if action_type == "offer":
            _qualified_host_reference(action.get("consumerActorRef"), "consumerActorRef")
        if action_type == "review" and (
            not isinstance(action.get("decision"), str)
            or action.get("decision") not in {"accepted", "returned"}
        ):
            raise CapabilityAuthorizationTargetError(
                "CAPABILITY_AUTHZ_TARGET_INVALID",
                "Work accountability review.decision must be accepted or returned.",
                capability="host.work.engagement.advance",
            )
        return HostAccountabilityAuthorizationTarget(
            capability="host.work.engagement.advance",
            resource_type="ordivon.host.work-engagement",
            resource_id="host-engagement:v1:" + _base64url_text(work_ref),
            attributes={
                "identityContract": "ordivon.host-engagement-request-resource.v1",
                "workRef": work_ref,
                "claimedActorRef": actor_ref,
                "expectedRevision": revision,
                "actionType": action_type,
                # These are claims/targets, never attested third-party proofs.
                "requestedConsumerActorRef": action.get("consumerActorRef")
                if action_type == "offer"
                else None,
                "reviewDecision": action.get("decision") if action_type == "review" else None,
            },
        )
    if tool_name == "work.engagement.list":
        assignee = arguments.get("assigneeActorRef")
        consumer = arguments.get("consumerActorRef")
        if assignee is not None:
            assignee = _qualified_host_reference(assignee, "assigneeActorRef")
        if consumer is not None:
            consumer = _qualified_host_reference(consumer, "consumerActorRef")
        phase = arguments.get("phase")
        if phase is not None and (
            not isinstance(phase, str)
            or phase
            not in {
                "offered",
                "claimed",
                "submitted",
                "returned",
                "accepted",
                "cancelled",
            }
        ):
            raise CapabilityAuthorizationTargetError(
                "CAPABILITY_AUTHZ_TARGET_INVALID",
                "Work accountability phase is invalid.",
                capability="host.work.engagement.list",
            )
        return HostAccountabilityAuthorizationTarget(
            capability="host.work.engagement.list",
            resource_type="ordivon.host.work-engagement-inbox",
            resource_id=(
                "host-engagement-inbox:v1:"
                + _base64url_text(assignee or "*")
                + "."
                + _base64url_text(consumer or "*")
            ),
            attributes={
                "identityContract": "ordivon.host-engagement-request-resource.v1",
                "requestedAssigneeActorRef": assignee,
                "requestedConsumerActorRef": consumer,
                "requestedPhase": phase,
            },
        )
    return None


# These original Host projections only read state. Every other Host operation
# in the single Gateway route registry is a write and REQUIRES Security PEP.
# New Owner tools therefore fail closed by default instead of inheriting an
# accidentally public state-changing route.
_HOST_READ_ONLY_TOOLS = frozenset(
    {
        "host.status",
        "work.get",
        "work.list",
        "space.get",
        "space.list",
        "space.participation.list",
        "space.subject.list",
        "topic.cursor.get",
        "topic.list",
        "topic.resume",
        "message.search",
        "message.relation.list",
        "subscription.list",
        "attention.get",
        "attention.delta",
        "attention.reentry",
    }
)


def _legacy_host_mutation_target(
    tool_name: str, arguments: Mapping[str, Any]
) -> HostAccountabilityAuthorizationTarget | None:
    """Single PEP for Host writes lacking versioned Engagement's typed target.

    The whole canonical request is digested, not just the untrusted actorRef:
    a PDP ALLOW for a different Work, role, tool or action cannot be replayed
    by modifying Tool arguments. No Domain validation or authorization is
    reimplemented here. Missing Security remains DENY, not service-bearer ALLOW.
    """
    if tool_name not in _SOCIAL_WORK_HOST_TOOLS or tool_name in _HOST_READ_ONLY_TOOLS:
        return None
    # Message author identity has a different wire field from other Host writers.
    # Never let a supplied ignored actorRef shadow the persisted authorActorRef.
    claimed_actor = (
        arguments.get("authorActorRef")
        if tool_name == "message.post"
        else arguments.get("actorRef")
    )
    _qualified_host_reference(
        claimed_actor,
        "authorActorRef" if tool_name == "message.post" else "actorRef",
        capability="host.legacy-write",
    )
    try:
        canonical = json.dumps(
            arguments,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise CapabilityAuthorizationTargetError(
            "CAPABILITY_AUTHZ_TARGET_INVALID",
            "Host mutation requires a JSON-compatible request.",
            capability="host.legacy-write",
        ) from exc
    if len(canonical) > 4_194_304:
        raise CapabilityAuthorizationTargetError(
            "CAPABILITY_AUTHZ_TARGET_INVALID",
            "Host mutation request exceeds maximum authorization budget.",
            capability="host.legacy-write",
        )
    digest = hashlib.sha256(canonical).hexdigest()
    return HostAccountabilityAuthorizationTarget(
        capability="host.legacy-write",
        resource_type="ordivon.host.legacy-write-request",
        resource_id="host-legacy-write:v1:" + _base64url_text(tool_name) + "." + digest,
        attributes={
            "identityContract": "ordivon.host-legacy-write-resource.v1",
            "toolName": tool_name,
            "requestSha256": digest,
            "claimedActorRef": claimed_actor,
            "workRef": arguments.get("workRef"),
            "spaceRef": arguments.get("spaceRef"),
            "topicRef": arguments.get("topicRef"),
            "messageRef": arguments.get("messageRef"),
            # Requested coordinates are not authorization evidence. The full
            # request digest binds any omitted fields too.
            "sourceMessageRef": arguments.get("sourceMessageRef"),
            "targetRef": arguments.get("targetRef"),
            "targetKind": arguments.get("targetKind"),
            "expectedRevision": arguments.get("expectedRevision"),
            "expectedState": arguments.get("expectedState"),
            "requestedState": arguments.get("state"),
            "requestedStanding": arguments.get("standing"),
        },
    )


class CapabilityAuthorizationTargetError(ValueError):
    def __init__(self, code: str, message: str, *, capability: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.capability = capability


AuthorizationTargetResolver = Callable[
    [str, Mapping[str, Any]],
    CapabilityAuthorizationTarget | HostAccountabilityAuthorizationTarget | None,
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
) -> CapabilityAuthorizationTarget | HostAccountabilityAuthorizationTarget | None:
    """Resolve the protected natural-owner object from trusted Gateway semantics.

    Tool name alone is insufficient: the operation reference must resolve to a
    qualified Runtime owner and artifact. Retired external worker references fail
    closed before reaching Runtime or the authorization provider.
    """

    engagement = _resolve_work_engagement_target(tool_name, arguments)
    if engagement is not None:
        return engagement
    legacy_mutation = _legacy_host_mutation_target(tool_name, arguments)
    if legacy_mutation is not None:
        return legacy_mutation
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
        authorizer: CapabilityAuthorizer | None,
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
            schema_version not in {2, 3}
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
