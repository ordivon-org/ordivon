# Autonomous Game Interest R4 — Declarative, Precommitted, No-Live-Human Search

Status: **PRE-GENERATION DRAFT / GENERATION FORBIDDEN UNTIL EXACT FREEZE + INDEPENDENT AUDIT PASS**

Observed: 2026-09-15

## Research question

Can Ordivon autonomously create and select a fresh whole-product game without receiving any live candidate-specific Human quality/fun/preference judgment before build freeze, such that the exact frozen winner later produces non-trivial voluntary continued play in a sealed Human holdout?

R4 deliberately narrows the machine-evaluable product space to finite deterministic discrete-decision games represented as declarative JSON. It does **not** claim that all games fit this substrate. The narrowing is methodological: the game logic becomes data interpreted by one protocol-owned evaluator instead of candidate-authored executable code.

---

# 1. Why R4 exists

R1 terminated because it froze surrogate concepts without freezing enough operational selection law. R2 moved the law into executable reference code, but pre-generation audit still found winner-identification defects before any candidate was generated. R3 then moved candidate logic to a declarative finite-state model and repaired the R2 evaluator defects, but its own pre-generation audit terminated at zero candidate slots because three contracts were still open: `uniqueObservationCount<=256` was measured but not enforced, matched-ablation eligibility trusted an unbound caller `playable` boolean, and the Human-visible renderer/conformance mapping was not frozen as executable bytes. R4 closes those three defects before any generation.

The inherited R2 defect classes included:

- P0 was documented as current-observation-only but the code also used seed/context/time;
- S8 duplicate-action comparison aligned independent per-action arrays instead of co-observed states;
- determinism was sampled rather than guaranteed;
- manifest self-report could steer applicability/complexity;
- declared episode/resource bounds were not mechanically binding;
- software/runtime admission remained partly unspecified;
- matched ablation IDs lacked a mechanical transition-level meaning;
- arbitrary candidate Python could inspect ambient execution context despite self-declared safety fields.

R2 correctly terminated with `0/12` semantic slots consumed. R4 treats those findings as protocol-design evidence only.

---

# 2. Information boundary

Before exact winner + ablation build freeze:

- no live Human candidate preference, fun score, playtest, qualitative steering, screenshot ranking or mechanic ranking may enter generation, implementation, evaluation or selection;
- user-visible progress is aggregate/process only;
- pretrained model priors, public/mature game-design knowledge, the registered 18 mechanism families, 33 motifs and mature engineering patterns are allowed fixed priors;
- automated Agent criticism is allowed but has no taste authority outside the frozen protocol.

After Human unblinding, the same R4 experiment cannot change candidate logic, balance, tutorial, pacing, art or thresholds and remain R4.

---

# 3. Freshness by provenance, not subjective similarity

R4 removes post-generation “looks too similar” rejection from the selection law because that would reintroduce evaluator discretion.

A fresh R4 candidate is instead defined by provenance:

- its authoritative model bytes are first authored **after** the exact R4 protocol freeze;
- exactly three fresh generator occurrences independently own `R4C01`, `R4C02`, `R4C03`;
- before fixing their model, generators may read the frozen R4 protocol, mechanism/motif libraries, public design priors and mature implementation patterns;
- they may **not** read R1 C01–C12 candidate payloads or the PC01/PC02/PC03 whole-product specifications;
- they may not consume candidate-specific Human feedback;
- once a semantic candidate model is fixed, it cannot be replaced after seeing another candidate or evaluation outcome.

R4 does not use semantic similarity to eliminate a candidate after generation. Low-level mature primitive reuse remains allowed.

---

# 4. Search budget and phase structure

R4 intentionally removes the 12→6→3 preimplementation selection layer.

```text
exactly 3 fresh candidate models
        ↓ schema + semantic validity
all valid candidates receive implementation/evaluation budget
        ↓ one frozen evaluator for all three
hard-core surrogates + Anti-Goodhart gates
        ↓ pairwise no-weight tournament
at most 1 autonomous winner
        ↓ mechanical coupling ablation
winner + ablation + renderer freeze
        ↓ sealed Human holdout
```

There is no preimplementation quality ranking, no QD curator and no Human tie-break. A candidate that fails schema/semantic validity is eliminated and not replaced.

---

