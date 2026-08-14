---
schema_version: 1
id: game.station-zero-v3.planning
title: Station Zero v3 — P3 first-playable planning layer
type: architecture
profile: engineering
lifecycle: accepted
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - player
  - designer
  - builder
  - agent
updated: 2026-08-14
summary: Accepted target architecture for the unregistered Station Zero v3 Commander Orders, bounded Agent planning, sealed Plan Preview, explicit Commit, dedicated API, first-playable browser, and recovery.
evidence_status: verified
readiness: READY
applies_to:
  - station-zero-v3-unregistered
related:
  - game.station-zero-v3.encounter
  - game.station-zero-v3.reducer
  - game.station-zero-v3.execution
  - game.authority
---
# Station Zero v3 — P3 first-playable planning layer

## Status

P3 connects the P0 encounter, P1 deterministic reducer, and P2 durable execution path into a bounded playable product preview.

```text
Target Scenario: station-zero@3
Target Ruleset: station-zero-core@4
World schema: 3
Commander Orders: complete
Agent Context / Candidate / Decision contract: complete
Optional exact Agent Action admission: complete
Policy-unit expansion: complete
Plan Preview and explicit Commit: complete
Dedicated v3 HTTP API: complete
Dedicated /v3 browser first-playable: complete
Process-restart recovery: complete
Current station-zero@2 replacement: deferred
G3 bounded live Provider realization: accepted; G4 production-experience validation pending
```

Station Zero v3 remains absent from `src/registry.ts`. The current root product and its v2/v3 execution contract remain unchanged. P3 is exposed only through a separate v3 database, API namespace, and `/v3` preview surface.

## Product loop

The P3 player loop is:

```text
read bounded Situation
→ edit Commander Order
→ generate one three-faction Plan Preview
→ inspect Rescue intentions and known risks
→ see Pirate and Swarm plans only as sealed commitments
→ explicitly Commit the Turn
→ P2 atomically executes and verifies the canonical Batch
→ inspect player-visible Aftermath
→ recover or continue from the next Planning Head
```

The player no longer authorizes routine Actor actions one at a time.

The explicit decision boundary is the complete simultaneous Turn.

## Authority split

### Player owns

- primary mission objective;
- cautious, balanced, or aggressive posture;
- cohesive or split formation;
- retreat threshold;
- lethal-force policy;
- collateral policy;
- loot policy;
- protected specialist;
- a known priority target;
- one remote Commander directive;
- the final decision to Commit the generated Turn.

### Agent Providers own

- selection among World-admitted local Candidates for high-fidelity Actors;
- a bounded rationale;
- confidence;
- Pirate Captain or Hive Alpha faction directive selection.

### Deterministic policies own

- expansion of the Pirate Captain directive to Hacker and Raider actions;
- expansion of the Hive Alpha directive to Stalker and Drone actions;
- stable tie-breaking among admitted Candidates.

### The World owns

- whether the committed operation remains valid;
- movement and Zone capacity;
- reactions;
- damage, injury, death, capture, and extraction;
- systems and environmental consequences;
- objective progress and faction outcomes.

### P2 owns

- immutable Faction Plan submission;
- canonical Batch identity;
- Host Task and Dispatch continuity;
- atomic Event / Record / World Head persistence;
- crash recovery and replay.

## Order, Preview, and Commit are separate states

P3 intentionally does not treat model deliberation as World commitment.

### Commander Order

The Commander Order is mutable while the underlying P2 Planning Head remains open and contains no durable Faction Plan.

Every revision is retained in a hash chain.

Changing the Order:

- increments the Order revision;
- clears the active Preview reference;
- requires the Plans to be generated again;
- does not alter World state;
- does not occupy any P2 Faction Plan slot.

### Plan Preview

A Preview contains:

- the exact Order revision and digest;
- bounded Agent Contexts;
- high-fidelity Agent Decisions;
- deterministic policy Decisions;
- the complete Rescue, Pirate, and Swarm Faction Plans;
- Rescue-facing explanations;
- known tactical risks;
- one content digest.

The authoritative database retains the complete Preview for later verification.

The player-facing projection reveals:

- Rescue intentions, rationales, and confidence;
- Rescue remote Commander action;
- Rescue-visible warnings;
- only the digest of each enemy Faction Plan.

The Browser never receives Pirate or Swarm Actor intentions before resolution.

### Commit

Only the currently active Preview may be committed.

Commit performs:

```text
selected Preview
→ submit its exact Rescue Plan
→ submit its exact Pirate Plan
→ submit its exact Swarm Plan
→ bind Order Head to selected Preview
→ P2 canonical Batch
→ P2 Host execution and World commit
```

After the first durable Faction Plan is submitted, the Commander Order and selected Preview are immutable.

## Agent Context

`StationZeroV3AgentContext` is the complete decision surface for a high-fidelity Agent.

It contains:

- exact identity and current state of the controlled Actor;
- global public resource telemetry;
- faction-discovered Zones and frontier Zones;
- faction-known Actors with health bands and confidence, not hidden exact values;
- faction-known Systems, Hazards, Items, and reports;
- faction objectives;
- the player Order only for Rescue specialists;
- a closed list of legal Candidates;
- a context digest.

It does not contain:

- hidden enemy positions;
- hidden exact enemy health;
- hidden inventory or equipment;
- enemy Commander Orders;
- another faction's Plan;
- direct World mutation capability.

At Genesis, Rescue Agent Contexts contain no Pirate Captain or Hive Alpha contact.

Pirate and Swarm Contexts never contain the player's Commander Order.

## Candidate admission

Providers do not emit arbitrary game commands.

P3 first enumerates Candidates from the current World and faction Knowledge:

- bounded movement;
- known-target attacks;
- local repair, stabilization, rescue, capture, devour, infect, or hack;
- known local Item pickup;
- extraction where currently available;
- guard or reaction;
- Ability use;
- wait.

The Provider returns only a Candidate identity.

Admission rejects:

- invented Candidate identities;
- stale Context digests;
- another Actor or Faction identity;
- invented Pirate or Swarm directives;
- invalid confidence;
- empty rationale or Provider identity.

The selected Candidate is copied into the Faction Plan. Free-form Provider prose never becomes a privileged operation.

## Optional exact Agent Action admission

Candidate admission proves that a Provider selected a legal local action. It does not by itself prove which continuing Subject and which concrete Cognition instance are authorized to embody that Actor for the submitted Intent.

The v3 Store therefore exposes an optional stronger admission boundary. It is deliberately disabled unless a caller enables it for one exact open Planning Head. When disabled, existing P3 planning and execution behavior is unchanged.

When enabled, every Agent-controlled Actor Intent in that Planning must have one exact `StationZeroV3AgentActionBinding`:

```text
Subject identity
+ Cognition identity
+ source authority / evidence digest
+ Run identity
+ Planning identity
+ World revision / digest
+ Actor identity
+ exact Intent digest
```

Game canonicalizes this Game-owned binding and retains its digest with the admission. It rejects:

- a binding for another Run, Planning, World revision, Actor, or Intent;
- a supplied binding digest that differs from the canonical Game binding;
- Subject laundering under an old digest;
- replacing an already admitted Actor with another Cognition, Subject, evidence identity, or Plan;
- upstream-private fields that are not part of the Game contract;
- persistent admission rows whose binding, Cognition, Plan, or admission digest drifts after restart.

`sourceEvidenceDigest` is opaque provenance. Game does not parse a Harness Run, World embodiment object, Provider transcript, or other upstream-private schema to decide action authority. An adapter may normalize upstream evidence into the Game binding, but the Game boundary remains stable if the upstream evidence format changes.

This is **action-scoped embodiment admission**, not a Presence system. It creates no global Subject registry, Cognition registry, Embodiment manager, Presence registry, or cross-world identity service. The World still decides whether the admitted Intent can produce a consequence when the Turn executes.

## High-fidelity and policy Actors

P3 invokes the Agent Provider for exactly five high-fidelity Actors when active:

```text
Engineer Imani
Medic Reyes
Security Chen
Pirate Captain Veyra
Hive Alpha
```

Lower-cost deterministic policy expansion controls:

```text
Pirate Hacker Nyx
Pirate Raider Holt
Swarm Stalker Kappa
Swarm Drone One
Swarm Drone Two
spawned Broods
```

