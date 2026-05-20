#!/usr/bin/env python3
"""Governance Evidence Collector — run commands, capture outputs, hash, index.

Usage:
    python3 scripts/governance/collect_evidence.py --phase AOS-AUTO-W0-5
    python3 scripts/governance/collect_evidence.py --phase AOS-AUTO-W0-5 --dry-run

Input:
    Reads evidence plan from docs/governance/evidence/<phase>/evidence-plan.json
    or falls back to default plan for the phase.

Output:
    docs/governance/evidence/<phase>/
    ├── stage-evidence-manifest.json
    ├── stage-evidence-index.jsonl
    ├── commands/
    │   ├── 001-<slug>.stdout.txt
    │   ├── 001-<slug>.stderr.txt
    │   └── 001-<slug>.command.json
    └── trace/
        └── governance-trace.jsonl
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "docs/governance/evidence"


DEFAULT_PLANS = {
    "AOS-AUTO-W0-5": [
        {
            "command_id": "AUTO-W0-5-CMD-001",
            "command": "python3 scripts/governance/inventory_phase.py --phase AOS --json",
            "description": "Inventory all AOS artifacts",
            "expected_failure": False,
            "supports_claims": ["AUTO-W0-5-CLAIM-001"],
            "timeout": 30,
        },
        {
            "command_id": "AUTO-W0-5-CMD-002",
            "command": "python3 scripts/governance/admit_artifact.py --stdin",
            "description": "Admission gate: reject invalid registry entry",
            "expected_failure": True,  # Expected to exit 1 on invalid input
            "stdin": '{"doc_id":"test-bad","path":"fake/path.md","title":"Bad","doc_type":"nonexistent","status":"current","authority":"wrong_auth"}',
            "supports_claims": ["AUTO-W0-5-CLAIM-002"],
            "timeout": 10,
        },
        {
            "command_id": "AUTO-W0-5-CMD-003",
            "command": "python3 scripts/governance/extract_receipt_claims.py receipts/governance/aos-1-object-identity-schema-receipt.md",
            "description": "Extract claims from AOS-1 receipt",
            "expected_failure": False,
            "supports_claims": ["AUTO-W0-5-CLAIM-003"],
            "timeout": 10,
        },
        {
            "command_id": "AUTO-W0-5-CMD-004",
            "command": "python3 scripts/validate-aos-object-identity.py --all-fixtures",
            "description": "Replay AOS-1 receipt claim: validate identity fixtures",
            "expected_failure": False,
            "supports_claims": ["AUTO-W0-5-CLAIM-003"],
            "timeout": 15,
        },
        {
            "command_id": "AUTO-W0-5-CMD-005",
            "command": "python3 scripts/governance/reconcile.py --dry-run",
            "description": "Reconciliation DAG dry-run",
            "expected_failure": False,
            "supports_claims": ["AUTO-W0-5-CLAIM-004"],
            "timeout": 10,
        },
        {
            "command_id": "AUTO-W0-5-CMD-006",
            "command": "python3 -m pytest tests/unit/governance/test_aos_identity_admission_compatibility.py -q",
            "description": "AOS identity + admission compatibility tests",
            "expected_failure": False,
            "supports_claims": ["AUTO-W0-5-CLAIM-005"],
            "timeout": 30,
        },
    ]
}


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def slugify(text: str) -> str:
    return text.lower().replace(" ", "-").replace("/", "-")[:40]


def run_command(cmd: dict, phase: str, dry_run: bool = False) -> dict:
    """Run a single command and capture results."""
    cmd_id = cmd["command_id"]
    slug = slugify(cmd["description"])

    result = {
        "command_id": cmd_id,
        "command": cmd["command"],
        "description": cmd["description"],
        "working_directory": str(ROOT),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": None,
        "stdout_path": f"commands/{cmd_id}-{slug}.stdout.txt",
        "stderr_path": f"commands/{cmd_id}-{slug}.stderr.txt",
        "command_record_path": f"commands/{cmd_id}-{slug}.command.json",
        "sha256_stdout": None,
        "sha256_stderr": None,
        "expected_failure": cmd.get("expected_failure", False),
        "supports_claims": cmd.get("supports_claims", []),
        "status": "skipped" if dry_run else "pending",
        "duration_ms": 0,
        "error": None,
    }

    if dry_run:
        return result

    evidence_phase_dir = EVIDENCE_DIR / phase
    cmds_dir = evidence_phase_dir / "commands"
    cmds_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    stdin_input = cmd.get("stdin", "")

    try:
        proc = subprocess.run(
            cmd["command"],
            shell=True,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=cmd.get("timeout", 30),
            input=stdin_input,
        )

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        # Write stdout
        stdout_file = cmds_dir / f"{cmd_id}-{slug}.stdout.txt"
        stdout_file.write_text(stdout)

        # Write stderr
        stderr_file = cmds_dir / f"{cmd_id}-{slug}.stderr.txt"
        stderr_file.write_text(stderr)

        # Hashes
        result["sha256_stdout"] = sha256_hex(stdout)
        result["sha256_stderr"] = sha256_hex(stderr)
        result["exit_code"] = proc.returncode

        # Command record
        cmd_record = {
            "command_id": cmd_id,
            "command": cmd["command"],
            "stdin": stdin_input if stdin_input else None,
            "working_directory": str(ROOT),
            "exit_code": proc.returncode,
            "stdout_path": str(stdout_file.relative_to(evidence_phase_dir)),
            "stderr_path": str(stderr_file.relative_to(evidence_phase_dir)),
            "sha256_stdout": result["sha256_stdout"],
            "sha256_stderr": result["sha256_stderr"],
            "started_at": result["started_at"],
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "expected_failure": cmd.get("expected_failure", False),
            "supports_claims": cmd.get("supports_claims", []),
        }
        cmd_record_file = cmds_dir / f"{cmd_id}-{slug}.command.json"
        cmd_record_file.write_text(json.dumps(cmd_record, indent=2))

        # Determine status
        if proc.returncode != 0 and cmd.get("expected_failure", False):
            result["status"] = "completed_expected_failure"
        elif proc.returncode != 0:
            result["status"] = "failed"
        else:
            result["status"] = "completed"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = f"Timed out after {cmd.get('timeout', 30)}s"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    result["duration_ms"] = int((time.time() - start) * 1000)
    result["ended_at"] = datetime.now(timezone.utc).isoformat()

    return result


def generate_manifest(phase: str, commands: list[dict], results: list[dict]) -> dict:
    return {
        "phase": phase,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_commands": len(commands),
        "completed": sum(1 for r in results if r["status"] in ("completed", "completed_expected_failure")),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "error": sum(1 for r in results if r["status"] == "error"),
        "timeout": sum(1 for r in results if r["status"] == "timeout"),
        "claims": list(set(claim for cmd in commands for claim in cmd.get("supports_claims", []))),
    }


def main():
    dry_run = "--dry-run" in sys.argv
    phase = None

    for i, arg in enumerate(sys.argv):
        if arg == "--phase" and i + 1 < len(sys.argv):
            phase = sys.argv[i + 1]

    if not phase:
        print("Usage: collect_evidence.py --phase <PHASE> [--dry-run]")
        print("Available phases:", list(DEFAULT_PLANS.keys()))
        return 1

    commands = DEFAULT_PLANS.get(phase, [])
    if not commands:
        # Try loading from file
        plan_path = EVIDENCE_DIR / phase / "evidence-plan.json"
        if plan_path.exists():
            commands = json.loads(plan_path.read_text())
        else:
            print(f"No evidence plan found for phase: {phase}")
            return 1

    evidence_phase_dir = EVIDENCE_DIR / phase
    evidence_phase_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        print("=== EVIDENCE COLLECTION PLAN (dry-run) ===")
        print(f"Phase: {phase}")
        print(f"Commands: {len(commands)}")
        for cmd in commands:
            print(f"  [{cmd['command_id']}] {cmd['description']}")
            print(f"    Command: {cmd['command']}")
            print(f"    Expected failure: {cmd.get('expected_failure', False)}")
        return 0

    # Collect
    print(f"=== COLLECTING EVIDENCE: {phase} ===")
    results = []
    for cmd in commands:
        print(f"  [{cmd['command_id']}] {cmd['description']}...", end=" ", flush=True)
        result = run_command(cmd, phase)
        status_icons = {
            "completed": "✓",
            "completed_expected_failure": "✓ (expected)",
            "failed": "✗",
            "error": "✗",
            "timeout": "⏱",
        }
        print(f"{status_icons.get(result['status'], '?')} ({result['duration_ms']}ms)")
        results.append(result)

    # Generate manifest
    manifest = generate_manifest(phase, commands, results)
    manifest_path = evidence_phase_dir / "stage-evidence-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Generate index
    index_path = evidence_phase_dir / "stage-evidence-index.jsonl"
    with open(index_path, "w") as f:
        for r in results:
            entry = {
                "evidence_id": r["command_id"],
                "command": r["command"],
                "exit_code": r["exit_code"],
                "sha256_stdout": r["sha256_stdout"],
                "status": r["status"],
                "started_at": r["started_at"],
                "duration_ms": r["duration_ms"],
                "supports_claims": r["supports_claims"],
            }
            f.write(json.dumps(entry) + "\n")

    # Summary
    print("\n=== EVIDENCE SUMMARY ===")
    print(f"Phase: {phase}")
    print(f"Commands: {len(commands)}")
    for s in ["completed", "completed_expected_failure", "failed", "skipped", "error", "timeout"]:
        count = manifest.get(s, 0)
        if count:
            print(f"  {s}: {count}")
    print(f"Manifest: {manifest_path}")
    print(f"Index: {index_path}")

    has_failures = manifest.get("failed", 0) > 0 or manifest.get("error", 0) > 0
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
