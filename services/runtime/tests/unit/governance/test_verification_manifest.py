"""Phase DG-6C: Verification Gate Manifest tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[3] / "scripts" / "check_verification_manifest.py"

VALID_MANIFEST = {
    "manifest_id": "test-v1",
    "profile": "pr-fast",
    "version": "1.0",
    "status": "current",
    "authority": "source_of_truth",
    "last_verified": "2026-04-30",
    "gate_count": 5,
    "gates": [
        {
            "gate_id": "ruff_check",
            "display_name": "ruff check (Wave files)",
            "layer": "L0",
            "hardness": "hard",
            "command": "python -m ruff check",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Static analysis",
            "protects_against": "code quality regression",
        },
        {
            "gate_id": "architecture_boundaries",
            "display_name": "Architecture boundaries",
            "layer": "L4",
            "hardness": "hard",
            "command": "python scripts/check_architecture.py",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Architecture check",
            "protects_against": "import violations",
        },
        {
            "gate_id": "document_registry_governance",
            "display_name": "Document registry governance",
            "layer": "L6",
            "hardness": "hard",
            "command": "python scripts/check_document_registry.py",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Document registry",
            "protects_against": "stale docs",
        },
        {
            "gate_id": "verification_debt_ledger",
            "display_name": "Verification debt ledger",
            "layer": "L7A",
            "hardness": "hard",
            "command": "python scripts/check_verification_debt.py",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Debt tracking",
            "protects_against": "hidden debt",
        },
        {
            "gate_id": "receipt_integrity",
            "display_name": "Receipt integrity",
            "layer": "L7B",
            "hardness": "hard",
            "command": "python scripts/check_receipt_integrity.py",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Receipt honesty",
            "protects_against": "contradictory receipts",
        },
    ],
}


MOCK_BASELINE = """def run_pr_fast_gates():
    summary = BaselineSummary()
    python = "python3"
    summary.results.append(
        _run_gate(
            "ruff check (Wave files)",
            "hard",
            "L0",
            [python, "-m", "ruff", "check"],
        )
    )
    summary.results.append(
        _run_gate(
            "Architecture boundaries",
            "hard",
            "L4",
            [python, "scripts/check_architecture.py"],
        )
    )
    summary.results.append(
        _run_gate(
            "Document registry governance",
            "hard",
            "L6",
            [python, "scripts/check_document_registry.py"],
        )
    )
    summary.results.append(
        _run_gate(
            "Verification debt ledger",
            "hard",
            "L7A",
            [python, "scripts/check_verification_debt.py"],
        )
    )
    summary.results.append(
        _run_gate(
            "Receipt integrity",
            "hard",
            "L7B",
            [python, "scripts/check_receipt_integrity.py"],
        )
    )
    return summary
"""


def _run_checker(manifest: dict) -> tuple[int, str]:
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as mf:
        json.dump(manifest, mf)
        tmp_manifest = mf.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as bf:
        bf.write(MOCK_BASELINE)
        tmp_baseline = bf.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp_manifest, "--baseline-path", tmp_baseline],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout
    finally:
        Path(tmp_manifest).unlink(missing_ok=True)
        Path(tmp_baseline).unlink(missing_ok=True)


# ── Positive ──────────────────────────────────────────────────────────


def test_valid_manifest_passes():
    exit_code, _ = _run_checker(VALID_MANIFEST)
    assert exit_code == 0


# ── Negative: invalid JSON ────────────────────────────────────────────


def test_invalid_json_fails():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not json\n")
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), tmp],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Negative: missing manifest field ──────────────────────────────────


def test_missing_manifest_field_fails():
    m = dict(VALID_MANIFEST)
    del m["status"]
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: duplicate gate_id ───────────────────────────────────────


def test_duplicate_gate_id_fails():
    m = dict(VALID_MANIFEST)
    m["gates"] = [dict(VALID_MANIFEST["gates"][0]), dict(VALID_MANIFEST["gates"][0])]
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: gate_count mismatch ─────────────────────────────────────


def test_gate_count_mismatch_fails():
    m = dict(VALID_MANIFEST)
    m["gate_count"] = 99
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: non-hard gate ───────────────────────────────────────────


def test_non_hard_gate_fails():
    m = dict(VALID_MANIFEST)
    m["gates"][0]["hardness"] = "soft"
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: no-op command ───────────────────────────────────────────


def test_noop_command_fails():
    m = dict(VALID_MANIFEST)
    m["gates"][0]["command"] = "echo done"
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: empty command ───────────────────────────────────────────


def test_empty_command_fails():
    m = dict(VALID_MANIFEST)
    m["gates"][0]["command"] = ""
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Summary counts ────────────────────────────────────────────────────


def test_summary_counts_correct():
    exit_code, out = _run_checker(VALID_MANIFEST)
    assert exit_code == 0
    assert "Expected gate count:       5" in out


# ── Checker never mutates ─────────────────────────────────────────────


def test_checker_never_mutates():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as mf:
        json.dump(VALID_MANIFEST, mf)
        tmp_manifest = mf.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as bf:
        bf.write(MOCK_BASELINE)
        tmp_baseline = bf.name
    try:
        subprocess.run(
            [sys.executable, str(CHECKER), tmp_manifest, "--baseline-path", tmp_baseline],
            capture_output=True,
            text=True,
            timeout=30,
        )
        with open(tmp_manifest) as f:
            reloaded = json.load(f)
        assert reloaded["gate_count"] == 5
    finally:
        Path(tmp_manifest).unlink(missing_ok=True)
        Path(tmp_baseline).unlink(missing_ok=True)
