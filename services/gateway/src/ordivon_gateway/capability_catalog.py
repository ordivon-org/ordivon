from __future__ import annotations

import asyncio
import hashlib
import json
from importlib.metadata import version as package_version
from typing import Any

from .capability_projection import project_capability_search, project_execution_capability
from .contracts import (
    CapabilityDescriptor,
    CapabilityProjection,
    CapabilityResolution,
    CapabilitySearchProjection,
    OwnerDescriptor,
    SystemDescription,
)
from .execution_refs import GatewayError
from .owner_protocol import _configuration_error, _configured
from .research_resolution import resolve_research_capability
from .routing import CapabilityRoute
from .upstream import OwnerToolCaller

_OWNER_ROLES = {
    "runtime.linux": "physical execution owner",
    "runtime.windows": "physical execution owner",
    "host": "external semantic continuity owner",
    "skills": "procedural Skill discovery and exact binding owner",
    "research.composition": "non-authoritative Research composition metadata",
}


class CapabilityCatalog:
    """Read-only capability discovery and composition resolution over natural owners.

    This catalog observes owners but never owns their execution, state or completion.
    The GatewayService API is a compatibility façade over this boundary.
    """

    def __init__(
        self,
        caller: OwnerToolCaller,
        routes: dict[str, CapabilityRoute],
        projection_timeout_seconds: float,
    ) -> None:
        self._caller = caller
        self._routes = routes
        self._projection_timeout_seconds = projection_timeout_seconds

    def system_describe(self) -> SystemDescription:
        owners = [
            OwnerDescriptor(
                owner_id=owner_id,
                role=role,
                configured=(
                    True
                    if owner_id == "research.composition"
                    else _configured(self._caller, owner_id)
                ),
            )
            for owner_id, role in _OWNER_ROLES.items()
        ]
        capabilities = set(self._routes)
        return SystemDescription(
            gateway_version=package_version("ordivon-gateway"),
            owners=owners,
            capabilities=sorted(capabilities),
        )

    async def capability_describe(self, capability: str | None = None) -> CapabilityProjection:
        # Discovery and dispatch share the same natural-owner route table.
        if capability is not None:
            route = self._routes.get(capability)
            if route is None:
                raise GatewayError(f"unknown capability: {capability}")
            selected = [route]
        else:
            selected = [self._routes[key] for key in sorted(self._routes)]

        runtime_cache: dict[str, tuple[dict[str, Any] | None, str | None]] = {}

        async def observe_owner(
            owner_id: str, tool_name: str, arguments: dict[str, Any]
        ) -> tuple[dict[str, Any] | None, str | None]:
            # Read-only observation timeout => UNKNOWN owner readiness.
            # No invented unavailable truth and no cross-request cache.
            started = asyncio.get_running_loop().time()
            try:
                async with asyncio.timeout(self._projection_timeout_seconds):
                    result = await self._caller.call_tool(owner_id, tool_name, arguments)
                return result, None
            except TimeoutError:
                elapsed_ms = int((asyncio.get_running_loop().time() - started) * 1000)
                return (
                    None,
                    f"TimeoutError: observation {owner_id}/{tool_name} timed out "
                    f"after {elapsed_ms}ms (budget={self._projection_timeout_seconds:g}s); "
                    "Owner readiness UNKNOWN",
                )
            except Exception as exc:
                return None, f"{type(exc).__name__}: {str(exc)[:240]}"

        async def runtime_description(
            owner_id: str,
        ) -> tuple[dict[str, Any] | None, str | None]:
            cached = runtime_cache.get(owner_id)
            if cached is not None:
                return cached
            if not _configured(self._caller, owner_id):
                value = (None, None)
                runtime_cache[owner_id] = value
                return value
            value = await observe_owner(owner_id, "runtime.describe", {"schemaVersion": 1})
            runtime_cache[owner_id] = value
            return value

        async def execution_descriptor(route: CapabilityRoute) -> CapabilityDescriptor:
            configured = _configured(self._caller, route.owner_id)
            if not configured:
                return project_execution_capability(
                    route,
                    configured_at_gateway=False,
                    owner_response=None,
                    configuration_error=_configuration_error(self._caller, route.owner_id),
                )
            response, error = await runtime_description(route.owner_id)
            return project_execution_capability(
                route,
                configured_at_gateway=True,
                owner_response=response,
                observation_error=error,
            )

        # Only independent read-only observations fan out. TaskGroup keeps child
        # lifetimes inside this request; no cross-request cache or effect retry.
        runtime_owners = {route.owner_id for route in selected if route.category == "execution"}
        if any(route.capability == "artifact.runtime" for route in selected):
            runtime_owners.update(("runtime.linux", "runtime.windows"))
        host_probe = None
        async with asyncio.TaskGroup() as probes:
            for owner_id in sorted(runtime_owners):
                probes.create_task(runtime_description(owner_id))
            if any(route.capability == "continuity.external" for route in selected) and _configured(
                self._caller, "host"
            ):
                host_probe = probes.create_task(
                    observe_owner("host", "host.status", {"detail": "summary"})
                )

        values: list[CapabilityDescriptor] = []
        for route in selected:
            if route.category == "execution":
                values.append(await execution_descriptor(route))
                continue

            if route.category == "research":
                values.append(
                    CapabilityDescriptor(
                        capability=route.capability,
                        owner_id=route.owner_id,
                        category=route.category,
                        configured=True,
                        # Local Research metadata is queryable/resolvable; this
                        # does not establish live provider readiness.
                        available=False,
                        context_mode=route.context_mode,  # type: ignore[arg-type]
                        observation_error=(
                            "Research composition route only; live provider readiness "
                            "UNKNOWN. Use capability.resolve for advisory selection."
                        ),
                        truth_boundary=route.truth_boundary,
                    )
                )
                continue

            if route.capability == "continuity.external":
                configured = _configured(self._caller, "host")
                available = False
                error: str | None = None
                if host_probe is not None:
                    result, error = host_probe.result()
                    available = result is not None
                values.append(
                    CapabilityDescriptor(
                        capability=route.capability,
                        owner_id=route.owner_id,
                        category=route.category,
                        configured=configured,
                        available=available,
                        context_mode=route.context_mode,  # type: ignore[arg-type]
                        observation_error=error,
                        truth_boundary=route.truth_boundary,
                    )
                )
                continue

            if route.capability == "artifact.runtime":
                nodes: list[str] = []
                available = False
                any_configured = False
                errors: list[str] = []
                for owner_id in ("runtime.linux", "runtime.windows"):
                    if not _configured(self._caller, owner_id):
                        configuration_error = _configuration_error(self._caller, owner_id)
                        if configuration_error is not None:
                            errors.append(f"{owner_id}: {configuration_error}")
                        continue
                    any_configured = True
                    result, error = await runtime_description(owner_id)
                    if error is not None:
                        errors.append(f"{owner_id}: {error}")
                        continue
                    if result is None:
                        continue
                    node = result.get("node")
                    node_id = (
                        str(node["nodeId"])
                        if isinstance(node, dict) and isinstance(node.get("nodeId"), str)
                        else None
                    )
                    targets = result.get("targets")
                    # An ill-typed or contradictory Owner projection is UNKNOWN.
                    # Never promote truthy strings or integers into Runtime truth.
                    if not isinstance(targets, list) or any(
                        not isinstance(item, dict)
                        or type(item.get("configured")) is not bool
                        or type(item.get("available")) is not bool
                        or (item.get("available") is True and item.get("configured") is False)
                        for item in targets
                    ):
                        errors.append(f"{owner_id}: invalid Runtime target status projection")
                        continue
                    owner_available = any(
                        item["configured"] is True and item["available"] is True for item in targets
                    )
                    if owner_available:
                        available = True
                        if node_id is not None:
                            nodes.append(node_id)
                values.append(
                    CapabilityDescriptor(
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
                )
                continue

            values.append(
                CapabilityDescriptor(
                    capability=route.capability,
                    owner_id=route.owner_id,
                    category=route.category,
                    configured=False,
                    available=False,
                    context_mode=route.context_mode,  # type: ignore[arg-type]
                    observation_error="no projection adapter for capability",
                    truth_boundary=route.truth_boundary,
                )
            )

        enriched: list[CapabilityDescriptor] = []
        for value in values:
            route = self._routes.get(value.capability)
            if route is None:
                enriched.append(value)
                continue
            enriched.append(
                value.model_copy(
                    update={
                        "description": route.description,
                        "tags": list(route.tags),
                    }
                )
            )
        values = enriched

        payload = [value.model_dump(mode="json") for value in values]
        digest = (
            "sha256:"
            + hashlib.sha256(
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()
        )
        return CapabilityProjection(
            projection_digest=digest,
            capabilities=values,
        )

    async def capability_search(
        self,
        *,
        query: str,
        category: str | None = None,
        owner_id: str | None = None,
        limit: int = 10,
        include_unavailable: bool = True,
    ) -> CapabilitySearchProjection:
        if not isinstance(query, str) or query != query.strip() or not query:
            raise GatewayError("query must be non-empty trimmed text")
        if len(query) > 512:
            raise GatewayError("query exceeds 512 characters")
        if category is not None and (
            not isinstance(category, str) or category != category.strip() or not category
        ):
            raise GatewayError("category must be non-empty trimmed text when provided")
        if owner_id is not None and (
            not isinstance(owner_id, str) or owner_id != owner_id.strip() or not owner_id
        ):
            raise GatewayError("ownerId must be non-empty trimmed text when provided")
        if type(limit) is not int or not 1 <= limit <= 50:
            raise GatewayError("limit must be an integer between 1 and 50")
        if type(include_unavailable) is not bool:
            raise GatewayError("includeUnavailable must be boolean")

        projection = await self.capability_describe()
        return project_capability_search(
            projection,
            query=query,
            category=category,
            owner_id=owner_id,
            limit=limit,
            include_unavailable=include_unavailable,
        )

    async def capability_resolve(
        self,
        *,
        capability: str,
        workspace_id: str | None = None,
        agent_id: str | None = None,
    ) -> CapabilityResolution:
        return await resolve_research_capability(
            self._caller,
            self._routes,
            capability=capability,
            workspace_id=workspace_id,
            agent_id=agent_id,
        )
