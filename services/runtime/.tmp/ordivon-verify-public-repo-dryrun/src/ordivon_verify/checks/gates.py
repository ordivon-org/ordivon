"""Ordivon Verify — gate manifest validator (lightweight external mode)."""

from __future__ import annotations

import json
from pathlib import Path


def _is_noop_cmd(cmd: str) -> bool:
    cmd_s = cmd.strip()
    if not cmd_s:
        return False
    return cmd_s in ("echo ok", "true", "exit 0", ": pass", "echo pass")


def validate_gate_manifest(path: Path) -> dict:
    """Validate a JSON gate manifest file. Returns result dict with status."""
    with open(path) as f:
        manifest = json.load(f)
    gates = manifest.get("gates", [])
    gate_count = manifest.get("gate_count", len(gates))
    errors = []
    for g in gates:
        gid = g.get("gate_id", "?")
        if not g.get("gate_id"):
            errors.append("gate missing gate_id")
        if not g.get("display_name"):
            errors.append(f"{gid}: missing display_name")
        cmd = g.get("command", "")
        if not cmd:
            errors.append(f"{gid}: missing command")
        elif _is_noop_cmd(cmd):
            errors.append(f"{gid}: command appears to be a no-op: '{cmd}'")
    if len(gates) != gate_count:
        errors.append(f"gate_count ({gate_count}) != actual gates ({len(gates)})")
    if errors:
        return {"status": "FAIL", "exit_code": 1, "stdout": "", "stderr": "; ".join(errors)}
    return {
        "status": "PASS",
        "exit_code": 0,
        "stdout": f"Gate manifest: {len(gates)} gates, 0 violations",
        "stderr": "",
    }
