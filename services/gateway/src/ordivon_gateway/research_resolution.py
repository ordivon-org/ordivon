from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import CapabilityInvocationRecipe, CapabilityResolution, CapabilitySkillBinding
from .execution_refs import GatewayError
from .owner_protocol import _configuration_error, _configured, _required_str
from .research_routes import research_capabilities
from .routing import CapabilityRoute
from .upstream import OwnerToolCaller


async def resolve_research_capability(
    caller: OwnerToolCaller,
    routes: dict[str, CapabilityRoute],
    *,
    capability: str,
    workspace_id: str | None = None,
    agent_id: str | None = None,
) -> CapabilityResolution:
    """Read-only Study/Skills composition adapter; never claims scientific completion."""
    specs = research_capabilities()
    spec = specs.get(capability)
    if spec is None:
        if capability not in routes:
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
        if not _configured(caller, "skills"):
            reason = _configuration_error(caller, "skills") or "owner endpoint is not configured"
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
                    result = await caller.call_tool("skills", "skills.resolve", arguments)
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
