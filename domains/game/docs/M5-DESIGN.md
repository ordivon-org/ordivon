# M5 design — replay, diagnosis, comparison, experiments, and first playable release

Status: design only; no M5 runtime or Web implementation is authorized by this document
Tracking: Issue #7
Depends on: M4 closeout at `main@2427aad4d35e76ffb3ab479f60be8c2239f5c9c8`
Audit: [`M1-M4-DEBT-AUDIT.md`](M1-M4-DEBT-AUDIT.md)

## 1. Why M5 is required

M4 completed the first trustworthy player control loop:

```text
configure
→ review Proposals before mutation
→ intervene
→ commit one verified Tick
→ inspect the result
```

The player still cannot complete the learning loop after a Run:

- reconstruct the station at any earlier revision;
- see one coherent record joining World, Team, authority, Message, and player evidence;
- identify which turns materially changed the outcome;
- distinguish a direct terminal mechanism from a contributing decision;
- compare two compatible Runs without reading raw journals;
- change a meaningful initial configuration and test whether the result improves;
- execute a bounded matrix locally or through Ordivon Runtime;
- verify that a downloadable first-playable artifact corresponds to the evaluated source.

M5 closes:

```text
Run
→ Replay
→ Explain
→ Compare
→ Configure
→ Re-run
→ Release
```

M5 is not a larger game, a generic analytics platform, or another Agent layer.

## 2. Product objective

The first playable is complete when a player can:

1. choose one explicit Station Zero Scenario Case and loadout;
2. configure the three specialist Providers and authority policy;
3. play or auto-advance a bounded mission through Mission Control;
4. open the completed Run in Replay;
5. scrub every verified World revision;
6. inspect resource curves, Objective transitions, Proposals, authority, player interventions, Messages, and verified Facts;
7. receive an evidence-backed diagnosis of a failure or success path;
8. compare the Run with one compatible alternative;
9. re-run a changed configuration and observe a verified outcome difference;
10. reproduce the complete slice from a clean source release and verify its manifest.

## 3. First principles

### 3.1 Replay derives from existing authority

World Commands, Events, Snapshots, Team records, Host Journal Events, and Artifacts remain authoritative. Replay views, diagnosis, curves, comparisons, and experiment reports are disposable projections.

M5 creates no replay truth table and no analytics database.

### 3.2 Sequence is authoritative; wall-clock time is metadata

Causal and execution order is defined by:

```text
World revision
Team Round worldRevision
Host Journal sequence
Task/configuration revision
typed identity links
```

`createdAt` may be displayed or used as operational telemetry only where explicitly measured. It is not used to infer causal order because historical Host Journal timestamps are not integrity-bound.

### 3.3 Diagnosis must preserve evidence class

M5 does not promise philosophical or statistical causality from one trace. It produces an evidence-backed diagnosis with explicit classes:

```text
VERIFIED_DIRECT
VERIFIED_CONTRIBUTOR
COUNTERFACTUAL_SENSITIVE
CONTEXT_ONLY
```

Model-generated prose is not required and cannot upgrade evidence.

### 3.4 Configuration must change semantics

A control is configurable only when it changes Genesis, deployment, authority, communication, or Provider routing in a retained and verifiable way.

A seed label that does not alter Genesis is not a scenario variable.

### 3.5 Comparison requires compatible inputs

A causal/configuration comparison requires the same:

- Scenario and Ruleset versions;
- Scenario Case;
- comparable metric definitions;
- evaluated-input contract.

Cross-case comparison is descriptive and is labelled as such.

### 3.6 Experiments remain bounded

M5 does not enumerate every combination. Deterministic release matrices contain at most 16 cells. More than four two-level factors require screening or an explicit subset rather than a full factorial.

### 3.7 Runtime executes experiments; Game defines them

Ordivon Game owns:

- Scenario Cases;
- deployment manifests;
- experiment cell semantics;
- Run execution command;
- result and evidence schema;
- aggregation and comparison.

Ordivon Runtime owns:

- Job and Attempt identity;
- process execution;
- cancellation;
- physical retry/recovery;
- stdout/stderr and Artifact retention;
- resource and elapsed-time telemetry.

