# M1–M4 debt audit — entry conditions for M5

Status: design audit only; no runtime behavior is changed by this document
Audited source: `main@2427aad4d35e76ffb3ab479f60be8c2239f5c9c8`
Tracking: Issue #7

## 1. Audit purpose

M5 is the last milestone before the first reproducible playable release. It must not become a container for every historical imperfection.

This audit classifies M1–M4 residue by one question:

> Does this issue prevent a player or evaluator from replaying a Run, explaining its verified outcome, comparing configurations, or reproducing the release?

Only issues that materially affect that loop enter M5.

Evidence labels used below:

- **Observed** — reproduced directly from current code, retained evidence, or a local execution;
- **Inferred** — follows from observed contracts but has not itself failed in a retained Run;
- **Decision** — M5 scope choice;
- **Unknown** — requires implementation evidence before freezing a value.

Priority labels:

- **M5.0** — harden before replay/configuration features;
- **M5 core** — required to satisfy Issue #7;
- **Deferred** — real debt, not required for first playable;
- **Rejected** — actively excluded because cost exceeds demonstrated value or violates stack boundaries.

## 2. Executive findings

The strongest existing layer is still the deterministic World Kernel. World command/event streams, snapshots, hash chains, recovery, and exact replay already exist. M5 does not need another event store.

The missing layer is a product evidence projection that joins:

```text
World revisions and Facts
+ Team Rounds and Actor Contexts
+ Proposals and authority
+ player commands and Messages
+ deployment configuration
→ replay frames, diagnosis, comparison, and release evidence
```

The audit found seven issues that must be handled before or during M5:

1. `seed` currently changes only a label, not Genesis;
2. `createdWithBuild` still reports `ordivon-game@0.2.0+m2`;
3. Mission Control timeline pagination only filters the latest 12 Rounds;
4. M4 evidence binds to a squash-pre-merge commit that is not an ancestor of `main`;
5. no immutable deployment manifest records the initial case, loadout, Providers, and authority policy together;
6. no browser-level end-to-end evidence proves the playable interaction loop;
7. there is no exact source-playable release artifact and input manifest.

Several other issues are real but must not expand M5:

- Host Journal timestamps are not integrity-bound;
- old M2 projections are not rebuilt from the complete Host Journal;
- Provider order is stored on the long-lived Actor Task;
- Web catalog constants are duplicated;
- Mission Control projection is becoming a large file;
- no item-transfer or automatic resource-negotiation mechanism exists.

M5 addresses only the portions necessary for trustworthy replay, comparison, experimentation, and release.

## 3. M1 audit — deterministic World and persistence

### 3.1 World replay exists but exposes only a terminal result

**Observed**

`GameStore` already retains:

- ordered Commands;
- ordered World Events;
- before/after state digests;
- command and event hash chains;
- Genesis and periodic Snapshots;
- recovery from the latest Snapshot;
- verification replay from the earliest Snapshot;
- canonical equality between replayed and retained Events.

`GET /api/replay` returns the final `ReplayResult`, not state at an arbitrary revision or a sequence of player-facing frames.

**Decision — M5 core**

M5 extends the existing replay kernel with point-in-time reconstruction. It does not create a second replay database or copy authoritative World states into product tables.

### 3.2 `seed` is metadata-only

**Observed**

Scenario v1 and v2 construct one fixed Genesis and then overwrite only `state.seed` when a custom seed is supplied.

A direct test created two Scenario-v2 Runs using `seed-a` and `seed-b`. After replacing the seed label with one common value, both Genesis digests were identical.

```text
seedOnlyChangesLabel = true
```

No scenario or World reducer consumes a random-number generator. `scripts/measure.ts` has a separate PRNG, but it randomizes policy action selection rather than World Genesis.

**Decision — M5.0**

M5 must not claim seed-dependent environments and must not add randomness merely to satisfy the word “seed”. It introduces deterministic **Scenario Cases** and immutable Genesis specifications. The existing `seed` field remains compatibility metadata until a future scenario contains real seeded randomness.

Terminology after M5:

```text
caseId / genesisSpecDigest  — deterministic environment input
policySeed                  — deterministic harness sampling/order
Provider nondeterminism     — replicated experimental variation
seed                        — compatibility metadata unless an RNG consumes it
```

