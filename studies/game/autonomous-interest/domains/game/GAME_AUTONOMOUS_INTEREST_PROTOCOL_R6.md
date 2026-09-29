# Autonomous Game Interest R6 — Closed Evidence, Neutral Presentation, Executable Human Holdout

Status: **PRE-GENERATION DRAFT / GENERATION FORBIDDEN UNTIL EXACT FREEZE + UNANIMOUS INDEPENDENT PRE-GENERATION AUDIT PASS**

Observed: 2026-09-15

## Research question

Can Ordivon autonomously create and select a fresh finite deterministic whole-product game, without any live candidate-specific Human quality/fun/preference judgment before build freeze, such that the exact autonomously selected winner later causes non-trivial voluntary continued play in a sealed Human holdout relative to a mechanically selected matched ablation?

R6 deliberately restricts the experiment to finite deterministic discrete-decision games represented as declarative JSON. This is a methodological restriction, not a claim about all games. Candidate gameplay is data interpreted by protocol-owned reference code; candidate-authored executable gameplay code is forbidden.

---

# 1. Why R6 exists

The protocol is versioned whenever a pre-generation audit exposes a winner/build/endpoint identification defect. No frozen version is repaired in place.

- **R1** froze concepts but not enough executable selection law.
- **R2** moved selection into executable references but pre-generation audit found P0 hidden inputs, state-misaligned duplicate-action detection, self-report authority, weak determinism/resource closure, ambiguous ablation and arbitrary candidate-code channels.
- **R3** moved gameplay to declarative finite-state data, but audit found an unenforced `uniqueObservationCount<=256` cap, caller-controlled matched-ablation eligibility and an unfrozen Human renderer.
- **R4** enforced measured caps, froze a renderer and tightened ablation fields, but terminated at zero candidate slots for three further reasons:
  1. candidate-controlled observation strings and action IDs were rendered verbatim, so a compliant candidate could directly tell Humans to “continue playing for at least 3 minutes,” attacking `VOLUNTARY_CONTINUATION_3M` without improving gameplay;
  2. selection still accepted caller-created score/P3 mappings rather than deriving all evidence from exact model bytes itself;
  3. renderer/build and Human-study execution were not fully closed: an unknown coupling could silently produce the winner world and no exact study runner bound assignment, exposure, stopping and continuation measurement.

R5 closed those channels but was itself terminated at zero candidate slots by post-freeze/pre-generation destroyers: (1) visible+focused heartbeat continuity alone could satisfy `VOLUNTARY_CONTINUATION_3M` with zero gameplay actions; (2) caller model ordering changed tournament/manifest evidence; and (3) candidate slot identity entered P1/P2 exploration RNG and could change S6/pairwise edges. R6 closes all three before any candidate exists. R1–R5 consumed zero R6 semantic candidate slots.

---

# 2. Information boundary

Before exact winner + matched-ablation build-manifest freeze:

- no live Human candidate preference, fun score, qualitative steering, screenshot ranking, mechanic ranking or playtest may enter generation, evaluation or selection;
- candidate-specific user-visible progress is forbidden; process/aggregate progress is allowed;
- pretrained model priors, public/mature game-design knowledge, the registered 18 mechanism families, 33 motifs and mature engineering patterns are fixed allowed priors;
- automated Agent criticism is allowed only under the frozen protocol and has no Human-taste authority.

After Human unblinding, changing model logic, renderer, study runner, thresholds, assignment, presentation, timing or selected coupling creates a different experiment version.

---

# 3. Freshness and search budget

Freshness is provenance-defined rather than subjectively adjudicated after generation.

Exactly three fresh generator occurrences may eventually own `R6C01`, `R6C02`, `R6C03`. They may start only after exact R6 freeze + unanimous controlling pre-generation PASS. They may read the R6 protocol, mechanism/motif libraries, public design priors and mature implementation patterns. They may not read R1 candidate payloads or the PC01/PC02/PC03 whole-product specifications, and may not consume candidate-specific live Human feedback.

Once a generator fixes its semantic model, it cannot replace that model after seeing another candidate or any evaluation outcome. A schema/semantic-invalid candidate is eliminated and not replaced.

