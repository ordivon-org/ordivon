# Agent operating rules

## Objective

Deliver one small, playable, verifiable Agent mission game. Prefer executable evidence over architectural volume.

## Hard boundaries

1. The Game World Kernel is authoritative for all physical and numerical state.
2. Model output is a proposal, never a direct world mutation.
3. Every important mutation uses a typed action with explicit preconditions and terminal semantics.
4. Observations, beliefs, proposals, Dispatches, and verified Facts remain distinct.
5. Provider sessions do not own Agent identity, mission state, or task continuity.
6. Routine simulation must not require an LLM call.
7. Replay and recovery are designed with the first state transition, not added later.
8. Do not extract a general platform before the vertical slice repeatedly needs it.

## Working method

```text
select the next acceptance criterion
→ build the smallest executable path
→ test success, rejection, interruption, and replay
→ preserve a receipt
→ revise the architecture only from observed evidence
```

## Change discipline

Every meaningful implementation change should identify:

- the milestone and acceptance criterion it advances;
- the authoritative state owner affected;
- new identities or transitions introduced;
- failure and recovery semantics;
- deterministic tests or replay evidence;
- model-cost impact when cognition is involved.

## Prohibited shortcuts

- parsing free-form model prose into privileged commands without a typed admission layer;
- allowing dialogue text to alter world state;
- treating Agent claims as verified outcomes;
- silently retrying uncertain external mutations;
- hiding unexplained failure behind randomness;
- adding many Agents before one Agent can continue correctly after interruption;
- using visual polish to mask an uninteresting deterministic game loop.

## Source of truth

- `docs/PRODUCT.md` owns the first-playable experience and scope.
- `docs/ARCHITECTURE.md` owns component and state boundaries.
- `docs/ROADMAP.md` owns milestone acceptance criteria.
- GitHub Issues own active work, dependencies, and discussion.
- Git commits own implementation history.
