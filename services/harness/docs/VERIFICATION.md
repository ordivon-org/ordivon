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
updated: 2026-11-21
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
SQLite. An Owner PostgreSQL qualification shard can supply HARNESS_PG_TEST_DSN
from a dedicated disposable test service. Tests create isolated unique schemas
and drop only those schemas. The portable queue/release wheel gate validates
metadata, isolated installation, imports and CLI even without this authority,
but explicitly reports the Host-free PostgreSQL smoke as NOT_RUN. Supplying
HARNESS_PG_TEST_DSN makes that smoke mandatory and fail-closed. Local real
PostgreSQL qualification must use an equivalent test-only DSN; no old SQLite
Run data are migrated or replayed. Missing PG authority is SKIPPED or NOT_RUN,
never a PASS receipt.

## Test quality: stable behavior before file layout (R37)

A test is a **business or mechanism contract**, not an obstacle to retiring a
Python file. Moving a class, renaming a private helper, splitting a large
module or deleting an unused historical implementation must not fail a test
when its actual documented consumer behavior stays identical.

- **Normal behavior**: create real Agent/domain entrypoints and assert their
  visible Tool definitions, Run stop reason, observations and output.
- **Denial behavior**: supply unknown, duplicate and ungranted Tools and verify
  rejection **before** a Domain/Runtime effect. Exercise empty Tool grants as
  cognition-only, not as wildcard authority or a fatal error.
- **Identity and concurrency**: test one immutable original Grant/Run across
  adversarial W1→W2 mutations by invoking the supported Factory/Run behavior.
  Do not monkeypatch a variable in a particular implementation source file.
- **Physical truth**: tests using fake MCP clients are contract tests only.
  Workspace loss, native job spawning, cancellation, output-byte delivery and
  Finalizer release require isolated real PG18/Runtime/OS consumers and
  immutable independent readback; an empty test fixture cannot certify them.
- **Boundary and provenance**: architecture-wide imports may be checked as a
  package dependency property, and published API/tool/CLI contracts may be
  checked for stability. A test must **not** prohibit arbitrary retired
  filenames, hardcode the module containing a class, or require obsolete
  planning node IDs. A historical file path is test data only where the exact
  external artifact is itself the user-visible contract.
- **Refactoring verification**: maintain a bounded pre-change negative where
  a business defect is repaired, run affected original consumer regressions,
  the complete isolated PG18 suite, source imports, Ruff, docs, evidence and
  installed Wheel checks. Record skipped and unknown physical proof honestly.
- **Test retirement**: replace a source-location assertion with the mechanism
  it was meant to protect. If that behavior is already covered in an
  independent whole-package or end-to-end test, retire the duplicate rather
  than force a historical file to exist. Formal properties constrain
  state/effect transitions, not directory names.

These rules permit finer Agent-facing modules without reducing the strength
of authorization or physical delivery evidence. The R37 module split keeps
`domain_tools` and `plugin_gateway_effect` as stable consumer entrypoints;
tests assert real grants, no-effect cognition, Gateway source identity and
same-Run exact execution rather than the old file that defined a helper.

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

## P0 scale acceptance

The full P0 persistence closeout uses an explicitly provided dedicated PostgreSQL test database (set `HARNESS_PG_TEST_DSN` first; never use the production DSN):

```bash
uv run python scripts/harness_p0_scale_acceptance.py \
  --runs 1000 \
  --events-per-run 100 \
  --batch-size 99 \
  --output evidence/hho-p0-scale-1000x100-<revision>.json
```

The receipt must bind the exact implementation revision and prove 1,000 Runs, 100,000 Events, a healthy full-history Doctor after reopen, exact original PostgreSQL object and event-edge cardinality, no orphan objects or outstanding leases, and sampled current-Run inspection below the recorded one-second gate. Each trace payload has a distinct Run/Event identity so CAS deduplication cannot mask the measured workload. Persistent output requires a clean, commit-bound source; dirty-tree smoke output is explicitly unqualified. Thresholds and machine measurements remain in the receipt rather than becoming timeless prose.

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

## Native Workspace-backed Run acceptance (R8 open gate)

A release claiming safe Workspace-backed PAUSED resume must establish the
**source / installed / physical / domain** boundaries independently. As of
2026-11-16, Runtime Job `job-01a1e41a-ca97-775b-ab8d-48c231b6455a`
provides a genuine failing physical baseline, not a repaired acceptance.
The requirement is to replay the relevant scenario against a candidate
using two independent PostgreSQL databases and an actual native Git Workspace;
a mocked Gateway or a passing TLA model alone is insufficient.

| Real consumer scenario | Required acceptance |
| --- | --- |
| PAUSED with frozen Workspace grant and **zero Tool calls** | HELD certified before the first pausable model turn; ordinary non-force close rejects; original Run still reopens and uses the same native Workspace |
| Native close races native claim reserve | Reserve-first prevents close; close-first prevents a false claim; lost reserve response uses the exact original key for readback |
| Run edits source while HELD | Subsequent original-Run Tool calls still work; changing `sourceStateDigest` does not change native Workspace incarnation or silently issue a new claim |
| Two Run claims share one Workspace | Terminal Run A release cannot remove PAUSED Run B's Workspace; all active claims must be separately resolved |
| Provider or Tool outcome UNKNOWN | Never certify Run finalization, release a needed claim, or blindly redispatch an uncertain external effect |
| Authenticated terminal / explicit successor and real output delivery | Native claim release succeeds only after grant seal, Tool settlement and Git/Artifact/domain consumer evidence; legal close then succeeds with a freshly read close-CAS digest |
| No-Tool or non-Workspace tool Run | Remains executable without unnecessary long-lived Workspace claim or deadlocked cleanup |
| Coding hidden DomainQA PASS without required artifacts | Delivery stays unverified until the exact Git commit/patch or Runtime Artifact is persisted and a downstream consumer independently reads the bytes and acknowledges them |
| Terminal Run with any earlier unsettled Provider/Tool intent | Read the complete original PG ordered Run event chain; any UNKNOWN or unqualified effect prevents certified release |
| Issuer revoked after admission but before native process spawn | Separately qualify native issuer currentness; Workspace claim success is **not** an OS-spawn revocation proof |