Game does not import Runtime internals or add Runtime Job tables.

### 3.8 Release provenance must survive squash and clean clone

The primary evidence identity is a canonical evaluated-input manifest and digest. A Git commit/tree is additional metadata, not the sole binding.

## 4. Scope boundary

### 4.1 M5 owns

- M1–M4 release-critical debt hardening;
- point-in-time verified World reconstruction;
- unified Run Evidence Graph;
- revision-based replay frames and true pagination;
- resource/system/health/item curves;
- deterministic key-turn extraction;
- evidence-backed outcome diagnosis;
- compatible Run comparison;
- immutable deployment manifests;
- deterministic Scenario Cases and constrained loadout profiles;
- product catalog derived from backend contracts;
- bounded experiment manifests and local execution;
- Ordivon Runtime cell-execution contract;
- replay and compare Web surfaces;
- one real Chromium end-to-end first-playable journey;
- evaluated-input manifest, source-playable release artifact, verification command, and final receipt.

### 4.2 M5 does not own

- a new World or Host authority;
- full Host Journal migration or projection rebuild;
- item-transfer or negotiation mechanics;
- strategy correction for Codex or Hermes;
- model-generated causal explanations;
- a general analytics warehouse;
- OpenTelemetry, MLflow, Temporal, or an experiment service dependency;
- arbitrary scenario sliders;
- uncontrolled random generation;
- a general Ordivon game platform;
- multiplayer, accounts, modding, 3D, or persistent society simulation.

## 5. Reference architecture

M5 adds four derived/orchestration modules above the frozen M1–M4 system:

```text
┌────────────────────────────────────────────────────────────┐
│                    First-playable Web                      │
│ Mission Control · Replay · Diagnosis · Compare · Configure │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ Replay / Diagnosis Projection                              │
│ RunEvidenceGraph · ReplayFrame · Curves · KeyTurns         │
│ RunDiagnosis · RunComparisonView                           │
└──────────────────────────────┬─────────────────────────────┘
                               │ pure reads
┌──────────────────────────────▼─────────────────────────────┐
│ Existing Game + Host evidence                              │
│ World Commands/Events/Snapshots                            │
│ Team Rounds/Contexts/Proposals/Authority/Messages          │
│ Player control Events/Effects/Dispatches/Observations      │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ Experiment / Release orchestration                         │
│ DeploymentManifest · ExperimentSpec · Result Artifacts     │
│ local executor or external Ordivon Runtime Jobs            │
└────────────────────────────────────────────────────────────┘
```

Suggested module boundaries:

```text
src/replay/model.ts
src/replay/store.ts
src/replay/evidence.ts
src/replay/frames.ts
src/replay/diagnosis.ts
src/replay/compare.ts

src/experiments/model.ts
src/experiments/catalog.ts
src/experiments/deployment.ts
src/experiments/runner.ts
src/experiments/aggregate.ts

src/release/inputs.ts
src/release/manifest.ts
src/release/verify.ts
```

Names may adjust to actual code pressure, but replay/experiments must not be added to the existing Mission Control projection monolith.

## 6. M5.0 — release-critical hardening

M5 begins with a small hardening slice before replay UI.

### 6.1 truthful Scenario identity

`RunMetadata.seed` remains for compatibility but the product does not describe it as an environment variation unless the Scenario consumes an RNG.

Add:

```ts
interface ScenarioCaseDefinition {
  schemaVersion: 1;
  caseId: string;
  scenarioId: string;
  scenarioVersion: number;
  label: string;
  description: string;
  genesisSpec: ScenarioGenesisSpec;
}
```

`ScenarioGenesisSpec` uses typed, bounded fields rather than arbitrary object patches:

```ts
interface ScenarioGenesisSpec {
  resources?: {
    batteryInitial?: number;
    oxygen?: number;
    reactorHeat?: number;
  };
  mission?: {
    turnLimit?: number;
  };
  crew?: Record<string, { health?: number }>;
  systems?: Record<string, { integrity?: number; powered?: boolean }>;
}
```

World invariants validate the resulting Genesis. Cases cannot add arbitrary Commands, alter reducers, or bypass conservation.