### 3.3 build identity is stale

**Observed**

`CURRENT_BUILD` is:

```text
ordivon-game@0.2.0+m2
```

A new M4 Run still records that string in `createdWithBuild`.

**Decision — M5.0**

Replace milestone text with a reproducible build/input identity. A release must bind to package version, evaluated-input digest, scenario/ruleset versions, and—when available—a reachable Git commit/tree. One mutable hard-coded milestone string is insufficient.

### 3.4 snapshot/replay performance is already adequate

**Observed**

M1–M4 receipts and clean-main gates repeatedly verify recovery and replay. Current missions contain at most 22 World revisions.

**Decision — freeze**

M5 may add nearest-Snapshot point-in-time replay, but it must not introduce a snapshot service, cache daemon, broker, or new persistence engine. Performance work requires measured pressure beyond current bounded missions.

## 4. M1.5 audit — measurement

### 4.1 existing random measurement is a policy experiment, not scenario variation

**Observed**

`scripts/measure.ts` runs 1,000 trajectories using a local deterministic PRNG to select from available M1 actions. It records terminal reasons, scores, and perturbations of the recovery policy.

The `seed` in that script controls action sampling only.

**Decision — preserve and rename conceptually**

M5 experiment schemas distinguish policy/harness seed from Scenario Case. The existing M1.5 evidence remains valid and does not need migration before M5 implementation.

### 4.2 measurements lack a general experiment manifest

**Observed**

M1.5 stores one bespoke JSON report with fixed factors embedded in code. M3 and M4 use other bespoke evaluation schemas.

**Decision — M5 core**

Introduce a small common experiment vocabulary:

```text
ExperimentSpec
ExperimentCell
ExperimentRunResult
Metric
ArtifactReference
```

This is a local TypeScript/JSON contract, not MLflow or another service.

## 5. M2 and M2.1 audit — persistent Agent Host

### 5.1 Host Journal timestamps are not integrity-bound

**Observed**

`HostStore.recordDigest()` includes sequence, identity, type, payload, and previous digest, but excludes `created_at`.

A direct audit changed a retained Host Journal timestamp to 1900. `verifyJournal()` still succeeded.

**Decision — M5.0 contract clarification**

For M5 diagnosis:

- Host sequence, World revision, Task revision, and typed identity are authoritative order;
- `createdAt` is display/operational metadata only;
- causal order must never be inferred from wall-clock timestamps;
- latency measurements must come from experiment telemetry, not Journal timestamps.

M5 does not rewrite historical Journal digests or claim cryptographic wall-clock provenance. A timestamp-binding migration belongs to Ordivon Host evolution if a future requirement justifies it.

### 5.2 old M2 projections are not full Journal rebuilds

**Observed**

The generic M2 Host verifies its append-only Journal chain, but current Goal/Task/Attempt projections are mutable tables rather than a reducer rebuilt from every Journal Event.

M3 Team Goal, Task, and configuration projections improve this by checking each current projection against its event head. They still do not form a universal Host state reducer.

**Decision — Deferred**

M5 diagnosis reads retained evidence and verifies known projection heads. It does not convert the complete M2/M3 Host into a new event-sourced architecture. That would be a Host project, not a first-playable requirement.

### 5.3 M2.1 strategic ranking remains single-Agent advisory history

**Observed**

M2.1 uses global authoritative state to rank single-Engineer Operations. M3 actor-local Context and Team proposal selection do not reuse that global ranking as a hidden coordinator.

**Decision — freeze**

Do not import M2.1 strategic score into M5 diagnosis, experiment ranking, or “best configuration” claims. M5 comparisons use verified outcomes and explicit metrics.

### 5.4 legacy product APIs remain callable

**Observed**

`/api/suggestion`, `/api/agent/*`, `/api/team/*`, and `/api/actions` remain available for debug compatibility. The main M4 product does not consume them.

**Decision — Deferred**

M5 catalog/documentation marks them debug/compatibility APIs. Do not delete them during the first-playable release unless a concrete collision occurs.

## 6. M3 audit — multi-Agent Team

### 6.1 Provider assignment is Task-scoped

**Observed**

