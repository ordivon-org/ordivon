# Ordivon — BASELINE_AFTER_AUDIT (2026-11-10)

## What this source-bound audit actually completed

- **Frozen before SourceCut:** `ef17d6879d12faa61fff3bb762b0d500d73c9113` (GitHub main at admission). Audit used isolated Runtime Workspace `ws-gpt6-repo-brownfield-full-audit-20261110-r1`; shared `/root/projects/ordivon` not modified.
- **P0 DONE**: `AUDIT_SCOPE.md`, `MODERN_CRITERIA.md`, 21 registered Owners (`tools/repo/owners.toml` schema_version 1) and active unmerged PR overlap mapped; no new orchestrator, reviewer gate, Skill installation or package-manager change.
- **P1 DONE for mechanical source inventory**: `INVENTORY.md` includes all 5002 Git-tracked paths, real bytes, extension/role and SHA256 prefix; 123,199,041 input bytes read, zero Python AST syntax failures, 23 identical-byte groups. Not a 5002-file detailed human semantic proof, not installed state.
- **P2 DONE as bounded source review**: `AUDIT_REPORT.md` scores all 21 owner roots across 12 criteria with PASS/PARTIAL/FAIL/UNKNOWN and 12 concrete prioritized findings. Reproduced F01 exact-input failure; high-risk other-owner findings are separate unresolved owner tasks, not fixed by writing this report.
- **P3 DONE for scoped actions**: `REFACTOR_PLAN.md` gives exact affected files, interface, required old and new semantics, existing tests, rollback and handoff; no test infrastructure/consumer/feature tasks accepted.
- **P4 CODE SOURCE_REPAIRED for F01**: `apps/web/src/config.ts:15-22` `integerEnv()` now parses only entire decimal positive integer inputs. Before: `Number.parseInt('42garbage',10) === 42`, exit0 in Node. After: actual source `loadConfig()` rejects malformed junk/negative/zero/float/whitespace/unsafe integer while keeping 8789 and zero-padded 0008. One natural-owner file; no new exports, tests, DB migrations or features.
- **P5 publication is a separate standing**: code commit `2ca7608e1139` is only source commit at time of this document; subsequent documentation commit and PR URL/status must be verified by Git. This document is source review, not deployed Web or final browser acceptance.

## Changes and risk ledger

| Actual path | Before | After | Risk and rollback |
| --- | --- | --- | --- |
| `apps/web/src/config.ts:15-22` | Partial integer coercion accepts suffixed garbage | Full lexical digits + `Number()` + safe/positive check | Invalid historical env values fail on startup by design; `git revert` code commit + native owner verify |
| `docs/audits/2026-11-10/AUDIT_SCOPE.md` | No user-requested frozen scope file for this run | Exact SourceCut and Owner/phase boundaries | No runtime effect; Git revert |
| `docs/audits/2026-11-10/MODERN_CRITERIA.md` | No evaluation checklist for this run | 12 source-evaluable checks and tri-state+UNKNOWN | Risk of treating matrix as proof; explicitly limited |
| `docs/audits/2026-11-10/INVENTORY.md` | No bounded file-by-file snapshot for this run | Full 5002-path tracked list with source hash prefixes | Stales immediately after main moves; frozen SourceCut, not current registry |
| `docs/audits/2026-11-10/AUDIT_REPORT.md` | No report for this run | Ranked exact source findings and 21-Owner score matrix | Incomplete deep semantic coverage honestly marked |
| `docs/audits/2026-11-10/REFACTOR_PLAN.md` | No action plan for this run | Scoped F01 repair and non-overlap actions | Owner tasks outside this PR intentionally untouched |

## Existing verification receipts (run against actual changed source)

- Before change: `/usr/bin/node` running `Number.parseInt('42garbage',10)` produced 42 and `safe:true`, exit 0.
- After change: eight direct `/usr/bin/node` imports of actual `apps/web/src/config.ts` through `loadConfig()`, all matched expected accept/reject outcomes, including `42garbage`, `12.5`, `0`, `-1`, whitespace, unsafe number and valid `8789`/`0008`.
- `cd apps/web && mise run verify`: **18 passed, 0 failed, 0 skipped** with pnpm 12.16.1; TypeScript `tsc --noEmit` PASS; exit 0. Existing tests only; **no test code added**.
- `python3 tools/repo/check_owner_boundaries.py`: PASS at baseline; scan `active_files=2320, packages=10, seams=31, references=38`, exit 0. After-edit retest PASS, exit 0, same 2320 active files/31 seams/38 refs.
- Entire `repo:ci` was NOT assumed from the targeted test outcomes; root CI / GitHub required checks / merge remain separate release facts.

## Independent challenge and bounded unresolved outcomes

- Space kickoff sequence **25960** in `space:ordivon-task-portfolio-and-proof-gates-r1:20261101`, topic `topic:ordivon-task:agent-text-contract-cross-audit:20261109`. Further handoff must include the exact PR head rather than old interim SHA.
- Cross-owner PRs #2006/#2010/#2013 on the same architecture program, #2012 Repo indexing, #2016 Host, #2015/#2009 Harness, #2011 Skills, #2008 Workstation, and #2004 Data were *not* modified or claimed accepted. For changes elsewhere, natural owner already has active work.
- `services/harness/src/ordivon_harness/ordivon/run_continuity.py`, `loop.py`, `services/runtime/.../pg_admission.rs`, `capabilities/artifact/artifact_verification/stage.py` remain qualified review candidates, not confirmed disposable modules.
- No production Runtime/Host/Finance DB, Workspace closure, network/device policy or systemd action performed. No new tests, consumer routes, product acceptance or weak-model experiment.
- Actual deployed schema versions of the 21 Owner services, current systemd binary identity and external domain success are **UNKNOWN** at this source snapshot. They require their natural owners' installed readback, not a synthetic Git inference.
- A 5002-file mechanical ledger does **not** satisfy a claim of exhaustive line-by-line semantic adjudication; completing that requires owner-local staged source reasoning on remaining `UNKNOWN` modules, naturally distributed rather than one huge unreviewable source patch.

## Success measurement and subsequent use

Achieved this bounded wave: one concrete correctness repair, no expanding tests/API, valid existing Web 18-test and typecheck receipt, explicit source-owner contract, reproducible baseline and a 12-point assessment with precise outstanding handoffs. **Not achieved:** all 21 owners independently fully modernized and verified, all possible dead code eliminated, full end-to-end or production deployment; do not report those as done.

Do not copy these snapshots into a second live registry. For the next Owner task read its actual current main/PR, follow `owners.toml`, native tool and the modern criteria; apply a small exact decision and use current evidence instead of treating this dated audit as authority.

## Final source-repository checks

After change native architecture-doc checker exit0. Existing owner-boundary unit tests 17/17 PASS exit0. This evidence is separate from not-run full aggregate repo CI.
