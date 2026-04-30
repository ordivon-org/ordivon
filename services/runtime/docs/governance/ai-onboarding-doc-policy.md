# AI Onboarding Document Policy

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: DG-1
Tags: `governance`, `ai`, `onboarding`, `read-path`, `context`, `freshness`

## 1. Purpose

This document defines the required read path for any AI agent (ChatGPT, Claude,
Codex, Copilot, IDE assistant, Hermes subagent) entering the Ordivon project.

The policy ensures that fresh AI agents understand current project state without
inferring truth from archived, stale, or superseded documents.

## 2. Read Path: Leveled System

AI agents must read documents in order, by level. Higher levels are mandatory
before lower levels provide useful context.

### Level 0 — Mandatory First Read

Read first, every time, before any work begins:

```
AGENTS.md                                    ← Root entry point
```

AGENTS.md must provide:
- Project identity (what Ordivon is and is not)
- Current phase status (7P: CLOSED, 8: DEFERRED)
- Critical boundaries (NO-GO items)
- Quick navigation to deeper AI onboarding docs
- Next recommended work

### Level 1 — Required Before Any Work

Read immediately after Level 0, before any task execution:

```
docs/ai/README.md                            ← AI onboarding start
docs/ai/current-phase-boundaries.md          ← What's live, what's deferred, what's NO-GO
docs/ai/ordivon-root-context.md              ← Identity, doctrine, architecture layers
docs/ai/agent-working-rules.md               ← How to operate within governance
docs/ai/architecture-file-map.md             ← Where things live
```

These five documents form the AI context core. After reading them, any agent
should understand:
- What Ordivon is (governance OS, not a trading bot)
- Current phase state (what's active, what's deferred, what's NO-GO)
- How to operate within governance (evidence before belief, CandidateRule ≠ Policy)
- Where code lives and how imports flow
- What actions are permitted and forbidden by layer

### Level 2 — Required Before Domain-Specific Work

Read when working on a specific domain:

```
docs/governance/document-governance-pack-contract.md   ← Document governance rules
docs/governance/document-taxonomy.md                   ← Document type system
docs/product/alpaca-paper-dogfood-stage-summit-phase-7p.md  ← Phase 7P closure
docs/design/design-pack-contract.md                    ← Design governance rules
```

Also applicable:
- Pack contract for the domain being modified
- Domain architecture docs
- Relevant ADRs

### Level 3 — Contextual, As Needed

Read when the specific task requires it:

```
docs/runtime/paper-trades/paper-trade-ledger.md        ← Paper trade status
docs/runtime/paper-trades/paper-dogfood-ledger-schema.md ← Ledger schema
docs/runtime/paper-trades/phase-7p-readiness-tracker.md ← Phase 8 tracker
docs/runbooks/ordivon-agent-operating-doctrine.md      ← Full doctrine
docs/runtime/ordivon-value-philosophy.md               ← Why not a trading bot
```

Also applicable: runtime evidence docs, red-team reports, runbooks.

### Level 4 — Archive, Only When Explicitly Needed

Read ONLY when the task specifically requires historical investigation:

```
docs/runtime/paper-trades/PT-001.md                    ← Individual trade receipt
docs/runtime/paper-trades/PT-002.md
docs/runtime/paper-trades/PT-003.md
docs/runtime/paper-trades/PT-004.md
docs/runtime/archive/                                  ← Archived docs
docs/audits/                                           ← Audit reports
```

Archived documents carry `archive` authority. They are historical only.

## 3. Critical Rules for AI Agents

### 3.1 Do Not Infer Current Truth from Archived Documents

An archived receipt is evidence of what happened, not authority for what is
currently allowed. After Phase 7P closure, reading a PT-001 receipt does not
authorize PT-005. Only `current-phase-boundaries.md` defines current authority.

### 3.2 Do Not Treat Any Document as Current Without Verifying Status

Every governed document carries a `Status:` header. If absent, treat the
document as `draft` (no authority). If present, respect the status.

### 3.3 Do Not Treat CandidateRule Docs as Policy

Documents describing CandidateRules carry "advisory only — NOT Policy" labels.
A CandidateRule document with status `advisory` is not a Policy document.

### 3.4 Do Not Treat Paper PnL as Live Readiness

Documents containing simulated paper PnL are NOT evidence of live trading
readiness. Phase 8 readiness requires explicit Stage Gate, not paper PnL.

### 3.5 Do Not Treat JSONL Ledger as Execution Authority

The JSONL ledger is machine-readable evidence, checked for consistency. It is
NOT authorization to place orders. New AI agents must not read ledger events
and conclude "trading is active."

### 3.6 Report Stale or Conflicting Documents

If an AI agent discovers a document whose status conflicts with its contents
(e.g., a `current`-status document referencing a deferred phase as active, or a
document missing status entirely), it should flag this rather than silently
accepting the contradiction.

### 3.7 Respect Immutable Receipts

Receipts are append-only and immutable. Do not edit them. Do not delete them.
Do not change their status. If consolidation is needed, follow the 11→1 pattern
(condense multiple files into one while preserving content).

## 4. Fresh AI Context Verification

After each phase transition or significant event, run the New AI Context Check:

1. Simulate a fresh AI reading AGENTS.md → docs/ai/README.md → docs/ai/current-phase-boundaries.md
2. Verify the agent would understand:
   - Current phase status (what's active, closed, deferred)
   - Critical boundaries (NO-GO items)
   - What work is authorized
   - What work is deferred or forbidden
   - Where to find deeper context if needed
3. If any of these would be misunderstood, update the onboarding docs.

The Phase 7P Stage Summit requires this check to be performed and recorded.

## 5. Onboarding Doc Maintenance

### 5.1 When to Update Root AI Context

| Trigger | Update |
|---------|--------|
| Phase state changes (open/close/defer) | `AGENTS.md`, `docs/ai/current-phase-boundaries.md` |
| New critical boundary established | `AGENTS.md`, `docs/ai/current-phase-boundaries.md` |
| Architecture structure changes | `docs/ai/architecture-file-map.md` |
| Governance doctrine changes | `docs/ai/ordivon-root-context.md`, `docs/ai/agent-working-rules.md` |
| New AI onboarding policy (this doc) changes | `docs/ai/README.md` |
| New pack contract published | `AGENTS.md` quick navigation, `docs/ai/README.md` |

### 5.2 Update Cadence

Root AI context files (`AGENTS.md`, `docs/ai/`) must be updated within 1 session
of any phase state change. This is the single highest-priority documentation
maintenance task.

### 5.3 Ownership

Project lead owns root AI context freshness. The lead may delegate maintenance
to an AI agent (e.g., Hermes) but remains accountable for correctness.

## 6. Relationship to Document Governance Pack

This policy is part of the Document Governance Pack. It is governed by the same
lifecycle, taxonomy, and authority rules it defines. This recursive governance
is intentional: the Document Governance Pack governs itself.

As a `governance_pack`-type document, this file carries `current_status` authority
once accepted, and must be kept fresh (≤30 days).

## 7. Future Enhancements

- Automated freshness checker for root AI context files
- AI agent self-check at session start: "Do my context files match current truth?"
- GitHub Actions check: flag PRs that change code without updating corresponding AI context
- Wiki-delivered AI onboarding: interactive read path with status indicators
