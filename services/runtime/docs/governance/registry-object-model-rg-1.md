# Registry Object Model — RG-1

**Phase:** RG-1 — Unified Registry Object Model
**Status:** IMPLEMENTED
**Date:** 2026-05-09
**Authority:** current_status (design specification)

## Purpose

Define the unified object model for Ordivon's future Registry Control Plane. This model bridges Document Registry, Artifact Registry, Checker Registry, Scanner surfaces, Auxiliary ledgers, Ownership rules, Policy activations, and Legacy scope declarations into a single canonical representation.

**RG-1 is model-only.** It does not fix RG-0 debts, does not create missing files, does not register pending docs, and does not change existing registry behavior. Old registries remain authoritative sources during RG-1.

## Architecture

```
RegistryObject (dataclass, frozen)
    ├── Identity:     registry_id, kind, path, title
    ├── Authority:    authority_tier, lifecycle_state, current_truth_allowed
    ├── Ownership:    owner, reviewer, approver
    ├── Provenance:   source_registry, discovered_by, registered_by
    ├── Generation:   generated, generated_from
    ├── Metadata:     content_hash, scope, project_id
    ├── Relations:    depends_on, supersedes, superseded_by
    ├── Freshness:    last_verified, review_date, ttl_days
    ├── Governance:   policy_refs, evidence_refs, receipt_refs
    └── Notes:        notes

RegistryFinding (dataclass, frozen)
    ├── finding_id, object_id, status, invariant, message
    └── repair_action

Invariant Validators (9, stateless, side-effect-free)
    ├── active-t0-requires-owner
    ├── generated-not-source-truth
    ├── current-truth-allowed-restricted
    ├── legacy-scope-requires-legacy-lifecycle
    ├── generated-requires-generated-from
    ├── tombstone-requires-reason
    ├── config-surface-not-current-truth
    ├── archive-snapshot-not-current-truth
    └── policy-activation-requires-target
```

## RegistryKind Taxonomy

| Kind | What it represents | Example |
|---|---|---|
| `document` | A governed document | AGENTS.md, phase-boundaries |
| `artifact` | Source code, test, script, fixture | src/ordivon_verify/runner.py |
| `checker` | A governance checker | checkers/document-registry/ |
| `scanner_surface` | Agent-native evidence surface | ~/.hermes/skills/ordivon-verify/SKILL.md |
| `ledger` | A JSONL data ledger | verification-debt-ledger.jsonl |
| `schema` | A JSON/YAML schema | document-registry.schema.json |
| `config_surface` | A project configuration file | pyproject.toml |
| `generated_view` | Machine-generated index/manifest | verification-gate-manifest.json |
| `ownership_rule` | A path ownership pattern | ownership-manifest.jsonl entry |
| `policy_activation` | CandidateRule-to-Policy bridge | policy-activation-ledger.jsonl entry |
| `legacy_scope` | Legacy directory scope declaration | apps/ directory identity |
| `archive_snapshot` | Archived state snapshot | docs/archive/ snapshot |
| `ai_handoff_packet` | Cross-agent context handoff | onboarding-snapshot.json |

## Authority Tiers (extended from metabolic)

| Tier | Meaning | current_truth_allowed default |
|---|---|---|
| T0_SOURCE_OF_TRUTH | Canonical truth | Yes |
| T1_CURRENT_STATUS | Current operational truth | Yes |
| T2_SUPPORTING_EVIDENCE | Corroborating evidence | No |
| T3_CANDIDATE_PROPOSAL | Proposed, not yet authoritative | No |
| T4_ARCHIVE_HISTORICAL | Historical record | No |
| T5_DEPRECATED_TOMBSTONED | Decommissioned | No |
| T6_OUT_OF_SCOPE | Explicitly outside current scope | No |

T6 is new — it gives legacy surfaces a formal identity instead of being silently ungoverned.

## Lifecycle States (extended from metabolic)

| State | Meaning | In ACTIVE set? |
|---|---|---|
| `draft` | Being written | No |
| `candidate` | Under review | Yes (may carry ownership requirements) |
| `active` | Current, maintained | Yes |
| `stable` | Mature, rarely changes | Yes |
| `generated` | Machine-produced | No |
| `archived` | Preserved for reference | No |
| `legacy_inactive` | Known pre-Ordivon surface, inactive | No |
| `deprecated` | Approaching tombstone | No |
| `tombstoned` | Decommissioned with reason | No |
| `out_of_scope` | Explicitly excluded | No |

Three states are new: `generated` (for machine-produced artifacts), `legacy_inactive` (for PFIOS/AegisOS legacy directories), and `out_of_scope` (for explicitly excluded surfaces).

## Key Design Decisions

1. **Model-only phase.** No RG-0 debt is fixed in RG-1. This is the abstraction layer that RG-2 import adapters and RG-3 reconciler will use.

2. **Separate from metabolic.** The metabolic `ArtifactRecord` and `AuthorityTier` remain unchanged. The registry-plane `AuthorityTier` extends with T6_OUT_OF_SCOPE. The planes coexist. RG-2 adapters will bridge them.

3. **Frozen dataclasses.** RegistryObject and RegistryFinding are frozen. Invariant validators are stateless functions that return findings, never mutate objects. This keeps the model deterministic and testable.

4. **Override via notes convention.** The "generated-as-truth" and "current-truth-override" note keywords let edge cases bypass invariants with explicit justification. This avoids an `override_reason: str | None` field while still requiring intent.

5. **Tuple fields for immutability.** depends_on, supersedes, generated_from, policy_refs, evidence_refs, receipt_refs are tuples — immutable by construction.

## What RG-1 Does NOT Do

- Does not create policy-activation-ledger.jsonl
- Does not register 156 pending docs
- Does not fix 9 L0/L1 owner gaps
- Does not give 28 legacy dirs formal identity (model supports it, but RG-2/RG-5 will execute)
- Does not alter document-registry.jsonl (except adding this doc and RG-1 artifacts per existing governance)
- Does not alter artifact-registry.jsonl (except adding new RG-1 files per existing governance)
- Does not modify checker behavior
- Does not delete legacy checker scripts
- Does not introduce SQLite/HTML/dashboard
- Does not change authorization semantics

## Validation

```
Product tests: 59 passed
ruff check:    PASS
ruff format:   PASS
compileall:    PASS
current-truth: PASS
document-registry: PASS (RG-0-only pre-existing: ctts-3m-stage-summit unregistered)
```

## Files

```
src/ordivon_verify/registry/__init__.py
src/ordivon_verify/registry/models.py
src/ordivon_verify/schemas/registry-object.schema.json
tests/unit/product/test_ordivon_verify_registry_object_model.py
docs/governance/registry-object-model-rg-1.md
```

## Next: RG-2 — Import Adapters

RG-2 will write adapters that convert existing registry rows into RegistryObject instances:

- `import_document_registry()` → RegistryObject list
- `import_artifact_registry()` → RegistryObject list
- `import_checker_registry()` → RegistryObject list
- `import_aux_ledgers()` → RegistryObject list
- `import_scanner_surfaces()` → RegistryObject list
