# Contributing to Ordivon

> **Status**: Current — Docs-D5C
> **Owner**: ordivon-core-maintainer
> **Last verified**: 2026-05-14

## Before You Start

Ordivon is a **governance operating system**, not a general-purpose framework or library. Contributions must respect:

1. **AGENTS.md** — the entry point for all collaborators. Read it first.
2. **`policies/constitution.md`** — 14 non-negotiable invariants. Every PR must comply.
3. **`docs/ai/current-phase-boundaries.md`** — what's ACTIVE, what's DEFERRED, what's NO-GO.
4. **`docs/ai/agent-output-contract.md`** — required output format for AI agents and human contributors.

The core philosophy: **only strictly survival logic deserves to live.** Dead code is removed, not tolerated.

## Development Environment

### Prerequisites

- Python 3.11+
- `uv` (Python package manager)
- Docker + Docker Compose (for infrastructure services)

### Setup

```bash
git clone <repo-url> ordivon
cd ordivon

# Install dependencies
uv sync --extra dev

# Start infrastructure services
docker compose -f docker-compose.infrastructure.yml up -d

# Verify infrastructure
uv run python scripts/health_check.py

# Create .env (use actual credentials)
cp .env.example .env  # if available, or create manually
```

### Infrastructure Services

Ordivon depends on 5 infrastructure services (see `docs/operations/runbook.md` for details):

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Truth-state database |
| NATS | 4222 | Event bus (JetStream) |
| Temporal | 7233 | Workflow runtime |
| OpenFGA | 8080 | Authorization |
| MinIO | 9000/9001 | Object storage (S3) |

All services start with `docker compose -f docker-compose.infrastructure.yml up -d`.

## Development Workflow

### 1. Branch

```bash
git checkout -b <type>/<description>
# Types: feat, fix, chore, docs, refactor, infra, governance
# Examples: feat/pg-schema-claims, fix/reconciler-race, chore/cleanup-dead-ci
```

### 2. Develop

- All code lives in `src/ordivon_verify/` and `src/ordivon_governance_core/`.
- Governance code: `src/ordivon_governance_core/` (registry, events, temporal, NATS, OPA, OpenFGA, S3).
- Verification code: `src/ordivon_verify/` (checkers, scanners, control plane, registry, CLI).
- Scripts: `scripts/` — standalone tools (health check, backup, governance operations).
- Tests: `tests/` — integration tests for infrastructure services.
- Docs: `docs/` — follow the document governance rules.

### 3. Before Committing

```bash
# Lint
uv run ruff check src/ scripts/ tests/ state/
uv run ruff format --check --preview src/ scripts/ tests/ state/

# Auto-fix lint issues
uv run ruff check --fix src/ scripts/ tests/ state/
uv run ruff format --preview src/ scripts/ tests/ state/

# Governance checks
uv run python scripts/check_document_registry.py
uv run python -m ordivon_verify document-governance --check

# Integration tests
uv run python tests/test_nats_integration.py
uv run python tests/test_authorization_integration.py
```

### 4. Commit

```
<type>(<scope>): <description>

[optional body — what and why, not how]
[optional footer — debt references, breaking changes]
```

Examples:
```
feat(governance): add claim-verification to PG migration
chore(ci): remove orphan codeql workflow
docs(adr): add ADR-0006 for LiteLLM integration
```

### 5. PR

Open a pull request to `main`. Fill in the PR template (`.github/pull_request_template.md`):

- **Summary**: what this PR changes, which Phase/Pack it belongs to.
- **Boundary Confirmation**: no live trading, no broker access, no policy activation.
- **Verification**: CI passes, checkers run, docs registered.
- **Behavioral Impact**: what behavior changes. Pre-existing debt exposed.
- **Debt Registration**: if this PR introduces known unresolved issues, register in debt ledger.

### 6. CI Gates

CI runs on every push to `main` and every PR:

| Job | What it checks | Gate type |
|-----|---------------|-----------|
| `ruff` | Python lint + format | Hard — fails → no merge |
| `governance` | Doc registry + governance checks | Hard |
| `infra-tests` | NATS + Temporal + OpenFGA + OPA | Soft — run if infra available |
| `db-check` | DB migration dry-run | Hard |

See `.github/workflows/ci.yml`.

## Document Governance

Every new document must be registered in the document registry (`docs/governance/document-registry.jsonl`). The registry is the single source of truth for document lifecycle.

### Registering a new document

