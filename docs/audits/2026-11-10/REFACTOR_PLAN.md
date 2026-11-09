# Ordivon current stock — existing-system repair execution plan

Exact starting SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113. Mandatory: observe → decide → plan → smallest owner-local edit → verify → Git rollback/PR. No new features, tests, consumer routes, governance services or abstraction-first redesign.

## Matt grill/clarify conclusions resolved from current request and source

1. Is this a brand-new monorepo migration? No. tools/repo/owners.toml and tools/repo/dependency_contracts.toml already provide explicit owner routing and guard semantics; existing repo:ci and owner-native CI are the authority. Reuse, do not introduce Nx/Turbo.
2. Does domain-first require moving services/runtime and services/host to a new packages tree? No. Their current public interfaces and installed service paths are contracts; proposed STRUCTURE_R2 is not current executable topology.
3. Is every SQLite file dead because PG is primary? No. Runtime repair/inspection and Harness experimental scripts have current source consumers. They require owner-specific lifecycle closure, not mass deletion.
4. Is the R2 Mailbox a production Artifact responsibility? No known installed or current source consumer; dated LEGO plan explicitly says DO_NOT_PROMOTE. A peer reviewer verified rclone copy is not equivalent to SigV4/temporary credentials, so retirement rests on no-current-consumer, not feature equivalence.
5. Should frozen Game/Media/Capital fixtures be aggressively deleted? No; they have possible exact-byte/engine/research consumers. Keep until those natural owners establish source/consumer closure.
6. Is doc-only modernization success? No; docs are navigation evidence; the concrete stock cleanup removes unconsumed custom code and self-consumed prototype files. Significant module reform remains by natural owners.

## Task DAG / expected owner / smallest seam / rollback

| Task | Blockers | Actual owner & exact edit | Current acceptance; stop rule | Rollback |
| --- | --- | --- | --- | --- |
| R00 Scope, criteria | none | root: AUDIT_SCOPE.md, MODERN_CRITERIA.md | frozen SourceCut, no new rule engines | revert root audit commit |
| R01 Whole-tree file census | R00 | root: FILE_LEDGER.tsv and INVENTORY.md | 5002/5002 exact tracked paths and content digest, 21 current owners | remove frozen files |
| R02 Standards-vs-Spec module audit | R01 | root: AUDIT_REPORT.md and DEPENDENCY_SIGHTINGS.tsv | exact issues and affected owners, independent root native guard green | revert source-only report |
| R03 Cross-Owner collaboration | R02 | Host Topic 03-refinement; source SHA, path, independent negative cases | real reviewer answer or UNKNOWN; no fake approvals | no source side effects |
| A01 Retire historic Artifact docs | R02,R03 | Artifact: delete 11 old standalone markdown reports, not current native verifiers | no tracked path refs / existing owner suite green | git revert Artifact PR |
| A02 Retire Artifact experiment self-consumers | R02,R03 | Artifact: old evidence_observation prototype plus sole self-asserting test | no runtime import path, existing suite remains green | git revert |
| A03 Retire unpromoted custom R2 transport | R02,R03 | Artifact: script/config/schema/sole test, exact static+installed nonuse witness | no current service/Domain call; fix historical LEGO plan source locator and README | git revert; provider data untouched |
| A04 Repair Artifact current navigation | A01,A02,A03 | Artifact: remove absent registry directory entry, update obsolete historical notes | links target existing live source and no factual provider equivalence claim | git revert |
| A05 Existing native regression check | A04 | Artifact: mise run verify; root repo guards/CI; inspect deletions | strict pre/post equivalence of current checked properties, no tests added | revert failed patch |
| R04 Root consolidation | R02,A05 when available | root audit report & frozen after-baseline | reconcile exact Artifact candidate Git/PR and peer Workstation/Game PRs, no invented merge | revert doc commit |
| R05 Protected delivery | R04 | normal GitHub PR, independent review; never modify shared physical main | exact SHA, PR status and CI checked; source != deployed | revert branch/PR |

For active owner-specific code findings (Runtime SQLite legacy, Harness Postgres/SQLite experiments, Runtime/Host loops, Media production history, Capital trade semantics, Game vendored engine, Workstation historical projection PR #2008), this plan outputs a **responsible owner-level review obligation** rather than running cross-owner edits without observed installed consumer closure. Do not create duplicate issue-per-file queues or overwrite their concurrent worktrees.

## Execution rubric (applies to each changed file/group)

- Exact input source identity and natural Owner are documented; source consumers including generated config/script/CI as applicable were inspected.
- Deletion test: would removing an obsolete module make the effective interface smaller without shifting complexity to a new wrapper? If not, no GO.
- Parnas/contract check: no strengthening consumer assumptions or weakening required outputs; preservation of rollback/source history.
- Honest evidence: static text search does not prove every external consumer absent. Existing native execution and installed facts can justify narrower action.
- Matt Standards review: naming, module depth, current docs, physical import/consumer seams; Matt Spec review: old user-visible/Agent behavior and contract preserved.
- Superpowers: worktree isolation and fresh Owner-native verification before calling complete.
- ECC: reuse existing hooks, CI, skill router and repository mechanics. No other hidden global authorization.
- Stopping condition: do not hold the whole program for hypothetical missing proofs; only block the specific destructive action whose real consumer or physical state is unknown.

## Handoff status schema (existing Host Space, no new database)

SOURCE: exact commit and checked paths.
STATUS: observed, planned, changed, local_verified, PR_open, merged, installed, consumed (do not jump levels).
COMPLETED: exact deletion/refactor and source diff count.
NATIVE_EVIDENCE: run command + exit/results and independent negative control when relevant.
OPEN: concrete source/runtime/dynamic consumer UNKNOWN, owner and next measurable check.
NEXT: consumer-native current job or existing Owner PR; no general approval bottleneck.
