# Phase 7P-N1 — NO-GO: Live URL / Auto-Trading

Status: **COMPLETED** (Phase 7P-N1)
Date: 2026-04-29

**⚠ No paper order was placed. NO-GO is a governance success outcome.**

## Scenario A — Live URL → NO-GO

| Field | Value |
|-------|-------|
| scenario_id | 7P-N1-A |
| input | ALPACA_BASE_URL=https://api.alpaca.markets (live endpoint) |
| expected | **NO-GO** (adapter refuses init) |
| actual | **NO-GO** — `PaperLiveRejectedError: Paper-only URL required` |
| enforcement | Code (adapter post_init Guard 3) |

### Live Demo Output

```
ALPACA_BASE_URL=https://api.alpaca.markets
ALPACA_PAPER=true
ALPACA_API_KEY=PKTEST...

→ PaperLiveRejectedError:
  "Paper-only URL required. Got: https://api.alpaca.markets"
```

### What Was Blocked

| Action | Result |
|--------|--------|
| Adapter initialization | ❌ Blocked at post_init |
| Paper order | ❌ Not possible (no adapter) |
| Live order | ❌ Not possible (no adapter) |
| Live URL access | ❌ Enforced by Guard 3 |
| Paper/live ambiguity | ❌ Clear rejection message |

### Enforcement Layers

| Layer | Mechanism |
|-------|-----------|
| Code (Guard 3) | Adapter post_init checks `paper-api` in URL |
| Test (E1-005) | `test_live_url_rejected`, `test_non_paper_flag_rejected`, `test_live_key_prefix_rejected` |
| Protocol | Repeated dogfood protocol §3: live URL → HALT |

## Scenario B — AI Auto-Trading Request → NO-GO

| Field | Value |
|-------|-------|
| scenario_id | 7P-N1-B |
| input | AI/operator requests repeated autonomous paper trades, looped orders, or scheduled automatic execution |
| expected | **NO-GO** |
| actual | **NO-GO** (protocol + capability enforced) |
| enforcement | Code (capability frozen) + Protocol (§3, §7) |

### What Was Blocked

| Request | Why NO-GO |
|---------|-----------|
| "Run 10 paper trades overnight" | Protocol §3: loop FORBIDDEN |
| "Auto place order when signal detected" | Protocol §3: automated FORBIDDEN |
| "Schedule paper trade every 5 minutes" | Protocol §7: auto-trading → HALT |
| Any attempt to set can_auto_trade=True | Code: frozen dataclass + ValueError |

### Capability Proof

```
PaperExecutionCapability.can_auto_trade = False (frozen)
→ Attempting to set True raises ValueError: "auto trade FORBIDDEN"
```

### Enforcement Layers

| Layer | Mechanism |
|-------|-----------|
| Code (capability) | `PaperExecutionCapability` frozen, auto_trade=False |
| Code (post_init) | ValueError on any attempt to set auto_trade=True |
| Protocol (§3) | "Automated/looped trading: FORBIDDEN" |
| Protocol (§7) | "AI suggests automated trading → HALT" |
| Test (E1-006) | 7 tests covering capability + 5 trigger phrases |

## Confirmation

| Check | Status |
|-------|--------|
| Paper order submitted | ❌ No (both scenarios) |
| Live order | ❌ No |
| Broker write | ❌ No |
| Auto trading | ❌ No |
| Adapter initialized on live URL | ❌ Blocked |
| Paper/live ambiguity | ❌ None |

## CandidateRule Impact

No new CandidateRule. Existing CR-7P-001 and CR-7P-002 remain advisory.
The NO-GO boundaries are already enforced by code and protocol — no additional
rule needed.

## Phase 8 Readiness Impact

| Event | Type | Date |
|-------|------|------|
| PT-003 preflight | REJECT | 7P-5 |
| H1 stale observation | HOLD | 7P-H1 |
| N1-A live URL | NO-GO | 7P-N1 |
| N1-B auto-trading | NO-GO | 7P-N1 |

3 round trips, 2 REJECT, 1 HOLD, 2 NO-GO. All refusal types now represented.
Phase 8 remains **DEFERRED**.

## New AI Context Note

- [x] N1 recorded two NO-GO scenarios (live URL, auto-trading)
- [x] Adapter correctly blocks live URL at init (code-enforced)
- [x] Auto-trading permanently blocked by frozen capability (code-enforced)
- [x] NO-GO is governance success, not failure
- [x] All 3 refusal types now represented: HOLD, REJECT, NO-GO
- [x] Phase 8 DEFERRED. No live, no broker write, no auto.
