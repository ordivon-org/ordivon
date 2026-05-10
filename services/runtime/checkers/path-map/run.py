"""Path Map Checker — verify generated path map matches repo reality.

Called by ordivon-verify auto-discovery (CHECKER.md + run.py pattern).
Delegates to scripts/verify-path-map.py.
"""

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
        [sys.executable, str(ROOT / "scripts/verify-path-map.py"), "--json"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=30
    )

    try:
        data = json.loads(result.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return CheckerResult(
            status="DEGRADED",
            exit_code=2,
            findings=[{"code": "PM-0", "message": "verify-path-map.py returned non-JSON output"}],
        )

    status = data.get("status", "DEGRADED")
    findings = []
    if data.get("drift"):
        findings.append({"code": "PM-1", "severity": "blocking", "message": "Path map drift detected — generated view inconsistent with repo reality"})
    if data.get("blocked"):
        findings.append({"code": "PM-2", "severity": "blocking", "message": "Unclassified protected paths exist"})
    if data.get("error"):
        findings.append({"code": "PM-0", "severity": "degraded", "message": data["error"]})

    return CheckerResult(
        status="READY" if status == "READY" else "BLOCKED" if status == "BLOCKED" else "DEGRADED",
        exit_code=0 if status == "READY" else 1 if status == "BLOCKED" else 2,
        findings=findings,
        stats={"status": status},
    )
