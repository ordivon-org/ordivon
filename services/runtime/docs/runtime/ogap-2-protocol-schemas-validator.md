# OGAP-2 — Protocol Schemas + Payload Validator

## Purpose

Turn OGAP-1 protocol examples into machine-validated draft JSON Schemas
and a local validator, so external systems can produce OGAP payloads
that Ordivon can validate structurally.

## Why OGAP-2 Follows OGAP-1

OGAP-1 defined protocol semantics — humans can read and understand.
OGAP-2 adds machine-checkable structure — validators can reject bad
payloads before any API/MCP/SDK exists.

## Schemas Added

| Schema | Required Fields | Notes |
|---|---|---|
| ogap-work-claim | 9 | evidence_bundle, coverage_report, debt_declaration required |
| ogap-governance-decision | 6 | Decision enum: READY/DEGRADED/BLOCKED/HOLD/REJECT/NO-GO |
| ogap-capability-manifest | 8 | Capabilities + no_go_actions + authority_required_for |
| ogap-coverage-report | 7 | claimed_universe, discovery_method, pass_scope_statement |
| ogap-trust-report | 9 | decision, evidence_summary, debt_summary, warnings |

All schemas: draft 2020-12, v0 prototype, `additionalProperties: true`,
explicit `_disclaimer` / `_maturity` metadata.

## Validator Behavior

`scripts/validate_ogap_payload.py`:
- Infers object type from payload shape (or accepts `--schema`)
- Validates required fields against JSON Schema
- Validates enum values (decision, adapter trust)
- Safety checks:
  - READY + "authorizes execution" → fails
  - READY + "authorizes deployment" → fails
  - CapabilityManifest without authority_note → fails
- Supports `--json` output
- Exits 0 on valid, nonzero on invalid

## Validation Results

All 5 OGAP-1 examples validate:
- work-claim-basic.json ✅
- governance-decision-ready.json ✅
- governance-decision-blocked.json ✅
- capability-manifest-basic.json ✅
- coverage-report-basic.json ✅

## What OGAP-2 Proves

1. OGAP payloads can be structurally validated without runtime.
2. READY-authorizes-execution language is machine-detectable.
3. Capability/manifest without authority disclaimers is machine-detectable.
4. Schemas provide a target for external adapter authors.

## What OGAP-2 Does NOT Prove

- That schemas cover all edge cases (prototype).
- That schemas validate semantic correctness (only structural + safety).
- That any real external system produces these payloads.

## Boundary Confirmation

- Schemas + validator only. No live API. No MCP server. No SDK.
- No public standard. No package publish. No license activation.
- Phase 8 DEFERRED. All NO-GO intact.

---

*Closed: 2026-05-01*
*Phase: OGAP-2*
