"""Pure projection of Runtime owner observations into Gateway discovery contracts.

No Runtime calls, caching, authority acquisition or persistent source of truth.
The owner response remains a transient read-only projection.
"""

from __future__ import annotations

from typing import Any

from .contracts import CapabilityDescriptor
from .routes import CapabilityRoute


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
            observation_error=observation_error,
            truth_boundary=route.truth_boundary,
        )

    target = next(
        (
            item
            for item in owner_response.get("targets", [])
            if isinstance(item, dict) and item.get("target") == route.execution_target
        ),
        None,
    )
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
        configured=bool(target.get("configured", False)),
        available=bool(target.get("available", False)),
        context_mode=context_mode,  # type: ignore[arg-type]
        contexts=contexts,
        owner_node_id=node_id,
        truth_boundary=route.truth_boundary,
    )
