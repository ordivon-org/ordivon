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
