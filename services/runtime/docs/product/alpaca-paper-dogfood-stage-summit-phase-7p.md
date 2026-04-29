# Alpaca Paper Dogfood — Stage Summit (Phase 7P Close)

Status: **PUBLISHED** | Date: 2026-04-29

## 1. Executive Summary

Phase 7P was Alpaca Paper dogfood — a controlled paper-only governance validation stage.
Its purpose was to test Ordivon's governance pipeline against a live external execution environment
(Alpaca Paper Trading) while maintaining hard boundaries: paper ≠ live,
CandidateRule ≠ Policy, execution ≠ autonomy, PnL ≠ readiness.

**Phase 7P was NOT**: a profitability test, a strategy validation, a trading bot demo,
or preparation for live trading.

**Phase 7P WAS**: a systematic test of whether Ordivon's governance loop
(Observe → Intake → Receipt → Execution → Fill → Outcome → Review → CandidateRule)
could interact with a real external API without violating its own core semantics.

## 2. Timeline — 24 Sub-Phases

| Phase | What | Type |
|-------|------|------|
| 7A-R | Roadmap correction: Alpaca Paper before Live | Docs |
| 7P-1 | Alpaca Paper Trading Constitution | Docs |
| 7P-2 | PaperExecutionAdapter | Code |
| 7P-3 | PT-001 AAPL — first paper trade | Dogfood |
| 7P-3F | PT-001 fill reconciliation | Recon |
| 7P-Z (1st) | PT-001 closeout + formal review | Review |
| 7P-R | Repeated dogfood protocol + CR handling | Docs |
| 7P-L | Ledger + template + Phase 8 tracker | Docs |
| 7P-4 | PT-002 MSFT — market-hours validation | Dogfood |
| 7P-4S | PT-002 semantics seal | Seal |
| 7P-B1 | 8 boundary cases (HOLD/REJECT/NO-GO) | Docs |
| 7P-E1 | 34-test boundary corpus | Code |
| 7P-5 | PT-003 GOOGL — boundary preflight + first loss | Dogfood |
| 7P-H1 | Stale observation HOLD scenario | Docs |
| 7P-N1 | Live URL / auto-trading NO-GO scenarios | Docs |
| 7P-6 | PT-004 NFLX — pending limit order | Dogfood |
| 7P-6E | PT-004 expiry reconciliation | Recon |
| 7P-7 | PT-001 archive (11 files → 1) | Docs |
| 7P-D1 | JSONL ledger + 16-invariant checker | Code |
| 7P-C | Governed paper cancel capability | Code |
| 7P-CR | PT-004 cancel formal review | Review |
| 7P-Z | This Stage Summit | Closure |

## 3. Evidence Matrix

| Metric | Count |
|--------|-------|
| Completed paper round trips | 3 (PT-001 AAPL +$1.52, PT-002 MSFT +$0.26, PT-003 GOOGL -$0.24) |
| Pending/canceled orders | 1 (PT-004 NFLX, canceled after 5h pending) |
| HOLD events | 1 (stale observation) |
| REJECT events | 1 (missing reason_not_to_trade) |
| NO-GO events | 2 (live URL, AI auto-trading) |
| CandidateRules | 3 (CR-7P-001/002/003, all advisory) |
| Boundary violations | 0 |
| Ledger events | 30 (JSONL) |
| Checker invariants | 16 |
| Unit tests (backend) | 204 |
| Frontend tests | 57 |
| Pr-fast baseline | 7/7 |

## 4. What Was Proved

1. **Submit capability can be governed**: 3 round trips, all paper-only, all receipt-complete.
2. **Cancel capability can be governed**: PT-004 canceled via governed lifecycle, no replace, no chase.
3. **Paper/live boundary held**: 0 live orders. All live URL/key attempts blocked at init.
4. **Read-only and execution remain separate**: ReadOnlyAdapterCapability unchanged through 7P.
5. **No auto-trading**: All 3 entry orders had explicit human GO. 0 automated loops.
6. **HOLD / REJECT / NO-GO are success outcomes**: 4 refusals all documented as governance wins.
7. **Loss and win governed identically**: PT-003 -$0.24 handled identically to PT-001 +$1.52.
8. **Ledger + checker can validate evidence**: 30 events, 16 invariants, machine-verifiable.
9. **Paper PnL ≠ live readiness**: All PnL labeled simulated. Phase 8 tracker remains 3/10.
10. **AI context stays current**: AGENTS.md + docs/ai updated through all sub-phases.

