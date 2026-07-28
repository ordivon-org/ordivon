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

## M5 — Replay, evaluation, and first playable

Complete the game loop:

- mission replay;
- key-turn identification;
- resource and system curves;
- decision and authority audit;
- outcome verification summary;
- configurable team loadout;
- several fixed scenario seeds;
- batch simulation through Ordivon Runtime;
- regression and conformance suite.

Acceptance criteria:

- a failed run exposes a concrete causal chain;
- players can improve outcomes by changing configuration;
- multiple viable strategies exist;
- the game remains bounded in model cost and latency;
- a clean checkout can run the full vertical slice;
- the repository contains an exact reproducible release receipt.

## Deferred branches

Only after M5 evidence:

- competitive Agent Arena modes;
- persistent station organization;
- larger Agent Society simulation;
- modding and user-authored scenarios;
- a reusable `ordivon-world` package;
- multiplayer or hosted service infrastructure.

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
