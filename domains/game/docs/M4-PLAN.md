# M4 plan — playable mission-control implementation sequence

Status: design only
Design: [`M4-DESIGN.md`](M4-DESIGN.md)
Tracking: Issue #6
Base revision: `b510818fdc682c1ee55885b0c1c06c93ab61cc8a`

## 1. Delivery strategy

M4 is implemented in six reviewable PRs. Each PR leaves the repository green and does not depend on an unfinished Web rewrite.

```text
PR1 control truth and persistent configuration
 → PR2 mission-control read model
 → PR3 player-visible advance and command API
 → PR4 playable Web shell
 → PR5 decision center and semantic evidence views
 → PR6 acceptance, evidence, and closeout
```

The order is intentional. UI implementation starts only after pause, resume, cancel, deny, Provider assignment, and authority configuration are semantically real.

## 2. PR1 — control truth and persistent configuration

### Goal

Make every advertised player control durable, auditable, and enforced by `TeamHost`.

### Code changes

```text
src/team/model.ts
src/team/store.ts
src/team/engine.ts
src/server.ts
src/team/configuration.ts        new
src/team/configuration-store.ts  new
```

### Work

1. add `TeamTaskControl` with `active | paused | cancelled`;
2. normalize legacy Tasks without control to active;
3. filter TeamHost eligibility by Task control and terminal Task state;
4. ensure Round verification does not reactivate paused/cancelled Actors;
5. add `resume`;
6. make cancel irreversible within a Run;
7. filter legal subsets and pending authority to `status == proposed`;
8. prove denied Proposals never execute;
9. add checked `TeamRunConfiguration` for authority mode;
10. make per-Actor `providerOrder` on Task authoritative;
11. add explicit `set-provider` and `set-authority-policy` commands;
12. construct Provider maps from persisted Task configuration;
13. preserve legacy request parameters only on old Team endpoints and mark them debug compatibility inputs.

### Tests

- pause survives Context preparation and multiple advance attempts;
- resume re-enables exactly one Actor;
- cancel never re-enters;
- deny removes Proposal from legal subsets;
- one denied Actor does not block other productive Proposals;
- Provider configuration survives fresh process;
- authority mode survives fresh process;
- checked configuration projection fails closed on drift;
- old M3 Task JSON without control defaults to active.

### Exit gate

No Web code changes. All 159 existing tests remain green plus new control conformance tests.

## 3. PR2 — bounded mission-control read model

### Goal

Create one pure player-facing projection without modifying authoritative state.

### Code changes

```text
src/mission-control/model.ts       new
src/mission-control/projection.ts  new
src/mission-control/explain.ts     new
src/mission-control/layout.ts      new
src/mission-control/timeline.ts    new
```

### Work

1. define `MissionControlView` and subordinate DTOs;
2. bind Station Zero v2 room layout outside World state;
3. project World resources, systems, hazards, crew, all three Actors, and inventory ownership;
4. load the latest Actor Context Artifact per Actor;
5. derive Observed / Assessed / Proposed / Executing / Verified stages;
6. project Objective dependencies and role mandates;
7. derive current Round phase;
8. derive authority, wait, provider-failure, pending-message, conflict, redundancy, mission-risk, and resource-mismatch cards;
9. derive deterministic consequence and urgency summaries;
10. derive current and previous verified resource trends;
11. provide latest 12 semantic Round timeline items;
12. hard-bound every list and encoded response size.

### Tests

- 22-Round view <= 64 KiB;
- repeated projection is pure and stable;
- Actor knowledge equals retained Context content, not current omniscient state;
- assessment never appears as verified Fact;
- current selected TickPlan appears as expected/executing, not verified;
- verified Facts appear only after Observation success;
- Security pickup of spare parts while Engineer has repair Objectives emits resource mismatch;
- mixed containment+sealing emits redundant-action information;
- authority cards include reason, consequence, urgency, expiry, and exact commands;
- station layout covers every Scenario v2 room exactly once.

### Exit gate

Projection is callable from tests but not yet exposed as the main Web API.

## 4. PR3 — player-visible advance and command API

### Goal

Expose mission semantics instead of Host persistence stages.

### Code changes

```text
src/mission-control/advance.ts  new
src/mission-control/service.ts  new
src/server.ts
```

### Routes

```text
GET  /api/mission-control/state
POST /api/mission-control/initialize
POST /api/mission-control/advance
POST /api/mission-control/command
GET  /api/mission-control/timeline
```

### Work

1. initialize M3 Run, Tasks, configuration, and Provider map;
2. implement `advance until proposal-review`;
3. implement `advance until tick-verified`;
4. stop at authority, blocked, all-paused, terminal, or bounded internal-step limit;
5. return `MissionControlView`, not raw Team envelope;
6. route approve, deny, redirect, pause, resume, cancel, set-provider, and set-authority-policy through canonical services;
7. make all GET routes strictly read-only;
8. paginate timeline with stable cursor and limit <= 50;
9. retain old `/api/team/*`, `/api/agent/*`, and `/api/actions` routes for debug compatibility;
10. add response-size and no-semantic-write assertions.

### Tests

- one `proposal-review` request stops before World mutation;
- one `tick-verified` request advances at most one World Tick;
- authority request stops before TickPlan;
- page reload retrieves the same pending review;
- input identity and stale revisions fail closed;
- GET state and timeline do not refresh Messages or append Journal events;
- scripted mission-control-only client reaches Fixture victory;
- direct primitive World Command is unnecessary for the player loop.

### Exit gate

A Node/fetch client can play the mission without Web UI.

