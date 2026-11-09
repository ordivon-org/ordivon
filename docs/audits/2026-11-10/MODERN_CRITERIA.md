# Ordivon — MODERN_CRITERIA (2025–2026 mature-pattern evaluation)

**Reference model:** Parnas information hiding and design-for-change; hexagonal/clean architecture and dependency inversion where external implementations actually vary; DDD bounded contexts where facts and lifecycle differ; Fowler modular-monolith/CQRS as a localized design choice; Matt deep modules, seam/deletion test; Nx/Turborepo monorepo dependency constraints as *ideas*, not required migrations; PostgreSQL/Alembic/MCP/Git/Systemd as mature native responsibility owners; lean change flow and explicit owner handoffs. Sources listed below.

**Score per module:** `PASS` = current implementation+existing checker/call evidence; `PARTIAL` = visible direction but gaps or manual-only enforcement; `FAIL` = concrete counterexample; `UNKNOWN` = source/installed consumer evidence insufficient. Do not aggregate to invented numerical grades. Each row in AUDIT_REPORT carries file:line and risk.

| ID | Checkable decision question | Required evidence and minimal falsifier | Interpretation / wrong proxy |
| --- | --- | --- | --- |
| C01 | Is each module/domain a coherent changing responsibility? | AST/import and callers; two unrelated change-reasons in one public surface as counterexample. | Domain-first is not mandatory directory structure; depth and locality count. |
| C02 | Are dependency directions actually enforced? | Actual Python/TS/Rust imports and root `check_owner_boundaries.py`, `affected_owners.py`, `owners.toml`; demonstrate violating import rejected. | `AGENTS.md` prose alone cannot earn PASS; Nx tag rules are analogy. |
| C03 | Is the module interface smaller and more stable than the implementation? | Exported symbols, external call sites, Matt deletion test. | File lines, adapter count and interface-to-code ratio are weak proxies; 15-line facade may be useful. |
| C04 | Are real state and fact owners unambiguous? | PG Journal tables, service stores, Runtime/Host/Harness/Catalog roles, single-writer evidence. | One Git repo does not imply one DB/transaction owner. |
| C05 | Are immutability, CAS, and effect semantics explicit? | Version expectations, receipts, immutable source/digest, transaction frame conditions; attempt/tool result vs domain outcome. | A test PASS cannot certify installed or business result. |
| C06 | Are configs, schema, published contracts and source aligned? | Alembic heads, source schema, MCP `tools/list`, manifests, uv/pnpm/Cargo lock, packaging. | A historical schema_version or planned route is not installed truth. |
| C07 | Is sharing based on real multi-consumer leverage and stable semantics? | Two independent consumers and dependency count; verify no internal import break. | Shared tree location not enough to justify generic package. |
| C08 | Does the repository avoid dead code/duplicate logic and unneeded seams? | All-file hash scan; AST call/import graph; actual dynamic consumers, data lineage and tests; deletion test. | No static import ≠ dead; exact identical bytes ≠ no distinct owner. |
| C09 | Are entrypoints and docs faithful to current capability? | README/AGENTS/ADR content vs actual modules/MCP/native commands; SourceCut and currentness. | Dated roadmap/release receipts must not masquerade as current authority. |
| C10 | Can work be localized, reversed and published without cross-owner drift? | Current PR overlap, surgical diff, separate worktree, Git rollback, native owner verification. | One global mega-PR or silent overwrite fails even with many green tests. |
| C11 | Is the abstraction/proof level appropriate to real hazard? | R2.1 11 fields only for independently contractable LEGO; explicit Hoare/A-G/refinement gap, evidence tiers; model negative control. | Formal theorem or plan can never alone prove SQL implementation or installed effects. |
| C12 | Do engineering processes reduce actual WIP and cost without replacing work? | Matt source-specific review; ECC four-axis gap register; Superpowers source plan + existing verifier, Space handoff; time/coupling benefit. | Hooks/rules must reuse actual host environment; a new process gate is not an improvement. |

## Decision thresholds

`FAIL` under C02/C04/C05/C06 with real effect risk merits `P0` or `P1` and owner-level repair. A weak doc or unneeded historical mirror is `P2/P3` unless it actively misleads publication. A large file is a **review hotspot**, not a violation. `UNKNOWN` never automatically triggers a deletion or a new test.

## External source pointers (evaluated during this task)

- Nx: https://nx.dev/docs/features/enforce-module-boundaries — tags + ESLint import constraints; language-agnostic conformance is a separate commercial capability, so do not pretend it applies to this Rust/Python/TS monorepo by default.
- Matt: https://github.com/mattpocock/skills/blob/main/docs/engineering/codebase-design.md — module/interface/depth/seam/leverage/locality and deletion test.
- Superpowers: https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md ; https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md — precise plan then existing verification.
- ECC: https://github.com/affaan-m/everything-claude-code — composable rules/skills/hooks; adapt only to actual Ordivon native owner methods.
- Parnas (1972): https://doi.org/10.1145/361598.361623 ; Martin Fowler CQRS (bounded use): https://martinfowler.com/bliki/CQRS.html ; PostgreSQL isolation: https://www.postgresql.org/docs/current/transaction-iso.html ; Alembic: https://alembic.sqlalchemy.org/en/latest/ .

**Do not add Nx, Turborepo, or ECC hooks just to obtain a modern-looking directory.** Evaluate current native enforcement and reuse before introducing dependencies.
