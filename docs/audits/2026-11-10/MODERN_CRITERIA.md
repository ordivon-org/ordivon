# Checkable 2025–2026 Architecture Criteria — Frozen Phase 0

Evaluate each Owner module with **PASS / PARTIAL / FAIL / UNKNOWN** plus exact source path:line and one relevant consumer/proof. Do not average labels into a fake universal quality score. Appropriate architecture differs across domains: a domain-first service can still use technical layers internally; a Godot scene isn't a Python package.

| ID | Falsifiable criterion | Source-based method / natural mature reference |
| --- | --- | --- |
| C01 | Owner boundaries correspond to state/effect responsibility, not merely directory or fashion; bounded contexts have one canonical authority | DDD Bounded Context, Parnas information hiding; `tools/repo/owners.toml` and Owner API |
| C02 | Imports and calls obey intended direction; no unintended circular dependencies / private cross-Owner imports | Nx `enforce-module-boundaries` model; existing `tools/repo/check_owner_boundaries.py`, static imports, real dynamic traces |
| C03 | Application/API adapters remain thin and do not duplicate domain semantics or PG transactions | Clean/Hexagonal Architecture, Ports & Adapters; actual call sites and state writes |
| C04 | Interfaces hide meaningful complexity and reduce change propagation; extracted helpers do not just relocate complexity | Ousterhout deep modules; Matt `improve-codebase-architecture` deletion test and recent-change coupling |
| C05 | Shared modules are demonstrably shared with compatible assumptions; avoid fake cross-Owner common abstractions | Modular monolith & information hiding; two real consumers/ports before sharing |
| C06 | Status, identity, time, evidence and source currentness have explicit canonical owners; no implicit truth promotion | Journal/CAS, event sourcing, immutable snapshots, formal refinement; Host/Runtime/Git/Artifact |
| C07 | Config, schema, build definitions and current docs match implementation and installed contract; historical evidence remains history | ADR + schema/evidence first; native schema migrations, current installer and exact source SHA |
| C08 | No demonstrated dead/obsolete source, circular self-sustaining wrappers, or redundant implementation of one responsibility | ECC refactor-clean / root-based reachability; distinguish static, dynamic and generated entrypoints |
| C09 | Error/retry/recovery and side effects have one Owner; no hidden global state/shared mutable data crossing contracts | Hexagonal ports + effect system / Hoare frames; PG transaction and Runtime state machines |
| C10 | Domain-first navigation makes an Agent/Human locate owner, entrypoint, contract and operations without parallel “current” plans | feature/domain-first modular monolith + Diátaxis; `AGENTS.md`, `README.md`, `docs/start` |
| C11 | Native CI/lint/dep constraints already constrain important violations; no new duplicate toolchain in this freeze | Nx tags and lint, Turborepo task graph analogy, Owner `mise`; explicitly mark source/import vs runtime gaps |
| C12 | Source change is rollbackable, can preserve prior behavior, and materially reduces maintenance toil/coordination WIP | Fowler small behavior-preserving refactors, Superpowers verification-before-completion, SRE eliminate-toil and Theory of Constraints |

**Correct mathematical use:** formal LEGO `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` for independently *declared* responsibilities, not every file. In a fixed behavioral universe, assume–guarantee refinement requires no stronger admissible-environment assumptions and no weaker saturated guarantees; don't claim model proof implies source refinement or deployed consumer acceptance. Independent identity and effect provenance remain intact.

**External methods adopted selectively:** Matt Pocock `improve-codebase-architecture`, `codebase-design`, `domain-modeling` → hunt changed code and apply deletion test; ECC `refactor-clean`, search-first, narrow quality verification → existing Owner only, don't install hooks blindly; Superpowers `writing-plans`, `executing-plans`, `systematic-debugging`, `verification-before-completion` → actual command outputs and conservative source diffs, with user’s explicit ban on adding tests respected. Upstream instruction text is a method reference, never authority to run broad hooks.

**Official references:** https://nx.dev/docs/features/enforce-module-boundaries ; https://turborepo.com/docs/crafting-your-repository/structuring-a-repository ; https://github.com/mattpocock/skills/blob/main/docs/engineering/improve-codebase-architecture.md ; https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md ; https://github.com/affaan-m/ECC ; https://martinfowler.com/books/refactoring.html ; https://sre.google/workbook/eliminating-toil/ ; Parnas (1972) DOI:10.1145/361598.361623.

**Non-claims:** A score, import graph, copied checksum, passing build or generic AI review cannot establish external consumer absence, installed semantic success, or a proof of stable architecture.
