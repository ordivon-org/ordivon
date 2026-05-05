from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_extended_mind_tool.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_extended_mind_tool" / "valid" / "codex.json"
BAD_REPLACE = ROOT / "tests" / "fixtures" / "pgi_extended_mind_tool" / "invalid" / "replaces-judgment.json"
BAD_DATA = ROOT / "tests" / "fixtures" / "pgi_extended_mind_tool" / "invalid" / "no-data-boundary.json"


spec = importlib.util.spec_from_file_location("validate_pgi_extended_mind_tool", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_extended_mind_tool_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_replacement_claim_fails():
    ok, errors = validator.validate_file(BAD_REPLACE)
    assert ok is False
    assert "replacement_claim_present must remain false" in errors
    assert "tool map must not claim the tool replaces human judgment or source-of-truth review" in errors
    assert any("tool is not authority" in e for e in errors)


def test_missing_data_boundary_fails():
    ok, errors = validator.validate_file(BAD_DATA)
    assert ok is False
    assert "data_boundary must state privacy, local, or redacted handling" in errors


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_REPLACE)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-extended-mind-tool-validator" in captured.out
    assert "replaces-judgment" in captured.out
