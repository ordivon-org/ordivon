from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts" / "governance"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import aos_action_audit as audit  # noqa: E402


FIXTURE_DIR = ROOT / "examples" / "aos" / "ai-action-declaration-dogfood"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def schema_errors(declaration: dict, observed: dict) -> tuple[list[str], list[str]]:
    return (
        audit.validate_with_schema(declaration, audit.DECL_SCHEMA),
        audit.validate_with_schema(observed, audit.OBS_SCHEMA),
    )


def evaluate(declaration: dict, observed: dict) -> dict:
    declaration_errors, observed_errors = schema_errors(declaration, observed)
    return audit.evaluate(declaration, observed, declaration_errors, observed_errors)


def test_aos_exact_match_verdict() -> None:
    result = evaluate(load_fixture("object.aos.json"), load_fixture("observed.match.json"))

    assert result["verdict"] == "ExactMatch"
    assert result["result"] == "MATCH"
    assert result["findings"] == []


def test_aos_under_verdict_when_expected_output_missing() -> None:
    observed = load_fixture("observed.match.json")
    observed["object_id"] = "aos:actions:ObservedAction:create-candidate-rule-dogfood-under"
    observed["observed_files_modified"] = []

    result = evaluate(load_fixture("object.aos.json"), observed)

    assert result["verdict"] == "Under"
    assert result["result"] == "MISMATCH"
    assert {item["finding_type"] for item in result["findings"]} == {"EXPECTED_OUTPUT_MISSING"}


def test_aos_over_verdict_when_declared_output_has_extra_path() -> None:
    result = evaluate(load_fixture("object.aos.json"), load_fixture("observed.scope-mismatch.json"))

    assert result["verdict"] == "Over"
    assert result["result"] == "MISMATCH"
    assert any(item["finding_type"] == "SCOPE_MISMATCH" for item in result["findings"])


def test_aos_mis_verdict_when_wrong_target_replaces_declared_target() -> None:
    observed = load_fixture("observed.match.json")
    observed["object_id"] = "aos:actions:ObservedAction:create-candidate-rule-dogfood-mis"
    observed["observed_files_modified"] = ["docs/governance/document-registry.jsonl"]

    result = evaluate(load_fixture("object.aos.json"), observed)

    assert result["verdict"] == "Mis"
    assert result["result"] == "MISMATCH"
    assert {item["finding_type"] for item in result["findings"]} == {
        "EXPECTED_OUTPUT_MISSING",
        "SCOPE_MISMATCH",
    }


def test_aos_declaration_invalid_for_unknown_action() -> None:
    result = evaluate(load_fixture("object.unknown-action.aos.json"), load_fixture("observed.match.json"))

    assert result["verdict"] == "DeclarationInvalid"
    assert result["result"] == "MISMATCH"
    assert any(item["finding_type"] == "DECLARATION_INVALID" for item in result["findings"])


def test_aos_unverifiable_when_observation_sources_missing() -> None:
    result = evaluate(load_fixture("object.aos.json"), load_fixture("observed.unknown.json"))

    assert result["verdict"] == "Unverifiable"
    assert result["result"] == "UNKNOWN"
    assert any(item["finding_type"] == "UNVERIFIABLE" for item in result["findings"])


def test_ai_written_observation_is_not_accepted_as_system_observed() -> None:
    forged = copy.deepcopy(load_fixture("observed.match.json"))
    forged["object_id"] = "aos:actions:ObservedAction:create-candidate-rule-dogfood-forged"
    forged["origin"] = "AI_WRITTEN"
    forged["created_by"] = "codex"
    forged["provenance"]["collector"] = "ai_agent"
    forged["observation_sources"] = ["AI_WRITTEN:self-report"]

    result = evaluate(load_fixture("object.aos.json"), forged)

    assert result["verdict"] == "SystemError"
    assert result["result"] == "UNKNOWN"
    assert any(item["finding_type"] == "SYSTEM_ERROR" for item in result["findings"])


def test_authorization_claim_in_receipt_triggers_blocking_finding(tmp_path, monkeypatch) -> None:
    receipt_path = tmp_path / "receipts" / "auth.json"
    receipt_path.parent.mkdir()
    receipt_path.write_text(json.dumps({"authorization": {"status": "approved"}}))
    monkeypatch.setattr(audit, "ROOT", tmp_path)

    observed = load_fixture("observed.match.json")
    observed["object_id"] = "aos:actions:ObservedAction:create-candidate-rule-dogfood-auth"
    observed["observed_receipts"] = ["receipts/auth.json"]

    result = evaluate(load_fixture("object.aos.json"), observed)

    assert result["verdict"] == "Mis"
    assert any(
        item["finding_type"] == "FORBIDDEN_ACTION" and item["declared"] == "claim_authorization"
        for item in result["findings"]
    )
