#!/usr/bin/env python3
"""Ordivon Verification Baseline Runner — orchestrates all verification gates.

Runs architecture checks, runtime evidence checks, DB-backed audit, eval corpus,
repo CLI smoke test, unit/integration/contract tests, and reports a unified
pass/fail summary with gate classification.

Hard gates failing = runner exits 1.
Escalation/Advisory gates failing = recorded but do not block.

Does NOT write to DB, modify files, create ExecutionRequest/Receipt,
or invoke shell/MCP/IDE beyond subprocess for local scripts.

Usage:
    uv run python scripts/run_verification_baseline.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


@dataclass
class GateResult:
    name: str
    gate_class: str
    layer: str
    passed: bool
    output: str  # combined stdout+stderr (for display)
    stdout: str  # stdout only (for JSON parsing)
    exit_code: int


@dataclass
class BaselineSummary:
    results: list[GateResult] = field(default_factory=list)

    @property
    def hard_passed(self) -> int:
        return sum(1 for r in self.results if r.gate_class == "hard" and r.passed)

    @property
    def hard_total(self) -> int:
        return sum(1 for r in self.results if r.gate_class == "hard")

    @property
    def hard_failed(self) -> int:
        return self.hard_total - self.hard_passed

    @property
    def overall_ready(self) -> bool:
        return self.hard_failed == 0


def _run_gate(name: str, gate_class: str, layer: str, cmd: list[str], **kwargs) -> GateResult:
    """Execute a verification gate as a subprocess."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=kwargs.pop("timeout", 120),
            cwd=str(ROOT),
            **kwargs,
        )
        # Only stdout carries structured output; stderr is diagnostics
        output = (result.stdout + result.stderr).strip()
        stdout = result.stdout.strip()
        exit_code = result.returncode

        # For "hard" gates, pass means exit 0
        if gate_class == "hard":
            passed = exit_code == 0
        else:
            passed = True

        return GateResult(
            name=name,
            gate_class=gate_class,
            layer=layer,
            passed=passed,
            output=output[:500],
            stdout=stdout[:500],
            exit_code=exit_code,
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            name=name,
            gate_class=gate_class,
            layer=layer,
            passed=False,
            output="TIMEOUT",
            stdout="",
            exit_code=-1,
        )
    except Exception as exc:
        return GateResult(
            name=name,
            gate_class=gate_class,
            layer=layer,
            passed=False,
            output=str(exc),
            stdout="",
            exit_code=-1,
        )


