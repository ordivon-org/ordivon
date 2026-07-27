# Roadmap

The roadmap is a dependency graph. Milestones may overlap when their invariants are stable, but later gameplay layers must not compensate for an invalid world kernel.

```text
M0 repository baseline
        ↓
M1 deterministic world kernel
        ↓
M2 single-Agent vertical path
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

## M2 — Single-Agent Host path

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

## M3 — Multi-Agent team and authority

Add Medic and Security specialist:

- independent observations;
- distinct goals, capabilities, and risk preferences;
- limited typed communication;
- team task dependencies;
- player-defined authority thresholds;
- conflicting proposals and explicit resolution;
- no duplicate or contradictory world mutation.

Acceptance criteria:

- each specialist has at least one exclusive capability;
- the same emergency can produce different valid plans;
- restricted actions require correct authority;
- communication limits materially affect coordination;
- one Agent can continue while another waits or fails.

## M4 — Player control surface

Build the playable Web interface:

- station map;
- mission and resource status;
- Agent cards and current intent;
- task graph and requests for approval;
- configure team, tools, risk, and authority;
- approve, deny, redirect, pause, and cancel;
- readable event timeline;
- clear terminal outcome.

Acceptance criteria:

- the player can operate without reading raw logs;
- every requested approval explains consequence and urgency;
- player intervention changes the admitted action path;
- the interface distinguishes observation, belief, proposal, execution, and verified fact.

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
