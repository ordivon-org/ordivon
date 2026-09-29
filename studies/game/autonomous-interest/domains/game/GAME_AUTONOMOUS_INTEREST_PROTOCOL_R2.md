# Autonomous Game Interest R2 — Operationalized No-Live-Human-Judgment Search

Status: **PRE-GENERATION PROTOCOL FREEZE / GENERATION FORBIDDEN UNTIL INDEPENDENT AUDIT PASS**

Observed: 2026-09-15

## Why R2 exists

R1 correctly terminated after candidate generation because its surrogate families were conceptually frozen but the concrete selection law was not. In particular, policy fixtures, seeds, QD mapping, uncertainty handling, complexity normalization and strict tournament comparison still admitted post-generation evaluator discretion.

R2 is intentionally narrower and more mechanical. It asks the same capability question, but only inside a deterministic finite discrete-decision game substrate for which the evaluator can be made executable **before any candidate exists**. R2 does not claim to cover every game genre.

The research question remains:

> Can Ordivon generate, falsify, implement and select a fresh whole-product game without any live candidate-specific Human quality/fun/preference judgment before build freeze, such that a later sealed Human holdout shows non-trivial voluntary continued play?

---

# 1. Information and lineage boundary

Before exact build freeze, candidate-specific Human judgment remains forbidden. The user may receive aggregate process information only; candidate names, themes, mechanics, screenshots and rankings remain concealed.

Allowed fixed priors include pretrained models, public design knowledge, the 18 mechanism families, 33 motifs, mature engineering tools and historical non-candidate-specific player research.

Forbidden candidate lineages:

- PC01 Causal Works;
- PC02 Persistent Workshop;
- PC03 Loop Cartographer;
- all R1 C01-C12 semantic candidates.

R2 uses a controlled loop-verb vocabulary. Candidate loop similarity is computed by the frozen cyclic-Levenshtein reference implementation. Similarity `>= 0.75` to any excluded frozen signature is a lineage hard kill. Pairwise R2 candidate similarity `>= 0.80` is a dedup collision; the lower canonical candidate-spec SHA-256 survives and the other is eliminated. No reviewer may reinterpret synonyms after generation.

Low-level implementation primitives may be reused.

---

# 2. Search budget

```text
12 fresh R2 composition slots
       ↓ manifest/schema + lineage + hard structural gate
≤ 6 structural survivors
       ↓ frozen QD-diversity subset rule
≤ 3 playable implementations
       ↓ frozen executable policies/surrogates/Anti-Goodhart
≤ 1 autonomous winner
       ↓ frozen leave-one-coupling-out ablation
winner + ablation exact freeze
       ↓
sealed Human holdout
```

No slot expansion, resurrection or replacement after semantic elimination. Pure infrastructure failure before semantic output does not consume a slot.

R1 candidates do not count as R2 slots and cannot be resurrected.

---

# 3. Candidate adapter contract

Every playable R2 candidate must expose the same deterministic adapter. Candidate-specific evaluator code is forbidden.

The normative schema is:

`domains/game/game-autonomous-interest-candidate-r2.schema.json`

The normative evaluator is:

`experiments/autonomous-interest-r2/evaluator_reference.py`

A candidate module exports:

- `MANIFEST`;
- `create_game(seed:int, context:int)`.

The returned game exposes:

- `observe()` — policy-visible canonical JSON state;
- `full_state()` — evaluator-only complete canonical JSON state;
- `legal_actions()` — action IDs from the manifest;
- `step(action)` — deterministic transition;
- `status()` — exactly `ONGOING`, `WIN` or `LOSS`;
- `clone()` — exact deterministic state clone.

The evaluator never reads a candidate reward. It never passes policy identity to the game. It never allows network or wall-clock state to affect gameplay evidence.

R2 candidates have exactly four contexts, 2–8 discrete actions, at most 96 decisions per episode and at most 50,000 reachable states per seed. This is a deliberate experimental scope restriction, not a general definition of a game.

---

# 4. Frozen seed matrix

Seeds are not chosen by evaluators.

For candidate slot, split, context and sample index:

```text
seed = UINT31_NONZERO(
  FIRST8_BE(
    SHA256_UTF8(
      "ordivon-autonomous-interest-r2-20260915-seed-v1"
      + "|" + candidateId
      + "|" + split
      + "|" + context
      + "|" + sampleIndex
    )
  )
)
```

Per candidate:

- 4 contexts;
- 8 training seeds/context = 32 training seeds;
- 24 evaluation seeds/context = 96 evaluation seeds;
- train/eval overlap forbidden.

