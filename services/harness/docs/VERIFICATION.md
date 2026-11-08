---
schema_version: 1
id: harness.verification
title: Harness Verification
type: reference
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - builder
  - operator
  - researcher
  - agent
updated: 2026-11-08
summary: Claim classes, evidence strength, historical evidence interpretation and current release gates.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.status
  - harness.compatibility
  - harness.releases
---
# Harness Verification

## Evidence classes

| Evidence | Proves | Does not prove |
| --- | --- | --- |
| deterministic unit/integration test | current source invariant under controlled inputs | live Provider or Runtime behavior |
| frozen fixture | a named failure trajectory and expected repair | arbitrary repositories or Providers |
| live receipt | one real journey on an exact dependency graph | current `main` after later changes |
| immutable research projection/result | one bounded owner/research observation bound to a tested implementation lineage | whole-current-product certification after later source changes |
| historical closeout/report | design evolution and prior decisions | current implementation correctness |

No implementation-bound evidence should be cited without its Harness/implementation revision and dependency context.

## Real PostgreSQL Run consumer qualification

The supported Agent Run Python API and installed-wheel Host-free
create/reopen/inspect smoke require a fresh PostgreSQL test authority, not
SQLite. The GitHub Owner shard supplies HARNESS_PG_TEST_DSN from its disposable
PostgreSQL service for harness:queue. Tests create isolated unique schemas
and drop only those schemas. Local verification must provide an equivalent
test-only DSN; no old SQLite Run data are migrated or replayed. Missing PG
authority is SKIPPED or NOT_RUN for native tests, never a PASS receipt.

## Formal-first proof-to-consumer frontier (ToolProgram, source-scoped)

**Claim under verification:** an already-admitted three-step ToolProgram never
broadens the current Tool grant, never exceeds its remaining physical Tool Call
budget, and never dispatches subsequent steps after a non-observed Tool result.
This is a **safety** obligation; an UNKNOWN step may have produced an external
side effect before its response was lost. A partial ToolProgram is not atomic.

| Stage | Owner-native artifact | Exact claim / status |
| --- | --- | --- |
| Specification | `tool_program_contract.py`, `agent_tool_observation.py`; `ToolProgramSafetyR1.tla` | Frozen exact-turn grant, pre-admission budget, ordered step outcomes. Source declaration only |
| Abstract model | `formal/ToolProgramSafetyR1.tla`, `formal/ToolProgramSafetyR1.cfg` | MaxSteps=3, all budgets 0..3, granted/denied, five observation statuses; abstract ToolBridge identity assumed |
| Independent falsification | `ToolProgramSafetyR1.{unknown,partial,complete}-probe.cfg` | Expected reachable counterexamples: UNKNOWN, non-atomic partial effects, success; probes must fail the **named** deliberately false invariants |
| Model checking | `mise run formal:tool-program`, Runtime-pinned TLC 1.7.4 | PASS: native SANY/TLC explored 36 generated / 33 distinct bounded states; 3/3 deliberate false-invariant probes produced the expected counterexample; not universal Python/effect proof |
| Implementation refinement | `tests/test_tool_program_model_refinement.py` invokes the actual `HarnessToolProgramExecutor` for 1,000 finite combinations | PASS on locked Python 3.15.1, bounded executable differential witness, not proof for arbitrary Tool Bridges |
| Consumer seam | `tests/test_p2_tool_program_provider_loop.py`, `tests/test_p2_tool_program_recovery.py`, `tests/test_postgres_harness_store.py`, `tests/test_postgres_cli.py` | PASS for native Python 3.15.1 full suite and real isolated PostgreSQL 18.6 (13/13); deployed external effects remain unverified |
| Release / installation | `mise run verify`, `mise run pg:verify`, offline wheel build and installed CLI readback | PASS for source candidate: official `mise run verify` exit 0, 12 CLI checks, wheel `ordivon_harness-0.6.0-py3-none-any.whl`; production installation NOT_RUN |