This proves hierarchical control without requiring a full model call for every creature.

A future hundred-Agent world should preserve this pattern:

```text
few strategic cognition nodes
→ bounded directives
→ many deterministic or lightweight local policies
```

## Fixture Provider

The first-playable uses `FixtureStationZeroV3AgentProvider` by default.

It is a deterministic executable baseline, not a claim that the final Agent behavior is solved.

The fixture Provider:

- receives the same bounded Context intended for a live Provider;
- selects one admitted Candidate;
- produces one rationale and confidence;
- makes Order changes materially alter Rescue plans;
- selects Pirate and Swarm directives;
- supports deterministic browser tests and replay diagnosis.

`StationZeroV3AgentProviderFactory` allows the live Provider to replace the fixture without changing World, Planning, persistence, or browser contracts. The current server can select the DeepSeek Provider pool through `ORDIVON_GAME_V3_PROVIDER=deepseek`; the deterministic World remains independent from model availability.

G3 live holdouts established bounded Candidate admission, hidden-information safety, stable Provider execution, and real strategic realization. `objective:advance` and `responsibility:advance` now expose Game-owned current-action meaning without compiling a winning sequence into Provider instructions. Shipping-quality planning latency, waiting experience, and outcome distribution remain G4/later product questions rather than P3 architecture claims.

## Tactical route behavior

The first-playable planner includes explicit bounded route pressure for important known objectives:

- Rescue Airlock;
- Medical Ward;
- Life Support Console;
- Reactor Console;
- Maintenance Nest;
- Cargo Airlock.

Route tags are created only for faction-known destination Zones.

They guide Candidate selection but do not reserve success. Reaction fire, capacity contention, target movement, death, and environmental damage can still interrupt a Preview.

A Preview is therefore an explainable commitment, not a promise.

## Civilian escort correction

P3 playtesting exposed a P1 World omission: a rescued civilian was bound to a specialist but remained fixed in the original Zone.

The reducer now treats escorted civilians as part of the moving party.

Rules:

- every escorted civilian consumes one destination capacity slot;
- an interrupted specialist leaves the civilians in the source Zone;
- a successful move emits one `actor_moved` Fact for the specialist and each escorted civilian;
- extraction moves the specialist and locally escorted civilians to `extracted`;
- objective progress derives from those World states.

This is a World rule, not a planner shortcut.

## Player projection

`createStationZeroV3PlayView()` extends the P2 bounded Mission Control view with:

- current Commander Order;
- active Rescue Plan Preview;
- sealed enemy Plan digests;
- known tactical map;
- own specialist cards;
- objectives;
- visible Aftermath Facts;
- Rescue Intent Results;
- asymmetric terminal outcomes.

The known map is built only from Rescue Knowledge.

Enemy contacts appear only at their retained last-known Zone and confidence.

## Dedicated API

P3 adds a separate namespace:

```text
GET  /api/station-zero-v3/catalog
GET  /api/station-zero-v3/runs
POST /api/station-zero-v3/runs
POST /api/station-zero-v3/resume
GET  /api/station-zero-v3/state
POST /api/station-zero-v3/order
POST /api/station-zero-v3/preview
POST /api/station-zero-v3/commit
```

The current v2 APIs remain unchanged.

The Preview endpoint returns only:

- Preview identity;
- Preview digest;
- idempotency status;
- the bounded player-safe Play View.

Complete Agent Contexts, Decisions, and Pirate/Swarm Faction Plans remain server-side evidence. They are not sent to the browser and are not merely hidden by rendering code.

The v3 Store uses a separate database by default:

```text
data/station-zero-v3.sqlite3
```

Consequently, v3 Runs do not appear in the current `/api/runs` contract.

## Browser first-playable

The preview is served at:

```text
http://127.0.0.1:4173/v3
```

The interface provides:

- new and retained Run selection;
- Turn and resource telemetry;
- Commander Order form;
- plan generation;
- three Rescue intention cards;
- sealed Pirate and Swarm Plan cards;
- explicit simultaneous Commit;
- own Actors and objectives;
- Rescue-known station map;
- visible Aftermath evidence;
- terminal faction outcomes.

