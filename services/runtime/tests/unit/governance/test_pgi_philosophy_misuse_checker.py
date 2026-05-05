from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "check_philosophy_misuse.py"
CLEAN = ROOT / "tests" / "fixtures" / "pgi_philosophy_misuse" / "clean"
UNSAFE = ROOT / "tests" / "fixtures" / "pgi_philosophy_misuse" / "unsafe"


spec = importlib.util.spec_from_file_location("check_philosophy_misuse", SCRIPT)
assert spec is not None
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def test_clean_philosophy_boundary_passes():
    findings, stats = checker.scan_paths([CLEAN])
    assert stats["findings"] == 0
    assert findings == []


def test_unsafe_philosophy_misuse_blocks():
    findings, stats = checker.scan_paths([UNSAFE])
    assert stats["blocking"] == 6
    assert {f.rule_id for f in findings} == {
        "PGI-MISUSE-001",
        "PGI-MISUSE-002",
        "PGI-MISUSE-003",
        "PGI-MISUSE-004",
        "PGI-MISUSE-005",
        "PGI-MISUSE-006",
    }


def test_cli_returns_failure_for_unsafe(capsys):
    exit_code = checker.main(["--json", str(UNSAFE)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-philosophy-misuse-checker" in captured.out
    assert "PGI-MISUSE-001" in captured.out
