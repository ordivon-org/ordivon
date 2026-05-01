# PV-N2 — Schema Extraction

## Purpose

PV-N2 extracts explicit, versioned JSON Schema artifacts for Ordivon Verify's data
shapes inside the private package prototype. These schemas are the first step
toward a public-facing contract without exposing private Ordivon Core.

## What Changed

Five new JSON Schema files created in `src/ordivon_verify/schemas/`:

| File | Describes |
|------|-----------|
| `ordivon.verify.schema.json` | External config (`ordivon.verify.json`) |
| `trust-report.schema.json` | JSON trust report output (`--json`) |
| `verification-debt-ledger.schema.json` | Debt ledger entry (`.jsonl`) |
| `verification-gate-manifest.schema.json` | Gate manifest (`.json`) |
| `document-registry.schema.json` | Document registry entry (`.jsonl`) |

All schemas:
- Use `$schema: draft/2020-12` for structural annotation
- Carry `schema_version: "0.1"` — pre-stability signal
- Are intentionally minimal: only required fields for external adoption
- Use `additionalProperties: true` on ledger/registry entries for gradual addition
- Use `additionalProperties: false` on config/report for verification integrity

## Schema Design Decisions

### Minimal External ≠ Native Ordivon

External schemas omit fields that only Ordivon native DG Pack uses:
- Extended metadata (phase tracking, cross-references)
- Full authority hierarchy
- Governed 18-type document taxonomy
- Soft/advisory gate types

An external repo can upgrade without schema conflict — the minimal schemas are
compatible subsets.

### Disclaimer Immutability

The trust report schema enforces `"const"` on the disclaimer field:
`"READY means selected checks passed; it does not authorize execution."`

This prevents any tool or person from accidentally weakening the core semantic.

### Gate Manifest No-Op Restriction

The gate manifest schema requires that `command` fields are not no-ops. This is
documented in the schema description, enforced by the existing `check_verification_manifest.py`.

## Private Reference Scan

A grep for (`Alpaca|broker|live trading|Phase 7P|RiskEngine|Policy|/root/projects|API_KEY|SECRET|TOKEN`)
across all schema files found zero matches. The only hits were in `schemas/README.md`
stating "They contain no broker, finance, API key, or live trading references" —
a boundary statement, not a leak.

## Tests

`tests/unit/product/test_ordivon_verify_schemas.py` — 29 tests:
- All 5 schema files exist and are valid JSON
- `schema_version` field present in config and report schemas
- External fixture configs conform structurally
- Trust report required fields + status enum + disclaimer immutability
- Gate manifest no-op restriction documented
- Debt ledger + document registry schemas are permissive (`additionalProperties: true`)
- No private references in any schema file
- External config schema does not require heavy DG Pack fields
- Schema tests are read-only (prove mtimes unchanged)

## Behavior Preservation

All fixture modes preserved identically:
- Native READY
- Standard external READY
- Clean advisory DEGRADED
- Bad external BLOCKED

## What PV-N2 Proves

1. Ordivon Verify's data shapes are cleanly extractable into JSON Schema.
2. Minimal external schemas differ from private Ordivon native schemas by design.
3. No private/broker/finance references leak into schema artifacts.
4. Schema files are harmless static artifacts — no new imports, no runtime overhead.
5. Lightweight structural validation works without any new dependencies.

## What PV-N2 Does NOT Prove

1. Schemas are NOT a public release.
2. Schemas do NOT enable external consumption yet.
3. No migration guides for external adopters exist.
4. No `schema_version 1.0` commitment.
5. Not all possible edge cases are covered — enumerations are intentionally open.

## Boundary Confirmation

- Schema extraction only
- Private package prototype only
- No public release, no public repo, no license activation
- No package publishing, no CI change, no SaaS, no MCP server
- No broker/API, no paper/live order, no Policy/RiskEngine activation
- Schemas are prototype artifacts, not public contract
- READY does not authorize execution
- Phase 8 remains DEFERRED

## Next Recommended Phase

PV-N3: Public Quickstart — write a public-facing quickstart doc that uses only
the public schemas and fixtures, validating the wedge boundary without
opening the repo.

---

*Closed: 2026-05-01*
*Phase: PV-N2*
*Task type: code/docs implementation / private package hardening*
*Risk level: R0/R1 read-only local tooling*
