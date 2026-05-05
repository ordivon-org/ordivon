"""Document Freshness Auditor (DG-2)."""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "docs" / "governance" / "document-registry.jsonl"
CRITICAL = {"source_of_truth","current_status"}

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    findings, stats = [], {"total":0,"with_freshness":0,"no_last_verified":0,"stale":0,"stale_critical":0}
    if not REGISTRY_PATH.exists():
        return CheckerResult("fail",1,[f"Missing: {REGISTRY_PATH}"],stats)
    entries=[]
    with open(REGISTRY_PATH) as f:
        for ln in f:
            if not (ln:=ln.strip()): continue
            try: entries.append(json.loads(ln))
            except json.JSONDecodeError: pass
    today = date.today(); stats["total"]=len(entries)
    for e in entries:
        did=e.get("doc_id","?")
        lv=e.get("last_verified",""); sa=e.get("stale_after_days")
        if not lv:
            if e.get("authority","") in CRITICAL: stats["no_last_verified"]+=1; findings.append(f"{did}: missing last_verified (critical)")
            continue
        stats["with_freshness"]+=1
        try: lvd=date.fromisoformat(lv)
        except: findings.append(f"{did}: bad date {lv}"); continue
        w=sa if isinstance(sa,int) else 14; age=(today-lvd).days
        if age>w*2:
            stats["stale"]+=1
            if e.get("authority","") in CRITICAL: stats["stale_critical"]+=1; findings.append(f"{did}: CRITICAL STALE {age}d (window={w}d)")
            else: findings.append(f"{did}: stale {age}d (window={w}d)")
        elif age>w: findings.append(f"{did}: approaching stale {age}d (window={w}d)")
    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, dict(stats))

if __name__ == "__main__":
    r=run()
    print(f"  Entries: {r.stats.get('total',0)} | With freshness: {r.stats.get('with_freshness',0)}")
    print(f"  Stale: {r.stats.get('stale',0)} ({r.stats.get('stale_critical',0)} critical)")
    print(f"  Findings: {len(r.findings)}")
    for f in r.findings[:20]: print(f"    {f}")
    if len(r.findings)>20: print(f"    ... +{len(r.findings)-20} more")
    sys.exit(r.exit_code)