**Observed executable defect and remediation:** The original
`tool_program_resolution._resolve_template` consumed the mutable public
`HarnessToolObservation.structured_content` view, although observation
evidence digests are derived from a construction-time canonical snapshot.
A later actor mutating that convenience view could redirect a referenced
argument without changing the retained digest. The implementation now resolves
references through `observation.to_dict()["structuredContent"]`, which reads
sealed canonical bytes. The test
`test_mutable_observation_projection_cannot_redirect_next_tool` is a
property-specific falsification witness. In an isolated Python environment,
six exact SHA-256-matched production and test source files were exercised
in an isolated Python 3.13 environment: 6 component/test-methods passed,
including 1,000 finite ToolBridge traces, using substituted canonical JSON,
model-value and ToolBridge ports. An independent receipt is produced outside
the Ordivon repository; this does **not** establish full-package, TLC or
deployed-Python qualification.

**Implementation refinement map (bounded):**
`admitted` ↔ every step's name in `HarnessToolProgramExecutor.admitted_tools`;
`initialBudget` ↔ `remaining_tool_calls`; `issued` ↔ count of actual
`ToolBridge.execute` invocations; `observed` ↔ leading successfully observed
steps; `stopped` ↔ first returned non-`observed` status; `completed` ↔
all steps observed and final template resolved. The model abstracts away
argument-dependent template failures, mismatched bridge receipts, persisted
reconciliation, dynamic cancellation, and external effects. The Python
executor may raise rather than return a terminal result for those failures;
that is not a model failure unless the admitted refinement relation claims
otherwise.

**Retirement rule:** Only remove a traditional test when its distinct
property/fault model is already entailed by a checked specification *and* a
validated current model-to-implementation refinement or the test has
independently proven zero consumers. Candidate redundancies include the
single-example ToolProgram budget/grant/UNKNOWN tests *after* the bounded
state/refinement checks have passed, but they are deliberately **retained**
for now. Keep PG serializability/readback, real Provider/Gateway delivery,
packaging/install and release checks: this model does not cover them.
Do not convert a CrossHair timeout, TLC bounded PASS, test SKIP, or
static source equality into a universal proof.

## P0-1 execution-loop decision refinement (source candidate, 2026-11-08)

The first split of the 2,121-line `OrdivonAgentLoop._run` extracts only
two side-effect-free, O(1) operators: `run_deadline_selection.py` and
`provider_retry_policy.py`. The enclosing loop retains dynamic clock
reads, Tool/Provider authority, reconciliation and external-effect truth.
No new scheduler, generic model router or persistence registry is created.

- **Specification:** Earliest effective deadline with original tie priority;
  only pre-dispatch-safe, transient Provider failures are eligible for
  bounded retry, subject to remaining Run authority and cancellation.
- **Implementation:** `src/ordivon_harness/ordivon/loop.py` consumes both
  operators; unsafe Provider outcomes bypass live clock/deadline reads and
  cannot be retried.
- **Differential refinement:** `tests/test_loop_decision_operators.py`
  compares finite products of the new decisions with the previous loop's
  explicit arithmetic and predicate. This is *bounded*, not a universal
  mathematical proof.
- **Real consumer:** `tests/test_loop_decision_consumer.py` invokes the
  real `OrdivonAgentLoop.run()` with an in-memory scripted Provider:
  expired assignment rejects dispatch; earlier external deadline wins;
  pre-dispatch-safe transient error retries once; ambiguous dispatch
  results in `PROVIDER_STATE_UNKNOWN` without redispatch.
- **Native evidence:** Windows Runtime workspace
  `ws-gpt6-harness-formal-windows-20261108-r2`, baseline
  `fc0fbfdf43c53a988b7af27a762856e491151ce1`, QGIS Python 3.12.13:
  11 focused tests PASS; 32 tests across five core suites PASS;
  20 Provider/ToolProgram/transport tests PASS; 15 selected suites:
  106 PASS, 3 FAIL at old SQLite Store `os.O_NONBLOCK` before the
  intended assertions (95 subtests PASS). The scopes overlap.
