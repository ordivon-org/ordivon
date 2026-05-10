from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "check_current_truth_protocol.py"
CLEAN = ROOT / "tests" / "fixtures" / "pgi_current_truth" / "clean"
UNSAFE = ROOT / "tests" / "fixtures" / "pgi_current_truth" / "unsafe"


spec = importlib.util.spec_from_file_location("check_current_truth_protocol", SCRIPT)
assert spec is not None
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def test_clean_current_truth_fixture_passes():
    findings, stats = checker.scan_paths([CLEAN])
    assert stats["findings"] == 0
    assert findings == []


def test_unsafe_current_truth_fixture_blocks():
    # Pass individual files: checker._iter_files filters "/unsafe" paths
    unsafe_files = list(UNSAFE.glob("*"))
    assert len(unsafe_files) >= 2, f"Expected >=2 fixture files, got {len(unsafe_files)}"
    findings, stats = checker.scan_paths(unsafe_files)
    assert stats["blocking"] == 2
    assert {f.rule_id for f in findings} == {"PGI-TRUTH-001", "PGI-TRUTH-002"}


def test_cli_returns_failure_for_unsafe(capsys):
    unsafe_files = list(UNSAFE.glob("*"))
    exit_code = checker.main(["--json"] + [str(f) for f in unsafe_files])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "pgi-current-truth-protocol-checker" in captured.out
    assert "PGI-TRUTH-001" in captured.out
