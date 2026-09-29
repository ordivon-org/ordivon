from __future__ import annotations

import hashlib
import json
import re
from importlib.metadata import version as package_version
from typing import Any

from .contracts import (
    ArtifactChunk,
    CapabilityDescriptor,
    CapabilityInvocationRecipe,
    CapabilityProjection,
    CapabilityResolution,
    CapabilitySearchMatch,
    CapabilitySearchProjection,
    CapabilitySkillBinding,
    ExecutionObservation,
    ExecutionReceipt,
    ExecutionResolution,
    OwnerDescriptor,
    SystemDescription,
)
from .external_worker import ExternalPullWorkerTransport, WorkerConflict
from .research_routes import research_capabilities
from .routes import CapabilityRoute, default_routes
from .upstream import OwnerToolCaller


class GatewayError(RuntimeError):
    pass


_OWNER_ROLES = {
    "runtime.linux": "physical execution owner",
    "runtime.windows": "physical execution owner",
    "host": "external semantic continuity owner",
    "skills": "procedural Skill discovery and exact binding owner",
    "research.composition": "non-authoritative Research composition metadata",
    "external.pull": "provider-neutral outbound pull execution transport",
}

_SOCIAL_WORK_HOST_TOOLS = frozenset(
    {
        "host.status",
        "actor.declare",
        "work.create",
        "work.get",
        "work.list",
        "work.snapshot.commit",
        "space.create",
        "space.get",
        "space.list",
        "space.participation.set",
        "space.participation.list",
        "space.subject.list",
        "topic.create",
        "topic.cursor.ack",
        "topic.cursor.get",
        "topic.list",
        "topic.resume",
        "message.post",
        "message.search",
        "message.relation.add",
        "message.relation.list",
        "subscription.follow",
        "subscription.list",
        "subscription.unfollow",
        "attention.get",
        "attention.delta",
        "attention.ack",
        "attention.reentry",
    }
)


def _configured(caller: OwnerToolCaller, owner_id: str) -> bool:
    probe = getattr(caller, "is_configured", None)
    if callable(probe):
        return bool(probe(owner_id))
    return True


def _configuration_error(caller: OwnerToolCaller, owner_id: str) -> str | None:
    probe = getattr(caller, "configuration_error", None)
    if callable(probe):
        value = probe(owner_id)
        return str(value) if value else None
    return None


def _execution_ref(owner_id: str, native_id: str) -> str:
    return f"ordivon-exec:v1:{owner_id}:{native_id}"


def parse_execution_ref(value: str) -> tuple[str, str]:
    prefix = "ordivon-exec:v1:"
    if not value.startswith(prefix):
        raise GatewayError("invalid execution operationRef")
    rest = value[len(prefix) :]
    try:
        owner_id, native_id = rest.rsplit(":", 1)
    except ValueError as exc:
        raise GatewayError("invalid execution operationRef") from exc
    if owner_id not in {"runtime.linux", "runtime.windows", "external.pull"} or not native_id:
        raise GatewayError("unsupported execution operationRef owner")
    return owner_id, native_id


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise GatewayError(f"owner response omitted {key}")
    return value


def _optional_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise GatewayError(f"owner response has invalid {key}")
    return value