Initial measured candidate cases:

| Case | Proposed Genesis difference | Measured Security path | Measured Engineer-seal path |
|---|---|---|---|
| `baseline` | current Scenario v2 | victory, Tick 18 | victory, Tick 22 |
| `power-constrained` | battery 50 instead of 56 | victory, battery 2 | `power_exhausted`, Tick 21 |
| `oxygen-constrained` | oxygen 62 instead of 78 | victory, oxygen 55 | `team_incapacitated`, Tick 19 |

These measurements establish useful case semantics. Exact names and values become contracts only after implementation tests freeze them.

### 6.2 build and evaluated-input identity

Remove milestone-specific `CURRENT_BUILD` drift.

Define:

```ts
interface EvaluatedInputManifest {
  schemaVersion: 1;
  product: string;
  packageVersion: string;
  scenarioContracts: Array<{ id: string; version: number }>;
  rulesetContracts: Array<{ id: string; version: number }>;
  files: Array<{ path: string; sha256: string; bytes: number }>;
  evaluatedInputsDigest: string;
  sourceCommit: string | null;
  sourceTree: string | null;
}
```

Canonical input set:

- `src/**`;
- `web/**`;
- executable release/evaluation scripts;
- `package.json`;
- `pnpm-lock.yaml`;
- Scenario Case definitions;
- Playwright configuration and release E2E.

Generated docs, reports, database files, `node_modules`, and distributable archives are excluded to avoid circular identity.

### 6.3 real timeline paging

The bounded Mission Control state keeps only recent history. Replay endpoints query retained Rounds and World Events directly by revision.

The old Mission Control timeline endpoint remains compatibility-only or becomes a thin alias to the new replay query.

### 6.4 explicit timestamp contract

Documentation and conformance tests state:

```text
sequence/revision = authoritative order
timestamp = metadata
```

M5 does not silently change historical Journal digest semantics.

### 6.5 22-Tick bound

Add a direct Engineer-seal test asserting:

```text
terminal Tick = 22
MissionControlView <= 64 KiB
```

The audited current size is 17,009 bytes.

### 6.6 product catalog

Expose a read-only catalog containing:

- Scenario Cases;
- loadout profiles;
- Actor identities and roles;
- role Objective options;
- Provider options;
- authority modes;
- compatibility/deprecation markers for debug APIs.

Web deployment controls consume this catalog instead of duplicating domain constants.

## 7. Immutable deployment manifest

Every M5 Run used for comparison or release has one immutable deployment manifest.

```ts
interface RunDeploymentManifest {
  schemaVersion: 1;
  runId: string;
  scenario: { id: string; version: number; caseId: string; genesisDigest: string };
  ruleset: { id: string; version: number };
  loadoutProfileId: string;
  actors: Array<{
    actorId: string;
    role: string;
    initialProviderOrder: string[];
  }>;
  authorityPolicyMode: "autonomous" | "supervised" | "locked";
  coordinationProfileId: string;
  evaluatedInputsDigest: string;
  createdWithBuild: string;
}
```

Persistence:

- content-address the manifest as a Host Artifact;
- add one run-to-manifest link with a checked Host Event head;
- prohibit replacement after the first World revision or first Team Context;
- subsequent Provider replacement and player commands remain retained events, not manifest mutation.

This solves comparison provenance without moving live Provider routing away from existing Tasks.

## 8. Loadout and coordination profiles

### 8.1 constrained profiles, not arbitrary sliders

A loadout profile defines item placement at Genesis while preserving `initialItems` exactly.

```ts
interface LoadoutProfile {
  profileId: string;
  label: string;
  actorInventory: Record<string, Partial<Inventory>>;
  roomInventory: Record<string, Partial<Inventory>>;
}
```

Validation requires:

- every item quantity is a non-negative integer;
- total quantity per item equals Scenario initial quantity;
- actors and rooms exist;
- no capability is granted by inventory mutation;
- no system state or mission predicate is edited by loadout.

Required release profiles:

1. `baseline` — current item placement;
2. one measured specialist-forward profile that changes a deterministic failure or materially improves turns/resources;
3. optionally one field-cache profile only if it demonstrates a distinct trade-off.