## 5. PR4 — playable Web shell

### Goal

Replace the engineering page with a coherent deployment and mission screen.

### Files

```text
web/index.html
web/app.js
web/api.js                 new
web/store.js               new
web/render-shell.js        new
web/render-map.js          new
web/render-actors.js       new
web/render-objectives.js   new
web/render-timeline.js     new
web/styles.css
web/debug.html             new
web/debug.js               new or migrated from current app.js
src/server.ts              static module routes only
```

### Work

1. move current M1/M2/manual/raw controls to debug page;
2. add Run list, create, URL selection, resume, and terminal state routing;
3. add deployment configuration for each Actor Provider and Team authority mode;
4. show fixed role risk and equipment without fake edit controls;
5. render fixed station topology with all Actors, crew, systems, hazard, and inventory;
6. render resource bands and verified trends;
7. render Objective dependencies;
8. render three Actor cards and task/control state;
9. add prepare/review and commit-one-Tick control bar;
10. persist selected Run in URL, not only JavaScript memory;
11. define complete CSS tokens and responsive layout;
12. display busy state during synchronous Provider calls.

### Tests

- static main page has no manual World action panel or M2 Agent panel;
- debug page retains legacy controls;
- URL run parsing and serialization are pure and tested;
- render modules produce all three Actors and Objective alternatives;
- main page contains no raw JSON output by default;
- browser JavaScript syntax and existing server static tests remain green.

### Exit gate

A player can create, reload, inspect, prepare, and commit a Fixture mission through the browser.

## 6. PR5 — decision center and semantic evidence

### Goal

Make coordination failures understandable and intervention practical.

### Work

1. intervention inbox sorted by severity and expiry;
2. authority cards with exact approve/deny controls;
3. resource-mismatch and redundant-action cards;
4. Actor detail drawer with Observed / Assessed / Proposed / Executing / Verified sections;
5. pending/delivered/expired Message status;
6. redirect Objective picker limited by role mandate;
7. pause/resume/cancel controls with durable status;
8. Provider replacement control with explicit continuity warning;
9. current Round Proposal review and exact selected batch preview;
10. terminal outcome, score components, final Objective status, and last verified events;
11. semantic recent timeline with no raw Journal payloads.

### Acceptance scenarios

- supervised hazard Proposal explains urgency and consequence before approval;
- player denies one legal Proposal and selected Tick changes;
- player pauses Medic and Engineer/Security continue;
- player resumes Medic and stabilization later completes;
- Security spare-parts mismatch appears before commit;
- player denies or redirects the harmful pickup path;
- Provider failure is displayed as Actor-local wait, not global crash;
- local vs pending radio Message state is legible.

### Exit gate

Issue #6 qualitative acceptance is testable without asking the player to read IDs or logs.

## 7. PR6 — M4 evidence and closeout

### Goal

Freeze M4 as a product-semantic milestone and unblock M5.

### Deliverables

```text
docs/M4-EVALUATION.json
docs/M4-RECEIPT.md
test/m4-evidence.test.ts
README.md update
docs/ROADMAP.md update
docs/DECISIONS.md updates
Issue #6 closeout
Program Issue #1 checkbox update
```

### Required evidence

1. clean-checkout Fixture mission completed through mission-control APIs only;
2. page reload retains Run and pending decision;
3. pause/resume/cancel/deny controls change execution and survive fresh process;
4. player intervention changes an admitted action path;
5. resource mismatch is visible before the harmful Tick;
6. authority card includes deterministic reason, consequence, urgency, and expiry;
7. all five evidence classes appear in one retained mission;
8. complete mission-control state remains <= 64 KiB at terminal state;
9. repeated GET requests append zero semantic events;
10. main page hides raw logs and direct primitive Commands;
11. all M1–M3 receipts remain green;
12. runtime dependency count remains zero.

### Optional usability evidence

A short manual receipt may record:

- first-time player can identify the pending decision;
- player can locate each specialist and scarce item;
- player can explain one failure without opening debug mode.

This is supporting evidence, not a substitute for deterministic tests.

## 8. Work deliberately deferred to M5

Do not pull the following into M4 merely because the UI makes them desirable:

- resource-transfer World Command;
- arbitrary loadout editing;
- multiple scenario seeds;
- replay scrubber;
- resource charts;
- causal key-turn classifier;
- batch comparison;
- Runtime experiment queue;
- release packaging.

If resource visibility and player denial/redirect are insufficient, the need for transfer or negotiation must be demonstrated by M4 evidence before a new World Command is designed.

## 9. Expected cost and risk

### Moderate cost

- player-facing projection and deterministic explanations;
- Web restructuring;
- control semantics and persistent configuration;
- broader HTTP conformance tests.

### Low architectural risk

- no World schema change;
- no new process;
- no runtime dependency;
- no new model role;
- no change to M3 Effect/Dispatch/Observation identity.

### Main implementation risks

1. accidentally leaking omniscient World information into Actor knowledge panels;
2. treating Provider rationale as fact;
3. making GET endpoints write through Message refresh;
4. duplicating Team state in a presentation database;
5. allowing UI controls to bypass Task revision and authority identity;
6. letting the main response grow with mission history;
7. moving M5 replay and loadout work into M4.

## 10. Stop conditions

M4 is complete when the browser is a truthful player interface over M3, not when it is visually polished.

Stop adding features when:

```text
player can configure
player can understand
player can intervene
player can commit one Tick
player can verify the result
player can resume after reload
```

Do not extend M4 into a generalized dashboard framework.
