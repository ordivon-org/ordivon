from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_ai_philosophical_onboarding.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_ai_onboarding" / "valid" / "collaborator.json"
BAD_AUTH = ROOT / "tests" / "fixtures" / "pgi_ai_onboarding" / "invalid" / "authority-overreach.json"
BAD_BOUNDARY = ROOT / "tests" / "fixtures" / "pgi_ai_onboarding" / "invalid" / "missing-boundaries.json"


spec = importlib.util.spec_from_file_location("validate_pgi_ai_philosophical_onboarding", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_ai_philosophical_onboarding_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_authority_overreach_fails():
    ok, errors = validator.validate_file(BAD_AUTH)
    assert ok is False
    assert any("forbidden_patterns missing required patterns" in e for e in errors)
    assert "onboarding text must not contain authority-overreach language" in errors
    assert any("authority over the creator" in e for e in errors)


def test_missing_required_boundaries_fails():
    ok, errors = validator.validate_file(BAD_BOUNDARY)
    assert ok is False
    assert "required_boundaries must include 'not financial advice'" in errors
    assert "required_boundaries must include 'candidate rule is not policy'" in errors
    assert "required_boundaries must include 'privacy boundary'" in errors


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_AUTH)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-ai-philosophical-onboarding-validator" in captured.out
    assert "authority-overreach" in captured.out