Candidate specialist-forward intent:

- move some repair parts closer to or onto Engineer;
- move the medkit closer to or onto Medic;
- preserve every item total.

Exact placement is **Unknown** until the implementation experiment proves a useful outcome difference without making the mission trivial.

### 8.2 coordination profile

A coordination profile may define an initial typed Message plan, such as local briefing versus unavailable station radio.

It is not free-form shared chat and does not bypass Message reachability.

The existing local-versus-radio failure becomes one release comparison fixture.

## 9. Point-in-time replay kernel

Add a verified point-in-time operation:

```ts
interface PointInTimeReplayResult {
  runId: string;
  revision: number;
  state: WorldState;
  digest: string;
  snapshotRevision: number;
  replayedCommandCount: number;
  verified: true;
}
```

Algorithm:

1. validate requested revision is an integer from 0 through terminal revision;
2. select the newest Snapshot whose revision is at most the target;
3. verify World command/event streams;
4. replay retained Commands from that Snapshot through target revision;
5. compare each retained before/after digest and Event;
6. return the exact state and digest at that revision.

Properties:

- revision zero equals Genesis digest;
- terminal revision equals current `verifyReplay()` digest;
- replay from different eligible Snapshots converges;
- repeated reads write nothing;
- corrupt or missing evidence fails closed;
- a replay frame never changes the live Run.

## 10. Run Evidence Graph

M5 joins existing records through a typed derived graph.

```ts
interface RunEvidenceGraph {
  schemaVersion: 1;
  runId: string;
  deploymentManifestDigest: string;
  nodes: EvidenceNode[];
  edges: EvidenceEdge[];
  terminalWorldDigest: string;
  graphDigest: string;
}
```

Required node kinds:

```text
run
configuration
world-tick
intent
world-fact
round
context
proposal
authority-decision
authority-grant
player-command
message
effect
dispatch
observation
objective-transition
provider-event
```

Required edge kinds:

```text
previous
configured-by
observed-in
proposed-from
authorized-by
selected-into
dispatched-as
verified-by
delivered-to
contributed-to
blocked-by
superseded-by
```

Rules:

- edges are created only from explicit IDs, revisions, and retained payload relations;
- graph construction is deterministic and read-only;
- missing required identity fails the affected explanation rather than inventing a link;
- graph order uses revision/sequence, not timestamp;
- graph size is bounded by the Run's retained evidence;
- no graph table is persisted for the first playable.

This borrows the minimal idea of trace spans and links—typed operations connected by explicit causal references—without adding an observability SDK.

## 11. Replay frames and timeline

One player frame corresponds to one World revision transition.

```ts
interface ReplayFrame {
  schemaVersion: 1;
  runId: string;
  revision: number;
  beforeDigest: string;
  afterDigest: string;
  before: ReplayWorldSummary;
  after: ReplayWorldSummary;
  round: ReplayRoundSummary | null;
  intents: ReplayIntentSummary[];
  facts: ReplayFactSummary[];
  objectiveTransitions: ObjectiveTransition[];
  authorityEvents: AuthorityAuditEntry[];
  playerEvents: PlayerAuditEntry[];
  messageEvents: MessageAuditEntry[];
  evidenceRefs: string[];
}
```

A frame exposes:

- station map and entity positions after the revision;
- selected and rejected Proposals;
- per-Intent verification;
- resource and item deltas;
- Objective changes;
- authority and player actions relevant to that revision;
- Messages delivered, pending, or expired;
- explicit evidence references for debug inspection.

True timeline pagination:

```text
GET /api/replay/timeline?runId=...&beforeRevision=...&limit=...
```

- direct query over retained revision/Round data;
- descending revision cursor;
- maximum page size 50;
- no dependence on the latest-12 Mission Control view;
- stable next cursor;
- no semantic writes.

## 12. Resource and system curves

Curves are derived by point-in-time replay or one linear replay pass.

Required series:

- battery charge and energy consumed;
- oxygen;
- reactor heat;
- crew health;
- each Actor health;
- system integrity and power state;
- finite item ownership by room/Actor/consumed ledger;
- Objective resolved count.

