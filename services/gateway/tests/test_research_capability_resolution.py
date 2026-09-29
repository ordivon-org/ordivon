from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from ordivon_gateway.research_routes import research_capabilities
from ordivon_gateway.service import GatewayError, GatewayService


class ResolverCaller:
    def __init__(
        self,
        responses: dict[tuple[str, str], dict[str, Any]] | None = None,
        configured: set[str] | None = None,
        configuration_errors: dict[str, str] | None = None,
    ) -> None:
        self.responses = responses or {}
        self.configured = configured or set()
        self.configuration_errors = configuration_errors or {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def is_configured(self, owner_id: str) -> bool:
        return owner_id in self.configured

    def configuration_error(self, owner_id: str) -> str | None:
        return self.configuration_errors.get(owner_id)

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_id, tool_name, arguments))
        return self.responses[(owner_id, tool_name)]


def skill_resolution(name: str) -> dict[str, Any]:
    return {
        "resolved": {
            "skillId": f"codex-user/{name}",
            "name": name,
            "instructionDigest": "sha256:" + "1" * 64,
            "packageRevision": "sha256:" + "2" * 64,
            "instructionAuthority": "ADVISORY",
        },
        "snapshotRevision": "sha256:" + "3" * 64,
        "snapshotInvocationMode": "explicit",
    }


def test_research_projection_is_discoverable_without_becoming_an_execution_owner() -> None:
    caller = ResolverCaller()
    service = GatewayService(caller)

    projection = asyncio.run(service.capability_describe("research.statistical.analysis"))
    item = projection.capabilities[0]
    assert item.owner_id == "research.composition"
    assert item.category == "research"
    assert item.configured is True
    assert item.available is True
    assert "scientific truth" in item.truth_boundary
    assert caller.calls == []

    result = asyncio.run(service.capability_search(query="statistical analysis"))
    assert result.total_matches == 1
    assert result.matches[0].capability.capability == "research.statistical.analysis"
    assert caller.calls == []


def test_research_resolve_binds_exact_current_skill_without_executing_it() -> None:
    caller = ResolverCaller(
        {("skills", "skills.resolve"): skill_resolution("paper-lookup")},
        {"skills"},
    )
    service = GatewayService(caller)

    resolved = asyncio.run(
        service.capability_resolve(
            capability="research.literature.discovery",
            workspace_id="ordivon-next",
            agent_id="agent-research",
        )
    )

    assert resolved.truth_role == "non-authoritative-composition-route"
    assert resolved.semantic_owner == "study.method-and-source-authorities"
    assert resolved.completion_owner == "study"
    assert resolved.selected_skill is not None
    assert resolved.selected_skill.ref == "paper-lookup"
    assert resolved.selected_skill.skill_id == "codex-user/paper-lookup"
    assert resolved.selected_skill.instruction_authority == "ADVISORY"
    assert resolved.resolution_digest.startswith("sha256:")
    assert resolved.observation_errors == []
    assert [recipe.kind for recipe in resolved.invocation_recipes] == ["skill"]
    assert caller.calls == [
        (
            "skills",
            "skills.resolve",
            {
                "ref": "paper-lookup",
                "invocationMode": "explicit",
                "forceRefresh": False,
                "workspaceId": "ordivon-next",
                "agentId": "agent-research",
            },
        )
    ]


def test_research_resolve_preserves_unknown_skills_owner_as_observation_gap() -> None:
    caller = ResolverCaller(
        configured=set(),
        configuration_errors={"skills": "owner endpoint is not configured"},
    )
    service = GatewayService(caller)

    resolved = asyncio.run(service.capability_resolve(capability="research.statistical.analysis"))
    assert resolved.selected_skill is None
    assert resolved.skill_candidates == ["statistical-analysis"]
    assert resolved.observation_errors == ["skills: owner endpoint is not configured"]
    assert resolved.completion_owner == "study"
    assert caller.calls == []


def test_recipe_only_resolution_exposes_canonical_invocation_without_running_it() -> None:
    caller = ResolverCaller()
    service = GatewayService(caller)

    resolved = asyncio.run(service.capability_resolve(capability="research.study.verify"))
    assert resolved.selected_skill is None
    assert resolved.execution_capability == "execution.linux"
    assert len(resolved.invocation_recipes) == 1
    recipe = resolved.invocation_recipes[0]
    assert recipe.kind == "mise-task"
    assert recipe.command == ["mise", "run", "research-study:verify"]
    assert "ad-hoc system Python" in recipe.note
    assert caller.calls == []


def test_capability_resolve_does_not_pretend_generic_execution_has_composition_semantics() -> None:
    with pytest.raises(GatewayError, match="no composition resolver"):
        asyncio.run(
            GatewayService(ResolverCaller()).capability_resolve(capability="execution.linux")
        )


def test_research_route_index_has_existing_monorepo_sources_and_explicit_owner_boundaries() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    specs = research_capabilities()
    assert len(specs) >= 10
    for capability, spec in specs.items():
        assert capability.startswith("research.")
        assert spec.semantic_owner
        assert spec.completion_owner
        assert spec.source_refs
        assert "scientific truth" in spec.truth_boundary
        for source_ref in spec.source_refs:
            if source_ref.startswith("research-v2:"):
                continue
            assert (repo_root / source_ref).exists(), f"missing source ref: {source_ref}"
        for recipe in spec.invocation_recipes:
            assert recipe.kind in {"skill", "mise-task", "owner-cli"}
            if recipe.kind == "skill":
                assert recipe.owner_id == "skills"
        if spec.preferred_skills:
            assert any(recipe.kind == "skill" for recipe in spec.invocation_recipes)


def test_three_study_route_dogfood_preserves_axis_and_authority_separation() -> None:
    service = GatewayService(
        ResolverCaller(
            configured=set(),
            configuration_errors={"skills": "owner endpoint is not configured"},
        )
    )

    paper1 = asyncio.run(service.capability_resolve(capability="research.publication.closure"))
    assert paper1.semantic_owner == "study.publication-authority"
    assert paper1.completion_owner == "study-and-human-submission-authority"
    assert paper1.execution_capability is None

    paper2 = asyncio.run(service.capability_resolve(capability="research.literature.discovery"))
    assert paper2.semantic_owner == "study.method-and-source-authorities"
    assert paper2.completion_owner == "study"
    assert paper2.execution_capability is None

    paper3 = asyncio.run(
        service.capability_resolve(capability="research.publication.perceptual-conformance")
    )
    assert paper3.semantic_owner == "publication-perceptual-observer-protocol"
    assert paper3.completion_owner == "study.publication-authority"
    assert paper3.execution_capability is None

    for resolved in (paper1, paper2, paper3):
        assert resolved.selected_skill is None
        assert resolved.observation_errors == ["skills: owner endpoint is not configured"]
        assert any("not authorization" in item for item in resolved.non_claims)
        assert any("Runtime execution success" in item for item in resolved.non_claims)
