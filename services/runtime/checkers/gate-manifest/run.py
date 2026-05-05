"""Gate Manifest Checker."""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "docs" / "governance" / "verification-gate-manifest.json"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    errors, stats = [], {}
    if not MANIFEST_PATH.exists():
        return CheckerResult("fail",1,[f"Missing: {MANIFEST_PATH}"],stats)
    try: m = json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError as e: return CheckerResult("fail",1,[f"Invalid JSON: {e}"])
    gates = m.get("gates",[]); stats["gates"]=len(gates)
    if m.get("gate_count",0) != len(gates): errors.append("gate_count mismatch")
    ids=set()
    for g in gates:
        gid=g.get("gate_id","?");
        if gid in ids: errors.append(f"dup: {gid}"); ids.add(gid)
        if g.get("hardness") not in ("hard", "escalation", "advisory"):
            errors.append(f"{gid}: invalid hardness '{g.get('hardness')}'")
        for fld in ("gate_id","display_name","layer","hardness","command"):
            if fld not in g: errors.append(f"{gid}: missing {fld}")
    return CheckerResult("fail" if errors else "pass", 1 if errors else 0, errors, stats)

if __name__ == "__main__":
    r=run(); print(f"  Gates: {r.stats.get('gates',0)} | Violations: {len(r.findings)}")
    for f in r.findings: print(f"    {f}"); sys.exit(r.exit_code)
