# Autonomous Game Interest R7 — Blinded Presentation, Closed Evaluation, Executable Holdout

Status: **PRE-GENERATION PROTOCOL FREEZE CANDIDATE / GENERATION FORBIDDEN UNTIL EXACT FREEZE + UNANIMOUS INDEPENDENT PRE-GENERATION AUDIT PASS**

Observed: 2026-09-15

## Research question

Can Ordivon autonomously create and select a fresh deterministic finite whole-product game without live candidate-specific Human quality/fun/preference judgment before exact build freeze, then produce non-trivial voluntary continued play in a sealed Human holdout relative to a mechanically selected matched ablation?

R7 deliberately restricts the experiment to finite deterministic discrete-decision games represented as declarative JSON. This is an experimental closure choice, not a claim that all games should use this substrate.

## Why R7 exists

R1–R6 were terminated before candidate generation whenever independent pre-generation review found protocol-level freedom capable of changing winner, ablation, Human presentation or endpoint accounting. R7 inherits every still-valid closure and specifically fixes the final R6 findings:

1. candidate-controlled 4x3 grayscale observations could encode pictograms/directives such as `CONTINUE` despite the absence of strings;
2. matched-ablation evidence could change when the same `trainInitialStates` were reordered because normal-world semantic ties retained caller array order while disabled-coupling behavior differed;
3. hidden/blur intervals occurring wholly between heartbeat ticks were invisible to the server even though the normative law claimed hidden/unfocused presence immediately reset interaction continuity.

Frozen R6 remains immutable historical evidence. R7 starts with zero semantic candidates.

---

## 1. Information boundary

Before exact winner + matched-ablation build freeze:

- no live Human candidate preference, fun score, qualitative steering, screenshot ranking, mechanic ranking or playtest may enter generation, evaluation or selection;
- candidate-specific user-visible progress is forbidden; aggregate process status is allowed;
- pretrained model priors, public/mature game-design knowledge, the registered 18 mechanism families, 33 motifs and mature engineering patterns are allowed priors;
- automated Agent criticism is allowed only under the frozen protocol and has no Human-taste authority.

After Human unblinding, changing model logic, evaluator, selector, renderer, presentation mapping, study runner, thresholds, assignment or selected coupling creates a different experiment version.

---

## 2. Search budget and freshness

Exactly three fresh generator occurrences may eventually own `R7C01`, `R7C02`, `R7C03`. They may start only after exact R7 freeze plus unanimous controlling pre-generation PASS.

They may read the R7 protocol, mechanism/motif libraries, public design priors and mature implementation patterns. They may not read R1 candidate payloads or the PC01/PC02/PC03 whole-product specifications and may not consume candidate-specific live Human feedback.

Once a generator fixes its semantic model, it cannot replace it after seeing another candidate or evaluation outcome. Schema/semantic-invalid candidates are eliminated and not replaced.

```text
3 fresh declarative candidate models
        ↓ schema + semantic validation
all valid models evaluated by frozen evaluator
        ↓ hard-core + Anti-Goodhart gates
frozen selector derives evidence from exact model bytes
        ↓ no-weight pairwise tournament
≤1 autonomous winner
        ↓ every declared coupling reevaluated
mechanically selected matched ablation
        ↓ exact build manifest + blinded presentation seed
winner + ablation + source bindings frozen
        ↓ one frozen renderer + one frozen study runner
sealed N=24 Human holdout
```

No preimplementation quality rank, QD curator, weighted global score or Human tie-break exists.

---

## 3. Declarative model authority

Normative schema:

`domains/game/game-autonomous-interest-model-r7.schema.json`

Each model contains only:

- candidate identity and `humanSignalUsed=false`;
- 2–8 canonical action IDs `a0..a(N-1)`;
- 3–6 canonical coupling IDs `c0..c(N-1)`;
- contexts `0..3`;
- four training starts/context and eight evaluation starts/context;
- 12–512 finite states;
- per-state `observationClass`, status and deterministic transitions.