1. Write the document in the appropriate location.
2. Register it in the document registry with:
   - `doc_id`: unique identifier (kebab-case)
   - `path`: relative path from repo root
   - `title`: human-readable title
   - `doc_type`: one of the valid types (see `docs/governance/schemas/document-types.json`)
   - `status`: `current`, `accepted`, `proposed`, `draft`, etc.
   - `authority`: `source_of_truth`, `current_status`, `supporting_evidence`, etc.
   - `last_verified`: date in `YYYY-MM-DD` format
   - `stale_after_days`: freshness window (integer or `null` for never-stale)
3. Run `uv run python scripts/check_document_registry.py` to validate.
4. The document must not contain any dangerous phrases (see checker for full list).

### Document types

Valid document types are defined in `docs/governance/schemas/document-types.json`. Adding a new type requires editing only that file — no dual-checker drift.

## Code Style

### Python

- **Formatter**: `ruff format --preview`
- **Linter**: `ruff check` with project config
- **Type hints**: Required for all public functions
- **Docstrings**: Required for all public modules, classes, and functions
- **Imports**: `from __future__ import annotations` in all files

### Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix with `_`

### Governance-Specific Conventions

- **Status values**: UPPERCASE (`READY`, `BLOCKED`, `VERIFIED`, `OPEN`)
- **Debt IDs**: `DEBT-XXX-NNN` format
- **Receipt IDs**: Structured, traceable format
- **Claim IDs**: Never self-generated — always system-assigned

## Architecture Rules

These are enforced by CI and must not be violated:

### Core/Pack/Adapter Import Direction

```
Core → (never imports) Pack / Adapter
Pack → (imports) Core, (never imports) Adapter
Adapter → (imports) Core, Pack
```

Violation: a Core module importing from a Pack or Adapter.

### State Truth Boundary

- PostgreSQL is the single source of truth for all domain entities.
- No governance-significant data may be written to filesystem, cache, or DuckDB.
- JSONL files are exports, not truth sources. They are regenerated from PG.

### Receipt Immutability

- Receipts are created once and never modified.
- Receipts must reference the governance decision that authorized them.
- Receipts are evidence pointers, not narrative summaries.

## Testing

### Integration Tests

```bash
# All integration tests
uv run python tests/test_nats_integration.py
uv run python tests/test_authorization_integration.py

# Individual test
uv run python -m pytest tests/test_nats_integration.py::test_jetstream_pub_sub
```

### CI Simulation

```bash
# Simulate full CI locally
uv run ruff check src/ scripts/ tests/ state/
uv run ruff format --check --preview src/ scripts/ tests/ state/
uv run python scripts/check_document_registry.py
uv run python -m ordivon_verify document-governance --check
uv run python tests/test_nats_integration.py
uv run python tests/test_authorization_integration.py
uv run python scripts/migrate_governance_to_pg.py --dry-run
```

## Adding New Infrastructure

When adding a new infrastructure component:

1. **ADR first** — write an Architecture Decision Record in `docs/architecture/adr/`.
2. **`.env` update** — add credential variables if needed.
3. **`docker-compose.infrastructure.yml`** — add the service definition.
4. **`runbook.md`** — add operational procedures (health check, common failures, recovery).
5. **Graceful fallback** — every service must have a documented degradation path per ADR-0005.
6. **Health check** — add to `scripts/health_check.py`.
7. **Secrets** — never commit credentials. Use `.env` + environment variables.

## Debt Management

Ordivon uses a debt ledger (`docs/governance/verification-debt-ledger.jsonl`) to track known issues.

### When to open a debt

- A known issue cannot be fixed in the current PR without scope creep.
- An edge case is acknowledged but not yet handled.
- A dependency upgrade is deferred.
- A security gap is documented and accepted for now.

### How to open a debt

Register in the debt ledger with:
- Unique ID (`DEBT-XXX-NNN`)
- Status: `OPEN`
- Description, severity, scope
- Owner and target stage

### Debt lifecycle

```
OPEN → TRIAGE → IN_PROGRESS → RESOLVED → CLOSED
                                      → REJECTED
```

## Communication

### Language

- **Code comments and identifiers**: English.
- **Documentation**: English.
- **Receipts and governance artifacts**: English.
- **Commit messages**: English.

### Review Expectations

- **Response time**: within 7 days.
- **Review scope**: boundary compliance, governance rules, document registry consistency.
- **Merge requirements**: CI green + at least one human approval.
- **No merge-without-review**: Even typo fixes go through PR review.

## Getting Help

1. **AGENTS.md** — the primary entry point.
2. **`docs/operations/runbook.md`** — infrastructure issues.
3. **`docs/architecture/adr/`** — why we chose what we chose.
4. **`docs/ai/new-ai-reading-order.md`** — 10-step onboarding.
5. **Debt ledger** — search for known issues before filing new ones.
