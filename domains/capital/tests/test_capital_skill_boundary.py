from __future__ import annotations

import json
from pathlib import Path

CAPITAL = Path(__file__).resolve().parents[1]
REPO = CAPITAL.parents[1]


def load(rel: str):
    return json.loads((CAPITAL / rel).read_text())


def test_capital_skills_use_standard_project_skill_root_and_are_advisory():
    contract = load("contracts/capital-skill-boundary-v1.json")
    assert contract["canonicalSkillRoot"] == "meta/next/.agents/skills"
    assert contract["truthRole"] == "ADVISORY_SKILL_BOUNDARY_NOT_FINANCIAL_AUTHORITY"
    for name, row in contract["skills"].items():
        path = REPO / row["path"]
        text = path.read_text()
        assert path.name == "SKILL.md"
        assert f"name: {name}" in text


def test_skills_cannot_infer_risk_or_initiate_effects():
    risk = (REPO / "meta/next/.agents/skills/capital-risk/SKILL.md").read_text().lower()
    observe = (REPO / "meta/next/.agents/skills/capital-observe/SKILL.md").read_text().lower()
    reconcile = (REPO / "meta/next/.agents/skills/capital-reconcile/SKILL.md").read_text().lower()
    assert "never synthesize" in risk
    assert "never initiates an external financial write" in observe
    assert "cannot initiate an effect" in reconcile
    production = load("contracts/production-authorization.json")
    assert production["state"] == "BLOCK_NOT_GRANTED"
    assert production["externalFinancialWriteAllowed"] is False
