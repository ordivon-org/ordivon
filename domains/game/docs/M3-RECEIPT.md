# M3 receipt — multi-Agent team, communication, and authority

## Verdict

Issue #5 is complete after this receipt merges to `main`.

M3 adds a persistent three-specialist team without introducing a manager model, shared transcript, second World authority, distributed sidecar, or general multi-Agent framework. Engineer, Medic, and Security receive actor-scoped Contexts, choose exact admitted Actions through replaceable Providers, produce independent Proposals, and contribute at most one compatible Intent each to one atomic Team Tick. The deterministic World advances environment and mission exactly once, emits one TickEvent with per-Intent receipts, and remains the only state authority.

The same seed now has two deterministic verified victory plans. Communication reachability changes the terminal outcome. Supervised high-risk Actions require an exact single-use Grant. One Provider can fail while unrelated specialists continue. Real all-Codex and mixed Codex/Hermes teams win without hidden correction. All-Hermes and Codex-to-Hermes replacement retain exact continuity and verified effects but fail strategically; those failures remain evidence rather than being overwritten by Fixture policy.

Canonical machine-readable evidence is stored in [`M3-EVALUATION.json`](M3-EVALUATION.json).

## Implemented architecture

```text
Shared Team Goal + Game Objective Graph
        ↓
Engineer Task · Medic Task · Security Task · Coordinator Task
        ↓
actor-local Observation + delivered Messages + visible verified Facts
        ↓
required/optional token-budget Context Blocks
        ↓
replaceable Codex / Hermes / Fixture cognition
        ↓
exact Action Proposal + ABAC Decision + optional Authority Grant
        ↓
exhaustive legal-subset selection for at most three Proposals
        ↓
one Team Tick Effect → one synthetic Dispatch
        ↓
atomic Ruleset-v3 TickBatch
        ↓
one TickEvent Observation with per-Intent Verification
        ↓
independent Actor Task advancement
```

The embedded TypeScript form was selected because Game, Host-conformant projections, and World already share one Node process and SQLite database. A Python Host sidecar would have added startup, protocol, packaging, and split-recovery boundaries without supplying a capability required by the three-specialist scenario.

## Specialists and exclusive capabilities

| Specialist | Exclusive responsibility | Independent state |
|---|---|---|
| Engineer Imani | repair systems, control power, physically seal the breach, transmit distress | actor Task, local Context, Provider Decision, Proposal, authority result, verification |
| Medic Reyes | collect medical supply and stabilize the casualty | actor Task, local Context, Provider Decision, Proposal, verification |
| Security Chen | contain the maintenance hazard | actor Task, local Context, Provider Decision, Proposal, verification |

Provider Sessions do not identify these actors. Goal, Tasks, World Run, Host Journal, Context Artifacts, Proposals, Effects, and Observations retain continuity when a Provider or Host process changes.

## Atomic multi-Actor time

Ruleset v3 admits at most one primitive Intent per actor against one before-state. Compatible mutations are applied canonically, then environment and mission advance once.

The complete batch rejects atomically for:

- stale World revision;
- duplicate Actor or Command identity;
- conflicting writes to one mutable target;
- shared-inventory over-allocation;
- illegal or nested Team Tick input;
- capability or World precondition failure.

One synthetic `team_tick` Command is retained in the existing World Command/Event journal. Retry after response loss queries the stable Command ID and observes the prior result instead of advancing another Tick.

## Automated evidence

```text
159 tests
159 passed
98.69% lines
90.57% branches
98.17% functions
```

The complete suite preserves all frozen M1, M1.5, M2, and M2.1 receipts.

### Interruption recovery

Fresh TeamHost continuation converges at eight persisted boundaries:

```text
after_context_persisted
after_provider_call
after_proposal_persisted
after_tick_plan_persisted
after_dispatch_prepared
after_world_apply
after_observation_persisted
before_task_advance
```

Every run reaches the same deterministic containment victory with exactly 18 World Ticks, 18 Effects, 18 Dispatches, and 18 Observations. The `after_world_apply` case proves response-loss reconciliation without duplicate World mutation.

### Two valid plans on the same seed

| Plan | Specialist controlling breach | Result | Tick | Score | Oxygen | Battery | Terminal digest |
|---|---|---|---:|---:|---:|---:|---|
| Security containment | Security | **victory** | 18 | 2264 | 71 | 8 | `a8ef1f491c35…b09ceb7` |
| Engineer sealing | Engineer | **victory** | 22 | 2255 | 51 | 0 | `0913c9cacb05…66939bf4` |

The second route is not a cosmetic alternative. It costs four additional Ticks, all remaining battery, and health exposure while using Engineer inventory and capability instead of Security containment.

### Communication changes the outcome

The same typed `task-offer` was evaluated under two reachability conditions:

| Channel | Initial delivery | Final result | Tick | Digest |
|---|---|---|---:|---|
| same-room local | `delivered` | **victory** | 18 | `a8ef1f491c35…b09ceb7` |
| station radio while communications are unavailable | `pending`, delivered only after recovery | `power_exhausted` | 20 | `6cdcff809b8d…eb3c8c` |

Security waits without a delivered containment assignment. Local delivery arrives in time; the radio message arrives after the relevant coordination window. Communication is therefore gameplay state, not decorative logging.

### Authority and independent progress

Under `supervised` policy, `seal_hull`, `contain_hazard`, power changes, and distress signalling may return `require-human`. Execution stops when only `wait` Actions could bypass the pending request. An exact Grant binds:

```text
Run + Actor + Proposal + Action candidate + Context
+ World digest + policy revision + operation + target + expiry
```

The Grant is single-use and stale-sensitive. Unrelated productive specialists may continue while another waits. A failed Security Provider leaves Security in a typed Provider wait while Engineer and Medic retain and execute their Proposals.

### Conflict resolution

Engineer sealing and Security containment both write the same hazard target. The Coordinator enumerates every non-empty subset of at most three Proposals, asks the pure Ruleset-v3 reducer whether each subset is legal, and deterministically selects one compatible subset. Exactly one conflicting hazard mutation is verified; input permutation does not change the Tick result.

## Live evaluation

All live runs use source revision:

```text
835c11a25fd27d5fbd9cd1c495a82b8c1e7dd9f3
```

No run loads a prior transcript, Provider Session, hidden Fixture fallback, or manager model. Codex uses an ephemeral read-only workspace. Hermes uses invocation-scoped HOME and HERMES_HOME, selected credentials only, no Toolsets, MCP, Memory, profile, skills, or retained Session.

| Team | Result | Tick | Calls | Failed calls | Score | Reported model cost |
|---|---|---:|---:|---:|---:|---:|
| all Codex | **victory** | 20 | 60 | 0 | 2227 | not reported by Codex CLI |
| Engineer Codex + Medic/Security Hermes | **victory** | 20 | 60 | 0 | 2322 | US$0.48826766 |
| all Hermes | `mission_timeout` | 22 | 66 | 0 | 723 | US$0.85372149 |
| Codex 4 Rounds → all Hermes | `mission_timeout` | 22 | 66 | 1 | 723 | US$0.73676739 |

Every live trajectory completed all retained Rounds. Every admitted Team Effect, Dispatch, Observation, and per-Intent Verification succeeded. Every World replay reproduced the exact terminal digest.

### All Codex

Codex reached verified rescue in 20 Ticks with 60 independently admitted specialist Decisions. It repaired and powered all three systems, stabilized the casualty, contained the breach, and transmitted distress. The final World digest is:

```text
3a223193d4dc569e9b885f3728d7d6500acf409ec8f0a77864f72f7469b775b9
```

Codex reported 1,195,887 input tokens, including 367,616 cached input tokens, and 10,690 output tokens. Its CLI supplied no comparable monetary estimate, so none is inferred.

### Mixed Codex and Hermes

Engineer used Codex while Medic and Security used independent Hermes/DeepSeek calls. The team reached victory in 20 Ticks with 60/60 successful Provider calls. The final digest is:

```text
0c18406fecff7d3835f386baef761064b8ce1347d80ecb24287adaf427dfac2b
```

Hermes reported an aggregate estimated cost of US$0.48826766. The trajectory both contained and sealed the breach, which increased Objective progress but was strategically redundant. The Host did not remove either valid choice through hidden policy.

### All Hermes

All 66 Hermes calls returned structurally valid, current, admitted Action identities. The Host and World behaved correctly, but the team timed out. Hermes repaired and powered cooling, stabilized the casualty, contained and sealed the breach, then failed to obtain and allocate the remaining spare parts needed for life support and communications.

```text
mission_timeout
life support damaged and unpowered
communications damaged and unpowered
22 verified Ticks
replay exact
```

This is a cognition and coordination failure, not an execution failure.

### Codex to Hermes replacement

Codex completed four Rounds. A fresh TeamHost then replaced all three Provider mappings with Hermes while preserving the same:

```text
Run
Team Goal
four Actor/Coordinator Tasks
Objective Graph
World Journal
Host Journal
Context/Proposal history
```

The first replacement state was World revision 4 with digest:

```text
eee837b212112e5af3fa6a43317ad5924985e18f20e1c2137dbf64e5b082790e
```

Hermes continued through revision 22. One Medic output invented an Action identity and was rejected; Engineer and Security still progressed in that Round. Later Security collected spare parts that Engineer needed, while the team had no successful negotiated resource handoff. The mission timed out without duplicate Effects or state loss.

The result proves **Provider replacement continuity**, not Provider strategy equivalence or guaranteed victory.

## Player control surface

M3 exposes bounded synchronous APIs:

```text
GET  /api/team/state
POST /api/team/initialize
POST /api/team/step
POST /api/team/run
POST /api/team/input
```

Typed player inputs include:

```text
approve
deny
send-message
redirect-objective
pause
cancel
```

The browser surface shows the three Actor Tasks, active Objectives, Team Rounds, Proposals, authority state, and approval controls. M2 single-Engineer APIs remain available for old Runs.

## What M3 proves

M3 proves that a thin Host can support a real three-Agent team with:

- persistent identities independent from model Sessions;
- materially different actor knowledge;
- bounded communication whose reachability changes outcomes;
- explicit player authority;
- deterministic conflict resolution;
- atomic multi-Actor physical time;
- failure isolation;
- fresh-process recovery;
- exact replay;
- heterogeneous real Providers.

It does not prove that any model configuration will coordinate scarce resources successfully. The retained Hermes failures show the next useful product problem: explicit resource/task negotiation and player-visible coordination support, not another hidden planner or larger transcript.

## Boundary after M3

M4 owns the player control surface as a product rather than an engineering panel. It should make resource ownership, task offers, waiting causes, authority requests, and Actor-local knowledge legible enough for the player to intervene without reading raw Host records.
