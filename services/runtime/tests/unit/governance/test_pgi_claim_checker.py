from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "check_philosophical_claims.py"
CLEAN = ROOT / "tests" / "fixtures" / "pgi_claim_argument" / "clean"
FALSE_COMFORT = ROOT / "tests" / "fixtures" / "pgi_claim_argument" / "false_comfort"


spec = importlib.util.spec_from_file_location("check_philosophical_claims", SCRIPT)
assert spec is not None
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def test_clean_claim_fixture_has_no_findings():
    findings, stats = checker.scan_paths([CLEAN])
    assert stats["findings"] == 0
    assert findings == []


def test_false_comfort_fixture_blocks():
    findings, stats = checker.scan_paths([FALSE_COMFORT])
    assert stats["blocking"] >= 1
    assert any(f.rule_id == "PGI-CLAIM-001" for f in findings)
    assert any(f.rule_id == "PGI-CLAIM-002" for f in findings)


def test_json_cli_false_comfort_returns_blocked(capsys):
    exit_code = checker.main(["--json", str(FALSE_COMFORT)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-philosophical-claim-checker" in captured.out
    assert "PGI-CLAIM-001" in captured.out
