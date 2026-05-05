from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_relationship_emotion_review.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_relationship_emotion" / "valid" / "boundary-review.json"
BAD_RAW = ROOT / "tests" / "fixtures" / "pgi_relationship_emotion" / "invalid" / "raw-private.json"
BAD_MANIP = ROOT / "tests" / "fixtures" / "pgi_relationship_emotion" / "invalid" / "manipulation-block.json"


spec = importlib.util.spec_from_file_location("validate_pgi_relationship_emotion_review", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_relationship_emotion_review_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_raw_private_data_fails():
    ok, errors = validator.validate_file(BAD_RAW)
    assert ok is False
    assert "raw_private_data_recorded must remain false for relationship/emotion seed reviews" in errors
    assert "do_not_record_acknowledged must be true" in errors
    assert "high emotion plus high-consequence decision requires decision_delay_required=true" in errors


def test_manipulation_block_requires_safe_step():
    ok, errors = validator.validate_file(BAD_MANIP)
    assert ok is False
    assert "block-level manipulation risk requires pause/repair/boundary/seek-help/delay step" in errors


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_RAW)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-relationship-emotion-review-validator" in captured.out
    assert "raw-private" in captured.out
