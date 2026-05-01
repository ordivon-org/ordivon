# Ordivon Verify — Package Structure Proposal

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-12
Authority: `proposal`

## 1. Proposed Repository Structure

```
ordivon-verify/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── src/
│   └── ordivon_verify/
│       ├── __init__.py
│       ├── cli.py              # CLI argument parsing + dispatch
│       ├── report.py           # Trust report builder (human + JSON)
│       ├── checks/
│       │   ├── __init__.py
│       │   ├── receipts.py     # Receipt contradiction scanner
│       │   ├── debt.py         # Debt ledger validator
│       │   ├── gates.py        # Gate manifest validator
│       │   └── docs.py         # Document registry validator
│       └── schemas/
│           ├── ordivon.verify.schema.json
│           ├── trust-report.schema.json
│           ├── verification-debt-ledger.schema.json
│           ├── gate-manifest.schema.json
│           └── document-registry.schema.json
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_cli.py
│   │   ├── test_report.py
│   │   ├── test_receipts.py
│   │   ├── test_debt.py
│   │   ├── test_gates.py
│   │   └── test_docs.py
│   └── fixtures/
│       ├── bad-external/
│       ├── clean-advisory/
│       └── standard/
├── examples/
│   └── github-action.yml.example
├── skills/
│   └── ordivon-verify/
│       └── SKILL.md
└── docs/
    ├── quickstart.md
    ├── adoption.md
    ├── cli-contract.md
    ├── ci.md
    └── pr-comments.md
```

## 2. What Belongs in Package Code

| Module | Contents |
|--------|---------|
| `cli.py` | argparse + subcommands, --root/--config/--mode/--json, main() entrypoint, exit code dispatch |
| `report.py` | determine_status(), build_report(), print_human(), status_to_exit_code() |
| `checks/receipts.py` | Receipt file scanner, SEALED/Skipped None/clean tree pattern detection |
| `checks/debt.py` | JSONL debt ledger loader + validator (required fields, open/closed count) |
| `checks/gates.py` | JSON gate manifest loader + validator (gate structure, no-op detection, count match) |
| `checks/docs.py` | JSONL document registry loader + validator (required fields, stale detection) |

## 3. What Does NOT Belong

- Finance pack (Alpaca adapters, paper execution, read-only providers)
- Broker API clients
- Ordivon Core ontology (Core/Pack/Adapter planes)
- Full DG Pack history (DG-1 through DG-Z)
- Internal stage summits and receipts
- Phase 7P paper dogfood ledger
- Hosted service logic
- Enterprise policy packs
- RiskEngine or Policy Platform
- AI onboarding docs (docs/ai/)
- Internal AGENTS.md phase scaffolding

## 4. Schema Extraction

Schemas should be published as standalone JSON Schema files alongside the package:

| Schema File | Source |
|------------|--------|
| `ordivon.verify.schema.json` | ordivon.verify.json format |
| `trust-report.schema.json` | JSON output from `--json` |
| `verification-debt-ledger.schema.json` | JSONL debt ledger format |
| `gate-manifest.schema.json` | Gate manifest JSON format |
| `document-registry.schema.json` | Document registry JSONL format |

## 5. Testing Strategy

| Layer | Tests |
|-------|-------|
| Unit | Per-module unit tests (report, receipts, debt, gates, docs) |
| Integration | CLI end-to-end with mock fixtures |
| Fixture ladder | Bad external → BLOCKED, clean advisory → DEGRADED, standard → READY |
| Safety | No network, no file writes, no shell injection |
| Schema | JSON schema validation against fixtures |

## 6. pyproject.toml Skeleton

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ordivon-verify"
version = "0.1.0"
description = "Verify AI-generated work before you trust it."
readme = "README.md"
requires-python = ">=3.12"
license = {text = "Apache-2.0"}
dependencies = []

[project.scripts]
ordivon-verify = "ordivon_verify.cli:main"

[project.optional-dependencies]
dev = ["pytest", "ruff"]
```

## 7. Non-Activation Clause

This is a structure proposal. No package has been created. No files have been moved.