`TeamTaskProjection.providerOrder` stores live Provider routing. This is coherent while each Actor owns one long-lived Task.

**Inferred**

A future Actor with multiple concurrent Tasks would make Actor deployment and Task routing ambiguous.

**Decision — M5 core without migration**

M5 adds an immutable `RunDeploymentManifest` that records initial Actor/Provider mapping. Live replacement remains a Task event for compatibility. M5 does not migrate Provider routing to a new generalized Actor service.

### 6.2 initial deployment is not one immutable comparison input

**Observed**

Current records separately retain scenario/ruleset metadata, Task Provider order, authority configuration, and World Genesis. They do not expose one immutable object containing all initial conditions.

**Decision — M5 core**

A comparison-quality Run begins with one immutable deployment manifest containing:

- Scenario Case and Genesis digest;
- loadout profile;
- Actor identities and initial Provider order;
- authority policy;
- initial Messages or communication option, when part of an experiment;
- build/evaluated-input identity.

Subsequent Provider replacement, player intervention, and Messages remain ordinary retained events.

### 6.3 resource handoff remains absent

**Observed**

All-Hermes and Codex-to-Hermes runs expose a spare-parts ownership failure. M4 makes the mismatch visible before commit but does not add item transfer or automatic negotiation.

**Decision — Deferred**

M5 diagnoses and compares this failure. It does not add a new World Command or hidden resource manager. A transfer mechanic requires separate gameplay design and must be justified by evidence after first playable.

### 6.4 multiple viable strategies already exist

**Observed**

On the same current Genesis:

| Strategy | Result | Turn | Score | Battery |
|---|---:|---:|---:|---:|
| Security containment | victory | 18 | 2264 | 8 |
| Engineer sealing | victory | 22 | 2255 | 0 |

**Decision — reuse**

M5 does not invent strategy diversity merely for acceptance. Replay and comparison must expose the existing materially different paths.

### 6.5 deterministic failure cases already exist

**Observed**

The same task offer delivered locally produces victory; delayed station-radio delivery produces `power_exhausted`. Live all-Hermes and replacement runs produce `mission_timeout` with retained resource-ownership evidence.

**Decision — reuse**

The deterministic communication failure is the required release diagnosis fixture. Live failures may be replayed descriptively, but the core release does not depend on paid/nondeterministic Provider calls.

## 7. M4 audit — Mission Control product

### 7.1 timeline pagination is not real pagination

**Observed**

`createMissionControlView()` retains the latest 12 Rounds. `/api/mission-control/timeline?before=&limit=` filters that already truncated array.

It cannot return an older Round once it falls outside the last 12.

**Decision — M5.0**

M5 supersedes this endpoint with direct revision-based replay queries over retained Rounds/Events. The main bounded Mission Control view continues to contain only recent history.

### 7.2 terminal 22-Tick payload was not frozen in M4 evidence

**Observed**

The M4 evaluation froze the 18-Tick containment path. The original acceptance text referred to a 22-Round terminal response.

A direct audit ran the Engineer-sealing Fixture path:

```text
turn: 22
status: victory
encoded MissionControlView: 17,009 bytes
timeline items: 12
```

**Decision — M5.0 evidence debt resolved by test**

Freeze this direct 22-Tick assertion in M5. It is comfortably below the 64 KiB contract and requires no architecture change.

### 7.3 M4 evidence provenance is fragile

**Observed**

`M4-EVALUATION.json.sourceRevision` points to:

```text
123e89bfd33f4fcd99149c95d08d6bb86dcaca2f
```

That revision is not an ancestor of final `main` after squash merge.

**Decision — M5.0**

M5 release evidence binds primarily to a canonical evaluated-input manifest and digest. Git commit/tree metadata is supplementary and must be reachable when claimed.

### 7.4 no real browser end-to-end evidence

**Observed**

M4 proves the complete Mission Control API loop, real view rendering, static ES-module loading, and product/debug separation. It does not prove a browser can click from deployment through terminal and replay.

**Decision — M5 core**

Add one Chromium Playwright release journey. Playwright is a dev-only dependency. CI uses one worker, one browser, and retains a trace only on failure. No frontend framework is introduced.

### 7.5 Web duplicates catalog constants

**Observed**

