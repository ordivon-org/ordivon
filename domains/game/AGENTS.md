# Agent operating rules

## Objective

Operate Ordivon Game according to owner-current standing without recreating deleted historical paths or anticipating a general game platform. This file is stable repository operating guidance, not current product/research standing, and must not select the next project action by itself. Before choosing immediate work, run `pnpm context:current-direction` to recover the exact current-direction projection for the invoked workspace source, then follow `docs/authority.md` to the current owner when deeper evidence is needed. The projection is not product authority and does not claim canonical Git currentness. If owner-current standing has not been recovered, do not infer it from the registered Station Zero product, the isolated v3 reference target, or historical G-stage labels.

## Current executable

```text
Mission Control
→ Station Zero Team domain
→ Embedded Host authority
→ deterministic Game World
→ SQLite evidence
→ Replay / Diagnosis / Comparison
```

The only registered product contract is:

```text
station-zero@2
station-zero-core@3
Engineer + Medic + Security
```

The isolated v3 preview contract is:

```text
station-zero@3
station-zero-core@4
Rescue vs Pirate vs Swarm
/v3 preview surface
```

Its stable product definition lives in `docs/STATION_ZERO_V3_PRODUCT.md`. Exact content, deterministic reducer, durable SQLite Turn authority, exact receipt/recovery, bounded player/Agent planning, policy expansion, and first-playable browser contracts remain under `src/station-zero-v3/`, `web-v3/`, and `docs/STATION_ZERO_V3_P0.md` through `docs/STATION_ZERO_V3_P3.md`.

The v3 preview is intentionally absent from `src/registry.ts` and uses its own API namespace and database. Do not replace the current root product until repeated playtesting and live-Provider evaluation justify deleting the v2 approval loop.

## Hard boundaries

1. The Game World is authoritative for all physical, numerical, temporal, and terminal state.
2. Model output is a Proposal or Candidate selection, never a direct mutation or completion claim.
3. Capability, authority, admission, execution, observation, and verification remain distinct.
4. Team/faction planning owns coordination. Registered v2 Team paths may use embedded Host commitment evidence; v3 owns exact Planning/Turn Batch/Event/Record identity directly after GC2.
5. Provider sessions do not own actor identity, task continuity, World state, Planning state, or replay.
6. Mission Control and Play views are pure bounded projections and own no second database.
7. Replay, diagnosis, deployment, comparison, and Aftermath derive from retained evidence rather than storing alternative truth.
8. Routine deterministic execution and policy-unit expansion must not require a model call.
9. Hot-path reads use verified heads and local CAS checks; complete stream and Journal verification belongs to recovery, explicit audit, and replay boundaries.
10. Materialized indexes and projections must remain rebuildable from their authority and must be point-validated before use.
11. New permanent structure must own a responsibility the existing owner cannot safely handle locally.
12. Do not restore old Scenario versions, reducers, single-Agent stacks, compatibility APIs, fixtures, milestone documents, or database migrations.
13. The v3 contract is Station Zero-specific. Do not generalize it into a tactical, RPG, roguelite, workflow, or simulation platform.
14. A correctly resolved but unsuccessful Intent is not execution or verification failure.
15. Faction Knowledge is authoritative gameplay state; projections and Agent Contexts must never read hidden World truth directly.
16. A normal local combat invalidation must not roll back an otherwise valid committed Turn.
17. Every accepted v3 Turn must produce exactly one Resolution per committed Intent and one content-addressed Turn Record.
18. Equivalent Faction Plan or Intent input ordering must produce identical World, Resolution, and Record digests.
19. An uncertain durable Turn must be observed or recovered by its original identity, never retried under a new identity.
20. Do not expose the pure v3 reducer as raw stepping or mutation controls through the product API.
21. One Faction may retain only one immutable Plan per Planning Head; replacement requires a new World revision and Planning identity.
22. World Event, Turn Record, World Head, Planning resolution, and Run status must commit atomically.
23. Registered v2 Team work retains its Host authority. Station Zero v3 owns Planning, Turn Batch, World Event, Turn Record, recovery, and Faction Knowledge directly; do not reintroduce a second local Host transcript without a new irreducible continuity need.
24. A new Planning Head must not open while the previous Turn lacks an authoritative World result or Host completion.
25. Historical verification must reconstruct the World at each Planning revision rather than validating old Plans against the latest Head.
26. Player projections must expose enemy state only through retained Rescue Knowledge and visible Fact identities.
27. Commander Orders may change repeatedly only while the P2 Planning Head is open and no durable Faction Plan has been submitted.
28. Editing a Commander Order must invalidate the active Preview reference without changing World state.
29. Generating a Preview must not occupy any immutable P2 Faction Plan slot.
30. A Provider may select only one Candidate already admitted in its exact Context digest; free-form prose never becomes a command.
31. Pirate and Swarm Plan contents must remain sealed in the player projection before Turn resolution.
32. Lower-cost policy Actors expand a leader directive deterministically and do not invoke the full Agent Provider by default.
33. Only the active selected Preview may submit its exact three Faction Plans and cross the explicit Commit boundary.
34. The `/v3` API and database must remain isolated from current `/api/runs`, root Mission Control, and registry identity until replacement is approved.
35. A browser journey is evidence that a loop works, not evidence that it is fun; playtest findings must be allowed to delete or simplify P0–P3 structure.