## 5. What Was Not Proved

1. **Live trading readiness**: ❌ Not tested, not attempted.
2. **Live broker API readiness**: ❌ Futu/IB not selected, no funded account.
3. **Profitability**: ❌ Cumulative $+1.54 simulated — meaningless.
4. **Strategy**: ❌ No strategy tested. All trades were governance pipeline tests.
5. **Automation readiness**: ❌ No automated trading tested. All orders required human GO.
6. **Policy activation readiness**: ❌ No CandidateRule promoted to Policy.
7. **Long-run behavioral stability**: ❌ Only 4 unique trading sessions across < 1 day.
8. **Fee/slippage/real market impact**: ❌ Paper execution hides real execution costs.
9. **Edge case coverage**: ❌ No partial fill, rejected order, or venue outage tested.

## 6. CandidateRule Review

| CR | Description | Status |
|----|------------|--------|
| CR-7P-001 | Market-hours awareness: intake should reject after-hours trades without explicit risk acknowledgment | Advisory only |
| CR-7P-002 | Review-before-next-trade: no next paper trade until prior trade review complete | Advisory only |
| CR-7P-003 | Cancel lifecycle discipline: pending orders need review gate before expire/cancel | Advisory only |

All three: **NOT Policy. NOT RiskEngine-active. NOT live readiness evidence.**

## 7. Risk Review

| Risk | Mitigation |
|------|-----------|
| Paper/live confusion | Multi-layer guards (URL, key, capability, disclaimer). 0 incidents. |
| Paper PnL overinterpretation | All PnL labeled simulated. Phase 8 tracker requires ≥5 RTs + Stage Gate. |
| Cancel as convenience | Cancel requires receipt, human GO, reason. Tests verify no auto. |
| Ledger as authority | Schema doc: "evidence, not execution authority." Checker validates consistency only. |
| AI context drift | AGENTS.md updated at every 7P sub-phase. Fresh agent check baked into each seal. |
| Markdown sprawl | PT-001 condensed from 11 files to 1. PT-002/003/004 use single-file format. |
| Document governance gap | Addressed in §9 — next recommended pack. |

## 8. Phase 8 Readiness Decision

**Phase 8: DEFERRED.**

Reason:
- 3 completed paper round trips (target ≥5)
- No live broker selected (Futu/IB pending)
- No funded live account
- Manual live constitution not refreshed (currently DRAFT, deferred 7A-R)
- Document Governance Pack not built
- No Phase 8 Stage Gate met

Phase 8 cannot begin until these conditions change. This is not a failure — it is correct governance.

## 9. Recommended Next Major Work: Document Governance Pack

Phase 7P exposed systematic document lifecycle problems:
- PT-001 needed 11→1 file consolidation
- Paper-trades grew to 12 files before templates existed
- JSONL vs Markdown relationship needed explicit schema
- AI onboarding freshness must be maintained across sub-phases
- Future wiki/doc store needs governance before live stage

**Recommended**: Document Governance Pack — define how Ordivon governs its own knowledge
(docs, AI context, receipts, ledgers) with the same discipline applied to paper trades.

## 10. Post-7P Allowed / Forbidden

**Allowed**:
- Document Governance Pack design
- PT-004 historical reference
- Paper dogfood continuation only after explicit new phase + human GO

**Forbidden**:
- Phase 8 live trading
- Live broker write
- Auto-trading
- Policy activation
- RiskEngine active finance policy
- PT-005 without explicit new phase and human GO

## 11. New AI Context

After this Stage Summit, a fresh AI reading AGENTS.md + docs/ai must understand:
- Phase 7P is CLOSED.
- Paper dogfood was governance validation, not profitability test.
- Phase 8 is DEFERRED.
- Next recommended work is Document Governance Pack.
- No live trading, auto-trading, or Policy activation is authorized.
- CandidateRules remain advisory only.