- **Re-qualified source:** Locked Python 3.15.1, complete tests, native SANY/TLC,
  real isolated PostgreSQL 18.6, pinned Ruff, `mise run verify`, source-built
  wheel and isolated installed CLI readback now PASS. Remaining distinct
  obligations: deployed production PG/Runtime/Gateway/Provider reconciliation,
  real production consumer readback and domain acceptance. Bounded models are
  not unbounded Python proofs.
- **Legacy removal after upstream backend-neutral refactor:** The
  former `ordivon/sqlite_run_store.py`, `ordivon/sqlite_agent_bridge.py` and
  `ordivon/sqlite_runtime_bridge.py` are already gone; `run_continuity.py`,
  `agent_bridge.py` and `runtime_bridge.py` are their actual consumers.
  `sqlite_store.py` remains imported by `agent_run.py` and
  `ordivon/continuity_guards.py`; do not infer that direct Python API
  is retired from PG-only CLI. Require native PG evidence and actual installed
  consumer replacement; do not migrate disposable Runtime SQLite data.

### CI PostgreSQL coverage closure (2026-11-08)

The exact source candidate was retested with five distinct databases in one
isolated, disposable PostgreSQL 18.6 cluster. All previously conditional
PG suites passed **86/86**, followed by the full locked Python 3.15.1 suite
with **1,490 PASS, zero SKIP/FAIL, and 254 subtests PASS**. This verifies
fixed-schema operations, real transactional accounting, concurrent Turn
Effects and Wake/Conversation Binding consumers. The server was stopped
and its temporary data were deleted.

The existing Monorepo Required `owner-verification` GitHub Actions job
already has a per-shard `postgres:18.6` service for other native Owners.
When selecting `harness:verify`, its workflow now creates five dedicated
databases in **that same ephemeral service** and passes five DSNs to the
existing `mise run verify`. Absent service/database/connection must FAIL
instead of yielding quiet PostgreSQL skips. Explicit `mise run pg:verify`
requires all five DSNs and runs the five native PostgreSQL test modules.

**Remote CI status:** this new workflow wiring is source-authored and still
requires live PR #1835 job evidence after push. Local 1,490/1,490 and
GitHub CI acceptance remain distinct claims, and neither proves production
deployment or physical Provider delivery.
## Native qualification — bounded source candidate (2026-11-08)

**Source:** Linux Runtime workspace `ws-gpt6-harness-verification-20261108-r3`,
imported as an exact SHA-256-verified Git bundle from the Windows candidate.
Execution-core Ruff corrections were captured in `e8f969ef31b681a3c29575cddda717d85f5b119d`;
the feature branch was subsequently rebased onto updated upstream main.
Any subsequent source change requires re-running affected gates.

| Gate | Native evidence / explicit boundary |
| --- | --- |
| Python / lock | Python 3.15.1, `uv lock --check --offline` and `uv sync --locked` PASS; pinned Playwright 1.63.0 installed |
| Static / contracts | Ruff 0.17.2 PASS after two small fixes; CrossHair reported 2 confirmed postconditions in official `mise run verify` |
| Formal | Runtime-pinned TLC 1.7.4: ToolProgram 33 distinct bounded states and 3/3 negative probes PASS; ProviderClaim 78 states / 5 probes PASS; ConversationBinding 10 states / 3 probes PASS |
| Full source tests | `mise run verify`: **1,404 PASS, 86 conditional SKIP, 254 subtests PASS**, zero failures, `ResourceWarning` treated as an error |
| PostgreSQL | Real isolated PostgreSQL **18.6**, local Unix socket and temporary storage, `mise run pg:verify` **13 PASS / 0 SKIP**; stopped and deleted after tests |
| Release candidate | Official `mise run verify` exit 0: `pip-audit`, doc/evidence/dependency checks, deterministic Agent Run demo, offline-built `ordivon_harness-0.6.0-py3-none-any.whl` with 12 installed CLI checks |
| Outside tested scope | Production installed revision, physical Provider/Runtime effects and domain acceptance remain **NOT_RUN**; TLC state exploration does not establish arbitrary implementation refinement |

PG integration and the 86 conditional skips belong to separate scopes: do
not count the skipped tests as passed. Do not treat a source-built installed
wheel in a temporary environment as production deployment.
## Current portable gate

