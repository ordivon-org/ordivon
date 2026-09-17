# Game Whole-Product Recomposition R1 — 2026-09-18

Status: **R01/R02 SUBSUMED / R03 CONDITIONAL MECHANICAL SURVIVOR / R04 DROP-NO-FIT / productSelected=false / G0=false / Human claims unobserved**

Source Game revision: `084f4043458117071d0d1189d07713e7fec2015b`

Host continuity: `task:game-whole-product-recomposition-r1-20260915`

Machine plan: `standards/game_self_attack_wave_r1.json`

Executable falsifier: `experiments/whole-product-recomposition-r1/run.ts`

Evidence receipt: `experiments/whole-product-recomposition-r1/evidence/recomposition-r1.json`

Run:

```bash
pnpm eval:recomposition:r1
```

## Purpose

This is the first bounded self-attack wave that applies the current Experience Library, Design Counterexample Memory and Counterexample Synthesis back onto Ordivon's own PC01/PC02/PC03 compositions and E01/E02/E03 mechanics.

It does not search for a winner. It asks a cheaper question first:

> Which previously retained mechanics actually add a new causal degree of freedom when recomposed with the current product compositions, and which are already subsumed or no-fit?

Exactly four recomposition probes were frozen before implementation, matching the retained Host frontier. Two extra stress probes expose transfer boundaries but have no elimination authority.

## R01 — PC01 × E01

Disposition: **`SUBSUMED_NO_INTEGRATION`**

E01 proves a bounded mechanical pattern:

```text
initially ambiguous hidden cause
→ one bounded inspection
→ observation separates possible causes
→ corrective action changes
→ cause-specific correction succeeds
```

Current PC01 already proves the same causal signature through its hidden `source/process/route` causes, bounded diagnostics, ambiguous negative observations, positive diagnosis expected-value uplift, and cause-specific architecture choice.

PC01 additionally contains dimensions E01 does not provide:

- persistence / switch cost;
- changing operating context;
- cross-cycle objective revaluation.

Therefore E01's **proven mechanical property** is contained inside PC01's already-tested composition. R01 does not justify another explicit E01 layer merely because E01 independently survived its mechanic wave.

This is mechanical subsumption only. It does not claim E01 is generally useless or forbid future compositions that use a materially different inspection relation.

## R02 — PC03 × E02

Disposition: **`SUBSUMED_NO_INTEGRATION`**

E02 proves that one relational timing rule transfers across spatially distinct routes while a timing-insensitive or memorized absolute schedule does not.

PC03 already proves the stronger bounded carrier needed here:

- the same `late-edge-jump-v1` rule is useful at two distinct physical gaps;
- the same rule is used outbound and return;
- timing-aware execution completes the demanding route;
- timing-insensitive execution fails;
- the successful witness uses the stable rule **4 times**;
- uninformed, timing-insensitive and timing-aware policies run against the same serialized World/rule/control invariant;
- no authoritative knowledge/progression state unlocks the route.

Therefore E02's tested transfer property is already inside PC03's current mechanical evidence and receives **no separate integration** in R1.

## R03 — PC01 + E03

Disposition: **`SURVIVES_MINIMAL_ADDITIVITY_FALSIFIER`**

R03 is the only recomposition in R1 that creates a new bounded decision frontier.

### Frozen coupling

The falsifier does **not** silently treat PC01 as if it already had E03 semantics. It introduces one explicit synthetic coupling:

```text
lagSteps = 1
hidden cause persists across the lag
next operating context is forecastable
execution reward context advances one cycle
current diagnosis observes the persisting current cause
```

Under that coupling, a current-context reactive policy is compared against an anticipatory policy that commits for the next operating context.

### Observed policy changes

Three policy structures change, not merely their scalar expected value:

1. cycle 1 → cycle 2 with previous `process`:
   - reactive: no diagnosis → keep `process`;
   - anticipatory: diagnose `route` → choose `process` or `route` from the observation.
2. cycle 1 → cycle 2 with previous `route`:
   - reactive diagnostic/action mapping differs from the anticipatory diagnostic/action mapping.
