from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT.parents[1] / ".agents" / "skills"
ROUTER = SKILLS / "method-router"


def test_method_router_is_standard_project_skill() -> None:
    text = (ROUTER / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\nname: method-router\n")
    assert "description:" in text
    assert "private trigger engine" in text.lower()
    assert (ROUTER / "references" / "method-map.md").is_file()


def test_agent_engineering_reference_is_readable_through_project_skill_api() -> None:
    """Verify a real scoped Skill consumer, not just Markdown substring presence."""
    from ordivon_skills.catalog import SkillCatalog
    from ordivon_skills.model import SkillContext, SkillSource, TrustState

    repo = ROOT.parents[1]
    catalog = SkillCatalog.scan(
        [SkillSource("project-ordivon-next", SKILLS, "project", 900, TrustState.TRUSTED)]
    )
    context = SkillContext(workspace_path=repo)
    found = {row.skill_id for row in catalog.search("agent engineering", context=context, invocation_mode="explicit")}
    assert "project-ordivon-next/method-router" in found
    resolved = catalog.resolve("method-router", context=context)
    assert resolved.resolved.skill_id == "project-ordivon-next/method-router"
    instruction = catalog.read_text(
        resolved.resolved.skill_id,
        context=context,
        expected_snapshot_revision=resolved.snapshot_revision,
        projection="raw",
    ).content
    assert "references/agent-engineering-delivery.md" in instruction
    reference = catalog.read_text(
        resolved.resolved.skill_id,
        relative_path="references/agent-engineering-delivery.md",
        context=context,
        expected_snapshot_revision=resolved.snapshot_revision,
        projection="raw",
    ).content
    assert "Matt `to-spec`" in reference
    assert "Superpowers `using-git-worktrees`" in reference
    assert "ECC pre/post-tool hooks" in reference
    assert "not a required" in instruction.lower()
    assert not catalog.search("method router")  # project scope is required
    assert (repo / "docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md").is_file()



def _referenced_agent_specs(entrypoint: Path, content: str) -> set[Path]:
    """Resolve actual Agent delivery Spec paths relative to the current caller."""
    relative_paths = re.findall(
        r"(?:\.\./)*(?:[A-Za-z0-9._-]+/)*AGENT_[A-Z0-9_]*_SPEC[A-Z0-9_]*\.md",
        content,
    )
    return {(entrypoint.parent / relative).resolve() for relative in relative_paths}


def test_current_delivery_spec_single_consumer() -> None:
    """Current project Skill and document consumers cannot choose different Specs."""
    repo = ROOT.parents[1]
    canonical = (repo / "docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md").resolve()
    assert canonical.is_file()
    entrypoints = [
        ROUTER / "SKILL.md",
        ROUTER / "references/agent-engineering-delivery.md",
        repo / "docs/start/tasks.md",
        repo / "docs/architecture/DECISIONS.md",
    ]
    for path in entrypoints:
        content = path.read_text(encoding="utf-8")
        assert _referenced_agent_specs(path, content) == {canonical}, path

    # A retired Spec path remains invalid even when its historical file is absent.
    # This negative route tests the selected path, not the old document bytes.
    reference = ROUTER / "references/agent-engineering-delivery.md"
    alternative = "AGENT_OUTCOME_REALIZATION_R21_SPEC_20261109.md"
    wrong_content = reference.read_text(encoding="utf-8").replace(canonical.name, alternative)
    assert _referenced_agent_specs(reference, wrong_content) == {
        (repo / "docs/architecture" / alternative).resolve()
    }


def test_other_formal_delivery_spec_cannot_hide_from_current_navigation() -> None:
    """An alternate formal-delivery Spec route must be observable by the existing guard."""
    repo = ROOT.parents[1]
    entrypoint = repo / "docs/start/tasks.md"
    canonical = (repo / "docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md").resolve()
    competing = (repo / "docs/architecture/AGENT_FORMAL_DELIVERY_SPEC_R1.md").resolve()
    original = entrypoint.read_text(encoding="utf-8")
    assert _referenced_agent_specs(entrypoint, original) == {canonical}
    mutated = original + "\n[extra formal delivery](../architecture/AGENT_FORMAL_DELIVERY_SPEC_R1.md)\n"
    assert _referenced_agent_specs(entrypoint, mutated) == {canonical, competing}

def test_method_router_targets_existing_canonical_methods() -> None:
    text = (ROUTER / "references" / "method-map.md").read_text(encoding="utf-8")
    required = {
        "systems-engineering",
        "design-structure-matrix",
        "compositional-contracts",
        "causal-intervention",
        "fmea-fta",
        "stpa",
        "feedback-control",
        "organizational-cybernetics",
        "information-flow-analysis",
        "evolutionary-search",
        "exploration-policy",
        "project-kernel-decomposition",
    }
    for name in sorted(required):
        assert (SKILLS / name / "SKILL.md").is_file(), name
        assert name in text


def test_router_does_not_define_tool_or_execution_authority() -> None:
    text = (ROUTER / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "does not execute tools" in text
    assert "authority transfer" in text
    assert "smallest method set" in text


def test_representation_first_routes_are_complete_and_non_authoritative() -> None:
    """Navigation contract only; never treat this textual check as formal proof."""
    skill = (ROUTER / "SKILL.md").read_text(encoding="utf-8")
    reference = (ROUTER / "references" / "representation-first.md").read_text(
        encoding="utf-8"
    )
    charter = (
        ROOT.parents[1] / "docs/architecture/COUNTEREXAMPLE_GUIDED_REPRESENTATION_R1.md"
    ).read_text(encoding="utf-8")
    assert "references/representation-first.md" in skill
    assert "before" in skill.lower()
    for lens in (
        "Type-driven",
        "Constraint-first",
        "Graph-first",
        "State-machine-first",
        "Algebra-first",
        "Equivalence-first",
        "Declarative-first",
        "Abstraction-first",
        "Causal-first",
        "Compression-first",
    ):
        assert reference.count(f"| {lens} |") == 1, lens
        assert charter.count(f"| {lens} |") == 1, lens
    for needed in (
        "UNKNOWN",
        "owner",
        "counterexample",
        "consumer",
        "not a new registry",
    ):
        assert needed.lower() in reference.lower()
    assert "owner-native" in charter
    assert "No new framework without residual" in charter


def test_cegar_retired_msr_method_routes_real_spurious_and_unknown() -> None:
    """Navigation contract only, NOT a claim of model/implementation refinement."""
    charter = (
        ROOT.parents[1] / "docs/architecture/COUNTEREXAMPLE_GUIDED_REPRESENTATION_R1.md"
    ).read_text(encoding="utf-8")
    router = (ROUTER / "references" / "representation-first.md").read_text(
        encoding="utf-8"
    )
    assert (
        "Minimum Sufficient Representation (MSR) as a **DEFAULT**: RETIRED" in charter
    )
    assert "optional, consumer-scoped Skill LEGO" in charter
    assert "Counterexample-Guided Abstraction Refinement (CEGAR)" in charter
    assert "No global minimality or sufficiency certificate" in charter
    assert "REAL_COUNTEREXAMPLE" in charter
    assert "SPURIOUS_COUNTEREXAMPLE" in charter
    assert "UNKNOWN" in charter
    assert "abstract-to-concrete" in charter
    assert "CEGAR" in router
    assert "spurious" in router
    assert "real" in router.lower()
    assert "owner-native" in charter


def test_scope_bound_observation_reference_rejects_default_target_inference() -> None:
    """Advisory Skill currentness only; not a formal runtime authorization proof."""
    reference = (ROUTER / "references" / "representation-first.md").read_text(
        encoding="utf-8"
    )
    for negative_control in (
        "Observation.Subject == Claim.Subject",
        "Default 'tailscale status'",
        "supported active-user execution identity",
        "Cached Git origin/main",
        "currentHeadRevision",
        "native admission gates",
    ):
        assert negative_control in reference
    assert "not evidence that a live Owner enforces" in reference