class GatewayService:
    def __init__(
        self,
        caller: OwnerToolCaller,
        routes: dict[str, CapabilityRoute] | None = None,
        *,
        external_workers: ExternalPullWorkerTransport | None = None,
    ) -> None:
        self._caller = caller
        self._routes = routes or default_routes()
        self._external_workers = external_workers

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
        external_projection = (
            self._external_workers.capability_projection()
            if self._external_workers is not None
            else {}
        )
        if capability is not None:
            route = self._routes.get(capability)
            if route is None and capability not in external_projection:
                raise GatewayError(f"unknown capability: {capability}")
            selected = [route] if route is not None else []
        else:
            selected = [self._routes[key] for key in sorted(self._routes)]

        runtime_cache: dict[str, tuple[dict[str, Any] | None, str | None]] = {}

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
            try:
                result = await self._caller.call_tool(
                    owner_id, "runtime.describe", {"schemaVersion": 1}
                )
                value = (result, None)
            except Exception as exc:
                value = (
                    None,
                    f"{type(exc).__name__}: {str(exc)[:240]}",
                )
            runtime_cache[owner_id] = value
            return value

        async def execution_descriptor(route: CapabilityRoute) -> CapabilityDescriptor:
            configured_at_gateway = _configured(self._caller, route.owner_id)
            if not configured_at_gateway:
                return CapabilityDescriptor(
                    capability=route.capability,
                    owner_id=route.owner_id,
                    category=route.category,
                    configured=False,
                    available=False,
                    context_mode=route.context_mode,  # type: ignore[arg-type]
                    observation_error=_configuration_error(self._caller, route.owner_id),
                    truth_boundary=route.truth_boundary,
                )

            result, error = await runtime_description(route.owner_id)
            if result is None:
                return CapabilityDescriptor(
                    capability=route.capability,
                    owner_id=route.owner_id,
                    category=route.category,
                    configured=True,
                    available=False,
                    context_mode=route.context_mode,  # type: ignore[arg-type]
                    observation_error=error,
                    truth_boundary=route.truth_boundary,
                )

            target = next(
                (
                    item
                    for item in result.get("targets", [])
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

            node = result.get("node")
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
                    contexts = [
                        dict(value) for value in structured_contexts if isinstance(value, dict)
                    ]
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
                    str(value)
                    for value in target.get("executionProfiles", [])
                    if isinstance(value, str)
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
                if configured:
                    try:
                        await self._caller.call_tool(
                            "host",
                            "host.status",
                            {"detail": "summary"},
                        )
                        available = True
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {str(exc)[:240]}"
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

    async def execution_submit(
        self,
        *,
        capability: str,
        request_id: str,
        workspace_id: str,
        executable: str,
        args: list[str],
        cwd_relative: str = ".",
        context: str | dict[str, Any] | None = None,
        env: dict[str, str] | None = None,
        timeout_ms: int | None = None,
        authority_references: list[dict[str, Any]] | None = None,
    ) -> ExecutionReceipt:
        route = self._routes.get(capability)
        if route is None and self._external_workers is not None:
            external_projection = self._external_workers.capability_projection()
            if capability in external_projection:
                if not request_id or not workspace_id or not executable:
                    raise GatewayError("requestId, workspaceId, and executable are required")
                parcel: dict[str, Any] = {
                    "workspace_id": workspace_id,
                    "executable": executable,
                    "args": list(args),
                    "cwd_relative": cwd_relative,
                }
                if context is not None:
                    parcel["context"] = context
                if env is not None:
                    parcel["env"] = dict(env)
                if timeout_ms is not None:
                    parcel["timeout_ms"] = timeout_ms
                if authority_references is not None:
                    parcel["authority_references"] = [dict(item) for item in authority_references]
                try:
                    operation = self._external_workers.submit(
                        capability=capability,
                        request_id=request_id,
                        parcel=parcel,
                    )
                except WorkerConflict as exc:
                    raise GatewayError(str(exc)) from exc
                return ExecutionReceipt(
                    operation_ref=_execution_ref("external.pull", operation.operation_id),
                    capability=capability,
                    owner_id="external.pull",
                    native_id=operation.operation_id,
                    state=operation.state,
                    terminal=operation.terminal,
                    delivery_disposition="queued" if not operation.terminal else "committed",
                )
        if route is None:
            raise GatewayError(f"unknown capability: {capability}")
        if route.category != "execution" or route.owner_tool != "workspace.exec":
            raise GatewayError(f"capability is not executable: {capability}")
        if not request_id or not workspace_id or not executable:
            raise GatewayError("requestId, workspaceId, and executable are required")

        execution: dict[str, Any] = {
            "workspaceId": workspace_id,
            "executable": executable,
            "args": list(args),
            "cwdRelative": cwd_relative,
            "executionTarget": route.execution_target,
        }
        if route.owner_id == "runtime.linux":
            if isinstance(context, dict):
                raise GatewayError("execution.linux context must be a provider-defined string")
            execution["executionProfile"] = context or route.default_context
        elif route.owner_id == "runtime.windows":
            execution["executionProfile"] = "trusted_local"
            if context is None:
                execution["windowsAuthority"] = route.default_context
            elif isinstance(context, str):
                # Compatibility only: Gateway does not interpret legacy authority values.
                execution["windowsAuthority"] = context
            else:
                # Structured Windows authority is opaque provider-owned data. Gateway only
                # lowers the generic northbound envelope into Runtime's owner field.
                execution["windowsContext"] = dict(context)
        else:
            raise GatewayError(f"unsupported execution owner: {route.owner_id}")
        if env is not None:
            if not all(
                isinstance(key, str) and key and isinstance(value, str)
                for key, value in env.items()
            ):
                raise GatewayError("env must map non-empty string names to string values")
            execution["env"] = dict(env)
        if timeout_ms is not None:
            execution["timeoutMs"] = timeout_ms
        if authority_references is not None:
            if any(not isinstance(item, dict) for item in authority_references):
                raise GatewayError("authorityReferences must contain objects")
            execution["foreignReferences"] = [dict(item) for item in authority_references]

        payload = {
            "schemaVersion": 1,
            "clientRequestId": request_id,
            "execution": execution,
            "waitMs": 0,
            "stdoutTailBytes": 4096,
            "stderrTailBytes": 4096,
        }
        result = await self._caller.call_tool(route.owner_id, route.owner_tool, payload)
        native_id = _required_str(result, "jobId")
        return ExecutionReceipt(
            operation_ref=_execution_ref(route.owner_id, native_id),
            capability=capability,
            owner_id=route.owner_id,
            native_id=native_id,
            state=str(result.get("status", result.get("attemptState", "unknown"))),
            terminal=bool(result.get("executionTerminal", False)),
            delivery_disposition=(
                str(result["deliveryDisposition"])
                if result.get("deliveryDisposition") is not None
                else None
            ),
        )

    async def execution_resolve(self, *, capability: str, request_id: str) -> ExecutionResolution:
        route = self._routes.get(capability)
        if route is None and self._external_workers is not None:
            operation = self._external_workers.resolve(capability, request_id)
            if operation is None:
                return ExecutionResolution(
                    request_id=request_id,
                    capability=capability,
                    owner_id="external.pull",
                    resolution="absent",
                )
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id="external.pull",
                resolution="found",
                operation_ref=_execution_ref("external.pull", operation.operation_id),
                native_id=operation.operation_id,
            )
        if route is None:
            raise GatewayError(f"unknown capability: {capability}")
        if route.category != "execution" or route.owner_tool != "workspace.exec":
            raise GatewayError(f"capability is not executable: {capability}")
        if not request_id:
            raise GatewayError("requestId is required")

        page = await self._caller.call_tool(
            route.owner_id,
            "job.list",
            {
                "limit": 2,
                "clientRequestId": request_id,
            },
        )
        jobs = page.get("jobs")
        if not isinstance(jobs, list) or any(not isinstance(item, dict) for item in jobs):
            raise GatewayError("Runtime job.list omitted jobs")
        for job in jobs:
            if job.get("clientRequestId") != request_id:
                raise GatewayError("Runtime job.list returned another clientRequestId")
        next_cursor = page.get("nextCursor")
        ambiguous = len(jobs) > 1 or next_cursor is not None
        if ambiguous:
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id=route.owner_id,
                resolution="ambiguous",
            )
        if not jobs:
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id=route.owner_id,
                resolution="absent",
            )
        native_id = _required_str(jobs[0], "jobId")
        return ExecutionResolution(
            request_id=request_id,
            capability=capability,
            owner_id=route.owner_id,
            resolution="found",
            operation_ref=_execution_ref(route.owner_id, native_id),
            native_id=native_id,
        )

    async def execution_get(
        self, operation_ref: str, *, event_limit: int = 10, wait_ms: int = 0
    ) -> ExecutionObservation:
        owner_id, native_id = parse_execution_ref(operation_ref)
        if owner_id == "external.pull":
            if self._external_workers is None:
                raise GatewayError("external pull worker transport is not configured")
            try:
                operation = self._external_workers.get(native_id)
            except WorkerConflict as exc:
                raise GatewayError(str(exc)) from exc
            return ExecutionObservation(
                operation_ref=operation_ref,
                capability=operation.capability,
                owner_id=owner_id,
                native_id=native_id,
                state=operation.state,
                terminal=operation.terminal,
                delivery_disposition=(
                    "committed"
                    if operation.terminal
                    else "unknown"
                    if operation.state == "reconcile_required"
                    else "in_progress"
                ),
                execution_disposition=(
                    "succeeded"
                    if operation.terminal and operation.exit_code == 0
                    else "failed"
                    if operation.terminal and operation.exit_code is not None
                    else None
                ),
                exit_code=operation.exit_code,
                recovery_required=operation.state == "reconcile_required",
                artifacts_available=bool(operation.artifact_ids),
                artifact_count=len(operation.artifact_ids),
                artifact_ids=operation.artifact_ids,
                artifact_projection_complete=True,
            )
        # eventLimit is retained on the northbound surface for connector compatibility.
        # Runtime's execution observation authority is job.observe; Gateway does not
        # project the job.get event timeline, so forwarding eventLimit would add no truth.
        _ = event_limit
        if type(wait_ms) is not int or not 0 <= wait_ms <= 30_000:
            raise GatewayError("waitMs must be an integer between 0 and 30000")
        result = await self._caller.call_tool(
            owner_id,
            "job.observe",
            {
                "schemaVersion": 1,
                "jobId": native_id,
                "waitMs": wait_ms,
                "waitUntil": "change_or_terminal",
                "stdoutTailBytes": 0,
                "stderrTailBytes": 0,
            },
        )
        observed_native_id = _required_str(result, "jobId")
        if observed_native_id != native_id:
            raise GatewayError("Runtime job.observe returned mismatched job identity")

        def artifact_ids(payload: dict[str, Any]) -> list[str]:
            values: list[str] = []
            for item in payload.get("artifacts", []):
                if isinstance(item, dict) and isinstance(item.get("artifactId"), str):
                    values.append(item["artifactId"])
            return values

        artifacts = artifact_ids(result)
        artifacts_available = (
            bool(result["artifactsAvailable"])
            if isinstance(result.get("artifactsAvailable"), bool)
            else None
        )
        artifact_count = len(artifacts)
        artifact_projection_complete: bool | None = None

        if bool(result.get("executionTerminal", False)) or artifacts_available:
            inspection = await self._caller.call_tool(
                owner_id,
                "job.get",
                {
                    "schemaVersion": 1,
                    "jobId": native_id,
                    "eventLimit": 1,
                },
            )
            job = inspection.get("job")
            if not isinstance(job, dict) or job.get("jobId") != native_id:
                raise GatewayError("Runtime job.get returned mismatched job identity")
            summary = inspection.get("artifacts")
            summary_count = (
                int(summary["count"])
                if isinstance(summary, dict) and isinstance(summary.get("count"), int)
                else None
            )
            if summary_count is not None:
                artifact_count = summary_count
                if len(artifacts) != summary_count:
                    refreshed = await self._caller.call_tool(
                        owner_id,
                        "job.observe",
                        {
                            "schemaVersion": 1,
                            "jobId": native_id,
                            "waitMs": 0,
                            "waitUntil": "change_or_terminal",
                            "stdoutTailBytes": 0,
                            "stderrTailBytes": 0,
                        },
                    )
                    if _required_str(refreshed, "jobId") != native_id:
                        raise GatewayError(
                            "Runtime job.observe refresh returned mismatched job identity"
                        )
                    artifacts = artifact_ids(refreshed)
                    artifacts_available = (
                        bool(refreshed["artifactsAvailable"])
                        if isinstance(refreshed.get("artifactsAvailable"), bool)
                        else artifacts_available
                    )
                artifact_projection_complete = len(artifacts) == summary_count
            else:
                artifact_projection_complete = not artifacts_available or bool(artifacts)

        return ExecutionObservation(
            operation_ref=operation_ref,
            capability=(
                "execution.windows" if owner_id == "runtime.windows" else "execution.linux"
            ),
            owner_id=owner_id,
            native_id=observed_native_id,
            state=str(result.get("status", result.get("attemptState", "unknown"))),
            terminal=bool(result.get("executionTerminal", False)),
            delivery_disposition=(
                str(result["deliveryDisposition"])
                if result.get("deliveryDisposition") is not None
                else None
            ),
            execution_disposition=(
                str(result["executionDisposition"])
                if result.get("executionDisposition") is not None
                else None
            ),
            exit_code=(
                int(result["exitCode"]) if isinstance(result.get("exitCode"), int) else None
            ),
            recovery_required=(
                bool(result["recoveryRequired"])
                if isinstance(result.get("recoveryRequired"), bool)
                else None
            ),
            artifacts_available=artifacts_available,
            artifact_count=artifact_count,
            artifact_ids=artifacts,
            artifact_projection_complete=artifact_projection_complete,
        )

    async def execution_cancel(self, operation_ref: str) -> ExecutionReceipt:
        owner_id, native_id = parse_execution_ref(operation_ref)
        if owner_id == "external.pull":
            if self._external_workers is None:
                raise GatewayError("external pull worker transport is not configured")
            try:
                operation = self._external_workers.cancel(native_id)
            except WorkerConflict as exc:
                raise GatewayError(str(exc)) from exc
            return ExecutionReceipt(
                operation_ref=operation_ref,
                capability=operation.capability,
                owner_id=owner_id,
                native_id=native_id,
                state=operation.state,
                terminal=operation.terminal,
                delivery_disposition="committed" if operation.terminal else "in_progress",
            )
        result = await self._caller.call_tool(
            owner_id,
            "job.cancel",
            {"schemaVersion": 1, "jobId": native_id},
        )
        return ExecutionReceipt(
            operation_ref=operation_ref,
            capability=(
                "execution.windows" if owner_id == "runtime.windows" else "execution.linux"
            ),
            owner_id=owner_id,
            native_id=_required_str(result, "jobId"),
            state=str(result.get("status", "unknown")),
            terminal=bool(result.get("executionTerminal", False)),
            delivery_disposition=(
                str(result["deliveryDisposition"])
                if result.get("deliveryDisposition") is not None
                else None
            ),
        )

    async def artifact_read(
        self,
        operation_ref: str,
        artifact_id: str,
        *,
        offset: int = 0,
        max_bytes: int = 1_048_576,
    ) -> ArtifactChunk:
        owner_id, native_id = parse_execution_ref(operation_ref)
        if owner_id == "external.pull":
            if self._external_workers is None:
                raise GatewayError("external pull worker transport is not configured")
            try:
                result = self._external_workers.read_artifact(
                    native_id, artifact_id, offset=offset, max_bytes=max_bytes
                )
            except WorkerConflict as exc:
                raise GatewayError(str(exc)) from exc
            return ArtifactChunk(
                operation_ref=operation_ref,
                owner_id=owner_id,
                native_id=native_id,
                artifact_id=artifact_id,
                offset=int(result["offset"]),
                next_offset=int(result["next_offset"]),
                eof=bool(result["eof"]),
                digest=str(result["digest"]),
                content=str(result["content"]),
            )
        result = await self._caller.call_tool(
            owner_id,
            "artifact.read",
            {
                "schemaVersion": 1,
                "jobId": native_id,
                "artifactId": artifact_id,
                "offset": offset,
                "maxBytes": max_bytes,
            },
        )
        if result.get("jobId") != native_id or result.get("artifactId") != artifact_id:
            raise GatewayError("artifact owner returned mismatched identity")
        return ArtifactChunk(
            operation_ref=operation_ref,
            owner_id=owner_id,
            native_id=native_id,
            artifact_id=artifact_id,
            offset=int(result.get("offset", offset)),
            next_offset=int(result.get("nextOffset", offset)),
            eof=bool(result.get("eof", False)),
            digest=_required_str(result, "digest"),
            content=str(result.get("content", "")),
        )

    async def social_work_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route one promoted Social Work Fabric operation to Host without re-owning semantics."""
        if tool_name not in _SOCIAL_WORK_HOST_TOOLS:
            raise GatewayError(f"unsupported Host Social Work tool: {tool_name}")
        result = await self._caller.call_tool("host", tool_name, arguments)
        if not isinstance(result, dict):
            raise GatewayError("Host Social Work owner returned non-object response")
        return result
