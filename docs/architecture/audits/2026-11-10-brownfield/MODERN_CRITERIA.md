# MODERN_CRITERIA — 2025–2026 bounded, falsifiable architecture audit

**Phase 0 frozen criteria.** Subject = actual Ordivon Git source `ef17d6879d12faa61fff3bb762b0d500d73c9113`. Each main module is marked `符合 / 部分符合 / 不符合 / 待验证` with one or more real `path:line` and a change/risk disposition, not a popularity score. UNKNOWN must never be called failure or success.

## Established practice used, not copied blindly

- [Nx dependency boundary enforcement](https://nx.dev/docs/features/enforce-module-boundaries): explicit project tags and valid dependency direction. Nx ESLint checks JS/TS; language-agnostic conformance is separate. Here keep `tools/repo/check_owner_boundaries.py` as existing source-native verifier instead of adding an unneeded Nx stack.
- [Turborepo purpose-scoped internal packages](https://turborepo.dev/docs/crafting-your-repository/creating-an-internal-package): apps as entrypoints, real reusable libraries as packages, package dependency graph. Do not force Rust/Python service roots into a TypeScript-only structure.
- [Hexagonal architecture, AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html): ports/adapters only when they avoid concrete infrastructure lock-in. Unneeded adapters introduce maintenance overhead; not every function requires a port.
- [Fowler Refactoring](https://martinfowler.com/books/refactoring.html): small behavior-preserving transformations and demonstrable regression evidence.
- [Diátaxis](https://diataxis.fr/): distinguish current reference, how-to, learning and explanatory/historical materials.
- **Matt Pocock Skills:** `to-spec`, `to-tickets`, `improve-codebase-architecture`, `domain-modeling` and `code-review` two axes (Standards vs Spec); prefer smallest independently reviewable change.
- **ECC:** `brownfield-retrospective` (baseline → historical causal reconstruction → gap register → targeted fix → re-audit), `search-first`, `change-impact`. The missing-feature branch of ECC's four-axis analysis is **out of scope**.
- **Superpowers:** `writing-plans`, `executing-plans`, `systematic-debugging`, `verification-before-completion`. Use existing tests; user forbids adding tests. Do not introduce an extra persistent subagent runtime or approval gate.
- **Mathematics and management:** Hoare triples, rely/guarantee, Liskov substitutability, dependency structure matrix (DSM), strongly connected components (SCC), Parnas information hiding, single-authority source of truth, NASA V&V distinction, Toyota Jidoka and Theory of Constraints.

## Eleven checkable criteria

| ID | Concrete review question | Positive evidence | Counterexample/failure signal |
|---|---|---|---|
| C01 | Does the module own one cohesive domain/physical decision? | owner guide, code and public seam align | one module writes another Owner's truth |
| C02 | Can the cross-Owner dependency direction be enforced? | existing `owners.toml` and `dependency_contracts.toml` checked | undeclared public cross-Owner import |
| C03 | Are apps entrypoints and actual reusable packages bounded? | package manifests + actual imports | duplicated shared business logic in app shells |
| C04 | Is Journal/CAS/write authority unique and types explicit? | distinct Host Work, Runtime Job, Harness Run contracts | dual writer or projection escalated to authority |
| C05 | Do schema/contract/config and current implementation agree? | actual source + current native test/run | stale command, schema mismatch or hidden fallback |
| C06 | Are source, identity, evidence and historical claims immutable where needed? | exact Git SHA/receipt and bounded standing | historical SourceCut rewritten as current, UNKNOWN->PASS |
| C07 | Are dependency cycles and implicit global state understood? | native import/Cargo/TS graph plus runtime refinement | harmful SCC or dynamically mutable process-wide authority |
| C08 | Are duplicate code/resources/legacy paths justified by real consumers? | source + runtime/config/static refs and owner readback | redundant independent writer or dead adapter verified |
| C09 | Do README, ADR, AGENTS and Skills describe current capability? | exact file/CLI/source readback | roadmap presented as installed fact |
| C10 | Does small change preserve existing public behaviour and rollback? | existing tests, exact diff and Git revert | new framework, expanded tests/consumers or semantic drift |
| C11 | Is coupling and maintenance cost controlled by natural owner? | localized changes, DSM/co-change analysis | giant method, shotgun surgery or speculative abstraction |

## Decision and qualification

- `符合`: supported within a stated source/consumer scope by concrete evidence.
- `部分符合`: real existing mechanisms, but incomplete boundary/proof/consumer closure.
- `不符合`: exact source violation, reproducible behavior or native test failure.
- `待验证`: static graph cannot establish it; don't invent outcome.
- Prioritization: BLOCKING = proven harm to existing consumer; HIGH = correctness or unchangeable dependency; MEDIUM = maintainability; LOW = stylistic/representation.
- The contract-preserving goal is `Obs_c(Traces(P_after,E)) = Obs_c(Traces(P_before,E))` for a named current consumer and environment, with explicit UNKNOWN for unavailable installed/external observations. A passing test is a bounded witness, not universal trace equivalence.
- Recursive LEGO R2.1 `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` describes independently contractable responsibility, not a file, script or arbitrary checklist item.
- Default action order `DELETE > REUSE > COMPOSE > REFACTOR > KEEP`, but do not delete merely because static references or line count are zero.
