# Modernization criteria | 2025-2026 mature practice

A result is classified PASS / PARTIAL / FAIL / UNVERIFIED **per natural Owner and actual source/consumer**. A pattern is not an obligation to create another service or another file.

| # | Checkable condition | Native observation and failure signature | Theory / upstream practice |
| --- | --- | --- | --- |
| C01 | Responsibility and domain-first decomposition | Owner manifest vs src and README; one durable fact/effect has one natural owner; modules change for one reason | DDD bounded context; Team Topologies; Parnas information hiding |
| C02 | Enforceable dependencies and direction | Existing tools/repo/check_owner_boundaries.py and dependency_contracts.toml; reverse private import and undocumented seam are failures | Nx enforce-module-boundaries **principle**, not an Nx installation |
| C03 | Deep modules over wrapper proliferation | Inspect public surface vs internal complexity; use Matt deletion test: if removed, does complexity collapse behind existing seam or spread to callers? | Matt improve-codebase-architecture; Ousterhout deep modules |
| C04 | Ports and effect boundaries | Public API, type, schema and actual adapter; policies separate from effects; no importing sibling Owner implementation internals | Clean/Hexagonal; dependency inversion |
| C05 | Durable truth and state transitions | Host Work Journal/CAS, Runtime Job/Attempt, native PG migrations, exact idempotency and replay; no duplicated source of truth | State machine refinement; Hoare pre/post; bounded-context aggregates |
| C06 | Current schema, version and migrations | Compare source schema/manifest/MCP contracts to code; distinguish source-vs-installed; migration state is not README state | Database evolution; contract-first; provenance |
| C07 | Evidence and decision provenance | Claim is bound to subject, revision, currentness, observer and consumer; SOURCE != MERGED != INSTALLED != DOMAIN_ACCEPTED | Reproducibility; distributed effect semantics |
| C08 | Dead/redundant code genuinely unconsumed | Git history, static imports, dynamic lookups, config, installed jobs, external links; zero grep alone is not proof | Mark/sweep reachable roots; mature package manager prune |
| C09 | Coupling, cycles and change propagation | Typed dependency graph SCC, module changes/hotspots, active effect consumers; no decomposition solely by file length | MIT design-structure matrix; change-impact analysis |
| C10 | Native build and tooling boundaries | Owner local uv/Cargo/pnpm/mise/lockfiles; root only routes checks; no duplicate global install/scheduler | Turborepo workspace package boundaries; modular monolith |
| C11 | Accurate navigation and decision records | README/AGENTS/ADR describe actual executable interfaces and current claims; superseded plans removed/archived in Git | Diátaxis; Matt domain-modeling; ADR decisions |
| C12 | Small reversible source-only delivery | Git source cut, isolated worktree, inspected diff, existing Owner checks, CI/merge state and rollback; no new features/tests/consumers | Superpowers verification-before-completion; ECC change-impact; Google code-review |

## Decision rules

DELETE if a current consumer no longer needs the carrier and unique provenance remains accessible via the actual owner/Git; MERGE only if behavior/effects/authority are contextually equivalent; FIX misleading or broken existing boundaries; SIMPLIFY without growing APIs; KEEP unique assets, actual protocols, independent licensed content and current effect/trace obligations; mark UNKNOWN for one precise unobserved edge. UNKNOWN is not a general veto. Comparing imports or exact byte hashes is a *screen*, not an equivalence theorem.

Do not impose an Nx/Turborepo installation on a Rust/Python/TypeScript modular monorepo with existing native boundary contracts. ECC hooks or imported CLI events are **optional contingent implementations**, not justified by this source-only audit. Likewise Matt's architecture survey is analysis, not automatic permission to create more modules.

## Upstream reading (dated 2026-11-10)

- Nx: https://nx.dev/docs/features/enforce-module-boundaries (tagged graph constraints; JS lint, separate language-agnostic enterprise conformance).
- Turborepo: https://turborepo.com/docs/crafting-your-repository/structuring-a-repository (workspace-owned packages, boundaries).
- Matt: https://github.com/mattpocock/skills/blob/main/docs/engineering/improve-codebase-architecture.md (deep module, change hotspot, deletion test) and https://github.com/mattpocock/skills/blob/main/docs/engineering/domain-modeling.md.
- Superpowers: https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md and https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md (root cause before fix, actual verification evidence).
- ECC: https://github.com/affaan-m/ECC (selective hooks/rules/memory; not adopted wholesale).
- Google: https://google.github.io/eng-practices/review/reviewer/looking-for.html (correctness, comprehensibility, complexity).
- Fowler: https://martinfowler.com/books/refactoring.html (behavior-preserving change).