For the normal Coding path also use the existing real-Provider
`tests/test_live_coding_task_r4.py` and independent
`evals/harness-edit-addressing-002/qa.py` hidden verifier.
Its historical success proves one specific hidden QA result, not durable delivery of the model-edited patch. For this case, record `DomainQA_PASS` and `DELIVERY_TO_CONSUMER_UNVERIFIED` until an original-byte consumer readback exists. Check the
original Harness PostgreSQL Provider/Tool rows, native Runtime Job/Artifact
bytes, the model's later Tool-output consumption, the exact Git diff,
domain PASS/FAIL/UNKNOWN and measured token/cost/time separately. No
individual Job exit code, model candidate or CI PASS implies TaskSolved.

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

### R38 original effect source coverage (2026-11-24)

Original Run recovery and finalization reads must reject missing historical
revision pairs and missing persisted PG event payload edges, even when the
last revision matches and the CAS object still exists. The existing
`test_postgres_harness_store.py` includes the real-PG fixture with a
truncated-read fault and a detached-edge fault; the latter changes only the
disposable PostgreSQL schema. The supported source-read APIs are unchanged.
The native formal gate uses `OriginalSourceCutR1` with a safety check, an
expected old-tail-only counterexample and an expected positive-acceptance
reachability witness. Bounded model PASS does not imply SQL implementation,
all native Attempts, OS no-future-spawn or real recipient delivery.

R38 candidate validation: isolated original PostgreSQL test environment,
1746 passed, 74 skipped, 5 deselected and 406 passing subtests. The first
invocation without a workspace-local environment exposed four legitimate
owner-environment tests; the original locked offline environment was
materialized and the unmodified tests reran green. Formal gate, dependency
boundary tests, Ruff, documentation and evidence-contract checks passed.
Production install and real Domain/OS finalization remain distinct.

### R39 request identity and pure budget recovery

The original Run prepare path must reject a new Intent with an already used
Runtime clientRequestId without advancing the original PG revision. A new
distinct key is accepted; deliberately persisted legacy conflicts still fail
the full issued-source inspection. Fault injection follows the actual
public continuity method, not a retired source filename.
The original TLC ToolUnknownRecoveryR1 model includes key-reuse and
fresh-next-admission probes. Runtime cross-principal and physical effect
qualification remain separate. Budget reconstruction tests check retained
usage, conservative provider accounting and caller-progress reset without
resetting resource debits or hiding invalid retained limits.

### R40 original Store terminal coverage

Direct normal PG terminal admission must refuse a partial original history
that hides a pending Tool, and a detached original payload edge, without
advancing the Run or consuming its lease. The original consistent Doctor
validator is reused on the exact cut inside the original locked transaction.
The SourceCut bounded model adds a terminal safety check and unsafe omission
and legitimate acceptance probes; actual SQL and OS/Domain release remain
separate evidence obligations.

### R41 PostgreSQL Store source responsibilities and snapshot

The PG Store facade retains the single original connection and atomic
Writer. Source-level facets isolate schema, pure codecs, immutable objects,
queries, leases and integrity; public behavior remains on the original
Store, with the intentional global Doctor snapshot correction. Verify the
real concurrent new-Run counterexample, the stable caller snapshot
positive, the standalone Doctor and nested single-Run validation. The
`DoctorSnapshotR1` bounded model uses the existing TLC gate with weak
snapshot and nonvacuous concurrent stable-snapshot probes.

The actual normal terminal consumer with settled original Provider and Tool
effects and its Doctor must succeed without opening a Run command facade.
The shared original immutable Provider reader preserves the same identity,
state, request, result and failure checks; the negative pending-effect
regressions remain in the same real PostgreSQL suite.

Source inspection consumes the exact original history cut returned by the
existing validation port. The real PG fixture substitutes a second
same-revision read after successful validation: the original code loses
the issued Tool, the new consumer uses exactly one Journal read and retains
the original identity. Concurrent append and actual missing-edge regressions
remain enforced; the original SourceCut formal gate adds a reread and
positive consumption probe.

### R42 verified new effect admission and PG experiment consumers

Real PostgreSQL fixtures retain pending Tool A and exercise both new Tool
and Provider admission with an injected partial read. The original writer
accepted each new effect before the correction; both must reject without
advancing Run revision now, with positive settled/replay paths retained.
The original SourceCut model covers distinct new-effect admission and
nonvacuity using the same TLC gate.

Adaptive Edit and Scale share the existing disposable test PG schema
lifecycle. A deterministic Provider fixture executes an actual in-memory
read/edit sequence and checks visible/hidden verifiers, oracle bytes, PG
Doctor, failure cleanup, and pre-existing schema collision safety. This is
not paid model performance or physical Runtime qualification.
