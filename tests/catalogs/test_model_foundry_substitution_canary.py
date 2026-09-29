from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FOUNDRY = ROOT / "catalogs" / "knowledge" / "model-foundry"
FIXTURE = Path(__file__).with_name("model_foundry_substitution_canary_r1.json")


def normalize(subject: str, selected: str, distribution: dict[str, float]) -> dict:
    return {
        "schemaVersion": 1,
        "operatorRef": "DECIDE",
        "subjectRef": subject,
        "candidateSetDigest": "sha256:canary-allow-deny-r1",
        "selectedCandidate": selected,
        "distribution": distribution,
        "confidence": max(distribution.values()),
        "calibrationRef": None,
        "qualificationRef": None,
        "abstainRecommended": False,
        "abstainReasons": [],
        "standing": "PROPOSAL",
        "evidenceRefs": ["fixture:model-foundry-substitution-canary-r1"],
        "explicitNonClaims": [
            "NOT_AUTHORIZATION",
            "NOT_EXECUTION_SUCCESS",
            "NOT_DOMAIN_COMPLETION",
        ],
    }


def deterministic_rule(score: float) -> dict:
    selected = "ALLOW" if score >= 0.5 else "DENY"
    distribution = {"ALLOW": 1.0, "DENY": 0.0} if selected == "ALLOW" else {"ALLOW": 0.0, "DENY": 1.0}
    return normalize("deterministic-rule-r1", selected, distribution)


def table_score(score: float) -> dict:
    distribution = {"ALLOW": score, "DENY": 1.0 - score}
    selected = max(distribution, key=distribution.get)
    return normalize("table-score-r1", selected, distribution)


def test_two_physical_plans_satisfy_one_logical_decision_shape() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["logicalOperator"] == "DECIDE"
    assert len(fixture["plans"]) == 2

    left = deterministic_rule(0.8)
    right = table_score(0.8)

    assert left["selectedCandidate"] == right["selectedCandidate"] == "ALLOW"
    assert left["operatorRef"] == right["operatorRef"] == "DECIDE"
    assert left["candidateSetDigest"] == right["candidateSetDigest"]
    assert set(left["explicitNonClaims"]) == set(right["explicitNonClaims"])


def test_decision_observation_contract_cannot_carry_authority_or_completion() -> None:
    schema = json.loads((FOUNDRY / "schemas" / "decision-observation-v1.schema.json").read_text(encoding="utf-8"))
    props = set(schema["properties"])
    assert "authorized" not in props
    assert "executionSucceeded" not in props
    assert "domainCompleted" not in props
    non_claims = set(schema["properties"]["explicitNonClaims"]["items"]["enum"])
    assert non_claims == {"NOT_AUTHORIZATION", "NOT_EXECUTION_SUCCESS", "NOT_DOMAIN_COMPLETION"}


def test_canary_is_not_misrepresented_as_real_model_qualification() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    text = " ".join(fixture["nonClaims"])
    assert "does not establish real-model equivalence" in text
    assert "does not qualify latency" in text
    assert "does not authorize" in text
