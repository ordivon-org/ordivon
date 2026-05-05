"""Paper Dogfood Ledger Checker — validates paper trading ledger invariants.

Migrated from scripts/check_paper_dogfood_ledger.py.
Entry point: def run() -> CheckerResult.
"""

from __future__ import annotations
import json, sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = ROOT / "docs" / "runtime" / "paper-trades" / "paper-dogfood-ledger.jsonl"

REQUIRED_COMPLETION = {"ORDER_SUBMITTED", "ORDER_FILLED", "ORDER_CLOSED", "OUTCOME_CAPTURED", "REVIEW_COMPLETED"}
BLOCKING = {"ORDER_PENDING"}
TERMINAL = {"ORDER_CLOSED", "ORDER_EXPIRED", "ORDER_REJECTED", "ORDER_CANCELED"}
REFUSAL = {"TRADE_REJECTED", "TRADE_HELD", "TRADE_NO_GO"}

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run() -> CheckerResult:
    stats = {"total_events": 0, "completed_rt": 0, "pending": 0,
             "hold": 0, "reject": 0, "no_go": 0, "boundary_violations": 0,
             "simulated_pnl": 0.0}
    findings = []

    if not LEDGER_PATH.exists():
        return CheckerResult("fail", 1, [f"Missing: {LEDGER_PATH}"], dict(stats))

    events = []
    with open(LEDGER_PATH) as f:
        for i, line in enumerate(f, 1):
            if not line.strip(): continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                findings.append(f"Line {i}: invalid JSON: {e}")

    stats["total_events"] = len(events)
    ids = set()
    trade_states = defaultdict(set)

    for e in events:
        eid = e.get("event_id", "?")
        tid = e.get("trade_id", "UNKNOWN")
        trade_states[tid].add(e["event_type"])

        if eid in ids:
            findings.append(f"DUPLICATE: {eid}")
        ids.add(eid)

        if e.get("environment") != "paper":
            findings.append(f"{eid}: environment={e.get('environment')}, expected 'paper'")
        if e.get("live_order") is not False:
            findings.append(f"{eid}: live_order={e.get('live_order')}, expected false")
        if e.get("paper_only") is not True:
            findings.append(f"{eid}: paper_only={e.get('paper_only')}, expected true")

        if e["event_type"] in REFUSAL and e.get("order_id_masked"):
            findings.append(f"{eid}: {e['event_type']} has order_id — no order should exist")

        if e["event_type"] == "CANDIDATE_RULE_OBSERVED":
            if e.get("status") != "advisory":
                findings.append(f"{eid}: CandidateRule status={e.get('status')}, expected 'advisory'")
            notes = str(e.get("notes", ""))
            if "Policy" in notes and "NOT Policy" not in notes:
                findings.append(f"{eid}: CandidateRule may be marked as Policy")

        if e.get("simulated_pnl") and "simulated" not in str(e.get("notes", "")).lower():
            findings.append(f"{eid}: simulated_pnl present but 'simulated' not in notes")

        if e.get("boundary_violation") not in (True, False):
            findings.append(f"{eid}: boundary_violation must be boolean")

        # Count stats
        if e["event_type"] in REFUSAL:
            if e["event_type"] == "TRADE_HELD": stats["hold"] += 1
            elif e["event_type"] == "TRADE_REJECTED": stats["reject"] += 1
            elif e["event_type"] == "TRADE_NO_GO": stats["no_go"] += 1
        if e.get("boundary_violation"): stats["boundary_violations"] += 1
        if isinstance(e.get("simulated_pnl"), (int, float)):
            stats["simulated_pnl"] += float(e["simulated_pnl"])

    # Check completed trades
    for tid, types in trade_states.items():
        if tid in ("LEDGER", "CR-GLOBAL") or tid.startswith(("B1-", "H1-", "N1-")):
            continue
        if "REVIEW_COMPLETED" in types:
            stats["completed_rt"] += 1
            missing = REQUIRED_COMPLETION - types
            if missing:
                findings.append(f"{tid}: completed but missing events: {missing}")
        if bool(BLOCKING & types) and not bool(TERMINAL & types) and "REVIEW_COMPLETED" not in types:
            stats["pending"] += 1

    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, dict(stats))

if __name__ == "__main__":
    r = run()
    s = r.stats
    print(f"Events: {s.get('total_events',0)} | RTs: {s.get('completed_rt',0)} completed, {s.get('pending',0)} pending")
    print(f"Refusals: {s.get('hold',0)} HOLD, {s.get('reject',0)} REJECT, {s.get('no_go',0)} NO-GO")
    if s.get('simulated_pnl', 0): print(f"Paper PnL: ${s['simulated_pnl']:+.2f} (simulated)")
    print(f"Violations: {len(r.findings)}")
    for f in r.findings: print(f"  {f}")
    sys.exit(r.exit_code)