R2 treats this fixed evaluation matrix as a **benchmark census**, not a population sample. No confidence interval, bootstrap or post-hoc significance threshold is used for autonomous selection. Human generalization is tested only by the later sealed holdout.

---

# 5. Frozen policy ensemble

All constants and algorithms are implemented in the normative evaluator.

## P0 — HASH_STATELESS

Current-observation-only deterministic hash action baseline. No learning and no memory.

## P1 — REACTIVE_Q

Tabular Q learner keyed only by current observation.

- 4 training epochs;
- alpha `0.25`;
- gamma `0.95`;
- epsilon linear `0.30 → 0.05`;
- ongoing reward `-0.01`;
- win `+1`;
- loss `-1`;
- action ties use manifest order.

## P2 — MEMORY_Q

Same training constants as P1, but state key is:

`previous observation + previous action + current observation`.

## P3 — ORACLE_BFS

Evaluator-only model-informed upper bound using `full_state()`/`clone()`.

- shortest-win objective only;
- depth cap `24`;
- node cap `50,000`;
- no candidate progress metric or reward;
- if no plan exists inside the frozen bound, choose the first legal manifest action.

No evaluator may substitute another policy after candidate visibility.

---

# 6. Surrogate law

There is no global `fun_score` and no weighted aggregate.

Universal required families are `S1, S3, S6, S8, S9`.

Additional applicability is deterministic from the manifest descriptors:

- `S2` unless improvement carrier is `execution-skill`;
- `S4` for informational, social-simulated or mixed agency;
- `S5` for economic-resource/compositional/social-simulated/mixed agency, or planning/authored-construction/adaptation/mixed improvement carrier;
- `S7` for `multi-loop` horizon.

A required family failing its threshold makes the candidate ineligible. No success on one family can rescue failure on another.

## S1 Agency / consequence

Score = fraction of sampled states with at least two legal actions where alternative one-step choices change terminal class, reachable-win status or oracle distance by at least two decisions.

PASS: `>= 0.20`.

## S2 Learnability / model value

Score = `max(P1 success, P2 success) - P0 success`.

PASS: `>= 0.15`.

## S3 Competence gradient / retained demand

Score = `P3 success - P0 success`.

PASS requires all:

- P3 `>= 0.65`;
- P0 `<= 0.75`;
- gap `>= 0.25`.

## S4 Information value

Score = `P2 memory success - P1 reactive success`.

PASS requires:

- delta `>= 0.10`;
- decision-relevant observation-aliasing rate `>= 0.10`.

## S5 Strategy diversity

Score = `P3 success - best constant-action policy success`.

PASS requires:

- gap `>= 0.15`;
- at least two distinct oracle first actions across frozen evaluation contexts/seeds.

## S6 Failure value

Score = `P2 final training epoch success - P2 first training epoch success`.

PASS requires:

- gain `>= 0.15`;
- first-epoch failure rate `>= 0.20`.

## S7 Recontextualization

Train one P1 table per context, then cross-evaluate all contexts.

Score = mean diagonal success minus mean off-diagonal success.

PASS requires:

- transfer penalty `>= 0.10`;
- at least two distinct context modal oracle first actions.

## S8 Complexity efficiency

No scalar score. Hard caps:

- actions `<= 8`;
- observation fields `<= 12`;
- player-facing rules `<= 12`;
- UI modes `<= 4`;
- episode decisions `<= 96`.

An action pair that produces the same successor signature on `>= 0.95` of co-observed samples is a duplicate-action failure.

## S9 Robustness

Split the 24 evaluation seeds/context into four fixed groups of six.

Score = minimum P3 success over all `4 contexts × 4 groups`.

PASS: `>= 0.50`.

---

# 7. Anti-Goodhart law

All applicable checks must pass independently:

1. **reward hacking** — candidate reward is absent from evaluator utility;
2. **complexity inflation** — S8 caps and duplicate-action test;
3. **RNG inflation** — exact same seed/context/action script must reproduce the same full-state/status trace;
4. **stalling** — mean unchanged-transition fraction across P2/P3 evaluation episodes `<= 0.25`;
5. **dominant universal policy** — best constant-action success must be at least `0.15` below P3;
6. **player-model overfit** — P2 final-train success minus P2 evaluation success `<= 0.25`;
7. **hidden authorization** — policy identity is not in the adapter and `policyIdentityVisible=false`;
8. **cosmetic consequence** — S1 passes;
9. **failure tax** — S6 passes;
10. **proxy-bundle gaming** — every required surrogate passes independently.

