from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "research" / "fixtures" / "research-fresh-agent-corpus-r1.json"

EXPECTED_FAMILIES = {
    "work_owner_cold_entry",
    "legal_skill_route",
    "wrong_owner_route",
    "stale_owner_route",
    "evidence_synthesis_hold",
    "tool_selection_owner_hold",
}

FORBIDDEN_TOP_LEVEL_KEYS = {
    "accuracy",
    "score",
    "pass",
    "passed",
    "effectiveness",
    "modelIndependence",
    "scientificValidity",
}

PAPER_SPECIFIC_TOKENS = tuple(f"paper{index}" for index in range(1, 6))

def iter_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from iter_strings(key)
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)

def reject_paper_specific_case_payload(row: dict) -> None:
    for text in iter_strings(row):
        if any(token in text.casefold() for token in PAPER_SPECIFIC_TOKENS):
            raise ValueError(f"case payload cannot reference Paper1-Paper5: {row.get('caseId')}")


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def validate_fixture(value: dict) -> None:
    if value.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    if value.get("kind") != "ordivon.research-fresh-agent-corpus":
        raise ValueError("kind mismatch")
    if value.get("corpusId") != "research-fresh-agent-corpus-r1":
        raise ValueError("corpusId mismatch")
    if value.get("standing") != "STRUCTURALLY_DEFINED_NOT_EXECUTED":
        raise ValueError("standing must remain NOT_EXECUTED")
    if FORBIDDEN_TOP_LEVEL_KEYS.intersection(value):
        raise ValueError("fixture cannot encode efficacy or scientific result")
    nonclaims = set(value.get("nonClaims", []))
    required_nonclaims = {
        "fresh_agent_effectiveness",
        "model_independence",
        "scientific_validity",
        "paper_resume",
        "provider_authority",
    }
    if not required_nonclaims.issubset(nonclaims):
        raise ValueError("missing required nonClaims")
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) != 10:
        raise ValueError("exactly 10 cases required")
    ids = [row.get("caseId") for row in cases]
    if any(not isinstance(case_id, str) or not case_id for case_id in ids):
        raise ValueError("caseId must be non-empty text")
    if len(ids) != len(set(ids)):
        raise ValueError("caseId must be unique")
    families = {row.get("family") for row in cases}
    if families != EXPECTED_FAMILIES:
        raise ValueError("six-family census mismatch")
    for row in cases:
        reject_paper_specific_case_payload(row)
        if row.get("standing") != "NOT_EXECUTED":
            raise ValueError(f"case must be NOT_EXECUTED: {row.get('caseId')}")
        if row.get("observedResult") is not None:
            raise ValueError(f"unexecuted case cannot carry observedResult: {row.get('caseId')}")
        owner = row.get("ownerCurrentnessAtRun")
        if not isinstance(owner, dict):
            raise ValueError(f"ownerCurrentnessAtRun required: {row.get('caseId')}")
        if owner.get("required") is not True:
            raise ValueError(f"owner currentness must be required: {row.get('caseId')}")
        if owner.get("standing") != "MUST_REVALIDATE_AT_RUN":
            raise ValueError(f"copied fixture cannot claim owner currentness: {row.get('caseId')}")
        if not isinstance(owner.get("ownerRef"), str) or not owner["ownerRef"]:
            raise ValueError(f"ownerRef required: {row.get('caseId')}")
        if not isinstance(row.get("expectedDecisionClass"), str) or not row["expectedDecisionClass"]:
            raise ValueError(f"expectedDecisionClass required: {row.get('caseId')}")


class ResearchFreshAgentCorpusR1Tests(unittest.TestCase):
    def test_fixture_exists_on_current_source(self) -> None:
        self.assertTrue(FIXTURE.is_file(), f"missing current-source fixture: {FIXTURE}")

    def test_fixture_contract_is_structurally_valid_but_not_executed(self) -> None:
        value = load_fixture()
        try:
            validate_fixture(value)
        except ValueError as exc:
            self.fail(str(exc))

    def test_duplicate_case_id_is_rejected(self) -> None:
        value = load_fixture()
        value["cases"][1]["caseId"] = value["cases"][0]["caseId"]
        with self.assertRaisesRegex(ValueError, "caseId must be unique"):
            validate_fixture(value)

    def test_missing_owner_currentness_is_rejected(self) -> None:
        value = load_fixture()
        value["cases"][0].pop("ownerCurrentnessAtRun")
        with self.assertRaisesRegex(ValueError, "ownerCurrentnessAtRun required"):
            validate_fixture(value)

    def test_copied_owner_currentness_claim_is_rejected(self) -> None:
        value = load_fixture()
        value["cases"][0]["ownerCurrentnessAtRun"]["standing"] = "CURRENT"
        with self.assertRaisesRegex(ValueError, "cannot claim owner currentness"):
            validate_fixture(value)

    def test_observed_result_on_unexecuted_case_is_rejected(self) -> None:
        value = load_fixture()
        value["cases"][0]["observedResult"] = {"standing": "PASS"}
        with self.assertRaisesRegex(ValueError, "unexecuted case cannot carry observedResult"):
            validate_fixture(value)

    def test_fixture_cannot_encode_aggregate_effectiveness(self) -> None:
        value = load_fixture()
        value["accuracy"] = 1.0
        with self.assertRaisesRegex(ValueError, "cannot encode efficacy"):
            validate_fixture(value)

    def test_nested_paper_specific_case_reference_is_rejected(self) -> None:
        value = load_fixture()
        value["cases"][4]["fixtureInput"] = {
            "nested": {
                "ownerRef": "host-work:work:research:paper3-example:r1",
            }
        }
        with self.assertRaisesRegex(ValueError, "cannot reference Paper1-Paper5"):
            validate_fixture(value)


if __name__ == "__main__":
    unittest.main()
