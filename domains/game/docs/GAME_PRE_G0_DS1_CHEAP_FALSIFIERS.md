---
schema_version: 1
id: game.pre-g0-direction-search.ds1
title: Ordivon Game Pre-G0 DS1 — Cheap Falsifier Battery
type: research
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - researcher
  - builder
  - agent
updated: 2026-08-17
summary: First executable Pre-G0 falsifier battery. Tests five zero-Agent direction hypotheses and one responsive-Agent baseline contrast with structural metrics before paying human-play, presentation or live-model costs. Eliminates weak realizations, preserves surviving GameForms only provisionally, and finds no FoundationReopenCondition.
evidence_status: measured
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.pre-g0-direction-search
  - game.foundations-research.r29
  - game.development-model
---
# Ordivon Game Pre-G0 DS1 — Cheap Falsifier Battery

## 0. Status

DS0 opened the GameForm candidate space. DS1 begins deletion.

This round does **not** ask whether a micro-treatment is fun enough to ship. It asks whether a candidate's claimed decision/learning/combination/response structure exists at all under a cheap executable model.

The executable battery is:

```text
scripts/pre-g0/ds1-battery.ts
```

and its measured evidence is:

```text
evidence/pre-g0/ds1-structural-battery.json
```

Canonical product status remains:

```text
Pre-G0
Product selected: no
G0 entered: no
FoundationReopenCondition: not triggered
```

---

# 1. Claim boundary — machine falsification is intentionally asymmetric

A deterministic/simulation battery can cheaply establish some **negative** facts:

```text
one action dominates
visible state rarely changes optimal response
information order does not matter
one build dominates across seeds
one layout solves every objective
one upgrade order is almost universal
an adaptive opponent adds no causal distinction
```

These are legitimate reasons to delete or redesign a realization before spending more.

But the same battery cannot establish:

```text
fun
attachment
creativity
meaning
game feel
suspense
beauty
willingness to replay
human causal comprehension
```

Therefore DS1 uses an asymmetric evidence rule:

```text
Structural failure can kill a cheap realization.
Structural survival only earns the next falsifier.
```

Strong law:

```text
SimulationSurvival != PlayerValueProof
```

---

# 2. Evidence states

DS1 distinguishes candidate/form claims from realization claims.

```text
structural-survivor
= this cheap realization contains the causal/decision structure it claimed;
  proceed to a more player-facing falsifier.

realization-eliminated
= this particular ruleset/parameterization failed;
  do not infer the entire GameForm is false from one realization.

weakened
= distinction exists but cheaper-baseline or effect-size pressure reduces the claim.

structural-failure
= reserved for stronger repeated evidence against the underlying structural hypothesis;
  DS1-A does not assign this verdict to any broad GameForm.
```

This preserves the DS0 rule:

```text
Poor realization != dead form
```

while still allowing aggressive deletion of experiments.

---

# 3. Shared structural measures

The first battery uses measurements that transfer across materially different forms without pretending they are one Player Value score:

```text
Dominant-choice pressure
State/counterfactual sensitivity
Adaptive information gain
Path-dependent policy advantage
Strategy/build diversity
Cheaper-baseline parity
```

They are diagnostic coordinates, not an optimization scalar.

---

# 4. Battery scope

The first executable pass covers:

```text
Wave A
D02 Legible Tactical Puzzle
D03 Epistemic Mystery
D04 Combinatorial Roguelike Buildcraft
D05 Automation / Logistics Engineering
D15 Incremental / Delegation Optimizer

Wave B
D14 Constraint-Based Co-Creation
```

Why these six?

```text
- all can be tested without expensive presentation;
- five establish strong zero-Agent baselines;
- D14 directly tests responsive-other value against cheaper non-model baselines;
- together they pressure Decision, World, Knowledge and Meaning/Creation value modes.
```

No current Station Zero or Casefile implementation receives candidate credit.

---

# 5. D02 — Legible Tactical Puzzle

## Hypothesis

```text
Visible future threats
+ constrained action
→ state-sensitive tactical response
```

without opponent cognition.

## Treatment

```text
6×6 board
3 player units
3 enemies
visible enemy target cells
move / strike / brace / wait
320 generated states
```

The test asks whether:

```text
one action family dominates
or
changing a visible enemy telegraph changes the best response often enough
```

