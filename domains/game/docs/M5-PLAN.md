# M5 plan — implementation graph for the first playable release

Status: design only
Design: [`M5-DESIGN.md`](M5-DESIGN.md)
Debt audit: [`M1-M4-DEBT-AUDIT.md`](M1-M4-DEBT-AUDIT.md)
Tracking: Issue #7
Base revision: `2427aad4d35e76ffb3ab479f60be8c2239f5c9c8`

## 1. Delivery graph

M5 is implemented in seven bounded slices:

```text
PR1 M5.0 identity, catalog, and paging hardening
 ├─→ PR2 verified point-in-time replay and Evidence Graph
 │    └─→ PR3 key turns, curves, and diagnosis
 └─→ PR4 Scenario Cases, deployment manifests, and comparison
       └──────────────┬──────────────────────────────┘
                      ▼
             PR5 experiments and Runtime cell contract
                      ▼
             PR6 Replay/Compare Web and Chromium E2E
                      ▼
             PR7 release evidence and closeout
```

PR2 and PR4 may proceed in parallel after PR1 if the actual file boundaries remain independent. PR3 requires replay frames. PR5 requires immutable deployment inputs and comparison metrics. PR6 requires replay/diagnosis/compare APIs. PR7 requires every prior exit gate.

The graph is a review boundary, not an instruction to preserve an inefficient order. Any changed path must retain the same contracts and be explained in the PR receipt.

## 2. PR1 — M5.0 identity, catalog, and paging hardening

### Goal

Remove the small M1–M4 defects that would make later replay or release claims misleading.

### Likely code areas

```text
src/run.ts
src/registry.ts
src/scenario.ts
src/server.ts
src/mission-control/model.ts
src/mission-control/projection.ts
src/mission-control/service.ts
src/experiments/catalog.ts          new
src/release/inputs.ts               new
web/store.js
web/render-shell.js
test/m5-hardening.test.ts           new
```

### Work

1. define `ScenarioCaseDefinition` and typed Genesis specification;
2. register measured baseline, power-constrained, and oxygen-constrained candidate Cases;
3. stop presenting arbitrary seed labels as environment variation;
4. preserve existing seed field for compatibility and explicitly mark its semantics;
5. replace stale `CURRENT_BUILD` milestone identity;
6. implement canonical evaluated-input file selection and digest generation;
7. add product catalog for Actors, roles, Providers, authority modes, Objectives, Cases, and loadout placeholders;
8. make M4 deployment render from catalog instead of duplicated constants;
9. implement direct revision-based timeline paging over retained Rounds/Events;
10. keep the latest-12 Mission Control view bounded;
11. add explicit timestamp-authority documentation and conformance tests;
12. freeze the audited Engineer-seal 22-Tick/17,009-byte condition as a <=64 KiB test;
13. mark legacy debug APIs in the catalog without deleting them.

### Tests

- different Scenario Case specs produce different Genesis digests;
- changing only compatibility seed does not claim a different Case;
- baseline Case reproduces the M3/M4 Genesis digest;
- power-constrained and oxygen-constrained measured paths reproduce their expected outcomes;
- Run build identity contains package/input identity and no `+m2` drift;
- evaluated-input manifest is canonical under file enumeration order;
- changing one included source file changes the input digest;
- changing generated docs or local databases does not change the input digest;
- timeline paging returns all 22 revisions over multiple pages without gap/duplicate;
- page reads write no semantic record;
- changing a Host Journal timestamp cannot change replay/diagnosis order;
- product catalog and backend Provider/Objective contracts agree;
- Tick-22 Mission Control response <=64 KiB.

### Exit gate

- no replay UI;
- no new runtime dependency;
- M1–M4 evidence remains green;
- exact Case values either freeze with evidence or remain hidden from product until validated.

## 3. PR2 — verified point-in-time replay and Evidence Graph

### Goal

Reconstruct any retained World revision and join all evidence needed for later explanation.

### Likely code areas

```text
src/storage.ts
src/replay/model.ts       new
src/replay/store.ts       new
src/replay/evidence.ts    new
src/replay/frames.ts      new
src/server.ts
test/replay-store.test.ts new
test/replay-graph.test.ts new
```

### Work

1. add nearest-Snapshot lookup at or before one target revision;
2. implement `stateAtRevision(runId, revision)` with full digest/Event verification;
3. expose exact Genesis through terminal revision;
4. define `RunEvidenceGraph` nodes and edges;
5. join World Tick/Intent/Fact identities to Team Round, Proposal, TickPlan, Effect, Dispatch, and Observation;
6. join Authority, player control, Message, Context, and Provider replacement evidence;
7. construct deterministic graph digest;
8. implement `ReplayFrame` for each World revision;
9. implement true pageable replay timeline;
10. expose summary/frame/timeline APIs;
11. retain old `/api/replay` as debug compatibility;
12. fail closed when a required retained identity is corrupt or missing.