# 5. Authoritative declarative game model

The normative schema is:

`domains/game/game-autonomous-interest-model-r4.schema.json`

The authoritative gameplay logic is JSON data only. Candidate-specific Python/JavaScript/GDScript is not executed by the automated evaluator.

Each model contains exactly:

- candidate identity and `humanSignalUsed=false`;
- 2–8 action IDs;
- 3–6 causal coupling IDs;
- contexts `0..3`;
- exactly four training initial states/context;
- exactly eight evaluation initial states/context;
- 12–512 total states;
- per-state observation, status and action transitions.

Terminal states have no transitions. Ongoing states have at least one transition. Every reference resolves, every declared action and coupling is actually used, every model state is reachable from the frozen initial-state pools, and training/evaluation initial-state identities are globally disjoint.

Observation complexity is evaluator-measured, not candidate-declared:

- reachable states `<=512`;
- unique observations `<=256`;
- observation JSON nodes `<=64`;
- canonical observation bytes `<=2048`;
- actions `<=8`.

JSON parsing is strict: duplicate object keys and non-standard numeric constants such as `NaN`/`Infinity` are rejected. Canonical JSON uses sorted compact UTF-8 and forbids NaN.

The mature schema validator is frozen as `/root/.local/bin/check-jsonschema`, version `0.38.0`, plus the protocol-owned semantic validator.

---

# 6. Determinism by representation

R4 does not attempt to sample whether candidate logic is deterministic. The candidate model has no executable transition code, RNG callback, network access, wall clock, environment access, policy identity or candidate reward.

For one state and action, the next-state reference is fixed by model bytes. Therefore candidate gameplay determinism is structural rather than inferred from a small probe.

The generic Human renderer later must load the same frozen model. Candidate-specific gameplay logic in the renderer is forbidden; renderer conformance is a final freeze gate.

---

# 7. Frozen policy ensemble

The protocol-owned evaluator is:

`experiments/autonomous-interest-r4/evaluator_reference.py`

Maximum episode length is fixed at `96` decisions for every candidate and is not candidate-declared.

## P0 — VISIBLE_STATE_HASH

P0 is a deterministic stateless baseline. Its action depends **only** on canonical:

`{current observation, current legal-action list}`.

It does not receive state ID, candidate seed, context ID or time step.

## P1 — REACTIVE_Q

Tabular Q-learning state = current visible state.

- epochs `4`;
- alpha `0.25`;
- gamma `0.95`;
- epsilon linear `0.30 → 0.05`;
- ongoing reward `-0.01`;
- WIN `+1`;
- LOSS `-1`.

## P2 — MEMORY_Q

Same learning constants. State = previous visible state + previous action + current visible state.

## P3 — EXACT_GRAPH_BFS

Exact shortest-path-to-WIN search over the complete finite reachable graph, bounded only by the protocol model cap (`<=512` states). It consumes no candidate reward/progress field.

Exploration decisions for P1/P2 are deterministic SHA-256-derived protocol values from fixed episode identities. They are not candidate RNG.

---

# 8. Evaluation data

Each context has four exact training start states and eight exact evaluation start states encoded in the candidate model before evaluation. Train/eval state identities are globally disjoint.

These are a frozen benchmark matrix, not a statistical sample from a claimed Human population. Autonomous selection therefore uses exact benchmark fractions and fixed effect thresholds, not post-hoc confidence intervals or significance choices.

Every candidate receives all scalar families `S1,S2,S3,S4,S5,S6,S7,S9`; manifest self-report cannot remove a difficult family.

---

# 9. Frozen surrogate law

There is no global `fun_score` and no weighted aggregate.

## S1 — Agency / consequence

The evaluator computes an exact future-behaviour bisimulation partition over reachable states using status, observation, legal actions and successor classes.

`S1` = fraction of reachable ongoing states with at least two legal actions whose alternatives lead to at least two distinct future-behaviour classes.

Hard pass: `S1 >= 0.20`.

## S2 — Learnability

`S2 = max(P1 success, P2 success) - P0 success`.

S2 is always recorded for tournament comparison but is not an independent hard-core threshold.

## S3 — Competence gradient

`S3 = P3 success - P0 success`.

Hard pass requires:

- `P3 >= 0.65`;
- `P0 <= 0.75`;
- `S3 >= 0.25`.

