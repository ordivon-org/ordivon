from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_builder_change_review.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_builder_change" / "valid" / "validator-seed.json"
BAD_COMPLEXITY = ROOT / "tests" / "fixtures" / "pgi_builder_change" / "invalid" / "hidden-complexity.json"
BAD_BOUNDARY = ROOT / "tests" / "fixtures" / "pgi_builder_change" / "invalid" / "no-tests-no-boundary.json"


spec = importlib.util.spec_from_file_location("validate_pgi_builder_change_review", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_builder_change_review_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_hidden_complexity_fails():
    ok, errors = validator.validate_file(BAD_COMPLEXITY)
    assert ok is False
    assert "complexity-increasing changes must declare debt" in errors
    assert "complexity-increasing changes must pass anti-overforce review" in errors
    assert "improves_decision_maker must explain the governance benefit" in errors


def test_missing_tests_and_boundary_fails():
    ok, errors = validator.validate_file(BAD_BOUNDARY)
    assert ok is False
    assert "tests_or_receipts must be a list of non-empty strings" in errors
    assert any("does not authorize" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_COMPLEXITY)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-builder-change-review-validator" in captured.out
    assert "hidden-complexity" in captured.out
