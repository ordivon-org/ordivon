from __future__ import annotations

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
    charter = (ROOT / "docs" / "META_THINKING_REPRESENTATION_R1.md").read_text(
        encoding="utf-8"
    )
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
    charter = (ROOT / "docs" / "META_THINKING_REPRESENTATION_R1.md").read_text(
        encoding="utf-8"
    )
    router = (ROUTER / "references" / "representation-first.md").read_text(
        encoding="utf-8"
    )
    assert "Minimum Sufficient Representation (MSR) as a **DEFAULT**: RETIRED" in charter
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
