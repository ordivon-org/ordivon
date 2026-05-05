"""Architecture Boundaries Checker."""

from __future__ import annotations
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ["governance","state","domains","capabilities","execution","shared"]
ALLOW = {"governance_engine/policy_source.py","state/db/schema.py","domains/finance/read_only_adapter.py"}
FORBID = [
    ("from packs.finance.tool_refs import","pack tool_refs in Core"),
    ("from packs.finance.policy import","pack policy in Core"),
    ("stop_loss","stop_loss in Core"),("max_loss_usdt","max_loss_usdt in Core"),
    ("is_chasing","is_chasing in Core"),("is_revenge_trade","is_revenge_trade in Core"),
    ("place_order","place_order in Core"),("execute_trade","execute_trade in Core"),
]

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    findings, stats = [], {"files":0}
    for m in CORE:
        mp = ROOT / m
        if not mp.exists(): continue
        for pf in mp.rglob("*.py"):
            if "__pycache__" in str(pf): continue
            rel = str(pf.relative_to(ROOT))
            if rel in ALLOW: continue
            stats["files"]+=1
            txt = pf.read_text(encoding="utf-8")
            for pat,desc in FORBID:
                if pat in txt: findings.append(f"{rel}: {desc}")
    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, stats)

if __name__ == "__main__":
    r=run(); print(f"  Files: {r.stats.get('files',0)} | Violations: {len(r.findings)}")
    for f in r.findings: print(f"    {f}"); sys.exit(r.exit_code)