## S4 — Information / memory value

`S4 = P2 success - P1 success`.

A diagnostic aliasing metric additionally records observations shared by multiple states whose oracle first actions differ. S4 remains a tournament signal rather than a universal hard threshold.

## S5 — Strategy value over universal action

`S5 = P3 success - best constant-action policy success`.

## S6 — Failure / learning value

`S6 = P2 final-training-epoch success - P2 first-training-epoch success`.

Hard pass requires:

- gain `>=0.15`;
- first-epoch failure rate `>=0.20`.

## S7 — Recontextualization

Train one P1 table per context and cross-evaluate it on all four contexts.

`S7 = mean diagonal success - mean off-diagonal success`.

## S8 — Measured complexity + duplicate-action gate

No candidate reports its own complexity rank.

For every action pair, enumerate the **same reachable states** where both actions are legal. For each such state compare the exact future-behaviour bisimulation class of the two successor states.

If `coObservedCount > 0` and:

`equivalentSuccessors / coObservedCount >= 0.95`

that pair is duplicate and S8 fails.

This is state-keyed co-observation semantics; independent per-action arrays are forbidden.

## S9 — Cross-context robustness

`S9 = minimum P3 success across the four exact evaluation contexts`.

Hard pass: `>=0.50`.

Hard-core candidate eligibility requires independent PASS of `S1,S3,S6,S8,S9`.

---

# 10. Anti-Goodhart law

Tournament admission also requires all of:

- **reward hacking absent by representation** — no candidate reward field;
- **RNG inflation absent by representation** — no gameplay RNG/clock/environment transition input;
- **stalling** — mean same-state transition fraction across P2+P3 evaluation episodes `<=0.25`;
- **dominant universal policy** — best constant-action success `<= P3 success - 0.15`;
- **player-model overfit** — P2 final-training success minus held-out P2 evaluation success `<=0.25`;
- **hidden policy authorization absent by representation** — policy identity does not enter the model interpreter;
- **complexity inflation** — S8 passes;
- **cosmetic consequence** — S1 passes using future-behaviour classes;
- **failure tax** — S6 passes;
- **proxy-bundle gaming** — every hard-core family passes independently.

No strong S2/S4/S5/S7 value can rescue a failed hard-core/Anti-Goodhart gate.

---

# 11. Selection

All schema/semantic-valid R4 candidates are evaluated; there is no QD preselection.

Pairwise comparison uses all scalar families:

`S1,S2,S3,S4,S5,S6,S7,S9`.

Family A is strictly better than B only when `A-B >= 0.05`; strictly worse only when `A-B <= -0.05`.

A defeats B iff:

- A is strictly better on at least two families;
- A is strictly worse on zero families.

Final winner rule among tournament-eligible candidates:

1. minimize pairwise losses;
2. maximize pairwise wins;
3. lowest `SHA256(candidateId)`.

The tie source is the preassigned slot ID only. Caller-supplied candidate/model digests are not accepted as selection inputs. There is no weighted metric sum.

---

# 12. Mechanical matched ablation

Each candidate declares 3–6 coupling IDs. A transition can bind a coupling only by containing:

- normal `next`;
- `couplingId`;
- explicit `withoutCouplingNext`.

Disabling a coupling has one unique interpreter meaning: for **every** transition bound to that coupling, substitute `withoutCouplingNext` for `next`.

Every coupling must affect at least one transition and its normal/fallback targets must differ.

For every winner coupling, retrain P1/P2 and reevaluate the complete surrogate suite **inside that ablated world**. An ablation is eligible only if the exact frozen `ablationEvaluation.policySuccess.P3 >= 0.50`. The selection function accepts only `{couplingId,winnerEvaluation,ablationEvaluation}`, verifies candidate/model digest identity and disabled-coupling binding, and accepts no caller-provided `playable` flag.

Choose the matched ablation by:

1. maximize number of scalar families dropping by `>=0.05`;
2. maximize the sorted descending family-loss vector lexicographically;
3. lowest `SHA256(couplingId)`.

There is no Human or implementer choice of how to remove a coupling.

---

# 13. Frozen software/runtime gate

A candidate model is evaluable only when all exact checks pass:

