from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_constitution_boundary_matrix.py"
MATRIX = ROOT / "docs" / "governance" / "constitution-boundary-matrix-pgi-1.json"
BAD = ROOT / "tests" / "fixtures" / "pgi_constitution_boundary" / "invalid" / "active-policy.json"


spec = importlib.util.spec_from_file_location("validate_constitution_boundary_matrix", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_constitution_boundary_matrix_passes():
    ok, errors = validator.validate_file(MATRIX)
    assert ok is True
    assert errors == []


def test_active_policy_fixture_fails():
    ok, errors = validator.validate_file(BAD)
    assert ok is False
    assert any("no action authorization" in e for e in errors)
    assert any("invalid classification" in e for e in errors)
    assert any("invalid activation_status" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(MATRIX), str(BAD)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-constitution-boundary-matrix-validator" in captured.out
    assert "active-policy" in captured.out
