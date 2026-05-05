from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_anti_overforce_intake.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_anti_overforce" / "valid" / "coding-blockage-redesign.json"
BAD_UNKNOWN = ROOT / "tests" / "fixtures" / "pgi_anti_overforce" / "invalid" / "try-harder-unknown.json"
BAD_EXHAUSTED = ROOT / "tests" / "fixtures" / "pgi_anti_overforce" / "invalid" / "exhausted-continue.json"


spec = importlib.util.spec_from_file_location("validate_pgi_anti_overforce_intake", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_anti_overforce_intake_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_try_harder_with_unknown_constraints_fails():
    ok, errors = validator.validate_file(BAD_UNKNOWN)
    assert ok is False
    assert "overforce impulse with unknown constraints cannot continue without constraint classification" in errors


def test_exhausted_continuation_fails():
    ok, errors = validator.validate_file(BAD_EXHAUSTED)
    assert ok is False
    assert "stop signals require pause/rest/redesign/seek_help/refuse, not continuation" in errors
    assert any("does not authorize" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_UNKNOWN)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-anti-overforce-intake-validator" in captured.out
    assert "try-harder-unknown" in captured.out