### Tests

- every revision 0–18 for containment reconstructs exactly;
- every revision 0–22 for sealing reconstructs exactly;
- terminal point-in-time digest equals `verifyReplay()`;
- reconstruction from different eligible Snapshots converges;
- frame before/after digests equal retained Event digests;
- selected Intents and verified Facts equal retained Tick Event receipts;
- evidence graph construction is deterministic under query order;
- every edge references an existing node;
- no wall-clock timestamp affects graph order or digest;
- repeated graph/frame reads append zero records;
- command/event corruption fails closed;
- invalid/out-of-range revision fails typed validation;
- page cursor has no gaps or duplicates.

### Exit gate

A Node/fetch client can scrub a complete Fixture Run without Web changes and inspect every evidence reference.

## 4. PR3 — key turns, curves, and bounded diagnosis

### Goal

Turn verified replay into a comprehensible post-Run explanation without inventing model intent.

### Likely code areas

```text
src/replay/curves.ts       new
src/replay/key-turns.ts    new
src/replay/diagnosis.ts    new
src/replay/counterfactual.ts new
src/server.ts
test/replay-curves.test.ts
test/replay-diagnosis.test.ts
```

### Work

1. derive battery, oxygen, heat, crew/Actor health, system, item, and Objective series;
2. attach warning/victory/terminal thresholds;
3. extract deterministic key turns;
4. define direct terminal explainers for every mission reason;
5. define verified contributor rules for resource ownership, communication delay, waiting, redundant work, authority, and Provider failure;
6. assign evidence classes to every diagnosis step;
7. implement bounded one-step counterfactual sensitivity over legal admitted alternatives;
8. optionally support named deterministic continuation branches as separate Runs;
9. expose diagnosis and replay summary APIs;
10. ensure every non-context diagnosis step has retained evidence references.

### Required fixture diagnoses

#### Communication failure

```text
radio task-offer pending
→ Security lacks timely containment assignment
→ breach remains active longer
→ power/oxygen pressure accumulates
→ power_exhausted
```

The implementation must prove each edge from retained evidence and may revise the wording if the actual trace supports a more precise chain.

#### Hermes coordination failure

Describe, without overclaiming unique causality:

```text
spare parts move to an Actor without repair capability
+ Engineer repair Objectives remain unresolved
+ no successful handoff exists
+ mission reaches timeout
```

This may consume retained M3 evidence as a descriptive fixture; it does not require paid Provider replay.

### Tests

- curves reproduce exact terminal M3/M4 values;
- each curve has one point per World revision and no synthetic interpolation;
- direct failure reason maps to exact threshold/terminal transition;
- victory diagnosis references every required victory predicate and distress Fact;
- key-turn ranking is deterministic and <=12;
- resource mismatch and delayed communication are contributors in known traces;
- contributors are not labelled unique causes;
- Context-only notes cannot appear as verified direct steps;
- one-step counterfactual uses the exact before-state and admitted legal alternatives;
- simulated continuation names its deterministic policy and receives a new Run identity;
- summary/frame/diagnosis bounds hold.

### Exit gate

The deterministic communication failure exposes a concrete, evidence-linked chain in API form. No model call is used for diagnosis.

## 5. PR4 — Scenario Cases, deployment manifests, loadouts, and comparison

### Goal

Make initial conditions explicit and allow one meaningful configuration improvement.

### Likely code areas

```text
src/experiments/model.ts          new
src/experiments/catalog.ts
src/experiments/deployment.ts     new
src/replay/compare.ts             new
src/team/store.ts
src/mission-control/service.ts
src/server.ts
web/render-shell.js
test/deployment-manifest.test.ts  new
test/run-comparison.test.ts       new
```

### Work

1. finalize three deterministic Scenario Cases from PR1 evidence;
2. define and validate loadout profile conservation;
3. measure candidate specialist-forward placement;
4. expose only profiles with a real verified trade-off;
5. define optional initial coordination profiles using existing typed Message semantics;
6. create immutable `RunDeploymentManifest` as content-addressed Host Artifact plus checked run link;
7. prevent manifest mutation after first Context/World revision;
8. record initial Actor Provider order and authority mode;
9. retain later Provider changes as existing Task Events;
10. render Cases/loadouts/coordination from product catalog;
11. define compatibility rules for two Runs;
12. implement `RunComparisonView` and compare API;
13. show input difference before outcome difference;
14. label cross-Case comparison descriptive-only;
15. never infer missing Provider cost/tokens.

