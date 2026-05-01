# Ordivon Verify — Package Extraction Plan

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-12
Tags: `product`, `verify`, `extraction`, `packaging`, `plan`
Authority: `proposal`

## 1. Purpose

PV-12 creates an extraction plan for turning Ordivon Verify into a future clean public/package-ready project. **No files are moved, published, relicensed, or released.**

## 2. Extraction Principle

**Curated extraction, not repository mirroring.**

The public package must be clean and user-facing. It must not expose private Core history, Finance dogfood, internal receipts, or broad Ordivon OS scaffolding. It must carry only the minimum product wedge.

## 3. Extraction Stages

### Stage A — Internal Package Shape (PV-12+)
- Decide source layout
- Isolate CLI code into package modules
- Define schema files
- Collect examples and fixtures
- Complete public README

### Stage B — Private Extraction Branch
- Create branch inside private repo
- Move/copy candidate files into target package structure
- Run full test suite against extracted structure
- Scan for internal references, broker mentions, private paths
- Create secret audit receipt

### Stage C — Clean Public Repo Dry-Run
- Create local temporary repo (no remote)
- Test `pip install -e .` or `uv pip install`
- Run fixture ladder from clean checkout
- Verify all checks pass with no Ordivon-private dependencies

### Stage D — Public Alpha Decision
- License finalized (Apache-2.0 recommended but not decided)
- Secret scan clean
- Internal references removed
- Public issue templates ready
- CI active in public repo
- Docs reviewed and tested

## 4. Source-to-Public Mapping

| Private Source | Public Path | Include? | Notes |
|---------------|------------|----------|-------|
| `scripts/ordivon_verify.py` | `src/ordivon_verify/cli.py` | ✅ | Core CLI, refactored into modules |
| `tests/unit/product/test_ordivon_verify_cli.py` | `tests/unit/test_cli.py` | ✅ | CLI tests |
| `tests/unit/product/test_ordivon_verify_*_fixture.py` | `tests/unit/test_fixtures.py` | ✅ | Fixture tests |
| `tests/fixtures/ordivon_verify_*_external_repo/` | `tests/fixtures/` | ✅ | Bad/clean/standard fixtures |
| `docs/product/ordivon-verify-public-readme-draft.md` | `README.md` | ✅ | Finalized public README |
| `docs/product/ordivon-verify-quickstart.md` | `docs/quickstart.md` | ✅ | Quickstart |
| `docs/product/ordivon-verify-adoption-guide.md` | `docs/adoption.md` | ✅ | Adoption guide |
| `docs/product/ordivon-verify-cli-contract.md` | `docs/cli-contract.md` | ✅ | CLI contract |
| `skills/ordivon-verify/SKILL.md` | `skills/ordivon-verify/SKILL.md` | ✅ | Agent skill |
| `examples/ordivon-verify/github-action.yml.example` | `examples/github-action.yml.example` | ✅ | CI example |
| `docs/runtime/paper-trades/` | — | ❌ | Phase 7P finance dogfood |
| `docs/product/document-governance-stage-summit-dg-z.md` | — | ❌ | Internal DG history |
| `docs/ai/` | — | ❌ | Internal AI onboarding |
| `adapters/finance/` | — | ❌ | Finance pack |
| `domains/finance/` | — | ❌ | Domain models |
| `apps/` | — | ❌ | Web/API |
| `.env`, credentials | — | ❌ | Never |

## 5. Package Target

Recommended future package shape:
- **Python package name**: `ordivon-verify` (PyPI) / `ordivon_verify` (import)
- **CLI command**: `ordivon-verify` (console_scripts entrypoint)
- **Module**: `ordivon_verify`
- **Entrypoint**: `ordivon_verify.cli:main`

Not implemented. Proposal only.

## 6. Release Labels

| Label | Meaning | Current |
|-------|---------|---------|
| `private extraction draft` | Planning only, no package exists | ✅ Now |
| `internal package prototype` | Package structure exists in private branch | Not yet |
| `private beta package` | Package testable by internal team | Not yet |
| `public alpha` | Public repo, early adopters | Not yet |
| `public beta` | Feature-complete, feedback phase | Not yet |
| `stable` | Production-ready, supported | Not yet |

## 7. Release Blockers

| Blocker | Status |
|---------|--------|
| Package structure not implemented | 🚫 |
| License not activated | 🚫 |
| Public repo not created | 🚫 |
| Package tests not separated from private repo | 🚫 |
| Schemas not extracted to JSON schema files | 🚫 |
| README not finalized for public repo | 🚫 |
| No public CI configured | 🚫 |
| No secret scan receipt | 🚫 |
| No dependency audit receipt | 🚫 |
| No public contribution policy | 🚫 |
| No issue templates | 🚫 |

## 8. Non-Activation Clause

This document plans package extraction. It does not move files, publish, relicense, create repos, activate CI, authorize trading, or enable Phase 8.
