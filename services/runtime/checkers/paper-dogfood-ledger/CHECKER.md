---
gate_id: paper_dogfood_ledger
display_name: Paper Dogfood Ledger
layer: L7E
hardness: hard
purpose: Validate paper dogfood ledger invariants — environment, live_order, paper_only, CandidateRule advisory, simulated PnL
protects_against: "Paper/live confusion, CandidateRule-as-Policy, PnL without simulated label, missing completion events, boundary violation ambiguity"
profiles: ['full']
timeout: 60
tags: [finance, paper-trading, dogfood, ledger]
---

# Paper Dogfood Ledger Checker

## Purpose

Validates the paper dogfood ledger JSONL — the evidence chain for Phase 7P
paper trading. Ensures every event is paper-only, every CandidateRule is
advisory, every PnL is labeled simulated, and every completed trade has
the full event chain.

## Protects Against

- Paper/live confusion (environment != paper)
- CandidateRule treated as Policy
- PnL without simulated label
- Incomplete trade event chains
- Boundary violations not explicitly flagged

## Governed Object

`docs/runtime/paper-trades/paper-dogfood-ledger.jsonl` — 30 events, 3 completed round trips, 4 refusals, 0 violations.