def run_all_gates() -> BaselineSummary:
    """Run all verification gates and return a summary."""
    summary = BaselineSummary()
    python = sys.executable

    # ── Layer 0: Static Analysis ─────────────────────────────
    # Only check this Wave's files, not pre-existing debt across the whole project
    wave_files = [
        str(SCRIPTS / "run_verification_baseline.py"),
        str(SCRIPTS / "check_document_registry.py"),
        str(SCRIPTS / "check_verification_debt.py"),
        str(SCRIPTS / "check_receipt_integrity.py"),
        str(SCRIPTS / "check_verification_manifest.py"),
        str(SCRIPTS / "check_coverage_governance.py"),
        str(SCRIPTS / "audit_runtime_evidence_db.py"),
        str(ROOT / "tests" / "unit" / "test_verification_baseline.py"),
        str(ROOT / "tests" / "unit" / "test_repo_governance_cli.py"),
        str(ROOT / "tests" / "unit" / "governance" / "test_coverage_governance.py"),
        str(ROOT / "tests" / "unit" / "governance" / "test_partial_checker_discovery.py"),
        str(SCRIPTS / "repo_governance_cli.py"),
    ]
    summary.results.append(
        _run_gate(
            "ruff check (Wave files)",
            "hard",
            "L0",
            [python, "-m", "ruff", "check", *wave_files],
        )
    )
    summary.results.append(
        _run_gate(
            "ruff format check (Wave files)",
            "hard",
            "L0",
            [python, "-m", "ruff", "format", "--check", "--preview", *wave_files],
        )
    )

    # ── Layer 4: Architecture Boundaries ────────────────────
    summary.results.append(
        _run_gate(
            "Architecture boundaries",
            "hard",
            "L4",
            [python, str(SCRIPTS / "check_architecture.py")],
        )
    )

    # ── Layer 4A: Coverage Governance ──────────────────────
    summary.results.append(
        _run_gate(
            "Coverage governance",
            "hard",
            "L4",
            [python, str(SCRIPTS / "check_coverage_governance.py")],
        )
    )

    # ── Layer 5: Runtime Evidence (Static) ──────────────────
    summary.results.append(
        _run_gate(
            "Runtime evidence integrity",
            "hard",
            "L5",
            [python, str(SCRIPTS / "check_runtime_evidence.py")],
        )
    )

    # ── Layer 6: DB-Backed Audit ────────────────────────────
    summary.results.append(
        _run_gate(
            "DB-backed audit",
            "escalation",
            "L6",
            [python, str(SCRIPTS / "audit_runtime_evidence_db.py")],
        )
    )

    # ── Layer 7: Eval Corpus ────────────────────────────────
    summary.results.append(
        _run_gate(
            "Eval corpus (24 cases)",
            "hard",
            "L7",
            [python, str(ROOT / "evals" / "run_evals.py")],
        )
    )

    # ── Layer 10: Repo CLI Smoke ────────────────────────────
    # Valid case → execute
    result = _run_gate(
        "Repo CLI smoke (valid→execute)",
        "hard",
        "L10",
        [
            python,
            str(SCRIPTS / "repo_governance_cli.py"),
            "--task-description",
            "Fix unit test naming",
            "--file-path",
            "tests/unit/test_example.py",
            "--estimated-impact",
            "low",
            "--reasoning",
            "Small test-only cleanup",
            "--test-plan",
            "uv run pytest tests/unit/test_example.py",
            "--json",
        ],
    )
    # Also verify the JSON output contains expected fields
    try:
        parsed = json.loads(result.stdout)
        if parsed.get("decision") != "execute":
            result.passed = False
            result.output += " [unexpected decision: " + parsed.get("decision", "?") + "]"
        if parsed.get("side_effects", {}).get("file_writes") is not False:
            result.passed = False
            result.output += " [side_effects violation]"
    except json.JSONDecodeError:
        result.passed = False
        result.output = "JSON parse failed: " + result.stdout[:200]
    summary.results.append(result)

    # Forbidden case → reject
    fb_result = _run_gate(
        "Repo CLI smoke (forbidden→reject)",
        "hard",
        "L10",
        [
            python,
            str(SCRIPTS / "repo_governance_cli.py"),
            "--task-description",
            "Add env var",
            "--file-path",
            ".env",
            "--estimated-impact",
            "medium",
            "--reasoning",
            "Need new env var",
            "--test-plan",
            "Check startup",
            "--json",
        ],
    )
    # Forbidden case: exit_code 3 = reject (expected), exit_code 0 = execute (unexpected)
    try:
        parsed = json.loads(fb_result.stdout)
        if parsed.get("decision") != "reject":
            fb_result.passed = False
            fb_result.output += " [expected reject, got " + parsed.get("decision", "?") + "]"
        else:
            fb_result.passed = True  # reject is the correct outcome
    except json.JSONDecodeError:
        fb_result.passed = False
        fb_result.output = "JSON parse failed: " + fb_result.stdout[:200]
    summary.results.append(fb_result)

    # ── Layer 1-3: Test Suites ──────────────────────────────
    summary.results.append(
        _run_gate(
            "Unit tests",
            "hard",
            "L1",
            [python, "-m", "pytest", "tests/unit", "-q", "--no-header", "-p", "no:cacheprovider"],
            timeout=180,
        )
    )
    summary.results.append(
        _run_gate(
            "Integration tests",
            "hard",
            "L2",
            [python, "-m", "pytest", "tests/integration", "-q", "--no-header"],
            timeout=120,
        )
    )
    summary.results.append(
        _run_gate(
            "Contract tests",
            "hard",
            "L3",
            [python, "-m", "pytest", "tests/contracts", "-q"],
            timeout=60,
        )
    )

    return summary


