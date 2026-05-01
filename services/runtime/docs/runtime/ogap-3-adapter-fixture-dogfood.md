# OGAP-3 — Adapter Fixture Dogfood

## Purpose

Prove OGAP v0 can represent and validate realistic external adapter
scenarios: AI coding agents, MCP servers, CI merge gates, IDE agents,
enterprise platforms, and financial action requests.

## Scenario Inventory

| Scenario | Payloads | Decision |
|---|---|---|
| AI coding agent | WorkClaim + GovernanceDecision | READY |
| MCP server | CapabilityManifest + GovernanceDecision | DEGRADED |
| CI merge gate | WorkClaim + GovernanceDecision | BLOCKED |
| IDE agent | WorkClaim | (READY requested, debt declared) |
| Enterprise agent platform | TrustReport | READY (human review required) |
| Financial action request | WorkClaim + GovernanceDecision | NO-GO |

All 10 payloads validate cleanly through `validate_ogap_payload.py`.

## Key Semantic Verifications

- AI coding READY: "not authorization" in authority statement ✅
- MCP capability: can_X ≠ may_X via authority_note ✅
- CI BLOCKED: hard_failures present, claim contradicts evidence ✅
- IDE: debt declaration with known gaps ✅
- Enterprise: human_review_required=true, trust report with coverage ✅
- Financial: NO-GO, no broker credentials, Phase 8 DEFERRED referenced ✅

## What OGAP-3 Proves

1. OGAP payloads can express 6 realistic external adapter scenarios.
2. Decision semantics (READY/DEGRADED/BLOCKED/NO-GO) map correctly.
3. Capability/authority separation is testable.
4. Financial actions correctly default to NO-GO.

## What OGAP-3 Does NOT Prove

- That any real external system integrates OGAP.
- That schemas cover every adapter edge case.
- That a runtime implementation could enforce these decisions.

## Boundary Confirmation

- Fixture dogfood only. No API/MCP/SDK/public standard.
- Phase 8 DEFERRED. Financial actions remain NO-GO.

---

*Closed: 2026-05-01*
*Phase: OGAP-3*