3. cycle 2 → cycle 3 with no previous architecture:
   - both inspect `route`, but the ambiguous `OK` branch changes from `process` to `source` under the forecast execution context.

Diagnosis also remains mechanically useful after lag in **7** evaluated state/context cases. Maximum measured lagged diagnosis expected-value uplift is approximately **+5.4** in the current reward units.

### Critical transfer boundary

Current PC01 does **not** contain a cross-cycle hidden-cause transition model. R03 therefore establishes only:

> If a future PC01 integration supplies a legible persistence/transition relation under which the relevant future operating context is forecastable, one-step commitment lag can change optimal diagnosis/commit policy without automatically erasing diagnosis value.

It does **not** establish that this coupling already belongs to PC01, that players will understand it, or that it improves the product.

## R04 — PC02 + E03

Disposition: **`DROP_NO_FIT`**

The attack delayed context feedback across later committed revisions and asked whether E03-style lag can add consequence without breaking PC02's exact source attribution.

Current PC02 already binds every context response to:

- exact `revisionId`;
- exact immutable `artifactDigest`;
- advisory-only context authority.

Both delayed pairs in the current three-revision evidence remain exactly attributable even when observed after a later revision exists. The earlier context digest differs from the newer artifact digest and still names its original source exactly.

PC02 also already proves that rejecting an audience preference does not block progression. Context feedback is therefore non-authoritative for progression.

Under the frozen R04 criterion:

```text
if lag preserves attribution and adds no mechanical consequence → DROP_NO_FIT
if lag gains consequence only by breaking attribution/authority → DROP
```

The first branch is what the current carrier demonstrates. No E03 integration is admitted for PC02 in R1.

## S01 — PC02 intent-axis stress

Boundary: **`INTENT_CURRENTLY_CAUSAL_THROUGH_COMMIT_GATE_NOT_CONTEXT_OR_AFFORDANCE_SEMANTICS`**

Current PC02 does mechanically use intent, but the location of that causality matters:

- intent changes commit admissibility;
- `profile_feedback(profile_id, pieces)` consumes committed geometry, not intent metadata;
- `derive_affordances(pieces)` consumes committed geometry, not intent metadata;
- context evaluation is explicitly tested not to consume intent metadata.

So the current carrier demonstrates a mechanically causal **intent gate**, not yet a broader claim that expressive intent itself changes later context interpretation or artifact-derived affordances.

This is a claim boundary, not a failure verdict. Human authorship, expressive ownership, desire to create and aesthetic value remain unobserved.

## S02 — E03 forecast-model stress

Boundary: **`E03_ANTICIPATION_VALUE_DEPENDS_ON_EXPLOITABLE_TRANSITION_MODEL`**

With the existing E03 lag-1 target dynamics:

| policy/model | recovery cost | misses |
| --- | ---: | ---: |
| perfect transition forecast | 0 | 0 |
| current-state reactive | 8 | 4 |
| wrong-direction forecast | 4 | 2 |
| always-center heuristic | 4 | 2 |

E03 therefore does not support the broad claim `lag → deeper anticipation`. Its bounded property is conditional on a future transition relation that can actually be exploited by the policy.

## Finite R1 standing

```text
R01 PC01 × E01  → SUBSUMED_NO_INTEGRATION
R02 PC03 × E02  → SUBSUMED_NO_INTEGRATION
R03 PC01 + E03  → SURVIVES_MINIMAL_ADDITIVITY_FALSIFIER
R04 PC02 + E03  → DROP_NO_FIT
```

Finite mechanical survivor set:

```text
PC01+E03@R03-coupling
```

This means only that the R03 coupling earned the right to receive the **next bounded playable integration/falsification cost** if the Game owner continues this line. It does not select PC01 as the product.

## Authority / evidence ceiling

```text
productSelected=false
G0=false
Human enjoyment=UNOBSERVED
Human comprehension=UNOBSERVED
Human planning value=UNOBSERVED
retention=UNOBSERVED
market value=UNOBSERVED
Game Core changed=false
```

The repository owns the exact mechanical evidence above. Host owns continuity/task standing. Neither this document nor the Counterexample Synthesis can convert the survivor into product selection or Human evidence.
