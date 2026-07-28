# Initial decisions

## D-001 — Repository name

Use `ordivon-game` as the product and experimentation repository. Do not create a generic `ordivon-games` platform before one playable game exists.

## D-002 — License

Use Apache License 2.0 for source code and repository-authored documentation unless a path explicitly declares different third-party terms.

Reason: the project is intended to remain permissively reusable while preserving patent-grant and notice obligations appropriate for infrastructure-oriented work.

## D-003 — First product form

Build an Agent Operations game with Arena-style bounded missions, construction choices, scoring, and replay.

Do not begin with a persistent Agent Society. Society remains the long-horizon direction after small-team autonomy is stable and understandable.

## D-004 — Web first

Use a browser-based 2D or graph interface for the first playable. Avoid Unity, Unreal, and asset-heavy pipelines until the core loop proves itself.

## D-005 — Deterministic world before cognition

The first executable milestone contains no LLM. The game world, typed actions, failure semantics, resource constraints, and replay must work with scripted policies first.

## D-006 — Model outside authoritative state

Models may propose plans and candidate actions. They never directly own or mutate authoritative game state.

## D-007 — Reuse concepts, not accidental deployment topology

Reuse the semantics of Ordivon Computing, Host, and Runtime. Do not send every in-world action through a remote MCP boundary merely because that boundary exists in the current infrastructure.

## D-008 — One process before services

Start with modular packages in one local service and one database where practical. Split services only after measured requirements justify distributed boundaries.

## D-009 — Replay is a primary feature

Every admitted world command, relevant context identity, provider decision, result, and verification receipt must support inspection. Replay is required for gameplay mastery, debugging, research, and conformance.

## D-010 — No premature platform extraction

Do not create `ordivon-world`, a general workflow DSL, a modding SDK, or a universal multi-Agent scheduler before the first playable demonstrates repeated use.

## D-011 — M0 implementation stack

Use one Node.js 26 process for the first executable slice:

- TypeScript source executed through Node's native type stripping;
- strict TypeScript 7 static checking in development and CI;
- Node's built-in `node:http`, `node:test`, cryptography, and `node:sqlite` modules;
- one SQLite database for admitted commands, immutable events, and world snapshots;
- a dependency-free HTML, CSS, and browser JavaScript surface;
- one typed provider interface with a deterministic fixture implementation;
- source modules under `src/` rather than premature workspace packages or services.

The runtime has no third-party dependencies. `typescript` and `@types/node` are development-only dependencies.

The spike falsified unrestricted native TypeScript: Node's strip-only execution rejects syntax that requires transformation, such as constructor parameter properties. Production source therefore uses erasable TypeScript syntax and CI performs a separate strict type check.

React, a bundler, independent services, and reusable packages remain deferred until actual UI or deployment pressure requires them.

## D-012 — One controllable Agent in M1

M1 keeps one Engineer as the only acting Agent. The casualty is a world entity rather than an autonomous Agent.

Reason: M1 must establish deterministic gameplay, conservation, failure progression, and replay before M3 introduces independent observations, communication, authority conflict, and concurrent Agent intent.

## D-013 — Every accepted command advances the world

Movement, pickup, repair, switching power, medical stabilization, sealing, signalling, and waiting each consume one turn. Environmental hazards advance after every accepted command.

Reason: time becomes a common scarce resource across navigation, repair, rescue, and power management. Routine actions therefore participate in the strategy rather than existing outside the world clock.

## D-014 — Explicit conservation ledgers

Finite battery energy and consumable items use visible initial, remaining, and consumed quantities. World invariants check conservation after every accepted command and during recovery.

Reason: a deterministic strategy game requires stronger guarantees than narrative plausibility. Resources must not be created or erased by model output, UI behavior, retries, or replay.

## D-015 — Scripted policies are scenario proofs, not production AI

The recovery policy proves one feasible winning trajectory. The communications-first policy proves that an individually reasonable local objective can cause global failure through reactor escalation.

They are executable acceptance witnesses and regression tools. They are not intended to become the player's final autonomous team logic.

