"""Runtime Evidence Checker."""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = [
    ("docs/governance/verification-gate-manifest.json","json"),
    ("docs/governance/checker-coverage-manifest.json","json"),
    ("docs/governance/document-registry.jsonl","jsonl"),
    ("docs/governance/verification-debt-ledger.jsonl","jsonl"),
]

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    findings, stats = [], {"present":0,"missing":0,"invalid":0}
    for ps,fmt in ARTIFACTS:
        p = ROOT / ps
        if not p.exists(): findings.append(f"Missing: {ps}"); stats["missing"]+=1; continue
        stats["present"]+=1
        try:
            if fmt=="json": json.loads(p.read_text())
            else:
                for ln in p.read_text().splitlines():
                    if ln.strip(): json.loads(ln)
        except Exception as e: findings.append(f"Invalid {ps}: {e}"); stats["invalid"]+=1
    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, stats)

if __name__ == "__main__":
    r=run(); print(f"  Present: {r.stats.get('present',0)} | Violations: {len(r.findings)}")
    for f in r.findings: print(f"    {f}"); sys.exit(r.exit_code)
