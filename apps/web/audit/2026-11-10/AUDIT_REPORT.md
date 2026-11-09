# AUDIT_REPORT — native source/contract findings ranked by consumer risk

SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113. PASS applies only to named source/consumer with native verification. Every item below has path, observed defect, action, and risk. No unqualified claim that all 5002 files had independent semantic review.

| Severity | Exact file/location | Observed counterexample or boundary | Mature action / natural Owner | Risk / rollback |
|---|---|---|---|---|
| HIGH F01 | apps/web/src/config.ts:37-38 | new URL('../.web.sqlite3', import.meta.url).pathname returns percent-encoded URL pathname rather than an actual file path; Node confirmed 'file:///tmp/Ordivon%20work/' becomes '/tmp/Ordivon%20work/' rather than '/tmp/Ordivon work/' | FIX using existing Node fileURLToPath() in same WebConfig source. No new adapter. | Current no-space Linux path is unchanged; cross-OS behavior uninstalled; revert one source commit if regression |
| MEDIUM F02 | apps/web/src/config.ts:15-22 | Number.parseInt('8789evil',10) returns 8789, silently accepting invalid numeric configuration | FIX using a strict ASCII decimal literal gate, then Number(raw) and current Number.isSafeInteger and >0 checks | Intentionally rejects invalid strings previously accepted. Verify existing Owner suite; revert if native valid caller relies on malformed env |
| HIGH candidate F03 | apps/web/src/agent-authority.ts:37-72 and app.ts:63-64 | SecurityContractAdmissionEvaluator uses spawnSync Python in an HTTP request path without a bounded timeout. Blocks Node event loop while running. | REVIEW without changing this batch: determine real request/latency and contract assumptions before converting to Node async child process. No speculative hardcoded timeout or new process broker. | Live throughput unknown, no production effect proof; untouched until actual negative/consumer evidence |
| MEDIUM delegated F04 | docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md:55-71 | Document says current 20 owners/Host schema 11, actual tools/repo/owners.toml has 21 and services/host/src/ordivon_host_v2/service.py:11 requires schema 13, migration 0013 exists | MERGE/CORRECT via active root Owner PRs #2006, #2010, #2013 rather than concurrent edit | Preserve legitimate 2026-11-06 historical schema 11 deployment receipt; never rewrite as if event never happened |
| MEDIUM reject-retirement F05 | apps/web/planning/lego-plan-r1.json and tools/repo/check_architecture_docs.py:227 | Plan has actual checker consumer; no-static-refs/age based deletion premise is false | KEEP Web planning source and root checker contract | Removing plan would break native repository verification |
| LOW accepted decision F06 | apps/web/src/store-schema.ts and README.md:54-69 | SQLite is explicitly the canary durable owner, not unintended global PG writer | KEEP existing schema and WebStore; avoid architecture-by-fashion PG migration | Do not confuse canary source scope with production installation approval |
| LOW coordinated F07 | services/harness/evals/fresh_agent_ab/run_live_v1.py and run_live_v2_currentness.py; extensions/chatgpt-skills-mcp/config/skills-mcp-requirements.txt | Active PRs #2009/#2011 already cover claimed retirements; this audit did not re-run their source | NO DUPLICATE EDIT; review source/PR collision before merge | GitHub OPEN does not imply merged/installed |

## Module-by-module source assessment (Web)
- Domain interfaces: src/model.ts, src/identity-digests.ts, src/store-row-projections.ts — PASS for type/identity placement; scope limited to source and 18 existing unit tests.
- Transactional state: src/store.ts, src/store-schema.ts, src/store-agent-grants.ts, src/store-sessions.ts — PASS bounded canary WAL/BEGIN/COMMIT and reuse of one DB authority. Do not split solely because store.ts is 810 lines.
- Human interfaces: src/webauthn.ts and src/browser-request-boundary.ts — PASS source separation; virtual authenticator/browser evidence is not production human presence.
- Agent interfaces: src/agent-authority.ts and src/security-agent-verifier.ts — PARTIAL owing F03, no unauthorized cross-Owner Rego duplication shown.
- HTTP assembly: src/app.ts — PARTIAL; 721 lines are route orchestration, no evidenced cross-domain state ownership leakage solely from size.
- Config: src/config.ts — FAIL F01/F02, smallest executable fix chosen.

## Theory and Skill falsification
Matt's deletion test: deleting the project-plan artifact is WRONG because the root checker consumes it; splitting the store into more files without changing caller complexity is superficial. DDD and Clean Architecture favor actual owner/data seams, not universal apps-thin/packages-thick forced restructuring. Nx/Turbo are reference semantics, not a toolchain migration obligation. ECC hook duplication and new CI are excluded. No weak-model A/B experiments or expanded test framework.

## Decision
Implement only F01/F02 in WebConfig, run existing native Web verification and repository mechanics; record one Git source diff and final currentness. F03 is a separately justified high-risk potential design issue, not a verified real outage. Delegate F04 to existing root PR Owners.
