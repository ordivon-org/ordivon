from __future__ import annotations

import asyncio
import hashlib
import json
import re
from importlib.metadata import version as package_version
from typing import Any

from .capability_projection import project_execution_capability
from .contracts import (
    CapabilityDescriptor,
    CapabilityInvocationRecipe,
    CapabilityProjection,
    CapabilityResolution,
    CapabilitySearchMatch,
    CapabilitySearchProjection,
    CapabilitySkillBinding,
    OwnerDescriptor,
    SystemDescription,
)
from .execution_refs import GatewayError
from .external_worker import ExternalPullWorkerTransport
from .owner_protocol import _configuration_error, _configured, _required_str
from .research_routes import research_capabilities
from .routing import CapabilityRoute
from .upstream import OwnerToolCaller

_OWNER_ROLES = {
    "runtime.linux": "physical execution owner",
    "runtime.windows": "physical execution owner",
    "host": "external semantic continuity owner",
    "skills": "procedural Skill discovery and exact binding owner",
    "research.composition": "non-authoritative Research composition metadata",
    "external.pull": "provider-neutral outbound pull execution transport",
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
        external_workers: ExternalPullWorkerTransport | None,
        projection_timeout_seconds: float,
    ) -> None:
        self._caller = caller
        self._routes = routes
        self._external_workers = external_workers
        self._projection_timeout_seconds = projection_timeout_seconds

    def system_describe(self) -> SystemDescription:
        owners = [
            OwnerDescriptor(
                owner_id=owner_id,
                role=role,
                configured=(
                    True
                    if owner_id == "research.composition"
                    else self._external_workers is not None
                    if owner_id == "external.pull"
                    else _configured(self._caller, owner_id)
                ),
            )
            for owner_id, role in _OWNER_ROLES.items()
            if owner_id != "external.pull" or self._external_workers is not None
        ]
        capabilities = set(self._routes)
        if self._external_workers is not None:
            capabilities.update(self._external_workers.capability_projection())
        return SystemDescription(
            gateway_version=package_version("ordivon-gateway"),
            owners=owners,
            capabilities=sorted(capabilities),
        )

    async def capability_describe(self, capability: str | None = None) -> CapabilityProjection:
        # The native route wins execution_submit/execution_resolve dispatch.
        # Discovery must expose that same natural owner exactly once, even
        # when a pull worker advertises an overlapping capability name.
        external_projection = {
            name: nodes
            for name, nodes in (
                self._external_workers.capability_projection().items()
                if self._external_workers is not None
                else ()
            )
            if name not in self._routes
        }
        if capability is not None:
            route = self._routes.get(capability)
            if route is None and capability not in external_projection:
                raise GatewayError(f"unknown capability: {capability}")
            selected = [route] if route is not None else []
        else:
            selected = [self._routes[key] for key in sorted(self._routes)]

        runtime_cache: dict[str, tuple[dict[str, Any] | None, str | None]] = {}

        async def observe_owner(
            owner_id: str, tool_name: str, arguments: dict[str, Any]
        ) -> tuple[dict[str, Any] | None, str | None]:
            try:
                async with asyncio.timeout(self._projection_timeout_seconds):
                    result = await self._caller.call_tool(owner_id, tool_name, arguments)
                return result, None
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
                        available=True,
                        context_mode=route.context_mode,  # type: ignore[arg-type]
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
                    owner_available = any(
                        isinstance(item, dict)
                        and bool(item.get("configured", False))
                        and bool(item.get("available", False))
                        for item in result.get("targets", [])
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

        external_keys = (
            [capability]
            if capability is not None and capability in external_projection
            else sorted(external_projection)
            if capability is None
            else []
        )
        for external_capability in external_keys:
            nodes = external_projection[external_capability]
            values.append(
                CapabilityDescriptor(
                    capability=external_capability,
                    owner_id="external.pull",
                    category="execution",
                    configured=True,
                    available=bool(nodes),
                    context_mode="none",
                    owner_node_ids=nodes,
                    truth_boundary=(
                        "External worker transport owns queue/lease/attempt delivery mechanics only; "
                        "workers do not acquire Task ownership or domain authority."
                    ),
                    description=(
                        "Execute through a live operator-admitted provider-neutral external pull worker."
                    ),
                    tags=["execution", "external", "pull", "worker"],
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

    async def capability_resolve(
        self,
        *,
        capability: str,
        workspace_id: str | None = None,
        agent_id: str | None = None,
    ) -> CapabilityResolution:
        specs = research_capabilities()
        spec = specs.get(capability)
        if spec is None:
            if capability not in self._routes:
                raise GatewayError(f"unknown capability: {capability}")
            raise GatewayError(f"capability has no composition resolver: {capability}")
        for label, value in (("workspaceId", workspace_id), ("agentId", agent_id)):
            if value is not None and (
                not isinstance(value, str) or value != value.strip() or not value
            ):
                raise GatewayError(f"{label} must be non-empty trimmed text when provided")

        selected_skill: CapabilitySkillBinding | None = None
        observation_errors: list[str] = []
        if spec.preferred_skills:
            if not _configured(self._caller, "skills"):
                reason = (
                    _configuration_error(self._caller, "skills")
                    or "owner endpoint is not configured"
                )
                observation_errors.append(f"skills: {reason}")
            else:
                for skill_ref in spec.preferred_skills:
                    arguments: dict[str, Any] = {
                        "ref": skill_ref,
                        "invocationMode": "explicit",
                        "forceRefresh": False,
                    }
                    if workspace_id is not None:
                        arguments["workspaceId"] = workspace_id
                    if agent_id is not None:
                        arguments["agentId"] = agent_id
                    try:
                        result = await self._caller.call_tool("skills", "skills.resolve", arguments)
                    except Exception as exc:
                        observation_errors.append(
                            f"skills/{skill_ref}: {type(exc).__name__}: {str(exc)[:240]}"
                        )
                        continue
                    resolved = result.get("resolved")
                    if not isinstance(resolved, dict):
                        observation_errors.append(
                            f"skills/{skill_ref}: owner response omitted resolved binding"
                        )
                        continue
                    try:
                        selected_skill = CapabilitySkillBinding(
                            ref=skill_ref,
                            skill_id=_required_str(resolved, "skillId"),
                            name=_required_str(resolved, "name"),
                            instruction_digest=_required_str(resolved, "instructionDigest"),
                            package_revision=_required_str(resolved, "packageRevision"),
                            snapshot_revision=_required_str(result, "snapshotRevision"),
                            instruction_authority=_required_str(resolved, "instructionAuthority"),
                        )
                    except GatewayError as exc:
                        observation_errors.append(f"skills/{skill_ref}: {exc}")
                        continue
                    break

        recipes = [
            CapabilityInvocationRecipe(
                recipe_id=value.recipe_id,
                kind=value.kind,  # type: ignore[arg-type]
                owner_id=value.owner_id,
                command=list(value.command),
                note=value.note,
            )
            for value in spec.invocation_recipes
        ]
        non_claims = [
            "Resolution is routing metadata, not authorization.",
            "A resolved Skill is advisory procedural content, not scientific truth authority.",
            "Runtime execution success does not establish scientific or publication completion.",
            "Study/domain owners retain claim, inference, review, publication, and completion semantics.",
            "sourceRefs are current monorepo paths at the release SourceCut only; independently requalify newer source and external Study authority before use.",
        ]
        digest_payload = {
            "capability": spec.capability,
            "semanticOwner": spec.semantic_owner,
            "completionOwner": spec.completion_owner,
            "executionCapability": spec.execution_capability,
            "studyTypes": list(spec.study_types),
            "skillCandidates": list(spec.preferred_skills),
            "selectedSkill": (
                selected_skill.model_dump(mode="json") if selected_skill is not None else None
            ),
            "invocationRecipes": [value.model_dump(mode="json") for value in recipes],
            "sourceRefs": list(spec.source_refs),
            "observationErrors": observation_errors,
            "nonClaims": non_claims,
        }
        resolution_digest = (
            "sha256:"
            + hashlib.sha256(
                json.dumps(
                    digest_payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()
        )
        return CapabilityResolution(
            capability=spec.capability,
            semantic_owner=spec.semantic_owner,
            completion_owner=spec.completion_owner,
            execution_capability=spec.execution_capability,
            study_types=list(spec.study_types),
            skill_candidates=list(spec.preferred_skills),
            selected_skill=selected_skill,
            invocation_recipes=recipes,
            source_refs=list(spec.source_refs),
            observation_errors=observation_errors,
            non_claims=non_claims,
            resolution_digest=resolution_digest,
        )
