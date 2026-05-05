from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_ethical_triad_review.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_ethical_triad" / "valid" / "review.json"
BAD_OUTCOME = (
    ROOT / "tests" / "fixtures" / "pgi_ethical_triad" / "invalid" / "outcome-proves-process.json"
)
BAD_MISSING = ROOT / "tests" / "fixtures" / "pgi_ethical_triad" / "invalid" / "missing-character.json"


spec = importlib.util.spec_from_file_location("validate_pgi_ethical_triad_review", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_ethical_triad_review_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_good_outcome_does_not_prove_good_process():
    ok, errors = validator.validate_file(BAD_OUTCOME)
    assert ok is False
    assert any("good outcome as proof" in e for e in errors)


def test_missing_character_review_fails():
    ok, errors = validator.validate_file(BAD_MISSING)
    assert ok is False
    assert "character_review must be a non-empty string" in errors
    assert "tradeoffs must be a non-empty array" in errors
    assert any("does not authorize action" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_OUTCOME)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-ethical-triad-review-validator" in captured.out
    assert "outcome-proves-process" in captured.out