```text
exactly 3 fresh candidate models
        ↓ strict schema + semantic validity
all valid candidates evaluated by frozen evaluator
        ↓ hard-core + Anti-Goodhart gates
frozen selector derives all evidence from model bytes
        ↓ pairwise no-weight tournament
at most 1 autonomous winner
        ↓ selector internally evaluates every declared coupling
mechanically selected matched ablation
        ↓ authoritative build manifest recomputation
winner + ablation + source/build digests frozen
        ↓ same frozen renderer + same frozen study runner
sealed 24-person Human holdout
```

There is no preimplementation quality rank, QD curator, weighted global score or Human tie-break.

---

# 4. Authoritative declarative model

Normative schema:

`domains/game/game-autonomous-interest-model-r6.schema.json`

Each model contains exactly:

- candidate identity and `humanSignalUsed=false`;
- 2–8 internal action IDs, fixed as the exact canonical prefix `a0..a(N-1)`;
- 3–6 internal causal-coupling IDs, fixed as the exact canonical prefix `c0..c(N-1)`;
- contexts `0..3`;
- four training initial states/context;
- eight evaluation initial states/context;
- 12–512 states;
- per-state neutral observation, status and transitions.

Terminal states have no transitions; ongoing states have at least one. Every reference resolves, every action/coupling is used, every state is reachable from the frozen initial pools, and train/eval initial-state identities are globally disjoint.

## 4.1 Neutral observation law

Candidate-controlled Human-visible text capacity is removed from the observation representation.

Every state observation is **exactly 12 integers**, each in `[0,15]`:

```text
[v0,v1,...,v11] where each vi ∈ {0,...,15}
```

Candidate strings, candidate-selected observation field names, Unicode text, HTML, labels or free-form JSON objects are invalid. Semantic validation independently rechecks this even after schema validation. Action/coupling names are not a candidate degree of freedom: non-canonical IDs are rejected. State IDs remain internal references only and are never Human-visible or evaluation-order authority.

Measured hard caps are recomputed and enforced by the semantic validator:

- actions `<=8`;
- reachable states `<=512`;
- unique observations `<=256`;
- observation JSON nodes `<=13`;
- canonical observation bytes `<=64`.

JSON parsing is strict: duplicate object keys and `NaN/Infinity` are rejected. Schema validation uses `/root/.local/bin/check-jsonschema`, exact version `0.38.0`, plus the protocol semantic validator.

---

# 5. Determinism and frozen policy ensemble

Candidate transitions contain no executable callback, RNG, wall-clock, environment, network or policy-identity input. One state/action pair has exactly one model-defined successor (or the mechanically defined coupling fallback under ablation).

Reference evaluator:

`experiments/autonomous-interest-r6/evaluator_reference.py`

Maximum episode length: `96` decisions.

- **P0 VISIBLE_STATE_HASH**: deterministic stateless action from canonical `{current observation,current legal actions}` only; no hidden state ID, seed, context or time.
- **P1 REACTIVE_Q**: tabular Q-learning, visible state; epochs `4`, alpha `0.25`, gamma `0.95`, epsilon `0.30→0.05`.
- **P2 MEMORY_Q**: same constants; state = previous visible state + previous action + current visible state.
- **P3 EXACT_GRAPH_BFS**: exact shortest path to WIN over all reachable states.

P1/P2 exploration is SHA-256-derived protocol determinism, not candidate RNG. Candidate slot/`candidateId` is excluded from exploration randomness and from every behavioral score path; it remains identity plus the explicit final tournament tie-break only. Hidden state IDs are also excluded: initial states are ordered by ID-independent future-behaviour semantic class + visible state, and RNG uses policy/epoch/context + semantic start identity + step + visible Q key. Renaming every state, reordering context arrays, or permuting one semantic model across candidate slots therefore cannot change evaluator behavioral evidence. Evaluator reward is protocol-owned: ongoing `-0.01`, WIN `+1`, LOSS `-1`.

---

# 6. Frozen surrogate and Anti-Goodhart law

