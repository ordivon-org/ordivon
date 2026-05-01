"""Ordivon Verify — document registry validator (lightweight external mode)."""

from __future__ import annotations

import json
from pathlib import Path


def validate_document_registry(path: Path) -> dict:
    """Validate a JSONL document registry file. Returns result dict with status."""
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
    errors = []
    for e in entries:
        did = e.get("doc_id", "?")
        for field in ("doc_id", "path", "type", "status", "authority"):
            if field not in e:
                errors.append(f"{did}: missing '{field}'")
        if e.get("status", "") == "stale":
            errors.append(f"{did}: document is stale")
    if errors:
        return {"status": "FAIL", "exit_code": 1, "stdout": "", "stderr": "; ".join(errors)}
    return {
        "status": "PASS",
        "exit_code": 0,
        "stdout": f"Document registry: {len(entries)} entries, 0 violations",
        "stderr": "",
    }
