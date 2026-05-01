"""Tests for Ordivon Verify quickstart example fixture (PV-N3)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

QUICKSTART = Path(__file__).resolve().parents[3] / "examples" / "ordivon-verify" / "quickstart"
CONFIG = QUICKSTART / "ordivon.verify.json"


def _run_verify(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[3] / "scripts" / "ordivon_verify.py")] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(Path(__file__).resolve().parents[3]),
    )


# ── Existence and structure ───────────────────────────────────────────


def test_quickstart_config_exists():
    assert CONFIG.is_file(), "Quickstart config missing"


def test_quickstart_receipt_exists():
    assert (QUICKSTART / "receipts" / "clean-receipt.md").is_file()


def test_quickstart_debt_ledger_exists():
    assert (QUICKSTART / "governance" / "verification-debt-ledger.jsonl").exists()


def test_quickstart_gate_manifest_exists():
    assert (QUICKSTART / "governance" / "verification-gate-manifest.json").is_file()


def test_quickstart_document_registry_exists():
    assert (QUICKSTART / "governance" / "document-registry.jsonl").is_file()


# ── Verify output ─────────────────────────────────────────────────────


def test_quickstart_returns_ready():
    result = _run_verify(["all", "--root", str(QUICKSTART), "--config", str(CONFIG)])
    assert result.returncode == 0, f"Expected exit 0: {result.stdout}"
    assert "READY" in result.stdout


def test_quickstart_json_returns_ready():
    result = _run_verify(["all", "--root", str(QUICKSTART), "--config", str(CONFIG), "--json"])
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["status"] == "READY"
    assert report.get("hard_failures") == []
    assert "does not authorize execution" in report.get("disclaimer", "")


def test_quickstart_json_has_no_hard_failures():
    result = _run_verify(["all", "--root", str(QUICKSTART), "--config", str(CONFIG), "--json"])
    report = json.loads(result.stdout)
    assert report.get("hard_failures") == []


def test_quickstart_json_has_disclaimer():
    result = _run_verify(["all", "--root", str(QUICKSTART), "--config", str(CONFIG), "--json"])
    report = json.loads(result.stdout)
    assert "does not authorize execution" in report.get("disclaimer", "")


# ── Read-only: verify does not mutate files ───────────────────────────


def test_quickstart_files_not_modified_by_verify():
    """Running Verify must not modify the quickstart fixture files."""
    mtimes = {}
    for p in QUICKSTART.rglob("*"):
        if p.is_file():
            mtimes[str(p)] = p.stat().st_mtime

    _run_verify(["all", "--root", str(QUICKSTART), "--config", str(CONFIG)])

    for p_str, orig in mtimes.items():
        assert Path(p_str).stat().st_mtime == orig, f"File modified: {p_str}"


# ── Content safety ────────────────────────────────────────────────────


def test_quickstart_readme_no_public_release_claim():
    readme = (QUICKSTART / "README.md").read_text()
    assert "public release" not in readme.lower() or "not a public release" in readme.lower()
    assert "production-ready" not in readme.lower()


def test_quickstart_readme_no_authorization_claim():
    readme = (QUICKSTART / "README.md").read_text()
    assert "authorizes execution" not in readme.lower()
    assert "evidence, not authorization" in readme.lower()


def test_quickstart_no_unsafe_pfios_identity():
    """Quickstart must not claim PFIOS/AegisOS as current identity."""
    for p in QUICKSTART.rglob("*"):
        if p.suffix in (".md", ".json", ".jsonl"):
            content = p.read_text()
            # Allow only in historical/boundary context
            if "AegisOS" in content:
                assert "historical" in content.lower() or "legacy" in content.lower(), (
                    f"{p.name}: 'AegisOS' present without historical/legacy classification"
                )


def test_quickstart_readme_mentions_coverage():
    readme = (QUICKSTART / "README.md").read_text()
    assert "PASS is scoped" in readme or "coverage" in readme.lower()
