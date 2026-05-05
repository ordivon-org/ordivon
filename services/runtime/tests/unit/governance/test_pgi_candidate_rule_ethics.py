from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_candidate_rule_ethics.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_candidate_rule_ethics" / "valid" / "scoped-rule.json"
BAD_CONTROL = ROOT / "tests" / "fixtures" / "pgi_candidate_rule_ethics" / "invalid" / "over-control.json"
BAD_POLICY = ROOT / "tests" / "fixtures" / "pgi_candidate_rule_ethics" / "invalid" / "policy-activation.json"


spec = importlib.util.spec_from_file_location("validate_pgi_candidate_rule_ethics", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_candidate_rule_ethics_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_over_control_candidate_fails():
    ok, errors = validator.validate_file(BAD_CONTROL)
    assert ok is False
    assert "block-level over-control risk cannot remain candidate" in errors
    assert "candidate rules must not contain over-control language" in errors


def test_policy_activation_fails():
    ok, errors = validator.validate_file(BAD_POLICY)
    assert ok is False
    assert "policy_activation_no_go must remain true" in errors
    assert any("candidate only" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_CONTROL)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-candidate-rule-ethics-validator" in captured.out
    assert "over-control" in captured.out
