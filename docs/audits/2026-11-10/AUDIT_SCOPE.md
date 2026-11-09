# Ordivon — AUDIT_SCOPE (2026-11-10)

## Phase 0: frozen source and execution contract

- **SourceCut**: `ef17d6879d12faa61fff3bb762b0d500d73c9113` (GitHub main, observed this turn). Candidate worktree: `ws-gpt6-repo-brownfield-full-audit-20261110-r1` from `/root/projects/ordivon`, separate from shared primary checkout.
- **Owner map**: `tools/repo/owners.toml` schema_version 1; **21** declared natural owners. This is repository-mechanics navigation, not a domain authority or additional Work registry.
- **Observed scope**: `git ls-files -z` returned **5002 tracked paths** under `.agents`, `.github`, `apps`, `capabilities`, `catalogs`, `docs`, `domains`, `extensions`, `packages`, `platform`, `profiles`, `services`, `studies`, `tests`, `tools` and root configs. Physical caches, Git object store, envs, and untracked/installed data are outside the tracked-file ledger; do not confuse absence from Git with physical non-existence.
- **Exact claimed level**: per-file path, bytes, SHA/extension/heuristic role and owner coverage; selective human-source-semantic inspection of critical modules, public interfaces and high-risk claims. A mechanical scan is not 5002 independent semantic proofs.
- **Approved language/tool scope**: Rust, Python, TypeScript (specialized formal, policy, DB and engine languages remain valid); per-owner Cargo/uv/pnpm; real PostgreSQL/Alembic/MCP/Systemd native owners; no common lockfile rewrite.
- **Production and lifecycle**: this audit reads Git source. PostgreSQL schema head, installer release source, systemd live unit, Runtime Journal and actual domain outcomes must be independently read from each owner. `migrations/versions/0013_unicode_substring_gin.py` is the Host source migration head, NOT proof of currently installed PG schema. Any `schemaVersion` in a JSON plan is that document's contract version, NOT a universal service schema.
- **Phase ordering**: P0 boundary and 12 criteria; P1 full source-tree evidence; P2 module-level finding with exact location and uncertainty; P3 executable change/rollback; P4 only already-present implementation cleanup and existing native checks; P5 update baseline and actual PR status. No work starts on shared main checkout.

## Explicit non-goals and hard exclusions

No feature additions, new tests/test infrastructure, no new external consumer route, product canary, software platform, universal LEGO kernel, new policy gate, extra auditing/approval service, or weak-model trials. Do not alter production DB, Finance funds, OS Network routes, Systemd services, active Runtime Workspaces, or historical Event/Work identities as part of source cleanup.
Use `DELETE-CUSTOM → REUSE → COMPOSE` when a specific retained responsibility is genuinely redundant; otherwise leave a justified KEEP or UNKNOWN. Review active source consumer, non-code dynamic use, published contract, snapshot provenance and rollback before deletion.

## Current overlapping work (read-only, no competing changes)

- `#2012`: existing repo-wide brownfield execution spec and `tools/repo/exhaustive_coverage.py` with tests. Do **not** edit or add parallel source indexing/verifier code.
- `#2010`, `#2013`, `#2006`: overlap `docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md`; do not alter that file.
- `#2016` Host; `#2015` and `#2009` Harness; `#2011` Skills MCP; `#2008` Workstation; `#2004` Data; other Owner PRs. Do not copy or override their pending implementations.
- Distinct output for this user-defined audit is restricted to `docs/audits/2026-11-10/` and only a demonstrably unowned source-path cleanup if discovered and existing verification proves it.

## Evidence sources and semantic owners

- Owner inventory and verify commands: `tools/repo/owners.toml`, root `AGENTS.md`, README, each Owner README / closest AGENTS.md. Root check: `mise.toml` -> existing `repo:ci`; use narrow native checks when root CI blocks on unrelated environment.
- User/domain role: Runtime (Workspace/Job/Attempt), Host (Work/Space/Topic/Message), Harness (Agent-run/tool cycles), Gateway (northbound adapter), Security (authz/identity), Network (egress), Workstation (installation), Artifact (bytes/provenance), Composition (typed contracts), Capital/Game/Media/Data (domain-specific), web (UI).
- Agent coordination: existing Space `space:ordivon-task-portfolio-and-proof-gates-r1:20261101`, topic `topic:ordivon-task:agent-text-contract-cross-audit:20261109`; kickoff Message sequence 25960. Message ≠ merge/installation/final proof.

## Source/impact discipline

Each finding must show `file:line`, actual current code or manifest evidence, currentness tier, severity and reason, natural owner, action/retained contract, risk and rollback. For docs/obsolete plans use precise Git source identity; if a property cannot be proven without live producer access, mark `UNKNOWN`, never `FAIL` or `PASS` by assumption.
Baseline after audit is a **source PR** state, not live deployment; `BASELINE_AFTER_AUDIT.md` must distinguish SOURCE/COMMIT/PR/MERGED/INSTALLED/CONSUMED.

## Reproduction

```sh
git rev-parse HEAD
git ls-files -z
git status --porcelain
cat tools/repo/owners.toml
git diff <sourcecut>...HEAD --name-status
```
