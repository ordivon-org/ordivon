# M4 design — playable mission-control interface

Status: design only; no M4 runtime or Web implementation is authorized by this document
Tracking: Issue #6
Depends on: completed M3 Issue #5
Next milestone: M5 replay, evaluation, and first playable receipt

## 1. Why M4 is required

M3 completed the trustworthy multi-Agent execution substrate. It did not complete the player product.

The current browser page is an engineering console that exposes three historical control surfaces at once:

```text
M1 manual World Commands
M2 single-Engineer Host
M3 three-specialist Team Host
```

It also exposes raw Command names, revisions, proposal identities, Host journal records, and JSON receipts. A developer who knows the schema can operate it; a player cannot reliably answer the questions that define Station Zero:

- What is currently most urgent?
- What does each specialist know, and what are they merely assuming?
- What is each specialist proposing?
- Which proposal is waiting for me?
- What consequence does approval or denial have?
- Who owns the scarce spare parts?
- Why is one specialist waiting?
- Did an action execute, or was it only proposed?
- Which result is independently verified?
- Can I safely reload the page and continue the same mission?

M4 is therefore not visual polish. It is the product-semantic layer that makes M3 controllable and legible without weakening M3's authority boundaries.

### 1.1 Measured current-state problems

The audit of `main@b510818fdc682c1ee55885b0c1c06c93ab61cc8a` found:

1. `web/app.js` joins raw World, M2 Agent, and M3 Team payloads directly in the browser.
2. `teamRunId` exists only in JavaScript memory and is lost on reload.
3. the station view highlights only Engineer Imani, despite M3 owning three specialists;
4. the main page still exposes direct `/api/actions`, which bypasses the intended mission-director role and Team authority path;
5. current Team cards show actor IDs, Task revisions, and raw command kinds instead of player decisions;
6. the latest receipt is raw JSON rather than a semantic outcome;
7. the UI cannot distinguish observation, unverified assessment, proposal, execution, and verified fact;
8. provider and authority choices are request parameters, not durable Run configuration;
9. the HTTP Team API accepts one transient Provider name for the whole Team even though `TeamHost` already supports per-Actor Provider mappings;
10. a complete 18-Round Team state response is about 270 KiB:

```text
projection       62,606 bytes
rounds           24,507 bytes
proposals        72,517 bytes
timeline        108,572 bytes
total           269,770 bytes
```

The response grows with mission history and is unsuitable as the frequently refreshed product view.

### 1.2 Control semantics are not yet product-safe

A control surface must not advertise controls that the execution engine ignores.

The current `pause` and `cancel` HTTP inputs mutate `TeamTaskProjection.state`, but `TeamHost.step()` considers every living Actor eligible regardless of Task state. An audited pause trace produced:

```text
Medic Task revision 2
state = waiting
wait.reason = Player paused Actor
        ↓ next Context preparation
Medic Task revision 3
state = running
wait = null
```

The pause was overwritten before the next Provider call. Cancel has the same eligibility problem.

Proposal denial also needs a stronger execution contract. A denied Proposal is marked `rejected`, but subset selection currently evaluates Proposal authority without first filtering current Proposal status. M4 must make pause, resume, cancel, and deny semantically effective before presenting them as game controls.

### 1.3 M3 failures define M4's product problem

The all-Hermes and Codex-to-Hermes trajectories were execution-correct but strategically unsuccessful:

- Security collected spare parts Engineer needed;
- Engineer lacked a successful recovery or handoff path;
- life support and communications remained damaged;
- every retained Tick, Effect, Dispatch, Observation, and replay still verified.

This means the next missing capability is not another World reducer, hidden manager model, or larger shared transcript. The missing product capability is player-visible coordination:

```text
resource ownership
+ task dependency
+ waiting cause
+ proposal consequence
+ communication state
+ bounded intervention
```

M4 must make those facts visible early enough for the player to change the admitted action path.

## 2. Product objective

M4 turns Station Zero into a playable mission-control experience in which the player can operate one M3 mission without reading raw infrastructure records.

The intended loop is:

```text
configure Team and authority
→ inspect current mission and Actor knowledge
→ prepare one coordination Round
→ review Proposals and intervention requests
→ approve, deny, redirect, pause, resume, or cancel
→ commit one atomic World Tick
→ inspect verified consequences
→ repeat until a clear terminal outcome
```

