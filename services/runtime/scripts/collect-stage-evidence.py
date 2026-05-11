#!/usr/bin/env python3
"""Collect stage evidence — run a command, save output, record hash (GOS-PM-1).

Usage:
    python scripts/collect-stage-evidence.py \\
        --stage GOS-PM-1-03 \\
        --evidence-id EV-GOS-PM-1-03-001 \\
        --command "uv run python scripts/verify-path-map.py" \\
        --expected-exit 0
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_BASE = ROOT / "docs/governance/evidence"
INDEX_PATH = EVIDENCE_BASE / "gos-pm-1" / "stage-evidence-index.jsonl"


def parse_args():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    return args


def main() -> int:
    args = parse_args()
    stage = args.get("stage", "")
    evidence_id = args.get("evidence-id", "")
    command = args.get("command", "")
    expected_exit = int(args.get("expected-exit", "0"))

    if not stage or not evidence_id or not command:
        print("Usage: collect-stage-evidence.py --stage GOS-PM-1-03 --evidence-id EV-... --command '...' [--expected-exit 0]")
        return 1

    # Create evidence directory
    stage_dir = EVIDENCE_BASE / "gos-pm-1" / f"{stage[8:]}-stage" if stage.startswith("GOS-PM-1-") else EVIDENCE_BASE / "gos-pm-1" / stage
    raw_dir = stage_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Run command
    print(f"Running: {command}")
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True,
        cwd=str(ROOT), timeout=60
    )

    # Save raw output
    output_file = raw_dir / f"{evidence_id}.txt"
    output_content = f"COMMAND: {command}\nEXIT: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    output_file.write_text(output_content)
    sha = hashlib.sha256(output_content.encode()).hexdigest()[:16]

    # Determine pass/fail
    passed = result.returncode == expected_exit

    # Create evidence entry
    entry = {
        "evidence_id": evidence_id,
        "stage_id": stage,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": command,
        "expected_exit": expected_exit,
        "actual_exit": result.returncode,
        "passed": passed,
        "raw_output": str(output_file.relative_to(ROOT)),
        "sha256": sha,
    }

    # Append to index
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    status = "✓" if passed else "✗"
    print(f"{status} {evidence_id}: exit={result.returncode} (expected {expected_exit}) sha256={sha}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