## Measured result

```text
Best-action family:
move   157 / 320
strike 159 / 320
wait     4 / 320

family entropy                     = 1.084 bits
dominant-family rate               = 49.7%
telegraph counterfactual changes
best action                        = 25.0%
mean near-optimal actions          = 3.119
```

## Verdict

```text
D02 realization v1: ELIMINATED
D02 broad GameForm: remains open
```

The problem is **not** action-family collapse: move and strike are both common.

The problem is that changing one visible enemy intent changed the optimal action in only one quarter of generated states. The current micro-ruleset therefore does not yet make telegraphed future information causally important enough.

This is precisely the kind of failure Into-the-Breach-like reasoning should not tolerate: a telegraph that is visible but often decision-irrelevant is presentation, not deep information play.

Next D02 work, if retained, must increase:

```text
TelegraphCausalLeverage
```

without merely adding more enemies or options.

Do not add Agent unpredictability to hide this weakness.

---

# 6. D03 — Epistemic Mystery / Knowledge Exploration

## Initial surprise

The first treatment used:

```text
18 hidden histories
8 clues
4 inspections
```

and produced:

```text
greedy adaptive remaining = 1.0
fixed checklist remaining  = 1.0
random remaining           ≈ 1.04
```

This is a **design failure**, even though every case is solvable.

The information budget is so generous that:

```text
ChoiceOfEvidence ≈ irrelevant
```

and the mystery degenerates toward checklist completion.

## Scarcity ablation

DS1 then changed **only the inspection budget**, not the hidden histories or clue semantics:

```text
4 inspections → 2 inspections
```

Measured result:

```text
adaptive greedy solved rate        = 100%
mean remaining after adaptive      = 1.0
mean remaining after fixed order   = 5.0
mean remaining after random order  = 2.209
adaptive clue sequences            = 2
```

The same evidence graph therefore exhibits two qualitatively different games:

```text
Generous information
→ checklist / eventual certainty

Scarce information
→ evidence-selection strategy
```

## Verdict

```text
D03: STRUCTURAL SURVIVOR
with a hard design constraint
```

New DS1 law:

```text
KnowledgePlay requires InformationScarcity / Cost / Branching.
```

More information is not monotonically better.

```text
Observation abundance
can destroy epistemic agency.
```

The next falsifier must therefore use a human-readable case where players choose what to learn and must test:

```text
MentalModelRevision
vs
ClueChecklistCompletion
```

---

# 7. D04 — Combinatorial Roguelike Buildcraft

## Hypothesis

```text
changing encounter demands
+ combinatorial synergies
+ constrained draft offers
→ path-dependent build decisions
```

## Treatment

```text
6 draft picks
3 choices per pick
6 card/effect families
5 encounter archetypes
180 generated runs
729 complete build paths per run
```

For every run the battery compares:

```text
exhaustively optimal build path
vs
locally greedy immediate-score choice
```

## Measured result

```text
mean optimal-vs-greedy score uplift = 5.2%
runs with >2% uplift                 = 46.7%
distinct top-two build signatures   = 11
largest single-card share in
optimal choices                      = 29.7%
```

## Verdict

```text
D04: STRUCTURAL SURVIVOR
```

The treatment does not collapse to one card or one build signature, and global path reasoning has measurable value over local greed.

However the result is not overwhelming:

```text
>2% optimal advantage occurs in < half of runs.
```

So the next treatment must not simply add cards. It should test whether a player can **perceive** synergy and trajectory stakes clearly enough that the mathematically real path dependence becomes playable rather than hidden optimization.

---

# 8. D05 — Automation / Logistics Engineering

## Hypothesis

```text
production goals
+ shared machine budget
+ bottleneck chains
→ materially different optimal system structures
```

## Treatment

```text
12-machine budget
9 machine types
science / ammo / circuit objectives
125,970 complete allocations exhaustively evaluated
```

## Measured result

Optimal layouts across the three objectives have:

```text
science ↔ ammo Jaccard overlap    = 0
science ↔ circuit overlap         = 0
ammo ↔ circuit overlap            = 0
universal optimal layouts         = 0
```

The best balanced solution reaches:

```text
normalized geometric mean = 0.630
```

while the top twenty balanced allocations are all distinct.