The current root browser remains unchanged.

## Recovery

On browser refresh or process restart:

```text
recover P2 World / Host history
→ verify P3 Order and Preview evidence
→ reconcile any response-lost prior Turn
→ retain or open the correct Planning Head
→ restore the current Order and Preview
```

The selected Preview survives restart before Commit.

If execution stops after only some Faction Plans were submitted, the Order and Preview become non-editable but the same Preview remains committable. Identical retained Plans are reused and missing Plans are submitted under their original identities.

If P2 already prepared the canonical Batch and Host Dispatch but the World result is absent, the same Commit resumes that prepared execution. It does not generate a replacement Preview, Task, Batch, or Dispatch.

A response-lost World result is reconciled under its original Dispatch before another Planning Head opens.

## Evidence verification

P3 verification checks:

- Order revision sequence and hash chain;
- Order content digest;
- Order Head revision and active Preview reference;
- Preview identity and digest;
- Context digest;
- Agent Decision admission;
- complete active-Actor plan coverage;
- exact Faction Plan content;
- selected Preview against P2 submitted Plan digests;
- all P2 World and Host evidence.

Changing an Order row or Preview row independently fails closed.

## P3 tests

`test/station-zero-v3-planning.test.ts` verifies:

1. limited Agent Contexts;
2. Candidate-only Agent Decisions;
3. Order revision and Preview invalidation;
4. material plan differences from player strategy;
5. Preview non-authority before explicit Commit;
6. exact three-faction Plan binding on Commit;
7. escorted civilian movement and extraction;
8. restart with retained Order and Preview;
9. deterministic policy-unit expansion;
10. complete 20-Turn execution without admission or recovery failure;
11. Order and Preview tamper detection;
12. continuation of the selected Preview after partial Plan submission or P2 preparation.

`test/station-zero-v3-agent-action-admission.test.ts` separately verifies the optional stronger Agent boundary: unchanged execution when admission is disabled, rejection of upstream-private binding fields, exact Subject × Cognition × Actor × Intent binding, wrong-action and Subject-laundering rejection, single-Cognition admission per Actor/Planning, successful execution under exact bindings, and restart-time failure after persisted Cognition tampering.

`test/station-zero-v3-server.test.ts` verifies the isolated v3 API, current-product separation, and that raw HTTP responses do not disclose internal Pirate or Swarm Plans.

`test/station-zero-v3-web.test.ts` verifies strategic controls, sealed enemy plans, bounded aftermath, and terminal rendering.

`scripts/e2e-station-zero-v3.ts` drives a real Chromium browser through:

```text
open /v3
→ create Run
→ change strategy
→ generate Preview
→ inspect sealed plans
→ Commit Turn 1
→ reload and recover
→ continue through Turn 14
→ inspect terminal outcomes
```

## Current product judgment

P3 proves that the new architecture can support an actual game loop.

It does not yet prove that the encounter is sufficiently fun, balanced, varied, or commercially legible.

The deterministic fixture planner can complete a full Run and form meaningful local chains such as:

```text
scan Reactor
→ power Cooling
→ route Engineer
→ repair Cooling
```

and:

```text
locate civilian
→ bind escort
→ move as one capacity footprint
→ extract specialist and civilian
```

It may still lose because enemy interference, capacity, and environmental pressure invalidate parts of the Preview. That is intentional. The fixture is a baseline opponent and planning oracle, not an automatic solver.

## Deferred after P3

The next phase should be playtest and replacement judgment rather than another infrastructure layer.

Required evidence before v3 replaces the current executable:

1. repeated human play sessions show decisions are understandable and consequential;
2. at least three non-dominated Rescue strategies are viable;
3. Pirate and Swarm directives produce recognizably different pressure;
4. planning latency and message volume remain tolerable with a live Provider;
5. a live Provider passes Candidate-admission, hidden-information, recovery, and fallback evaluations;
6. plan explanations help decisions rather than merely narrating them;
7. the tactical map communicates concurrency and uncertainty clearly;
8. obsolete v2 approval-loop structure can be deleted rather than maintained in parallel.

Do not build a larger campaign, progression system, generic RPG engine, or hundred-Agent society until the Station Zero Turn loop earns retention through play.
