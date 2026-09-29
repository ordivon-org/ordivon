# Recursive LEGO R2.1 Prospective Validation R1

Status: **prospective consumer experiment; calibration must pass before inferential execution**.

This study tests one bounded claim: whether exposing the exact canonical Recursive LEGO R2.1 method contract changes fresh-Agent correctness on frozen cross-layer reasoning tasks. It does **not** test Skill discovery UX, live Runtime/Tool execution, or general intelligence.

The study deliberately reuses existing Ordivon owners instead of creating another experiment framework:

- Harness `DeepSeekTurnAdapter` owns Provider calls and effective model identity;
- `anc_canonical` owns canonical digests;
- Experimental Fabric R2 contributes the design rules: preregistration before outcomes, task-instance replication, seeded randomized order, disjoint calibration/inferential cohorts, provider identity preflight, and fail-closed `trial_started` journals;
- the canonical R2.1 Skill remains the treatment artifact and does not own evaluation.

## Design

- Provider/model factor: fixed `deepseek-flash` for both arms.
- Arms:
  - `control`: evidence-bounded generic problem solving with UNKNOWN preservation;
  - `r2_1`: the same generic contract plus the exact canonical R2.1 `SKILL.md` bytes.
- Independent unit: one frozen task instance.
- Each task receives both arms once; the two calls are paired observations, not two independent tasks.
- Calibration: 12 disjoint tasks (2 per family) × 2 arms = 24 calls.
- Inferential: 24 disjoint tasks (4 per family) × 2 arms = 48 calls.
- Families: minimal broken frontier, verifier/spec bridge, legal operator program, experimental-design replication, qualified feasible optimization, execution-vs-semantic completion.
- No Tools are exposed in R1; this isolates the method contract before a later real-Tool/recovery experiment.

## Primary endpoint

`exactChoiceCorrect`, evaluated by a deterministic arm-blind answer key. The inferential estimand is the task-level paired difference in correctness (`R2.1 - control`). The preregistered exact paired test is McNemar's conditional two-sided binomial test over discordant task pairs.

Secondary diagnostics are JSON parse validity, Provider/effective-model continuity, prompt/completion/total tokens, and latency. They are not combined into a weighted score.

## Calibration gate

Calibration is only a difficulty/discrimination gate. It never contributes to the inferential effect estimate. It passes only when:

- all 24 trials complete under the frozen Provider identity;
- pooled exact successes are between 4 and 20 inclusive;
- at least 2 task blocks are mixed (one arm correct, the other wrong);
- mixed blocks span at least 2 task families.

A failed gate closes this task-bank revision. Any revised bank must receive a new revision and new preregistration before further Provider calls.

## Safety/currentness boundaries

- Treatment bytes are digest-bound to the canonical Skill.
- Hidden gold choices are never included in Provider messages.
- The runner refuses unmatched `trial_started` records instead of blind retrying an ambiguous call.
- Effective model drift stops the campaign before the next trial.
- Inferential execution is refused unless a committed preregistration and passing calibration receipt exist.
