"""Coverage Governance Checker."""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "docs" / "governance" / "checker-coverage-manifest.json"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

REQ={"schema_version","generated","purpose","coverage_policy","checkers"}

def run():
    errors, stats = [], {}
    if not MANIFEST_PATH.exists():
        return CheckerResult("fail",1,[f"Missing: {MANIFEST_PATH}"],stats)
    try: d=json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError as e: return CheckerResult("fail",1,[f"Invalid JSON: {e}"])
    if m:=REQ-set(d.keys()): errors.append(f"Missing top: {m}")
    checkers = d.get("checkers",[]); stats["checkers"]=len(checkers)
    seen=set()
    for c in checkers:
        cid=c.get("checker_id","?");
        if cid in seen: errors.append(f"dup: {cid}"); seen.add(cid)
    return CheckerResult("fail" if errors else "pass", 1 if errors else 0, errors, stats)

if __name__ == "__main__":
    r=run(); print(f"  Checkers: {r.stats.get('checkers',0)} | Violations: {len(r.findings)}")
    for f in r.findings: print(f"    {f}"); sys.exit(r.exit_code)
