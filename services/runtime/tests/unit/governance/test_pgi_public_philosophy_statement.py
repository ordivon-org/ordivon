from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_public_philosophy_statement.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_public_philosophy" / "valid" / "about.json"
BAD_GUARANTEE = ROOT / "tests" / "fixtures" / "pgi_public_philosophy" / "invalid" / "guarantee.json"
BAD_BOUNDARY = ROOT / "tests" / "fixtures" / "pgi_public_philosophy" / "invalid" / "missing-boundary.json"


spec = importlib.util.spec_from_file_location("validate_pgi_public_philosophy_statement", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_public_philosophy_statement_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_guarantee_statement_fails():
    ok, errors = validator.validate_file(BAD_GUARANTEE)
    assert ok is False
    assert "personal_origin_disclosed must be true" in errors
    assert "statement must not contain success/therapy/finance/ultimate-truth guarantees" in errors
    assert any("not therapy" in e for e in errors)


def test_missing_advice_boundaries_fails():
    ok, errors = validator.validate_file(BAD_BOUNDARY)
    assert ok is False
    assert "not_advice_boundary must include 'not financial advice'" in errors
    assert "not_advice_boundary must include 'not life advice'" in errors


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_GUARANTEE)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-public-philosophy-statement-validator" in captured.out
    assert "guarantee" in captured.out
