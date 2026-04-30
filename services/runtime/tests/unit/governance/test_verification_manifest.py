"""Phase DG-6C: Verification Gate Manifest tests.

Post-DG-H1: Rewrote _run_checker to use direct function calls
(extract_baseline_gates + check_invariants) instead of subprocess,
eliminating the xfail/xpass instability tracked as VD-2026-04-30-004.

Root cause of VD-004: test_non_hard_gate_fails, test_noop_command_fails,
and test_empty_command_fails used shallow dict() copy of VALID_MANIFEST,
mutating the shared gate dicts in place.  Subsequent tests that expected
a pristine manifest saw corrupted data.  Fixed by using copy.deepcopy().
"""

from __future__ import annotations

import copy
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parents[3] / "scripts" / "check_verification_manifest.py"

# Import checker functions directly — avoids subprocess for deterministic tests.
# The checker module uses sys.exit in load_manifest and main(), but those are
# never called from _run_checker.
sys.path.insert(0, str(CHECKER.parent))
from check_verification_manifest import (  # noqa: E402
    check_invariants,
    extract_baseline_gates,
    print_summary,
)

VALID_MANIFEST = {
    "manifest_id": "test-v1",
    "profile": "pr-fast",
    "version": "1.0",
    "status": "current",
    "authority": "source_of_truth",
    "last_verified": "2026-04-30",
    "gate_count": 11,
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
            "gate_id": "ruff_format_check",
            "display_name": "ruff format check (Wave files)",
            "layer": "L0",
            "hardness": "hard",
            "command": "python -m ruff format --check",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Format consistency",
            "protects_against": "formatting drift",
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
            "gate_id": "runtime_evidence",
            "display_name": "Runtime evidence integrity",
            "layer": "L5",
            "hardness": "hard",
            "command": "python scripts/check_runtime_evidence.py",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Runtime evidence",
            "protects_against": "evidence corruption",
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
            "gate_id": "eval_corpus",
            "display_name": "Eval corpus (24 cases)",
            "layer": "L7",
            "hardness": "hard",
            "command": "python evals/run_evals.py",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Eval regression",
            "protects_against": "eval breakage",
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
        {
            "gate_id": "verification_manifest",
            "display_name": "Verification gate manifest",
            "layer": "L8",
            "hardness": "hard",
            "command": "python scripts/check_verification_manifest.py",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Manifest integrity",
            "protects_against": "gate removal",
        },
        {
            "gate_id": "repo_cli_smoke_valid",
            "display_name": "Repo CLI smoke (valid→execute)",
            "layer": "L10",
            "hardness": "hard",
            "command": "python scripts/run_repo_cli_smoke.py valid",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Repo integrity",
            "protects_against": "repo breakage",
        },
        {
            "gate_id": "repo_cli_smoke_forbidden",
            "display_name": "Repo CLI smoke (forbidden→reject)",
            "layer": "L10",
            "hardness": "hard",
            "command": "python scripts/run_repo_cli_smoke.py forbidden",
            "expected_result_type": "exit_code_0",
            "may_be_removed_only_by": "Stage Summit",
            "purpose": "Repo integrity",
            "protects_against": "repo breakage",
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
            "ruff format check (Wave files)",
            "hard",
            "L0",
            [python, "-m", "ruff", "format", "--check"],
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
            "Runtime evidence integrity",
            "hard",
            "L5",
            [python, "scripts/check_runtime_evidence.py"],
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
            "Eval corpus (24 cases)",
            "hard",
            "L7",
            [python, "evals/run_evals.py"],
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
    summary.results.append(
        _run_gate(
            "Verification gate manifest",
            "hard",
            "L8",
            [python, "scripts/check_verification_manifest.py"],
        )
    )
    summary.results.append(
        _run_gate(
            "Repo CLI smoke (valid→execute)",
            "hard",
            "L10",
            [python, "scripts/run_repo_cli_smoke.py", "valid"],
        )
    )
    summary.results.append(
        _run_gate(
            "Repo CLI smoke (forbidden→reject)",
            "hard",
            "L10",
            [python, "scripts/run_repo_cli_smoke.py", "forbidden"],
        )
    )
    return summary
"""


def _run_checker(manifest: dict) -> tuple[int, str]:
    """Run manifest checks deterministically using direct function calls.

    Writes MOCK_BASELINE to a temp file, then calls extract_baseline_gates
    and check_invariants directly — no subprocess.  Eliminates the
    subprocess state pollution that caused VD-2026-04-30-004.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as bf:
        bf.write(MOCK_BASELINE)
        tmp_baseline = bf.name
    try:
        gates = extract_baseline_gates(Path(tmp_baseline))
        errors = check_invariants(manifest, gates)

        out = io.StringIO()
        old = sys.stdout
        sys.stdout = out
        try:
            print_summary(manifest, gates, errors)
            if errors:
                print(f"\n❌ {len(errors)} INVARIANT VIOLATION(S):\n")
                for err in errors:
                    print(f"  - {err}")
                print()
            else:
                print("\n✅ All verification gate manifest invariants pass.\n")
        finally:
            sys.stdout = old

        return (0 if not errors else 1, out.getvalue())
    finally:
        Path(tmp_baseline).unlink(missing_ok=True)


# ── Positive ──────────────────────────────────────────────────────────


def test_valid_manifest_passes():
    exit_code, _ = _run_checker(VALID_MANIFEST)
    assert exit_code == 0


# ── Negative: invalid JSON ────────────────────────────────────────────


def test_invalid_json_fails():
    """Tests main() handling of invalid JSON — requires subprocess."""
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
    m = copy.deepcopy(VALID_MANIFEST)
    del m["status"]
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: duplicate gate_id ───────────────────────────────────────


def test_duplicate_gate_id_fails():
    m = copy.deepcopy(VALID_MANIFEST)
    m["gates"] = [dict(VALID_MANIFEST["gates"][0]), dict(VALID_MANIFEST["gates"][0])]
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: gate_count mismatch ─────────────────────────────────────


def test_gate_count_mismatch_fails():
    m = copy.deepcopy(VALID_MANIFEST)
    m["gate_count"] = 99
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: non-hard gate ───────────────────────────────────────────


def test_non_hard_gate_fails():
    m = copy.deepcopy(VALID_MANIFEST)
    m["gates"][0]["hardness"] = "soft"
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: no-op command ───────────────────────────────────────────


def test_noop_command_fails():
    m = copy.deepcopy(VALID_MANIFEST)
    m["gates"][0]["command"] = "echo done"
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Negative: empty command ───────────────────────────────────────────


def test_empty_command_fails():
    m = copy.deepcopy(VALID_MANIFEST)
    m["gates"][0]["command"] = ""
    exit_code, _ = _run_checker(m)
    assert exit_code != 0


# ── Summary counts ────────────────────────────────────────────────────


def test_summary_counts_correct():
    exit_code, out = _run_checker(VALID_MANIFEST)
    assert exit_code == 0
    assert "Expected gate count:       11" in out


# ── Checker never mutates ─────────────────────────────────────────────


def test_checker_never_mutates():
    """Tests that main() never writes to the manifest — requires subprocess."""
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
            cwd=str(Path(__file__).resolve().parents[3]),
        )
        with open(tmp_manifest) as f:
            reloaded = json.load(f)
        assert reloaded["gate_count"] == 11
    finally:
        Path(tmp_manifest).unlink(missing_ok=True)
        Path(tmp_baseline).unlink(missing_ok=True)
