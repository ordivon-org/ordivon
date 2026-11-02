"""Pure projection of Runtime owner observations into Gateway discovery contracts.

No Runtime calls, caching, authority acquisition or persistent source of truth.
The owner response remains a transient read-only projection.
"""

from __future__ import annotations

import re
from typing import Any

from .contracts import (
    CapabilityDescriptor,
    CapabilityProjection,
    CapabilitySearchMatch,
    CapabilitySearchProjection,
)
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


def project_capability_search(
    projection: CapabilityProjection,
    *,
    query: str,
    category: str | None,
    owner_id: str | None,
    limit: int,
    include_unavailable: bool,
) -> CapabilitySearchProjection:
    """Rank one immutable owner observation without I/O or authority decisions."""
    normalized = query.casefold()
    query_tokens = set(re.findall(r"[a-z0-9]+", normalized))
    priority = {"exact": 0, "prefix": 1, "token": 2, "substring": 3}
    ranked: list[tuple[int, str, CapabilitySearchMatch]] = []

    for item in projection.capabilities:
        if category is not None and item.category != category:
            continue
        if owner_id is not None and item.owner_id != owner_id:
            continue
        # An observation error is UNKNOWN owner observation, not proof of owner unavailability.
        if not include_unavailable and not item.available and item.observation_error is None:
            continue

        capability_name = item.capability.casefold()
        corpus_values = [
            item.capability,
            item.category,
            item.owner_id,
            item.description,
            *item.tags,
        ]
        corpus = " ".join(value.casefold() for value in corpus_values if value)
        corpus_tokens = set(re.findall(r"[a-z0-9]+", corpus))

        match_kind: str | None = None
        if normalized == capability_name:
            match_kind = "exact"
        elif capability_name.startswith(normalized):
            match_kind = "prefix"
        elif query_tokens and query_tokens.issubset(corpus_tokens):
            match_kind = "token"
        elif normalized in corpus:
            match_kind = "substring"
        if match_kind is None:
            continue

        match = CapabilitySearchMatch(
            match_kind=match_kind,  # type: ignore[arg-type]
            capability=item,
        )
        ranked.append((priority[match_kind], item.capability, match))

    ranked.sort(key=lambda row: (row[0], row[1]))
    total_matches = len(ranked)
    matches = [row[2] for row in ranked[:limit]]
    return CapabilitySearchProjection(
        query=query,
        projection_digest=projection.projection_digest,
        total_matches=total_matches,
        matches=matches,
    )
