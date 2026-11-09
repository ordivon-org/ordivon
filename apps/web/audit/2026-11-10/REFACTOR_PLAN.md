# REFACTOR_PLAN — bounded existing-behavior Web modernization

Frozen starting revision: ef17d6879d12faa61fff3bb762b0d500d73c9113. Original 35 Web files and full 5002 Git source inventory captured. No features, tests, consumers, package changes, schema migration, extra hooks/CI, general refactor or new Owner.

| Task | Dependency | Exact implementation (small enough to execute) | Command + expected evidence | Revert |
|---|---|---|---|---|
| P0 | none | Check Git main, owners.toml, existing PRs and native files | Source SHA and path list stable; no other Web PR overlap | n/a |
| P1 | P0 | Read/hash all 5002 tracked file bytes; parse Python AST/JSON/TOML; inspect all Web file metadata and core source relationships | Counts: 5002 files, 123199041 bytes, 1460 Python AST, 1315 JSON, 50 TOML, 0 syntax errors | n/a |
| P2 | P1 | Compare DDD/Parnas/ports, Node file semantics and real Web/Security owner boundaries; post falsifier to existing Host Space | Actual negative '8789evil' parsed; encoded filename differs from native fileURLToPath; root plan reader found at check_architecture_docs.py:227 | n/a |
| P3 | P2 | Freeze F01/F02 as one tiny WebConfig patch. Do not change schema/store/HTTP admission, no source file moves, no new tests | Spec/Standards review accepts the exact existing API and current examples; disjoint from parallel root PRs | n/a |
| P4 | P3 | apps/web/src/config.ts import fileURLToPath from node:url, convert default databasePath by fileURLToPath(new URL(...)); Number.parseInt(raw,10) to /^[0-9]+$/-guarded Number(raw) | Existing apps/web mise run verify: TypeScript compile and 18/18 tests PASS; Node counterexample now shows proper native conversion and invalid number refusal; root architecture/boundary checks | git revert isolated commit |
| P5 | P4 | Record post-fix checks/remaining UNKNOWN in BASELINE_AFTER_AUDIT.md; publish single owner branch through GitHub normal PR and CI, no invented completion | Exact diff, no additional test/consumer lines, PR state scoped to SOURCE until merge, installed state not asserted | git revert SHA after merge |

Handoff in existing capability task Space: status, SourceCut/head commit, done tests, pending questions and exact message/GitHub PR URLs. F03 synchronous child concern remains TODO only where real native consumer justifies a future existing-code refactor; no new task framework. No arbitrary tests are added to improve a score.