## Working method

For a **new product before G0**, start from `docs/GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md`: construct a mature comparable reference class, play/teardown it, reproduce the bounded baseline, validate the player-relevant baseline with an appropriate Human method, then test controlled differences. Do not begin from an internally generated GameForm winner.

After G0, locate work in the canonical lifecycle from `docs/DEVELOPMENT_MODEL.md`:

```text
pre-G0: reference → teardown → reproduce → Human baseline → controlled differentiation
G0+: identify the current development stage and false exit gate
→ classify the blocker as gameplay, Agent participation, content, expression, runtime, or production throughput
→ locate the sole owner
→ make the smallest owner-local experiment/change
→ test the relevant success/falsifier/recovery/information boundaries
→ verify real play or real produced artifacts at the stage boundary
→ retain, shrink, or delete the treatment
```

A research series is a search method inside a development stage; it is never the product lifecycle itself.

## Required change evidence

A meaningful change should state:

- which current responsibility changes;
- which authority owns it;
- what player or execution value it adds;
- its failure and recovery behavior;
- which current-contract or first-playable test demonstrates it;
- what obsolete structure it replaces or avoids.

## Prohibited shortcuts

- parsing free-form model prose into privileged commands;
- allowing dialogue to alter World state;
- treating Provider success as verified task completion;
- retrying an uncertain World effect under a new identity;
- adding a second Task, World, replay, diagnosis, Planning, or product authority;
- exposing internal stepping or raw mutation controls through the product API;
- showing enemy Plan details because they exist in the retained Preview;
- submitting Plans as a side effect of GET, rendering, or Preview generation;
- invoking one expensive model call per low-fidelity creature;
- preserving dead paths for historical sentiment;
- adding generic infrastructure before a second materially different world requires it;
- using visual polish to conceal an uninteresting play loop.

## Sources of truth

