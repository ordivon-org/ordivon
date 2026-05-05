"""Coding Discipline Fixtures Checker — validates coding intake test data."""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIRS = [
    ROOT / "tests" / "unit" / "packs",
    ROOT / "tests" / "fixtures" / "coding",
]

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run() -> CheckerResult:
    findings, stats = [], {"files": 0, "valid": 0, "invalid": 0}
    for d in FIXTURE_DIRS:
        if not d.exists(): continue
        for fpath in sorted(d.rglob("*.json")):
            stats["files"] += 1
            try:
                json.loads(fpath.read_text())
                stats["valid"] += 1
            except json.JSONDecodeError as e:
                stats["invalid"] += 1
                findings.append(f"{fpath.name}: {e}")

    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, dict(stats))

if __name__ == "__main__":
    r = run()
    s = r.stats
    print(f"Fixtures: {s.get('files',0)} | Valid: {s.get('valid',0)} | Invalid: {s.get('invalid',0)}")
    for f in r.findings: print(f"  {f}")
    sys.exit(r.exit_code)
