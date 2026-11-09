# Audit scope | Ordivon brownfield modernization | 2026-11-10

**Frozen source:** ef17d6879d12faa61fff3bb762b0d500d73c9113
**Real root:** /root/projects/ordivon (Runtime Linux, isolated source Workspace).
**Repository owner schema:** tools/repo/owners.toml, schema_version=1, with 21 natural Owners.
**Tracked file observation:** 5002 files; exact bytes, paths and digests read from the frozen Git tree.
**Not claimed:** The file census is mechanical; it does not prove 5002 individual semantic reviews, actual installed source, or domain acceptance.

## Boundary and excluded change

The system of interest is the existing modular Ordivon monorepo: services/ (Runtime, Host, Harness, Gateway), platform/ (Network, Workstation, Security), packages/ (Composition, Data), capabilities/ (Artifact, Media, Preservation, Distribution), domains/ (Capital, Game), catalogs/, apps/ (Web, Chaoxing), extensions/, profiles/, studies/, docs/, .agents/ and root tooling. The recognized truth owner is the natural domain/platform owner, not a root presentation document.

Current task is **observe -> judge -> plan -> subtract or repair -> verify current consumers**. Allowed: removal of dead/superseded code or prose, consolidation of truly equivalent responsibilities, behavior-preserving refactoring, correction of stale documentation/contracts. Excluded: new product feature, test *expansion*, new consumer wiring, new policy/Agent/Registry, reinstallation of Matt/ECC/Superpowers runtimes, weak-model comparisons and destructive live-state cleanup unrelated to a proven retired consumer.

## Real version and lifecycle facts

- Host: services/host/pyproject.toml declares ordivon-host-v2 v0.8.0; Alembic source versions/0001 through versions/0013; this is a **source migration ceiling**, not proof that production databases are at 0013.
- Runtime: services/runtime/Cargo.toml Rust workspace; core migrations/runtime/0001 through 0006 plus pg_fresh_epoch.sql; actual PG/SQLite runtime selection must be separately checked on installed nodes.
- Harness: services/harness/pyproject.toml declares v0.6.0.
- Gateway: services/gateway/pyproject.toml declares v0.10.8.
- Web: apps/web/package.json declares v0.1.0 with Node/TypeScript and SQLite **canary**; its local state boundary is not automatically a violation of platform PostgreSQL usage.
- Owner manifest is a mechanical routing map (21 entries), not 21 identical schema versions. Git, PG, systemd, MCP and user/domain observations have distinct truth scopes.
- Existing boundary checker: tools/repo/check_owner_boundaries.py; at source it reports 2,320 active files, 10 packages, 31 declared seams and 38 references. Existing architecture check: tools/repo/check_architecture_docs.py. Both passed pre-edit source scan on the frozen revision.

## Source and coordination

Read root AGENTS.md, closest available Owner AGENTS/README, exact source, imports and real clients. Record each deletion's observed consumers and effect/rollback. Concurrent source work at snapshot: PR #2006, #2010 and #2014 overlap existing architecture programmes; PR #2017 owns Chaoxing retirement; PR #2008 Workstation historical projection; PR #2015 Harness historic runner removal; PR #2007 Distribution evidence; PR #2011 Skills dependency reduction; PR #2012 Repo inventory. Do **not** independently reapply those changes. PR states are time-sensitive; re-fetch before merge.

This is a **dated audit observation**, not a new source of operational truth, owner, API or long-lived Agent policy. Source of plan coordination remains the existing [Issue #1964 R4](https://github.com/ordivon-org/ordivon/issues/1964#issuecomment-6747472263).

## Phases and scope status

P0 completed for actual source/manifest/criteria and selected schema history. P1 completed as mechanical all-file census, with detailed semantics for selected modules only. P2 staged findings in AUDIT_REPORT.md. P3 executable per-source tasks in REFACTOR_PLAN.md. P4 current source edits must carry Git diff and existing native verification. P5 BASELINE_AFTER_AUDIT.md distinguishes completed/blocked work; it cannot claim whole-repo semantic convergence without full evidence.
