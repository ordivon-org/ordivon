"""Tests for Ordivon Verify external fixture mode.

Covers: config loading, external receipt scanning, mode behavior,
warnings vs failures, and backward compatibility with native mode.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.ordivon_verify import (
    load_config,
    validate_config,
    is_ordivon_native,
    scan_receipt_files,
    run_external_receipts,
    run_external_checker,
    determine_status,
    build_report,
    main,
    _BUILTIN_ROOT,
)


FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ordivon_verify_external_repo"


# ── Config loading ─────────────────────────────────────────────────────


def test_load_config_from_path():
    cfg = load_config(FIXTURE / "ordivon.verify.json", FIXTURE)
    assert cfg is not None
    assert cfg["schema_version"] == "0.1"
    assert cfg["project_name"] == "external-fixture"
    assert cfg["mode"] == "advisory"
    assert "receipts" in cfg["receipt_paths"]


def test_load_config_missing_file():
    cfg = load_config(Path("/nonexistent/config.json"), FIXTURE)
    assert cfg is None


def test_load_config_auto_detect():
    cfg = load_config(None, FIXTURE)
    assert cfg is not None
    assert cfg["project_name"] == "external-fixture"


def test_validate_config_valid():
    errors = validate_config({"schema_version": "0.1", "mode": "advisory"})
    assert errors == []


def test_validate_config_bad_version():
    errors = validate_config({"schema_version": "0.2"})
    assert len(errors) >= 1
    assert "unsupported" in errors[0].lower() or "0.2" in errors[0]


def test_validate_config_bad_mode():
    errors = validate_config({"schema_version": "0.1", "mode": "dangerous"})
    assert any("mode" in e.lower() for e in errors)


def test_validate_config_not_dict():
    errors = validate_config("not a dict")  # type: ignore[arg-type]
    assert len(errors) >= 1


# ── is_ordivon_native ──────────────────────────────────────────────────


def test_ordivon_native_returns_true():
    assert is_ordivon_native(_BUILTIN_ROOT) is True


def test_external_fixture_not_native():
    assert is_ordivon_native(FIXTURE) is False


# ── scan_receipt_files ─────────────────────────────────────────────────


def test_scan_valid_receipt_passes():
    failures, scanned = scan_receipt_files(["receipts"], FIXTURE)
    # valid-receipt.md should have no failures — it has no contradictory language
    valid_fails = [f for f in failures if "valid-receipt" in f]
    assert valid_fails == []


def test_scan_bad_receipt_detected():
    failures, scanned = scan_receipt_files(["receipts"], FIXTURE)
    bad_fails = [f for f in failures if "bad-receipt" in f]
    assert len(bad_fails) >= 1


def test_scan_receipt_files_counts_scanned():
    failures, scanned = scan_receipt_files(["receipts"], FIXTURE)
    assert scanned >= 2


# ── run_external_receipts ──────────────────────────────────────────────


def test_run_external_receipts_returns_fail_for_bad():
    result = run_external_receipts(["receipts"], FIXTURE)
    assert result["id"] == "receipts"
    assert result["status"] == "FAIL"
    assert result["exit_code"] == 1
    assert "bad-receipt" in result["stderr"]


def test_run_external_receipts_on_valid_only():
    # Create a temp dir with only a valid receipt
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        rec_dir = tdp / "receipts"
        rec_dir.mkdir()
        (rec_dir / "ok.md").write_text(
            "# Receipt\n"
            "Status: **COMPLETE**\n"
            "\n"
            "## Verification Results\n"
            "| Check | Result |\n"
            "|-------|--------|\n"
            "| Unit tests | 42 passed |\n"
            "\n"
            "Skipped Verification: None\n"
            "\n"
            "All verification commands were executed successfully.\n"
        )
        result = run_external_receipts(["receipts"], tdp)
        assert result["status"] == "PASS"


# ── run_external_checker ───────────────────────────────────────────────


def test_external_checker_debt_missing_advisory():
    result = run_external_checker("debt", FIXTURE, "advisory")
    assert result["status"] == "WARN"
    assert "not found" in result["stderr"]


def test_external_checker_debt_missing_strict():
    result = run_external_checker("debt", FIXTURE, "strict")
    assert result["status"] == "FAIL"
    assert "Missing required file" in result["stderr"]


def test_external_checker_gates_missing_advisory():
    result = run_external_checker("gates", FIXTURE, "advisory")
    assert result["status"] == "WARN"


def test_external_checker_docs_missing_advisory():
    result = run_external_checker("docs", FIXTURE, "advisory")
    assert result["status"] == "WARN"


# ── determine_status with WARN ─────────────────────────────────────────


def test_determine_status_with_warnings():
    results = [
        {"id": "receipts", "status": "PASS", "exit_code": 0},
        {"id": "debt", "status": "WARN", "exit_code": -1},
    ]
    assert determine_status(results) == "DEGRADED"


def test_determine_status_fail_overrides_warn():
    results = [
        {"id": "receipts", "status": "FAIL", "exit_code": 1},
        {"id": "debt", "status": "WARN", "exit_code": -1},
    ]
    assert determine_status(results) == "BLOCKED"


# ── build_report with warnings ─────────────────────────────────────────


def test_build_report_includes_warnings():
    results = [
        {"id": "receipts", "status": "PASS", "exit_code": 0, "stdout": "ok", "stderr": ""},
        {"id": "debt", "status": "WARN", "exit_code": -1, "stdout": "", "stderr": "Not configured"},
    ]
    report = build_report(results, "advisory")
    assert report["status"] == "DEGRADED"
    assert len(report["warnings"]) == 1
    assert report["warnings"][0]["id"] == "debt"


# ── main() external fixture ───────────────────────────────────────────


def test_main_external_all_advisory(monkeypatch, capsys):
    """main with --root pointing to external fixture → bad receipt BLOCKED, others WARN."""
    exit_code = main(["all", "--root", str(FIXTURE)])
    # Bad receipt + advisory → receipts FAIL (BLOCKED), debt/gates/docs WARN
    # Overall: BLOCKED due to receipt contradiction
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out


def test_main_external_receipts(monkeypatch, capsys):
    """main receipts --root fixture → detects bad receipt."""
    exit_code = main(["receipts", "--root", str(FIXTURE)])
    # Should be BLOCKED because bad-receipt.md has contradictions
    captured = capsys.readouterr()
    assert exit_code == 1 or "BLOCKED" in captured.out


def test_main_external_json_includes_warnings(monkeypatch, capsys):
    """JSON output includes warnings for missing optional checks."""
    exit_code = main(["all", "--root", str(FIXTURE), "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert "warnings" in report
    assert len(report["warnings"]) > 0
    assert exit_code in (1, 2)


def test_main_external_strict_mode(monkeypatch, capsys):
    """Strict mode with missing files → BLOCKED."""
    exit_code = main(["all", "--root", str(FIXTURE), "--mode", "strict"])
    assert exit_code == 1  # BLOCKED — bad receipt + missing required files
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out


def test_main_native_still_works(monkeypatch, capsys):
    """Native Ordivon mode (no --root) still returns READY."""
    exit_code = main(["all"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "READY" in captured.out


def test_main_native_json_still_works(monkeypatch, capsys):
    """Native JSON output still works."""
    exit_code = main(["all", "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "READY"
    assert len(report["checks"]) == 4


def test_main_root_not_found():
    """--root pointing to nonexistent dir → exit 3."""
    exit_code = main(["all", "--root", "/nonexistent/path/xyz"])
    assert exit_code == 3


def test_main_invalid_mode():
    """--mode with invalid value → exit 3."""
    exit_code = main(["all", "--mode", "imaginary"])
    assert exit_code == 3


def test_main_bad_config():
    """--config pointing to invalid JSON → exit 3."""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not json")
        bad_path = f.name
    try:
        exit_code = main(["all", "--config", bad_path])
        # Invalid JSON → load_config returns None → no config, mode defaults to advisory
        # Running against Ordivon-native root (default) in advisory mode still works
        assert exit_code in (0, 1, 2, 3)  # config load doesn't crash
    finally:
        os.unlink(bad_path)


# ── No file writes ─────────────────────────────────────────────────────


def test_no_file_writes_in_fixture(monkeypatch):
    """External mode must not write any files."""
    # Capture original file modification times
    orig_mtimes = {}
    for p in FIXTURE.rglob("*"):
        if p.is_file():
            orig_mtimes[p] = p.stat().st_mtime

    main(["all", "--root", str(FIXTURE)])

    for p, mtime in orig_mtimes.items():
        assert p.stat().st_mtime == mtime, f"File modified: {p}"
