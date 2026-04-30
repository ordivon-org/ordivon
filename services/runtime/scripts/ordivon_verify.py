#!/usr/bin/env python3
"""Ordivon Verify — Local read-only verification CLI.

Wraps existing governance checkers into a unified command surface.

Usage:
    uv run python scripts/ordivon_verify.py              # same as 'all'
    uv run python scripts/ordivon_verify.py all          # run all checks
    uv run python scripts/ordivon_verify.py receipts     # receipt integrity only
    uv run python scripts/ordivon_verify.py debt         # debt ledger only
    uv run python scripts/ordivon_verify.py gates        # gate manifest only
    uv run python scripts/ordivon_verify.py docs         # document registry only
    uv run python scripts/ordivon_verify.py all --json   # JSON output

Exit codes:
    0 = READY (all checks pass)
    1 = BLOCKED (one or more hard checks failed)
    2 = DEGRADED / NEEDS_REVIEW (reserved)
    3 = config / usage error
    4 = tool runtime error

Never calls network, broker, API, or writes files. Read-only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKER_SCRIPTS = {
    "receipts": ROOT / "scripts" / "check_receipt_integrity.py",
    "debt": ROOT / "scripts" / "check_verification_debt.py",
    "gates": ROOT / "scripts" / "check_verification_manifest.py",
    "docs": ROOT / "scripts" / "check_document_registry.py",
}

CHECKER_LABELS = {
    "receipts": "Receipt Integrity",
    "debt": "Verification Debt",
    "gates": "Gate Manifest",
    "docs": "Document Registry",
}

ALL_CHECKS = ["receipts", "debt", "gates", "docs"]


def run_check(check_id: str) -> dict:
    """Run a single checker script and return its result dict."""
    script = CHECKER_SCRIPTS[check_id]
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(ROOT),
        )
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Checker timed out: {check_id}",
        }
    except Exception as exc:
        return {
            "id": check_id,
            "label": CHECKER_LABELS[check_id],
            "status": "FAIL",
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Runtime error: {exc}",
        }


def determine_status(results: list[dict]) -> str:
    """Determine overall status from check results."""
    has_fail = any(r["status"] == "FAIL" for r in results)
    if has_fail:
        return "BLOCKED"
    return "READY"


def build_report(results: list[dict], mode: str) -> dict:
    """Build the full report dict (for JSON output)."""
    status = determine_status(results)
    hard_failures = [
        {"id": r["id"], "label": r["label"], "stderr": r["stderr"]} for r in results if r["status"] == "FAIL"
    ]
    return {
        "tool": "ordivon-verify",
        "schema_version": "0.1",
        "status": status,
        "mode": mode,
        "checks": [
            {
                "id": r["id"],
                "status": r["status"],
                "exit_code": r["exit_code"],
                "summary": (r["stdout"].split("\n")[-1] if r["stdout"] else (r["stderr"] or "no output")),
            }
            for r in results
        ],
        "hard_failures": hard_failures,
        "warnings": [],
    }


def print_human(results: list[dict]) -> None:
    """Print human-readable report."""
    status = determine_status(results)
    print("ORDIVON VERIFY")
    print(f"Status: {status}")
    print("Checks:")
    for r in results:
        icon = "\u2713" if r["status"] == "PASS" else "\u2717"
        print(f"  - {r['label'].lower()}: {icon} {r['status']}")
    print()


def status_to_exit_code(status: str) -> int:
    """Map status string to exit code."""
    if status == "READY":
        return 0
    if status == "BLOCKED":
        return 1
    if status in ("DEGRADED", "NEEDS_REVIEW"):
        return 2
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments. --json can appear before or after subcommand."""
    parser = argparse.ArgumentParser(
        prog="ordivon-verify",
        description="Ordivon Verify — local read-only verification CLI",
    )
    sub = parser.add_subparsers(dest="command", title="commands")

    sub.add_parser("all", help="Run all checks (receipts + debt + gates + docs)")
    sub.add_parser("receipts", help="Scan receipts for contradictions")
    sub.add_parser("debt", help="Check debt ledger invariants")
    sub.add_parser("gates", help="Verify gate manifest integrity")
    sub.add_parser("docs", help="Check document registry + semantic safety")

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON report",
    )

    # Use parse_known_args so --json can appear after subcommand
    known, unknown = parser.parse_known_args(argv)
    # Re-parse unknowns to catch --json in any position
    if unknown:
        for u in unknown:
            if u == "--json":
                known.json = True
            else:
                parser.error(f"unrecognized arguments: {' '.join(unknown)}")

    return known


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns exit code 0-4."""
    try:
        args = parse_args(argv)
    except SystemExit:
        return 3

    command = args.command or "all"

    if command not in CHECKER_SCRIPTS and command != "all":
        print(f"Unknown command: {command}", file=sys.stderr)
        return 3

    # Determine which checks to run
    if command == "all":
        check_ids = ALL_CHECKS
    else:
        check_ids = [command]

    try:
        results = [run_check(cid) for cid in check_ids]
        status = determine_status(results)

        if args.json:
            report = build_report(results, command)
            print(json.dumps(report, indent=2))
        else:
            print_human(results)

        return status_to_exit_code(status)
    except Exception as exc:
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
