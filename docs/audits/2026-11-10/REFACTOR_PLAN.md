# REFACTOR_PLAN — stock-only executable changes

Base: ef17d6879d12faa61fff3bb762b0d500d73c9113. This is a bounded plan within existing docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md; not a parallel long-lived task system.

## Decision rules

- Every change is native Git diff and easily reverted using git revert <commit>, not destructive database operations.
- Do not add features, tests, consumers, product extensions, hooks or new owner registries.
- Standards review: follow local AGENTS, pyproject/mise, owner boundary checker. Spec review: remove a real contradiction/obsolete entry, no behavior extension.
- Use ECC brownfield classification and Matt deletion test: do not extract a shared helper merely because two files have similar bytes.
- When blocked by a concurrent PR, transfer concrete path/issue to the owning peer, not duplicate its changes.

## Independent tasks / order

| Task | Owner and exact paths | Verified premise / proposed action | Existing verification | Risk / rollback | Depends on |
|---|---|---|---|---|---|
| A01 | Harness: services/harness/pyproject.toml | requires-python ==3.15.1, mise 3.15.1, README 3.15.1 but Trove classifier explicitly claims 3.14; remove stale minor-version classifier, keep major 3 + exact canonical requires-python; do not add capability | Python tomllib readback; uv lock --check; existing wheel check and Ruff; repository structural checks | Low: metadata changed only; git revert precise commit | Phase2 evidence |
| A02 | Harness: services/harness/evals/fresh_agent_ab/run_live_v1.py, run_live_v2_currentness.py | Both old scripts import a missing module; peer source PR #2009 already deletes them, preserving result and study. Do not duplicate patch. | existing Harness suite (PR body has 1383 passed), GitHub PR final state | Low for source, dynamic path UNKNOWN; revert peer commit if needed | PR #2009 owner |
| A03 | Repo: tools/repo/exhaustive_coverage.py and docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md | Already targeted by concurrent #2012/#2006/#2010/#2013/#2014; converge PRs, no new duplicate source guard or audit programmes | repo:ci, existing Git SourceCut checks, GitHub queue | High: CI/source graph semantics; cannot change in parallel | Peer integration |
| A04 | Data: packages/data/docs/AGENT.md, HUMAN.md, LEGO_CENSUS.md | #2004 pre-existing peer reduction; reconcile current Data SourceCut and overlapping #1970 first | data:verify and formal:verify already owner native | Medium: unique semantic instructions | Peer integration |
| A05 | Host: services/host/src/ordivon_host_v2/service.py and Host PG Work snapshots | Existing source integrity false-healthy fixed; historical missing snapshots still actual data concern, no invented schema/revision. No DB effect in stock-source pass. | native Host read-only status + existing PG tests | High: external data integrity | Host natural Owner |
| A06 | Runtime: services/runtime/crates/ordivon-runtime-mcp/src/server/pg_server.rs and runtime/platform/linux.rs | Linux PG path denies Windows context; keep existing live Windows persistence until Windows native replacement actually verified. No new feature in this scope. | native Windows provider / runtime verify when Owner agrees | High: active Runtime data | Runtime natural Owner |
| A07 | Artifact: capabilities/artifact/artifact_verification/stage.py and scripts/artifact_verify.py | Do not merge stage and standing names until their exact consumers/contract outcomes are compared. | artifact:verify + genuine receipt reads | High: false evidence claims | Artifact natural Owner |
| A08 | Capital/Media/Game/Workstation/Network/Security source roots | Work with active peers; prioritize no-reader old wrappers only when actual current consumer and recovery facts support; protect media originals, historical replay and service drop-ins. | native owner tasks, no test additions | Varies, likely medium/high | Existing per-owner audit work |

## A01 exact native execution sequence

1. Read the three authority files: services/harness/pyproject.toml, services/harness/mise.toml, services/harness/README.md and its existing scripts/check_wheel.py. Check no open PR touches pyproject.toml.
2. Capture baseline via git status and git diff origin/main...HEAD. Confirm project requires-python is exactly ==3.15.1, current version minor classifier is 3.14. Re-run this source inquiry; if mismatch no longer exists, skip A01.
3. Delete only the obsolete Programming Language :: Python :: 3.14 entry. Do not replace with a second mutable version pin; exact interpreter remains owned by requires-python and mise.
4. Verify with Python stdlib tomllib that version pin remains, classifier 3.14 absent and Python 3 major retained. Run existing uv lock --check, uv build --offline --wheel and scripts/check_wheel.py; no new tests.
5. Run existing root documentation/Owner checks; read exit codes and diffs. Commit with exact baseline. Preserve any verification limitations.
6. Post Space handoff with SourceCut, diff, test commands, risk, and outstanding GitHub queue status. Do not report source PR as deployed.

## Independent cross-review checklist per task

- Theory: does change implement Parnas information hiding and real lower Owner; does A/G substitution preserve assumptions?
- Matt: does the change make a deeper module or remove a misleading decision? Is Standards/Spec review bound to fixed diff?
- ECC: is the failure Thinking, Coding, Missing, or Technology? Why is Missing NOT a feature request here?
- Superpowers: was original contradiction directly measured? Were all reported checks actually run in this session?
- Overconservative: are we retaining useless legacy solely from hypothetical consumers despite Git-reversible source-only change?
- Superficial: did we merely change formatting instead of remove actual wrong responsibility?
- Representation: are we confusing stale metadata, journal authority, and runtime behavior?
- Mature reuse: does native package metadata supply this already without a custom validator?
- Risk: give a concrete counterexample and rollback SHA rather than global safety theatre.

## Exit

Finish a scoped Task A01 code edit and native verification, include exact before/after baseline. The remaining 5002-file semantic review is a separate naturally owned programme; this plan does not claim each file fully understood or allow all old code to be bulk deleted.