The current release gate includes:

- compile and Ruff;
- complete deterministic suite with `ResourceWarning` as error;
- exact dependency and lockfile checks;
- Host import-boundary tests;
- stable API contract tests;
- semantic-history validation tests;
- documentation and evidence-index validation;
- wheel metadata validation, isolated installation, CLI smoke testing and dependency audit;
- bounded atomic Event-batch replay/rollback tests and the deterministic scale smoke.
- Agent Automation pre-switch Browser Security qualification after admission closure and workflow drain, using same-carrier LKG comparisons across the Browserless pool. Drift is localization evidence only; the qualification never claims provider-authoritative root cause.

## Evidence index and revision binding

`evidence/index.json` classifies every repository `evidence/*.json` object and `scripts/check_evidence.py` enforces exact file correspondence, revision binding and `verified` currentness.

Two revision-binding modes are supported:

- **embedded** — the default legacy receipt mode. The payload itself must carry the exact implementation/source revision recorded by the index.
- **index-creation-lineage** — explicit opt-in for immutable research projections/results whose frozen payload shape does not carry the legacy receipt revision field. The index revision must be an ancestor of the evidence file's unique Git creation commit, no invalidating implementation path may change before evidence creation, and the evidence bytes must remain identical to the creation commit. Recognized embedded tested-revision hints, when present, must agree with the index.

The second mode does not make the index semantic truth owner. It binds repository provenance/currentness without rewriting frozen evidence bytes.

A `verified` entry is current only while no later invalidating implementation path has changed after its bound revision. Once that condition fails, the evidence remains useful historical evidence but must be demoted rather than silently certifying current code.

## P0 PostgreSQL scale acceptance

Use a disposable PostgreSQL test database and set HARNESS_PG_TEST_DSN before
running the scale program or scripts/local-acceptance run. The program creates
a fresh uniquely named schema, checks PostgreSQL Run/Event/CAS digest
referential completeness and full history after reconnect, and drops only that
schema. The receipt kind is ordivon.harness-pg-scale-acceptance; it is not
comparable to historical SQLite filesystem/object-file measurements. No old
Run data are migrated, retained, or required.


The full P0 persistence closeout uses:

```bash
uv run python scripts/harness_p0_scale_acceptance.py \
  --runs 1000 \
  --events-per-run 100 \
  --batch-size 99 \
  --output evidence/hho-p0-scale-1000x100-<revision>.json
```

The receipt must bind the exact implementation revision and prove 1,000 Runs, 100,000 Events, a healthy full-history Doctor after reopen, PostgreSQL object/digest reference closure, and sampled current-Run inspection below the recorded one-second gate. Thresholds and machine measurements remain in the receipt rather than becoming timeless prose.

## Historical live receipts

`evidence/index.json` classifies repository evidence. Existing Codex, Hermes, DeepSeek, Runtime and replacement/recovery receipts are historical because they bind commits before current `main`. They remain valuable evidence for those trajectories but must not be described as certification of current code.

## Current live acceptance

A current release-changing Provider, Runtime, recovery or completion path should produce a new receipt containing:

- Harness Git commit and package version;
- Protocol revision, and Host/caller revision only when that caller participates in the exercised graph;
- Runtime identity and Tool catalog digest when Runtime Tools participate;
- Provider adapter/model identity;
- caller reference and Harness Run identity;
- relevant Tool Step and Provider Call identities;
- final status and explicit unknowns;
- receipt integrity digest;
- limitations.

The canonical command is `scripts/local-acceptance run` on an owner-trusted acceptance environment.

A deletion-only recovery change needs evidence for the capability that actually remains. If the retired path has no current writer/consumer and retained-state census finds no instances, do not recreate the obsolete writer merely to manufacture a "live" trajectory. Bind the exact pre-evidence implementation revision, prove writer/consumer and retained-state absence with bounded read-only evidence, regress the surviving Recovery/UNKNOWN path, and run the normal portable gate. Such a deletion receipt proves the scoped retirement; it does not generalize absence beyond the observed authorities.

## Claim discipline