## D-016 — Run is the durable execution boundary

One `Run` identifies one independent game-world execution. Commands, events, snapshots, idempotency, recovery, and replay are scoped by `runId`. A database may contain several Runs without sharing command identity or world state.

## D-017 — Scenario, ruleset, and state-schema versions are distinct

Every Run binds `scenarioId + scenarioVersion`, `rulesetId + rulesetVersion`, `stateSchemaVersion`, seed, and creating build. Opening or replaying a Run resolves these exact versions through registries and fails closed when a version is unavailable.

## D-018 — M1 v1 is a frozen compatibility fixture

`fixtures/m1-v1` retains genesis, successful and failing command journals, events, per-step digests, and a manifest bound to the M1 source commit. Later architecture work must execute this fixture byte-for-byte or declare an explicit migration.

## D-019 — Command sequence, world revision, and simulation tick are distinct

`commandSequence` orders accepted commands inside one Run. `worldRevision` protects optimistic concurrency. `simulationTick` advances environmental time. M1.5 still admits exactly one intent per Tick, so their numeric values often coincide, but they are separate contracts and are persisted separately in the journal envelope.

## D-020 — Multi-intent Tick batches fail closed until conflict resolution exists

The kernel accepts a typed `TickBatch`, but station-zero-core v1 requires exactly one intent. This preserves the future multi-Agent shape without inventing ordering, collision, or shared-resource rules before M3.

## D-021 — Command Journal is the replay input

Run metadata, Genesis, the accepted Command Journal, and the bound Ruleset reproduce the world. Journal Events are execution receipts checked during verification. Snapshots are disposable recovery caches rather than an independent source of truth.

## D-022 — Recovery and verification replay are separate

Recovery starts from the newest valid Snapshot and replays only the command tail. Verification starts from Genesis and compares every reproduced Journal Event and digest with retained history.

## D-023 — Snapshot cadence is sparse and explicit

The default policy retains Genesis, every eighth accepted revision, and the terminal state. Old per-revision Snapshot databases are pruned during migration without deleting the Command/Event journal.

## D-024 — Command and Event streams are hash chained

Each retained Command and Journal Event records the previous record digest and its own canonical digest. Existing PR2 rows are backfilled only when integrity metadata is missing; already-populated hashes are never silently recomputed.

## D-025 — Ruleset v2 enriches evidence without changing world state

`station-zero-core@1` remains the frozen M1 compatibility reducer. `station-zero-core@2` wraps the same deterministic state transition and adds typed Facts plus a Verification receipt. New Runs default to v2; existing Runs replay with their bound version.

## D-026 — Raw state diff and domain facts coexist

`WorldEvent.changes` remains the low-level audit and replay diagnostic. `WorldEvent.facts` is the stable player/Host-facing semantic layer. `WorldEvent.verification` records command-specific checks and must succeed independently of model claims.

## D-027 — Generated tests protect the state machine

Example tests remain the readable contract, while `fast-check` properties exercise arbitrary legal sequences, stale decisions, pure/persisted/recovered equivalence, and an independent movement reference model. Generated failures must shrink to a reproducible counterexample.

## D-028 — Transaction fault points are explicit test seams

The storage adapter exposes development-only fault injection points around transaction begin, Command insert, Event insert, Snapshot write, and commit. Pre-commit faults must leave no effect. An after-commit uncertainty must converge through the same `runId + commandId` idempotency identity.

## D-029 — Mission score is a read-only evaluation projection

Mission scoring is derived from terminal WorldState and never participates in authoritative rules, victory, replay, or persistence. It exists to distinguish partial progress, resource quality, and safety outcomes before Agent evaluation begins.

## D-030 — Coverage thresholds protect the whole executable core

CI requires at least 95% line coverage, 90% branch coverage, and 95% function coverage across loaded source modules. Core achieved branch coverage is separately reviewed for `scenario.ts`, `world.ts`, and `storage.ts`; global coverage does not justify leaving a critical reducer untested.

## D-031 — Provider sessions do not identify the Engineer

