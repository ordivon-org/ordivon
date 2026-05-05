from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_memory_content_record.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_memory_content" / "valid" / "current-receipt-summary.json"
BAD_POLICY = ROOT / "tests" / "fixtures" / "pgi_memory_content" / "invalid" / "candidate-policy.json"
BAD_STALE = ROOT / "tests" / "fixtures" / "pgi_memory_content" / "invalid" / "stale-safe.json"


spec = importlib.util.spec_from_file_location("validate_pgi_memory_content_record", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_memory_content_record_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_candidate_rule_as_policy_fails():
    ok, errors = validator.validate_file(BAD_POLICY)
    assert ok is False
    assert "CandidateRule memory cannot be source_of_truth" in errors
    assert "candidate_rule_as_policy contamination requires do_not_use" in errors


def test_stale_degraded_safe_memory_fails():
    ok, errors = validator.validate_file(BAD_STALE)
    assert ok is False
    assert "missing source_receipt must set missing_source contamination flag" in errors
    assert "stale/superseded/unknown memory cannot be safe_to_use" in errors
    assert "degraded_as_fact contamination requires do_not_use" in errors
    assert any("not source of truth" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_POLICY)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-memory-content-record-validator" in captured.out
    assert "candidate-policy" in captured.out
