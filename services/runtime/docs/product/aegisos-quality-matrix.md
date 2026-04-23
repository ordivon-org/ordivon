# AegisOS Quality Matrix

This document maps quality responsibilities to the concrete workflows and commands that enforce them.

| Quality Layer | Primary Command | Primary Workflow / Job | Current Intent |
| --- | --- | --- | --- |
| Static backend | `pnpm lint:py` | `CI -> backend-static` | Python compile + lint gate on every PR |
| Static frontend | `pnpm lint:web` / `pnpm typecheck:web` | `CI -> frontend-static` | Web lint + type gate on every PR |
| Unit | `pnpm test:unit` | `CI -> backend-unit` | Core Python module correctness |
| Component | `pnpm --dir apps/web test` | `CI -> frontend-components` | Rendered React component behavior |
| Integration | `pnpm test:integration:core` | `CI -> backend-integration` | Mainline backend integration behavior |
| Contract | `pnpm test:contract` / `pnpm generate:openapi` | `CI -> api-contract` | Public API and object-shape continuity |
| Accessibility | `pnpm test:e2e:a11y` | `CI -> a11y-smoke` | MVP route accessibility smoke |
| E2E / Smoke | `pnpm test:e2e:mvp` | `CI -> mvp-e2e` | MVP gold path from user perspective |
| Visual regression | `pnpm test:e2e:visual` | `Nightly Regression -> frontend-quality-regression` | Stable screenshots for core MVP surfaces |
| Performance | `pnpm test:perf:web` / `pnpm test:perf:api` / `pnpm lighthouse` | `Nightly Regression` | Lightweight baselines, not full load testing |
| Security | `pnpm scan:security` / `pnpm audit:py` / `pnpm audit:web` | `Security` | Static code scan + dependency hygiene |
| Release validation | `pnpm test:e2e:release` | `Delivery` | Built app pair boots and serves MVP routes |

## Defaults

- PR checks stay fast and representative.
- Nightly checks carry broader regression, visual, accessibility, performance, and security depth.
- Delivery remains release validation, not production deployment.
- `mock` remains the default reasoning provider in automated CI.
