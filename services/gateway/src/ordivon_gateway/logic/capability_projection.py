"""Pure projection of Runtime owner observations into Gateway discovery contracts.

No Runtime calls, caching, authority acquisition or persistent source of truth.
The owner response remains a transient read-only projection.
"""

from __future__ import annotations

from typing import Any

from ..contracts import (
    CapabilityDescriptor,
    CapabilityRoute,
)
from .runtime_status import valid_runtime_status_envelope, valid_runtime_target_inventory


def project_execution_capability(
    route: CapabilityRoute,
    *,
    configured_at_gateway: bool,
    owner_response: dict[str, Any] | None,
    observation_error: str | None = None,
    configuration_error: str | None = None,
) -> CapabilityDescriptor:
    """Build an execution capability without interpreting physical Runtime truth."""
    if not configured_at_gateway:
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            configured=False,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error=configuration_error,
            truth_boundary=route.truth_boundary,
        )

    if owner_response is None:
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            configured=True,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error=observation_error or "Runtime status was not observed",
            truth_boundary=route.truth_boundary,
        )

    if not valid_runtime_status_envelope(owner_response):
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            configured=False,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error="invalid versioned Runtime status envelope",
            truth_boundary=route.truth_boundary,
        )

    # The Owner's inventory is evidence, not an ordered route-preference list.
    # A malformed container or duplicate identity is UNKNOWN; accepting the
    # first matching target can incorrectly advertise an executable as ready.
    targets = owner_response.get("targets")
    if not isinstance(targets, list):
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            configured=False,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error="owner returned invalid execution-target inventory",
            truth_boundary=route.truth_boundary,
        )
    matches = [
        item
        for item in targets
        if isinstance(item, dict) and item.get("target") == route.execution_target
    ]
    if len(matches) > 1:
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            configured=False,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error="owner advertised duplicate execution-target identities",
            truth_boundary=route.truth_boundary,
        )
    target = matches[0] if matches else None
    if target is None:
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            configured=False,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error="owner did not advertise the routed execution target",
            truth_boundary=route.truth_boundary,
        )

    configured_status = target.get("configured")
    available_status = target.get("available")
    # Runtime observation is untrusted JSON, not a Python truthiness contract.
    # Invalid or contradictory status is UNKNOWN, never proof of availability.
    if (
        type(configured_status) is not bool
        or type(available_status) is not bool
        or (available_status is True and configured_status is False)
    ):
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            # Invalid Owner data proves neither target configuration nor
            # readiness. Keep legacy configured=False and express UNKNOWN
            # through the independent observation diagnostic.
            configured=False,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error="owner returned invalid execution-target status",
            truth_boundary=route.truth_boundary,
        )

    # Check the whole Owner target inventory AFTER reporting the selected
    # target's precise malformed-status counterexample. A valid selected
    # target can never mask an invalid or duplicate sibling target.
    if not valid_runtime_target_inventory(targets):
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            configured=False,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error="owner returned invalid execution-target inventory",
            truth_boundary=route.truth_boundary,
        )

    # Context inventories are Owner-declared lists. Invalid explicitly supplied
    # types must not crash discovery or be silently projected as a ready route.
    context_fields = (
        ("windowsContexts", "windowsAuthorities")
        if route.execution_target == "windows_native"
        else ("executionProfiles",)
    )
    if any(field in target and not isinstance(target[field], list) for field in context_fields):
        return CapabilityDescriptor(
            capability=route.capability,
            owner_id=route.owner_id,
            category=route.category,
            configured=False,
            available=False,
            context_mode=route.context_mode,  # type: ignore[arg-type]
            observation_error="owner returned invalid execution-context inventory",
            truth_boundary=route.truth_boundary,
        )

    node = owner_response.get("node")
    node_id = (
        str(node["nodeId"])
        if isinstance(node, dict) and isinstance(node.get("nodeId"), str)
        else None
    )
    context_mode = route.context_mode
    if route.execution_target == "windows_native":
        structured_contexts = target.get("windowsContexts")
        if isinstance(structured_contexts, list) and any(
            isinstance(value, dict) for value in structured_contexts
        ):
            contexts = [dict(value) for value in structured_contexts if isinstance(value, dict)]
            context_mode = "provider-defined-json"
        else:
            contexts = [
                str(value)
                for value in target.get("windowsAuthorities", [])
                if isinstance(value, str)
            ]
            context_mode = "provider-defined-string"
    else:
        contexts = [
            str(value) for value in target.get("executionProfiles", []) if isinstance(value, str)
        ]
    return CapabilityDescriptor(
        capability=route.capability,
        owner_id=route.owner_id,
        category=route.category,
        configured=configured_status,
        available=available_status,
        context_mode=context_mode,  # type: ignore[arg-type]
        contexts=contexts,
        owner_node_id=node_id,
        truth_boundary=route.truth_boundary,
    )


def project_native_release_capability(
    route: CapabilityRoute,
    *,
    configured_at_gateway: bool,
    owner_response: dict[str, Any] | None,
    observation_error: str | None = None,
    configuration_error: str | None = None,
) -> CapabilityDescriptor:
    """Read-only Runtime release discovery; never infer the caller's PDP ALLOW.

    This route cannot be positively 'available' from runtime.describe alone:
    it does not attest installed Gateway tools/list, the Runtime original
    ReleaseEffect admission/receipt or the current Principal's Security grant.
    """
    issue = observation_error
    configured = False
    node_id: str | None = None
    if not configured_at_gateway:
        issue = configuration_error or "Linux Runtime Owner endpoint is unconfigured"
    elif owner_response is None:
        issue = issue or "Runtime source/installed release state is not observed"
    elif not valid_runtime_status_envelope(owner_response):
        issue = "invalid native Linux Runtime structured-release status"
    else:
        node = owner_response.get("node")
        targets = owner_response.get("targets")
        enabled = owner_response.get("structuredReleaseConfigured")
        if (
            not isinstance(node, dict)
            or node.get("nodeId") != "linux-pg"
            or node.get("platform") != "linux"
            or node.get("native") is not True
            or not valid_runtime_target_inventory(targets)
            or type(enabled) is not bool
        ):
            issue = "invalid native Linux Runtime structured-release status"
        else:
            node_id = "linux-pg"
            matches = [
                item
                for item in targets
                if isinstance(item, dict) and item.get("target") == "local_linux"
            ]
            target = matches[0] if len(matches) == 1 else None
            if (
                target is None
                or type(target.get("configured")) is not bool
                or type(target.get("available")) is not bool
                or (target["available"] is True and target["configured"] is False)
            ):
                issue = "invalid Linux release target status; readiness UNKNOWN"
            elif enabled is False or target["configured"] is False:
                issue = None  # Exact disabled Runtime/target means NOT_READY.
            else:
                configured = True
                issue = (
                    "Runtime reports structured release configured; installed "
                    "Gateway/Runtime tool identities, authenticated Security "
                    "grant and actual ReleaseEffect readiness are still UNKNOWN"
                )
    return CapabilityDescriptor(
        capability=route.capability,
        owner_id=route.owner_id,
        category=route.category,
        configured=configured,
        available=False,  # No positive grant/installed action truth from owner metadata.
        context_mode=route.context_mode,  # type: ignore[arg-type]
        owner_node_id=node_id,
        observation_error=issue,
        truth_boundary=route.truth_boundary,
    )
