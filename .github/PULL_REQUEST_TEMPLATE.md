## What and why

<!-- Business / research outcome, real consumer, and one falsifiable acceptance test. If value is not established, say UNKNOWN or STOP; avoid format/hash-only success claims. -->

## Source boundary and reuse

<!-- Affected directories, natural contract boundaries, and mature upstream libraries/config reused. No invented owner agent. Identify any custom code retained/removed and why. -->

## Change type

- [ ] Semantic change
- [ ] Source relocation only (no semantic change)
- [ ] Repository mechanics (tools/, .github/, root files)
- [ ] Documentation

## Consumer and engineering review

<!-- Required for EVERY PR. Concise evidence/results in each row; use PASS, FAIL, UNKNOWN, NOT_RUN, or N/A (with a reason). A table filled with promises is not acceptance. For docs-only changes, note which runtime rows are N/A and why. -->

| Review question | Evidence / measured result / reason not applicable | Standing |
| --- | --- | --- |
| **Business goal / observable acceptance:** Which actual user or downstream consumer improves, by how much? |  | UNKNOWN |
| **Consumer path / interfaces / boundaries:** Source → decision → effect → readback; which external effect is permitted? |  | UNKNOWN |
| **Correctness, data quality, formal refinement:** Preconditions, state invariants, real counterexamples, PIT and missing-data semantics |  | UNKNOWN |
| **Performance and resource budget:** CPU/latency, RAM and Workspace lifecycle/leaks, disk, network/API/tool cost; before/after where material |  | UNKNOWN |
| **Reliability, failure and recovery:** Cancellation, partial effects, crash/restart, timeouts and safe rollback |  | UNKNOWN |
| **Observability and audit:** Reproducible operator diagnostics, source evidence, consumer-visible outcomes and limitations |  | UNKNOWN |
| **Architecture and evolution:** Modular contracts, scaling assumptions, later extension, technical debt deleted vs introduced |  | UNKNOWN |
| **Reuse, dependencies and external compliance:** Mature upstream primitives first; lockfiles, update authority, licenses, supply-chain and applicable standards |  | UNKNOWN |
| **Security and effect authority:** Credential handling, access boundary, simulated vs actual financial/other side effects |  | UNKNOWN |
| **Docs and collaboration:** Changed consumer-facing docs, operator runbook, migration and dependency coordination |  | UNKNOWN |

## Verification

<!-- Exact commands, environment, source revision, observed outcome. PASS means actually run; FAIL, SKIP, NOT_RUN and ENV_BLOCKED are not PASS. -->

| Command / real experiment | Result |
| --- | --- |
|  | NOT_RUN |

## Independent Agent audit — required before merge

<!-- Give the identity of ONE different actual reviewing Agent and its Host message or GitHub review permalink. Author self-check, invented agents, and requests for review do not count. Real defects and residual UNKNOWN go here. Use the repository's existing GitHub review requirement, not a custom approval service. -->

- Reviewer (different ActorRef / GitHub reviewer):
- Review evidence link:
- Review standing: **PENDING** / PASS / CHANGES_REQUESTED
- Substantive challenge, counterexample or remaining blocker:
- Resolution / follow-up commit:

## Existing repository checks

- [ ] No secrets, credentials or large binaries added
- [ ] No imports of another natural code boundary's internals
- [ ] Relocation and semantic changes are not mixed
- [ ] Any relevant UNKNOWN / FAIL is explicitly bounded; independent peer audit actually completed before merge