Use these terms consistently:

- **operational**: repeatedly exercised in the supported graph;
- **experimental**: implemented and tested, but public behavior may still change;
- **verified in pinned graph**: deterministic/live evidence exists for named revisions;
- **historical**: evidence exists only for an earlier graph;
- **unsupported**: no contract or safe path exists.

Tests and evidence verify bounded behavior. They do not turn Runtime success into semantic Task completion or remove Provider/domain uncertainty.

## Browser Security release qualification

Agent Automation activation uses the immutable candidate's own `browser_security_pool_runner.py` and `browser_security_witness_source.py` after new admission is closed and the production Temporal task queue is drained, but before the worker stops and before `/opt/ordivon/agent-automation/current` changes. The runner verifies Security-v2 LKG bundle digests, observes the current Browserless pool through neutral/read-only probes, and delegates canonicalization/classification to Security-v2.

The release owner admits only `NO_OBSERVED_DRIFT` as an automatic PASS. `DETECTOR_DRIFT`, `GLOBAL_DRIFT`, `CARRIER_LOCAL_DRIFT`, `MIXED_DRIFT`, malformed receipts, baseline digest failure, busy carriers, or collector failure produce HOLD. A private `0600` qualification receipt binds the candidate commit, Security revision, pool identity/index digest, classification standing, and the explicit facts that no provider challenge was visited and no provider SEND was attempted.

This is a **pre-switch currentness gate**, not proof of the behavioral effect of a Browserless/Chromium launch change that has not yet been deployed. Browser-substrate mutation still requires a separate candidate/canary and post-change witness transaction before promotion.

## Browserless paired image canary

Browserless/Chromium image changes are qualified before production mutation with reserved instance 91. The control image is discovered from the installed rendered production Quadlet; candidate identity is an exact locally present OCI digest. Active production carriers are cross-checked against the Quadlet while sleeping on-demand carriers are accepted as normal lifecycle state. Control and candidate run sequentially with an empty profile class, the same Network-v2 namespace, equivalent Ordivon-owned environment, 1440x1000 headful Xvfb geometry, and the same neutral Browser Security detectors.

Acceptance requires the same-image control to return `PASS_CONTROL_REPRODUCIBLE`. A different image may carry expected browser/control identity changes, but any detector-shape drift, Network-v2 authority drift, challenge metadata drift, or CF02-CF07 public observation change fails closed. The canary receipt explicitly records `productionMutationAttempted=false`, `providerChallengeVisited=false`, `providerSendAttempted=false`, and `rootCauseEstablished=false`.

The 2026-09-18 negative control passed; a genuinely different older local image was held because PeetPrint and User-Agent changed. Production carriers were not restarted or rewritten in either run, and reserved instance 91 left no container, profile, X socket, or Xauthority residue.


## Browserless image promotion transaction

Promotion verification is split across authority owners. Harness verifies exact source/rendered/installed Quadlet identities, the image identity of every active carrier, the preserved active/inactive lifecycle topology, exact paired-canary receipt, Network-v2 generation, admission fencing, Temporal/browser quiescence, staged qualification health, rollback, and durable post-change evidence. Security-v2 independently rebuilds candidate bundles from manifests and recomputes old-LKG versus candidate pool drift before it may reseal per-carrier LKG fixtures.

After reseal is reviewed and committed, Harness finalize requires: the promotion gate is still closed, MCP is still stopped, the worker remains active, no Workflow/browser session is active, the Security-v2 revision differs from the pre-reseal revision, the pool-index digest differs from the pre-reseal digest, and a fresh live pool against that new index returns `NO_OBSERVED_DRIFT`. Any failure preserves the closed gate; image-mutation failures additionally restore the pre-attempt Quadlet and carriers.

A current-image live read-only plan on 2026-09-18 returned `NOOP_ALREADY_CURRENT`, with rendered source Quadlet SHA-256 exactly equal to the installed Quadlet and every active carrier on the same control image; sleeping carriers are represented explicitly instead of forcing residency. MCP/worker remained healthy and admission stayed open. No real different-image `--apply` has been executed as part of this acceptance.