There is no global `fun_score`.

Scalar tournament families are `S1,S2,S3,S4,S5,S6,S7,S9`. Hard-core admission independently requires `S1,S3,S6,S8,S9`.

- **S1 Agency**: fraction of reachable >=2-action decision states whose alternatives lead to >=2 exact future-behaviour bisimulation classes. Pass `>=0.20`.
- **S2 Learnability**: `max(P1,P2)-P0`.
- **S3 Competence gradient**: `P3-P0`; pass requires `P3>=0.65`, `P0<=0.75`, gap `>=0.25`.
- **S4 Memory value**: `P2-P1`.
- **S5 Strategy vs universal action**: `P3-best constant-action success`.
- **S6 Failure/learning value**: P2 last-training-epoch minus first; pass gain `>=0.15` and first-epoch failure `>=0.20`.
- **S7 Recontextualization**: mean context-specific P1 diagonal minus cross-context off-diagonal success.
- **S8 Complexity + duplicate-action gate**: for each action pair, compare successor bisimulation classes only on the same reachable states where both are legal. If `coObserved>0` and equivalent/coObserved `>=0.95`, the pair is duplicate and S8 fails.
- **S9 Cross-context robustness**: minimum P3 success over four eval contexts; pass `>=0.50`.

Tournament admission also independently requires: no candidate reward/RNG/policy-identity channel by representation; same-state transition fraction across P2+P3 eval `<=0.25`; best constant-action success `<=P3-0.15`; P2 train→held-out overfit gap `<=0.25`; S1/S6/S8 pass; and all hard-core gates pass. No soft family rescues a failed gate.

---

# 7. Selection evidence closure

Reference selector:

`experiments/autonomous-interest-r6/selection_reference.py`

**Its authoritative inputs are exact candidate models, not caller-created evaluation rows.**

`selection_reference` invokes the frozen sibling evaluator itself. It does not accept caller-supplied scores, P3, eligibility, model digest or `playable` values as selection authority.

Pairwise comparison uses `S1,S2,S3,S4,S5,S6,S7,S9`. A family is strictly better only for difference `>=0.05` and strictly worse for `<=-0.05`. A defeats B iff A is strictly better on at least two families and strictly worse on zero.

Winner among eligible candidates:

1. minimize pairwise losses;
2. maximize pairwise wins;
3. lowest `SHA256(candidateId)`.

The preassigned candidate slot ID is the only final tie source.

---

# 8. Mechanical matched ablation

Each candidate declares 3–6 coupling IDs. A coupled transition contains normal `next`, `couplingId`, and explicit `withoutCouplingNext`. Disabling a coupling means substituting `withoutCouplingNext` for every transition bound to that exact declared coupling.

The selector accepts the **winner model**, then internally evaluates every declared coupling with the frozen evaluator. Unknown couplings are rejected. No caller-provided ablation evaluation is selection authority.

An ablation is eligible iff internally recomputed `P3>=0.50`.

Choose among eligible couplings by:

1. maximize count of scalar-family drops `>=0.05`;
2. maximize sorted descending loss vector lexicographically;
3. lowest SHA-256 of the **coupling semantic-effect fingerprint**: sorted affected-transition records containing source semantic-state identity, canonical action ordinal, normal successor semantic identity and disabled successor semantic identity;
4. canonical coupling ID only if semantic effects are identical.

Thus coupling naming cannot steer a matched-ablation tie.

P1/P2 are retrained inside every ablated world.

---

# 9. Authoritative build manifest

Reference:

`experiments/autonomous-interest-r6/build_manifest_reference.py`

The Human build is admitted only through a manifest recomputed from the exact three candidate model bytes. Before any evaluation/evidence construction, the three models are canonicalized by ascending `candidateId`; caller argv/input order has no authority. The reference recomputes tournament winner and matched ablation; the caller cannot choose either.

The manifest binds at least:

- winner candidate ID and exact winner model digest;
- winner evaluator-result digest;
- complete tournament-evidence digest;
- exact selected coupling ID;
- exact ablation evaluator-result digest;
- winner arm `disabledCoupling=null`;
- ablation arm `disabledCoupling=<selected coupling>`;
- renderer ID and study-runner ID;
- SHA-256 of evaluator, selector, renderer, study runner, build-manifest reference, model schema and machine protocol.

