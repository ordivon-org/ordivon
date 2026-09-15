# Autonomous Game Interest R1 — No-Live-Human-Judgment Whole-Product Synthesis

Status: **PROTOCOL FROZEN BEFORE CANDIDATE GENERATION / PRE-G0 / PRODUCT NOT SELECTED**

Observed: 2026-09-15

## Research question

Can the Ordivon game-production system generate, falsify, select, implement and polish a fresh whole-product game candidate **without receiving any live Human quality/fun/preference judgment during development**, such that a later sealed Human holdout shows non-trivial voluntary continued-play behaviour?

This experiment tests the autonomous search-and-selection system, not whether its pretrained models or design priors are free of historical Human influence. Public design literature, pretrained model priors, mature games, Ordivon's mechanism/motif library and mature engineering tools are allowed **priors**. Candidate-specific live Human reactions are forbidden until the final build is frozen.

## Hypotheses

### H1 — autonomous-interest capability

A candidate produced and selected under the frozen no-live-Human protocol will, after immutable build freeze, produce non-trivial voluntary continued play in a sealed fresh-participant holdout and outperform a matched autonomous structural ablation on the same behavioural endpoint.

### H0 — surrogate gap

The frozen automated proxy ensemble is insufficient: the autonomous winner does not meet the voluntary-continuation criterion and/or does not outperform its matched structural ablation.

Either result is useful. H0 identifies a measurable gap between machine-searchable game structure and Human interest.

---

# 1. Information boundary

## Allowed before build freeze

The autonomous development system may consume:

- the registered 18 mechanism families, 33 motifs, historical mechanism/coupling evidence and negative findings;
- public/mature game-design knowledge and literature available before protocol freeze;
- pretrained model priors;
- engine/platform documentation and mature implementation patterns;
- formal models, deterministic simulations, synthetic policies, automated players and runtime telemetry;
- software, physics, reachability, robustness and performance tests;
- independent Agent critiques, destructive reviews and anti-Goodhart analysis;
- historical Human/player research **only as a prior for metric/protocol design**, not candidate-specific feedback.

## Forbidden before build freeze

No candidate-specific live Human signal may enter generation, ranking, revision, balancing, polish or selection. In particular:

- no user preference vote;
- no Human playtest;
- no Human fun/enjoyment/interest score;
- no qualitative comment such as “this one seems fun/boring/confusing”;
- no Human ranking of candidates, screenshots, names, themes or mechanics;
- no adaptation to Human facial/voice/emotional reaction;
- no candidate-specific social/media/reviewer feedback;
- no Human choice of which candidate survives.

LLM/Agent statements such as “this seems fun” have **zero evidential authority** unless grounded in the frozen measurable surrogate contract.

## Candidate concealment from the user

From the first candidate-generation effect until final build freeze, user-visible progress reports may disclose only process-level information such as counts, gate standing, infrastructure failures and protocol adherence. They must not disclose candidate names, themes, concrete mechanics, screenshots, rankings or other candidate-specific details likely to elicit preference feedback.

If candidate-specific Human feedback is accidentally observed before freeze, the affected candidate is `CONTAMINATED` and cannot become the R1 winner.

---

# 2. Freshness / lineage exclusion

PC01 Causal Works, PC02 Persistent Workshop and PC03 Loop Cartographer are **not eligible candidates**. They received prior Human/user steering and are retained only as apparatus/evidence sources.

A fresh R1 candidate is rejected if it is materially isomorphic to one of PC01/PC02/PC03 at the whole-product loop level. Similar low-level mature primitives are allowed; copying the prior product thesis/loop is not.

Lineage audit records for every candidate:

- mechanism graph;
- loop signature;
- primary player promise;
- reused implementation primitives;
- nearest prior Ordivon composition and the material distinction.

---

# 3. Frozen search budget

The R1 autonomous search is bounded before outcome observation:

```text
12 composition specifications
        ↓ hard structural validity + lineage/dedup gate
 6 structural survivors maximum
        ↓ surrogate/QD + destructive falsification
 3 playable microgame implementations maximum
        ↓ embodied/runtime evaluation + anti-Goodhart review
 1 autonomous winner maximum
        ↓ matched causal ablation
 exact winner + ablation build freeze
        ↓
 sealed Human holdout
```

Rules:

- exactly 12 initial composition slots are admitted; a generation failure consumes a slot unless it is a pure infrastructure failure before semantic output;
- at most 6 may enter structural F0 realization;
- at most 3 may receive playable implementation budget;
- no more than one winner proceeds to Human holdout;
- candidate count/budget cannot be increased after seeing proxy outcomes;
- no candidate may be resurrected after elimination except to reconcile an execution/recording ambiguity.

