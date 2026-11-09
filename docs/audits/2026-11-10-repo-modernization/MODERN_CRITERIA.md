# Modernization criteria: twelve checkable source/Owner predicates

**SourceCut:** `ef17d6879d12faa61fff3bb762b0d500d73c9113`. Mark `C` verified conforming for stated evidence scope, `P` partial, `N` witnessed nonconformance, `U` insufficient evidence. There is **no composite vanity score**. Do not falsely equate native code checks with deployment or business acceptance.

| ID | Checkable engineering property | Existing positive witness | Falsifier / minimal correction |
|---|---|---|---|
| M01 | Folder maps to a concrete reason-to-change, not just technical layering | `tools/repo/owners.toml`, each Owner source/README | cross-owner implementation mixed behind unqualified directory -> restore natural owner |
| M02 | Dependency direction through public seam rather than private impl | `check_owner_boundaries.py`, `dependency_contracts.toml` | undeclared private import -> use existing public port or remove dead call |
| M03 | Core domain rules not coupled to storage/HTTP/UI adapters | Owner `src/` and actual import graph | rule imports concrete adapter -> invert existing dependency |
| M04 | Truth, state, identity and effect have a single natural Owner | Host/Runtime/Security/Workstation source authority | Job exit reported as Work completion -> correct existing implementation or wording |
| M05 | Versioned schema/contract matches real producer/consumer | Owner `pyproject.toml`, `Cargo.toml`, `package.json`, JSON Schema | version mismatch or orphan schema -> repair existing contract |
| M06 | Generic behavior delegated to upstream mature provider | Git/systemd/Ansible/Nix/DSC/OpenTofu/Temporal/PostgreSQL | locally invented controller duplicates native capability without unique claim -> delete/compose |
| M07 | Modules are *deep*: complex behavior behind smaller stable surface | Matt deep module deletion test; actual callsite count | removing adapter moves more complexity into callers -> KEEP or deepen not blindly delete |
| M08 | CI/source guards are existing, discriminating and in sync with docs | `mise run repo:ci`, original boundary checker | standing docs cite obsolete measured counts -> repair source-bound currentness |
| M09 | Typed public dependency graph has no unjustified cyclic authority | 31 declared seam edges, SCC of named owner pairs | live private import cycle and no protocol boundary -> correct seam |
| M10 | README/ADR/Agent discovery states current not historical wish | exact source and native entrypoint, version/dates | stale dated facts promoted to today's installed state -> mark history or remove |
| M11 | Dead/duplicate/code-history classification uses real consumers | Git source refs + installed process + source digest + original verifiers | `rg` absence alone used to authorize delete -> UNKNOWN, obtain actual consumer |
| M12 | Each refactor is reversible, scoped and independently verifiable | isolated Runtime worktree, original tests, Git commit/PR | mixed move/API/DB/release changes in one patch -> split by natural owner |

## Mathematical and management foundations

- Parnas information hiding: modules split by **reasons for change**. Clean/Hexagonal/DDD are responsibility guides, not folder-name requirements.
- For compatible assume–guarantee contracts, candidate must not strengthen assumptions or weaken required guarantees, with the actual behavior universe and effect/observer side conditions. R2.1 eleven coordinates apply only to **independently declared semantic LEGO**.
- Graph-theoretic SCC on declared source seams proves no cycle in that **projection**, not in all dynamic imports and RPC calls.
- Theory of Constraints, Lean and organizational cybernetics favour eliminating the dominant wrong-owner or stale-evidence bottleneck before adding another quality framework.
- Matt `improve-codebase-architecture` is a survey/deep-module deletion test, not permission to refactor every large file. ECC `search-first`/`verification-loop` and Superpowers `writing-plans`/`verification-before-completion` reuse Ordivon's existing git/mise/CI; they do **not** create new hooks, tests or orchestration this pass.

## Verified external references

- Nx official source boundaries: https://nx.dev/docs/kb/enforce-module-boundaries . Its language-agnostic Conformance feature is a separate **Nx Enterprise** option; do not claim it is already available.
- Microsoft DDD dependency direction: https://learn.microsoft.com/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/ddd-oriented-microservice .
- Matt original architecture survey: https://github.com/mattpocock/skills/blob/main/docs/engineering/improve-codebase-architecture.md .
- Superpowers writing and executing plans: https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md and https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md .
- ECC methods: https://github.com/affaan-m/everything-claude-code .
- Parnas: https://doi.org/10.1145/361598.361623 .
- Project-native Skills: `.agents/skills/{systems-engineering,design-structure-matrix,recursive-lego-calculus,compositional-contracts,method-router}/SKILL.md`.
