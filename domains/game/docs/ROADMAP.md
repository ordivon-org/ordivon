# Roadmap

The roadmap is a dependency graph. Milestones may overlap when their invariants are stable, but later gameplay layers must not compensate for an invalid world kernel.

```text
M0 repository baseline
        ↓
M1 deterministic world kernel
        ↓
M1.5 architecture hardening
        ↓
M2 single-Agent vertical path
        ↓
M2.1 goal-directed strategy semantics
        ↓
M3 multi-Agent team and authority
        ↓
M4 player control surface
        ↓
M5 replay, evaluation, and first playable
```

## M0 — Repository baseline — implemented

Evidence: [`M0-RECEIPT.md`](M0-RECEIPT.md).

Deliverables:

- product definition;
- architecture and state ownership;
- milestone acceptance criteria;
- Apache-2.0 license;
- initial issue graph;
- selected implementation stack after a short executable spike.

Exit condition: contributors can explain what the first playable is, what it is not, and which layer owns every critical state transition.

## M1 — Deterministic world kernel — implemented

Evidence: [`M1-RECEIPT.md`](M1-RECEIPT.md).

Implemented without model calls:

- station graph and room state;
- turn/event clock;
- Agent position and inventory;
- power, oxygen, health, communications, and equipment integrity;
- typed actions and precondition failures;
- linked emergency scenario;
- immutable event log;
- snapshot and deterministic replay;
- one scripted baseline policy capable of winning and one capable of failing.

Acceptance criteria:

- resources cannot appear or disappear outside declared transitions;
- invalid actions fail without partial mutation;
- replay reaches the identical world digest;
- the scenario contains at least two meaningful resource trade-offs;
- the deterministic game is understandable before any LLM is connected.

## M1.5 — Architecture hardening — implemented

Evidence: [`M15-RECEIPT.md`](M15-RECEIPT.md).

Implemented before cognition:

- versioned multi-Run identity;
- separate Command Sequence, World Revision, and Simulation Tick;
- sparse recovery and full verification replay;
- Command/Event hash chains and typed storage errors;
- ruleset-v2 typed Facts and Verification;
- transaction fault injection;
- property-based and independent model-based validation;
- coverage gates and fixed-seed strategy measurement.

Exit condition: M2 can persist Agent cognition above the world without redefining world identity, time, replay, evidence, or transaction semantics.

## M2 — Single-Agent Host path — complete

Integrate one Engineer Agent:

- durable Goal and Task state;
- bounded observations;
- structured candidate actions;
- Context persistence before provider invocation;
- decision admission after world recheck;
- Effect → Dispatch → Observation → Verification path;
- interruption and fresh-process continuation;
- deterministic fallback policy for provider failure.

Acceptance criteria:

- the Agent cannot invent an action or object;
- stale decisions are rejected;
- a completed repair requires independent world verification;
- provider session loss does not erase mission continuity;
- all admitted actions can be replayed.

Receipt: [`M2-RECEIPT.md`](M2-RECEIPT.md). Live evaluation: [`M2-EVALUATION.json`](M2-EVALUATION.json).

## M2.1 — Goal-directed strategy semantics — complete

Expose the consequences needed for real Providers to sustain the terminal Goal:

- explicit victory requirements and distress prerequisites;
- finite threat horizons;
- persistent objective regression;
- resource and power-control meaning;
- optimistic Goal lower bounds;
- advisory strategic rank;
- exactly one subsequent-Operation lookahead.

Acceptance evidence:

- the original M1/M2 Fixture digest remains frozen;
- a public rank-one baseline wins without Fixture or Provider calls;
- Codex-only reaches verified victory;
- Codex → Hermes reaches verified victory without session transfer;
- Hermes-only variance remains honestly recorded;
- no hidden policy override changes a valid Provider Decision.

Receipt: [`M21-RECEIPT.md`](M21-RECEIPT.md). Evaluation: [`M21-EVALUATION.json`](M21-EVALUATION.json).