- `README.md` describes the registered product, v3 preview, and repository map.
- `docs/PRODUCT.md` defines the current Station Zero product.
- `docs/ARCHITECTURE.md` defines current ownership and execution boundaries.
- `docs/VISION.md` defines long-horizon direction without authorizing current scope.
- `docs/GAME_FRONT_HALF_EXTERNAL_REFERENCE_PROFILE.md` owns the product-discovery profile before G0: mature comparable references, teardown, bounded baseline reproduction, Human baseline validation, and controlled differentiation. Its R0–R4 labels are profile steps, not product stages.
- `docs/GAME_R0_SUCCESS_UNIVERSE_20260911.md` owns current R0-A/R0-B success-universe census and archetype coverage. Successful games must be observed before implementation-cost filtering; unlike platform/time-window metrics remain separate.
- `docs/GAME_R0_REFERENCE_STACKS_20260911.md` owns current R0-C and R1 reference-teardown admission. Its wave selects for archetype information coverage; it does not admit clone implementation, product selection or G0.
- `docs/GAME_R1_REFERENCE_TEARDOWN_WAVE1_20260911.md` owns current Wave-1 comparative desk teardown. Observed facts, causal hypotheses, confounds and smallest baselines remain distinct; direct-play experience claims remain pending and the document cannot admit R2 by itself.
- `docs/GAME_R0_EXTERNAL_REFERENCE_CLASS_20260911.md` is the superseded first R0 attempt; its Balatro / Vampire Survivors / Mini Metro set is cheap-baseline support only and has no current authority.
- `docs/DEVELOPMENT_MODEL.md` defines cross-game classification, the Agentic Consequence Loop, development stage gates, and the Game↔Studio production boundary without registering a product.
- `docs/GAME_PRE_G0_DIRECTION_SEARCH.md` retains DS0 candidate/mechanism evidence; its old GameForm↔Agent coupling and search-priority semantics are historical after the decoupling correction.
- `docs/GAME_PRE_G0_DS1_CHEAP_FALSIFIERS.md` owns the first executable structural-falsifier results and their exact claim boundary: simulation may delete weak realizations but cannot prove human Player Value; broad forms are not killed by one failed micro-treatment.
- `docs/GAME_PRE_G0_FORM_AGENT_ROLE_DECOUPLING.md` is supporting anti-Agent-bias/coverage guidance only: GameForm selection remains independent of Agent affinity, but this document no longer selects or prioritizes products ahead of mature comparable references.
- `docs/GAME_PRE_G0_PLAYABLE_PROOF_PORTFOLIO.md` is retained supporting prototype/falsifier apparatus; its historical C0/C1/C2 labels do not replace claim-specific mature Human playtest practice and do not authorize product selection or G0.
- `docs/GAME_PRE_G0_PLAYABLE_WAVE1_APPARATUS.md` owns only the bounded automated A/D/I mechanical apparatus evidence; automation is below C0/C1 human Player Value standing and leaves B/C/E/F/G/H/J untested rather than inferior.
- `docs/GAME_CORE_RESEARCH_RESET.md` reserves G0–G8 for `DEVELOPMENT_MODEL.md` and defines current post-dogfood work as Game Core research rather than product-stage progression.
- `docs/GAME_CORE_DIRECTION_SPACE.md` defines the open Core → Experience direction space and experimental contract.
- `docs/GAME_CORE_EXPERIMENT_FINDINGS.md` owns cross-treatment findings without selecting a product winner.
- `docs/GAME_CORE_EXPERIMENT_CASEFILE.md` retains Casefile as an executable epistemic research treatment, not a G-stage candidate.
- `docs/STATION_ZERO_V3_CONTRACTION.md` records compact Game-local contraction decisions and reopen conditions; cross-project theory is not duplicated into Game authority.
- `docs/STATION_ZERO_V3_PRODUCT.md` preserves the stable unregistered v3 reference target, historical stage evidence, production profile, and replacement boundary.
- `docs/STATION_ZERO_V3_VERTICAL_SLICE.md` preserves the historical production/calibration slice and then-current G4 judgment; it no longer owns current product-stage admission.
- `docs/STATION_ZERO_V3_PRODUCT_VALUE.md` defines G4 comparative product-value evidence, proven/dead control surface, pressure/information findings, and Content Grammar v0; read it before adding player controls or producing a second encounter.
- `docs/STATION_ZERO_V3_P0.md` defines the frozen encounter contract.
- `docs/STATION_ZERO_V3_P1.md` defines the pure deterministic Turn reducer and replay contract.
- `docs/STATION_ZERO_V3_P2.md` defines durable Planning, SQLite Turn execution, exact receipt/recovery, and bounded projection boundaries.
- `docs/STATION_ZERO_V3_P3.md` defines Commander Orders, Agent Context and Candidate admission, sealed Preview, explicit Commit, policy hierarchy, and browser first-playable boundaries.
- GitHub Issues own active work and discussion.
- Git history owns deleted implementation history.
