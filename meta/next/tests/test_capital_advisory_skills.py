from __future__ import annotations

from pathlib import Path

NEXT = Path(__file__).resolve().parents[1]
REPO = NEXT.parents[1]
SKILLS = REPO / ".agents" / "skills"


def test_capital_advisory_skills_are_local_agent_skill_packages():
    expected = {"capital-observe", "capital-risk", "capital-reconcile"}
    for name in expected:
        path = SKILLS / name / "SKILL.md"
        text = path.read_text()
        assert text.startswith("---\n")
        assert f"name: {name}" in text
        assert "/root/.config/ordivon/secrets/" not in text


def test_capital_advisory_skills_do_not_claim_financial_authority():
    observe = (SKILLS / "capital-observe" / "SKILL.md").read_text().lower()
    risk = (SKILLS / "capital-risk" / "SKILL.md").read_text().lower()
    reconcile = (SKILLS / "capital-reconcile" / "SKILL.md").read_text().lower()
    assert "never initiates an external financial write" in observe
    assert "never synthesize" in risk
    assert "cannot initiate an effect" in reconcile
    assert "no blind resend" in reconcile