def print_summary(summary: BaselineSummary) -> None:
    """Print human-readable summary."""
    print("\n" + "=" * 60)
    print("ORDIVON VERIFICATION BASELINE")
    print("=" * 60)
    print()

    # Results table
    for r in summary.results:
        symbol = "✅" if r.passed else "❌"
        tag = f"[{r.gate_class.upper()}]"
        print(f"  {symbol} {tag:15s} {r.name:45s} (L{r.layer})")
        if not r.passed or r.exit_code != 0:
            preview = r.output[:200].replace("\n", " | ")
            print(f"     {'':15s} → {preview}")

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Hard gates:       {summary.hard_passed}/{summary.hard_total} PASS")
    esc_total = sum(1 for r in summary.results if r.gate_class == "escalation")
    esc_pass = sum(1 for r in summary.results if r.gate_class == "escalation" and r.exit_code == 0)
    print(f"  Escalation gates: {esc_pass}/{esc_total} clean")
    adv_total = sum(1 for r in summary.results if r.gate_class == "advisory")
    adv_run = sum(1 for r in summary.results if r.gate_class == "advisory" and r.exit_code >= 0)
    print(f"  Advisory gates:   {adv_run}/{adv_total} run")
    print()
    if summary.overall_ready:
        print("  OVERALL: READY (all hard gates pass)")
    else:
        print(f"  OVERALL: BLOCKED ({summary.hard_failed} hard gate(s) failed)")
    print()


