# M2 receipt — persistent single-Agent Host vertical path

## Verdict

M2 is complete against Issue #4 acceptance.

The Engineer now owns durable Goal, Task, Attempt, Context, Decision, Effect, Dispatch, Observation, Verification, and Fact continuity. Codex and Hermes are replaceable cognition providers; neither provider session is the Agent identity or replay source.

The deterministic Fixture baseline wins. Three real-provider evaluations did not win, but they proved that invalid strategy cannot corrupt world authority: every admitted decision remained inside the exact Operation frontier, every world mutation was independently verified, every Dispatch was unique, and every terminal state replayed exactly.

## Merged implementation

| PR | Boundary | Status |
|---|---|---|
| #15 | durable Goal, Task, Attempt, Artifact, Host Journal | merged |
| #16 | strategic Operation frontier, deterministic Skills, bounded Context | merged |
| #17 | isolated Codex and Hermes adapters, technical fallback | merged |
| #18 | durable Effect, Dispatch, Observation, reconciliation | merged |
| #19 | Agent API and browser control surface | merged |

The evaluation harness and this receipt are finalized in the M2 closeout PR.

## Formal acceptance

| Issue #4 criterion | Receipt |
|---|---|
| durable Goal and Task state | SQLite projections plus independent hash-chained Host Journal |
| bounded observations and Context | canonical Context, maximum 16 KiB, exact Run/Task/world identity |
| structured candidate decisions | Provider returns one exact admitted strategic Operation ID |
| freshness and identity admission | wrong Context, stale world, or invented Operation fails closed |
| Effect → Dispatch → Observation → Verification | persisted per primitive Skill step |
| interruption recovery and provider fallback | seven injected interruption boundaries; technical-only Provider Chain |
| Agent cannot invent world objects/actions | model never emits WorldCommand or object mutation |
| repairs independently verified | Attempt advances only from World Journal Facts and Verification |
| fresh process can continue | all interruption tests converge to one effect history |

## Automated evidence

The deterministic baseline produces:

```text
10 Provider Decisions
10 succeeded Attempts
25 Effects
25 Dispatches
25 Observations
25 verified World Events
victory: rescue_signal_verified
turn: 25
digest: 41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2
```

Seven failure points were injected across Context persistence, Provider return, Decision persistence, Dispatch preparation, World commit, Observation persistence, and Attempt advancement. Every fresh Host process converged without duplicate world effects.

## Live evaluation

Canonical results are stored in [`M2-EVALUATION.json`](M2-EVALUATION.json).

| Run | Provider calls | Effects | Result | Score | Max Context |
|---|---:|---:|---|---:|---:|
| Codex | 13 | 27 | `power_exhausted`, turn 27 | 989 | 11,654 B |
| Hermes / DeepSeek | 6 | 10 | `reactor_meltdown`, turn 10 | 735 | 10,554 B |
| Codex → Hermes | 14 | 28 | `engineer_incapacitated`, turn 28 | 979 | 11,594 B |

Across all three runs:

- every provider response satisfied the strict structured contract;
- every selected Operation belonged to the exact current frontier;
- no human correction or hidden Fixture fallback occurred;
- all Effects, Dispatches, Observations, and World Events had equal counts;
- every terminal World digest matched full verification replay;
- Codex → Hermes continued after five completed Attempts without transferring transcript, memory, Tool history, or session state.

Hermes reported an estimated USD 0.0758118 for the Hermes-only run and USD 0.11519902 for the Hermes portion of the switched run. Codex CLI did not expose a comparable monetary estimate, so no cost is inferred.

## Strategy finding

The models generally reached a nearly recoverable state, then optimized for one more non-terminal Tick rather than the terminal Goal. The symmetric power-toggle frontier allowed them to regress completed objectives:

```text
communications repaired and powered
→ communications disabled
→ cooling disabled
→ life support disabled
→ wait
→ terminal failure
```

This is a policy/representation result, not a Host correctness failure. It is tracked in Issue #20. The next investigation should expose Goal-progress delta, prerequisite edges, reversal cost, irreversible risk, and bounded plan commitment without adding a hidden scripted oracle.

## Boundary after M2

M2 proves:

```text
persistent Agent identity
+ replaceable cognition
+ exact action admission
+ deterministic execution
+ idempotent Dispatch
+ independent Verification
+ replayable evidence
+ fresh-process continuation
```

M2 does not prove that a general model will reliably solve Station Zero. That remains an explicit measured problem rather than an implicit Host promise.
