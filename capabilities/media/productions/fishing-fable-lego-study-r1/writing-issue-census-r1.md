# Writing LEGO 2.1 — owner-local typed issue registration R1

Status: source-scoped investigation, not an independent enterprise-wide Issue Registry. Natural owner Media; registration in existing `planning/lego-plan-r1.json` slice VS2 and the existing `Production` manifest.

| ID | Type | Evidence & actual consumer | State | Hard contract / next falsifier | Disposition |
|---|---|---|---|---|---|
| WRI-SOURCE-01 | SOURCE_IDENTITY / PROVENANCE | `story-archival-reconstruction.md` was re-recorded from the earlier chat; no original-chat byte witness | CONFIRMED_SCOPE_LIMIT | never claim word-for-word fidelity; exact input comparison would be required | RETAIN source with explicit "reconstruction" standing |
| WRI-MSR-02 | REPRESENTATION_OVERCLAIM | old `writing-lego-research-dossier-r1.md` used "minimum sufficient" unproved | CONFIRMED_ERROR | remove normative MSR claim; do not infer minimal or sufficient from 3-layer example | CORRECT wording; MSR only optional/qualified method |
| WRI-REGISTER-03 | MISSING_NATIVE_CONSUMER_REGISTRATION | story + research existed as 2 markdown files without Production manifest; Media `models.validate_repository` enumerates all production directories | CONFIRMED_REGISTRY_GAP | add `production.json` / `claims.json`, reuse index instead of custom registry | REGISTER existing owner |
| WRI-DIGEST-04 | FORMAL_ORACLE_GAP | Production schema checks digest syntax but cannot prove actual content hash equals listed bytes | BOUNDED_GAP | targeted byte read-back and mismatch mutation in existing Media test | REUSE owner test |
| WRI-READER-05 | CONSUMER_EVIDENCE | no independent reader observation for this fable | UNKNOWN | real reader response, preserve plurality; no global aesthetics score | DEFER experiment |
| WRI-STORY-06 | CAUSAL/STATE/CONTINUITY | rich story with character/prop/temporal changes, but not formally modeled | UNKNOWN | textual counterexample required before introducing graph/solver | NO NEW ENGINE |
| WRI-LEGACY-07 | REDUNDANT_METHOD_OR_SKILL | Matt Fragments/Beats/Shape, ECC Article/Voice, Media Writing profile overlap in parts of writing | UNKNOWN_CONSUMERS | inspect contract and use; no deletion by similar title alone; delete only proven unconsumed duplicate responsibilities | DO NOT DELETE before consumer cut |
| WRI-FORMAL-08 | OVERGENERALIZATION_RISK | academic narrative metrics & formal source proof can be conflated with literature quality | CONFIRMED_SCOPE_LIMIT | machine checks verify encoded property only | BOUNDARY DOCUMENTED |
| WRI-GIT-09 | SOURCE_DRIFT | local main `26c51eacc7f5`; cached origin/main `fc164834b66d`; live GitHub main queried as `db5520b72c67`; many concurrent worktrees | OBSERVED_AT_PRECHECK | do not compare stale origin/main to live main as if current; no unrelated reset/rebase | NO GIT CLEANUP |
| WRI-CI-10 | CI_STANDING | 8 open GitHub PRs observed; no writing PR in that snapshot, PR check status alone not writing verification | OBSERVED_AT_PRECHECK | owner native tests + exact source identity; do not conflate all repo CI with writing | NO DEPENDENCY PR MERGE |

Notes: no real consumers of WRI-LEGACY-07 proved absent; their removal would be unsafe. Under aggressive subtractive policy, do not preemptively create a new verifier, orchestrator, adapter, Skill, database or score. Existing C-K, Matt, ECC, Media production, contracts and direct human edits are composition candidates.

Preflight evidence captured 2026-10-25 from local Git refs, Runtime, `gh pr list`, `gh api /branches/main`; branch/head values are time-scoped. Exact ref totals observed: 28 local branches, 73 remote-tracking refs, 66 worktrees; one Runtime list had `REVISION_NOT_FOUND` for another worker's workspace. The task must not edit or destroy unrelated unmerged work.

