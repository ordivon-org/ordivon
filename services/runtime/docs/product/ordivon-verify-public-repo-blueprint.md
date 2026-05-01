# Ordivon Verify — Public Repo Blueprint

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-11
Tags: `product`, `verify`, `packaging`, `repo`, `blueprint`
Authority: `proposal`

## 1. Public Repo Goal

A clean, external-facing repository for Ordivon Verify — the CLI, schemas, examples, and docs — extracted from the private Ordivon monorepo without internal history, finance details, or unfinished governance design.

## 2. Minimum Viable Public Repo Contents

```
ordivon-verify/
├── README.md                          # Public README from PV-10 draft
├── LICENSE                            # Apache-2.0 (recommended, not activated)
├── CHANGELOG.md                       # Empty initially
├── pyproject.toml                     # Package metadata
├── src/ordivon_verify/
│   ├── __init__.py                    # Package init
│   ├── cli.py                         # CLI entry (extracted from scripts/ordivon_verify.py)
│   ├── report.py                      # Trust report builder
│   ├── validators.py                  # Lightweight governance validators
│   └── scanner.py                     # Receipt scanner
├── tests/
│   ├── __init__.py
│   ├── test_cli.py                    # CLI tests (from existing product tests)
│   ├── test_report.py                 # Report tests
│   ├── test_validators.py             # Validator tests
│   └── fixtures/
│       ├── bad-external/              # Bad receipt fixture
│       ├── clean-advisory/            # Clean advisory fixture
│       └── standard/                  # Standard fixture
├── examples/
│   └── github-action.yml.example      # CI example
├── skills/
│   └── ordvon-verify/
│       └── SKILL.md                   # Agent skill
├── schemas/
│   ├── verify-report.schema.json
│   ├── debt-ledger.schema.json
│   ├── gate-manifest.schema.json
│   └── document-registry.schema.json
└── docs/
    ├── quickstart.md
    ├── adoption-guide.md
    ├── cli-contract.md
    ├── ci-example.md
    └── pr-comment-examples.md
```

## 3. What to Strip from Private Repo

| Strip | Why |
|-------|-----|
| AGENTS.md phase context | Internal: Phase 7P, DG-Z, Post-DG, PV history |
| docs/ai/ directory | AI onboarding specific to Ordivon internal |
| docs/governance/ full history | Internal verification debt ledger, DG Pack history |
| docs/runtime/ paper trades | Phase 7P finance dogfood |
| docs/product/ stage summits | Internal phase closure documents |
| docs/architecture/ full ontology | Not ready for external consumption |
| adapters/ directory | Finance adapters, not part of Verify |
| domains/ directory | Domain models, not part of Verify |
| apps/ directory | Web/API, not part of Verify |
| .github/workflows/ (existing) | Internal CI, not the Verify example |
| .env, secrets, credentials | Never public |

## 4. Migration Plan

| Step | Action | Status |
|------|--------|--------|
| 1 | Extract CLI package from `scripts/ordivon_verify.py` | Not started |
| 2 | Extract schemas from existing JSON/JSONL formats | Not started |
| 3 | Extract examples (fixtures, CI, skill) | Not started |
| 4 | Write final public README (from PV-10 draft) | Draft exists |
| 5 | Port and deduplicate tests | Not started |
| 6 | Add public CI (new workflow, clean) | Not started |
| 7 | Choose and add LICENSE file | Not decided |
| 8 | Run secret scan on extracted repo | Not applicable yet |
| 9 | Create public repo on GitHub | **Only after review** |

## 5. Public Repo Non-Goals

The public Verify repo must NOT:
- Include full Ordivon governance OS
- Expose trading/finance capability
- Contain internal phase history
- Offer SaaS or hosted service
- Include MCP server (future, not v0)
- Claim enterprise readiness
- Authorize any action

## 6. Dependency Boundaries

Public Verify repo should have minimal dependencies:
- Python 3.12+ (standard library + `pyyaml` or pure stdlib for JSON)
- No broker SDKs
- No database driver
- No web framework
- No AI/ML libraries
- No network libraries

This keeps the public wedge auditable and trustworthy.

## 7. Non-Activation Clause

This blueprint defines what a public Verify repo could look like. It does not create, publish, or activate any public repository today.
