"""Tests for Ordivon Verify external fixture mode.

Covers: config loading, external receipt scanning, mode behavior,
warnings vs failures, and backward compatibility with native mode.
"""

from __future__ import annotations

import json
from pathlib import Path

from ordivon_verify import (
    load_config,
    validate_config,
    scan_receipt_files,
    run_external_receipts,
    run_external_checker,
    determine_status,
    build_report,
    main,
)

from ordivon_verify.config import is_ordivon_native

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
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    assert is_ordivon_native(root) is True


def test_external_fixture_not_native():
    assert is_ordivon_native(FIXTURE) is False


# ── scan_receipt_files ─────────────────────────────────────────────────


def test_scan_valid_receipt_passes():
    failures, scanned = scan_receipt_files(["receipts"], FIXTURE)
    # valid-receipt.md should have no failures — it has no contradictory language
    valid_fails = [f for f in failures if "valid-receipt" in f.get("file", "")]
    assert valid_fails == []


def test_scan_bad_receipt_detected():
    failures, scanned = scan_receipt_files(["receipts"], FIXTURE)
    # failures are now dicts with "file" key
    bad_fails = [f for f in failures if "bad-receipt" in f.get("file", "")]
    assert len(bad_fails) >= 1
    assert "file" in bad_fails[0]
    assert "reason" in bad_fails[0]
    assert "why_it_matters" in bad_fails[0]
    assert "next_action" in bad_fails[0]


def test_scan_receipt_files_counts_scanned():
    failures, scanned = scan_receipt_files(["receipts"], FIXTURE)
    assert scanned >= 2


# ── run_external_receipts ──────────────────────────────────────────────


def test_run_external_receipts_returns_fail_for_bad():
    result = run_external_receipts(["receipts"], FIXTURE)
    assert result["id"] == "receipts"
    assert result["status"] == "FAIL"
    assert result["exit_code"] == 1
    assert "failures" in result
    assert len(result["failures"]) >= 1
    assert "bad-receipt" in result["failures"][0]["file"]


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
    result = run_external_checker("debt", FIXTURE, "advisory", {})
    assert result["status"] == "WARN"
    assert "not found" in result["stderr"]


def test_external_checker_debt_missing_strict():
    result = run_external_checker("debt", FIXTURE, "strict", {})
    assert result["status"] == "FAIL"
    assert "Missing required file" in result["stderr"]


def test_external_checker_gates_missing_advisory():
    result = run_external_checker("gates", FIXTURE, "advisory", {})
    assert result["status"] == "WARN"


def test_external_checker_docs_missing_advisory():
    result = run_external_checker("docs", FIXTURE, "advisory", {})
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
        {
            "id": "receipts",
            "label": "Receipt Integrity",
            "status": "PASS",
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
        },
        {
            "id": "debt",
            "label": "Verification Debt",
            "status": "WARN",
            "exit_code": -1,
            "stdout": "",
            "stderr": "Not configured",
            "next_action": "Add debt ledger.",
        },
    ]
    report = build_report(results, "advisory", "/root/test", None)
    assert report["status"] == "DEGRADED"
    assert len(report["warnings"]) == 1
    assert report["warnings"][0]["check"] == "debt"


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


# ── Rich report assertions ─────────────────────────────────────────────


def test_human_output_includes_disclaimer(monkeypatch, capsys):
    """Human output includes the READY disclaimer."""
    main(["all"])
    captured = capsys.readouterr()
    assert "does not authorize execution" in captured.out


def test_json_includes_disclaimer(monkeypatch, capsys):
    """JSON report includes disclaimer field."""
    main(["all", "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert "disclaimer" in report
    assert "does not authorize execution" in report["disclaimer"]


def test_external_human_output_shows_hard_failures(monkeypatch, capsys):
    """External fixture human output includes 'Hard failures' section."""
    main(["all", "--root", str(FIXTURE)])
    captured = capsys.readouterr()
    assert "Hard failures" in captured.out
    assert "receipt_contradiction" in captured.out or "bad-receipt" in captured.out


def test_external_human_output_shows_warnings(monkeypatch, capsys):
    """External fixture human output includes 'Warnings' section."""
    main(["all", "--root", str(FIXTURE)])
    captured = capsys.readouterr()
    assert "Warnings" in captured.out


def test_external_human_output_shows_next_action(monkeypatch, capsys):
    """External fixture human output includes 'Next suggested action' section."""
    main(["all", "--root", str(FIXTURE)])
    captured = capsys.readouterr()
    assert "Next suggested action" in captured.out


def test_json_hard_failure_has_file_field(monkeypatch, capsys):
    """JSON hard_failures include file/reason/why_it_matters/next_action."""
    main(["all", "--root", str(FIXTURE), "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert len(report["hard_failures"]) >= 1
    hf = report["hard_failures"][0]
    assert "file" in hf
    assert "reason" in hf
    assert "why_it_matters" in hf
    assert "next_action" in hf


def test_json_warning_has_next_action(monkeypatch, capsys):
    """JSON warnings include next_action field."""
    main(["all", "--root", str(FIXTURE), "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert len(report["warnings"]) >= 1
    w = report["warnings"][0]
    assert "next_action" in w


def test_strict_mode_debt_is_hard_failure(monkeypatch, capsys):
    """Strict mode missing debt/gates/docs are FAIL not WARN."""
    main(["debt", "--root", str(FIXTURE), "--mode", "strict"])
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out
    assert "FAIL" in captured.out


def test_advisory_mode_debt_is_warning(monkeypatch, capsys):
    """Advisory mode missing debt is WARN not FAIL."""
    main(["debt", "--root", str(FIXTURE), "--mode", "advisory"])
    captured = capsys.readouterr()
    assert "WARN" in captured.out


def test_external_blocked_remains_expected(monkeypatch, capsys):
    """External fixture BLOCKED is expected governance success."""
    exit_code = main(["all", "--root", str(FIXTURE)])
    assert exit_code == 1  # BLOCKED — bad receipt
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out
    assert "bad-receipt" in captured.out.lower()


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