```ts
interface RunSeries {
  seriesId: string;
  label: string;
  unit: string;
  points: Array<{ revision: number; value: number }>;
  thresholds: Array<{ value: number; kind: "warning" | "terminal" | "victory" }>;
}
```

Current missions are at most 22 revisions. M5 hard-bounds product curves to 128 revisions and rejects unsupported larger Runs rather than silently sampling release evidence.

Web renders plain SVG/CSS. No chart dependency is added.

## 13. Key-turn extraction

Key turns are deterministic annotations over Replay Frames.

A revision is key when at least one of the following occurs:

- terminal mission transition;
- Objective becomes satisfied, superseded, or irrecoverably blocked;
- resource crosses a warning, victory, or terminal threshold;
- finite item is consumed or becomes a demonstrated ownership bottleneck;
- authority is requested, granted, denied, consumed, or expires;
- player redirects, pauses, resumes, cancels, or changes Provider;
- Message delivery/expiry changes an Actor action frontier;
- Provider fails or is replaced;
- an admitted alternative is counterfactual-sensitive.

Ranking is public and lexicographic:

```text
terminal
> direct terminal mechanism
> player/authority intervention
> Objective transition
> resource threshold
> communication/provider event
> other verified contributor
```

The summary returns at most 12 key turns. The full timeline remains pageable.

## 14. Evidence-backed diagnosis

```ts
interface RunDiagnosis {
  schemaVersion: 1;
  runId: string;
  outcome: { status: string; reason: string | null; revision: number };
  headline: string;
  chain: DiagnosisStep[];
  unresolvedObjectives: string[];
  decisiveResources: string[];
  playerInterventions: string[];
  confidence: "verified" | "bounded-counterfactual";
}

interface DiagnosisStep {
  stepId: string;
  revision: number;
  evidenceClass:
    | "VERIFIED_DIRECT"
    | "VERIFIED_CONTRIBUTOR"
    | "COUNTERFACTUAL_SENSITIVE"
    | "CONTEXT_ONLY";
  statement: string;
  evidenceRefs: string[];
}
```

### 14.1 direct terminal mechanism

Each terminal reason has a deterministic explainer tied to World state and Facts:

- `reactor_meltdown` — heat reached terminal threshold;
- `station_asphyxiation` — oxygen reached zero;
- `crew_lost` / `team_incapacitated` — verified health transition;
- `power_exhausted` — battery reached zero before victory predicates;
- `mission_timeout` — turn limit reached with listed unresolved Objectives;
- victory — all verified victory predicates and final distress Fact.

### 14.2 verified contributors

Contributor rules identify retained conditions such as:

- breach remained uncontrolled for a revision interval;
- repair parts were owned by an Actor lacking repair capability while repair Objectives remained unresolved;
- a required Message was pending or expired;
- an authority request or player denial delayed one action path;
- a system consumed battery while no longer required by the remaining Goal;
- repeated `wait` or redundant action consumed scarce Ticks.

A contributor is not labelled the unique cause.

### 14.3 bounded counterfactual sensitivity

At a selected before-state, M5 may enumerate the legal alternate Intent subsets already admitted by the deterministic Ruleset and compare one-step verified deltas.

Optional full terminal continuation is allowed only when:

- the continuation Provider/policy is deterministic and named;
- the branched Run has a separate identity;
- the result is labelled `simulated under <policy>`;
- M5 does not claim the original model would have selected that continuation.

The first playable requires one bounded counterfactual example, not exhaustive branching.

## 15. Run comparison

```ts
interface RunComparisonView {
  schemaVersion: 1;
  leftRunId: string;
  rightRunId: string;
  compatibility: "configuration-comparable" | "descriptive-only" | "incompatible";
  inputDiff: ComparisonInputDiff;
  outcomeDiff: ComparisonOutcomeDiff;
  metricDeltas: ComparisonMetricDelta[];
  objectiveTiming: ObjectiveTimingDiff[];
  keyTurnAlignment: KeyTurnAlignment[];
  diagnosisDiff: DiagnosisDiff;
}
```

Compatibility rules:

