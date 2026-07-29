# Host authority cutover: P3–P6

## Status

Implemented and validated on top of:

- Ordivon Protocol 0.3: `ca5af401eda77d1081487c2df07ce9d94003719e`
- Ordivon Host workload lifecycle: `0cd52c0d7b6b7884fd5e633906c2379a78da9863`
- Ordivon Game P0–P2 baseline: `652abfbe8d034608725cede13b2eb677faba1159`
- Ruleset-v3 recovery fix: `cafd023400c3b2a78e79557677e0eb0ab728719c`
- Game authority implementation: `98508b13a08db1da47b0cbaa8d354b497de81b5f`

This document supersedes the migration architecture in `HOST-CONVERGENCE-P0-P2.md`. The P0–P2 adapters proved semantic mappability; P3–P6 removes them and establishes one production authority.

## Final authority boundary

```text
Agent cognition or Team coordination
→ EmbeddedHostAuthority
→ TaskDescriptor
→ Dispatch
→ Observation
→ VerificationReceipt
→ TaskOutcome

GameWorldExecutor
→ authoritative World Command / Event / Snapshot
```

The generic Host lifecycle is stored only in:

- `host_artifacts`
- `host_journal`

Game owns:

- World state, Ruleset and replay;
- Agent cognition sessions;
- Team actor sessions and leases;
- profiles, Messages, Decisions and Grants;
- Rounds, actor-visible Context references, Proposals and TickPlans.

There is no dual write, compare mode, legacy authority mode, or transcript reconstruction mode.

## P3: implementation decision

A minimal Python JSONL sidecar was implemented and exercised before the authority cutover. It correctly completed one real World Tick, including recovery after a World commit with a lost response. It did not require HTTP, MCP, Python-to-Node callbacks, or a cross-database transaction.

It nevertheless failed the engineering decision gate.

### No-Provider comparison, 20 lifecycles

| Metric | Python stdio sidecar | Embedded TypeScript authority |
|---|---:|---:|
| Startup | 196.120 ms | 36.896 ms |
| Five-stage lifecycle p50 | 259.260 ms | 96.567 ms |
| Five-stage lifecycle p95 | 286.873 ms | 111.843 ms |
| Production lines | 879 | 212 |
| Extra process | yes | no |

Operation p95:

| Operation | Sidecar | Embedded |
|---|---:|---:|
| ensure Task | 43.752 ms | 17.780 ms |
| prepare Effect | 85.182 ms | 30.256 ms |
| record Observation | 60.001 ms | 19.803 ms |
| record Verification | 56.961 ms | 22.535 ms |
| complete Task | 57.102 ms | 24.437 ms |

The sidecar implementation was deleted and never merged. Its result remains negative evidence: reusing the same Python implementation did not compensate for transport, startup, deployment and code-size cost in the in-process Game workload.

## P4: single-Actor authority

The previous `HostExecutionStore` and `SingleActorHostContractAdapter` were deleted.

The Agent path now separates:

- cognition continuity in `game_agent_sessions`;
- Context, Provider Decision and SkillPlan as domain artifacts;
- one authoritative Host workload Task per primitive World Effect;
- World execution in `GameWorldExecutor`.

The frozen deterministic workload remains unchanged:

- 10 admitted Decisions;
- 25 primitive World Effects;
- 25 TaskDescriptors;
- 25 Dispatches;
- 25 Observations;
- 25 VerificationReceipts;
- 25 TaskOutcomes;
- final World revision 25;
- final digest `41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2`.

All retained fault-injection boundaries converge without duplicate World Events or duplicate Host lifecycle stages.

A live Codex run also succeeded after the cutover:

- 10 isolated Provider calls;
- 27 World Effects, Dispatches and Observations;
- 138 Host loop steps;
- final mission `victory`;
- final World revision 27;
- final digest `fa6a3a7f17973cc3dec0bd6b179e94bc03f0ee591e977c545508c831f9fb9439`;
- replay digest equal to the terminal digest;
- 196,371 input tokens, of which 13,056 were cached, and 1,575 output tokens.

The complete temporary Provider transcript was not committed. Its receipt digest was `sha256:415db02ad832bdd9e5f64c3293d48d8bc591b4bacfb63543b099e38b469b5073`.

## P5: Team authority

The previous `TeamHostContractAdapter` and generic Team Host tables were deleted.

One Team Round now owns one authoritative joint Effect lifecycle:

```text
Round + Proposals + TickPlan
→ one Host TaskDescriptor
→ one Dispatch
→ one atomic TickBatch
→ one Observation
→ one VerificationReceipt with per-Actor resultItems
→ one TaskOutcome
```

The frozen Team workload remains unchanged:

- 18 Rounds;
- 54 actor Contexts;
- 54 Proposals;
- 18 joint Effects;
- 18 Dispatches;
- 18 Observations;
- 18 VerificationReceipts;
- 54 per-Actor result items;
- 18 TaskOutcomes;
- zero duplicate Ticks;
- final World revision 18;
- final digest `a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7`.

The final fixture receipt digest was `sha256:24c76b71caab985a2713a65b02368baef84f55d2f2fe3eaf51ddc5a8e6cb6cd6`.

## P6: Mission Control projection

Mission Control now consumes:

```text
Embedded Host authority transcript
+
Game domain sessions / Messages / Authority / Rounds / Proposals / TickPlans
+
World replay
→ MissionControlProjection
```

It does not own or recreate Task, Effect, Dispatch, Observation or Verification truth. Existing HTTP and browser contracts remain stable. Product timelines continue to exclude `host-contract.*` records; protocol transcripts remain independently queryable.

## Deleted authority overlap

The following generic duplicate tables are no longer created:

### Single Actor

- `host_goals`
- `host_tasks`
- `host_attempts`
- `host_effects`
- `host_dispatches`
- `host_observations`

### Team

- `team_goals`
- `team_tasks`
- `team_task_leases`
- `team_context_refs`
- `team_effects`
- `team_dispatches`
- `team_observations`

The migration deletes thirteen duplicate truth tables. `HostStore` is reduced to immutable Artifacts and one hash-chained Journal.

## Retained domain state

Retained state is not a second generic Host:

- `game_agent_sessions` — cognition progress and Provider attempt state;
- `team_actor_sessions`, `team_actor_leases` — actor/coordinator domain sessions;
- `team_profiles`, `team_run_configurations`;
- `team_messages`;
- `team_authority_decisions`, `team_authority_grants`;
- `team_rounds`, `team_round_contexts`, `team_proposals`, `team_tick_plans`.

## Validation

Final local gate:

- TypeScript typecheck: passed;
- browser syntax and product contract checks: passed;
- tests: 213 passed, zero failed;
- line coverage: 98.10%;
- branch coverage: 90.05%;
- function coverage: 98.23%;
- `git diff --check`: passed;
- deterministic single-Actor and Team digests preserved;
- live Codex single-Actor run completed with verified replay;
- Mission Control, Team HTTP, player authority and point-in-time replay tests passed.

Implementation and test diff relative to the P0–P2 Game baseline:

- 1,466 lines added;
- 2,107 lines deleted;
- net 641 lines deleted.

The more important result is structural: thirteen duplicate truth tables, two reconstruction adapters and the duplicate execution store are gone.

## Non-goals

This cutover does not:

- migrate historical databases that already contain removed legacy tables;
- promote Game-specific Action or Tick types into Ordivon Protocol;
- create a generic scheduler, DAG, workflow engine or RPC service;
- make Mission Control an authority store;
- require Python Host deployment for in-process Game execution.

Old databases remain historical evidence. New Runs use the unique authority path.