The Engineer is represented by persistent Goal, Task, Attempt, semantic history, and current world binding. Codex and Hermes are replaceable cognitive calls. Their sessions, memories, tools, and transcripts never enter task continuity.

## D-032 — Host and World journals share SQLite but not authority

M2 stores Host state in the same SQLite database as the world for local atomicity and deployment simplicity. Host Journal, projections, and Artifacts use independent tables and an independent hash chain. Host records are not replay inputs for the deterministic World Kernel.

## D-033 — Models choose Operations, not primitive Commands

A Provider selects one exact strategic Operation. The Host compiles that Operation into deterministic movement, pickup, and action steps. This bounds model latency and cost while preserving the World Kernel as the only command authority.

## D-034 — Compiled Context is semantic state, not transcript replay

The M2 Context contains exact Run and Task identity, current world binding, bounded Agent observation, recent verified Facts, and the admitted Operation frontier. Provider sessions, chat history, hidden reasoning, Tool history, and complete world state are excluded. Canonical Context is capped at 16 KiB and drops recent Facts before failing closed.

## D-035 — Strategic Operations expand into deterministic Skills

Providers choose exact strategic Operation identities. The Host deterministically compiles paths, item collection, and primitive actions from the current world. Each primitive step is re-materialized against the latest world revision; a stale Operation or Skill Plan is rejected rather than repaired implicitly.

## D-036 — Routine logistics may anticipate known task requirements

When an admitted Skill already enters Storage, the deterministic controller may collect other finite supplies whose future need is directly implied by the fixed Goal and current damaged objectives. This is routine logistics, not a new strategic model decision, and remains subject to world inventory conservation and replay.

## D-037 — CLI Providers run as isolated cognition, not local Agents

Codex receives an ephemeral read-only empty work directory, ignores user configuration and rules, and must satisfy a JSON Schema. Hermes receives invocation-scoped HOME and HERMES_HOME, only the selected Provider credential, no toolsets, MCP, memory, user profile, rules, skills, or retained session. Neither CLI can inspect or mutate the game repository or world database.

## D-038 — Provider fallback handles technical invalidity only

A Provider Chain advances after timeout, unavailable executable, non-zero exit, malformed output, wrong Context identity, invented Operation identity, or invalid usage evidence. A valid admitted strategic choice is never retried merely because another model might choose differently.

## D-039 — Effect, Dispatch, and Command identities are stable across interruption

Each Skill step binds a deterministic Effect, Dispatch, and World Command identity derived from the persistent Attempt and step index. A retry uses the same Command ID. The Host first queries retained world history and observes an existing result before considering redispatch.

## D-040 — Observation and Verification advance an Attempt

A successful world write alone does not advance Skill progress. The Host retains the corresponding Journal Event as an Observation and requires the World Kernel Verification receipt to succeed before it marks the Dispatch, Effect, and Skill step complete.

## D-041 — Provider cognition is outside replay and deterministic continuation

After a Decision and Skill Plan are retained, execution and interruption recovery require no Provider call. World replay consumes only the World Command Journal. Host continuation consumes persistent Host projections, Artifacts, Effects, Dispatches, Observations, and current world state.

## D-042 — Agent control APIs are synchronous and bounded

M2 exposes initialize, step, and run operations as explicit HTTP requests. `run` is a bounded synchronous loop rather than a hidden background scheduler. Long-lived or recurring orchestration remains outside the game Host until measured demand requires it.

## D-043 — Provider selection may change between Host steps

A request selects the cognition Provider for that invocation, but Goal, Task, Attempt, Context, Decision, Effect, and world identity remain persistent. Switching Codex and Hermes does not fork the Engineer or discard prior semantic state.

## D-044 — Manual and autonomous control share the same World Kernel

Manual Commands and Agent Dispatches use the same versioned Run, Command admission, Tick reducer, journal, Facts, and Verification. Manual intervention may make a pending Context or Effect stale; the Host must reject or reconcile it rather than claim exclusive ownership of the world.

## D-045 — Goal semantics are explicit Host data

The Host derives a public dependency graph for terminal victory requirements and distress prerequisites. Models are not expected to reconstruct the mission graph solely from booleans and prose. The graph annotates Decisions but does not grant world authority.

