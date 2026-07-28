# M4 receipt — playable mission-control interface

## Verdict

M4 is complete.

Station Zero now has a player-facing Mission Control product above the verified M3 Team system. The player can create or resume a Run, configure three independent specialist Providers and authority policy, inspect bounded Actor-local evidence, stop before World mutation to review Proposals, intervene through typed commands, and commit at most one independently verified Team Tick.

The deterministic Fixture team reaches `victory / rescue_signal_verified` in 18 World Ticks using only Mission Control APIs. The terminal `MissionControlView` is 16,465 encoded bytes, repeated state reads create no Host Journal events, and recovery reproduces the exact terminal digest.

M4 does not add a frontend framework, runtime dependency, hidden manager model, new World authority, replay system, or live-model strategy correction.

## Implementation sequence

M4 was delivered through the following slices:

- PR #31 — reviewed M4 product and implementation design;
- PR #32 — durable player controls and checked per-Run configuration;
- PR #33 — bounded Mission Control read model and player-semantic API;
- PR #34 — playable dependency-free Web and isolated engineering debug surface;
- closeout changeset — AND/OR Objective resolution, frozen evaluation, receipt, evidence test, and milestone status.

The implementation order changed from six mechanical PRs to three implementation PRs plus closeout. The read model and API were combined because neither contract was meaningful without the other; the Web shell and decision center were combined because they shared one dependency-free rendering surface.

## Control truth

The audit at M4 entry found that the old `pause` input changed only the current Task state. The next Context preparation could reactivate that Actor. Proposal denial also remained eligible for legal-subset selection.

M4 adds explicit durable Task control:

```text
active
paused
cancelled
```

The Team Host now excludes paused, cancelled, terminal, and rejected work from cognition and selection. Resume is explicit. Cancellation is irreversible within the current Run. Denied Proposals remain historical evidence but cannot enter a TickPlan.

Per-Actor Provider order and per-Run authority policy are persisted as checked projections with Host Journal heads. Fresh-process tests prove that pause, resume, cancellation, Provider replacement, authority configuration, and a pending Proposal-review frontier survive process replacement.

Configuration-only changes do not advance the World revision.

## Bounded Mission Control read model

The product reads one pure projection rather than exposing the growing internal Team response:

```text
MissionControlView
├── Run and mission status
├── bounded resource state and trends
├── station topology
├── all specialists, crew, systems, hazards, and inventory
├── Objective graph and Actor assignments
├── current coordination Round
├── intervention inbox
├── recent semantic timeline
└── available player controls
```

The read model is rebuilt from authoritative World, Host, Team, Context Artifact, Proposal, TickPlan, and Observation state. It does not maintain a second truth store.

Repeated reads are semantically pure:

```text
identical views: true
Host Journal delta: 0
```

The complete 18-Tick terminal response is:

```text
16,465 bytes
```

This is below the M4 hard target of 64 KiB and substantially below the approximately 270 KiB raw M3 engineering response.

## Player-visible execution frontiers

M4 exposes two bounded execution operations:

### `proposal-review`

The service advances internal Host steps until all current Actor Proposals are available, then stops before World mutation.

Frozen evidence:

```text
World revision: 0
Actor Proposals: 3
World mutation before review: false
```

### `tick-verified`

The service admits one compatible Proposal subset, dispatches one Team Tick, observes the World result, verifies per-Intent effects, and stops.

Frozen first-Tick evidence:

```text
World revision delta: 1
phase: verified
verified Facts: 6
```

The API does not expose primitive World Commands as product controls. Legacy manual and raw engineering APIs remain available only through the explicit debug surface.

## Evidence semantics

Actor panels distinguish five stages:

```text
Observed
Assessed · unverified
Proposed
Executing
Verified
```

Observed items come from retained Actor-local Context. Assessed items are Provider rationale and confidence and are labelled unverified. Verified items come only from World Observation and per-Intent Verification.

No generic Belief Store or shared transcript was introduced.

## Intervention inbox

Deterministic rules create intervention cards for:

- authority requests;
- resource mismatch;
- conflicting or redundant Proposals;
- Task waits;
- Provider failure;
- pending Messages;
- mission risk.

Every authority card includes an explanation, consequence, urgency, expiry window, and typed approve/deny commands.

A frozen supervised run reached an authority frontier. Denying the exact Proposal kept it out of the selected TickPlan and changed the admitted action path while allowing the Round to continue to a verified Tick.

The M3 spare-parts failure mode is visible before execution: when Security proposes taking repair parts while Engineer still owns unsatisfied repair Objectives, Mission Control emits a critical `resource-mismatch` card involving both Actors and offers deny or pause intervention.

## AND/OR Objective resolution

The Fixture victory uses Security containment rather than Engineer sealing. The initial M4 projection showed 11/12 satisfied nodes even after verified victory because `breach-sealed` remained false.

M4 closeout corrected this product semantic without changing World or Objective predicates:

```text
11 satisfied
1 superseded alternative
12 resolved / 12 total
```