Terminal states have no transitions. Ongoing states have at least one. Every reference resolves, every action/coupling is used, every state is reachable from the frozen initial pools, and train/eval initial-state identities are globally disjoint.

### 3.1 Observation-equivalence only

A candidate does **not** author Human-visible pixels, text, symbols, HTML, CSS, assets, media, colors, geometry or arbitrary JSON observations.

Each state declares only:

```text
observationClass: integer in [0,255]
```

The integer label itself has no authority. The evaluator canonicalizes the candidate-declared observation partition label-invariantly against protocol-measured gameplay structure. Renaming raw observation labels cannot change behavioral evaluation, semantic model fingerprint or final Human presentation seed.

State IDs remain internal references only. Action/coupling IDs have canonical prefixes and no naming degree of freedom.

Measured caps are recomputed by the semantic validator:

- actions <=8;
- reachable states <=512;
- canonical observation classes <=256.

JSON parsing is strict: duplicate object keys and `NaN/Infinity` are rejected.

---

## 4. Determinism and policy ensemble

Candidate transitions contain no executable callback, RNG, wall clock, environment, network, reward or policy-identity input.

Reference evaluator:

`experiments/autonomous-interest-r7/evaluator_reference.py`

Maximum episode length: 96 decisions.

- **P0 VISIBLE_STATE_HASH** — deterministic stateless action from canonical observation class + legal actions only.
- **P1 REACTIVE_Q** — tabular Q-learning on current visible state; epochs 4, alpha .25, gamma .95, epsilon .30→.05.
- **P2 MEMORY_Q** — same constants; state = previous visible + previous action + current visible.
- **P3 EXACT_GRAPH_BFS** — exact shortest path to WIN over the finite graph.

Protocol reward is ongoing `-0.01`, WIN `+1`, LOSS `-1`.

P1/P2 exploration is SHA-256-derived protocol determinism. Candidate ID/slot is excluded from all behavioral score paths. Hidden state IDs and caller array order are excluded from evaluator authority.

Crucially, `initial_states(model, split, context, disabledCoupling)` canonicalizes starts under the **exact world being evaluated**. An ablated world therefore cannot inherit normal-world stable-sort ties.

---

## 5. Surrogate and Anti-Goodhart law

There is no global `fun_score`.

Scalar tournament families: `S1,S2,S3,S4,S5,S6,S7,S9`.
Hard-core admission independently requires `S1,S3,S6,S8,S9`.

- **S1 Agency** — fraction of reachable >=2-action states whose alternatives lead to >=2 future-behavior classes; PASS >=.20.
- **S2 Learnability** — `max(P1,P2)-P0`.
- **S3 Competence gradient** — `P3-P0`; requires P3>=.65, P0<=.75, gap>=.25.
- **S4 Memory value** — `P2-P1`.
- **S5 Strategy vs universal action** — `P3-best constant-action success`.
- **S6 Failure/learning value** — P2 final training epoch minus first; gain>=.15 and first-epoch failure>=.20.
- **S7 Recontextualization** — context-specific P1 diagonal minus cross-context off-diagonal success.
- **S8 Complexity + duplicate-action gate** — action-pair comparison is keyed to the same reachable co-observed state. If equivalent/coObserved>=.95, the pair is duplicate and S8 fails.
- **S9 Robustness** — minimum P3 success across four eval contexts; PASS >=.50.

Tournament admission also independently requires no candidate reward/RNG/policy channel, unchanged-transition fraction <=.25, best constant-action success <=P3-.15, P2 train→eval overfit gap <=.25, and all hard-core gates. No soft family rescues a hard failure.

---

## 6. Selection and matched ablation

Reference selector:

`experiments/autonomous-interest-r7/selection_reference.py`

Its authoritative inputs are exact candidate models, never caller-created score rows.

Pairwise strict difference is .05 on `S1,S2,S3,S4,S5,S6,S7,S9`. A defeats B iff A is strictly better on >=2 families and strictly worse on 0.