`web/store.js` duplicates Actor identities, Provider options, and role Objective lists already represented by backend contracts.

**Decision — M5.0**

Expose a small read-only product catalog and render deployment controls from it. Do not add schema generation or a build pipeline.

### 7.6 Mission Control projection is a hotspot

**Observed**

`src/mission-control/projection.ts` currently owns resource bands, labels, station projection, Actor evidence, Objectives, interventions, timeline, and top-level view assembly.

**Decision — controlled growth**

M5 replay and experiments live in new modules. Shared fact-label helpers may move only when touched. Do not perform a broad aesthetic refactor before replay behavior is proven.

### 7.7 debug/product duplication is deliberate

**Observed**

The old engineering page is retained under `/debug.html` while the root is the player product.

**Decision — freeze**

M5 may add links to replay evidence but does not merge the two surfaces or remove debug observability.

## 8. Cross-cutting release debt

### 8.1 no source-playable release artifact

**Observed**

CI checks source but does not create a deterministic bundle, release manifest, or artifact attestation.

**Decision — M5 core**

M5 produces a source-playable archive and `M5-RELEASE.json` with digests, environment, commands, evaluated inputs, evidence artifacts, and terminal outputs. Local verification is authoritative. GitHub artifact attestation is an additional CI provenance layer, not a runtime dependency.

### 8.2 no common comparison contract

**Observed**

M1.5, M2, M3, and M4 use different evaluation JSON structures.

**Decision — M5 core, additive**

M5 defines one comparison-oriented result schema for new experiments. Historical evidence is referenced, not migrated wholesale.

### 8.3 no browser artifact on failure

**Observed**

Current CI cannot retain a DOM/action trace for a failed first-playable journey.

**Decision — M5 core**

The one release E2E retains a Playwright trace on failure. Screenshots/videos are not retained for every passing run.

## 9. Ownership matrix

| Debt | Evidence | Ownership | M5 action |
|---|---|---|---|
| seed changes label only | Observed | Game Scenario | replace release semantics with Scenario Cases |
| stale `CURRENT_BUILD` | Observed | Game release | evaluated-input/build identity |
| final-only World replay | Observed | Game storage | point-in-time state reconstruction |
| false timeline pagination | Observed | Mission Control | revision-based replay paging |
| Host timestamp not hashed | Observed | Host contract | declare metadata-only; sequence is authoritative |
| generic Host projection not fully rebuildable | Observed | Ordivon Host | defer architecture migration |
| Provider mapping on Task | Observed | Host Team | immutable initial deployment manifest; no migration |
| no item transfer | Observed | Game mechanics | defer |
| M4 provenance points to non-ancestor | Observed | evidence/release | evaluated-input manifest digest |
| no browser E2E | Observed | product release | one Chromium release journey |
| Web catalog duplication | Observed | Mission Control | read-only catalog |
| projection hotspot | Observed | Mission Control | isolate new replay modules; no broad rewrite |
| no exact release bundle | Observed | release/CI | deterministic archive + manifest + optional attestation |
| no common experiment result | Observed | evaluation | small TypeScript/JSON experiment schema |

## 10. Explicitly rejected M5 work

M5 must not add:

- random World variation solely to make `seed` meaningful;
- a second replay or analytics database;
- OpenTelemetry, MLflow, Temporal, or another platform dependency;
- a model-generated causal explanation treated as fact;
- a hidden manager Agent;
- automatic replacement of valid Provider choices;
- a general item-transfer or negotiation system;
- arbitrary numerical loadout sliders;
- a full factorial experiment with uncontrolled factor growth;
- Runtime Job tables inside the Game database;
- React, Vue, a chart framework, or a frontend build pipeline;
- multiplayer, accounts, modding, 3D, or a general game platform;
- a complete Host event-sourcing rewrite.

## 11. M5 entry verdict

M1–M4 are sufficiently sound to begin M5. No World or Team redesign is required.

M5 should begin with a narrow hardening slice:

```text
truthful Scenario Case semantics
+ immutable deployment/build identity
+ real revision paging
+ stable evidence provenance
+ explicit timestamp authority
```

After that, M5 may build replay, diagnosis, comparison, experiments, browser evidence, and release packaging entirely as derived or orchestration layers above the frozen M1–M4 contracts.
