from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from ordivon_gateway.research_resolution import resolve_research_capability
from ordivon_gateway.research_routes import research_capabilities
from ordivon_gateway.routing import default_routes
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
    assert item.available is False  # no real provider readiness observation
    assert "UNKNOWN" in (item.observation_error or "")
    assert "scientific truth" in item.truth_boundary
    assert caller.calls == []

    result = asyncio.run(service.capability_search(query="statistical analysis"))
    assert result.total_matches == 1
    assert result.matches[0].capability.capability == "research.statistical.analysis"
    # UNKNOWN entries remain discoverable even with an availability filter;
    only_ready = asyncio.run(
        service.capability_search(query="statistical analysis", include_unavailable=False)
    )
    assert only_ready.total_matches == 1
    assert only_ready.matches[0].capability.available is False
    assert "UNKNOWN" in (only_ready.matches[0].capability.observation_error or "")
    assert caller.calls == []


def test_research_metadata_catalog_never_claims_live_provider_readiness() -> None:
    # Finite source-cut invariant over every declared research composition route.
    caller = ResolverCaller()
    projection = asyncio.run(GatewayService(caller).capability_describe())
    research = [item for item in projection.capabilities if item.category == "research"]
    assert {item.capability for item in research} == set(research_capabilities())
    assert research
    for item in research:
        assert item.configured is True  # native metadata resolver exists
        assert item.available is False  # no provider readiness observation
        assert "UNKNOWN" in (item.observation_error or "")
        assert "scientific truth" in item.truth_boundary
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


def test_research_resolution_owner_seam_matches_public_gateway_contract() -> None:
    """Composition may move out of the catalog, but exact Skill bytes and digest do not."""
    owner_responses = {("skills", "skills.resolve"): skill_resolution("paper-lookup")}
    facade_caller = ResolverCaller(owner_responses, {"skills"})
    adapter_caller = ResolverCaller(owner_responses, {"skills"})
    arguments = {
        "capability": "research.literature.discovery",
        "workspace_id": "workspace-source-cut",
        "agent_id": "agent-research-owner",
    }

    via_gateway = asyncio.run(GatewayService(facade_caller).capability_resolve(**arguments))
    via_adapter = asyncio.run(
        resolve_research_capability(adapter_caller, default_routes(), **arguments)
    )
    assert via_gateway.model_dump(mode="json") == via_adapter.model_dump(mode="json")
    assert via_gateway.resolution_digest == via_adapter.resolution_digest
    assert facade_caller.calls == adapter_caller.calls
    assert len(facade_caller.calls) == 1


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
    assert recipe.kind == "owner-cli"
    assert recipe.command == [
        "uv",
        "--directory",
        "/root/projects/ordivon-research-v2",
        "run",
        "--locked",
        "ordivon-research-study",
        "check-all",
    ]
    assert "does not verify scientific" in recipe.note
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
                # Explicit external Study owner: monorepo source presence is
                # neither required nor a claim of external scientific truth.
                assert source_ref.removeprefix("research-v2:").strip()
                continue
            source_path = (repo_root / source_ref).resolve()
            # Native Gateway SourceCut check: no path traversal, symlink to
            # an external authority or retired/fictional current file.
            assert source_path.is_relative_to(repo_root.resolve()), source_ref
            assert source_path.is_file(), f"unqualified missing current source ref: {source_ref}"
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


def test_research_birth_route_calls_existing_locked_owner_not_uninstalled_shell_binary() -> None:
    from ordivon_gateway.research_routes import research_capabilities

    route = research_capabilities()["research.study.birth"]
    assert len(route.invocation_recipes) == 1
    recipe = route.invocation_recipes[0]
    assert recipe.owner_id == "research-v2"
    assert recipe.kind == "owner-cli"
    assert list(recipe.command) == [
        "uv",
        "--directory",
        "/root/projects/ordivon-research-v2",
        "run",
        "--locked",
        "ordivon-research-study",
    ]
    assert "research-v2:crates/research-birth/src/spec.rs" in route.source_refs
    assert route.execution_capability == "execution.linux"


