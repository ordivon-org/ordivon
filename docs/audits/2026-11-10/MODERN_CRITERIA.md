# MODERN_CRITERIA — 12 checkable modernization conditions

Judgment per module: CONFORMING (positive current source evidence), PARTIAL (missing direct behavior/refinement evidence), NONCONFORMING (specific counterexample), UNKNOWN (insufficient), N/A (outside role). Ratings are not numerical quality scores.

| ID | Criterion | Condition | Evidence hook | Pattern |
|---|---|---|---|---|
| C01 | Parnas information hiding | Single owner of one volatile design decision | AGENTS/README; public import/API; source implementations | Parnas 1972 |
| C02 | DDD bounded context | Work/Job/Run/Principal are separate domain identities and stores | PG migrations; schema; source IDs | DDD |
| C03 | Clean/Hexagonal direction | domain code does not import transport/deployment details backwards | Python imports; Rust crate dirs; owners.toml | Hexagonal |
| C04 | Enforced module boundaries | cross-owner dependency direction is checked by extant source rules | tools/repo/check_owner_boundaries.py; dependency_contracts.toml | Nx boundaries |
| C05 | Deep modules and thin entrypoints | public surface is smaller and stable; no fake shared lib | pyproject; API; CLI; modules | Turborepo; Matt |
| C06 | Journal and CAS coherence | distinct owner of immutable history, mutable current pointer, effect receipt | Host Work; Runtime Attempt; Harness Journal | A/G; PG |
| C07 | Schema/config aligned | migrations, schemas, dependency locks and actual code agree | alembic; schemas; pyproject; mise; Cargo | contract-first |
| C08 | No duplicate/legacy mechanism | new implementation truly retires replaced old code | path/grep/AST/import readers | Fowler Strangler |
| C09 | No avoidable cycles/global state | module dependency cycles and hidden process-global mutation reduced | AST graph; owner refs; module code | DSM; modular monolith |
| C10 | Native tool reuse | prefer systemd/PG/Git/uv/Cargo/pnpm to custom control wrappers | unit files; db; tools scripts | Google SRE toil |
| C11 | Current documentation | README, AGENTS and ADR describe actual executable API and release | git grep; existing checks; installed version | ECC; Matt |
| C12 | Evidence and reversible delivery | fixed SourceCut, scoped claims, native tests and Git rollback | git diff; PR; owner verify; runtime readback | Superpowers; R2.1 |

## Mature external references and transfer bounds

- Parnas: https://doi.org/10.1145/361598.361623 — design by independent decisions, not files-per-module.
- Nx: https://nx.dev/docs/features/enforce-module-boundaries — JS/TS lint tags and optional enterprise language-agnostic conformance; existing Ordivon Python/Rust checks take precedence, do not introduce Nx.
- Turborepo: https://turborepo.dev/docs/core-concepts/package-types — deployable apps are graph leaves, internal libraries are real shared code, not a mandate to migrate all state into packages.
- Fowler: https://martinfowler.com/articles/2024-strangler-fig-rewrite.html — when replacement is consumed, actually retire the legacy path.
- Google SRE: https://sre.google/workbook/eliminating-toil/ — eliminate the causes of recurrent maintenance toil rather than building toil-management machinery.
- Matt Skills: improve-codebase-architecture (deep modules/deletion test), domain-modeling (bounded vocabulary), code-review (Standards and Spec separately).
- ECC brownfield-retrospective: reconstruct actual code decisions and classify Thinking/Coding/Missing/Technology without adding missing product features in this scope.
- Superpowers: writing/executing plans, systematic debugging and verification-before-completion. Existing source consumers validate; no new tests.
- Recursive LEGO R2.1: only formally declared independent responsibilities receive all 11 coordinates, not every file. The Lean model does not certify deployed behavior.

## Decision standard

A finding must identify a real path, source failure mode, recommended KEEP/MERGE/MODIFY/DELETE, and risk. A missing static reference is insufficient for declaring no runtime consumers. All source-state claims are scoped to the pinned Git SHA.
