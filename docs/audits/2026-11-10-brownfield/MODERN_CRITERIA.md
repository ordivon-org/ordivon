# MODERN_CRITERIA — evidence-based 2025–2026 architecture quality

Criteria are not checkboxes commanding implementation. Mark **PASS / PARTIAL / FAIL / UNKNOWN** only with path:line, actual consumer, exception/risk. Partial/UNKNOWN cannot be converted to FAIL merely by lacking a decorative technology.

| ID | Checkable question | Evidence / falsifier | Mature idea |
|---|---|---|---|
| C01 | Does code live under real business/feature owner, not artificial technical symmetry? | owner manifest + actual imports vs README | DDD bounded context / Modular Monolith |
| C02 | Do imported dependencies obey actual owner authority and explicit contracts? | source import graph and boundary rules; cycle/SCC | Nx depConstraints (idea), Clean/Hexagonal |
| C03 | Does each module expose a small, stable interface hiding complex decision logic? | call-site readset, shallow forwarding wrappers | Parnas information hiding, Matt Deep Modules |
| C04 | Is each state and evidence fact written and recovered by exactly one natural owner? | schema, migrations, transaction, CAS/Journal, receipts | single writer / ownership / source-of-truth |
| C05 | Are schema/version/lifecycle and documentation claims aligned with executable source? | README front matter, owner API/schema, negative example | contract-first / bounded provenance |
| C06 | Are candidate external frameworks proven current/consumed, not listed as active merely by installation? | config vs installed version/real import | ECC search-first, adapter qualification |
| C07 | Are expensive/dangerous effects explicitly separated from observation, intent and authorization? | real read/write call graph / policy; UNKNOWN handling | state machines, effect systems, safety |
| C08 | Is shared code actually shared without duplicate business rule implementations or circular dependencies? | module-level import edges, clone analysis | cohesion/coupling / DSM |
| C09 | Does the repository contain dead code, historical scripts, duplicate helpers or self-referential tests/registries? | consumer graph + Git history + deletion test | Matt deletion test, lean waste |
| C10 | Do build/verify commands correctly select affected natural Owners and preserve lockfiles? | actual repo:ci, mise/pyproject/pnpm/cargo | Turborepo task DAG/Nx project graph; no new Nx install |
| C11 | Are human/agent entrypoints discoverable, accurate, and free of stale roadmap/superseded current-truth assertions? | README/AGENTS/Skill/ADR vs running CLI | docs-as-navigation, living architecture |
| C12 | Are proofs/tests tied to exact bounded claims, preserving UNKNOWN and business acceptance boundaries? | Hoare pre/post, invariants, trace/readback, negative controls | R2.1 contract, CEGAR, assurance case |

### Architecture decision rule
Prefer DELETE → REUSE → COMPOSE → (only if necessary) REFACTOR of existing code; work down owner responsibilities not across unrelated Owners. A hypothetical abstraction with one concrete implementation and no consumer benefit is presumptively worse. Domain truth `phi` is not proved by a tooling gate `psi` without a valid `psi => phi` bridge.

### External reference anchors
- Nx official project boundaries: https://nx.dev/docs/features/enforce-module-boundaries (TS ESLint vs language-agnostic Conformance distinction).
- Turborepo task DAG: https://turborepo.dev/docs/core-concepts/package-and-task-graph
- Martin Fowler Strangler Fig: https://martinfowler.com/bliki/StranglerFigApplication.html
- Matt Pocock codebase-design: local `matt-native/codebase-design` Skill, deep-module/deletion-test.
- ECC brownfield-retrospective: local `ecc-native/brownfield-retrospective` Skill; Superpowers verification-before-completion/systematic-debugging.
- Ordivon `.agents/skills/recursive-lego-calculus/SKILL.md`; root `AGENTS.md`. These are decision aids, not added runtime code.
