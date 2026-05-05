from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_review_to_rule_candidate.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_review_to_rule" / "valid" / "multiple-examples.json"
BAD_SINGLE = ROOT / "tests" / "fixtures" / "pgi_review_to_rule" / "invalid" / "single-anecdote-candidate.json"
BAD_EMOTION = ROOT / "tests" / "fixtures" / "pgi_review_to_rule" / "invalid" / "emotional-policy.json"


spec = importlib.util.spec_from_file_location("validate_pgi_review_to_rule_candidate", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_review_to_rule_candidate_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_single_anecdote_candidate_fails():
    ok, errors = validator.validate_file(BAD_SINGLE)
    assert ok is False
    assert "single anecdotes cannot become candidate rules without more evidence or high-severity rationale" in errors
    assert "candidate rules need multiple examples unless high_severity is declared" in errors
    assert "candidate rules must not use absolute overreaction language" in errors


def test_emotional_policy_candidate_fails():
    ok, errors = validator.validate_file(BAD_EMOTION)
    assert ok is False
    assert "emotionally intense candidate rules require cool_down_review_completed=true" in errors
    assert "candidate rules must not use absolute overreaction language" in errors
    assert any("no policy activation" in e for e in errors)
    assert any("does not authorize" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_SINGLE)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-review-to-rule-candidate-validator" in captured.out
    assert "single-anecdote-candidate" in captured.out
