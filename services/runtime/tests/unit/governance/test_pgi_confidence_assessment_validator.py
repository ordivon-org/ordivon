from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_confidence_assessment.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_confidence_assessment" / "valid" / "high-confidence.json"
BAD_BASE = ROOT / "tests" / "fixtures" / "pgi_confidence_assessment" / "invalid" / "high-confidence-no-base-rate.json"
BAD_BAND = ROOT / "tests" / "fixtures" / "pgi_confidence_assessment" / "invalid" / "wrong-band.json"


spec = importlib.util.spec_from_file_location("validate_pgi_confidence_assessment", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_confidence_assessment_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_high_confidence_requires_base_rate():
    ok, errors = validator.validate_file(BAD_BASE)
    assert ok is False
    assert "confidence >= 0.7 requires numeric base_rate" in errors


def test_confidence_band_must_match_value():
    ok, errors = validator.validate_file(BAD_BAND)
    assert ok is False
    assert any("confidence_band must be VERY_HIGH" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_BASE)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-confidence-assessment-validator" in captured.out
    assert "high-confidence-no-base-rate" in captured.out