The implementation carrier should prefer existing mature Game apparatus and Godot/web primitives. New infrastructure is not a candidate-quality improvement and receives no search credit.

---

# 4. Evaluation architecture

The automated system does **not** optimize a scalar `fun_score`.

Selection is three-layered:

1. **hard validity gates** — candidate must first be a functioning game-like whole product;
2. **heterogeneous surrogate vector + quality-diversity archive** — preserve qualitatively different good solutions instead of collapsing to one metric;
3. **anti-Goodhart tournament** — attempt to show that apparent proxy strength is degenerate, cosmetic, RNG-driven, complexity-driven or player-model-specific.

No weighted sum of all metrics is permitted.

## 4.1 Hard validity gates

A playable candidate is ineligible if any applicable condition holds:

- no stable action→state→feedback loop;
- required player goal cannot be reached from a pristine state under at least one admissible policy;
- dominant trivial policy solves the intended decision problem across the tested state distribution;
- progress requires hidden evaluator authority not represented in the player-facing rules;
- repeated dead time exceeds the bounded carrier contract without meaningful decision/information/skill work;
- restart/retry is broken or unbounded;
- candidate violates engine/runtime/software quality gates;
- the implementation or evaluator mutates the rules differently for preferred policies;
- whole-product loop is materially isomorphic to excluded PC01/PC02/PC03.

## 4.2 Surrogate families

These are **signals**, not universal hard requirements. A candidate may be strong in different ways, and the QD archive must preserve distinct behavioural niches.

### S1 Agency / consequence

Measure whether materially different admissible actions/policies create distinguishable future state/outcome distributions under matched starting conditions.

Degeneracy attack: cosmetic branching or state differences with no future consequence receive no credit.

### S2 Learnability / model value

Compare frozen policy tiers such as naive/stateless, memory-informed and model-informed agents. Evidence is positive when acquired state/model information improves decisions under the same World rather than changing World authorization.

Degeneracy attack: an answer key or hidden unlock is not learning.

### S3 Competence gradient / retained demand

Test whether different bounded capability/timing/planning tiers separate without making the game either uniformly trivial or uniformly impossible.

Degeneracy attack: difficulty created only by input noise, arbitrary punishment or an evaluator-specific exploit receives no credit.

### S4 Information value / uncertainty reduction

Test whether observations/experiments can reduce decision-relevant uncertainty and alter subsequent policy choice.

Degeneracy attack: surprise/RNG without changed decision value receives no credit.

### S5 Policy / strategy diversity

Estimate non-dominated policy diversity across states/objectives/contexts. The goal is not maximal action entropy; it is multiple contextually defensible behaviours.

Degeneracy attack: random behaviour or equivalent actions do not count as strategy diversity.

### S6 Failure value

Test whether failure can produce actionable information, skill refinement, route/build refinement or altered future policy.

Degeneracy attack: failure that only consumes time receives no positive signal.

### S7 Recontextualization / replay depth

Test whether later contexts can revalue previously learned actions, structures or knowledge without invalidating the underlying rules.

Degeneracy attack: reskinned repetition or random parameter changes without changed decision structure receive no credit.

### S8 Complexity efficiency

Measure useful decision/learning/replay structure per player-facing rule/mechanic/UI burden. This is primarily an anti-bloat pressure.

Degeneracy attack: metric improvements obtained by adding many buttons/resources/states are penalized unless those additions create independently verified decision value.

### S9 Robustness across player models/seeds

A claimed property should survive a frozen small ensemble of distinct policies/seeds where the claim logically permits variation.

Degeneracy attack: a candidate whose quality exists only for the evaluator policy that selected it is fragile and may be eliminated.

---

# 5. Quality-diversity and selection rule

The 6-survivor stage maintains an archive over frozen behavioural descriptors rather than one global score. Descriptor axes are:

- dominant agency mode: spatial / temporal / informational / economic-resource / compositional / social-simulated / mixed;
- dominant improvement carrier: execution skill / world-model knowledge / planning / authored construction / adaptation / mixed;
- consequence horizon: immediate / short-loop / multi-loop;
- failure value: low / information / skill / redesign / mixed.

Within a descriptor cell, replacement uses an ordinal dominance rule:

1. hard validity;
2. fewer surviving anti-Goodhart counterexamples;
3. broader surrogate-family support;
4. lower complexity burden;
5. lower implementation/runtime cost.

Ties are broken by deterministic hash order, never Human preference.