## M3.0 — Cross-stack correction — complete historical entry contract

Design: [`M30-DESIGN.md`](M30-DESIGN.md). Implementation entry: [`M30-PLAN.md`](M30-PLAN.md).

M3.0 corrected the first M3 architecture before implementation:

- reused Host Event, checked-projection, lease, and token-budget Context semantics;
- kept World, Objective predicates, actor observation, and Tick semantics Game-owned;
- replaced serialized one-Command interleaving with atomic multi-Actor TickBatch execution;
- constrained strategy to Actor Knowledge rather than omniscient World advice;
- replaced an authority ladder with attribute-based policy;
- mapped one selected Team Tick to Effect → Dispatch → Observation → Verification;
- selected an embedded conformance-backed TypeScript adapter instead of a sidecar.

The documents remain the reviewed historical contract against which M3 was implemented.

## M3 — Multi-Agent team and authority — complete

Receipt: [`M3-RECEIPT.md`](M3-RECEIPT.md). Evaluation: [`M3-EVALUATION.json`](M3-EVALUATION.json).

Implemented:

- persistent Engineer, Medic, and Security identities;
- specialist-exclusive capabilities;
- independent actor-local observations and token-budget Contexts;
- typed local/radio Messages with delivery and expiry;
- one shared Objective Graph and independent actor Tasks;
- attribute-based player authority and exact single-use Grants;
- explicit Proposal conflict and waiting semantics;
- atomic multi-Actor Ruleset-v3 TickBatch execution;
- durable Team Rounds, Effects, Dispatches, Observations, and fresh-process recovery;
- isolated Codex and Hermes cognition and mid-Run Provider replacement;
- synchronous Team APIs and an engineering browser panel.

Acceptance evidence:

- Security containment and Engineer sealing are two verified victory plans on the same seed;
- supervised high-risk Actions stop for exact authority;
- the same task Message produces victory over local delivery and `power_exhausted` when radio delivery is delayed;
- one Provider failure leaves unrelated specialist Proposals intact;
- eight interruption boundaries converge without duplicate effects;
- all-Codex and mixed Codex/Hermes teams reach verified victory;
- all-Hermes and Codex-to-Hermes replacement failures remain exact, replayable counterexamples rather than being hidden-corrected.

## M4 — Playable mission-control interface — complete

Receipt: [`M4-RECEIPT.md`](M4-RECEIPT.md). Evaluation: [`M4-EVALUATION.json`](M4-EVALUATION.json). Design: [`M4-DESIGN.md`](M4-DESIGN.md). Implementation plan: [`M4-PLAN.md`](M4-PLAN.md).

M4 converted the M3 engineering panel into a truthful player product:

- make pause, resume, cancel, deny, Provider assignment, and authority configuration durable and enforced;
- add one bounded mission-control read model rather than exposing raw Team history;
- expose player-visible Proposal-review and one-Tick-verified frontiers;
- render the station map, all specialists, resources, Objective dependencies, and inventory ownership;
- distinguish observed, assessed, proposed, executing, and verified information;
- explain authority, urgency, waiting, communication, conflict, redundancy, and resource mismatch;
- support approve, deny, redirect, pause, resume, cancel, and Provider replacement;
- move M1/M2/manual/raw controls to an explicit debug surface;
- show a clear terminal outcome without implementing M5 replay.

Acceptance evidence:

- the Fixture team reaches verified victory in 18 Ticks through Mission Control APIs only;
- every requested approval explains deterministic consequence and urgency;
- Proposal denial changes the admitted action path;
- pause, resume, cancel, Provider, authority, and pending review survive process replacement and reload;
- the interface distinguishes observation, unverified assessment, Proposal, execution, and verified Fact;
- the terminal response is 16,465 bytes, below the 64 KiB target;
- repeated state reads create no semantic event;
- the Security spare-parts mismatch is detected before commit;
- the main product adds no runtime dependency, hidden manager model, framework, primitive World control, or raw Host log.

