# Agent operating rules

## Objective

Improve the current Station Zero product without recreating deleted historical paths or anticipating a general game platform.

## Current executable

```text
Mission Control
→ Station Zero Team domain
→ Embedded Host authority
→ deterministic Game World
→ SQLite evidence
→ Replay / Diagnosis / Comparison
```

The only supported execution contract is:

```text
station-zero@2
station-zero-core@3
Engineer + Medic + Security
```

The unregistered v3 target is:

```text
station-zero@3
station-zero-core@4
Rescue vs Pirate vs Swarm
```

Its frozen content and pure deterministic reducer live only under `src/station-zero-v3/`, `docs/STATION_ZERO_V3_P0.md`, and `docs/STATION_ZERO_V3_P1.md`. Do not register, persist, serve, or render this target until P2 supplies one durable Turn commitment path, crash recovery, retained Replay, and bounded product projections.

## Hard boundaries

1. The Game World is authoritative for all physical, numerical, temporal, and terminal state.
2. Model output is a Proposal, never a direct mutation or completion claim.
3. Capability, authority, admission, execution, observation, and verification remain distinct.
4. Team state owns Station Zero coordination; embedded Host state owns generic commitment identity.
5. Provider sessions do not own actor identity, task continuity, World state, or replay.
6. Mission Control is a pure bounded projection and owns no second database.
7. Replay, diagnosis, deployment, and comparison derive from retained evidence rather than storing alternative truth.
8. Routine deterministic execution must not require a model call.
9. Hot-path reads use verified heads and local CAS checks; complete stream and Journal verification belongs to recovery, explicit audit, and replay boundaries.
10. Materialized indexes and projections must remain rebuildable from their authority and must be point-validated before use.
11. New permanent structure must own a responsibility the existing owner cannot safely handle locally.
12. Do not restore old Scenario versions, reducers, single-Agent stacks, compatibility APIs, fixtures, milestone documents, or database migrations.
13. The v3 contract is Station Zero-specific. Do not generalize it into a tactical, RPG, roguelite, or simulation platform.
14. A correctly resolved but unsuccessful Intent is not execution or verification failure.
15. Faction knowledge is authoritative gameplay state; projections and Agent Contexts must never read hidden World truth directly.
16. A normal local combat invalidation must not roll back an otherwise valid committed Turn.
17. Every accepted v3 Turn must produce exactly one Resolution per committed Intent and one content-addressed Turn Record.
18. Equivalent Faction Plan or Intent input ordering must produce identical World, Resolution, and Record digests.
19. An uncertain durable Turn must be observed or recovered by its original identity, never retried under a new identity.
20. Do not expose the pure v3 reducer as raw stepping or mutation controls through the product API.

## Working method

```text
identify a current player or World problem
→ locate the sole state owner
→ make the smallest owner-local change
→ test success, rejection, interruption, and replay where relevant
→ verify the browser journey when product behavior changes
→ delete replaced structure
```

## Required change evidence

A meaningful change should state:

- which current responsibility changes;
- which authority owns it;
- what player or execution value it adds;
- its failure and recovery behavior;
- which current-contract test demonstrates it;
- what obsolete structure it replaces or avoids.

## Prohibited shortcuts

- parsing free-form model prose into privileged commands;
- allowing dialogue to alter World state;
- treating provider success as verified task completion;
- retrying an uncertain World effect under a new identity;
- adding a second Task, World, replay, diagnosis, or product authority;
- exposing internal stepping or raw mutation controls through the product API;
- preserving dead paths for historical sentiment;
- adding generic infrastructure before a second materially different world requires it;
- using visual polish to conceal an uninteresting play loop.

## Sources of truth

- `README.md` describes the current executable and repository map.
- `docs/PRODUCT.md` defines the current Station Zero product.
- `docs/ARCHITECTURE.md` defines current ownership and execution boundaries.
- `docs/VISION.md` defines long-horizon direction without authorizing current scope.
- `docs/STATION_ZERO_V3_P0.md` defines the frozen next encounter contract.
- `docs/STATION_ZERO_V3_P1.md` defines the pure deterministic Turn reducer and replay contract.
- GitHub Issues own active work and discussion.
- Git history owns deleted implementation history.
