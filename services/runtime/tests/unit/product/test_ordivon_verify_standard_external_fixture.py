"""Tests for Ordivon Verify standard external fixture (PV-8).

Validates that a clean external repo with governance files reaches READY
in standard mode.
"""

from __future__ import annotations

import json
from pathlib import Path

from ordivon_verify import (
    load_config,
    run_external_checker,
    main,
)


STD_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ordivon_verify_standard_external_repo"
CLEAN_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ordivon_verify_clean_external_repo"
BAD_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ordivon_verify_external_repo"
DOGFOOD_ROOT = Path(__file__).resolve().parents[3] / "examples" / "ordivon-verify" / "dogfood"

STD_CONFIG = STD_FIXTURE / "ordivon.verify.json"


# ── Config ──────────────────────────────────────────────────────────────


def test_standard_fixture_config_loads():
    cfg = load_config(STD_CONFIG, STD_FIXTURE)
    assert cfg is not None
    assert cfg["mode"] == "standard"
    assert cfg["debt_ledger"] == "governance/verification-debt-ledger.jsonl"
    assert cfg["gate_manifest"] == "governance/verification-gate-manifest.json"
    assert cfg["document_registry"] == "governance/document-registry.jsonl"


# ── Governance file validation ──────────────────────────────────────────


def test_standard_debt_ledger_passes():
    result = run_external_checker(
        "debt", STD_FIXTURE, "standard", {"debt_ledger": "governance/verification-debt-ledger.jsonl"}
    )
    assert result["status"] == "PASS"


def test_standard_gate_manifest_passes():
    result = run_external_checker(
        "gates", STD_FIXTURE, "standard", {"gate_manifest": "governance/verification-gate-manifest.json"}
    )
    assert result["status"] == "PASS"


def test_standard_document_registry_passes():
    result = run_external_checker(
        "docs", STD_FIXTURE, "standard", {"document_registry": "governance/document-registry.jsonl"}
    )
    assert result["status"] == "PASS"


# ── Standard mode: missing configured file → FAIL ───────────────────────


def test_standard_missing_configured_debt_is_fail():
    result = run_external_checker("debt", STD_FIXTURE, "standard", {"debt_ledger": "governance/nonexistent.jsonl"})
    assert result["status"] == "FAIL"
    assert "not found" in result["stderr"].lower()


def test_standard_missing_configured_gates_is_fail():
    result = run_external_checker("gates", STD_FIXTURE, "standard", {"gate_manifest": "governance/nonexistent.json"})
    assert result["status"] == "FAIL"


# ── Standard external READY ─────────────────────────────────────────────


def test_standard_fixture_all_ready(monkeypatch, capsys):
    exit_code = main(["all", "--root", str(STD_FIXTURE), "--config", str(STD_CONFIG)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "READY" in captured.out


def test_standard_fixture_json_ready(monkeypatch, capsys):
    main(["all", "--root", str(STD_FIXTURE), "--config", str(STD_CONFIG), "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "READY"
    assert len(report["hard_failures"]) == 0
    assert "disclaimer" in report
    assert "does not authorize" in report["disclaimer"]


def test_standard_fixture_check_target_json_ready(monkeypatch, capsys):
    exit_code = main(["check", str(STD_FIXTURE), "--config", str(STD_CONFIG), "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["root"] == str(STD_FIXTURE.resolve())
    assert report["status"] == "READY"
    assert len(report["hard_failures"]) == 0


def _run_dogfood(case_name: str, capsys):
    case_root = DOGFOOD_ROOT / case_name
    exit_code = main(["check", str(case_root), "--config", str(case_root / "ordivon.verify.json"), "--json"])
    report = json.loads(capsys.readouterr().out)
    return exit_code, report


def test_dogfood_clean_ai_task_ready(monkeypatch, capsys):
    exit_code, report = _run_dogfood("clean-ai-task", capsys)
    assert exit_code == 0
    assert report["trust_signal"] == "READY_WITHOUT_AUTHORIZATION"
    assert report["surfaces"]["tests"]["status"] == "PASS"
    assert report["missing_evidence"] == []


def test_dogfood_false_comfort_ai_task_blocked(monkeypatch, capsys):
    exit_code, report = _run_dogfood("false-comfort-ai-task", capsys)
    assert exit_code == 1
    assert report["status"] == "BLOCKED"
    assert any(f["id"] == "missing_test_evidence" for f in report["hard_failures"])


def test_dogfood_realistic_degraded_task_reports_missing_evidence(monkeypatch, capsys):
    exit_code, report = _run_dogfood("realistic-degraded-task", capsys)
    assert exit_code == 2
    assert report["status"] == "DEGRADED"
    assert {item["check"] for item in report["missing_evidence"]} == {"debt", "gates", "docs"}


def test_dogfood_markdown_is_pr_pasteable(monkeypatch, capsys):
    case_root = DOGFOOD_ROOT / "false-comfort-ai-task"
    exit_code = main(["check", str(case_root), "--config", str(case_root / "ordivon.verify.json"), "--markdown"])
    assert exit_code == 1
    markdown = capsys.readouterr().out
    assert "## Ordivon Verify Trust Report" in markdown
    assert "### Hard Failures" in markdown
    assert "missing_test_evidence" in markdown
    assert "### Recommended Next Action" in markdown
    assert "does not authorize" in markdown


# ── Cross-fixture: bad remains BLOCKED ──────────────────────────────────


def test_bad_fixture_still_blocked(monkeypatch, capsys):
    exit_code = main(["all", "--root", str(BAD_FIXTURE), "--config", str(BAD_FIXTURE / "ordivon.verify.json")])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out


# ── Cross-fixture: clean advisory remains DEGRADED ──────────────────────


def test_clean_fixture_still_degraded(monkeypatch, capsys):
    exit_code = main(["all", "--root", str(CLEAN_FIXTURE), "--config", str(CLEAN_FIXTURE / "ordivon.verify.json")])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "DEGRADED" in captured.out


# ── Native remains READY ────────────────────────────────────────────────


def test_native_still_ready(monkeypatch, capsys):
    exit_code = main(["all"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "READY" in captured.out


# ── No file writes ──────────────────────────────────────────────────────


def test_no_file_writes_in_standard_fixture(monkeypatch):
    orig_mtimes = {}
    for p in STD_FIXTURE.rglob("*"):
        if p.is_file():
            orig_mtimes[p] = p.stat().st_mtime

    main(["all", "--root", str(STD_FIXTURE), "--config", str(STD_CONFIG)])

    for p, mtime in orig_mtimes.items():
        assert p.stat().st_mtime == mtime, f"File modified: {p}"