External references: CEGAR Clarke et al. (2000) DOI 10.1007/10722167_15; W3C PROV-O https://www.w3.org/TR/prov-o/; ACL ConStory-Bench https://aclanthology.org/2026.findings-acl.410/ . All are methodological sources, not proof of current user code correctness.

### WRI-SOURCE-FENCE-11 — frozen source revision versus newly added material

Found during final counterexample review: a claimed source file added in the current candidate does not exist at the frozen source revision `127c171b...` that `Production.sourceBindings` names. A source path valid in the current worktree is not sufficient to establish that its bytes were present at an earlier source SHA. Corrected `claims.json` so claim source paths reference files present in the frozen revision (existing Recursive LEGO and Writing Profile); the new study reports remain supporting current-candidate documents, not falsely attested old-revision source artifacts. This fix does NOT supply original-chat bytes or independent reader observations.

This reveals a general owner-native test gap: schema source-path syntax + mapping membership does not prove exact `sourceBinding.revision:path` existence. Formal qualification should use `git cat-file -e SHA:path` for repository-owned source bindings when the repository identity is available, and explicitly UNKNOWN for nonlocal repositories. Prefer extending the current Media source-binding verifier only after a real native consumer needs it; no parallel source registry.

## R2 delta — current-main integration / consumer-counterexample results (2026-10-25)

R1 Git and PR values above were time-scoped observations, **not** active currentness; do not overwrite them retroactively.

| Issue LEGO | Problem type | Observed current evidence | Status / action |
|---|---|---|---|
| WRI-DIGEST-04 | `FORMAL_ORACLE_GAP` | `sourceCarrier` with owner-schema `dependentRequired`, real-file SHA-256 in `models._validate_production_semantics`, 4 real consumers; forged digest rejected | FIXED for opted-in exact-byte outputs; do not generalize to unbound transforms |
| WRI-SOURCE-FENCE-11 | `SOURCE_REVISION_IDENTITY` | `git cat-file -t <SHA>^{commit}` and `<SHA>:<path>`; synthetic missing revision and missing historical blob rejected | FIXED locally for `repository=ordivon` bindings, Git history must be available |
| WRI-HISTORY-12 | `REMOTE_REACHABILITY / SOURCE_CUT` | prior source commit `127c171...` returned GitHub HTTP 404, despite local Git availability | REBIND current integration archived-story commit; require PR and post-merge qualification; never treat local object as remote fact |
| WRI-CONSUMER-13 | `EQUIVALENCE / FALSE_GLOBAL_INVARIANT` | Ordivon Book derived chapter digests differ from whole-book source digest | REJECT universal `outputs.digest = article.digest`; use optional exact carrier contract |
| WRI-ENV-14 | `ENVIRONMENT_DEPENDENCY` | indiscriminate unittest discovery without `resolve` extra failed OpenTimelineIO import; `pyproject.toml` already declares optional `opentimelineio` and owner test command separates `python:test:resolve` | NOT CODE BUG; invoked declared uv extra; 200 whole-Media tests passed with the correct environment |
| WRI-CURRENT-15 | `GIT_CURRENTNESS` | fresh current-base `main=origin/main=bd22b7ba7dc5`; 25 local branches, 75 remote-tracking refs, 63 worktrees; 12 open PR in latest sampled GitHub query | TIME-SCOPED, no unrelated branch/PR cleanup |
| WRI-READERS-16 | `SEMANTIC_CONSUMER_EVIDENCE` | no controlled independent readers for the fable | UNKNOWN; cannot be solved by SHA-256, JSON Schema, TLA+ or textual score |

The main cleanup in R2 is **logical subtraction**: retire per-story-only duplicate checksum logic in favor of the exact source-carrier seam shared with three preexisting works. No unconsumed Skill deletions were proven, so none were deleted. Runtime/Host/Harness/Network remain owned by their respective domain authorities; this Media slice does not claim their formal closure.
