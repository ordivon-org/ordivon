## Business outcome and affected consumers

Describe the observable consumer behavior changed, the before/after state, the
business acceptance criterion, and the measured result. Link the real Runtime,
Host, Gateway, Security or domain consumer. UNKNOWN is not equivalent to FALSE.
Do not equate a passing test with a production effect.

## Source and boundary

- **Change type:** semantic / relocation / repository mechanics / documentation
- **Touched modules:** real source paths and cross-boundary contracts
- **Source cut:** exact commit SHA and installed SHA if applicable
- **Mature components reused / custom components deleted:** actual evidence
- **Rollout and rollback:** actual release effects, recovery and hold reason

## PR consumer review matrix

Complete every row with PASS, FAIL, UNKNOWN or N/A plus a verifiable reason.
Only reproducible consumer results or source evidence justify PASS. N/A must
explain why the area is irrelevant. An UNKNOWN is never silently waived.
Prioritize meaningful outcomes over formalities, formats, bytes and hashes.

| Decision area | Consumer outcome / budget / risk | Evidence, counterexample, or N/A reason | Standing |
| --- | --- | --- | --- |
| Business goal and acceptance |  |  | UNKNOWN |
| End-to-end consumer chain and natural boundaries |  |  | UNKNOWN |
| Correctness, data quality and state invariants |  |  | UNKNOWN |
| Reliability, cancellation, recovery and UNKNOWN effects |  |  | UNKNOWN |
| Performance, latency, throughput and efficiency budget |  |  | UNKNOWN |
| Workspace memory, cgroup/Swap, disk, CPU, IO and cleanup |  |  | UNKNOWN |
| Debuggability, observability, logs and audit receipts |  |  | UNKNOWN |
| Security authority, privacy and applicable external compliance |  |  | UNKNOWN |
| Dependency supply chain, ecosystem reuse (Rust/Python/TS) |  |  | UNKNOWN |
| Modularity, scaling, evolution and technical debt removed |  |  | UNKNOWN |
| Agent collaboration, decision record and durable core docs |  |  | UNKNOWN |
| Tests, independent falsification, formal model/refinement |  |  | UNKNOWN |
| Actual installation/consumer readiness, rollout and rollback |  |  | UNKNOWN |

## Verified execution

| Exact source SHA / command / external consumer | Outcome (PASS, FAIL, SKIP, ENV_BLOCKED, NOT_RUN) | Evidence link or Job |
| --- | --- | --- |
|  | NOT_RUN |  |

## Independent Agent audit — mandatory before merge

A different real Agent must inspect the exact source cut in the shared Space.
Do not invent a reviewer, reuse the author's own judgment or equate CI with
independent audit. A GitHub review by a shared account does not prove a
different Agent identity. If unavailable, mark PENDING and hold the PR.

- **Reviewer actor / identity:** PENDING
- **Reviewed exact source SHA:** PENDING
- **Independent findings and counterexample(s):** PENDING
- **Space Topic + message sequence / review link:** PENDING
- **Disposition:** PENDING (ACCEPT, BLOCK or UNKNOWN)
- **Resolution and re-review if source changed:** PENDING

## Release disposition

- [ ] Business acceptance demonstrated, or explicitly held
- [ ] Actual resource budgets measured, or UNKNOWN with reason
- [ ] No credentials, private keys or unexpected binaries committed
- [ ] Independent Agent audit on this source cut complete without blockers
- [ ] Installed consumer and rollback evidence obtained, or release held