### Configuration-improvement gate

At least one measured configuration change must satisfy one of:

- deterministic failure → victory;
- same victory with at least two fewer Ticks;
- same victory with materially better terminal battery/oxygen/health and a visible trade-off elsewhere.

The preferred candidate is a conservation-preserving specialist-forward loadout in a constrained Case. If measurement shows it trivializes the mission or has no effect, do not expose it; test another bounded profile.

### Tests

- deployment manifest digest is stable and immutable;
- fresh process restores exact manifest;
- Case/loadout/Providers/authority/coordination are all bound;
- item totals are conserved for every profile;
- invalid actor/room/item placement fails closed;
- manifest cannot mutate after cognition or World execution begins;
- baseline containment and sealing remain viable;
- constrained Cases reproduce expected strategy sensitivity;
- required configuration improvement is verified;
- same-case comparisons are configuration-comparable;
- cross-case comparison is descriptive-only;
- ruleset mismatch is incompatible;
- comparison metric deltas reproduce terminal states and curves.

### Exit gate

Two retained Runs can be compared through one pure API, and one meaningful configuration improvement is frozen in deterministic evidence.

## 6. PR5 — bounded experiments and Ordivon Runtime cell contract

### Goal

Run and aggregate reproducible configuration matrices without turning Game into a workflow engine.

### Likely code areas

```text
src/experiments/model.ts
src/experiments/runner.ts       new
src/experiments/aggregate.ts    new
scripts/experiment-plan.ts      new
scripts/experiment-cell.ts      new
scripts/experiment-aggregate.ts new
test/experiment-contract.test.ts new
examples/experiments/m5-release.json new
```

### Work

1. define Experiment Spec, factors, cells, result, metrics, and Artifact references;
2. create canonical cell input digest;
3. enforce maximum 16 deterministic release cells;
4. implement local sequential reference executor;
5. implement one-cell CLI independent from local orchestration;
6. implement aggregate verification for expected cells/results/digests;
7. distinguish Game terminal failure from executor failure;
8. export Runtime-ready cell command/working-directory/environment contract;
9. run each cell as one Ordivon Runtime Job during evaluation;
10. retain result JSON/stdout/stderr as Runtime Artifacts;
11. aggregate Runtime outputs through the same Game reducer;
12. capture Runtime Job/Attempt IDs only as external evidence references;
13. add explicit budget fields for any live Provider study;
14. do not run paid live matrix by default.

### Release experiment design

Freeze an objective before execution, for example:

> Measure how breach strategy and constrained Case/loadout affect verified success, turns, and resource margin under deterministic Fixture cognition.

Use no more than four meaningful two-level factors or an explicitly selected <=16-cell subset. Avoid an accidental 32/64-cell expansion.

### Tests

- plan generation is deterministic;
- cells are unique and <=16;
- each result binds exact plan/cell/input digest;
- local repeated execution produces identical deterministic results;
- aggregation rejects missing/duplicate/foreign cells;
- executor failure has no fake World status;
- local and Runtime-executed semantic result JSON are equal after removing executor metadata;
- randomized execution order does not change deterministic cell outcomes;
- live Provider fields require explicit replications and budget;
- unreported cost/token metrics stay null/unknown.

### Exit gate

One release matrix runs locally and through Ordivon Runtime with the same semantic aggregate. Runtime remains an external executor.

## 7. PR6 — Replay/Compare Web and Chromium E2E

### Goal

Make the learn–compare–reconfigure loop usable in the actual browser.

### Likely files

```text
web/app.js
web/api.js
web/render-shell.js
web/render-replay.js       new
web/render-curves.js       new
web/render-diagnosis.js    new
web/render-compare.js      new
web/styles.css
playwright.config.ts       new
e2e/first-playable.spec.ts new
.github/workflows/ci.yml
package.json
```

### Work

1. add terminal `Review mission` and `Compare` actions;
2. add Replay route/state without a frontend framework;
3. render revision scrubber and key-turn navigation;
4. fetch one Replay Frame on selection;
5. render station state at selected revision;
6. render plain SVG resource/system curves;
7. render Actor Proposals, selected Intents, Facts, Objective transitions, authority, player, Message, and Provider evidence;
8. render diagnosis steps with evidence-class labels;
9. add compare selection and input/outcome/key-turn differences;
10. update deployment from backend catalog;
11. add one Playwright Chromium journey;
12. configure `webServer`, one CI worker, and trace retention on failure;
13. install only Chromium headless shell/dependencies in browser CI;
14. retain the HTML/trace report only on failure or release evidence need.

### E2E journey

The release browser test must:

