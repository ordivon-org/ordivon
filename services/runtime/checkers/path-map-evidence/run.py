"""Path Map Evidence Checker — verify every governed node has evidence (GOS-PM-2)."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CheckerResult:
    status: str
    exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def run() -> CheckerResult:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify-path-map-evidence.py"), "--json"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=30
    )
    try:
        data = json.loads(result.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return CheckerResult(status="DEGRADED", exit_code=2, findings=[{"code": "PME-0", "message": "verify-path-map-evidence returned non-JSON"}])

    status = data.get("status", "DEGRADED")
    return CheckerResult(
        status=status,
        exit_code=0 if status == "READY" else 1,
        findings=data.get("findings", []),
        stats=data.get("stats", {}),
    )
