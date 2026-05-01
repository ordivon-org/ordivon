# PV-N2H — DG Coverage Completeness + Legacy Identity Hygiene

## Purpose

Remediate VD-0026-05-01-005 by hardening DG coverage: extend the document
registry checker to detect unregistered current-scope docs and unsafe identity
surfaces, while classifying legacy PFIOS/AegisOS artifacts.

## VD-005 Summary

VD-005 identified a meta-verification gap: `check_document_registry.py` validated
only registered documents, not whether it knew about everything it should.
Two sub-gaps:

- **A. Contract scope gap:** Identity-bearing config/package/env files excluded from DG.
- **B. Checker implementation gap:** No completeness check for unregistered docs.

## Root Cause

The DG checker was initialized with 31 documents created during DG-1 — Ordivon-native
phase artifacts. PFIOS/AegisOS docs, Ordivon-phase runtime receipts, and architectural
specs created outside the DG phase were never registered. The checker had no
mechanism to discover them.

## What Was Built

### 1. Completeness Checker (`check_document_registry.py` extension)

New functions:
- `check_completeness(entries, exclusions)` — discovers all `.md` files under
  `docs/ai`, `docs/governance`, `docs/product`, `docs/architecture`, `docs/runtime`
  (excluding `docs/archive/`). Each file must be registered or excluded with reason.
- `check_identity_surfaces()` — validates `pyproject.toml`, `package.json`,
  `README.md`, and `tests/conftest.py` do not carry legacy PFIOS identity.

New summary lines:
- `Completeness violations`
- `Identity surface violations`

### 2. Exclusions File (`docs/governance/document-registry-exclusions.json`)

141 entries total:
- 23 legacy AegisOS/PFIOS docs → `archive_historical`
- 118 Ordivon-phase docs → `pending_registration`

Every exclusion carries: `path`, `reason`, `classification`, `owner`, `reviewed_at`.

### 3. DG Contract Update

`document-governance-pack-contract.md` scope table updated:

- Added identity-bearing surfaces as governed objects:
  `pyproject.toml`, `package.json`, `apps/*/package.json`, `apps/*/pyproject.toml`,
  `README.md`, `tests/conftest.py`
- Clarified: identity surface governance is about current-truth identity, not
  runtime config semantics.
- Removed `.env` and config files from explicit out-of-scope (they are now
  governed when identity-bearing).

## What Was Cleaned

### Identity surfaces (already done in PV-N2H)
- `pyproject.toml`: name `pfios` → `ordivon`
- `package.json`: name `pfios-monorepo` → `ordivon`, 18 PFIOS scripts → 12 Ordivon
- `apps/web/package.json`: name `pfios-web` → `ordivon-web`
- `apps/api/pyproject.toml`: name `pfios-api` → `ordivon-api`
- `README.md`: 196-line AegisOS → 110-line Ordivon
- `tests/conftest.py`: global PFIOS_DB_URL → scoped to legacy paths

### Legacy docs classification
- 23 AegisOS/PFIOS docs classified as `archive_historical`
- 4 legacy runtime READMEs annotated with deferral headers

## What Was Intentionally Deferred

- **118 Ordivon-phase docs** — classified as `pending_registration`. These are
  valid Ordivon documents created during DG/PV phases but never registered in
  `document-registry.jsonl`. Full registration (with doc_id, doc_type, status,
  authority, freshness) exceeds the scope of PV-N2H. The completeness checker
  now knows about them and will fail if any future doc is created without
  registration or exclusion.
- **Legacy runtime modules** (`orchestrator/`, `capabilities/`, etc.) — not deleted.
- **AegisOS product docs** (`docs/product/aegisos-*`) — not moved to archive.

## New Checker Invariants

1. Every discoverable `.md` file under current-scope directories must be
   registered or excluded with a valid reason.
2. `pyproject.toml` must not contain `name = "pfios"`.
3. `package.json` name must not contain "pfios".
4. `README.md` opening must not identify as "Financial AI OS" or "AegisOS".
5. `tests/conftest.py` must not globally set PFIOS_DB_URL unconditionally.
6. Exclusions without `reason` or `classification` are themselves violations.

## VD-005 Status

- **Contract gap (A):** REMEDIATED. Identity-bearing surfaces added to DG scope.
- **Checker gap (B):** REMEDIATED. Completeness + identity surface checks implemented.
- **Identity surfaces:** CLEAN. Zero legacy PFIOS references on current surfaces.
- **Unregistered docs:** CLASSIFIED. 118 docs in `pending_registration`, 23 in `archive_historical`.

VD-005 can be closed with the note that `pending_registration` entries require a
separate DG-H completeness pass to fully register.

## Verification Results

| Check | Result |
|-------|--------|
| Document registry checker | PASS (0 completeness, 0 identity) |
| Debt checker | PASS (1 open, 4 closed) |
| Receipt integrity | PASS |
| Gate manifest | PASS |
| Paper dogfood | PASS |
| Product tests | 140/140 PASS |
| Governance tests | 192/192 PASS |
| Finance tests | 204/204 PASS |
| Native Verify | READY |
| pr-fast | 11/11 PASS |
| Architecture | clean |
| Runtime evidence | clean |
| Eval corpus | 24/24 PASS |
| Ruff check | clean |
| Ruff format | all formatted |

## New AI Context Check

A fresh AI reading README.md → AGENTS.md → docs/ai/README.md →
docs/ai/current-phase-boundaries.md → this document →
docs/governance/document-governance-pack-contract.md →
docs/governance/document-registry.jsonl →
docs/governance/document-registry-exclusions.json

would understand:
- Current project identity is Ordivon. PFIOS/AegisOS are historical.
- Ordivon Verify is the current product wedge.
- DG checker now detects unregistered current-scope docs and identity pollution.
- 141 docs are excluded (23 archive_historical, 118 pending_registration).
- No unsafe identity references remain on current surfaces.
- Legacy runtime modules are deferred, not deleted.
- Phase 8 remains DEFERRED.
- No live/broker/auto/Policy/RiskEngine action is authorized.

## Boundary Confirmation

- Governance coverage hardening only
- No public release / public repo / license activation / package publishing
- No CI change / SaaS / MCP server
- No broker/API / paper/live order / Policy/RiskEngine activation
- No legacy runtime deletion
- READY does not authorize execution
- Phase 8 remains DEFERRED

## Next Recommended Phase

PV-N3 — Public Quickstart (unblocked: VD-005 remediated, surfaces clean).

---

*Closed: 2026-05-01*
*Phase: PV-N2H*
*Task type: governance coverage hardening / identity hygiene*
*Risk level: R1*
