from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_externalization_alignment.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_externalization_alignment" / "valid" / "alpha0.json"
BAD_PLATFORM = ROOT / "tests" / "fixtures" / "pgi_externalization_alignment" / "invalid" / "platform-claim.json"
BAD_CASEBOOK = ROOT / "tests" / "fixtures" / "pgi_externalization_alignment" / "invalid" / "no-casebook.json"


spec = importlib.util.spec_from_file_location("validate_pgi_externalization_alignment", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_externalization_alignment_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_platform_claim_fails():
    ok, errors = validator.validate_file(BAD_PLATFORM)
    assert ok is False
    assert "internal_root_preserved must be true" in errors
    assert "schema_public_claim must remain false in PGI-3.08" in errors
    assert "externalization alignment must not claim public standard/platform/SDK/MCP/adapter release" in errors
    assert any("release approval" in e for e in errors)


def test_no_casebook_fails():
    ok, errors = validator.validate_file(BAD_CASEBOOK)
    assert ok is False
    assert "casebook_refs must be a non-empty list of strings" in errors
    assert "external_claim must stay anchored to trust audit or governed work" in errors


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_PLATFORM)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-externalization-alignment-validator" in captured.out
    assert "platform-claim" in captured.out
