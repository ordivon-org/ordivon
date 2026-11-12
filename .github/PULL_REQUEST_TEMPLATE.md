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

## Engineering review (Runtime / shared execution)

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

## Independent Agent audit (required before merge)

<!-- At least one other *actual* Agent, not the author or a fictional owner, must independently inspect this PR. A CI result, invitation, or self-review is not a peer audit. Leave this PENDING until the real review evidence exists. -->

- [ ] One independent Agent reviewed the actual diff, consumer impact, failure cases and residual risk
- Reviewer (Agent identity):
- Review evidence (PR review/comment or durable Space message link/reference):
- Verdict and blocking findings/resolution: **PENDING**

## Checklist

- [ ] No secrets, credentials or large binaries added
- [ ] No imports of another owner's internals
- [ ] Relocation and semantic changes are not mixed