`validate_manifest` canonicalizes the same three candidate models by `candidateId`, recomputes the complete manifest and requires canonical equality. Any permutation of the same exact three models must yield the identical tournament-evidence digest and manifest digest. Human serving may not proceed from a caller-edited manifest.

---

# 10. Frozen neutral Human renderer

Reference:

`experiments/autonomous-interest-r6/renderer_reference.py`

Renderer ID: `ORDIVON_R6_NEUTRAL_GRID_UI_V1`.

The Human UI contains only protocol-owned fixed copy plus neutral state/action presentation:

- observation = 12 fixed grayscale cells, each level determined by one `[0,15]` observation integer;
- actions use global stable protocol ordinals: canonical `a0` is always `Action 1`, `a1` is always `Action 2`, etc.; illegal actions are omitted without renumbering;
- status = fixed `ONGOING/WIN/LOSS` token;
- terminal control = fixed `Next round`;
- title/headings/CSS are protocol-owned;
- candidate action IDs, state IDs, coupling IDs, candidate ID, candidate text, candidate CSS/art/media/scripts and external assets are not Human-visible authority.

Unknown `disabledCoupling` is a hard error. Renderer conformance enumerates every reachable view and action edge in normal and selected-ablation worlds and proves exact transition equivalence. It also proves the fixed 32-eval-start schedule for all 12 within-arm participant ordinals; stride `13 mod 32` visits every start exactly once over 32 episodes.

---

# 11. Executable sealed Human holdout

Reference:

`experiments/autonomous-interest-r6/study_runner_reference.py`

Study runner ID: `ORDIVON_R6_HOLDOUT_RUNNER_V1`.

The runner consumes the exact three candidate models plus an authoritative R6 build manifest. It recomputes/validates the manifest before serving. Winner and ablation use identical renderer/study code; the only arm gameplay difference is the manifest-bound `disabledCoupling`.

## 11.1 Assignment

N=`24` fresh participants, enrollment ordinals `0..23`. Assignment is deterministic from a frozen SHA-256 assignment seed: rank all 24 ordinals; first 12 = winner, remaining 12 = matched ablation. Each arm maps deterministically to within-arm ordinal `0..11` for the exact start-state schedule.

## 11.2 Mandatory interaction-qualified play

Mandatory exposure is **8 minutes of accumulated interaction-qualified active play**, not foreground dwell time and not server wall clock.

The protocol-owned page emits a heartbeat every `5000ms` only while visible and focused. Heartbeats are **presence witnesses only**: they never directly increment mandatory or optional play time. A heartbeat gap `>6500ms`, hidden/unfocused heartbeat, or loss of recent foreground presence clears the current interaction anchor.

A qualifying gameplay interaction is admitted only after the renderer/session successfully verifies the requested transition. It must be either (a) a participant-initiated legal canonical action or (b) protocol-owned `Next round`, and the verified before/after states must differ in the frozen future-behaviour semantic class. Rejected/illegal requests, self-loops and semantic no-ops contribute zero and clear the interaction anchor.

Play time accrues only as the elapsed interval between two successive qualifying interactions in the same phase when the interaction gap is `<=30000ms` and valid visible+focused heartbeat continuity was maintained. The first qualifying interaction only establishes an anchor. Candidate model bytes cannot alter the heartbeat/activity law or observe study time, arm or participant identity.

The Stop/Continue choice does not appear until `480000ms` interaction-qualified mandatory play has accumulated. Focused idle with zero meaningful interactions remains at `0ms`.

## 11.3 Costless stopping and optional phase

At the boundary, exact protocol-owned copy states that the required portion is complete and full compensation is unchanged whether the participant stops or continues. Fixed controls are `Stop now` and `Continue playing`.

Choosing Stop terminates immediately. Choosing Continue begins an optional phase capped at `12` minutes wall clock and resets the interaction anchor.

