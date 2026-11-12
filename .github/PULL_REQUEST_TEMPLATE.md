## User outcome and acceptance

State the **real user/business outcome**, original failure or feature, affected
consumer chain, the exact acceptance test, and the source/runtime evidence.
Link to an issue, Space discussion, or independently reproducible observation.
Mark unknowns **UNKNOWN**, not success or failure.

| Engineering dimension | Evidence, decision, and remaining risk (or **N/A — reason**) |
| --- | --- |
| Outcome / acceptance | User-visible outcome; before/after; executable acceptance |
| End-to-end consumer chain | Input → authority → physical effect → receipt → actual consumer; dependencies and boundary |
| Correctness / data quality | Invariants, transactional limits, failure counterexamples; no fabricated success |
| Capacity / performance | Critical-path latency/throughput or measured budget; expected overhead |
| Resource costs / Workspace leaks | Job/Workspace memory, disk, handles, cleanup, long-running recovery; measurement or N/A |
| Reliability / failure recovery | Abort, timeouts, retry/UNKNOWN, isolation, cancellation, rollback, non-idempotent effects |
| Debuggability / observability / audit | Operators can reconstruct who did what, when, by which source and physical receipt |
| Architecture / LEGO reuse | Mature project/config reused; DELETE-CUSTOM→REUSE→COMPOSE; no duplicate Store/state machine |
| Evolution / technical debt | Change surface, compatibility, migration/retirement; test and doc ownership |
| Security / external compliance | Permissions, data privacy, relevant standard/legal obligations; explicit scope |
| Dependency / supply-chain safety | Existing updater/lockfile, upstream provenance, license and deploy closure |
| Formal methods / independent falsification | Contracts and refinement boundaries; red→green and independent counterexamples |
| Deployment and rollback | Source vs installed vs running; rollback and user-impact boundary |
| **Independent Agent review — required** | **Other actual participant's identity, review link, exact revision, verdict and unresolved findings. PENDING means not reviewed.** |

**Scope of verification:** State which checks ran against this exact revision,
which required external services/roles, what was skipped, and what remains
UNKNOWN. Never equate a green unit test, hash, document, schema or JSON shape
with production effect or business completion.

**Independence:** The reviewer must not be this PR's sole author. Record a
real review on GitHub or an attributable existing Space message; do not invent
a role/person, create a signoff-only Agent, or mark the gate complete based on
a self-review. Keep a Draft PR until substantive review and required tests
are actually complete.

**Review economy:** Keep each cell to one concrete sentence or one test/trace
link. N/A must give a reason; don't create synthetic metrics, ritual checklists,
extra approval layers, or byte/hash exercises unrelated to business outcomes.
