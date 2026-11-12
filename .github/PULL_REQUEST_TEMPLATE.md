## What and why

<!-- The change and its reason, in a few sentences. Link the issue. -->

## Owner

<!-- Natural owner directory, for example services/runtime. Cross-owner changes: name each owner and the contract used. -->

## Change type

- [ ] Semantic change
- [ ] Source relocation only (no semantic change)
- [ ] Repository mechanics (`tools/`, `.github/`, root files)
- [ ] Documentation

## Verification

<!-- Exact commands and results. Use PASS, FAIL, SKIP, NOT_RUN or ENV_BLOCKED; only PASS counts as verified. -->

| Command | Result |
| --- | --- |
|  |  |

## Engineering review (all PRs; risk-tiered)

<!-- Complete the rows relevant to this PR. For irrelevant rows use N/A with a consumer-based reason; unknown is NOT failure or success. Keep concrete evidence, budgets, and counterexamples rather than hashes/format ceremonies. Do not assign fictional owner Agents. -->

| Review axis | Decision / acceptance criterion | Evidence, cost, remaining risk or N/A reason |
| --- | --- | --- |
| Business outcome | <!-- User-visible result and measurable acceptance --> | <!--  --> |
| Consumer path and boundaries | <!-- Entry -> state/effect -> receipt -> downstream; API/contracts changed --> | <!--  --> |
| Correctness and data quality | <!-- Authoritative source, UNKNOWN handling, invariants --> | <!--  --> |
| Performance and efficiency budget | <!-- p95/p99 latency, throughput, bottleneck/DB-lock budget --> | <!--  --> |
| Total resources | <!-- CPU, anon RSS vs page cache, I/O, disk, process/workspace lifetime, $ cost --> | <!--  --> |
| Reliability and fault handling | <!-- Crash/cancel/restart, stale actor, UNKNOWN/receipt/replay, rollback --> | <!--  --> |
| Debuggability, observability, audit | <!-- How an operator reproduces and traces a failure end-to-end --> | <!--  --> |
| Reuse, modularity, long-term evolution | <!-- Mature LEGO reused/changed, contracts and technical debt retired --> | <!--  --> |
| Dependencies, supply chain, security, compliance | <!-- Rust/Python/TS ecosystem, pinned deps, trust boundary, applicable standards --> | <!--  --> |
| Formal refinement and core tests | <!-- Critical invariant/counterexample, native or model evidence, gaps --> | <!--  --> |
| Collaboration and core documentation | <!-- Actual affected Agents/consumers consulted, durable handoff and docs --> | <!--  --> |
| Source -> CI -> merge -> installed -> consumer | <!-- Separate real statuses; SOURCE PASS is not a deployment claim --> | <!--  --> |

## Independent Agent audit (required process gate before merge)

<!-- For EVERY PR: one real other Agent must review the exact CURRENT full HEAD commit SHA, consumer path, counterexample, and unresolved risks. Record evidence in PR review/comment or durable Space. The author, CI success, an old-HEAD review, or a fictional owner cannot sign off. ANY new source commit invalidates the previous approval until a different Agent re-reviews the new HEAD. This Markdown checklist is NOT a machine-enforced GitHub branch rule; do not claim native enforcement without separate ruleset evidence. -->

- [ ] Independent other Agent reviewed the current exact HEAD and resolved material blockers; otherwise DO NOT MERGE
- Current PR HEAD (full SHA, checked before merge):
- Independent reviewer (actual Agent identity, distinct from author):
- Exact reviewed HEAD SHA (must equal current HEAD):
- Review evidence (GitHub review/comment or durable Space reference):
- Falsification, verdict and blockers/resolution: **PENDING**

## Checklist

- [ ] No secrets, credentials or large binaries added
- [ ] No imports of another owner's internals
- [ ] Relocation and semantic changes are not mixed
