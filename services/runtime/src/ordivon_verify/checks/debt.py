"""Ordivon Verify — debt ledger validator (lightweight external mode)."""

from __future__ import annotations

import json
from pathlib import Path


def validate_debt_ledger(path: Path) -> dict:
    """Validate a JSONL debt ledger file. Returns result dict with status."""
    with open(path) as f:
        entries = []
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                return {"status": "FAIL", "exit_code": 1, "stdout": "", "stderr": f"Line {i}: invalid JSON: {e}"}
    open_count = sum(1 for e in entries if e.get("status") == "open")
    closed_count = sum(1 for e in entries if e.get("status") == "closed")
    if open_count > 0:
        return {"status": "FAIL", "exit_code": 1, "stdout": "", "stderr": f"{open_count} open debt(s) found"}
    return {
        "status": "PASS",
        "exit_code": 0,
        "stdout": f"Debt ledger: {len(entries)} entries, {closed_count} closed, 0 open",
        "stderr": "",
    }
