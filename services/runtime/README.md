# Financial AI OS

Financial AI OS is a personal finance and trading AI operating system organized around a controlled multi-layer architecture.

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

## Package Manager

This repository uses `pnpm` as the only supported JavaScript package manager.

- Use the root workspace scripts in [package.json](./package.json) for frontend tasks.
- Do not use `npm`, `yarn`, or `bun` in this repo.
- The workspace lockfile source of truth is [pnpm-lock.yaml](./pnpm-lock.yaml).

## Current Status

The repository is in an active migration phase:

1. legacy implementation still exists in parts of `pfios/`
2. the root-layer structure is now the architectural baseline for new work
3. historical migration notes remain useful, but they do not override the baseline

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

See [architecture-baseline](./docs/architecture/architecture-baseline.md), [layer-module-inventory](./docs/architecture/layer-module-inventory.md), [ai-financial-assistant-roadmap](./docs/product/ai-financial-assistant-roadmap.md), [task-template-system](./docs/product/task-template-system.md), [task-cards](./docs/tasks/README.md), [architecture-diagram](./docs/architecture/architecture-diagram.md), [system-overview](./docs/architecture/system-overview.md), [layer-definition](./docs/architecture/layer-definition.md), and [ADR-001](./docs/decisions/ADR-001-repo-structure.md).
