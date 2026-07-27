# M2 implementation plan

1. Durable Host Core — independent Host Journal, Goal, Task, Attempt, and Artifact projections.
2. Operation Frontier — bounded observations, strategic candidates, deterministic Skill plans, Context digest.
3. Provider Adapters — fixture, Codex CLI, isolated Hermes CLI, fallback and evidence.
4. Execution Semantics — Effect, Dispatch, Observation, Verification, reconciliation and interruption faults.
5. Control Surface — Agent step/run/pause API, browser timeline, fresh-process continuation.
6. Live Evaluation — Codex, Hermes, provider switching, receipts, latency/token/cost and mission outcomes.

Every PR must preserve the frozen M1 digests and the M1.5 coverage gates.

## PR1 status — implemented

- independent hash-chained Host Journal;
- durable Goal, root Task, Attempt projections;
- content-addressed immutable Host Artifacts;
- one SQLite deployment with separate Host and World authority;
- multi-Run isolation and idempotent initialization;
- fresh HostStore reconstruction and tamper detection.

No Provider is called and no Host operation can mutate the world in PR1.

## PR2 status — implemented

- strategic Operation frontier instead of primitive model actions;
- deterministic path, pickup, repair, power, sealing, medical, signal, and wait Skills;
- projected terminal resource and hazard outcomes for every candidate;
- canonical bounded Agent Context with exact world and task identity;
- Context and Operation staleness admission;
- deterministic Recovery Operation Provider baseline;
- 10 strategic decisions reproduce the frozen 25-Tick victory exactly.

## PR3 status — implemented

- ephemeral read-only Codex CLI adapter with JSON Schema output;
- isolated no-tool/no-memory Hermes CLI adapter with usage accounting;
- strict shared Decision parser and exact Context/Operation copying;
- bounded subprocess execution, timeout, output, and unavailable classification;
- technical-failure Provider Chain with retained attempt evidence;
- fake executable conformance tests for every isolation and failure mode.