Winner rule:

1. minimize pairwise losses;
2. maximize pairwise wins;
3. lowest SHA-256(candidateId).

For the winner, every declared coupling is reevaluated by the frozen evaluator with P1/P2 retrained in the disabled-coupling world. An ablation is eligible iff P3>=.50.

Matched ablation selection:

1. maximize count of scalar-family drops >=.05;
2. maximize sorted descending loss profile;
3. lowest SHA-256 of coupling semantic-effect fingerprint;
4. canonical coupling ID only if semantic effects are identical.

The disabled successor identity inside the fingerprint is computed under the disabled-coupling semantics. Caller initial-state order, state IDs and coupling spelling cannot steer the ablation.

---

## 7. Semantic model fingerprint and post-fix blinded presentation

R7 separates gameplay semantics from Human-visible presentation.

`semantic_model_fingerprint(model)` is invariant to raw state IDs, raw observation-class labels and context-array ordering. It binds the canonical gameplay graph, canonical observation partition, action/coupling ordinals and context start semantics.

After all three exact candidate models are fixed, the authoritative build manifest derives:

```text
presentationSeed = SHA256(
  "ordivon-r7-presentation-blind-v1" |
  sorted(semantic fingerprint of each exact candidate)
)
```

No individual generator knows the final seed while authoring its own model because the other exact models do not yet exist.

The renderer then derives a participant-specific permutation over 256 protocol-owned token identities from:

```text
fixed renderer domain | presentationSeed | enrollment ordinal
```

A candidate observation class is shown as **one protocol-owned neutral token**, not as a candidate-authored pixel array. Token appearance is fixed by renderer code from the blinded token identity. Candidate bytes cannot choose text, glyph layout, multiple-pixel spatial patterns, CSS or assets.

Raw observation-label renaming and state-ID renaming do not change the semantic fingerprint or presentation seed.

---

## 8. Authoritative build manifest

Reference:

`experiments/autonomous-interest-r7/build_manifest_reference.py`

The build manifest canonicalizes the exact three models by candidate ID, recomputes tournament + matched ablation, and binds:

- winner candidate ID and exact model digest;
- winner evaluator result digest;
- tournament evidence digest;
- selected coupling;
- ablation evaluator result digest;
- winner/ablation disabled-coupling bindings;
- presentation seed;
- renderer and study-runner IDs;
- evaluator, selector, renderer, study runner, build-manifest reference, model schema and machine-protocol digests.

Caller order cannot change the manifest. Human serving rejects caller-edited manifests.

---

## 9. Human renderer

Reference:

`experiments/autonomous-interest-r7/renderer_reference.py`

Renderer ID: `ORDIVON_R7_BLINDED_TOKEN_UI_V1`.

The Human UI contains protocol-owned fixed copy plus:

- one blinded state token;
- global stable action ordinals: canonical `a0` = `Action 1`, etc.; illegal actions are omitted without renumbering;
- fixed `ONGOING/WIN/LOSS` status;
- fixed `Next round` terminal control.

Candidate ID, state IDs, coupling IDs, raw observation labels, arbitrary candidate text, assets or scripts never become presentation authority.

The 32 exact evaluation starts use stride 13 for each within-arm participant ordinal 0..11. Winner and ablation use the same normal-world start schedule; only the manifest-bound disabled coupling differs.

Renderer conformance checks every reachable view/action edge and both arms before Human serving.

---

## 10. Executable sealed Human holdout

Reference:

`experiments/autonomous-interest-r7/study_runner_reference.py`

Study runner ID: `ORDIVON_R7_HOLDOUT_RUNNER_V1`.

N=24, deterministic 12 winner / 12 ablation assignment from the frozen assignment seed.

### Mandatory phase

The required exposure is 8 minutes of **interaction-qualified active play**, not foreground dwell.

Heartbeat every 5000ms is a presence witness only and never adds play time. Presence continuity also has event-driven loss reporting:

- `visibilitychange` to hidden → `/presence-loss`;
- `blur` → `/presence-loss`;
- `pagehide` → `/presence-loss`.

The server immediately clears heartbeat and interaction anchors on these events. Therefore a hidden/blur interval wholly between heartbeat ticks cannot be counted as uninterrupted foreground presence.

A qualifying gameplay interaction must be a protocol-verified legal canonical action or protocol-owned Next round whose before/after semantic classes differ. Rejected, illegal, self-loop or semantic no-op interactions add zero and clear the interaction anchor.

Time accrues only between successive qualifying interactions in the same phase when interaction gap <=30000ms and recent valid foreground presence exists. The first meaningful interaction only establishes an anchor.

Focused idle remains 0ms.

### Choice and optional phase

After 480000ms accumulated mandatory active play, fixed protocol copy states compensation is unchanged whether the participant stops or continues. Controls are fixed `Stop now` / `Continue playing`.

Optional play is capped at 12 wall-clock minutes and uses the same interaction-qualified accounting.

Primary endpoint:

```text
VOLUNTARY_CONTINUATION_3M =
  choice == continue
  AND activeOptionalPlayMs >= 180000
```

Pilot support requires winner >=8/12 and winner count at least 3 higher than ablation. Thresholds are immutable after unblinding.

---

## 11. Software/runtime gate

Evaluable model requires exact schema validation, semantic validation, reference closure, reachability, terminal/ongoing invariants, action/coupling use, global train/eval disjointness, measured caps and reference evaluation completion.

Human serving additionally requires exact manifest recomputation, selected coupling declaration, renderer conformance, exact source bindings and exact frozen study runner.

Frozen runtime identity:

- CPython 3.14.6 at `/usr/bin/python3.14`, SHA-256 `2700be1aabe3687bd597f21b0eac3b9bbdf7417e93035255a9286c67935b59bd`;
- check-jsonschema 0.38.0 at `/root/.local/bin/check-jsonschema`, SHA-256 `95ceb8a922618479d4d9b73fc55a979013290f160922e5fc6e747dfd759a2e9a`.

---

## 12. Mandatory pre-generation regressions

Before R7 candidate generation, the exact frozen bytes must independently survive at least:

- observation-class-only schema/semantic closure;
- raw observation label permutation invariance;
- state-ID and context-array reorder invariance;
- R6 S8 co-observed-state duplicate-action counterexample;
- R6 disabled-coupling initial-state-order counterexample;
- candidate-slot/candidate-ID behavioral invariance;
- caller-evidence forgery resistance;
- model-input permutation invariant build manifest;
- semantic-fingerprint invariant presentation seed;
- R6 bitmap/pictogram injection closure;
- candidate-controlled text/ID leakage closure;
- unknown-coupling rejection;
- focused-idle non-counting;
- explicit hidden/blur/pagehide reset entirely between heartbeat ticks;
- illegal/no-op/rejected interaction non-counting;
- choice-phase rejected requests cannot mutate game state;
- balanced arm assignment and winner/ablation symmetry;
- exact runtime/tool identities.

Any protocol-level defect terminates R7 and requires a successor version. Frozen R7 is never repaired after audit exposure.

Only unanimous controlling `PASS_R7_PREGEN` may open `R7C01–R7C03`.

---

## Pre-generation standing

```text
R7_PROTOCOL_FROZEN                false
R7_PREGEN_AUDIT_PASSED            false
R7_CANDIDATE_GENERATION_STARTED   false
R7_SEMANTIC_SLOTS_CONSUMED        0
R7_EXACT_FRESH_CANDIDATES         3
CANDIDATE_EXECUTABLE_CODE         false
CANDIDATE_VISIBLE_PIXELS_ALLOWED  false
CANDIDATE_VISIBLE_TEXT_ALLOWED    false
LIVE_HUMAN_JUDGMENT_ALLOWED       false
WEIGHTED_GLOBAL_SCORE_ALLOWED     false
PRODUCT_SELECTED                  false
G0_ENTERED                        false
```
