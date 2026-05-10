# Registry Reality Freeze — RG-0 Baseline

**Phase:** RG-0 — Registry Control Plane Kickoff
**Status:** BASELINE FROZEN
**Date:** 2026-05-08
**Authority:** supporting_evidence
**Doc Type:** runtime / audit

## Purpose

Freeze the current state of Ordivon's registry system — not to fix anything, but to establish a measured truth baseline before the Registry Control Plane refactoring (RG-1 through RG-9).

This document records what exists, what classes of registry artifacts are present, and what cross-registry coherence gaps exist as of this date.

## Executive Summary

Ordivon has **5 distinct registry layers** with separate semantics, schemas, discoverers, and checkers. The layers interoperate only through human convention, not through a unified object model. This document identifies **89 classified artifacts** across 16 categories and **33 cross-registry coherence gaps** (13 BLOCKED, 20 DEGRADED).

The refactoring target is: one Registry Control Plane with a unified object model, multiple source adapters, one reconciler, generated views, and explicit lifecycle/authority/ownership/provenance for every governed object.

---

## 1. Registry Artifact Inventory

### 1.1 Registry Sources (4 artifacts)

| Artifact | Path | Classification |
|---|---|---|
| Document Registry | docs/governance/document-registry.jsonl | registry_source (244 entries) |
| Artifact Registry | docs/governance/artifact-registry.jsonl | registry_source (705 entries) |
| Document Exclusions | docs/governance/document-registry-exclusions.json | registry_source (161 entries) |
| Document Registry Schema | src/ordivon_verify/schemas/document-registry.schema.json | registry_source_schema |

### 1.2 Checker Ecosystem (38 packages + 2 sidecars)

