from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "checkers" / "egb3-operating-governance" / "run.py"
FIXTURES = ROOT / "tests" / "fixtures" / "egb3_operating"

spec = importlib.util.spec_from_file_location("egb3_operating_governance", SCRIPT)
assert spec is not None
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def test_detects_reviewer_approver_confusion():
    text = "The reviewer approves this OEP for release."

    assert "reviewer_approver_confusion" in checker.detect_operating_violations(text)


def test_detects_ownerless_approval():
    text = "Approval is granted without owner review because the change looks small."

    assert "ownerless_approval" in checker.detect_operating_violations(text)


def test_detects_shadow_hard_laundering():
    text = "The shadow-tested checker is now a hard gate and must pass for merge."

    assert "shadow_hard_laundering" in checker.detect_operating_violations(text)


def test_detects_freeze_authorization():
    text = "The closure freeze approves new scope because final verification has started."

    assert "freeze_authorization" in checker.detect_operating_violations(text)


def test_detects_trust_budget_expansion():
    text = "The trust budget is spent, but the stage can continue with new scope and ship anyway."

    assert "trust_budget_expansion" in checker.detect_operating_violations(text)


def test_valid_redteam_ledger_passes():
    errors = checker.validate_redteam_ledger(FIXTURES / "valid" / "redteam.jsonl")

    assert errors == []


def test_mismatched_redteam_ledger_fails():
    errors = checker.validate_redteam_ledger(FIXTURES / "invalid" / "mismatched-redteam.jsonl")

    assert any("expected trust_budget_expansion" in e for e in errors)


def test_egb3_document_passes():
    assert checker.validate_egb3_document() == []
