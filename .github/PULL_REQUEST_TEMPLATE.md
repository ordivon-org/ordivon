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

## Consumer and evidence review

For every substantive PR, fill each row with actual result/evidence or UNKNOWN.
No separate approval service or imaginary owner agent. Reference one Git source
revision and the real downstream consumer. Do not turn a successful unit test
or data checksum into a claim of business success.

| Review lens | Specific evidence, decision, or UNKNOWN |
| --- | --- |
| Business goal / measurable acceptance | |
| Core consumer path / module and authority boundaries | |
| Economic correctness / real data quality / point-in-time access | |
| Mature project and native configuration reused before custom code | |
| Performance, RAM/Workspace lifetime, disk, and resource budget | |
| Reliability, failure recovery, observability, and audit trail | |
| Security, dependency supply chain, licenses, and applicable external standards | |
| Test/refinement counterexamples and remaining unproven assumptions | |
| Long-term evolution, duplication removed, and technical debt | |
| Other affected Rust/Python/TypeScript components and compatibility | |

**Independent real-agent review required before merge:** record the reviewing
ActorRef, exact commit(s), what code and Job/effects were actually checked,
counterexamples, outcome (PASS / FAIL / UNKNOWN), and the Topic/PR review link.
A request for review or an author's self-review is NOT independent approval.
A missing or unverified evidence item stays UNKNOWN, not implicitly PASS.
## Checklist

- [ ] No secrets, credentials or large binaries added
- [ ] No imports of another owner's internals
- [ ] Relocation and semantic changes are not mixed
