"""Verification Debt Ledger Checker."""

from __future__ import annotations
import json, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = ROOT / "docs" / "governance" / "verification-debt-ledger.jsonl"

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

VALID_CAT = {"skipped_verification","pre_existing_tooling_debt","untracked_residue","baseline_gate_gap","receipt_integrity_gap","checker_degradation","stale_baseline_count","semantic_overclaim"}
VALID_SEV = {"low","medium","high","blocking"}
VALID_STS = {"open","closed","accepted_until","superseded"}
REQ = {"debt_id","category","severity","status","owner","evidence","opened_at","closed_at"}

def run():
    errors, stats = [], {"total":0,"open":0,"closed":0}
    if not LEDGER_PATH.exists():
        return CheckerResult("fail",1,[f"Missing: {LEDGER_PATH}"],stats)
    entries = []
    with open(LEDGER_PATH) as f:
        for i, line in enumerate(f, 1):
            if not (line:=line.strip()): continue
            try: entries.append(json.loads(line))
            except json.JSONDecodeError as e: errors.append(f"L{i}: {e}")
    stats["total"] = len(entries); ids = set()
    for e in entries:
        did = e.get("debt_id","?")
        if m:=REQ-set(e.keys()): errors.append(f"{did}: missing {m}")
        if did in ids: errors.append(f"{did}: dup"); ids.add(did)
        if (c:=e.get("category","")) not in VALID_CAT: errors.append(f"{did}: bad cat {c}")
        if (s:=e.get("severity","")) not in VALID_SEV: errors.append(f"{did}: bad sev {s}")
        st = e.get("status","")
        if st not in VALID_STS: errors.append(f"{did}: bad status {st}")
        if st in ("open","accepted_until"): stats["open"]+=1
        if st=="closed": stats["closed"]+=1
    return CheckerResult("fail" if errors else "pass", 1 if errors else 0, errors, dict(stats))

if __name__ == "__main__":
    r=run()
    print(f"  Debts: {r.stats.get('total',0)} | Open: {r.stats.get('open',0)} | Violations: {len(r.findings)}")
    for f in r.findings[:10]: print(f"    {f}")
    sys.exit(r.exit_code)