## Verdict

```text
D05: STRUCTURAL SURVIVOR
```

This is the strongest zero-Agent structural result in DS1-A.

The system already produces:

```text
Goal change
→ bottleneck change
→ architecture/allocation change
```

without authored story, character cognition or generated content.

But this treatment is still spreadsheet-like. The next falsifier must add **transport/topology** in a tiny interactive surface and ask whether finding/debugging bottlenecks becomes legible and satisfying.

Do not jump to a large Factorio-like production simulation.

---

# 9. D15 — Incremental / Delegation Optimizer

## Hypothesis

Sparse intervention remains interesting if horizon/shocks alter the investment policy enough to require re-planning.

## Treatment

```text
5 upgrades
all 120 upgrade orders
6 horizon/shock scenarios
```

## Measured result

```text
best first choice:
generator 5 / 6 scenarios
storage   1 / 6

distinct scenario-optimal orders = 3

best universal order mean regret = 7.4%
maximum regret                   = 19.3%
```

There is some scenario sensitivity, but most environments begin with the same generator-first logic, and one order remains broadly competitive.

## Verdict

```text
D15 realization v1: ELIMINATED
D15 candidate: DEMOTED / PAUSED
```

This treatment is too close to:

```text
learn a strong ordering
→ repeat it
→ wait for compounding
```

The 19.3% worst-case regret is evidence that scenarios are not literally identical, but the early decision topology is still too concentrated to justify player-value investment now.

Do not rescue D15 by adding dozens of currencies/upgrades. A second realization should be admitted only if a **cheap** design can create genuinely state-conditioned intervention without complexity inflation.

---

# 10. D14 — Constraint-Based Co-Creation

This is DS1's first direct Agent-necessity pressure test.

## Hypothesis

```text
Creation
+ another participant with learnable preferences/response
→ creative choices become strategically consequential
```

## Baseline ladder

DS1 deliberately does **not** start with an LLM.

```text
A. visible static rubric
B. hidden fixed persona preference
C. deterministic responsive-policy persona
```

The creative action space is held fixed:

```text
6 motifs
4 choices
1,296 complete sequences
5 persona profiles
```

## A — visible static rubric

Every motif has equal static value.

Result:

```text
1,296 sequences
→ 1 unique score
```

The baseline is completely degenerate.

```text
Creation without differentiated consequence
= arrangement, not strategy.
```

## B — hidden fixed persona

Different personas produce:

```text
4 distinct optimal sequences
```

but optima often collapse into repetition:

```text
logic > logic > logic > logic
empathy > empathy > empathy > empathy
humor > humor > humor > humor
...
```

Preference diversity helps, but static preference remains exploitable as one-dimensional maximization.

## C — deterministic responsive persona

Add only:

```text
novelty preference
repeat aversion
specific contrast preferences
```

The optimal sequence changes for:

```text
5 / 5 personas
```

and produces:

```text
5 distinct persona-optimal sequences
```

Examples:

```text
scholar: wonder > logic > wonder > logic
romantic: wonder > empathy > risk > empathy
trickster: wonder > humor > risk > humor
warrior: risk > violence > risk > violence
healer: logic > empathy > logic > empathy
```

## Verdict

```text
D14 responsive-other hypothesis: STRUCTURAL SURVIVOR
High-cost / model Agent necessity: NOT ESTABLISHED
```

This is an important negative result for Agent-first temptation.

A cheap deterministic responsive policy already creates the tested causal distinction.

Therefore:

```text
ResponsiveOtherNeed
!=
LLMNeed
```

and DS1 explicitly rejects the next step:

```text
"it survived, so now call a live model"
```

Instead the next evidence must be human play:

> Is adapting creation to a responsive other intrinsically interesting, and does the intended creative space require interpretation/generalization that the cheap policy cannot preserve?

Only if the answer is yes does live-model cognition receive a new admission case.

---

# 11. First portfolio update

DS1 does **not** rank products. It updates evidence state.