An unchosen branch of an already satisfied OR Objective is now shown as `superseded`, not as an incomplete required task.

## Playable Web and debug boundary

The root Web product provides:

- new deployment and retained-Run resume;
- URL-based `?runId=` selection and reload recovery;
- independent Provider selection for Engineer, Medic, and Security;
- authority policy selection;
- station topology and entity ownership;
- resource state and deterministic trends;
- Objective dependencies and assignments;
- Proposal review and one-verified-Tick commit;
- intervention inbox;
- Actor pause, resume, cancel, Provider replacement, and Objective redirect;
- semantic recent timeline;
- verified terminal outcome and score.

The old engineering controls remain at:

```text
/debug.html
```

That page retains M1 manual Commands, M2 single-Agent controls, M3 raw Team controls, replay, receipts, and raw identifiers. The product root contains none of those controls or raw logs.

The Web remains plain HTML, CSS, and ES modules. Runtime dependency count remains zero.

## Frozen automated evidence

Machine-readable evidence is stored in [`M4-EVALUATION.json`](M4-EVALUATION.json) and bound to implementation revision:

```text
123e89bfd33f4fcd99149c95d08d6bb86dcaca2f
```

Fixture terminal evidence:

```text
status: victory
reason: rescue_signal_verified
turn: 18
world digest: a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7
score: 2264
World events: 18
replay verified: true
recovered digest matches: true
terminal response: 16,465 bytes
```

Control and reload evidence confirms all of the following:

- pending Proposal review restored;
- pause restored;
- paused Medic excluded from Proposal generation;
- resume persisted;
- cancellation persisted;
- Provider assignment persisted;
- authority policy persisted;
- configuration caused no World revision change.

The standalone Web smoke renders a real `MissionControlView`, verifies all three specialists, Proposal controls, evidence stages, terminal score, retained Run handling, and product/debug isolation. Static HTTP tests load the complete ES-module graph.

The local environment did not contain Chromium, Firefox, Playwright, or Puppeteer. M4 therefore does not claim screenshot or real-browser automation evidence and did not add a browser dependency solely to manufacture it.

## Final repository gates

The closeout branch passed the full repository gate:

```text
178 tests
178 passed
0 failed

Lines:     98.68%
Branches:  90.10%
Functions: 98.30%
```

The frozen M1 receipt remains unchanged:

```text
victory digest: 41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2
failure digest: 4db74d8a1d2f4583031d5ba7f2fbe9310ef89ef3f57847d803eb70edab737ac1
replay verified: true
```

`pnpm measure` also retained the fixed recovery and communications-first baselines, 1,000 random runs, and the 103 one-step perturbation alternatives. M4 therefore changes product control and presentation without moving frozen M1–M3 World behavior.

## Acceptance matrix

| Issue #6 acceptance condition | Result |
|---|---:|
| Complete Fixture mission through Mission Control only | Passed |
| Pause/resume/cancel/deny/Provider/authority survive process and reload | Passed |
| Authority requests explain consequence and urgency | Passed |
| Intervention changes admitted action path | Passed |
| Security spare-parts mismatch visible before harmful Tick | Passed |
| Observed/assessed/proposed/executing/verified are distinct | Passed |
| Repeated GET creates no semantic event | Passed |
| Terminal response at most 64 KiB | Passed — 16,465 bytes |
| Main product exposes no primitive Command control or raw logs | Passed |
| No runtime dependency, manager model, framework, or new World authority | Passed |

## What M4 proves

M4 proves that the deterministic World and persistent multi-Agent Host can support a small playable operations product without collapsing into either a raw engineering dashboard or a hidden autonomous manager.

The player can intervene at meaningful semantic boundaries while models remain proposers and the World remains authoritative. Product readability is achieved through a bounded derived projection, not by weakening evidence or duplicating state.

M4 also proves that limited player control can coexist with durable Agent autonomy: one Actor may be paused, redirected, denied, reconfigured, or cancelled without silently resetting the whole team or mutating unrelated World state.

## Costs and limitations

M4 added a second presentation projection and approximately one thousand lines of dependency-free Web rendering. This is justified by the removal of raw infrastructure coupling from the player product, but it creates projection-maintenance cost whenever World or Team contracts change.

Remaining limits are deliberate:

- no replay scrubbing or causal diagnosis;
- no resource curves or key-turn extraction;
- no configurable World loadout or alternate seeds;
- no batch comparison through Ordivon Runtime;
- no browser automation evidence in the current environment;
- no claim that Codex or Hermes strategy quality improved after M3;
- no new item-transfer Command or automatic resource negotiation.

Live Provider runs were not repeated because M4 changes control, projection, and presentation rather than cognition semantics. M3 remains the canonical live Codex/Hermes evidence.

## Boundary after M4

M5 is now the only remaining milestone before the first playable release receipt.

M5 should add replay and causal analysis, configuration comparison, fixed scenario seeds, resource curves, Runtime batch experiments, and a clean-checkout release receipt. It should not reopen M4 by adding a general game platform, frontend framework, hidden manager, Society layer, multiplayer, or 3D pipeline.