| Artifact | Path | Classification |
|---|---|---|
| Checker Packages | checkers/*/ (38 dirs) | checker_package (self-registering via CHECKER.md) |
| Bundled Manifest | checkers/.bundled_manifest | checker_sidecar_state |
| Usage Telemetry | checkers/.usage.json | checker_sidecar_telemetry |
| Curator State | checkers/.curator_state | ***MISSING*** |

All 38 checker packages have CHECKER.md + run.py. Covered by checker-maturity-ledger (38 entries) and checker registry auto-discovery.

### 1.3 Auxiliary Ledgers (13 files, 3 missing)

| Ledger | Entries | Classification | Status |
|---|---|---|---|
| verification-debt-ledger.jsonl | 8 | aux_manual_ledger | PRESENT |
| checker-maturity-ledger.jsonl | 38 | aux_manual_ledger | PRESENT |
| policy-activation-ledger.jsonl | 0 | aux_manual_ledger | ***MISSING*** |
| candidate-rule-drafts.jsonl | 2 | aux_extracted_ledger | PRESENT |
| lesson-ledger.jsonl | 5 | aux_extracted_ledger | PRESENT |
| shadow-evaluation-log.jsonl | 502 | aux_generated_ledger | PRESENT |
| entropy-telemetry.jsonl | 247 | aux_generated_ledger | PRESENT |
| agent-native-evidence-redteam.jsonl | 9 | aux_manual_ledger | PRESENT |
| ownership-manifest.jsonl | 10 | aux_source_ledger | PRESENT |
| external-benchmark-source-registry.jsonl | 16 | aux_source_ledger | PRESENT |
| lesson-extraction-log.jsonl | 2 | aux_generated_ledger | PRESENT |
| release-claim-map.jsonl | 0 | aux_source_ledger | ***MISSING*** |
| tool-boundary-map.jsonl | 0 | aux_source_ledger | ***MISSING*** |

### 1.4 Generated Manifests (2 files)

| Artifact | Path | Classification |
|---|---|---|
| Verification Gate Manifest | docs/governance/verification-gate-manifest.json | generated_view |
| Checker Coverage Manifest | docs/governance/checker-coverage-manifest.json | generated_view |

### 1.5 Control Modules (16 files)

- `src/ordivon_verify/checker_registry.py` (747 lines) — canonical checker discovery
- `src/ordivon_verify/registry.py` (190 lines) — DEPRECATED legacy checker registry
- `src/ordivon_verify/discovery.py` (1556 lines) — evidence discovery + report generation
- `src/ordivon_verify/report.py` (515 lines) — trust report rendering
- `src/ordivon_verify/runner.py` (311 lines) — checker execution
- `src/ordivon_verify/cli.py` (415 lines) — CLI entry point
- `src/ordivon_verify/config.py` (97 lines) — config loading
- Metabolic: `registry.py`, `models.py`, `discover.py` (409 lines total)
- Scanners: `skill_boundary.py`, `memory_hygiene.py`, `trace_evidence.py` (975 lines total)
- 18 JSON schemas under `src/ordivon_verify/schemas/`

### 1.6 Legacy Deprecated Checkers (18 scripts)

All `scripts/check_*.py` files are deprecated legacy checkers. They persist for historical reference and backward compatibility. Superseded by `checkers/<gate_id>/run.py` packages.

### 1.7 Runners (3 scripts)

- `scripts/run_baseline.py` — runs all checkers via auto-discovery
- `scripts/ordivon_reconcile.py` — governance reconciliation + receipt generation
- `scripts/run_stage.py` — interactive stage execution

### 1.8 Config Surfaces (6 files, all unregistered)

`pyproject.toml`, `package.json`, `pnpm-workspace.yaml`, `docker-compose.yml`, `Makefile`, `.env.example`

No formal registration. Identity-checked by document-registry checker for PFIOS legacy markers, but not classified by kind/authority/lifecycle.

### 1.9 Domain Models (2 files)

`domains/policies/models.py` (215 lines), `domains/policies/shadow.py` (329 lines)

These are domain-aware objects (PolicyRecord, PolicyShadowEvaluator). Used by the policy-shadow checker. Operate at object level, not file level.

### 1.10 Document Directories Outside Scope (10 dirs, ~60 files)

`docs/audits/` (13), `docs/runbooks/` (12), `docs/design/` (11), `docs/decisions/` (6), `docs/plans/` (6), `docs/adr/` (1), `docs/tasks/` (3), `docs/workflows/` (2), `docs/roadmap/` (2), `docs/schemas/` (1)

Not in DISCOVERABLE_DIRS. Not in document-registry. No formal identity.

### 1.11 Legacy Scope Directories (28 dirs)

`apps/` (531 files), `capabilities/` (104), `governance_engine/` (73), `orchestrator/` (68), `state/` (72), `intelligence/` (54), `knowledge/` (95), `tools/` (26), `infra/` (41), `adapters/` (34), `packs/` (46), `execution/` (29), `workflows/`, `policies/`, `prompts/`, `shared/` (52), `services/`, `alembic/`, `data/` (37), `db/`, `scratch/`, `wiki/`, `build/` (167), `dist/`, `evals/`, `knowledge_state/`, `skills/`, `stage-templates/` (2)

Primarily PFIOS/AegisOS legacy code. No `lifecycle_state = legacy_inactive` identity. No formal scope declaration. Distinction from active code is purely social knowledge.

---

## 2. Cross-Registry Coherence Gaps

### 2.1 BLOCKED (13 gaps)

#### Referenced-but-missing (4)

`policy-activation-ledger.jsonl` is referenced by 4 active documents but the file does not exist:

1. **AGENTS.md** — lists it in the Extension & Governance Systems section
2. **docs/governance/extension-processes.md** — references it in policy activation flow
3. **checkers/owner-activation/CHECKER.md** — validates against it
4. **docs/ai/systems-reference.md** — cross-references it

Impact: owner-activation checker validates against a non-existent ledger. Policy activation loop cannot close.

#### Critical L0/L1 documents without owner (9)

These documents have `authority = source_of_truth` or `current_status`, `doc_layer = L0/L1`, and `owner = null`:

| Doc ID | Path | Layer | Authority |
|---|---|---|---|
| agents-md | AGENTS.md | L0 | source_of_truth |
| ai-readme | docs/ai/README.md | L0 | source_of_truth |
| phase-boundaries | docs/ai/current-phase-boundaries.md | L1 | current_status |
| agent-output-contract | docs/ai/agent-output-contract.md | L1 | current_status |
| phase-8-tracker | docs/runtime/paper-trades/phase-7p-readiness-tracker.md | L1 | current_status |
| ordivon-root-context | docs/ai/ordivon-root-context.md | L0 | source_of_truth |
| agent-working-rules | docs/ai/agent-working-rules.md | L1 | current_status |
| architecture-file-map | docs/ai/architecture-file-map.md | L1 | current_status |
| ai-collaborator-guide | docs/ai/new-ai-collaborator-guide.md | L1 | current_status |

Impact: owner is needed for freshness resolution, review authority, and policy activation. Without owner, there is no accountable party for stale-truth findings.

### 2.2 DEGRADED (20 gaps)

#### Ledger files without artifact identity (11)

All JSONL ledgers in `docs/governance/` are in document-registry but not in artifact-registry (which only covers `tests/`, `scripts/`, `domains/`, `src/`). This is a scope limitation, not a true gap. However, artifact-registry is the only place that tracks `artifact_class`, `artifact_criticality`, and `artifact_layer` for non-document files. These ledgers have no classification.

Affected: verification-debt-ledger, paper-dogfood-ledger, philosophical-governance-gap-ledger, lesson-ledger, candidate-rule-drafts, entropy-telemetry, checker-maturity-ledger, artifact-registry itself, external-benchmark-source-registry, ownership-manifest, egb3-operating-governance-redteam.

#### Schema files without artifact identity (4)

JSON schema files are in doc-registry (as `doc_type = schema`) but outside artifact-registry scope. Their `artifact_class` (should be `source_schema`), `artifact_criticality` (should be `governance_critical`), and `artifact_layer` (should be `L3_CANON`) are unrecorded.

#### Registry self-registration gaps (3)

1. `artifact-registry.jsonl` is NOT registered in artifact-registry (it's in docs/governance/, outside governed dirs)
2. `document-registry.jsonl` is registered in document-registry (line 243), OK
3. `document-registry-exclusions.json` is NOT registered in document-registry

#### Generated manifest authority mismatch (1)

`docs/governance/checker-coverage-manifest.json` is a generated view but registered with `authority = source_of_truth`. Generated views should have `authority = supporting_evidence` or `derived_from_registry`.

#### Ledger field completeness (1)

`external-benchmark-source-registry.jsonl` entries lack `source_type` and `external_framework` fields — all 16 entries show `type=? framework=?`.

---

## 3. Coverage Summary

| Surface | Registered | Discovered | Gap |
|---|---|---|---|
| Active docs (.md in 5 discoverable dirs) | 244 | 360 | 156 pending_registration |
| Active artifacts (tests/scripts/domains/src/) | 705 | 743 | 38 unregistered |
| Checker packages | 38 | 38 | 0 |
| Config files | 0 | 6 | 6 unregistered |
| Aux ledgers | 11 | 13 | 2 missing, 0 pending |
| Doc dirs outside scope | 0 | 10 dirs | ~60 files |
| Legacy code directories | 0 | 28 dirs | ~1500+ files |

---

## 4. Split-Brain Identified

The following pairs disagree on identity or classification:

1. **Document Registry** says `checker-coverage-manifest.json` is `source_of_truth`; it is actually a generated view
2. **Document Registry** says `verification-gate-manifest.json` is `supporting_evidence`; this is correct, but `gate-manifest` checker treats it as authoritative
3. **AGENTS.md** lists `policy-activation-ledger.jsonl` as existing; it does not
4. **artifact-registry** only covers `tests/scripts/domains/src/` — ledgers, schemas, configs in other directories have no artifact identity
5. **ownership-manifest** uses directory-level patterns; individual T0/T1 docs have `owner = null`
6. **Legacy checker scripts** (`scripts/check_*.py`) are deprecated but 18 still exist alongside their `checkers/` replacements

---

## 5. Invariant Status

Against the proposed Registry Control Plane invariants:

| Invariant | Status |
|---|---|
| 1. Every active object has one stable identity | FAIL — ledgers/schemas/configs lack artifact identity |
| 2. Every active T0/T1 object has an owner | FAIL — 9 critical docs without owner |
| 3. Every object has lifecycle_state | PARTIAL — docs have status, artifacts have layer, legacy dirs have nothing |
| 4. current_truth_allowed only on T0/T1 | UNVERIFIED — no cross-registry checker |
| 5. Generated objects cannot be source_of_truth | FAIL — 1 violation (checker-coverage-manifest) |
| 6. CandidateRule → Policy requires PolicyActivation | FAIL — policy-activation-ledger is missing, bridge cannot close |
| 7. Legacy code must have scope identity | FAIL — 28 directories, ~1500+ files, no formal identity |
| 8. Referenced objects resolve to existing files | FAIL — 4 references to non-existent policy-activation-ledger |
| 9. Registry systems themselves are registered | PARTIAL — document-registry self-registered, artifact-registry not |
| 10. Exclusions have owner/reason/scope/review_date | PARTIAL — exclusions have reason and classification, but review_date on only some entries |

Score: **0/10 passing, 3/10 partial, 7/10 failing.**

---

## 6. Baseline Declaration

This document is the RG-0 baseline. It freezes the current state. No fixes are made in this phase.

Next: **RG-1 — Unified Registry Object Model definition.**

### Metric Anchors

| Metric | Value |
|---|---|
| Total classified registry artifacts | 89 |
| Cross-registry coherence gaps | 33 |
| BLOCKED gaps | 13 |
| DEGRADED gaps | 20 |
| Self-declared registry layers | 5 (Document, Artifact, Checker, Scanner, Aux Ledger) |
| Split-brain instances | 6 |
| Invariants passing | 0/10 |

---

## 7. Debt Registration

This reality freeze itself identifies new debt. These will be registered in `verification-debt-ledger.jsonl` during RG-1 or RG-2 (after unified object model exists to represent them):

| Debt ID | Description | Severity |
|---|---|---|
| RG-0-B1 | policy-activation-ledger.jsonl MISSING — referenced by 4 docs + 1 checker | BLOCKED |
| RG-0-B2 | 9 critical L0/L1 docs without owner | BLOCKED |
| RG-0-D1 | 11 ledgers lack artifact identity (scope limitation in artifact-registry) | DEGRADED |
| RG-0-D2 | 4 schemas lack artifact identity | DEGRADED |
| RG-0-D3 | checker-coverage-manifest.json registered as source_of_truth (should be generated) | DEGRADED |
| RG-0-D4 | 28 legacy directories have no lifecycle_state identity | DEGRADED |
| RG-0-D5 | 6 config surface files unregistered | DEGRADED |
| RG-0-D6 | 10 document directories outside DISCOVERABLE_DIRS | DEGRADED |
| RG-0-D7 | external-benchmark-source-registry entries lack required fields | DEGRADED |
| RG-0-D8 | 18 legacy checker scripts coexist with checkers/ replacements | DEGRADED |
