"""Phase DG-6B: Receipt Integrity Checker tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[3] / "scripts" / "check_receipt_integrity.py"


def _run_checker_on_file(content: str) -> tuple[int, str]:
    """Write content to temp file and run checker against it."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Positive: valid receipt passes ────────────────────────────────────


def test_valid_receipt_passes():
    content = "# Test Receipt\n\nAll verification gates passed.\nTracked working tree clean.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code == 0


# ── Negative: Skipped None + not run ──────────────────────────────────


def test_skipped_none_with_not_run_fails():
    content = "# Receipt\n\nSkipped Verification: None\n\nRuff not run.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code != 0


# ── Negative: SEALED + pending ────────────────────────────────────────


def test_sealed_with_pending_fails():
    content = "# Receipt\n\nStatus: SEALED\n\nPending verification.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code != 0


# ── Negative: clean working tree + untracked ──────────────────────────


def test_clean_working_tree_with_untracked_fails():
    content = "# Receipt\n\nclean working tree.\nUntracked residue present.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code != 0


# ── Positive: tracked working tree clean + untracked ──────────────────


def test_tracked_working_tree_clean_passes():
    content = "# Receipt\n\nTracked working tree clean.\nUntracked residue remains.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code == 0


# ── Negative: stale 7/7 baseline ─────────────────────────────────────


def test_stale_baseline_7_7_fails():
    content = "# Receipt\n\n7/7 baseline passed.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code != 0


# ── Positive: 7/7 → 8/8 historical transition ────────────────────────


def test_historical_7_7_to_8_8_passes():
    content = "# Phase DG-5 Receipt\n\nBefore DG-5: 7/7. After DG-5: 8/8 baseline.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code == 0


# ── Negative: Ruff clean with pre-existing debt ───────────────────────


def test_ruff_clean_with_preexisting_fails():
    content = "# Receipt\n\nRuff clean. Pre-existing debt remains.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code != 0


# ── Positive: DG scope clean with pre-existing debt ───────────────────


def test_dg_scope_clean_passes():
    content = "# Receipt\n\nDG-5 files clean. Pre-existing debt in scripts/ remains.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code == 0


# ── Negative: CandidateRule validated ─────────────────────────────────


def test_candidate_rule_validated_fails():
    content = "# Receipt\n\nCandidateRule validated successfully.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code != 0


# ── Positive: CandidateRule advisory ──────────────────────────────────


def test_candidate_rule_advisory_passes():
    content = "# Receipt\n\nCandidateRule supported by evidence, advisory only, NOT Policy.\n"
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code == 0


# ── Positive: safe NO-GO phrases ──────────────────────────────────────


def test_safe_nogo_phrases_pass():
    content = (
        "# Receipt\n\nPhase 8 remains DEFERRED.\nLive trading is NO-GO.\n"
        "CandidateRules are NOT Policy.\nLedger is evidence, not execution authority.\n"
    )
    exit_code, _ = _run_checker_on_file(content)
    assert exit_code == 0


# ── Summary counts ────────────────────────────────────────────────────


def test_summary_includes_counts():
    content = "# Test\n\nTracked working tree clean.\n"
    exit_code, out = _run_checker_on_file(content)
    assert exit_code == 0
    assert "Files scanned:" in out
    assert "Hard failures:" in out


# ── Historical skip ───────────────────────────────────────────────────


def test_historical_files_excluded():
    """Files under archive/ should be skipped."""
    import tempfile

    archive_dir = Path(tempfile.mkdtemp())
    archive_file = archive_dir / "archive" / "old-receipt.md"
    archive_file.parent.mkdir(parents=True, exist_ok=True)
    archive_file.write_text("Skipped Verification: None\nnot run\n")
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), str(archive_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
    finally:
        import shutil

        shutil.rmtree(archive_dir)