- `check-jsonschema 0.38.0` schema validation;
- protocol semantic validation;
- all references resolve;
- all states reachable;
- terminal/ongoing transition invariants hold;
- every declared action and coupling is used;
- train/eval initial states globally disjoint;
- measured complexity caps are recomputed and enforced by the semantic validator, including `uniqueObservationCount<=256`;
- reference evaluation completes;
- candidate logic contains no arbitrary executable code.

This is the complete automated game-logic gate for R4; evaluators may not add candidate-specific runtime-quality criteria after generation.

Presentation/renderer defects are handled separately before final Human freeze and cannot alter the selected model logic.

---

# 14. Frozen Human renderer boundary

Automated selection authority is the declarative model only. The Human build is no longer left to a later generic implementation. R4 freezes one exact renderer artifact before candidate generation:

`experiments/autonomous-interest-r4/renderer_reference.py`

Its presentation and session law is fixed:

- it interprets the same frozen model using the protocol evaluator's exact `next_state` semantics;
- observation is shown only as canonical JSON, HTML-escaped, inside one fixed `<pre>` panel;
- legal actions are sorted exactly as the evaluator sorts them and shown as fixed-style buttons labelled by action ID;
- status is the fixed `ONGOING/WIN/LOSS` token;
- CSS, title, headings, terminal copy and `Next round` control are protocol-owned constants;
- candidate-specific CSS, art, media, scripts, gameplay code and external network assets are forbidden;
- each arm has exactly 12 participant ordinals; episode starts come only from the 32 frozen eval starts and advance by stride 13 modulo 32, which visits every eval start exactly once over 32 episodes for each ordinal;
- terminal rounds expose only the fixed `Next round` control; no candidate-specific restart/pacing logic is permitted.

Before final build freeze, `renderer_reference.conformance_report` must enumerate every reachable view and action edge and prove renderer transition equivalence to the evaluator, exact observation/action/status mapping, and the complete 32-start schedule for all 12 within-arm participant ordinals. The exact frozen renderer bytes are the Human-build authority; later candidate-specific presentation work would create a different experiment version.

---

# 15. Sealed Human holdout

Unchanged capability-pilot endpoint:

- N=`24` fresh participants;
- randomized 12 winner / 12 matched ablation;
- identical compensation/instructions;
- mandatory exposure `8` minutes;
- after that, stopping is costless with full compensation;
- optional continuation up to `12` further minutes;
- primary endpoint `VOLUNTARY_CONTINUATION_3M`.

Pilot support requires both:

- at least `8/12` winner participants voluntarily continue >=3 minutes;
- winner exceeds ablation by at least `3` participants on the same endpoint.

No threshold can change after unblinding. Human self-report is explanatory only and cannot override the behavioral endpoint.

---

# 16. Pre-generation audit law

Before any R4 generator occurrence is allowed to create `R4C01–R4C03`, the complete R4 artifacts must be committed and revalidated from a fresh main workspace.

Independent pre-generation auditors must attack at least:

- strict JSON/schema/parser agreement;
- P0 visible-state-only semantics;
- declarative determinism and absence of ambient candidate code authority;
- state-keyed S8 co-observation;
- measured rather than self-declared complexity;
- train/eval separation;
- P1/P2 deterministic learning semantics;
- exact graph BFS;
- ablation retraining and coupling mechanics;
- tournament input closure/tie-breaking;
- protocol/code/prose agreement;
- any two-compliant-evaluator counterexample.

Any protocol-level defect terminates/version R4. It may not be repaired in place after the frozen commit is exposed to candidate generation.

Only unanimous controlling pre-generation PASS may open the three fresh generator occurrences.

---

# Pre-generation standing

```text
R4_PROTOCOL_FROZEN               false   # becomes true only at exact freeze commit
R4_PREGEN_AUDIT_PASSED           false
R4_CANDIDATE_GENERATION_STARTED  false
R4_SEMANTIC_SLOTS_CONSUMED       0
R4_EXACT_FRESH_CANDIDATES        3
PREIMPLEMENTATION_QUALITY_RANKING false
CANDIDATE_LOGIC_EXECUTABLE_CODE  false
LIVE_HUMAN_JUDGMENT_ALLOWED      false
WEIGHTED_GLOBAL_SCORE_ALLOWED    false
PRODUCT_SELECTED                 false
G0_ENTERED                       false
```