```text
load deployment
→ select baseline configuration
→ start Run
→ prepare Proposals
→ commit verified Ticks to terminal
→ verify outcome
→ open Replay
→ scrub to earlier revision
→ verify map/resource change
→ compare with deterministic alternative
→ verify input and outcome difference
→ return to reconfiguration
```

The test may use Fixture cognition but must use real HTTP, DOM events, persisted SQLite state, and production Web modules.

### Tests/gates

- existing unit/static Web checks remain;
- Chromium E2E passes from clean checkout;
- no raw debug controls appear in product Replay/Compare;
- frame loading is bounded and does not preload full Contexts;
- chart rendering contains every expected revision;
- key-turn navigation selects the exact frame;
- diagnosis evidence links open debug detail without exposing raw records by default;
- browser failure retains a trace;
- Playwright is dev-only;
- runtime dependency count remains zero.

### Exit gate

The first playable loop is proven in a real browser, not only API and string-render tests.

## 8. PR7 — release evidence and Program closeout

### Goal

Produce one exact, clean-checkout-verifiable first-playable release and close Issues #7 and #1.

### Likely deliverables

```text
docs/M5-EVALUATION.json
docs/M5-RELEASE.json
docs/M5-RECEIPT.md
test/m5-evidence.test.ts
scripts/m5-evaluation.ts
scripts/release-inputs.ts
scripts/release-build.ts
scripts/release-verify.ts
README.md
docs/ROADMAP.md
docs/DECISIONS.md
.github/workflows/release.yml
package.json version update
```

### Work

1. freeze final evaluated-input manifest/digest;
2. run deterministic replay/diagnosis/comparison matrix;
3. run local and Runtime cell paths;
4. freeze browser E2E result and failure-trace policy;
5. generate M5 evaluation and release manifest;
6. add evidence test binding every load-bearing claim;
7. build source-playable archive from exact release source;
8. verify archive and manifest locally;
9. run clean checkout:

```text
git clean -fdx
pnpm install --frozen-lockfile
pnpm check
pnpm e2e
pnpm receipt
pnpm measure
pnpm experiment:release
pnpm release:build
pnpm release:verify
```

10. create release workflow for tag/archive upload;
11. optionally generate GitHub artifact attestation and record verification command;
12. update status and close #7/#1 only after release evidence succeeds;
13. tag the exact first-playable release after merge.

### Required release evidence

- exact Scenario/Ruleset/Case/loadout/deployment manifests;
- every revision replay equality;
- known success and failure diagnosis;
- meaningful configuration improvement;
- two viable baseline strategies;
- deterministic experiment aggregate;
- local/Runtime semantic equality;
- browser first-playable journey;
- M1–M4 compatibility evidence;
- input/archive/report digests;
- clean worktree and reachable release source identity.

### Provenance rule

Do not repeat M4's squash-pre-merge source binding. Evidence must remain verifiable from the final tagged source through evaluated-input and release artifact digests.

### Exit gate

Issue #7 closes only when the exact release artifact and manifest can be verified from a clean checkout. Program #1 closes only after the tag/release assets and repository receipt agree.

## 9. Expected cost

### Necessary cost

- point-in-time replay and evidence joins;
- deterministic diagnosis rules;
- configuration/deployment provenance;
- experiment schemas and CLI;
- one browser testing dependency;
- replay/compare product modules;
- release scripts and CI.

### Cost deliberately avoided

- new database/service for analytics;
- generic tracing SDK;
- Python experiment platform;
- model-based diagnosis;
- arbitrary scenario editor;
- large live-model matrix;
- frontend framework/chart library;
- Runtime integration inside Game internals.

## 10. Main implementation risks

1. overclaiming causal truth from one trace;
2. allowing Scenario Cases to become arbitrary World patches;
3. exposing a loadout that is cosmetic or trivializes the mission;
4. coupling replay to M4's truncated timeline;
5. introducing another persistent evidence authority;
6. using timestamps for causal ordering;
7. comparing Runs with incompatible Cases/Rulesets as if controlled;
8. experiment factor explosion;
9. confusing Runtime executor failure with Game outcome;
10. release manifest circularity or binding to an unreachable commit;
11. letting Playwright grow into a large cross-browser test suite;
12. adding replay logic to the Mission Control projection hotspot.

## 11. Stop conditions

M5 does not continue adding features after all of the following are true:

```text
any revision is verifiable
one failure is explainable
one alternative is comparable
one configuration improves a verified outcome
one bounded experiment is reproducible locally and through Runtime
one browser journey proves play → replay → compare
one source release is independently verifiable
```

At that point Station Zero first playable is complete. Further game mechanics, scenarios, model strategy research, and platform extraction require new evidence and new Issues.