def print_json_summary(summary: BaselineSummary) -> None:
    """Print machine-readable JSON summary."""
    data = {
        "verification_baseline_version": "v1",
        "overall_ready": summary.overall_ready,
        "hard_gates": {
            "passed": summary.hard_passed,
            "total": summary.hard_total,
        },
        "gates": [
            {
                "name": r.name,
                "gate_class": r.gate_class,
                "layer": r.layer,
                "passed": r.passed,
                "exit_code": r.exit_code,
            }
            for r in summary.results
        ],
    }
    print("--- JSON SUMMARY ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def run_pr_fast_gates() -> BaselineSummary:
    """Run only PR Fast Gate: skip heavy test suites and DB audit."""
    summary = BaselineSummary()
    python = sys.executable

    # ── Layer 0: Static Analysis ─────────────────────────────
    wave_files = [
        str(SCRIPTS / "run_verification_baseline.py"),
        str(SCRIPTS / "check_document_registry.py"),
        str(SCRIPTS / "check_verification_debt.py"),
        str(SCRIPTS / "check_receipt_integrity.py"),
        str(SCRIPTS / "check_verification_manifest.py"),
        str(SCRIPTS / "check_coverage_governance.py"),
        str(SCRIPTS / "audit_runtime_evidence_db.py"),
        str(ROOT / "tests" / "unit" / "test_verification_baseline.py"),
        str(ROOT / "tests" / "unit" / "test_repo_governance_cli.py"),
        str(ROOT / "tests" / "unit" / "governance" / "test_coverage_governance.py"),
        str(ROOT / "tests" / "unit" / "governance" / "test_partial_checker_discovery.py"),
        str(SCRIPTS / "repo_governance_cli.py"),
    ]
    summary.results.append(
        _run_gate(
            "ruff check (Wave files)",
            "hard",
            "L0",
            [python, "-m", "ruff", "check", *wave_files],
        )
    )
    summary.results.append(
        _run_gate(
            "ruff format check (Wave files)",
            "hard",
            "L0",
            [python, "-m", "ruff", "format", "--check", "--preview", *wave_files],
        )
    )

    # ── Layer 4: Architecture Boundaries ────────────────────
    summary.results.append(
        _run_gate(
            "Architecture boundaries",
            "hard",
            "L4",
            [python, str(SCRIPTS / "check_architecture.py")],
        )
    )

    # ── Layer 4A: Coverage Governance ──────────────────────
    summary.results.append(
        _run_gate(
            "Coverage governance",
            "hard",
            "L4",
            [python, str(SCRIPTS / "check_coverage_governance.py")],
        )
    )

    # ── Layer 5: Runtime Evidence (Static) ──────────────────
    summary.results.append(
        _run_gate(
            "Runtime evidence integrity",
            "hard",
            "L5",
            [python, str(SCRIPTS / "check_runtime_evidence.py")],
        )
    )

    # ── Layer 6: Document Registry Governance ────────────────
    summary.results.append(
        _run_gate(
            "Document registry governance",
            "hard",
            "L6",
            [python, str(SCRIPTS / "check_document_registry.py")],
        )
    )

    # ── Layer 7: Verification Debt Ledger ────────────────────
    summary.results.append(
        _run_gate(
            "Verification debt ledger",
            "hard",
            "L7A",
            [python, str(SCRIPTS / "check_verification_debt.py")],
        )
    )

    # ── Layer 7: Receipt Integrity ───────────────────────────
    summary.results.append(
        _run_gate(
            "Receipt integrity",
            "hard",
            "L7B",
            [python, str(SCRIPTS / "check_receipt_integrity.py")],
        )
    )

    # ── Layer 8: Verification Gate Manifest ──────────────────
    summary.results.append(
        _run_gate(
            "Verification gate manifest",
            "hard",
            "L8",
            [python, str(SCRIPTS / "check_verification_manifest.py")],
        )
    )

    # ── Layer 7: Eval Corpus ────────────────────────────────
    summary.results.append(
        _run_gate(
            "Eval corpus (24 cases)",
            "hard",
            "L7",
            [python, str(ROOT / "evals" / "run_evals.py")],
        )
    )

    # ── Layer 10: Repo CLI Smoke ────────────────────────────

    result = _run_gate(
        "Repo CLI smoke (valid→execute)",
        "hard",
        "L10",
        [
            python,
            str(SCRIPTS / "repo_governance_cli.py"),
            "--task-description",
            "Fix unit test naming",
            "--file-path",
            "tests/unit/test_example.py",
            "--estimated-impact",
            "low",
            "--reasoning",
            "Small test-only cleanup",
            "--test-plan",
            "uv run pytest tests/unit/test_example.py",
            "--json",
        ],
    )
    try:
        parsed = json.loads(result.stdout)
        if parsed.get("decision") != "execute":
            result.passed = False
            result.output += " [unexpected decision: " + parsed.get("decision", "?") + "]"
    except json.JSONDecodeError:
        result.passed = False
        result.output = "JSON parse failed: " + result.stdout[:200]
    summary.results.append(result)

    fb_result = _run_gate(
        "Repo CLI smoke (forbidden→reject)",
        "hard",
        "L10",
        [
            python,
            str(SCRIPTS / "repo_governance_cli.py"),
            "--task-description",
            "Update environment secret",
            "--file-path",
            ".env",
            "--estimated-impact",
            "low",
            "--reasoning",
            "Dangerous secret change",
            "--test-plan",
            "manual review",
            "--json",
        ],
    )
    try:
        parsed = json.loads(fb_result.stdout)
        if parsed.get("decision") != "reject":
            fb_result.passed = False
            fb_result.output += " [expected reject, got " + parsed.get("decision", "?") + "]"
        else:
            fb_result.passed = True
    except json.JSONDecodeError:
        fb_result.passed = False
        fb_result.output = "JSON parse failed: " + fb_result.stdout[:200]
    summary.results.append(fb_result)

    return summary


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Ordivon Verification Baseline Runner")
    parser.add_argument(
        "--profile",
        choices=["full", "pr-fast"],
        default="full",
        help="Which gate set to run (default: full)",
    )
    args = parser.parse_args()

    if args.profile == "pr-fast":
        summary = run_pr_fast_gates()
    else:
        summary = run_all_gates()

    print_summary(summary)
    print_json_summary(summary)
    return 0 if summary.overall_ready else 1


if __name__ == "__main__":
    sys.exit(main())