## D-046 — Strategic rank is advisory, not admission policy

Every current Operation remains selectable unless the existing world and identity admission rejects it. The Host may sort and annotate Candidates using Goal progress, threat horizons, regression, resource use, and optimistic lower bounds. It does not silently replace a valid Provider choice with rank one.

## D-047 — Lookahead is bounded to one subsequent Operation

For each Candidate, the Host may compile one additional frontier and report whether projected victory is available on the next strategic decision. Full state-space search was measured and rejected because it exceeded the latency and complexity budget of the thin Host.

## D-048 — Power-off meaning depends on Goal and safety state

Power-off Operations are neither universally removed nor treated as equivalent. Cooling shutdown is beneficial when the reactor remains within the victory heat threshold over the optimistic remaining Goal horizon. Communications power is a prerequisite only until distress transmission. Life-support power remains a terminal requirement. These semantics are exposed to the Provider and tested without changing World rules.

## D-049 — M3 uses independent specialists without a manager model

Engineer, Medic, and Security each own persistent actor-scoped Tasks, Attempts, Contexts, Proposals, and replaceable Providers under one shared Team Goal. The Host compiles public task, authority, communication, conflict, and scheduling semantics but does not add a hidden manager model that chooses the team plan.

## D-050 — Multi-Agent cognition may be concurrent while World mutation remains serialized

M3 may invoke bounded specialist Providers concurrently and may retain multiple non-conflicting active Attempts. The authoritative World still commits exactly one primitive Command per simulation Tick. Interleaving provides independent progress without redefining Command/Event replay, environment advancement, or partial multi-intent retry semantics.

## D-051 — Team coordination is represented by explicit graphs and typed waits

M3 uses an AND/OR Team Task DAG, a time-varying communication graph, and a per-round Proposal conflict graph. Waiting is persisted with typed dependency, message, authority, conflict, replan, or Provider reasons so one blocked specialist cannot implicitly block unrelated work.

## D-052 — Communication and authority remain separate bounded protocols

Agent communication uses typed delivery-limited Messages that reference immutable Facts and Artifacts. Restricted Operations require stale-sensitive, single-use Authority Grants bound to the exact Proposal, Context, actor, and World digest. A Message can request authority but cannot provide it.

## D-053 — M3.0 is a cross-stack correction, not a feature milestone

M3.0 freezes ownership, time, state, observation, authority, and deployment contracts before specialist implementation. It changes no World rules or executable code and does not satisfy Issue #5. The first M3 documents remain as superseded design history.

## D-054 — The Team Coordinator is an Ordivon Host workload, not a new Kernel

Goal and Task continuity, Host Events, checked projections, leases, Context compilation, Provider turns, candidate admission, waiting, and outcomes follow `ordivon-host` contracts. Game supplies Objective predicates, actor-visible observations, candidate semantics, message reachability, conflict predicates, and World execution. A conformance-backed embedded adapter may precede extraction, but Game does not define a second permanent Host architecture.

## D-055 — Atomic multi-Actor TickBatch supersedes serialized one-Command-per-Tick M3 execution

D-050 is superseded for M3. Compatible actors may contribute at most one primitive Intent each to one atomic TickBatch. All preconditions bind the same before-state, shared resources are reserved across the batch, environment advances once, mission evaluates once, and one TickEvent carries per-Intent receipts. Ruleset v1/v2 remain unchanged.

## D-056 — One Game Objective Graph supersedes a separate Team Task dependency graph

D-051's separate Team Task DAG is superseded. Game owns one Objective Graph with AND/OR satisfaction predicates and visibility. Host Tasks represent durable actor claims, attempts, and coordination state for Objectives; they do not duplicate Objective dependencies.

## D-057 — Multi-Agent strategy is bounded by Actor Knowledge

Physical admission may use authoritative World truth, but actor Context, candidate annotations, Tasks, and advisory ranks may use only public alarms, local observations, delivered Messages, and visible verified Facts. M2.1's omniscient strategic score cannot become the team scheduler or leak hidden state.