The player remains a director, not a unit controller. The main product surface must not expose primitive manual World Commands.

## 3. First principles

### 3.1 The World remains authoritative

M4 adds no new authoritative resource, health, inventory, movement, system, hazard, mission, or scoring state. It reads existing World and Team records and sends typed player commands through existing Host boundaries.

### 3.2 A product read model is not a second authority

M4 introduces a pure, bounded `MissionControlView`. It is recomputed from:

```text
WorldState
+ Team Goal / Profiles / Tasks
+ latest Actor Context Artifacts
+ Messages / Authority records
+ current and recent Team Rounds
+ Proposals / TickPlans / Observations
```

The view is disposable. It owns no independent truth and is never replay input.

### 3.3 Player controls must be durable and auditable

Provider assignment, authority policy, pause, resume, cancel, redirect, approve, and deny must write Host evidence with stable identity and revision semantics. UI-only flags cannot alter execution.

### 3.4 Model language is not verified fact

Provider rationale and confidence may be shown as an Agent assessment, but must never be presented as observed or verified state.

The UI uses five explicit evidence classes:

```text
OBSERVED   — content present in the Actor's admitted Context
ASSESSED   — Provider rationale or confidence; unverified model statement
PROPOSED   — admitted Action Proposal not yet executed
EXECUTING  — selected TickPlan / Effect / Dispatch
VERIFIED   — World Facts and successful per-Intent receipts
```

M4 does not add a general belief store. `ASSESSED` is a presentation classification over already retained Provider output.

### 3.5 No hidden correction

M4 may warn about resource mismatch, redundancy, urgency, or consequence. It may not silently replace a valid Proposal or add a manager model. The player decides whether to intervene.

### 3.6 Progressive disclosure

The main mission view must use human-scale summaries. Raw IDs, digests, Context Artifacts, complete Host journals, and legacy M1/M2 controls move to an explicit developer/debug surface.

### 3.7 Thin product stack

M4 keeps:

```text
Node
TypeScript
SQLite
plain HTML / CSS / ES modules
zero runtime dependencies
```

A frontend framework, bundler, graph library, WebSocket layer, or background workflow system is not justified for one fixed eight-room vertical slice.

## 4. Scope boundary

### 4.1 M4 owns

- durable Team Provider and authority configuration;
- real pause, resume, cancel, redirect, approve, and deny semantics;
- a bounded mission-control read model;
- one player-visible coordination-Round advance API;
- station map with all specialists, crew, systems, hazards, and known inventory;
- Agent cards with Task, knowledge, assessment, Proposal, execution, and verification state;
- Objective dependency presentation;
- resource ownership and deterministic coordination warnings;
- an intervention inbox with consequence and urgency;
- typed Message delivery visibility;
- current-mission semantic timeline;
- clear terminal outcome and score summary;
- Run creation, selection, reload, and resume through the URL;
- a separate developer/debug surface for legacy M1/M2/manual controls.

### 4.2 M4 does not own

M5 retains:

- full mission replay and scrubber;
- key-turn identification;
- resource curves;
- complete causal diagnosis;
- fixed-seed comparison;
- configurable World loadouts;
- batch simulation through Ordivon Runtime;
- release packaging and exact first-playable receipt.

M4 also does not add:

- a resource-transfer World Command;
- free-text shared chat;
- a manager Agent;
- model-generated authority explanations;
- new specialists or rooms;
- multiple scenarios;
- asynchronous server Job infrastructure;
- multiplayer, accounts, or hosted-service concerns.

### 4.3 Corrected interpretation of “loadout, risk, and authority configuration”

Current code has fixed role risk preferences and fixed World inventories. Neither is currently a meaningful player-controlled parameter:

- `riskPreferenceId` is stored but does not yet alter Provider Context or admission;
- mutable equipment loadouts belong to M5's configuration-comparison loop.

M4 therefore:

- allows real per-Actor Provider assignment;
- allows real Team authority-policy configuration;
- displays role risk preference and current loadout;
- does not expose cosmetic controls that have no semantic effect.

## 5. Existing code that M4 reuses

