# Ordivon Verify — Prototype Schemas

> **Status:** Private package prototype artifacts.
> **Not yet:** Public release, stable API contract, or externally consumable package.

## What These Are

These JSON Schema files describe the minimal external shape of Ordivon Verify's
data artifacts:

| File | Describes |
|------|-----------|
| `ordivon.verify.schema.json` | External config file (`ordivon.verify.json`) |
| `trust-report.schema.json` | JSON trust report output (`--json`) |
| `verification-debt-ledger.schema.json` | Debt ledger entry (`verification-debt-ledger.jsonl`) |
| `verification-gate-manifest.schema.json` | Gate manifest (`verification-gate-manifest.json`) |
| `document-registry.schema.json` | Document registry entry (`document-registry.jsonl`) |

## Schema Version

All schemas use `schema_version: "0.1"` internally (where applicable).
The `$schema` references draft 2020-12 for structural annotation.

`schema_version` starts at `0.1` — this signals pre-stability. No backward
compatibility guarantee is implied at this stage.

## Relationship to Ordivon Native Schemas

| Aspect | Minimal External (these files) | Private Ordivon Native |
|--------|-------------------------------|----------------------|
| Scope | Usable by any external repo | Full Ordivon internal DG Pack |
| Fields | Minimal required set | Extended metadata, phase tracking, cross-references |
| Authority model | Simplified (source_of_truth / supporting) | Full Ordivon authority hierarchy |
| Debt categories | Open enumeration | Governed category taxonomy |
| Gate hardness | `hard` only | `hard` / `soft` / `advisory` |
| Document types | Open enumeration | Governed 18-type taxonomy |

These minimal schemas are **intentionally compatible subsets** of the Ordivon
native schemas. An external repo adopting these schemas can later upgrade to
a fuller governance model without schema conflict.

## Public Package Compatibility Policy

**Not finalized.** Current policy (prototype):

1. These schemas are read-only, non-executable artifacts.
2. Schema changes must not break existing fixture behavior.
3. `additionalProperties: true` is used on ledger/registry entries to allow
   gradual addition of fields.
4. `additionalProperties: false` is used on config and report schemas where
   strict field control matters for verification integrity.
5. No SemVer commitment is made until a public release is authorized.

## What These Schemas Are NOT

- They are not a public API contract.
- They are not a published package.
- They do not imply license activation.
- They do not authorize any action.
- They do not expose private Ordivon Core internals.
- They do not require full DG Pack adoption.
- They contain no broker, finance, API key, or live trading references.

## Next Steps

These schemas are read-only artifacts within the private `src/ordivon_verify/`
package prototype. Future phases may:

- Add lightweight structural validation tests
- Extract to a public wedge repo
- Evolve to stable schema_version `1.0`
- Add migration guides for external adopters