- same Scenario, Ruleset, Case, and evaluated-input contract: configuration-comparable;
- different Case but compatible schemas: descriptive-only;
- different Ruleset or incompatible evidence schema: incompatible.

Comparison displays:

- initial Provider/authority/loadout/coordination differences;
- outcome, reason, score, and turns;
- final resources and health;
- Objective resolution timing;
- model calls/tokens/cost/latency only when reported comparably;
- authority and player intervention counts;
- key-turn alignment;
- unexplained evidence gaps.

No synthetic currency or token estimate is inferred when a Provider does not report one.

Required release comparisons:

1. Security containment versus Engineer sealing on baseline;
2. local briefing versus unavailable radio communication;
3. one configuration change that turns a deterministic failure into victory or produces a material verified improvement.

## 16. Experiment model

M5 borrows only the minimal run/parameter/metric/artifact vocabulary used by mature experiment trackers.

```ts
interface ExperimentSpec {
  schemaVersion: 1;
  experimentId: string;
  objective: string;
  evaluatedInputsDigest: string;
  factors: ExperimentFactor[];
  cells: ExperimentCell[];
  execution: {
    mode: "local" | "ordivon-runtime";
    maximumCells: number;
    maximumParallelism: number;
    timeoutMsPerCell: number;
    liveProviderBudget?: LiveProviderBudget;
  };
  metrics: string[];
}
```

One `ExperimentCell` freezes:

- Scenario Case;
- loadout and coordination profile;
- Actor Providers;
- authority mode;
- deterministic policy seed when applicable;
- replication index;
- cell input digest.

One `ExperimentRunResult` contains:

- Run/deployment identity;
- status/reason/score/turns;
- resources/health/Objectives;
- Provider call and failure counts;
- tokens/cost/latency only where reported;
- authority/player intervention counts;
- replay/evidence graph digests;
- result artifact references;
- executor metadata.

### 16.1 design budget

- deterministic release matrix: at most 16 cells;
- deterministic Fixture cells: one replication;
- live Provider study: separately approved, replicated, randomized in order, and budgeted;
- five or more candidate factors: screening or explicit subset, not full factorial;
- local sequential execution is the reference CI path;
- Runtime parallelism must not alter cell result identity.

### 16.2 required deterministic matrix

The exact matrix is frozen after M5 configuration implementation, but it must cover:

- baseline containment and sealing strategies;
- at least two Scenario Cases;
- at least two meaningful deployment/loadout or coordination configurations;
- one known deterministic failure;
- one configuration-improved outcome;
- no more than 16 cells.

## 17. Ordivon Runtime integration

M5 does not embed Runtime. It produces cell commands and consumes results.

Required Game CLI contracts:

```text
pnpm experiment:plan --spec <path> --out <plan.json>
pnpm experiment:cell --plan <plan.json> --cell <cell-id> --out <result.json>
pnpm experiment:aggregate --plan <plan.json> --results <directory> --out <report.json>
```

Runtime execution model:

```text
ExperimentCell
→ one Runtime Job
→ one or more Runtime Attempts
→ Game CLI process
→ result JSON + optional Run database
→ Runtime Artifacts
→ Game aggregate verifies cell/result digests
```

Runtime owns physical elapsed time, cancellation, process exit, stdout/stderr, and Attempt history. Game owns semantic success, replay equality, and experiment metrics.

A Runtime failure cannot be represented as a Game mission failure. It is an executor failure with no fabricated terminal World state.

## 18. Product APIs

Proposed minimal APIs:

```text
GET  /api/mission-control/catalog

GET  /api/replay/summary?runId=...
GET  /api/replay/frame?runId=...&revision=...
GET  /api/replay/timeline?runId=...&beforeRevision=...&limit=...
GET  /api/replay/diagnosis?runId=...

POST /api/compare
```

`POST /api/compare` body:

```json
{
  "leftRunId": "run:left",
  "rightRunId": "run:right"
}
```

Experiment execution and release creation remain CLI operations, not public browser APIs.

All replay/compare GETs are read-only and must produce zero semantic writes.

## 19. Replay and compare Web

### 19.1 terminal entry

The M4 terminal panel gains:

