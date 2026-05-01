# Ordivon Verify — Public Packaging Boundary

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-11
Tags: `product`, `verify`, `packaging`, `public`, `boundary`
Authority: `proposal`

## 1. Purpose

PV-11 defines the public/private packaging boundary for Ordivon Verify and the broader Ordivon governance system. It does **not** publish, open-source, or release anything. It defines what may become public later and what must remain private.

## 2. Recommended Strategy

**Private Core + Public Verify Wedge**

Keep the main Ordivon repository private. Curate Ordivon Verify as the first public product wedge. This preserves internal design flexibility while enabling external adoption.

## 3. Private Core — What Stays Private

| Category | Contents | Reason |
|----------|---------|--------|
| Full Ordivon repo | `zycxfyh/Ordivon` (private) | Contains internal DG history, finance pack, incomplete roadmaps |
| DG Pack evolution | All DG-1 through DG-Z history | Internal governance design iteration |
| Internal receipts | Phase 7P dogfood, paper trade receipts | Finance-specific, not yet productized |
| Finance pack | Alpaca adapters, paper execution, read-only providers | Not part of Verify product |
| Core/Pack/Adapter ontology drafts | Architecture docs still evolving | Not ready for external consumption |
| Rust kernel design | Future Plans | Pre-product, internal only |
| Commercial roadmap | Enterprise, hosted, pricing | Proprietary strategy |
| Internal prompts | Phase scaffolds, AI task templates | Operational, not product |

## 4. Public Verify Wedge — Candidate Contents

| File / Directory | Status | Notes |
|-----------------|--------|-------|
| `scripts/ordivon_verify.py` | Candidate | Core CLI — needs extraction to package |
| Trust report schema | Candidate | JSON schema documented in CLI contract |
| `README.md` (public draft) | Candidate | Already drafted in PV-10 |
| Quickstart | Candidate | Already drafted in PV-10 |
| `skills/ordivon-verify/SKILL.md` | Candidate | Agent skill |
| GitHub Action example | Candidate | Already in examples/ |
| PR comment examples | Candidate | Already drafted |
| Fixture ladder | Candidate | bad/clean/standard external fixtures |
| Receipt checker (lightweight) | Candidate | External-mode receipt scanner from ordvon_verify.py |
| Debt ledger minimal schema | Candidate | JSONL format already defined |
| Gate manifest minimal schema | Candidate | JSON format already defined |
| Document registry minimal schema | Candidate | JSONL format already defined |
| Adoption guide | Candidate | Already drafted |
| CLI contract | Candidate | Already drafted |
| Product brief | Candidate | Already drafted |

## 5. Do Not Public Yet

- Full `zycxfyh/Ordivon` private history
- Phase 7P / paper dogfood internal details
- Finance adapter implementations
- RiskEngine / Policy Platform
- Internal AGENTS.md phase context
- All historical stage summits
- Internal commercial/enterprise strategy
- Unvetted Rust kernel plan
- Any `.env` / secrets / API keys
- Private integration credentials

## 6. Release Maturity Labels

| Label | Meaning | Current? |
|-------|---------|----------|
| `internal` | Only within the team | ✅ Ordivon core |
| `private beta candidate` | Ready for internal review before external sharing | ✅ Ordivon Verify |
| `public alpha` | Shared with early adopters, known gaps | Not yet |
| `public beta` | Feature-complete, seeking feedback | Not yet |
| `stable` | Production-ready, documented, supported | Not yet |

**Current recommendation**: Ordivon Verify is **private beta candidate**. Not yet public alpha.

## 7. Public Repo Shape (Future)

Target public repo: `ordivon-verify`

```
ordivon-verify/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── src/ordivon_verify/
│   ├── __init__.py
│   ├── cli.py
│   ├── report.py
│   ├── validators.py
│   └── scanner.py
├── tests/
│   └── test_ordivon_verify.py
├── examples/
│   └── github-action.yml.example
├── skills/
│   └── ordvon-verify/SKILL.md
├── schemas/
│   ├── verify-report.schema.json
│   ├── debt-ledger.schema.json
│   ├── gate-manifest.schema.json
│   └── document-registry.schema.json
└── docs/
    ├── README.md
    ├── quickstart.md
    ├── adoption-guide.md
    ├── cli-contract.md
    └── ci-example.md
```

## 8. Release Blockers — Public Alpha Gate

| Blocker | Status |
|---------|--------|
| Package structure extracted from monorepo | Not started |
| License decision | Not finalized (PV-11 proposal only) |
| Secret scan on extracted repo | Not applicable yet |
| Dependency audit | Not applicable yet |
| Clean README (no internal references) | Drafted, needs review |
| Minimal external fixture docs | Done (bad/clean/standard) |
| Public issue template | Not created |
| Contribution policy (if open-source) | Not decided |
| No private-core references in public files | Needs extraction audit |

## 9. Boundary Statement

**Ordivon Verify can be public. Ordivon Core remains private.**

This boundary is a proposal. It does not change any repository visibility, license, or release status today.

## 10. Non-Activation Clause

This document defines packaging strategy. It does not publish, open-source, release, activate CI, authorize trading, enable Phase 8, or modify any NO-GO boundary.
