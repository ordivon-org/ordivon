from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_control_boundary_review.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_control_boundary" / "valid" / "good-process-bad-outcome.json"
BAD_LAUNDERING = (
    ROOT / "tests" / "fixtures" / "pgi_control_boundary" / "invalid" / "good-outcome-laundering.json"
)
BAD_QUADRANT = ROOT / "tests" / "fixtures" / "pgi_control_boundary" / "invalid" / "quadrant-mismatch.json"


spec = importlib.util.spec_from_file_location("validate_pgi_control_boundary_review", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_control_boundary_review_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_good_outcome_laundering_fails():
    ok, errors = validator.validate_file(BAD_LAUNDERING)
    assert ok is False
    assert "outcome_interpretation must not claim good outcome proves good process" in errors


def test_quadrant_mismatch_fails():
    ok, errors = validator.validate_file(BAD_QUADRANT)
    assert ok is False
    assert "process_outcome_quadrant must be good_process_bad_outcome" in errors[0]


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_LAUNDERING)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-control-boundary-review-validator" in captured.out
    assert "good-outcome-laundering" in captured.out