## M5 — Replay, diagnosis, comparison, and first playable — implementation in progress

Design: [`M5-DESIGN.md`](M5-DESIGN.md). Release implementation graph: [`M5-PLAN.md`](M5-PLAN.md). Entry audit: [`M1-M4-DEBT-AUDIT.md`](M1-M4-DEBT-AUDIT.md).

Release target: `v0.1.0-alpha.1`, a local source-playable developer Alpha whose default browser journey uses deterministic Fixture cognition.

M5.0 and verified point-in-time World replay are complete. The remaining critical path is:

```text
Evidence Graph + Replay Frames
→ Diagnosis and immutable Deployment/Comparison
→ Replay/Diagnosis/Compare Web + Chromium E2E
→ exact release archive and clean verification
```

Acceptance criteria:

- every revision from Genesis to terminal reconstructs to the retained digest and a bounded Replay Frame;
- a deterministic failure and victory expose evidence-linked explanations without model-generated causal claims;
- one immutable deployment change produces a verified improvement and two compatible Runs compare exactly;
- one Chromium journey proves deploy → play → terminal → replay → diagnose → reconfigure → compare;
- a clean unpacked source archive passes all release checks and reproduces the frozen receipt;
- runtime dependencies remain zero and no second World, Host, replay, diagnosis, or comparison authority is added.

Equal-budget ablations, Runtime experiment matrices, and final embedded Host convergence remain explicit post-alpha work. They constrain later scientific and platform claims but do not block the first deterministic source-playable release.

## Post-alpha opportunity graph

The first playable is not the complete definition of Ordivon Game. After M5 evidence, later work may proceed through several independent opportunity tracks. These are hypotheses and bounded experiments, not one mandatory feature sequence.

```text
                         M5 first playable
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
       G-PLAY                 G-WORLD               G-CREATE
playground and return   Agent participation      player/Agent creation
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                ▼
                         optional verticals
                 product worlds / social worlds /
                 evaluation / Security / Arena
```

### G-PLAY — Playability, leisure, and return

Prove that Station Zero or a second small world can remain enjoyable outside terminal mission optimization:

- one optional non-mission activity;
- one relationship or world consequence that changes later interaction;
- one event not caused by a player Objective;
- one reason to revisit after mastering the emergency.

### G-WORLD — Agent-native world participation

Test identity, body, memory, relationships, self-directed activity, longer timescales, and world history. Do not begin with hundreds of residents or a generic civilization engine.

### G-CREATE — Creative medium and modding

Test bounded player-authored scenarios, Agent-created Artifacts, construction, performance, and world modification. Candidate content does not gain authoritative consequence until admitted by the Game World.

### G-EXPERIMENT — Evaluation and Security worlds

Retain deterministic Scenario Cases, hidden truth, paired trajectories, replay, reset, independent scoring, and adversarial roles as optional consumers of the Game World. Security remains a vertical consumer, not the owner of the Game roadmap.

### Deferred infrastructure

Competitive Arena modes, persistent organizations, larger Agent societies, multiplayer, hosted services, and reusable engine packages remain deferred until a concrete vertical demonstrates that their experience value or shared responsibility exceeds their cost.

## Measurement

Track from the first executable slice:

- world actions per mission;
- model calls and tokens per mission;
- decision admission/rejection counts;
- stale or unresolved Dispatches;
- average approval latency;
- recoveries after interruption;
- replay digest equality;
- mission success by team configuration;
- player-visible unexplained failures.

## Post-alpha M5-R1 control-boundary evaluation — completed

The paired control-boundary matrix is closed in
[`M5-R1-CONTROL-BOUNDARY-EVALUATION.md`](M5-R1-CONTROL-BOUNDARY-EVALUATION.md).
It retained two owner-local invariants—accepted Verification before completion
and terminal Team Task irreversibility—while rejecting a new control platform.
The next active consumer is Ordivon Security #19; equal-budget single versus
multi-Agent coordination remains deferred in #40, and Session/compaction remains
deferred in #59.
