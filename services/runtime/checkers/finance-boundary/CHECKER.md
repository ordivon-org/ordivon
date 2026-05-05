---
gate_id: finance_boundary
display_name: Finance Boundary Enforcement
layer: L5A
hardness: hard
purpose: Detect live trading references in docs/code — Phase 8 DEFERRED, live trading NO-GO
protects_against: "Live trading language, broker write references, Phase 8 premature activation, live order claims"
profiles: ['full']
timeout: 60
tags: [finance, boundary, no-go, live-trading]
---

# Finance Boundary Checker

## Purpose

Enforces the Phase 8 DEFERRED boundary: no live trading language should
appear in documentation, architecture, or governance files. Detects
dangerous phrases that suggest live trading capability or intent.

## Protects Against

- "live trading" references outside of explicit NO-GO/DEFERRED context
- "live order" / "place_live_order" claims
- Phase 8 readiness claims without "DEFERRED" qualifier
- Broker write API references without "NO-GO" qualifier

## Design

Scans docs/ and AGENTS.md for dangerous phrases. Uses safe context
detection: if a phrase appears WITHIN a NO-GO/DEFERRED/BLOCKED statement,
it's allowed. If it appears WITHOUT negation, it's a violation.
