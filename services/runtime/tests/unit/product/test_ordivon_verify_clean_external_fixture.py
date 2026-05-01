"""Tests for Ordivon Verify clean external fixture (PV-7).

Validates that a clean external repo with honest receipts and no
governance files returns DEGRADED (warnings, no hard failures).
"""

from __future__ import annotations

import json
from pathlib import Path

from ordivon_verify import (
    load_config,
    scan_receipt_files,
    run_external_receipts,
    run_external_checker,
    determine_status,
    main,
)


CLEAN_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ordivon_verify_clean_external_repo"
BAD_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ordivon_verify_external_repo"


# ── Config ──────────────────────────────────────────────────────────────


def test_clean_fixture_config_loads():
    cfg = load_config(CLEAN_FIXTURE / "ordivon.verify.json", CLEAN_FIXTURE)
    assert cfg is not None
    assert cfg["project_name"] == "clean-external-fixture"
    assert cfg["mode"] == "advisory"
    assert "receipts" in cfg["receipt_paths"]


# ── Receipt scan ────────────────────────────────────────────────────────


def test_clean_receipt_zero_failures():
    failures, scanned = scan_receipt_files(["receipts"], CLEAN_FIXTURE)
    clean_fails = [f for f in failures if "clean-receipt" in f.get("file", "")]
    assert clean_fails == []
    assert scanned >= 1


def test_clean_external_receipts_passes():
    result = run_external_receipts(["receipts"], CLEAN_FIXTURE)
    assert result["status"] == "PASS"
    assert result["exit_code"] == 0
    assert "0 contradictions" in result["stdout"]


# ── Advisory mode warnings (not failures) ───────────────────────────────


def test_clean_debt_advisory_warning():
    result = run_external_checker("debt", CLEAN_FIXTURE, "advisory", {})
    assert result["status"] == "WARN"


def test_clean_gates_advisory_warning():
    result = run_external_checker("gates", CLEAN_FIXTURE, "advisory", {})
    assert result["status"] == "WARN"


def test_clean_docs_advisory_warning():
    result = run_external_checker("docs", CLEAN_FIXTURE, "advisory", {})
    assert result["status"] == "WARN"


# ── Status: DEGRADED (warnings, no hard failures) ───────────────────────


def test_clean_fixture_is_degraded_not_blocked(monkeypatch, capsys):
    """Clean fixture: receipt PASS, debt/gates/docs WARN → DEGRADED."""
    exit_code = main(["all", "--root", str(CLEAN_FIXTURE), "--config", str(CLEAN_FIXTURE / "ordivon.verify.json")])
    assert exit_code == 2  # DEGRADED
    captured = capsys.readouterr()
    assert "DEGRADED" in captured.out
    assert "FAIL" not in captured.out


def test_clean_fixture_json_no_hard_failures(monkeypatch, capsys):
    """JSON output for clean fixture has zero hard_failures."""
    main(["all", "--root", str(CLEAN_FIXTURE), "--config", str(CLEAN_FIXTURE / "ordivon.verify.json"), "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "DEGRADED"
    assert len(report["hard_failures"]) == 0
    assert len(report["warnings"]) == 3
    assert "disclaimer" in report
    assert "does not authorize" in report["disclaimer"]


def test_clean_fixture_determine_status():
    """Unit test: PASS + WARN → DEGRADED."""
    results = [
        {"id": "receipts", "status": "PASS", "exit_code": 0},
        {"id": "debt", "status": "WARN", "exit_code": -1},
        {"id": "gates", "status": "WARN", "exit_code": -1},
        {"id": "docs", "status": "WARN", "exit_code": -1},
    ]
    assert determine_status(results) == "DEGRADED"


def test_clean_fixture_human_includes_disclaimer(monkeypatch, capsys):
    main(["all", "--root", str(CLEAN_FIXTURE), "--config", str(CLEAN_FIXTURE / "ordivon.verify.json")])
    captured = capsys.readouterr()
    assert "does not authorize execution" in captured.out


def test_clean_fixture_human_includes_warnings(monkeypatch, capsys):
    main(["all", "--root", str(CLEAN_FIXTURE), "--config", str(CLEAN_FIXTURE / "ordivon.verify.json")])
    captured = capsys.readouterr()
    assert "Warnings" in captured.out


# ── Cross-fixture: bad remains BLOCKED ──────────────────────────────────


def test_bad_fixture_still_blocked(monkeypatch, capsys):
    """Existing bad fixture must still produce BLOCKED."""
    exit_code = main(["all", "--root", str(BAD_FIXTURE), "--config", str(BAD_FIXTURE / "ordivon.verify.json")])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out


# ── Native remains READY ────────────────────────────────────────────────


def test_native_still_ready(monkeypatch, capsys):
    exit_code = main(["all"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "READY" in captured.out


# ── No file writes ──────────────────────────────────────────────────────


def test_no_file_writes_in_clean_fixture(monkeypatch):
    orig_mtimes = {}
    for p in CLEAN_FIXTURE.rglob("*"):
        if p.is_file():
            orig_mtimes[p] = p.stat().st_mtime

    main(["all", "--root", str(CLEAN_FIXTURE), "--config", str(CLEAN_FIXTURE / "ordivon.verify.json")])

    for p, mtime in orig_mtimes.items():
        assert p.stat().st_mtime == mtime, f"File modified: {p}"
