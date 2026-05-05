from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_learning_review.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_learning" / "valid" / "philosophy-to-governance.json"
BAD_READ = ROOT / "tests" / "fixtures" / "pgi_learning" / "invalid" / "read-more-only.json"
BAD_BLOCK = ROOT / "tests" / "fixtures" / "pgi_learning" / "invalid" / "block-without-pause.json"


spec = importlib.util.spec_from_file_location("validate_pgi_learning_review", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_learning_review_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_read_more_only_fails():
    ok, errors = validator.validate_file(BAD_READ)
    assert ok is False
    assert "output_artifact must name a concrete output, not consumption only" in errors
    assert "next_application must apply learning, not only read/watch/study more" in errors


def test_block_without_pause_fails():
    ok, errors = validator.validate_file(BAD_BLOCK)
    assert ok is False
    assert "block-level consumption loop risk requires a pause or application-first next step" in errors
    assert any("does not authorize" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_READ)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-learning-review-validator" in captured.out
    assert "read-more-only" in captured.out
