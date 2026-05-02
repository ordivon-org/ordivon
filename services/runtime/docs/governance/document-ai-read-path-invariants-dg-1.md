# AI Read Path Invariants (DG-1)

Status: **current** | Date: 2026-05-02 | Phase: DG-1
Tags: `dg-1`, `ai-read-path`, `invariants`, `onboarding`, `freshness`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This document defines the invariants that the AI read path must satisfy
for any fresh AI agent entering the Ordivon project. These invariants are
enforced by ADP-3 registry checks, New AI Context Checks, and the document
governance system.

## L0 — Mandatory First Read

**AGENTS.md** is the single L0 document. It must:

1. State project identity (what Ordivon is and is not).
2. List current phase status for all phases (CLOSED / ACTIVE / DEFERRED).
3. List critical NO-GO boundaries.
4. Provide quick navigation to L1 docs.
5. State pr-fast gate status.
6. State open debt that affects the next phase.
7. State that detector PASS is not authorization.
8. State that absence of findings is not safety proof.
9. State that public wedge is not public release.
10. Be updated within 1 session of any phase state change.

**Freshness**: last_verified ≤ 7 days, stale_after_days = 7.

## L1 — Required Before Any Work

L1 documents must be read immediately after AGENTS.md, before any task execution:

1. `docs/ai/README.md` — Onboarding index, read-order guide.
2. `docs/ai/current-phase-boundaries.md` — What's live, deferred, NO-GO.
3. `docs/ai/ordivon-root-context.md` — Identity, doctrine, architecture layers.
4. `docs/ai/agent-working-rules.md` — How to operate within governance.
5. `docs/ai/architecture-file-map.md` — Where things live.

**Freshness**: All L1 docs require `last_verified` and `stale_after_days`.

## L2 — Required Before Domain-Specific Work

L2 documents must be read when working on a specific domain:

Active governance pack docs, stage summits for current phases, product notes,
architecture docs, external benchmark reading guides.

**Freshness**: L2 docs strongly recommended to have `last_verified`.

## L3 — Contextual, As Needed

Runtime evidence docs, individual receipts, ledgers, trackers.

**Freshness**: Dated at creation; archival after phase closure.

## L4 — Archive, Only When Explicitly Needed

Archived docs, superseded docs, historical records.

**Invariant**: L4 docs must never appear in L0/L1 current guidance.

## Invariants Enforced by ADP-3

The ADP-3 detector enforces these invariants via registry checks:

| Rule | Invariant |
|------|-----------|
| ADP3-DG-AI-STALE | L0/L1 docs must not be superseded or archived |
| ADP3-DG-STALENESS | L0/L1 docs must have freshness metadata |
| ADP3-DG-SUPERSEDED | Current docs must not have superseded_by |
| ADP3-DG-DEGRADED-LIFECYCLE | DEGRADED docs must have lifecycle fields |

## New AI Context Check

After every phase transition, the New AI Context Check must verify:

1. A fresh AI reading AGENTS.md → L1 docs would understand current phase state.
2. A fresh AI would know what is allowed, deferred, and NO-GO.
3. A fresh AI would know that detector PASS is not authorization.
4. A fresh AI would know that no findings is not safety proof.
5. A fresh AI would know that public wedge is not public release.
6. A fresh AI would know what open debt exists.
7. A fresh AI would know what the next recommended phase is.