| Current code | M4 use |
|---|---|
| `src/model.ts` | authoritative map, agents, crew, systems, hazards, inventory, Facts, Tick receipts |
| `src/storage.ts` | Run list, current World, recent events, replay-safe retained state |
| `src/team/model.ts` | Goal, Actor Profiles, Tasks, Messages, Authority, Proposals, Rounds, Effects, Dispatches, Observations |
| `src/team/store.ts` | checked projections, Task revisions, Message delivery, Grants, Host Journal |
| `src/team/context.ts` | exact Actor-visible Context and evidence boundary |
| `src/team/engine.ts` | durable coordination stages and one atomic Team Tick |
| `src/team/execution-store.ts` | current/recent Rounds and execution records |
| `src/team/authority.ts` | deterministic risk tags, consequence inputs, and authority reasons |
| `src/team/objectives.ts` | Objective dependencies, priority, satisfaction, and role mandate |
| `src/scoring.ts` | terminal and current score presentation |
| `src/server.ts` | local HTTP service and legacy compatibility routes |
| `web/` | replaced as the product shell; legacy controls retained separately for debugging |

M4 should not move or duplicate these authorities.

## 6. Required control-semantic corrections

### 6.1 Separate player control from execution state

`TeamTaskState` currently mixes execution state with player intent. M4 adds an explicit control record to each Actor Task:

```ts
interface TeamTaskControl {
  mode: "active" | "paused" | "cancelled";
  reason: string | null;
  issuedBy: string;
  issuedAtTick: number;
}
```

`TeamTaskProjection` gains:

```ts
control: TeamTaskControl;
```

Backward compatibility:

- missing `control` on an existing M3 Task normalizes to `active`;
- old M3 evidence and replay remain valid because this is Host projection state, not World state;
- checked projection events continue to bind the complete Task value.

Engine eligibility becomes:

```text
Actor exists
AND health > 0
AND Task control.mode == active
AND Task state is not completed/failed/cancelled
```

Pause persists until an explicit resume. Cancel is irreversible for the current Run. Verification must not overwrite paused or cancelled control state.

### 6.2 Add resume

The player command union becomes:

```text
approve
deny
redirect-objective
pause
resume
cancel
set-provider
set-authority-policy
```

Agent-to-Agent Message creation remains a separate advanced control because it is in-world communication, not a player directive.

### 6.3 Make denial change execution

Before legal-subset enumeration:

- only `status == proposed` Proposals are eligible;
- `authorityPending` ignores rejected Proposals;
- a denied Proposal is never selected;
- other legal Proposals may execute;
- if only `wait` remains after explicit denial, one World Tick may advance and the denied Actor replans at the next revision.

This preserves player agency without adding a second Round at the same World revision.

### 6.4 Persist Provider and authority configuration

Current Provider and policy values are transient request parameters. M4 makes them Run state.

Per-Actor Provider order already belongs naturally on `TeamTaskProjection.providerOrder`. M4 uses it as the authoritative Actor Provider configuration and journals every change through Task revision.

Team-level authority mode receives one checked Host projection:

```ts
interface TeamRunConfiguration {
  schemaVersion: 1;
  runId: string;
  authorityPolicyMode: "autonomous" | "supervised" | "locked";
  revision: number;
  createdAt: string;
  updatedAt: string;
}
```

It is stored in a small `team_run_configurations` table with a Host Journal head. `TeamHost` construction reads current Task Provider orders and the Team configuration instead of trusting request parameters.

Mid-Run Provider replacement becomes an explicit `set-provider` player command and remains compatible with M3's replacement evidence.

## 7. Mission-control read model

M4 adds a new module boundary:

```text
src/mission-control/model.ts
src/mission-control/projection.ts
src/mission-control/explain.ts
src/mission-control/layout.ts
src/mission-control/advance.ts
```

### 7.1 Top-level view

```ts
interface MissionControlView {
  schemaVersion: 1;
  generatedFrom: {
    worldRevision: number;
    worldDigest: string;
    goalRevision: number;
    configurationRevision: number;
  };
  run: MissionRunView;
  mission: MissionStatusView;
  resources: ResourceView[];
  station: StationMapView;
  actors: ActorMissionView[];
  objectives: ObjectiveMissionView[];
  currentRound: CoordinationRoundView | null;
  inbox: InterventionCard[];
  timeline: TimelinePage;
  controls: MissionControlAvailability;
}
```

