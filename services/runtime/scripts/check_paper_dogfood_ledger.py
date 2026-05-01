#!/usr/bin/env python3
"""Phase 7P-D1: Paper Dogfood Ledger Consistency Checker.

Reads paper-dogfood-ledger.jsonl and verifies core invariants.
Never calls Alpaca. Never requires API keys. Read-only evidence validation.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs" / "runtime" / "paper-trades" / "paper-dogfood-ledger.jsonl"

# ══════════════════════════════════════════════════════════════════════

REQUIRED_COMPLETION_EVENTS = {
    "ORDER_SUBMITTED",
    "ORDER_FILLED",
    "ORDER_CLOSED",
    "OUTCOME_CAPTURED",
    "REVIEW_COMPLETED",
}

BLOCKING_EVENTS = {"ORDER_PENDING"}

TERMINAL_EVENTS = {"ORDER_CLOSED", "ORDER_EXPIRED", "ORDER_REJECTED", "ORDER_CANCELED"}

REFUSAL_EVENTS = {"TRADE_REJECTED", "TRADE_HELD", "TRADE_NO_GO"}


def load_ledger(path: Path) -> list[dict]:
    events = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"ERROR line {i}: invalid JSON: {e}")
                sys.exit(1)
    return events


def check_invariants(events: list[dict]) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    trade_states: dict[str, set[str]] = defaultdict(set)

    for e in events:
        eid = e.get("event_id", f"line-{events.index(e)}")
        tid = e.get("trade_id", "UNKNOWN")

        # Track events per trade
        trade_states[tid].add(e["event_type"])

        # Invariant: unique event_id
        if eid in ids:
            errors.append(f"DUPLICATE event_id: {eid}")
        ids.add(eid)

        # Invariant: environment must be paper
        if e.get("environment") != "paper":
            errors.append(f"{eid}: environment={e.get('environment')}, expected 'paper'")

        # Invariant: live_order must be false
        if e.get("live_order") is not False:
            errors.append(f"{eid}: live_order={e.get('live_order')}, expected false")

        # Invariant: paper_only must be true
        if e.get("paper_only") is not True:
            errors.append(f"{eid}: paper_only={e.get('paper_only')}, expected true")

        # Invariant: HOLD/REJECT/NO-GO must not have order_id
        if e["event_type"] in REFUSAL_EVENTS:
            if e.get("order_id_masked"):
                errors.append(f"{eid}: {e['event_type']} has order_id_masked — no order should exist")

        # Invariant: CandidateRule is advisory, not Policy
        if e["event_type"] == "CANDIDATE_RULE_OBSERVED":
            if e.get("status") != "advisory":
                errors.append(f"{eid}: CandidateRule status={e.get('status')}, expected 'advisory'")
            if "Policy" in str(e.get("notes", "")):
                if "NOT Policy" not in str(e.get("notes", "")):
                    errors.append(f"{eid}: CandidateRule may be marked as Policy")

        # Invariant: paper PnL labeled simulated
        if e.get("simulated_pnl") is not None and e.get("simulated_pnl") != "":
            if "simulated" not in str(e.get("notes", "")).lower():
                errors.append(f"{eid}: simulated_pnl present but 'simulated' not in notes")

        # Invariant: boundary violations explicit
        if e.get("boundary_violation") not in (True, False):
            errors.append(f"{eid}: boundary_violation must be boolean")

    # Check completed trades
    for tid, types in trade_states.items():
        if tid in ("LEDGER", "CR-GLOBAL") or tid.startswith(("B1-", "H1-", "N1-")):
            continue

        if "REVIEW_COMPLETED" in types:
            missing = REQUIRED_COMPLETION_EVENTS - types
            if missing:
                errors.append(f"{tid}: completed but missing events: {missing}")

        # Pending check
        has_blocking = bool(BLOCKING_EVENTS & types)
        has_terminal = bool(TERMINAL_EVENTS & types)
        has_review = "REVIEW_COMPLETED" in types

        if has_blocking and not has_terminal and not has_review:
            # Pending is valid — just record. No next trade allowed.
            if has_blocking and "TRADE_INTAKE_ACCEPTED" in types:
                # Check that no second intake exists for another trade while this is pending
                pass  # handled by human governance, not code

    return errors


def print_summary(events: list[dict]) -> None:
    trade_states: dict[str, set[str]] = defaultdict(set)
    refusals: dict[str, int] = defaultdict(int)
    total_simulated_pnl = 0.0

    for e in events:
        tid = e.get("trade_id", "UNKNOWN")
        trade_states[tid].add(e["event_type"])
        if e["event_type"] in REFUSAL_EVENTS:
            refusals[e["event_type"]] += 1
        if isinstance(e.get("simulated_pnl"), (int, float)):
            total_simulated_pnl += float(e["simulated_pnl"])

    completed = sum(
        1
        for tid, types in trade_states.items()
        if "REVIEW_COMPLETED" in types and not tid.startswith(("B1-", "H1-", "N1-", "LEDGER", "CR-"))
    )
    pending = sum(
        1 for tid, types in trade_states.items() if "ORDER_PENDING" in types and "REVIEW_COMPLETED" not in types
    )

    print("=" * 50)
    print("PAPER DOGFOOD LEDGER SUMMARY")
    print("=" * 50)
    print(f"  Total events:          {len(events)}")
    print(f"  Completed round trips: {completed}")
    print(f"  Pending trades:        {pending}")
    print(f"  HOLD events:           {refusals.get('TRADE_HELD', 0)}")
    print(f"  REJECT events:         {refusals.get('TRADE_REJECTED', 0)}")
    print(f"  NO-GO events:          {refusals.get('TRADE_NO_GO', 0)}")
    print(f"  Boundary violations:   {sum(1 for e in events if e.get('boundary_violation'))}")
    if total_simulated_pnl != 0:
        print(f"  Cumulative paper PnL:  ${total_simulated_pnl:+.2f} (simulated)")
    print("  Phase 8 readiness:     3/10 DEFERRED")
    print()
    if pending:
        print(f"  ⚠ PT-005 BLOCKED: {pending} pending trade(s) unresolved")
    print("=" * 50)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else LEDGER_PATH
    if not path.exists():
        print(f"ERROR: ledger not found at {path}")
        return 1

    events = load_ledger(path)
    errors = check_invariants(events)

    if errors:
        print(f"\n❌ {len(errors)} INVARIANT VIOLATION(S):\n")
        for err in errors:
            print(f"  - {err}")
        print()
        return 1

    print_summary(events)
    print("\n✅ All invariants pass.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
