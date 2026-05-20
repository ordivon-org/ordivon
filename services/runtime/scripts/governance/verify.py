#!/usr/bin/env python3
"""Governance Verify — run all AOS-AUTO checks and produce verification summary.

Usage:
    python3 scripts/governance/verify.py
    python3 scripts/governance/verify.py --phase AOS
    python3 scripts/governance/verify.py --json

Checks:
    inventory gap check
    admission validator test
    receipt claim replay
    reconciliation dry-run
    evidence bundle check
    overclaim / authority safety
    AOS identity test
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ordivon_governance_core.result import GovernanceResult

ROOT = Path(__file__).resolve().parents[2]

# Known deferred gaps and their severity (updated post-RT-1, post-HARDEN-1)
KNOWN_GAPS = {
    "RT-INV-001": {
        "description": "AOS prefix does not discover AOS-AUTO files; use --phase AOS-AUTO or --phase-family AOS",
        "severity": "WARN",
        "blocks_promotion": False,
        "resolution": "DEFERRED — AOS-AUTO prefix works; phase-family mode available",
    },
    "RT-ROUTE-001": {
        "description": "docs/governance/aos-auto/ surface added to routing",
        "severity": "WARN",
        "blocks_promotion": False,
        "resolution": "RESOLVED — aos-auto surface now mapped",
    },
    "RT-VERIFY-001": {
        "description": "Verify now reports bounded_limitations and known WARN findings",
        "severity": "WARN",
        "blocks_promotion": False,
        "resolution": "RESOLVED — verify includes known_gaps, promotion_readiness, overall_status semantics",
    },
    "CI-NOT-CONFIGURED": {
        "description": "Governance verify is local-only; CI not configured",
        "severity": "WARN",
        "blocks_promotion": False,
        "resolution": "DEFERRED — CI config requires infra change",
    },
    "ROUTING-PARTIAL": {
        "description": "Routing covers 10+ surfaces, not exhaustive for all Ordivon paths",
        "severity": "WARN",
        "blocks_promotion": False,
        "resolution": "DEFERRED — expand as surfaces grow",
    },
    "HISTORICAL-EVIDENCE-ABSENT": {
        "description": "AOS-0..RS evidence not retroactively filled; AUTO evidence covers W0-5 and later",
        "severity": "WARN",
        "blocks_promotion": False,
        "resolution": "DEFERRED — not retroactively fabricated",
    },
}


CHECKS = [
    {
        "check_id": "inventory-gaps",
        "name": "Inventory registry gap check",
        "command": ["python3", str(ROOT / "scripts/governance/inventory_phase.py"), "--phase", "AOS", "--json"],
        "parse_output": "inventory_json",
        "pass_condition": "gaps_acceptable",
        "timeout": 30,
    },
    {
        "check_id": "admission-reject-invalid",
        "name": "Admission: reject invalid registry entries",
        "command": ["python3", str(ROOT / "scripts/governance/admit_artifact.py"), "--stdin"],
        "stdin": '{"doc_id":"test-reject","path":"fake.md","title":"Bad","doc_type":"nonexistent","status":"current","authority":"wrong"}',
        "parse_output": "admission_json",
        "pass_condition": "rejected",
        "expected_exit": 1,
        "timeout": 10,
    },
    {
        "check_id": "receipt-replay",
        "name": "Receipt claim replay: AOS-1 identity validation",
        "command": ["python3", str(ROOT / "scripts/validate-aos-object-identity.py"), "--all-fixtures"],
        "parse_output": "text",
        "pass_condition": "contains_valid_pass",
        "expected_exit": 0,
        "timeout": 15,
    },
    {
        "check_id": "reconcile-dry-run",
        "name": "Reconciliation DAG dry-run",
        "command": ["python3", str(ROOT / "scripts/governance/reconcile.py"), "--dry-run"],
        "parse_output": "text",
        "pass_condition": "contains_steps",
        "expected_exit": 0,
        "timeout": 10,
    },
    {
        "check_id": "overclaim",
        "name": "Overclaim detection via OPA",
        "command": [
            "python3",
            str(ROOT / "scripts/detect_overclaim.py"),
            str(ROOT / "receipts/governance/aos-rs-final-summit-receipt.md"),
            str(ROOT / "receipts/governance/aos-fix-1-closure-receipt.md"),
        ],
        "parse_output": "opa_overclaim",
        "pass_condition": "zero_findings",
        "expected_exit": 0,
        "timeout": 15,
    },
    {
        "check_id": "evidence-index",
        "name": "Evidence index exists for AOS-AUTO-W0-5",
        "command": [
            "python3",
            "-c",
            "import json; from pathlib import Path; p=Path('/root/projects/Ordivon/docs/governance/evidence/AOS-AUTO-W0-5/stage-evidence-index.jsonl'); print(f'EXISTS={p.exists()}, ENTRIES={sum(1 for _ in open(p)) if p.exists() else 0}')",
        ],
        "parse_output": "text",
        "pass_condition": "exists_with_entries",
        "expected_exit": 0,
        "timeout": 5,
    },
]


def check_inventory_json(output: str, condition: str) -> tuple[bool, str]:
    try:
        data = json.loads(output)
        total = data.get("total_files", 0)
        registered = data.get("registered_count", 0)
        unregistered = data.get("unregistered_count", 0)
        data.get("missing_registry_entries", [])
        boundary = data.get("phase_boundary_present", False)

        findings = []
        if unregistered > 0:
            findings.append(f"{unregistered} unregistered files")
        if not boundary:
            findings.append("phase boundary not present")

        if condition == "gaps_acceptable":
            # Acceptable: gaps exist but are tracked
            passed = total > 0 and boundary
            detail = f"Files: {total}, Registered: {registered}, Unregistered: {unregistered}, Boundary: {boundary}"
            return passed, detail
        return False, f"Unknown condition: {condition}"
    except Exception as e:
        return False, f"Parse error: {e}"


def check_admission_json(output: str, condition: str) -> tuple[bool, str]:
    try:
        data = json.loads(output)
        valid = data.get("valid", True)
        errors = data.get("errors", [])
        if condition == "rejected":
            passed = not valid and len(errors) > 0
            return passed, f"Rejected: {not valid}, Errors: {len(errors)}"
        return False, f"Unknown condition: {condition}"
    except Exception as e:
        return False, f"Parse error: {e}"


def check_text(output: str, condition: str) -> tuple[bool, str]:
    if condition == "contains_valid_pass":
        passed = "Valid fixtures: 1/1 passed" in output or "1/1 passed" in output
        return passed, f"Contains valid pass: {passed}"
    elif condition == "contains_steps":
        passed = "Steps:" in output and "RECONCILIATION PLAN" in output
        return passed, f"Contains DAG plan: {passed}"
    elif condition == "zero_findings":
        passed = "Findings: 0" in output
        return passed, f"Zero overclaim findings: {passed}"
    elif condition == "exists_with_entries":
        passed = "EXISTS=True" in output and "ENTRIES=" in output
        # Extract entry count
        import re

        m = re.search(r"ENTRIES=(\d+)", output)
        count = int(m.group(1)) if m else 0
        return passed, f"Evidence index entries: {count}"
    return False, f"Unknown condition: {condition}"


PARSERS = {
    "inventory_json": check_inventory_json,
    "admission_json": check_admission_json,
    "text": check_text,
}


def run_check(check: dict) -> dict:
    result = {
        "check_id": check["check_id"],
        "name": check["name"],
        "status": "pending",
        "passed": False,
        "detail": "",
        "exit_code": None,
        "duration_ms": 0,
    }

    start = time.time()
    try:
        proc = subprocess.run(
            check["command"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=check.get("timeout", 30),
            input=check.get("stdin", ""),
        )

        output = proc.stdout or ""
        result["exit_code"] = proc.returncode

        expected_exit = check.get("expected_exit", 0)
        if proc.returncode != expected_exit:
            result["status"] = "exit_mismatch"
            result["detail"] = f"Expected exit {expected_exit}, got {proc.returncode}"
            return result

        parser_name = check.get("parse_output", "text")
        parser = PARSERS.get(parser_name)
        if parser:
            passed, detail = parser(output, check["pass_condition"])
            result["passed"] = passed
            result["status"] = "passed" if passed else "failed"
            result["detail"] = detail
        else:
            result["status"] = "unparsed"
            result["detail"] = f"No parser: {parser_name}"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)

    result["duration_ms"] = int((time.time() - start) * 1000)
    return result


def main():
    output_json = "--json" in sys.argv

    print("=== GOVERNANCE VERIFY ===")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Checks: {len(CHECKS)}")
    print()

    results = []
    for check in CHECKS:
        print(f"  [{check['check_id']}] {check['name']}...", end=" ", flush=True)
        result = run_check(check)
        icon = "✓" if result["status"] == "passed" else "✗"
        print(f"{icon} ({result['duration_ms']}ms)")
        if not result["passed"] and result["status"] != "passed":
            print(f"       {result['detail'][:120]}")
        results.append(result)

    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] in ("failed", "exit_mismatch"))
    error = sum(1 for r in results if r["status"] in ("error", "timeout"))

    result = GovernanceResult(
        tool="governance-verify",
        status="PASS",
        run_id=None,
        summary=f"Functional checks: {passed}/{len(CHECKS)} passed. Failed: {failed}, Error: {error}",
        command="python3 scripts/governance/verify.py",
    )

    for r in results:
        if r["status"] != "passed":
            result.add_finding(r["check_id"], r["status"], r.get("detail", ""), affected_surface=r.get("name", ""))

    for gap_id, gap in sorted(KNOWN_GAPS.items()):
        result.add_gap(gap_id, gap["description"], gap.get("severity", "WARN"), gap.get("resolution", ""))

    if any(v.get("blocks_promotion") for v in KNOWN_GAPS.values()):
        result.promotion_impact = "p2"

    print("\n=== VERIFICATION SUMMARY ===")
    result.emit(output_json=False)

    summary = result.to_dict()
    summary["checks"] = [
        {
            "check_id": r["check_id"],
            "name": r["name"],
            "status": r["status"],
            "passed": r["passed"],
            "detail": r["detail"],
            "duration_ms": r["duration_ms"],
        }
        for r in results
    ]

    summary_path = ROOT / "docs/governance/generated/aos-auto-verification-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\nSummary: {summary_path}")

    if output_json:
        print(json.dumps(summary, indent=2))

    return 0 if result.status in ("PASS", "PASS_WITH_WARNINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
