# Host R2.1 — Zero-base Subtractive Execution Plan

Specification: services/host/docs/HOST_R21_AGENT_EXECUTION_SPEC.md. SourceCut Git 7d7dcbe087136ae6249cd47524d1f6e33209f3e5; main refreshed ef17d6879d12faa61fff3bb762b0d500d73c9113 with zero Host changes. This document replaces old A1–G1 increment checklist; do not carry over feature/test/consumer additions.

## Validated intake

[x] Git tracked Host file-by-file first-pass ledger: 117 files, 36 production Python AST scans.
[x] Host AGENTS/README, existing source dependencies/Doc tests, cross-monorepo file-name refs examined.
[x] External mature methods: Parnas information hiding; Matt deep modules/code review; ECC brownfield-retrospective; Superpowers precise plan and verification; R2.1 full 11-coordinates only for independent LEGO.
[x] Existing task Space messages soliciting independent falsifiers; collaboration not authority.
[x] Prior additive test PR #2000 closed; no unmerged tests reused as a silent feature request.

## S1 — Replace obsolete Host Spec and Plan in place

Files: docs/HOST_R21_AGENT_EXECUTION_SPEC.md and docs/HOST_R21_AGENT_EXECUTION_PLAN.md. Rebuild current canonical Host-specific audit and 117-file ledger, eliminating old incremental C1/C2 status prose; retain Git history not duplicate append-only docs.

Expected result: two existing docs continue as current Owner guides, with exact source/prior-art mapping, owner/non-owner boundaries, no duplicate global Agent Spec. Verify Git diff --check and source link paths; no new tests.

## S2 — Retire static historical observatory if exact readset remains unchanged

Files:
DELETE planning/host-friction-observatory-r1.json (192 obsolete static lines).
MODIFY planning/lego-plan-r3.json freezeRule.evidence only, replacing local-current-path assertion with immutable historical Git blob/path pin of original observations; preserve same constraints and do-not-own.
MODIFY docs/HOST_OWNER_GUIDE.md historical pointer accordingly.

Before delete verify no outside Host file mentions its basename, confirm original Git object is reachable and content hash matches current tracked file. Do not pretend historical measurement is current. Do not modify schema, Work, Goal or service. Existing root checker and Host native tests must still pass; if real consumer exists stop ONLY this item.

## S3 — Concentrate present-day Owner guide

Files: docs/HOST_OWNER_GUIDE.md and at most README.md/AGENTS.md for current navigation consistency. Replace obsolete dated observation/test receipts with concise real source/module/MCP/PG commands, preserve unique operator procedures and safe existing source links. No new guide. Existing docs checks, no external execution claim.

## S4 — Deepening at code level only when proven better

Candidate: src/ordivon_host_v2/social_read_queries.py (15-line read mixin). Maintain rather than delete if removal just expands SocialStore multiple inheritance and compromises CQRS clarity. Audit 36 modules for comparable complexity hidden behind a single real interface; do not add adapter or public method. Potential change requires exact before/after call-site comparison and existing Host tests. Zero source code changes is valid if no worthwhile subtraction found.

## S5 — Deferred cross-owner R1 retirement

Do not delete planning/lego-plan-r1.json or R3: active root graph checker consumers. Historical planning/social-work-fabric-r1.json remains because root tools/repo/test_architecture_docs.py directly consumes it. Retired the old test_social_work_fabric_architecture.py nine-plan-assertion mirror separately under Host Owner, while existing actual Work/MCP/PG tests remain. Consult Repo Owner before any R1 plan JSON removal. Existing docs/SOCIAL_WORK_FABRIC_R1.md and R2_IMPLEMENTATION.md may retire only if unique current evidence preserved by exact Git objects and active README assertions removed. Do not edit other Agent branches without coordination.

## S6 — Existing verification and Git delivery

Run existing commands only: git diff --check, current link/source references, cd services/host && mise run verify, and if code/PG source actually changes use existing mise run test:postgres:disposable. If architecture graph changes, existing Repo native graph checks plus root repo:ci as applicable. No new tests, consumer routes or features. Use Matt two-axis Standards/Spec review on real diff and independent Space negative feedback. Commit bounded Host-only patch and publish PR against refreshed main; mark merged/installed/consumed separately.

## Stop conditions

No addition of policy registry, approval queue, test suite, consumer path, Skill clone or new authority. No change to production Host PG or historical Work data. Revisit only when source makes a real changed-behavior claim; otherwise STOP at KEEP with reason. Old docs and source provenance remain in Git.

## 2026-11-10 executed stock-subtraction receipts

- Baseline 117 Git-tracked Host files; no new feature, test, consumer, database or schema path.
- REWRITE Host Spec and Plan in place, Guide from 254 to 59 lines of current navigation; preserve prior history in Git.
- DELETE obsolete static measurement `planning/host-friction-observatory-r1.json` (192 lines), pin original Git blob `a5503d5be27a121b7b9a3d5fa2088ea44cac4c79` in R3 freezeRule.evidence. Historical numbers not rewritten.
- DELETE historical self-referential plan test `tests/test_social_work_fabric_architecture.py` (95 lines, nine R1 JSON/source-string assertions) without creating replacement tests. Preserve existing real Work/MCP/PG tests; `planning/social-work-fabric-r1.json` retained because Repo checker consumes it.
- KEEP `planning/lego-plan-r1.json` and `planning/lego-plan-r3.json` due current Repo graph consumers; KEEP 15-line `social_read_queries.py` pending genuine interface/deletion-value proof.
- Existing Host `mise run verify`: 383 passed, 51 skipped, exit 0. CrossHair/Z3/Lean checked; skipped PG is NOT PG acceptance.
- Existing `python3 tools/repo/check_architecture_docs.py`: PASS exit 0. Existing root Repo pytest suite (as prescribed by `mise.toml`): 533 passed in 48.67s, exit 0.
- First Workspace whole repo:ci ran partial checks including 533 pytest PASS, but no verified terminal; submitted proper Runtime cancellation, do not claim whole-CI PASS.
- Existing Space messages 25878 / 25893 / 25940 carry peer falsification requests, not approval. Final PR review pending. Production Host unchanged; live history Doctor issue not reclassified or fixed.
