from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_reversibility_assessment.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_reversibility_assessment" / "valid" / "local-doc.json"
BAD_REVIEW = (
    ROOT / "tests" / "fixtures" / "pgi_reversibility_assessment" / "invalid" / "high-side-effect-no-review.json"
)
BAD_UNKNOWN = ROOT / "tests" / "fixtures" / "pgi_reversibility_assessment" / "invalid" / "unknown-external.json"


spec = importlib.util.spec_from_file_location("validate_pgi_reversibility_assessment", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_reversibility_assessment_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_high_side_effect_requires_review():
    ok, errors = validator.validate_file(BAD_REVIEW)
    assert ok is False
    assert "financial side effects require review_required=true" in errors


def test_external_unknown_reversibility_fails():
    ok, errors = validator.validate_file(BAD_UNKNOWN)
    assert ok is False
    assert "high side-effect actions cannot have unknown reversibility" in errors
    assert any("does not authorize action" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_REVIEW)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-reversibility-assessment-validator" in captured.out
    assert "high-side-effect-no-review" in captured.out