The final 3 playable candidates enter a pairwise **surrogate tournament**. Candidate A defeats B only when A has no new hard failure and is strictly better on at least two surrogate families without being strictly worse on more families, after complexity normalization. Cycles are allowed. If no unique tournament winner exists, select among the non-dominated set by deterministic precommitted hash order. No metric weights may be tuned to force a preferred winner.

---

# 6. Anti-Goodhart contract

A dedicated destroyer must attempt, for every playable candidate, at least the following attacks:

- **reward hacking:** high metric caused by evaluator loophole;
- **complexity inflation:** more state/actions produce higher diversity without more meaningful choice;
- **RNG inflation:** randomness masquerades as replay/strategy diversity;
- **stalling:** long episodes masquerade as engagement/replay depth;
- **dominant universal policy:** one policy collapses nominal choice;
- **policy overfit:** only the selecting agent benefits;
- **hidden authorization:** knowledge/progress flag changes World instead of player understanding/ability;
- **cosmetic consequence:** telemetry divergence without decision consequence;
- **failure tax:** retries consume time without learning/skill/design update;
- **proxy bundle gaming:** candidate is mediocre on every underlying phenomenon but survives through aggregation artifacts.

Any newly discovered proxy exploit becomes a **candidate falsifier for R1**, not a reason to alter the frozen metric suite after observing candidate ranking. A protocol defect that invalidates the experiment may terminate R1, but must not be patched mid-run and continued under the same R1 label.

---

# 7. Matched autonomous ablation

After the autonomous winner is selected and before any Human exposure, generate one matched ablation from the exact winner.

Ablation selection is mechanical:

1. run leave-one-coupling-out sensitivity over the winner's declared causal mechanism graph;
2. identify the single coupling whose removal causes the largest loss across the frozen surrogate vector while preserving basic playability and controls;
3. remove/neutralize that coupling with the smallest implementation delta;
4. preserve visual presentation, controls, session length and unrelated rules as closely as practical;
5. freeze winner and ablation together.

The ablation may not be chosen or edited using Human feedback.

---

# 8. Immutable development freeze

Before Human evaluation, record:

- winner source commit and build digest;
- ablation source commit and build digest;
- full candidate lineage ledger;
- all eliminations and reasons;
- surrogate raw evidence and archive state;
- anti-Goodhart reports;
- exact Human protocol and analysis script;
- protocol digest;
- confirmation that no candidate-specific live Human judgment was consumed.

After freeze, **no gameplay, balance, tutorial, art, pacing or bug change is allowed** under R1. A critical technical defect discovered during Human testing invalidates the affected session; fixing it requires a new R1.x protocol/build and a fresh holdout.

---

# 9. Sealed Human holdout

R1 is a capability pilot, not a population-level publication claim.

## Participants

- `N = 24` fresh participants;
- randomized 1:1: autonomous winner (`n=12`) vs matched autonomous ablation (`n=12`);
- participants must not have seen candidate development artifacts;
- compensation, instructions and maximum session time are identical across arms;
- optional continuation must not affect compensation.

## Session

1. standardized neutral instructions;
2. **8-minute mandatory exposure**;
3. participant is told the required task is finished and they may stop immediately with full compensation;
4. participant may voluntarily continue for up to **12 additional minutes**;
5. no experimenter persuasion or game-specific hints during optional play;
6. short post-play questionnaire/interview occurs only after behavioral endpoint capture.

## Primary behavioral endpoint

`VOLUNTARY_CONTINUATION_3M` = participant continues playing for at least 3 minutes after the mandatory 8-minute exposure when stopping is costless.

### R1 success rule

H1 receives **pilot support** only if both are true:

1. winner arm: at least `8/12` participants meet `VOLUNTARY_CONTINUATION_3M`;
2. winner arm exceeds ablation by at least `3 participants` on the same endpoint (>=25 percentage-point discrete margin at n=12/arm).

Otherwise R1 does not support H1. No threshold may be changed after unblinding.

This is deliberately an effect-size/feasibility criterion, not a null-hypothesis significance claim; R1 is too small for a strong population inference.

## Secondary behavioral endpoints

Recorded without changing the primary decision:

- optional continuation seconds (0–720);
- voluntary new-run/restart count;
- optional-route/content exploration count where applicable;
- retry after voluntary failure;
- time-to-first-voluntary-stop opportunity;
- action/strategy diversity using game-specific frozen telemetry definitions.

## Secondary self-report / explanatory evidence

After behavioral capture only:

- brief competence and autonomy items using a validated game-experience/needs instrument where licensing/wording permits;
- perceived control/intuitive-controls or PXI functional-consequence items where appropriate;
- one neutral open question: what, if anything, made you want to continue or stop?