| Candidate | DS1 state | Why |
| --- | --- | --- |
| D02 tactical puzzle | realization eliminated; form open | current telegraphs lack enough causal leverage |
| D03 epistemic mystery | structural survivor | scarcity makes evidence selection decisively matter |
| D04 roguelike buildcraft | structural survivor | global synergy/path reasoning beats greedy and stays diverse |
| D05 automation/logistics | structural survivor | objective changes force completely different optimal allocations |
| D15 incremental/delegation | realization eliminated; candidate demoted | early policy remains too universal/rote |
| D14 constraint co-creation | structural survivor; model need unproven | responsive other matters, but deterministic policy is already sufficient structurally |

This is the first actual narrowing of Pre-G0:

```text
Advance now:
D03 / D04 / D05 / D14

Cheap redesign allowed:
D02

Pause unless a materially different cheap realization appears:
D15
```

This is **not** a finalist set. D01/D06–D13/D16 have not yet received equivalent DS1 evidence.

---

# 12. Strongest DS1 deductions

## 12.1 Constraint can create the game

D03 shows:

```text
same truth
same clues
same deduction machinery
+ different observation budget
→ different decision topology
```

The scarce resource is not content quantity but access to information.

## 12.2 Internal depth must survive causal-access pressure

D02 shows the opposite failure:

```text
visible telegraph exists
but often does not alter preferred action
→ weak PlayerCausalAccess
```

Legibility alone is not enough; the visible distinction must matter.

## 12.3 Build diversity is different from content diversity

D04's value comes from:

```text
interaction among choices across time
```

rather than merely seeing different cards.

## 12.4 System goals can create content-like variety without content production

D05 shows that changing desired output can transform the system architecture itself.

```text
Goal diversity
→ system-solution diversity
```

This is a potentially high resource-conversion form because repeated content authoring burden can remain low while decision structure expands combinatorially.

## 12.5 Sparse input does not automatically mean meaningful delegation

D15 warns:

```text
low interaction frequency
+ compounding
!=
interesting high-level control
```

Delegation needs state-sensitive policy questions, not just fewer clicks.

## 12.6 Agent necessity is an ablation result, not a feature aspiration

D14 is the first DS1 proof of this rule:

```text
Adaptive/Responsive Value exists
AND
cheap deterministic policy realizes it
→ expensive Agent cognition is not yet admitted.
```

---

# 13. FoundationReopenCondition audit

Nothing in DS1 requires a new semantic coordinate.

D03 information scarcity is expressible through:

```text
F5 Time / budget
F7 Observation / Representation
F8 Evaluation
F9 Action / control over inspection
```

D04 path-dependent buildcraft uses state/transition/evaluation/time/action.

D05 bottleneck/resource views remain derived over state/relation/transition.

D14 responsive preference uses Subject state/evaluation/policy/relation/time.

D02's failure is a PlayerCausalAccess failure, not a missing foundation.

Therefore:

```text
FoundationReopenCondition = NOT TRIGGERED
Game Foundations v1 remains frozen.
```

---

# 14. What DS1 has and has not earned

Earned:

```text
- delete D02 grid-telegraph v1;
- retain D02 form only for one cheap redesign;
- retain D03 with information scarcity as a hard constraint;
- advance D04 to a playable legibility test;
- advance D05 to a tiny topology/bottleneck interaction test;
- demote/pause D15 current direction;
- retain D14 responsive-other hypothesis;
- explicitly refuse high-cost model cognition for D14 until cheaper policy fails a human-relevant requirement.
```

Not earned:

```text
- no claim that D03/D04/D05/D14 are fun;
- no claim that any is a product finalist;
- no claim that D15 as an entire genre is impossible;
- no claim that D02 needs an Agent;
- no claim that D14 needs an LLM;
- no G0 selection.
```

---

# 15. Exact next frontier

DS1-A structural battery is complete.

The next high-information work is:

```text
Pre-G0 DS2 — Playable Value Falsifiers
```

Recommended order by information gain / cost:

```text
1. D03 — one human-readable epistemic case
2. D05 — tiny interactive bottleneck/topology grid
3. D04 — tiny draft/run with visible synergy feedback
4. D14 — bounded creative interaction against deterministic responsive personas
5. D02 — one redesigned telegraph ruleset, only if its new causal hypothesis is explicit
```

DS2 should measure experience-facing evidence that DS1 cannot:

```text
causal comprehension
choice justification
strategy/model revision
voluntary continued interaction / desire for another round
perceived authorship / adaptation in D14
```

D15 stays paused during this wave.

No live model is required for the first DS2 pass.
