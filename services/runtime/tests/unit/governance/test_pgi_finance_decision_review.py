from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_pgi_finance_decision_review.py"
VALID = ROOT / "tests" / "fixtures" / "pgi_finance_decision" / "valid" / "review-only-hold.json"
BAD_FOMO = ROOT / "tests" / "fixtures" / "pgi_finance_decision" / "invalid" / "fomo-ready.json"
BAD_BROKER = ROOT / "tests" / "fixtures" / "pgi_finance_decision" / "invalid" / "broker-write.json"


spec = importlib.util.spec_from_file_location("validate_pgi_finance_decision_review", SCRIPT)
assert spec is not None
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def test_valid_finance_review_passes():
    ok, errors = validator.validate_file(VALID)
    assert ok is True
    assert errors == []


def test_fomo_ready_review_fails():
    ok, errors = validator.validate_file(BAD_FOMO)
    assert ok is False
    assert "block-level FOMO/gambling risk requires hold or reject posture" in errors
    assert "thesis must not contain guaranteed-profit language" in errors


def test_broker_write_boundary_fails():
    ok, errors = validator.validate_file(BAD_BROKER)
    assert ok is False
    assert "live_trading_no_go must remain true in PGI-2.06" in errors
    assert "broker_write_boundary must state no broker write" in errors
    assert any("not financial advice" in e for e in errors)


def test_cli_returns_failure_for_invalid(capsys):
    exit_code = validator.main([str(VALID), str(BAD_FOMO)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-finance-decision-review-validator" in captured.out
    assert "fomo-ready" in captured.out