def test_research_verify_route_is_an_invokable_mechanical_birth_check_not_missing_mise_task() -> (
    None
):
    from ordivon_gateway.research_routes import research_capabilities

    route = research_capabilities()["research.study.verify"]
    assert len(route.invocation_recipes) == 1
    recipe = route.invocation_recipes[0]
    assert recipe.owner_id == "research-v2"
    assert list(recipe.command) == [
        "uv",
        "--directory",
        "/root/projects/ordivon-research-v2",
        "run",
        "--locked",
        "ordivon-research-study",
        "check-all",
    ]
    assert route.semantic_owner == "research-v2.study-birth-contract"
    assert "mechanical" in route.description.lower()
    assert "scientific" in recipe.note.lower()


def test_scholarly_intelligence_does_not_pretend_unimplemented_execution_recipe_exists() -> None:
    from ordivon_gateway.research_routes import research_capabilities

    route = research_capabilities()["research.scholarly.intelligence"]
    assert route.invocation_recipes == ()
    assert route.execution_capability is None
    assert route.completion_owner == "study"
    assert "no generic" in route.description.lower()


def test_real_birth_recipe_reroutes_to_installed_research_owner_when_available() -> None:
    """Cross-repo native consumer, without granting Study/science/Host authority."""
    import json
    import shutil
    import subprocess

    owner = Path("/root/projects/ordivon-research-v2")
    if not owner.is_dir() or shutil.which("uv") is None:
        pytest.skip("external Research-v2 owner or mature uv runner not installed here")
    route = research_capabilities()["research.study.birth"]
    recipe = route.invocation_recipes[0]
    result = subprocess.run(
        [*recipe.command, "--repo-root", str(owner), "defaults"],
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    projected = json.loads(result.stdout)
    assert projected["birthPolicy"]["policyId"].startswith("research-study-birth-")
    assert projected["birthPolicy"]["digest"].startswith("sha256:")
    assert projected["dataPlane"]["digest"].startswith("sha256:")


def test_actual_gateway_research_check_all_and_r2_no_host_fence(
    tmp_path: Path,
) -> None:
    """One real Gateway resolution -> uv owner invocation -> bounded outcome."""
    import shutil
    import subprocess

    owner = Path("/root/projects/ordivon-research-v2")
    if not owner.is_dir() or shutil.which("uv") is None:
        pytest.skip("external Research-v2 owner or mature uv runner not installed here")

    caller = ResolverCaller()
    resolved = asyncio.run(
        GatewayService(caller).capability_resolve(capability="research.study.verify")
    )
    assert caller.calls == []
    assert resolved.selected_skill is None
    assert resolved.execution_capability == "execution.linux"
    recipe = resolved.invocation_recipes[0]
    checked = subprocess.run(
        [*recipe.command],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert checked.returncode == 0, checked.stderr
    assert checked.stdout.strip() == "PASS research-study-birth-policy"

    # Running a real routed CLI is physical execution only. The current r2
    # policy must not authorize a fresh Study without Host decision evidence.
    root = tmp_path / "research-source-only"
    (root / "profiles").mkdir(parents=True)
    shutil.copytree(owner / "profiles/birth", root / "profiles/birth")
    shutil.copytree(owner / "profiles/data_plane", root / "profiles/data_plane")
    for name in ("method_authority_bindings.toml", "research_birth_policy.toml"):
        shutil.copy2(owner / "profiles" / name, root / "profiles" / name)
    birth = asyncio.run(
        GatewayService(ResolverCaller()).capability_resolve(capability="research.study.birth")
    ).invocation_recipes[0]
    denied = subprocess.run(
        [
            *birth.command,
            "--repo-root",
            str(root),
            "create",
            "--study-id",
            "no-gateway-approval",
            "--study-type",
            "empirical-software-engineering",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert denied.returncode != 0
    assert "live Host admission" in denied.stderr
    assert not (root / "studies/research/no-gateway-approval").exists()