The main view has a hard encoded-size target:

```text
<= 64 KiB at 22 Rounds
```

Mission history must not cause unbounded growth.

### 7.2 Run and mission

```ts
interface MissionRunView {
  runId: string;
  scenarioId: string;
  scenarioVersion: number;
  rulesetVersion: number;
  turn: number;
  turnLimit: number;
  revision: number;
  status: "setup" | "running" | "victory" | "failure";
}
```

`MissionStatusView` contains:

- human title and verified reason;
- turns remaining;
- Objective progress;
- score and score components at terminal state;
- one current urgency summary generated by deterministic rules.

### 7.3 Resource view

Each resource includes:

```ts
interface ResourceView {
  resourceId: string;
  label: string;
  current: number;
  maximum: number | null;
  unit: "energy" | "percent" | "health" | "count" | "ticks";
  band: "stable" | "warning" | "critical" | "terminal";
  trend: "improving" | "stable" | "worsening" | "unknown";
  causeSummary: string | null;
}
```

Trends are derived only from the current and previous verified World events. They are not predictions.

### 7.4 Station layout

World rooms intentionally contain topology but no presentation coordinates. M4 adds scenario-specific presentation metadata outside World state:

```ts
interface RoomLayout {
  roomId: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
}
```

`src/mission-control/layout.ts` binds layout to `station-zero@2`. Coordinates never enter World digest, replay, or admission.

The map shows:

- all three specialists;
- injured crew;
- systems and integrity/power;
- hazard status;
- room inventory;
- communication availability;
- selected Actor and Objective focus.

### 7.5 Actor view and evidence classes

```ts
interface ActorMissionView {
  actorId: string;
  name: string;
  role: string;
  health: number;
  location: string;
  inventory: InventoryItemView[];
  riskPreference: string;
  providerOrder: string[];
  task: ActorTaskView;
  knowledge: ActorKnowledgeView;
  assessment: AgentAssessmentView | null;
  proposal: ProposalView | null;
  execution: ExecutionView | null;
  verified: VerifiedActionView | null;
}
```

`ActorKnowledgeView` is loaded from the latest retained `CompiledTeamContext` Artifact for that Actor and is bounded to:

- latest local observation;
- at most eight visible Facts;
- at most five delivered Messages;
- omitted-block count and Context freshness.

The player may inspect what each Agent knew when it proposed an Action. The view must not silently replace the Actor's historical Context with current omniscient World state.

`AgentAssessmentView` is derived from `ActionProposal.rationale` and `confidence` and is explicitly labelled unverified.

### 7.6 Objective view

The Objective Graph is rendered as a fixed dependency view:

- critical path and alternatives;
- satisfied / active / blocked / available;
- Actor mandate;
- required capability;
- associated Proposal or wait;
- alternate breach-control routes.

M4 does not add another Task graph. It presents the existing Objective Graph and Actor Tasks together.

### 7.7 Current coordination Round

The current Round view is bounded and player-oriented:

```ts
interface CoordinationRoundView {
  roundId: string;
  worldRevision: number;
  phase: "preparing" | "proposal-review" | "authority" | "committing" | "verified" | "blocked";
  actorEntries: RoundActorEntry[];
  selectedProposalIds: string[];
  rejectedProposalIds: string[];
  blocker: string | null;
}
```

Each Actor entry shows the five evidence stages without exposing raw full objects by default.

### 7.8 Intervention inbox

M4 derives deterministic intervention cards:

```ts
interface InterventionCard {
  cardId: string;
  kind:
    | "authority-request"
    | "resource-mismatch"
    | "proposal-conflict"
    | "redundant-action"
    | "task-wait"
    | "provider-failure"
    | "message-pending"
    | "mission-risk";
  severity: "info" | "warning" | "critical";
  actorIds: string[];
  title: string;
  explanation: string;
  consequence: string;
  urgency: string;
  expiresAtTick: number | null;
  availableCommands: PlayerCommandDescriptor[];
  evidenceRefs: string[];
}
```

Explanations are deterministic templates over typed state. No model call is used to explain authority or consequence.

#### Resource-mismatch rule

