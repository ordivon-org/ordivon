from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_self_model_entry.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_self_model" / "valid" / "not-enough-evidence.json"
BAD_VERDICT = ROOT / "tests" / "fixtures" / "pgi_self_model" / "invalid" / "punitive-verdict.json"
BAD_CONFIRMED = ROOT / "tests" / "fixtures" / "pgi_self_model" / "invalid" / "confirmed-with-one-evidence.json"


spec = importlib.util.spec_from_file_location("validate_pgi_self_model_entry", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_self_model_entry_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_punitive_verdict_fails():
    ok, errors = validator.validate_file(BAD_VERDICT)
    assert ok is False
    assert "verdict_language_present must remain false" in errors
    assert "self_language must not contain fixed or punitive identity verdicts" in errors
    assert any("not a verdict" in e for e in errors)


def test_confirmed_pattern_requires_multiple_evidence_refs():
    ok, errors = validator.validate_file(BAD_CONFIRMED)
    assert ok is False
    assert "confirmed_pattern requires at least two evidence_refs" in errors


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_VERDICT)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-self-model-entry-validator" in captured.out
    assert "punitive-verdict" in captured.out