```text
Review mission
Compare with another Run
Configure another deployment
```

### 19.2 Replay page

Primary layout:

```text
Outcome + diagnosis headline
Revision scrubber / key-turn navigation
Station map at selected revision
Resource and health curves
Actor Proposals / selected Intents / verified Facts
Objective transitions
Authority, player, Message, and Provider audit
Evidence references
```

The page initially loads summary and key turns. Frames load by selected revision. It does not download every Context Artifact by default.

### 19.3 Compare page

The player selects two retained compatible Runs. The page shows input differences first, then outcome and evidence differences. It never labels one configuration universally superior when Cases or metrics are incompatible.

### 19.4 Configuration page

Deployment uses backend catalog data for:

- Case;
- loadout;
- coordination profile;
- Actor Provider;
- authority mode.

Only measured, retained configurations are exposed.

### 19.5 browser release evidence

Add one Playwright Chromium journey:

1. launch local server through Playwright `webServer`;
2. create a baseline Fixture deployment;
3. prepare and commit until terminal;
4. verify explicit victory;
5. open Replay;
6. scrub to one earlier revision and verify map/resource change;
7. open a retained comparison or create the required deterministic alternative;
8. verify the comparison identifies the input and outcome difference.

CI:

- one worker;
- Chromium headless shell only;
- trace retained on failure;
- no video/screenshot retention for passing runs;
- browser test is separate from fast unit coverage but required by release CI.

## 20. Release provenance and artifact

### 20.1 version

M5 first playable remains pre-1.0. Proposed package/release version:

```text
0.2.0
```

Release label:

```text
station-zero-first-playable-1
```

The exact tag is frozen during closeout.

### 20.2 release manifest

```ts
interface M5ReleaseManifest {
  schemaVersion: 1;
  releaseId: string;
  packageVersion: string;
  evaluatedInputs: EvaluatedInputManifest;
  cleanCheckout: {
    nodeVersion: string;
    pnpmVersion: string;
    commands: string[];
  };
  evidence: Array<{ path: string; sha256: string }>;
  releaseAcceptance: Record<string, boolean>;
  archive?: { name: string; sha256: string; bytes: number };
  githubAttestation?: { workflowRunId: string; subjectDigest: string };
}
```

### 20.3 local verification

```text
pnpm release:inputs
pnpm release:build
pnpm release:verify
```

`release:verify` must:

- recompute every evaluated input digest;
- run frozen deterministic acceptance/evidence tests;
- verify replay/evidence report digests;
- verify archive digest when an archive is present;
- fail if source, lockfile, case, or release evidence differs.

### 20.4 source-playable archive

On a release tag, CI creates a deterministic source archive from the exact tag/commit and uploads:

- source archive;
- `M5-RELEASE.json`;
- evaluation/experiment report;
- Playwright report only when needed;
- optional attestation bundle.

The archive includes source, Web, package manifest/lockfile, README, LICENSE, and release verification instructions. It excludes credentials, local databases, model sessions, and `node_modules`.

### 20.5 GitHub attestation

For the public repository, release CI may use GitHub artifact attestation to bind the uploaded archive to repository, workflow, and commit identity.

This is additional supply-chain provenance. It does not replace local SHA-256 verification and does not claim the artifact is secure merely because it is attested.

## 21. Metrics and budgets

Required per Run:

- mission status and reason;
- score and turns;
- final battery, oxygen, heat, crew/Actor health;
- Objective resolution timing;
- model call/success/failure counts;
- reported tokens, cost, and latency when present;
- authority requested/granted/denied/expired/consumed counts;
- player pause/resume/cancel/redirect/Provider-change counts;
- stale/rejected Proposal and unresolved Dispatch counts;
- recovery and replay equality;
- unexplained diagnosis gaps.

Required product bounds:

- replay summary <= 96 KiB;
- one Replay Frame <= 64 KiB without expanded Context Artifact;
- timeline page <= 50 revisions;
- curves <= 128 points per series;
- key turns <= 12;
- deterministic experiment <= 16 cells;
- main Mission Control view remains <= 64 KiB at 22 Ticks;
- no runtime dependency added by replay/experiment modules;
- Playwright remains dev-only.