The M3 failure must be visible before execution. A pickup Proposal receives a warning when:

- the item is scarce;
- the proposing Actor cannot consume it through any capability;
- another active Actor has a capability and unsatisfied Objective that requires it.

For the observed M3 failure:

```text
Security proposes pickup spare-parts
Security lacks repair_system
Engineer has unsatisfied repair Objectives
→ resource-mismatch warning before Tick commit
```

The Host still admits the valid Proposal unless the player denies, redirects, or pauses.

#### Consequence preview

For a Proposal, M4 shows only deterministic claims:

- target and operation;
- items or energy consumed;
- Objective relation;
- authority risk tags;
- whether the action is irreversible;
- current mission urgency;
- whether another Proposal conflicts.

For an exact selected TickPlan, the pure Ruleset-v3 reducer may be used as a non-persistent preview. The UI labels this `EXPECTED IF COMMITTED`, never `VERIFIED`.

## 8. Player-visible execution frontier

`TeamHost.step()` exposes internal persistence stages. `TeamHost.run()` may execute an entire mission. Neither is the correct player abstraction.

M4 adds `MissionControlAdvanceService`, which loops existing `TeamHost.step()` calls until a player-visible boundary.

### 8.1 API

```text
GET  /api/mission-control/state?runId=...
POST /api/mission-control/initialize
POST /api/mission-control/advance
POST /api/mission-control/command
GET  /api/mission-control/timeline?runId=...&before=...&limit=...
```

`advance` accepts:

```ts
interface AdvanceMissionInput {
  until: "proposal-review" | "tick-verified";
  maximumInternalSteps?: number; // bounded, default 12
}
```

### 8.2 `proposal-review`

The service continues through:

```text
Round creation
Context preparation
Provider calls
Proposal admission
```

and stops before TickPlan selection.

The player can inspect or modify Proposals before World mutation.

### 8.3 `tick-verified`

The service continues from the current Round through:

```text
legal subset
TickPlan
Effect
Dispatch
World Tick
Observation
Verification
Task advancement
```

and stops after exactly one verified World Tick, or earlier at:

- authority request;
- all active Actors paused/cancelled;
- blocked Round;
- Provider failure requiring intervention;
- terminal mission.

The Web client may implement autoplay as repeated `tick-verified` requests. M4 does not add a server-side background Job system.

### 8.4 Read-only GET contract

All mission-control GET endpoints must:

- avoid Message refresh writes;
- avoid Task transitions;
- avoid implicit initialization;
- avoid Provider construction when not required;
- produce the same Host Journal count on repeated reads.

## 9. Web information architecture

The main product moves from one long engineering page to four product states.

### 9.1 Deployment

- list and resume compatible Runs;
- create one Scenario v2 / Ruleset v3 Run;
- assign Provider order independently to Engineer, Medic, and Security;
- select Team authority mode;
- display fixed role risk preference and starting equipment;
- start mission.

Provider configuration is persisted. Mutable World loadouts remain M5.

### 9.2 Mission

Primary layout:

```text
┌ mission status / critical resources / turn ┐
├ station map ─────────────┬ intervention inbox ┤
├ Objective dependencies ─┼ Actor detail drawer ┤
├ coordination Round review / commit controls ┤
└ semantic recent timeline ────────────────────┘
```

The map and inbox remain visible during decisions.

### 9.3 Actor detail

Tabs or labelled sections:

```text
Observed
Assessed
Proposed
Executing
Verified
```

Controls:

- redirect Objective;
- pause;
- resume;
- cancel;
- change Provider order.

### 9.4 Terminal

- explicit victory/failure;
- verified reason;
- final resources and Actor health;
- Objective completion;
- score components;
- last decisive verified events;
- continue to M5 replay placeholder.

M4 does not implement replay scrubbing.

### 9.5 Debug separation

The current M1 manual Commands, M2 single-Agent controls, raw JSON receipt, and raw Host timeline move to:

```text
/debug.html
```

or an explicit `?debug=1` route. Legacy APIs remain unchanged for compatibility and engineering tests.

## 10. Frontend structure

M4 keeps browser code dependency-free but splits it into testable ES modules:

```text
web/app.js                 bootstrap and route state
web/api.js                 typed request helpers
web/store.js               one immutable client view state
web/render-shell.js        deployment/mission/terminal shell
web/render-map.js          station topology and entities
web/render-actors.js       Actor evidence stages
web/render-inbox.js        intervention cards and controls
web/render-objectives.js   Objective dependency view
web/render-timeline.js     recent semantic Rounds
web/styles.css             product tokens and responsive layout
web/debug.html             legacy engineering controls
web/debug.js               existing M1/M2/raw behavior
```

Pure render functions accept `MissionControlView` fragments and return HTML strings. They can be tested under Node without adding JSDOM or a browser framework.

The current undefined CSS custom properties (`--line`, `--muted`, `--online`) are removed through a complete token definition rather than patched individually.

## 11. Timeline boundary

M4 provides a bounded recent mission feed, not full replay.

A timeline item is derived primarily from one Team Round:

```ts
interface MissionTimelineItem {
  cursor: string;
  worldRevision: number;
  turn: number;
  status: "verified" | "blocked" | "terminal";
  actorActions: TimelineActorAction[];
  worldFacts: string[];
  authorityEvents: string[];
  playerEvents: string[];
  summary: string;
}
```

Default main-view timeline:

```text
latest 12 Rounds
```

The paginated endpoint accepts a stable cursor and a maximum limit of 50. M5 may later build replay and key-turn analysis from the same retained sources.

## 12. Security and authority presentation

The UI must never imply that approval guarantees success. An authority card says:

```text
Approval permits this Proposal to participate in deterministic subset selection.
It may still be rejected by conflict, stale World state, or World preconditions.
```

Every authority request displays:

- Actor and role;
- exact operation and target;
- reason and risk tags;
- current resource bands;
- expiry Tick;
- known direct resource consumption;
- approve and deny commands;
- evidence references available in debug detail.

## 13. Migration and compatibility

- World schema and digest do not change for M4 presentation work.
- M1/M2/M3 legacy APIs remain callable.
- existing Tasks without `control` normalize to active;
- existing Runs without Team configuration infer:

```text
authorityPolicyMode = autonomous
providerOrder = existing Task providerOrder or fixture
```

- inferred configuration is materialized only on the first explicit configuration write, not on GET;
- M3 receipts and replay remain valid;
- main product uses M3 Runs only.

## 14. Acceptance criteria

### 14.1 Control truth

1. a paused Actor receives no new Context or Proposal across repeated advance calls;
2. resume makes the Actor eligible again;
3. a cancelled Actor never re-enters the Run;
4. a denied Proposal is never selected or executed;
5. other active Actors may progress while one is paused, cancelled, denied, waiting, or technically failed;
6. Provider and authority changes survive process restart and page reload.

### 14.2 Read model

1. a 22-Round mission-control state response is at most 64 KiB;
2. repeated GETs append no Host or World event;
3. Actor observations are bounded by the exact retained Actor Context;
4. Provider rationale is labelled assessed/unverified;
5. proposed, executing, and verified stages cannot be confused by field or UI class;
6. current/recent history does not grow unbounded in the main response.

### 14.3 Player operation

1. a scripted client can complete the deterministic containment victory using only mission-control APIs;
2. the client never reads raw Host Journal payloads or submits primitive World Commands;
3. every authority request includes deterministic consequence and urgency text;
4. denying or redirecting a Proposal changes the admitted action path;
5. the Security spare-parts Proposal produces a resource-mismatch card before execution;
6. reload with `?runId=` restores the same mission and pending decision;
7. all three specialists, their locations, inventories, current Tasks, and waits are visible;
8. terminal victory or failure is explicit and includes verified reason.

### 14.4 Product boundary

1. the main page contains no M1 manual Command controls;
2. the main page contains no M2 single-Agent panel;
3. raw IDs and JSON are hidden by default;
4. legacy engineering controls remain available in debug mode;
5. no runtime dependency or frontend build pipeline is added.

## 15. Decision summary

M4 is necessary because M3's trusted execution is currently inaccessible as a game. The correct next architecture is:

```text
fix player-control truth
→ persist real Team configuration
→ derive one bounded mission-control read model
→ expose player-visible Round frontiers
→ replace the engineering page with a semantic control room
```

M4 should not solve weak coordination by hiding it. It should make weak coordination observable and interruptible.
