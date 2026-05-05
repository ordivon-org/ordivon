from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_decision_gate.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_decision_gate" / "valid" / "ready-without-authorization.json"
BAD_MISSING = ROOT / "tests" / "fixtures" / "pgi_decision_gate" / "invalid" / "ready-with-missing-evidence.json"
BAD_AUTH = ROOT / "tests" / "fixtures" / "pgi_decision_gate" / "invalid" / "authorizes-execution.json"


spec = importlib.util.spec_from_file_location("validate_pgi_decision_gate", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_decision_gate_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_ready_cannot_have_missing_evidence():
    ok, errors = validator.validate_file(BAD_MISSING)
    assert ok is False
    assert "READY_WITHOUT_AUTHORIZATION cannot have missing_evidence" in errors
    assert "high/irreversible READY posture cannot have unknown reversibility" in errors


def test_authorizing_execution_fails():
    ok, errors = validator.validate_file(BAD_AUTH)
    assert ok is False
    assert any("does not authorize execution" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_AUTH)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-decision-gate-validator" in captured.out
    assert "authorizes-execution" in captured.out