Exact latency targets are not frozen before measurement. Local deterministic replay should remain comfortably sub-second for a 22-Tick Run, but M5 reports measured values rather than designing around an arbitrary threshold.

## 22. Acceptance criteria

### 22.1 debt hardening

1. custom seed is no longer presented as semantic environment variation;
2. three deterministic Scenario Cases produce distinct Genesis digests where their specs differ;
3. new Run build/deployment identity contains no stale milestone string;
4. Host timestamp metadata cannot change diagnosis order;
5. true replay timeline pages all revisions, including those older than 12;
6. Engineer-seal Tick-22 Mission Control response remains <= 64 KiB;
7. Web deployment catalog contains no duplicated hard-coded Provider/Objective contract;
8. release evidence uses a stable evaluated-input digest, not only a branch commit.

### 22.2 replay

1. every revision from Genesis through terminal reconstructs and verifies;
2. terminal point-in-time digest equals current World replay digest;
3. frame Facts and Intents match retained Tick Events;
4. replay reads create no World or Host writes;
5. corrupt evidence fails closed;
6. full timeline pages without gaps or duplicates;
7. curves reproduce known final resource values.

### 22.3 diagnosis

1. one deterministic failure exposes a concrete evidence chain from retained records;
2. direct terminal mechanism and contributors are distinguished;
3. diagnosis contains evidence references for every non-context statement;
4. resource mismatch and delayed communication appear as contributors in their known Runs;
5. one bounded counterfactual identifies a sensitive decision without claiming model intent;
6. victory diagnosis proves all required predicates and the distress Fact.

### 22.4 configuration and comparison

1. deployment manifest is immutable and survives process replacement;
2. loadout profiles conserve every finite item;
3. at least one configuration change turns a deterministic failure into victory or materially improves a verified outcome;
4. containment and sealing strategies remain independently viable on baseline;
5. compatible Runs show exact input and outcome deltas;
6. cross-case comparison is labelled descriptive-only;
7. missing Provider cost/token data is never inferred.

### 22.5 experiments and Runtime

1. the deterministic release matrix contains at most 16 cells;
2. local sequential execution is reproducible;
3. result aggregation rejects missing, duplicate, or digest-mismatched cells;
4. the same plan executed as Runtime Jobs produces semantically identical cell results;
5. Runtime cancellation/failure is reported as executor failure, not Game mission failure;
6. no Game database table stores Runtime Job truth.

### 22.6 product and release

1. one Chromium journey completes deployment through terminal, Replay, scrub, and comparison;
2. trace is retained on browser failure;
3. clean checkout installs and passes unit, property, evidence, browser, receipt, and release verification gates;
4. the exact evaluated-input manifest verifies after clean clone;
5. source archive digest is frozen and locally verifiable;
6. M1–M4 receipts and terminal digests remain valid unless an explicitly versioned Scenario/Ruleset change supersedes them;
7. runtime dependencies remain zero;
8. `M5-RECEIPT.md`, `M5-EVALUATION.json`, and `M5-RELEASE.json` bind the first playable.

## 23. Stop conditions

M5 is complete when the player can learn from one Run and reproduce the release:

```text
play
→ inspect any revision
→ understand the evidence chain
→ compare a meaningful alternative
→ change configuration
→ verify the changed outcome
→ reproduce the exact evaluated slice
```

Stop before adding:

- more scenarios than needed to validate the Case mechanism;
- more experiment cells than needed to answer the frozen questions;
- more charts than the required resource/system series;
- generalized analytics queries;
- automated strategy recommendations;
- new gameplay mechanics.

## 24. Decision summary

The corrected M5 is:

```text
M5.0 truthful identity and paging
→ verified point-in-time replay
→ typed Run Evidence Graph
→ key turns, curves, and bounded diagnosis
→ immutable deployment and meaningful cases/loadouts
→ compatible comparison and bounded experiments
→ external Runtime execution contract
→ replay/compare Web plus one browser journey
→ stable evaluated-input manifest and first-playable release
```

The central design rule is:

> M5 explains and compares retained evidence; it does not become a second authority or a hidden strategist.