Self-report explains behavioral results; it does not override the primary endpoint.

---

# 10. Interpretation law

## If H1 receives pilot support

Allowed claim:

> Under the frozen R1 protocol, an autonomous Ordivon composition-and-falsification pipeline that received no live candidate-specific Human quality judgment before build freeze produced a candidate with non-trivial voluntary continued play in a small sealed Human holdout and a positive margin over its matched autonomous ablation.

Forbidden upgrades:

- “AI solved fun”;
- “the game is commercially viable”;
- “the system no longer needs Humans”;
- population-wide retention claims;
- product selection or G0 admission without the separate decision gate.

## If H0 is not rejected / H1 fails

Do not patch the winner and reuse the same holdout. Instead open a new `surrogate-gap` analysis:

- identify which frozen surrogate predictions were strongest;
- identify which Human behavioral/self-report outcomes diverged;
- classify missing dimensions such as meaning, aesthetics, fantasy, pacing, sociality, embodiment, surprise, narrative/context or other unmodeled factors;
- use that gap only to design a future protocol/version, not to retroactively rescue R1.

---

# 11. Execution roles

Once this protocol is committed and Host/Board continuity is available, use independent roles:

- **G01 Composer/Generator** — proposes the 12 fresh composition specs under lineage exclusion;
- **E01 Structural Evaluator** — hard validity, formal/simulation evidence, dedup;
- **E02 Simulated-Player Ensemble** — frozen policy tiers and surrogate telemetry;
- **Q01 Quality-Diversity Curator** — maintains archive using frozen descriptors/rules, no aesthetic authority;
- **D01 Anti-Goodhart Destroyer** — proxy exploitation and degeneracy attacks;
- **I01 Implementation Integrator** — builds only admitted survivors, cannot change evaluation law;
- **A01 Protocol Auditor** — audits information boundary, Human-signal leakage, lineage and threshold drift; cannot choose candidate by taste;
- **F01 Final Freeze Gatekeeper** — verifies exact winner/ablation/protocol/evidence digests before Human unblinding.

All coordination uses Host Task + Board. Agent Birth provides occurrence execution only.

---

# 12. External-method rationale

The protocol deliberately separates automated content/game testing from Human player experience. Recent automated-PCG work demonstrates that autonomous/DRL agents can provide meaningful playability, navigation and generated-content evaluation evidence, but that does not itself establish Human interest or experience. Quality-diversity methods motivate maintaining diverse high-quality solutions across behavioral descriptors instead of optimizing one global objective. For final Human measurement, validated player-experience work supports multi-dimensional constructs such as competence/autonomy while also warning against treating one questionnaire as the whole player experience. Recent continuance research further distinguishes expressed intention from actual continued-play behaviour, motivating a behavioral voluntary-continuation primary endpoint.

References frozen for R1 protocol design:

- Kalafatis et al., *A Modular Framework for Automated Evaluation of Procedural Content Generation in Serious Games With Deep Reinforcement Learning Agents*, IEEE Transactions on Games 17(4), 2025, DOI 10.1109/TG.2025.3589439.
- Kar, *Runtime Evaluation of Procedural Content Generation in an Endless Runner Game Using Autonomous Agents*, arXiv:2605.01783, 2026.
- Gravina et al., *Procedural Content Generation through Quality Diversity*, arXiv:1907.04053, 2019.
- Johnson, Gardner & Perry, *Validation of two game experience scales: PENS and GEQ*, International Journal of Human-Computer Studies 118, 2018, DOI 10.1016/j.ijhcs.2018.05.003.
- Abeele et al., *Development and validation of the Player Experience Inventory*, International Journal of Human-Computer Studies, 2020.
- *Play the game then forever can begin: Designing games to extend gameplay*, International Journal of Information Management, 2025/2026 online record; uses system-captured continued-play data and distinguishes actual gameplay extension from stated continuance intention.

---

# Frozen R1 standing

```text
PROTOCOL_FROZEN              true
CANDIDATE_GENERATION_STARTED false
LIVE_HUMAN_JUDGMENT_ALLOWED  false
INITIAL_CANDIDATES            12
STRUCTURAL_SURVIVORS_MAX       6
PLAYABLE_CANDIDATES_MAX        3
AUTONOMOUS_WINNERS_MAX         1
HUMAN_HOLDOUT_N               24
PRIMARY_ENDPOINT              VOLUNTARY_CONTINUATION_3M
WINNER_SUCCESS_MIN             8/12
MIN_MARGIN_OVER_ABLATION       3 participants
PRODUCT_SELECTED              false
G0_ENTERED                    false
```
