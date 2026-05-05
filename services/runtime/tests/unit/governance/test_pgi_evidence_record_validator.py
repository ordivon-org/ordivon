from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_evidence_record.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_evidence_record" / "valid" / "file-read.json"
BAD_AUTH = ROOT / "tests" / "fixtures" / "pgi_evidence_record" / "invalid" / "missing-authority-boundary.json"
BAD_CONF = ROOT / "tests" / "fixtures" / "pgi_evidence_record" / "invalid" / "bad-confidence.json"


spec = importlib.util.spec_from_file_location("validate_pgi_evidence_record", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_evidence_record_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_missing_authority_boundary_fails():
    ok, errors = validator.validate_file(BAD_AUTH)
    assert ok is False
    assert any("does not authorize action" in e for e in errors)


def test_bad_confidence_fails():
    ok, errors = validator.validate_file(BAD_CONF)
    assert ok is False
    assert "confidence must be between 0 and 1" in errors


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_AUTH)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-evidence-record-validator" in captured.out
    assert "missing-authority-boundary" in captured.out