## D-058 — Attribute-based policy replaces the M3 authority ladder

Authority is decided from subject, action, target, environment, and player policy attributes. The result is permit, require-human, or deny. Capability and authority remain distinct. A Grant is single-use and binds the exact actor, proposal, Context, World, policy revision, target, operation, and expiry.

## D-059 — Three-actor proposal selection enumerates legal subsets

With at most three actor Proposals, the Team Coordinator enumerates at most eight subsets, rejects stale, unauthorized, and conflicting combinations, and selects one through public deterministic control criteria. M3 does not implement a general maximal-independent-set engine or use hidden model judgment.

## D-060 — One Team Tick is one semantic Effect and one Game Dispatch

Action Proposals are cognition records, not independent external Effects. After authority and compatibility selection, the Coordinator forms one semantic Effect to advance one admitted Team Tick and binds it to one MultiActorTickBatch Dispatch. One TickEvent Observation and Verification contain per-Intent receipts that advance actor Tasks independently. No generic EffectGroup is introduced.

## D-061 — M3 Context uses Host token budgets rather than a new fixed byte constant

The 16 KiB contract remains part of frozen M2 compatibility. M3 actor Contexts use required/optional typed Context Blocks, source digests, freshness, priorities, token budgets, and selected/omitted manifests from Ordivon Host semantics. Byte and message limits are measured scenario policy, not universal architecture constants.

## D-062 — Deployment begins with a measured embedded-versus-sidecar choice

The target ownership is an Ordivon Host Team Coordinator workload with a Game World adapter. The first executable slice defaults to a conformance-backed in-process TypeScript adapter unless a local Python Host sidecar experiment proves lower total complexity or a required independent-Host capability. Implementation does not begin before this choice is reviewed.


## D-063 — M3 uses an embedded Host-conformant Team adapter

The first executable Team Coordinator remains inside the TypeScript Game process and shares the existing SQLite deployment. It conforms to Host Event, checked projection, revision, lease, Context, Effect, Dispatch, Observation, and Verification semantics. A Python sidecar was rejected because it would add startup, protocol, packaging, and split-recovery boundaries without supplying a capability required by the three-specialist scenario.

## D-064 — Communication reachability is authoritative gameplay state

A Message is visible to an actor only after the Game delivery graph admits it. Local delivery, unavailable station radio, later delivery, and expiry are persistent Host evidence. The same containment task offer produces an 18-Tick victory when delivered locally and `power_exhausted` when radio delivery arrives too late. Communication is therefore part of strategy and cannot be simulated by a shared transcript.

## D-065 — Provider replacement guarantees continuity, not strategy equivalence

Changing Codex and Hermes mappings preserves Run, Team Goal, actor Tasks, Objective Graph, World and Host journals, Context/Proposal history, and recovery identity. It does not guarantee that the replacement model will choose an equivalent plan or win. M3 records a continuous Codex-to-Hermes trajectory that completes every verified Tick but times out strategically.

## D-066 — Valid live Provider choices are never hidden-corrected

The Team Host may reject malformed, stale, unauthorized, conflicting, or invented identities. It may not replace a valid admitted Action because Fixture or another Provider would choose better. All-Hermes failure and redundant mixed-team sealing/containment remain canonical evidence. Real Provider evaluation measures cognition as delivered, not a policy secretly repaired by the Host.

## D-067 — Resource negotiation remains explicit follow-up work

M3 exposes inventory, Messages, Objectives, Tasks, and waiting state but adds no hidden resource manager or automatic inter-actor transfer. All-Hermes and replacement runs show that one specialist may collect spare parts another needs. M4 should make resource ownership and task negotiation legible to player and Agents before considering a new transfer Command or coordination protocol.

## D-068 — Player control is persistent state separate from Task lifecycle

Pause, resume, and cancellation are explicit Task control modes rather than transient Task-state labels. Context compilation, Provider eligibility, Proposal selection, and Round verification respect the control mode. Pause may resume explicitly; cancellation is irreversible within the Run. Control changes do not advance World time.

