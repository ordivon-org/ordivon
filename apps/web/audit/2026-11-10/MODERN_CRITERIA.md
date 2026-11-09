# MODERN_CRITERIA — 2025–2026 source-modernization evidence checklist

Base: ef17d6879d12faa61fff3bb762b0d500d73c9113. Methods are selected for their factual seam, not activated as mandatory rituals. Criterion result may be PASS, PARTIAL, FAIL or UNKNOWN with exact Owner and consumer scope.

| # | Concrete criterion | Natural evidence/negative | Web current result |
|---|---|---|---|
| C01 | Parnas/DDD: one owner holds each domain state, identity, lifecycle and effect | WebStore sole node:sqlite handle and actual transaction functions | PASS for canary |
| C02 | Domain-first discoverability, terms are stable across code and docs | Principal, Session, Grant and AgentEffect typed in src/model.ts | PASS scoped |
| C03 | Hexagonal / dependency inversion | Typed AgentAdmissionEvaluator interface consumes Security-owned contract | PARTIAL: synchronous process adapter risk |
| C04 | Enforced Owner boundaries; no arbitrary private imports | tools/repo/owners.toml and check_owner_boundaries.py | PASS for declared source mechanics, dynamic external dependencies not proven |
| C05 | Deep module: small public seam concentrates complexity | store.ts owns transaction; store-sessions.ts / store-agent-grants.ts are local helpers | PARTIAL; large file length alone is not a failure |
| C06 | Platform-native path, strict configuration parsing | config.ts URL.pathname and parseInt counterexamples | FAIL: repair F01/F02 |
| C07 | Configuration/schema/contract sync and exact version semantics | src/store-schema.ts and planning/lego-plan-r1.json; Host source schema 13 vs old root plan 11 | PARTIAL; cross-Owner coordination drift |
| C08 | Immutability/identity/receipt authority and scoped UNKNOWN | store.ts effect receipt/replay; README canary qualification | PASS scoped canary, installed UNKNOWN |
| C09 | Actual consumer trace before retire | tools/repo/check_architecture_docs.py:227 names apps/web/planning/lego-plan-r1.json | PASS keep plan |
| C10 | Recovery/transaction guarantees sourced, no speculative global state | store.ts BEGIN IMMEDIATE/COMMIT/ROLLBACK and existing native replay tests | PASS current owner source scope |
| C11 | Tests/README/ADR truthful; no new route/hook/registry | apps/web/mise.toml verify and current 18 native tests; README nonproduction qualifier | PASS baseline |

Actual per-Owner evaluation: only Web code/seams have targeted semantic source inspection here. Other 20 named Owners have complete source metadata/read+hash inventory and remain UNKNOWN at semantic level pending their independent natural-Owner audit. A numerical score would misrepresent this scope.

Comparators: Nx official module boundaries (https://nx.dev/docs/features/enforce-module-boundaries); Turborepo official repository structuring (https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository); Node official file URL conversion (https://nodejs.org/api/url.html); Ordivon existing skills systems-engineering, compositional-contracts, design-structure-matrix, recursive-lego-calculus, skill-supply-chain-audit and task-space-reentry. Matt improve-codebase-architecture/domain-modeling, ECC selective native hooks, and Superpowers planning/debugging/verification supply methods, not new execution authorities. Do not install Nx/Turbo or copy external hooks solely to imitate a fashionable directory.
