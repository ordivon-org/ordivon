# PV-N2H — Legacy Identity Hygiene

## Purpose

Clean PFIOS/AegisOS identity pollution from current Ordivon surfaces (package metadata,
README, AI onboarding, config files) without deleting legacy runtime modules.
Ensure fresh AI and future public-package extraction understand the project as Ordivon.

## Legacy Residue Inventory

| Path | Legacy Term | Classification | Action |
|------|-----------|---------------|--------|
| `pyproject.toml` | `name = "pfios"` | package_identity_pollution | Changed to `"ordivon"` |
| `pyproject.toml` | `description = "Personal Financial..."` | package_identity_pollution | Changed to Ordivon description |
| `package.json` | `"name": "pfios-monorepo"` | package_identity_pollution | Changed to `"ordivon"` |
| `package.json` | 18 `PFIOS_*` scripts | package_identity_pollution | Replaced with Ordivon scripts |
| `apps/web/package.json` | `"name": "pfios-web"` | package_identity_pollution | Changed to `"ordivon-web"` |
| `apps/api/pyproject.toml` | `name = "pfios-api"` | package_identity_pollution | Changed to `"ordivon-api"` |
| `apps/api/pyproject.toml` | `"Financial-AI-OS API Service"` | package_identity_pollution | Annotated as legacy |
| `tests/conftest.py` | Global `PFIOS_DB_URL` for all tests | test_env_pollution | Scoped to PFIOS paths only |
| `.env` | `# PFIOS Environment Configuration` | package_identity_pollution | Changed to Ordivon (local-only, not tracked) |
| `README.md` | 196 lines of AegisOS/PFIOS content | current_truth_pollution | Fully rewritten as Ordivon |
| `docs/ai/README.md` | Phase status stale | current_truth_pollution | Updated to PV-N2H |
| `orchestrator/runtime/README.md` | No legacy annotation | legacy_runtime_deferred | Added legacy header |
| `capabilities/workflow/README.md` | No legacy annotation | legacy_runtime_deferred | Added legacy header |
| `packs/README.md` | "AegisOS / CAIOS core meaning" | legacy_runtime_deferred | Marked historical |
| `knowledge/wiki/architecture/README.md` | No legacy annotation | legacy_runtime_deferred | Added legacy header |
| `docs/product/aegisos-*` (3 files) | AegisOS as current identity | archive_historical | Deferred to archive classification (P4) |
| `docs/runtime/h1-*, h2-*, h9-*, codeql-*, dependabot-*` | PFIOS/AegisOS in historical context | archive_historical | Acceptable — historical phase docs |
| `docs/archive/` | ~15 AegisOS batch/phase docs | archive_historical | Already in archive |

## What Was Cleaned

### P1 — Package identity (4 files)
- `pyproject.toml`: name → `ordivon`, description → governance OS
- `package.json`: name → `ordivon`, 18 legacy PFIOS scripts → 12 Ordivon scripts
- `apps/web/package.json`: name → `ordivon-web`
- `apps/api/pyproject.toml`: name → `ordivon-api`, description annotated as legacy

### P1 — Test environment (1 file)
- `tests/conftest.py`: global `PFIOS_DB_URL` → scoped to PFIOS test paths only

### P2 — Root identity (3 files)
- `README.md`: 196-line AegisOS/PFIOS content → 110-line Ordivon README
- `AGENTS.md`: header + phase inventory updated to PV-N2H
- `docs/ai/README.md`: phase status + identity updated

### P3 — Legacy runtime READMEs (4 files)
- `orchestrator/runtime/README.md`, `capabilities/workflow/README.md`,
  `packs/README.md`, `knowledge/wiki/architecture/README.md`: added legacy headers

## What Was Intentionally Deferred

- **Legacy runtime directories** (`orchestrator/`, `capabilities/`, `intelligence/`,
  `state/`, `infra/`, `services/`, `apps/`, `domains/`, `adapters/`) — NOT deleted.
  These contain PFIOS code that Ordivon does not depend on but is preserved as
  historical reference.
