from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_failure_predicate.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_failure_predicate" / "valid" / "roadmap-claim.json"
BAD_NON_FALSIFIABLE = (
    ROOT / "tests" / "fixtures" / "pgi_failure_predicate" / "invalid" / "non-falsifiable.json"
)
BAD_AUTH = (
    ROOT / "tests" / "fixtures" / "pgi_failure_predicate" / "invalid" / "no-authority-boundary.json"
)


spec = importlib.util.spec_from_file_location("validate_pgi_failure_predicate", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_failure_predicate_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_non_falsifiable_predicate_fails():
    ok, errors = validator.validate_file(BAD_NON_FALSIFIABLE)
    assert ok is False
    assert any("non-falsifiable marker" in e for e in errors)


def test_missing_authority_boundary_fails():
    ok, errors = validator.validate_file(BAD_AUTH)
    assert ok is False
    assert any("does not authorize action" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_NON_FALSIFIABLE)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-failure-predicate-validator" in captured.out
    assert "non-falsifiable" in captured.out
