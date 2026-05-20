# Contributing to Ordivon

Ordivon is a governance system, not a general-purpose framework.
Contributions must respect the boundaries defined in [AGENTS.md](AGENTS.md).

## Setup

```bash
git clone <repo-url> ordivon
cd ordivon
uv sync --extra dev
docker compose -f docker-compose.infrastructure.yml up -d
PYTHONPATH=.:src .venv/bin/python scripts/verify_infrastructure.py
```

## Infrastructure

| Service | Port |
|---------|------|
| PostgreSQL | 5432 |
| NATS | 4222 |
| Temporal | 7233 |

OpenFGA and MinIO are stopped (zero production consumers).

## Before Committing

```bash
# Lint
uv run ruff check src/ scripts/ tests/ state/
uv run ruff format --check --preview src/ scripts/ tests/ state/

# Governance
PYTHONPATH=.:src .venv/bin/python scripts/check_document_registry.py
PYTHONPATH=.:src .venv/bin/python -m ordivon_verify all --check

# Tests
PYTHONPATH=.:src .venv/bin/python -m pytest -q tests/
cargo test --workspace
```

## Document Governance

New documents must be registered in `docs/governance/document-registry.jsonl`.
Run `check_document_registry.py` to validate.

## Architecture Rules

- Core never imports from Pack/Adapter
- PostgreSQL is the canonical data store
- JSONL files are exports, not truth sources
- Receipts are created once, never modified
- All outputs carry `draft: true` — status requires evidence + authority

## Debt

Register unresolved issues in `docs/governance/dependency-audit-debts.jsonl`.
