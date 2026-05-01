"""Tests for Ordivon Coverage Governance Checker (COV-1)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "scripts" / "check_coverage_governance.py"


def _make_valid_entry(**overrides) -> dict:
    base = {
        "checker_id": "document_registry",
        "checker_path": "scripts/check_document_registry.py",
        "status": "implemented",
        "claimed_universe": "test universe",
        "discovery_method": "filesystem glob",
        "registry_or_manifest": "test.json",
        "exclusion_policy": "explicit exclusions with reason",
        "reconciliation_required": True,
        "coverage_summary_required": True,
        "unknown_object_test_required": True,
        "pass_scope_statement_required": True,
        "known_gaps": [],
        "owner": "test",
        "reviewed_at": "2026-05-01",
    }
    base.update(overrides)
    return base


def _make_manifest(checkers: list[dict]) -> dict:
    return {
        "schema_version": "0.1",
        "generated": False,
        "purpose": "test manifest",
        "coverage_policy": "coverage precedes confidence",
        "checkers": checkers,
    }


def _run(manifest: dict) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(manifest, f)
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--manifest", tmp],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(ROOT),
        )
        return result.returncode, result.stdout
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Positive ──────────────────────────────────────────────────────────


def test_valid_manifest_passes():
    manifest = _make_manifest([
        _make_valid_entry(),
        _make_valid_entry(
            checker_id="verification_debt",
            checker_path="scripts/check_verification_debt.py",
            status="partial",
            reconciliation_required=False,
            unknown_object_test_required=False,
            coverage_summary_required=True,
            known_gaps=["no auto-discovery"],
        ),
        _make_valid_entry(
            checker_id="receipt_integrity",
            checker_path="scripts/check_receipt_integrity.py",
            status="partial",
            reconciliation_required=False,
            unknown_object_test_required=False,
            known_gaps=["config-bound"],
        ),
        _make_valid_entry(
            checker_id="verification_manifest",
            checker_path="scripts/check_verification_manifest.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
        _make_valid_entry(
            checker_id="pr_fast_baseline",
            checker_path="scripts/run_verification_baseline.py",
            status="partial",
            reconciliation_required=False,
            unknown_object_test_required=False,
            known_gaps=["wave_files whitelist"],
        ),
        _make_valid_entry(
            checker_id="public_wedge_audit",
            checker_path="scripts/audit_ordivon_verify_public_wedge.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
        _make_valid_entry(
            checker_id="public_repo_dryrun",
            checker_path="scripts/dryrun_ordivon_verify_public_repo.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
        _make_valid_entry(
            checker_id="private_install_smoke",
            checker_path="scripts/smoke_ordivon_verify_private_install.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
        _make_valid_entry(
            checker_id="build_artifact_smoke",
            checker_path="scripts/smoke_ordivon_verify_build_artifacts.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
    ])
    exit_code, _ = _run(manifest)
    assert exit_code == 0


# ── Structure ─────────────────────────────────────────────────────────


def test_invalid_json_fails():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not json")
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--manifest", tmp],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(ROOT),
        )
        assert result.returncode != 0
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_missing_top_level_field_fails():
    manifest = _make_manifest([_make_valid_entry()])
    del manifest["purpose"]
    exit_code, _ = _run(manifest)
    assert exit_code != 0


def test_duplicate_checker_id_fails():
    manifest = _make_manifest([
        _make_valid_entry(checker_id="dup"),
        _make_valid_entry(checker_id="dup"),
    ])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


def test_invalid_status_fails():
    manifest = _make_manifest([_make_valid_entry(status="invalid_status")])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


# ── Implemented requirements ──────────────────────────────────────────


def test_implemented_missing_claimed_universe_fails():
    entry = _make_valid_entry(claimed_universe="")
    manifest = _make_manifest([entry])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


def test_implemented_missing_discovery_method_fails():
    entry = _make_valid_entry(discovery_method="")
    manifest = _make_manifest([entry])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


def test_implemented_missing_owner_fails():
    entry = _make_valid_entry(owner="")
    manifest = _make_manifest([entry])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


def test_implemented_missing_reviewed_at_fails():
    entry = _make_valid_entry(reviewed_at="")
    manifest = _make_manifest([entry])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


def test_implemented_missing_path_fails():
    entry = _make_valid_entry(checker_path="nonexistent/path.py")
    manifest = _make_manifest([entry])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


def test_pass_scope_statement_required_false_fails():
    entry = _make_valid_entry(pass_scope_statement_required=False)
    manifest = _make_manifest([entry])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


# ── Deferred checks ───────────────────────────────────────────────────


def test_deferred_with_path_missing_passes():
    """Deferred checker can have missing path — needs critical checkers too."""
    entry = _make_valid_entry(
        checker_id="deferred_ok",
        checker_path="nonexistent.py",
        status="deferred_with_reason",
        known_gaps=["not yet built"],
    )
    manifest = _make_manifest([
        entry,
        _make_valid_entry(),
        _make_valid_entry(
            checker_id="verification_debt",
            checker_path="scripts/check_verification_debt.py",
            status="partial",
            reconciliation_required=False,
            unknown_object_test_required=False,
            known_gaps=["none"],
        ),
        _make_valid_entry(
            checker_id="receipt_integrity",
            checker_path="scripts/check_receipt_integrity.py",
            status="partial",
            reconciliation_required=False,
            unknown_object_test_required=False,
            known_gaps=["n/a"],
        ),
        _make_valid_entry(
            checker_id="verification_manifest",
            checker_path="scripts/check_verification_manifest.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
        _make_valid_entry(
            checker_id="pr_fast_baseline",
            checker_path="scripts/run_verification_baseline.py",
            status="partial",
            reconciliation_required=False,
            unknown_object_test_required=False,
            known_gaps=["whitelist"],
        ),
        _make_valid_entry(
            checker_id="public_wedge_audit",
            checker_path="scripts/audit_ordivon_verify_public_wedge.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
        _make_valid_entry(
            checker_id="public_repo_dryrun",
            checker_path="scripts/dryrun_ordivon_verify_public_repo.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
        _make_valid_entry(
            checker_id="private_install_smoke",
            checker_path="scripts/smoke_ordivon_verify_private_install.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
        _make_valid_entry(
            checker_id="build_artifact_smoke",
            checker_path="scripts/smoke_ordivon_verify_build_artifacts.py",
            reconciliation_required=False,
            unknown_object_test_required=False,
        ),
    ])
    exit_code, _ = _run(manifest)
    assert exit_code == 0


def test_deferred_without_known_gaps_fails():
    entry = _make_valid_entry(
        checker_id="deferred_bad",
        checker_path="nonexistent.py",
        status="deferred_with_reason",
        known_gaps=[],
    )
    manifest = _make_manifest([entry])
    exit_code, _ = _run(manifest)
    assert exit_code != 0


# ── Critical checkers ────────────────────────────────────────────────


def test_critical_checker_missing_fails():
    """Manifest without document_registry must fail."""
    entry = _make_valid_entry(checker_id="other_checker")
    manifest = _make_manifest([entry])
    exit_code, out = _run(manifest)
    assert exit_code != 0
    assert "critical" in out.lower()


# ── Non-mutating ──────────────────────────────────────────────────────


def test_checker_never_mutates_files():
    mtime = Path(MANIFEST_PATH).stat().st_mtime if MANIFEST_PATH.exists() else 0
    manifest = _make_manifest([_make_valid_entry()])
    _run(manifest)
    if MANIFEST_PATH.exists():
        assert MANIFEST_PATH.stat().st_mtime == mtime


MANIFEST_PATH = ROOT / "docs" / "governance" / "checker-coverage-manifest.json"