## D-069 — Mission Control is a pure bounded projection, not a second truth store

The product derives one `MissionControlView` from authoritative World, Host, Team, Context Artifact, Proposal, TickPlan, and Observation records. Reads must not refresh Messages, transition Tasks, append semantic events, or retain an independent product database. The terminal encoded response is bounded to at most 64 KiB.

## D-070 — Product execution stops at Proposal review and verified Tick boundaries

The player API exposes `proposal-review` before World mutation and `tick-verified` after at most one admitted atomic Team Tick has been observed and verified. Internal Host steps may be folded into these boundaries, but primitive World Commands, raw Effects, and intermediate infrastructure phases are not product controls.

## D-071 — Resolved OR branches are explicit superseded Objectives

An Objective branch not chosen after an alternative satisfies the parent is neither satisfied nor still required. Mission Control marks it `superseded` and counts it as resolved path structure. World predicates and score semantics remain unchanged. This prevents a verified victory from appearing as an incomplete required mission.

## D-072 — The root Web is the player product; raw controls live on an explicit debug surface

The root page exposes deployment, bounded state, semantic evidence, intervention, Proposal review, and verified Tick control. M1 manual Commands, M2 single-Agent controls, M3 raw Team controls, identifiers, receipts, and replay remain available at `/debug.html`. Product simplification does not delete engineering observability.

## D-073 — M4 reuses M3 live Provider evidence

M4 changes durable control, bounded projection, HTTP boundaries, and Web presentation without changing Codex/Hermes cognition contracts or hidden-correcting valid model choices. Live Provider runs are therefore not repeated for M4 closeout; M3 remains the canonical live Provider evaluation. Fixture, persistence, intervention, recovery, and product evidence are re-evaluated directly.


## D-074 — Scenario Cases supersede label-only seed semantics for M5

A release-comparable environment is identified by a deterministic Scenario Case and Genesis specification digest. The legacy seed field remains compatibility metadata until an actual Scenario RNG consumes it. M5 does not add randomness merely to make a seed label appear meaningful.

## D-075 — M5 replay and diagnosis are pure projections over existing evidence

Point-in-time state, Replay Frames, curves, key turns, diagnosis, and comparison derive from existing World Commands, Events, Snapshots, Host/Team records, and Artifacts. M5 adds no replay truth table or analytics database. World revision and Host sequence define authoritative order; wall-clock timestamps are metadata.

## D-076 — Diagnosis uses explicit evidence classes rather than model-generated causality

M5 distinguishes verified direct mechanism, verified contributor, bounded counterfactual sensitivity, and context-only information. Every non-context diagnosis statement references retained evidence. A contributor is not presented as the unique cause, and model prose cannot upgrade an evidence class.

## D-077 — Deployment manifests freeze initial comparison inputs without replacing live Task routing

Every M5 comparison Run records one immutable manifest containing Scenario Case, Genesis digest, loadout, initial Actor Provider mapping, authority policy, coordination profile, and evaluated-input digest. Later Provider changes remain existing Task Events. This supplies experiment provenance without migrating current Host routing ownership.

## D-078 — Ordivon Runtime executes experiment cells but does not become Game state

Game defines Experiment Specs, cell commands, semantic metrics, and result digests. Runtime owns Job/Attempt/process/cancellation/artifact truth. Runtime failures remain executor failures and cannot be converted into fabricated Game mission outcomes. Game adds no Runtime Job tables or embedded Runtime dependency.

## D-079 — First-playable evidence binds evaluated inputs and a release artifact

M5 release claims bind a canonical manifest of executable source, Web, lockfile, Scenario/Ruleset contracts, and release tests. Git commit/tree metadata and GitHub artifact attestations are additional provenance, not the sole identity. This survives squash merges and remains locally verifiable from a clean source release.

## D-080 — One Chromium journey is the browser release gate

M5 adds Playwright as a development-only dependency for one end-to-end deployment → play → terminal → replay → comparison journey. CI uses one worker and one Chromium headless browser with trace retention on failure. This closes M4's browser-evidence gap without creating a broad cross-browser test program.