Optional play time uses the same interaction-qualified law. Heartbeat-only presence, hidden/unfocused time, rejected requests, semantic no-ops, or gaps beyond the frozen bounds do not count.

Primary endpoint:

`VOLUNTARY_CONTINUATION_3M = (choice == continue) AND (activeOptionalPlayMs >= 180000)`

Thus an idle/background/merely-focused tab cannot satisfy the continued-play endpoint.

Pilot support requires both:

- at least `8/12` winner participants satisfy the endpoint;
- winner count exceeds matched-ablation count by at least `3`.

Thresholds are immutable after unblinding. Human self-report may be collected separately only as explanation and cannot override the endpoint.

---

# 12. Frozen software/runtime gate

A model is evaluable only if all exact checks pass: schema `0.38.0`, semantic validation, all references resolve, all states reachable, terminal/ongoing invariants, all actions/couplings used, global train/eval disjointness, all measured caps, reference evaluation completion, and no candidate executable gameplay code.

A Human build is servable only if: authoritative build manifest recomputes exactly; selected coupling is declared; renderer conformance passes for the relevant arm; all source bindings match the manifest; and the exact frozen study runner is used. Runtime identity is also frozen: CPython `3.14.6`, `/usr/bin/python3.14` SHA-256 `2700be1aabe3687bd597f21b0eac3b9bbdf7417e93035255a9286c67935b59bd`; `check-jsonschema 0.38.0` executable SHA-256 `95ceb8a922618479d4d9b73fc55a979013290f160922e5fc6e747dfd759a2e9a`.

No later evaluator, implementer or operator may add candidate-specific quality criteria or choose a different winner/coupling/presentation after generation.

---

# 13. Pre-generation audit law

Before any occurrence may create `R6C01–R6C03`, the complete R6 artifact set must be committed at one exact clean revision and independently revalidated.

Independent auditors must attack at least:

- strict schema/parser/semantic agreement and neutral-observation closure;
- any candidate-controlled Human-visible semantic/text channel;
- P0 visible-state-only semantics and representation determinism;
- canonical action/coupling IDs and rejection of naming-based score/tie-break gaming;
- state-ID rename + context-array reorder invariance for evaluator evidence, coupling-effect fingerprint and Human start schedule;
- state-keyed S8 and all measured hard caps, including the 257-unique-observation witness;
- train/eval separation and P1/P2/P3 determinism;
- caller-evidence forgery against tournament and ablation;
- unknown-coupling / winner-world masquerading as ablation;
- build-manifest recomputation and exact source bindings;
- renderer internal-ID leakage and normal/ablation transition equivalence;
- balanced arm assignment and arm symmetry;
- mandatory active-exposure accounting;
- costless Stop/Continue boundary;
- focused-idle, hidden/idle-tab endpoint gaming, heartbeat gaps, interaction-gap and timer boundaries;
- illegal/rejected/no-op interaction attempts against activity accounting, including proof that a rejected request cannot mutate game state;
- candidate-slot permutation invariance of all evaluator behavioral evidence;
- candidate input-order permutation invariance of tournament evidence and complete build manifest;
- any two-compliant-implementation counterexample affecting winner, ablation, Human build or endpoint.

Any protocol-level defect terminates/versions R6. Frozen R6 is never patched after audit exposure. Only unanimous controlling `PASS_R6_PREGEN` may open the three fresh generator occurrences.

---

# Pre-generation standing

```text
R6_PROTOCOL_FROZEN                false
R6_PREGEN_AUDIT_PASSED            false
R6_CANDIDATE_GENERATION_STARTED   false
R6_SEMANTIC_SLOTS_CONSUMED        0
R6_EXACT_FRESH_CANDIDATES         3
PREIMPLEMENTATION_QUALITY_RANKING false
CANDIDATE_LOGIC_EXECUTABLE_CODE   false
CANDIDATE_VISIBLE_TEXT_ALLOWED    false
LIVE_HUMAN_JUDGMENT_ALLOWED       false
WEIGHTED_GLOBAL_SCORE_ALLOWED     false
PRODUCT_SELECTED                  false
G0_ENTERED                        false
```