A defect in these laws after protocol freeze terminates R2 and requires a successor version. It is never repaired after candidate visibility.

---

# 8. Quality-diversity allocation before playables

QD descriptors are **candidate-declared exact enum fields**, not inferred by a reviewer:

- agency mode;
- improvement carrier;
- consequence horizon;
- failure value.

If more than six candidates survive hard structural gates, or if more than three structural survivors remain before implementation, the normative `choose_diverse_subset` function enumerates all fixed-size subsets and applies, in order:

1. maximize the sorted pairwise 4-axis Hamming-distance profile;
2. maximize fixed-axis unique coverage tuple `[agency, carrier, horizon, failure]`;
3. minimize declared carrier cost with `web-ts=0`, `godot-2d=1`;
4. deterministic subset hash.

There is no post-generation descriptor mapping and no Human/Q01 taste authority.

---

# 9. Playable tournament

A candidate enters the tournament only if:

- all required surrogate families pass;
- all Anti-Goodhart checks pass;
- software/runtime quality gates pass.

For a pair A/B, compare the intersection of applicable scalar families among `S1,S2,S3,S4,S5,S6,S7,S9`.

A family is strictly better only for score difference `>= 0.05`.

A defeats B only when:

- A is strictly better on at least two common families;
- A is strictly worse on zero common families.

Winner selection is exact:

1. minimize pairwise losses;
2. maximize wins;
3. minimize lexicographic complexity vector `[actions, observation fields, player-facing rules, UI modes, episode decisions]`;
4. lowest `SHA256(candidateSpecDigest)`.

No metric weights and no Human tie-break.

---

# 10. Matched autonomous ablation

Before Human exposure, the winner's manifest already contains 3–6 causal coupling IDs.

For every coupling, construct the smallest leave-one-coupling-out ablation and run the same frozen evaluator. Only ablations retaining P3 playability `>= 0.50` are eligible.

Choose the ablation by:

1. largest count of tournament scalar families falling by `>= 0.05`;
2. largest lexicographically sorted descending loss vector;
3. lowest `SHA256(couplingId)`.

No Human feedback may select the ablation.

---

# 11. Final sealed Human holdout

The R1 holdout contract is retained unchanged:

- `N=24`, randomized 12 winner / 12 matched ablation;
- 8-minute mandatory exposure;
- stopping then becomes costless with full compensation;
- optional play up to 12 further minutes;
- primary endpoint `VOLUNTARY_CONTINUATION_3M`;
- pilot support requires at least `8/12` winner participants to continue >=3 minutes and a winner-minus-ablation margin of at least 3 participants.

Human outcomes are unavailable until exact winner + ablation + protocol + analysis freeze. After unblinding, R2 cannot modify the build and still claim the same experiment.

---

# 12. Protocol reference artifacts

Normative machine authority:

- `game-autonomous-interest-protocol-r2.json`;
- `game-autonomous-interest-candidate-r2.schema.json`;
- `experiments/autonomous-interest-r2/selection_reference.py`;
- `experiments/autonomous-interest-r2/evaluator_reference.py`;
- `experiments/autonomous-interest-r2/protocol_selftest.py`.

`selftest_adapter.py` is infrastructure-only and uses reserved non-candidate identity `R2SELFTEST`; it consumes no semantic candidate slot and may never enter ranking/archive/tournament evidence.

Before R2 generation, independent Agents must attack the exact frozen commit for:

- evaluator degrees of freedom;
- seed/policy ambiguity;
- QD/tournament ambiguity;
- hidden reward/authorization channels;
- ability to produce contradictory selections from identical candidate evidence;
- protocol/code disagreement.

Only unanimous protocol-level PASS is sufficient to open fresh generation. Any protocol-level defect terminates R2 and requires another version.

---

# Frozen pre-generation standing

```text
R1_REUSED_AS_CANDIDATE_EVIDENCE  false
R2_PROTOCOL_FROZEN               true
R2_PREGEN_AUDIT_PASSED           false
R2_CANDIDATE_GENERATION_STARTED  false
R2_SEMANTIC_SLOTS_CONSUMED       0
INITIAL_CANDIDATES               12
STRUCTURAL_SURVIVORS_MAX          6
PLAYABLE_CANDIDATES_MAX           3
AUTONOMOUS_WINNERS_MAX            1
LIVE_HUMAN_JUDGMENT_ALLOWED      false
WEIGHTED_GLOBAL_SCORE_ALLOWED    false
PRODUCT_SELECTED                 false
G0_ENTERED                       false
```
