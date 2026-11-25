"""Pure capability catalog projections from explicit request-local evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..contracts import CapabilityDescriptor, CapabilityProjection, CapabilityRoute
from .catalog_identity import digest_json
from .readiness_inquiry import project_readiness_inquiry
from .runtime_status import valid_runtime_status_envelope, valid_runtime_target_inventory


def project_host_capability(
    route: CapabilityRoute,
    *,
    configured: bool,
    result: dict[str, Any] | None,
    error: str | None,
) -> CapabilityDescriptor:
    available = False
    if result is not None:
        available = (
            isinstance(result, dict)
            and type(result.get("schemaVersion")) is int
            and result["schemaVersion"] == 3
            and result.get("kind") == "ordivon.host-status"
        )
        if not available:
            error = "invalid Host status projection"
    return CapabilityDescriptor(
        capability=route.capability,
        owner_id=route.owner_id,
        category=route.category,
        configured=configured,
        available=available,
        context_mode=route.context_mode,  # type: ignore[arg-type]
        observation_error=error,
        truth_boundary=route.truth_boundary,
    )


def project_artifact_capability(
    route: CapabilityRoute,
    *,
    observations: list[tuple[str, bool, dict[str, Any] | None, str | None]],
) -> CapabilityDescriptor:
    """Aggregate only qualified Runtime status inventories, not Artifact truth."""
    nodes: list[str] = []
    available = False
    any_configured = False
    errors: list[str] = []
    for owner_id, configured, result, error in observations:
        if error is not None:
            errors.append(f"{owner_id}: {error}")
        if not configured:
            continue
        any_configured = True
        if error is not None or result is None:
            continue
        if not valid_runtime_status_envelope(result):
            errors.append(f"{owner_id}: invalid versioned Runtime status envelope")
            continue
        node = result.get("node")
        node_id = (
            str(node["nodeId"])
            if isinstance(node, dict) and isinstance(node.get("nodeId"), str)
            else None
        )
        targets = result.get("targets")
        if not valid_runtime_target_inventory(targets):
            errors.append(f"{owner_id}: invalid Runtime target status projection")
            continue
        if any(item["configured"] is True and item["available"] is True for item in targets):
            available = True
            if node_id is not None:
                nodes.append(node_id)
    return CapabilityDescriptor(
        capability=route.capability,
        owner_id=route.owner_id,
        category=route.category,
        configured=any_configured,
        available=available,
        context_mode=route.context_mode,  # type: ignore[arg-type]
        owner_node_ids=sorted(set(nodes)),
        observation_error="; ".join(errors) if errors else None,
        truth_boundary=route.truth_boundary,
    )


def project_static_capability(route: CapabilityRoute) -> CapabilityDescriptor:
    research = route.category == "research"
    return CapabilityDescriptor(
        capability=route.capability,
        owner_id=route.owner_id,
        category=route.category,
        configured=research,
        available=False,
        context_mode=route.context_mode,  # type: ignore[arg-type]
        observation_error=(
            "Research composition route only; live provider readiness "
            "UNKNOWN. Use capability.resolve for advisory selection."
            if research
            else "no projection adapter for capability"
        ),
        truth_boundary=route.truth_boundary,
    )


def assemble_catalog_projection(
    values: list[CapabilityDescriptor],
    routes: Mapping[str, CapabilityRoute],
    *,
    route_identity: str,
    owner_configurations: dict[str, tuple[bool, str | None]],
    owner_observations: dict[str, tuple[dict[str, Any] | None, str | None]],
) -> CapabilityProjection:
    """Enrich from the same evidence; never re-observe an Owner."""
    enriched: list[CapabilityDescriptor] = []
    for value in values:
        route = routes.get(value.capability)
        if route is None:
            enriched.append(value)
            continue
        descriptor = value.model_copy(
            update={"description": route.description, "tags": list(route.tags)}
        )
        descriptor._readiness_inquiry = project_readiness_inquiry(
            descriptor,
            route,
            owner_configurations=owner_configurations,
            owner_observations=owner_observations,
        )
        enriched.append(descriptor)
    return CapabilityProjection(
        projection_digest=digest_json([value.model_dump(mode="json") for value in enriched]),
        route_digest=route_identity,
        capabilities=enriched,
    )
