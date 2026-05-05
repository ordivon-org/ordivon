from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_body_energy_review.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_body_energy" / "valid" / "tired-low-risk.json"
BAD_EXHAUSTED = ROOT / "tests" / "fixtures" / "pgi_body_energy" / "invalid" / "exhausted-high-risk.json"
BAD_RAW = ROOT / "tests" / "fixtures" / "pgi_body_energy" / "invalid" / "raw-private-data.json"


spec = importlib.util.spec_from_file_location("validate_pgi_body_energy_review", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_body_energy_review_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_exhausted_high_risk_blocks_major_decision():
    ok, errors = validator.validate_file(BAD_EXHAUSTED)
    assert ok is False
    assert "high-consequence decisions must be blocked under exhausted/ill/high-fatigue states" in errors


def test_raw_private_data_is_rejected():
    ok, errors = validator.validate_file(BAD_RAW)
    assert ok is False
    assert "raw_private_data_recorded must remain false for PGI-2.05 seed reviews" in errors
    assert any("not medical advice" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_EXHAUSTED)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-body-energy-review-validator" in captured.out
    assert "exhausted-high-risk" in captured.out
