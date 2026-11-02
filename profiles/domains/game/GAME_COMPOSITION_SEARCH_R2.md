# Game Composition Search — R2

Status: **BRIDGE-DRIVEN / EXPERIMENT SEARCH / NOT PRODUCT SELECTION**
Observed: 2026-09-14

## What changed from R1

R1 created eight evidence-guided candidate graphs from the first mechanism ledger. R2 regenerates the search from the **33 top-game motifs ↔ local evidence bridge**. Every candidate now requires external recurrence, local evidence, a bounded UNKNOWN edge set, and a cheapest falsifier.

| Rank | Candidate | External motifs | Local claims | Unknowns | Cost | Status |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 1 | **cs2-05-persistent-authorship-response Persistent Authorship with Non-Authoritative Response** | 3 | 4 | 2 | `LOW` | `ADMIT_WAVE_A` |
| 2 | **cs2-02-path-dependent-automation Path-Dependent Automation Architecture** | 4 | 4 | 2 | `LOW` | `ADMIT_WAVE_B` |
| 3 | **cs2-01-knowledge-timed-investigation Knowledge-Timed Investigation** | 3 | 5 | 2 | `LOW` | `ADMIT_WAVE_A` |
| 4 | **cs2-03-upstream-random-buildcraft Upstream-Random Buildcraft** | 3 | 2 | 1 | `VERY_LOW` | `ADMIT_WAVE_A` |
| 5 | **cs2-04-failure-attribution-mastery Failure-to-Information Mastery** | 3 | 3 | 2 | `VERY_LOW` | `ADMIT_WAVE_A` |
| 6 | **cs2-06-multiscale-command Multi-Timescale Command with Bounded Information** | 4 | 6 | 2 | `HIGH` | `HOLD_HIGH_COST_REUSE_ONLY` |
| 7 | **cs2-08-rule-growth-inspection Rule-Growth Inspection Under Scarcity** | 3 | 4 | 2 | `LOW` | `ADMIT_WAVE_B` |
| 8 | **cs2-10-conditional-ownership Conditional Ownership / Bank-or-Continue** | 3 | 3 | 2 | `VERY_LOW` | `ADMIT_WAVE_B` |
| 9 | **cs2-09-failure-generates-state Failure Generates Future State** | 3 | 2 | 2 | `VERY_LOW` | `ADMIT_WAVE_B` |
| 10 | **cs2-07-communication-topology Communication Topology as Gameplay** | 2 | 3 | 2 | `MEDIUM` | `ADMIT_WAVE_B` |

## Wave A — execute first

### cs2-03-upstream-random-buildcraft — Upstream-Random Buildcraft

**Motifs:** `m08`, `m04`, `m12`
**Local evidence:** `c03`, `c05`
**Reuse:** `NEW_SYMBOLIC_CARRIER`
**Target:** Randomness changes the decision problem before choice; player decisions, not hidden post-choice rolls, determine most consequence.

**Key UNKNOWN:**
- Does moving randomness from outcome resolution to offer/encounter generation measurably improve attribution and adaptation?

**Cheapest falsifier:** Tiny four-round symbolic draft with matched A/B conditions: random offers/known resolution versus fixed offers/random downstream resolution; identical payoff space.

**Kill if:**
- players report equal or worse attribution in upstream-random condition
- offer randomness overwhelms build intent
- greedy policy performs as well as path-aware policy

### cs2-04-failure-attribution-mastery — Failure-to-Information Mastery

**Motifs:** `m03`, `m11`, `m27`
**Local evidence:** `c08`, `r2-c16`, `r2-c26`
**Reuse:** `REUSE_PGP_A`
**Target:** Failure yields a specific model update, immediate retry tests that update, and optional challenge lets the player escalate difficulty voluntarily.

**Key UNKNOWN:**
- Does explicit causal feedback improve learning beyond fast retry alone?
- Can assist tuning preserve self-attributed mastery rather than converting success into external rescue?

**Cheapest falsifier:** Extend PGP-A with two matched variants: raw instant retry versus retry + one concise causal cue/ghost; add one assist knob that changes timing margin only.

**Kill if:**
- causal cue does not change next-attempt behavior
- assist users cannot explain what skill improved
- harder optional route is solved mainly by route discovery instead of execution

### cs2-01-knowledge-timed-investigation — Knowledge-Timed Investigation

**Motifs:** `m24`, `m06`, `m03`
**Local evidence:** `c01`, `c02`, `c10`, `r2-c23`, `r2-c31`
**Reuse:** `REUSE_PGP_D`
**Target:** Selective evidence acquisition under a bounded cycle creates durable knowledge that changes later routes and decisions.

**Key UNKNOWN:**
- Does a reset/loop structure make retained knowledge feel like progression, or merely force repetitive traversal?
- Does delayed scan information create anticipation and planning, or waiting/friction?

**Cheapest falsifier:** Extend PGP-D: three short cycles, one action/time budget, one delayed scan, a persistent knowledge journal, and zero inventory unlocks.

**Kill if:**
- players repeat traversal without changing their model
- persistent knowledge does not alter a later route/action
- time pressure produces guessing rather than prioritization

### cs2-05-persistent-authorship-response — Persistent Authorship with Non-Authoritative Response

**Motifs:** `m02`, `m05`, `m10`
**Local evidence:** `c06`, `c07`, `r2-c18`, `r2-c28`
**Reuse:** `REUSE_PGP_I`
**Target:** A self-authored artifact persists, receives interpretable response, and is revised without converting the audience into a score function.

**Key UNKNOWN:**
- Does external response deepen the player’s own intent or hijack it into evaluator optimization?
- Does persistence make revisions more meaningful by changing later possibilities?

**Cheapest falsifier:** Extend PGP-I across three rounds: player states intent first, artifact persists, deterministic persona comments qualitatively, revision changes one later affordance.

**Kill if:**
- players revise mainly to satisfy persona
- stated intent disappears after feedback
- persistent state does not change a later creative decision

## Wave B / holds

Wave B contains path-dependent automation, communication topology, rule-growth inspection, failure-generated state and conditional ownership. These are valid, but should not displace cheaper reuse-first falsifiers.

`cs2-06-multiscale-command` remains **HOLD_HIGH_COST_REUSE_ONLY**. Station Zero already provides substantial evidence and a measured administration-burden risk; no greenfield command game is authorized.

## Search law

```text
top-game recurring motif
    + local measured/structural edge
    + <= 2 important UNKNOWN couplings
    + cheapest discriminative carrier
    + explicit kill condition
    = admissible composition experiment
```

A successful falsifier result updates mechanism knowledge. It does **not** select a product.

Machine-readable authority: `game-composition-search-r2.json`. R1 remains frozen.