- **AegisOS product docs** (`docs/product/aegisos-*`) — NOT moved. They remain as
  historical phase documentation, classified as archive_historical.
- **PFIOS/AegisOS references in runtime docs** — NOT cleaned. These are historical
  phase records. Cleaning them would distort the historical record.
- **`pyproject.toml` `include` directive** — `"pfios*"` remains in `tool.setuptools.packages.find.include`
  because PFIOS packages still exist in the repo. This is harmless for Ordivon
  since we are not publishing.
- **`tests/contracts/`, `tests/integration/`, `tests/e2e/`** — NOT modified. Legacy
  PFIOS tests scoped by their own directory structure.

## Why Legacy Runtime Modules Were Not Deleted

1. They contain historical implementation that informed Ordivon's design.
2. The PFIOS repo history is carried in this repo's git history — deleting
   files would break that continuity.
3. Some modules (e.g., `governance/`) were extracted from PFIOS and are
   now Ordivon-native. The migration boundary is fuzzy and deleting the
   old code risks breaking subtle imports.
4. The cost of deletion (risk to working Ordivon tests) outweighs the
   benefit of cosmetic cleanup at this stage.
5. Future phases may extract reusable patterns from legacy code.

## Current Identity After Cleanup

- **Project:** Ordivon
- **Product wedge:** Ordivon Verify (`src/ordivon_verify/`)
- **Active phases:** PV-N2H (hygiene), PV-N3 (next)
- **Historical:** PFIOS → AegisOS/CAIOS → Ordivon

## Legacy Scan Result

Scan: `rg "PFIOS|AegisOS|CAIOS|pfios"` on current identity surfaces.

All remaining hits are:
- **Intentional historical context** (README historical section, AGENTS phase inventory)
- **Explicit legacy classification headers** (4 legacy READMEs)
- **Legacy test infrastructure** (conftest.py, scoped)
- **Historical phase docs** (docs/runtime/*, docs/product/aegisos-*)
- **Package include directive** (pyproject.toml, harmless)

No unsafe current-truth pollution remains.

## Verification Results

| Check | Result |
|-------|--------|
| Product tests | 140/140 PASS |
| Governance tests | 192/192 PASS |
| Finance tests | 188/188 PASS |
| Native Verify | READY |
| Standard external | READY |
| Clean advisory | DEGRADED |
| Bad external | BLOCKED |
| Checkers (5) | All PASS |
| pr-fast | 11/11 PASS |
| Architecture | clean |
| Runtime evidence | clean |
| Eval corpus | 24/24 PASS |
| Frontend | 57 pass + static build |
| Ruff check | clean |
| Ruff format | all formatted |

## Boundary Confirmation

- Identity hygiene only
- No public release / public repo / license activation / package publishing
- No CI change / SaaS / MCP server
- No broker/API / paper/live order / Policy/RiskEngine activation
- No legacy runtime deletion
- READY does not authorize execution
- Phase 8 remains DEFERRED

## New AI Context Check

A fresh AI reading README.md → AGENTS.md → docs/ai/README.md →
docs/ai/current-phase-boundaries.md → docs/runtime/legacy-identity-hygiene-pv-n2h.md
would understand:

- Current project identity is Ordivon.
- Ordivon Verify is current product wedge.
- PFIOS/AegisOS are historical identities, not current truth.
- Legacy runtime directories are deferred, not public wedge.
- Phase 8 remains DEFERRED.
- No live/broker/auto/Policy/RiskEngine action is authorized.

## Next Recommended Phase

PV-N3 — Public Quickstart. Write a public-facing quickstart doc using only
public schemas and fixtures, validating the wedge boundary.

---

*Closed: 2026-05-01*
*Phase: PV-N2H*
*Task type: cleanup / identity hygiene / docs-config boundary*
*Risk level: R1*
