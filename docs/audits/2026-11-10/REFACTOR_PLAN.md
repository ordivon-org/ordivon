# Stock-only refactor execution plan

**Accepted scope:** delete/merge/fix/behavior-preserving code modernization, no new feature, no new test, no new consumer route. SourceCut is in AUDIT_SCOPE.md. Every task below carries a native Owner and a rollback path; this file is a *dated plan*, not a second work authority.

## R0 — Resolve concurrent active plans, before editing shared files

- Owner: repository architecture coordination; target existing Owner programme and Agent contract docs.
- Inspect: GitHub PR #2006, #2010, #2014; compare exact tree diffs and known consumers at docs/start/tasks.md and method-router. Existing #2006 and #2010 overlap the Owner programme, so select exactly ONE current form.
- Action: coordinate original PR authors to drop overlapping second implementation; do not open third competing PR.
- Verify: current GitHub original PR checks and full changed-path diff; read current main after merge.
- Rollback: Git revert of actual merged change. Risk: losing unique Owner requirements when overwriting.

## R1 — Retire stale Agent plan (after R0 author decision)

- Owner: repo docs; source: docs/architecture/AGENT_OUTCOME_CONSTRAINT_EXECUTION_SPEC_R1.md.
- Independent source review confirmed old 220-line speculative plan has no identified necessary internal consumer; canonical AGENT_CONTRACT_EXECUTION_SPEC_R1.md and AGENT_OUTCOME_REALIZATION_R21_SPEC_20261109.md preserve current and historic unique obligations.
- Action: reuse existing PR #2010's deletion only; do not duplicate. If full CI cannot run because jobs were abandoned, repair/rerun the existing workflow, not write new tests.
- Verify: git grep with actual dynamic Skill catalog and root architecture source checker; current methods point to canonical. Rollback: Git restore from frozen SHA.
- Risk: external bookmarks not visible to source; no fake compatibility document.

## R2 — Audit Repo's deep modules before moving any lines

- Owner: tools/repo.
- Inputs: check_architecture_docs.py (2,524 lines), exhaustive_coverage.py (2,052), convergence_plan.py (1,025), check_owner_boundaries.py and dependency_contracts.toml.
- Test Matt deep-module deletion condition and Parnas reason-for-change; find actual root CI/Owner route call graph, duplicated decisions and effects. A long file is a review pressure signal.
- Action: remove ONLY a proven dead/unreachable responsibility or merge duplicated policy in existing carrier; no extra lint framework, root registry or test file. Work with #2012/#1999 Owner before touching overlapping source.
- Verify: existing python source checks and native repo:ci; rollback: single-file Git revert.
- Risk: Root checks can falsely stop all Owners if mis-refactored.

## R3 — Review Web's existing 35 files (no speculative packages)

- Owner: apps/web, no active overlap with refactor PRs at source cut.
- Real files: src/app.ts 721 lines, src/store.ts 810, src/store-sessions.ts, src/store-agent-grants.ts, src/webauthn.ts, src/server.ts 20.
- Confirmed negative source observation: with ORDIVON_WEB_PORT=8080garbage, src/config.ts:Number.parseInt accepted 8080. Replace permissive parsing with strict decimal syntax and Number.isSafeInteger; no new test file. Preserve documented existing positive integer contract.
- Confirmed equal effect digests: src/agent-authority.ts:stableEffectDigest and src/identity-digests.ts:stableDigest both SHA-256 JSON.stringify with sha256: prefix; only app.ts has the two caller references. Remove redundant implementation and import existing stableDigest directly.
- Preserve the actual SQLite canary domain truth and Security-owner protocol verifier seam; do not impose a new packages/ split by appearance.
- Existing check: run Node direct positive/negative config probes, pnpm in the Owner's mise context for typecheck and test, no new tests; rollback: Git revert.
- Risk: WebAuthn, effect approvals, replay guards, CSRF/Origin subtle semantics.

## R4 — Let existing natural Owners retire their own known legacy

- Chaoxing: #2017 for fake 11-file MVP, with installed/remote consumer check.
- Harness: #2009/#2015 for historical A/B runner code, retain unique replay evidence where consumed.
- Workstation: #2008 for Host-v1 projector, do not delete original PG/archive obligations.
- Distribution: #2007, distinguish obsolete evidence wrappers from unique release receipts.
- Skills/Data/Host: #2011/#2004/#2016, respectively.
- Every such PR must carry native verification, current SourceCut, deletion diff, rollback. No parallel root cleanup for the same file.

## R5 — Other Owners, scoped per-file coverage

- Group by actual Owner in INVENTORY.md; inspect code imports/public APIs/installed or dynamic consumers, classify each as KEEP, REMOVE, FIX, MERGE, UNKNOWN at the natural responsibility level.
- Compare mature tool: Git for worktree/history, PostgreSQL/Alembic for Host ledger, Rust typed state for Runtime, Node package manager for Web, systemd/Windows for services, OCI/FFmpeg for Artifact/Media. **Reuse existing capabilities** rather than installing Nx or broad ECC hook framework.
- Must capture exact path/line/source, effect/caller, native check and risk for each material refactor; skip work with no established benefit.
- Cross-Agent handoff: STATUS; DONE; SOURCE/PR; OWNER/CONSUMER; CHECKS; OPEN UNKNOWN; NEXT SAFE ACTION. Space is coordination evidence, not merge/installation authority.

## R6 — Completion and cleanup

- After each Owner action: verify existing tests and negative assertions; compare source to canonical docs; inspect Git diff and CI, report PR OPEN vs MERGED vs INSTALLED vs CONSUMED separately.
- Final baseline in BASELINE_AFTER_AUDIT.md must never claim all 5,002 semantics checked because the census is complete.
- Risk stopping rule: do not convert one person's blocked upstream CI or one unobserved dynamic consumer into whole-repo permanent HOLD.
