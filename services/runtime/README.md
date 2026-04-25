# Financial AI OS

Financial AI OS, now tracked under the working identity **AegisOS / CAIOS**, is a governance-first AI workflow operating system baseline for constrained real-world work.

The current canonical design baseline uses **nine responsibility surfaces**:

1. Experience
2. Capability
3. Orchestration
4. Governance
5. Intelligence
6. Execution
7. State
8. Knowledge
9. Infrastructure

The canonical current architecture baseline is [docs/architecture/architecture-baseline.md](./docs/architecture/architecture-baseline.md).

The highest-level AegisOS positioning and execution map now live in:

- [AegisOS Overview](./docs/architecture/aegisos-overview.md)
- [AegisOS Layer Roadmap](./docs/architecture/aegisos-layer-roadmap.md)
- [AegisOS MVP Brief](./docs/product/aegisos-mvp-brief.md)
- [AegisOS MVP Execution Checklist](./docs/product/aegisos-mvp-execution-checklist.md)
- [AegisOS Post-MVP Refinement Execution Plan](./docs/architecture/aegisos-post-mvp-refinement-execution-plan.md)

## Current MVP

The current MVP is:

> a single-agent, single-mainline, finance-seed, governance-aware workflow where a user can clearly complete the analyze -> recommendation -> review chain through the product surfaces.

The MVP gold path is:

`homepage -> quick analyze -> /analyze -> result / recommendation -> /reviews`

The three core page roles are:

- `/` = command center
- `/analyze` = execution workspace
- `/reviews` = supervision workbench

See [AegisOS MVP Brief](./docs/product/aegisos-mvp-brief.md) for the current delivery boundary.

## Delivery Gate

The current repository delivery gate is:

- `backend-static`
- `backend-unit`
- `backend-integration`
- `frontend-static`
- `frontend-build`
- `frontend-components`
- `api-contract`
- `a11y-smoke`
- `mvp-e2e`

The repository also carries:

- a `Security` workflow for dependency and static security scanning
- a `Nightly Regression` workflow for broader integration, visual, accessibility, and performance checks
- a `Delivery` workflow that validates the built release and assembles the current MVP delivery bundle after successful CI on `main` or via manual dispatch

## Package Manager

This repository uses `pnpm` as the only supported JavaScript package manager.

- Use the root workspace scripts in [package.json](./package.json) for frontend tasks.
- Do not use `npm`, `yarn`, or `bun` in this repo.
- The workspace lockfile source of truth is [pnpm-lock.yaml](./pnpm-lock.yaml).

## Development Setup (Linux / Arch WSL2)

### Prerequisites

- Python 3.11+
- Node.js 20+
- [pnpm](https://pnpm.io) 10.33+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://docs.docker.com/) (for PostgreSQL + Redis services)

### First-Time Setup

```bash
cd ~/projects/financial-ai-os

# Copy environment template (edit with your keys)
cp .env.example .env

# Start PostgreSQL and Redis (required)
docker compose up -d postgres redis

# Install Python dependencies (including dev tools)
uv sync --extra dev

# Install JavaScript dependencies
pnpm install --frozen-lockfile
```

### Start Development

```bash
# Terminal 1 — API server (http://127.0.0.1:8000)
uv run uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Web dev server (http://127.0.0.1:3000)
pnpm dev:web
```

### Run Tests

```bash
# Unit tests (Python)
uv run pytest tests/unit -q

# Integration tests (Python)
uv run pytest tests/integration -q

# Frontend type check
pnpm typecheck:web

# E2E end-to-end (requires Playwright browser)
pnpm exec playwright install --with-deps chromium
pnpm test:e2e
```

### Lint & Security

```bash
uv run ruff check .
uv run bandit -r .
pnpm lint:web
```

## Current Status

The repository is past the idea stage and into a load-bearing systems phase:

1. Phase 0 core primitives are frozen
2. Phase 1 load-bearing behavior is in place
3. the MVP gold path is now being closed at the product surface level
4. legacy implementation still exists in parts of `pfios/`, but does not define the current target

## Responsibility Surfaces

```text
financial-ai-os/
- Experience Layer      -> apps/
- Capability Layer      -> capabilities/ plus domains/
- Orchestration Layer   -> orchestrator/
- Governance Layer      -> governance/
- Intelligence Layer    -> intelligence/
- Execution Layer       -> execution/ with skills/ and tools/
- State Layer           -> state/ plus fact-bearing domain objects
- Knowledge Layer       -> knowledge/ plus knowledge-facing wiki assets
- Infrastructure Layer  -> infra/
```

## Engineering Mapping

- `apps/` stays the concrete home for web, API, and worker entrypoints.
- `capabilities/` becomes the home for user-visible product capabilities such as market brief, asset analysis, portfolio review, and postmortem.
- `domains/` remains the business semantic core that capabilities depend on.
- `execution/` is the umbrella layer for `skills/` and `tools/`.
- `knowledge_state/` remains a migration-era umbrella, but the canonical design baseline now treats `knowledge` and `state` as separate responsibility surfaces.
- `infra/` remains the physical infrastructure directory even though the architectural layer is called Infrastructure.

## Hard Rules

1. Experience layers do not own business rules.
2. Risk decisions must pass through `governance/`.
3. Product capabilities are explicit modules, not route-handler side effects.
4. Prompts do not live inside business modules.
5. Tools and skills are different execution units.
6. Workflows do not directly own database details.
7. Knowledge and state are different truths, even when grouped under one layer.
8. `shared/` cannot become a business junk drawer.
9. New capabilities should enter through capability modules, domain services, skills, or workflows, not ad hoc scripts.
10. Major structural changes require an ADR in `docs/decisions/`.

## Migration Map

- `apps/` is now the concrete directory for the Experience Layer.
- `capabilities/` is the new landing zone for product-facing system capabilities.
- `pfios/domain/*` is being split toward `domains/` plus `state/`.
- `pfios/reasoning/*` is being split toward `intelligence/`.
- `pfios/governance/*` maps to root `governance/`.
- `pfios/orchestrator/*` maps to root `orchestrator/`.
- `skills/` and `tools/` are grouped by the Execution Layer without forcing a risky move today.
- `knowledge/` and `state/` are grouped by `knowledge_state/` while remaining internally separated.
- `wiki/` will migrate toward `knowledge/wiki/`.
- `policies/` will migrate toward `governance/policies/`.
- `scripts/` is reserved for operational tasks only; business scripts should move into formal layers.

See [AegisOS Overview](./docs/architecture/aegisos-overview.md), [AegisOS Layer Roadmap](./docs/architecture/aegisos-layer-roadmap.md), [AegisOS MVP Brief](./docs/product/aegisos-mvp-brief.md), [AegisOS MVP Execution Checklist](./docs/product/aegisos-mvp-execution-checklist.md), [architecture-baseline](./docs/architecture/architecture-baseline.md), [layer-module-inventory](./docs/architecture/layer-module-inventory.md), [ai-financial-assistant-roadmap](./docs/product/ai-financial-assistant-roadmap.md), [task-template-system](./docs/product/task-template-system.md), [task-cards](./docs/tasks/README.md), [architecture-diagram](./docs/architecture/architecture-diagram.md), [system-overview](./docs/architecture/system-overview.md), [layer-definition](./docs/architecture/layer-definition.md), and [ADR-001](./docs/decisions/ADR-001-repo-structure.md).
