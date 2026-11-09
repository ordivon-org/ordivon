# Ten checkable modern architecture criteria

Use PASS / PARTIAL / FAIL / UNKNOWN. Score is not a proxy for usefulness. Every adverse claim must cite a current source path and exact observed consequence. Do not conflate historical notes with current source.

| ID | Check | Grounded method / mature project |
| --- | --- | --- |
| C01 | Owner/domain responsibility is clear, and one fact/effect has one natural authority | DDD bounded contexts, Parnas information hiding, R2.1 |
| C02 | Dependency direction is demonstrated in current imports/manifests and enforced where owner needs it | Clean/Hexagonal Architecture, Nx tag dependency constraints, existing Ordivon owner boundary checks |
| C03 | Interfaces are deeper and more stable than thin wrappers; cross-module changes follow volatility | Parnas 1972, Modular Monolith, Matt improve-codebase-architecture deletion test |
| C04 | Journal/CAS, source digest, state and receipts have exact source/currentness/atomicity contracts | Hoare/Assume–Guarantee, event sourcing, NASA V&V |
| C05 | Schema/lifecycle/contract/config/lockfiles agree with actual code and real CLI | JSON Schema, Cargo/uv/pnpm lockfiles, R2.1 identity and provenance |
| C06 | Standard tools/providers used wherever they fully serve real consumers | DELETE-CUSTOM → REUSE → COMPOSE, OCI/ORAS/Zot, in-toto/SLSA, BuildKit/Nix |
| C07 | Unconsumed custom implementation/history/prototype material is retired rather than endlessly wrapped | Lean waste, Theory of Constraints, Git history and reversible commits |
| C08 | Domain-first navigation, scoped AGENTS/README/ADR and true current versus historical facts are discoverable | ISO/IEC/IEEE 42010, Matt domain-modeling |
| C09 | Existing native verification and rollback are known; no new test/consumer lines for cleanup | Superpowers verification-before-completion, systematic-debugging, Matt two-axis review |
| C10 | Module coupling/cycles, concurrent PR overlap and excessive conservative approval cost are addressed | MIT DSM, Goldratt TOC, R2.1 typed UNKNOWN |

Sources and applicability:
- Nx official module boundary constraints: https://nx.dev/docs/features/enforce-module-boundaries — reuse the enforcement pattern, do not install Nx into Rust/Python merely for this review.
- Turborepo internal packages: https://turborepo.dev/docs/core-concepts/internal-packages — apply only to workspace boundary thinking; Ordivon is polyglot.
- Parnas, On the Criteria To Be Used in Decomposing Systems into Modules, DOI:10.1145/361598.361623.
- ISO/IEC/IEEE 42010 and NASA Systems Engineering Handbook; verification is not validation.
- MIT DSM: graph edges must be evidence-supported, not appearance-based clusters.
- Cousot abstract interpretation: bounded proved state is not physical or domain truth.
- BuildKit, Nix, Bazel: declare input/dependency closure when a consumer actually requires it; do not build another CAS/scheduler.
- Matt skills: to-spec, to-tickets, improve-codebase-architecture, domain-modeling, code-review. Use current repo glossary, existing seam and deletion test.
- Superpowers: writing-plans -> executing-plans, verification-before-completion and systematic debugging; use isolated worktree and real existing gates.
- ECC: brownfield context/quality/feedback ideas; do not install mandatory global hooks, another Skills router, memory or governance authority.
