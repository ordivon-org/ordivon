from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_personal_case_entry.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_personal_case" / "valid" / "builder-case.json"
BAD_PRIVATE = ROOT / "tests" / "fixtures" / "pgi_personal_case" / "invalid" / "private-externalized.json"
BAD_EMPTY = ROOT / "tests" / "fixtures" / "pgi_personal_case" / "invalid" / "no-artifacts.json"


spec = importlib.util.spec_from_file_location("validate_pgi_personal_case_entry", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_personal_case_entry_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_private_externalized_case_fails():
    ok, errors = validator.validate_file(BAD_PRIVATE)
    assert ok is False
    assert "raw_private_data_recorded must remain false for casebook entries" in errors
    assert "externalization_allowed=true requires privacy_level=public_safe" in errors
    assert any("publication approval" in e for e in errors)


def test_case_without_artifacts_fails():
    ok, errors = validator.validate_file(BAD_EMPTY)
    assert ok is False
    assert "artifact_refs must be a non-empty list of strings" in errors
    assert "review_refs must be a non-empty list of strings" in errors


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_PRIVATE)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-personal-case-entry-validator" in captured.out
    assert "private-externalized" in captured.out
