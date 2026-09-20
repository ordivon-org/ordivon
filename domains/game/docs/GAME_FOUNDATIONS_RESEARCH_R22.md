---
schema_version: 1
id: game.foundations-research.r22
title: Ordivon Game Foundations Research — R22 Uncertainty, Probability, Randomness, Risk, Luck, Variance, Determinism and Fairness
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
summary: Canonical R22 decomposition of uncertainty, ignorance, probability, randomness, stochasticity, ambiguity, risk, luck, variance, determinism, unpredictability, expected value and fairness across deterministic, strategic, stochastic, social and generative game forms.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.r18
  - game.foundations-research.r19
  - game.foundations-research.r20
  - game.foundations-research.r21
  - game.foundations-research.map
  - game.foundations-research.continuation
  - game.core-research.reset
---
# Ordivon Game Foundations Research — R22 Uncertainty, Probability, Randomness, Risk, Luck, Variance, Determinism and Fairness

## 0. Status and boundary

R22 continues the foundation programme after R1–R21. It is a research record, not a product specification and not a G0–G8 promotion.

R21 asked:

> How does participant intent become controlled and attributable action?

R22 asks:

> What changes when relevant facts, action consequences or future states cannot be known or controlled exactly, and how should probability, risk, luck and fairness be separated?

The overloaded terms under attack are:

```text
Uncertainty
Ignorance
Probability
Randomness
Stochasticity
Chance
Ambiguity
Risk
Variance
Luck
Expected Value
Distribution
Determinism
Predictability
Fairness
Symmetry
Balance
Outcome Equality
Procedural Fairness
Perceived Fairness
Skill Attribution
```

Starting warnings:

```text
Uncertainty != Randomness
Randomness != Unpredictability
Determinism != Predictability
Probability != Uncertainty itself
Risk != Probability alone
Risk != Variance
ExpectedValue != Distribution
Luck != Random sampling
Fairness != Equal outcome
Fairness != Symmetry
Fairness != Balance
Bad outcome != Bad decision
Good outcome != Good decision
Randomized resolution != Physical indeterminism
```

No product is selected by R22.

---

# 1. External anchors and what they do — and do not — establish

R22 triangulates decision theory, ambiguity research, behavioral decision experiments, uncertainty quantification, deterministic chaos, probability-forecast verification and experimental fairness. These are pressure tests, not a universal Game ontology.

## 1.1 Knight — measurable risk and deeper uncertainty are not the same problem

Frank Knight's *Risk, Uncertainty and Profit* made the historically influential distinction between cases where uncertainty can be represented by known/estimable probabilities and cases where it cannot be reduced that cleanly.

Game lesson:

```text
Known 20% failure chance
is a different decision object from
“We do not know the failure probability.”
```

R22 does not adopt Knight's terminology as the only modern definition of risk, but preserves the core separation between uncertainty **within a probability model** and uncertainty **about the model/probabilities themselves**.

## 1.2 Ellsberg — ambiguity changes choice even when nominal outcomes look comparable

Ellsberg's 1961 experiments showed systematic preferences between gambles with known probabilities and gambles whose probability composition was ambiguous, creating violations of Savage-style subjective expected-utility assumptions.

Game lesson:

```text
Known odds
!= Unknown odds
```

Even if expected payoff could be made similar under some assumed model, players may value the epistemic status differently.

## 1.3 Expected utility is a representation under assumptions, not a substance

von Neumann–Morgenstern and Savage-style decision theories formalize coherent choice under particular assumptions. R18 already established:

```text
Utility is not a substance stored inside the Subject.
```

R22 adds:

```text
Expected utility is one decision representation,
not a complete ontology of risk experience.
```

## 1.4 Prospect theory — outcome distribution is filtered through reference and weighting

Kahneman and Tversky's 1979 prospect theory and later cumulative prospect theory showed experimentally motivated departures from simple expected-utility descriptions, including reference dependence, asymmetry between gains/losses and nonlinear weighting of probabilities.

Game lesson:

```text
Two mathematically equivalent probability descriptions
need not produce equivalent player experience or choice.
```

R22 therefore preserves actual Subject/player preference separately from designer expected value.

## 1.5 Aleatory and epistemic uncertainty are useful but model-relative

Der Kiureghian and Ditlevsen's 2009 discussion of aleatory versus epistemic uncertainty emphasizes that the distinction is useful but depends on the modeling boundary and available knowledge.

Game lesson:

```text
Aleatory:
variation represented as irreducible within the current model

Epistemic:
uncertainty attributable to missing knowledge/model/state
```

but:

```text
what counts as “irreducible”
can change when the model or information boundary changes.
```

## 1.6 Deterministic systems can be hard to predict

Lorenz's 1963 deterministic nonperiodic-flow work is a canonical demonstration that deterministic dynamics can produce complex, aperiodic behavior with strong sensitivity to initial conditions.

Game lesson:

```text
Unique future under full state/rules
!= Easy future prediction for a bounded player.
```

Chess, hidden deterministic seeds, chaotic simulations and large Agent systems reinforce this distinction from different directions.

## 1.7 Probability forecasts can be evaluated independently of one realized event

Brier's 1950 work on probabilistic forecasts provides an early formal example of scoring probability judgments across repeated events rather than judging a probability statement by whether one sample happened.

Game lesson:

```text
“30% chance”
was not wrong merely because the 30% event occurred.
```

Calibration/forecast quality must be separated from one outcome.

## 1.8 Humans can mistake chance for control

Langer's 1975 illusion-of-control experiments showed that chance tasks containing cues associated with skilled situations can lead people to behave as if they possess more control than the mechanism warrants.

Game lesson:

```text
Perceived agency / skill attribution
can exceed actual ActionCausality.
```

This is the uncertainty-side complement to R21's finding that actual control and Sense of Agency differ.

## 1.9 Humans also judge decision quality through outcome

Baron and Hershey's 1988 outcome-bias experiments showed that people can evaluate the quality of an earlier decision differently after learning whether its uncertain outcome was good or bad, even when the decision-relevant information was held constant.

Game lesson:

```text
DecisionQuality != OutcomeQuality
```

A fair game must often help players distinguish these if learning/skill matters.

## 1.10 Small samples are easily misread

Tversky and Kahneman's 1971 “law of small numbers” work documented people's tendency to expect small samples to resemble population properties more closely than they statistically should.

Game lesson:

```text
Short-run streaks and clusters
will often be interpreted as
balance changes, hidden manipulation or personal skill/luck.
```

Do not assume statistically correct RNG automatically feels understandable.

## 1.11 Procedure matters to fairness, not only allocation

Bolton, Brandts and Ockenfels' experimental work on fair procedures involving lotteries shows that procedures themselves can affect fairness-related behavior/judgment beyond the final allocation alone.

Fehr and Schmidt's inequity-aversion model separately shows that distributive comparisons can matter to behavior.

Game lesson:

```text
Fairness has procedural and distributive dimensions.
```

A bad outcome can emerge from a fair procedure, and an equal outcome can emerge from an unfair procedure.

## 1.12 Shannon entropy is not “fun” or “meaningful uncertainty”

Shannon's information theory gives a precise quantitative measure related to uncertainty in a probability distribution for communication problems.

Game lesson:

```text
Entropy can measure distributional uncertainty.
It does not by itself measure:
player stakes,
meaning,
fairness,
learnability,
agency,
or value.
```

### Primary reference anchors used in this round

- Knight, F. H. (1921), *Risk, Uncertainty and Profit*.
- Ellsberg, D. (1961), *Risk, Ambiguity, and the Savage Axioms*, DOI 10.2307/1884324.
- Kahneman, D. & Tversky, A. (1979), *Prospect Theory: An Analysis of Decision under Risk*, DOI 10.2307/1914185.
- Tversky, A. & Kahneman, D. (1992), *Advances in Prospect Theory: Cumulative Representation of Uncertainty*, DOI 10.1007/BF00122574.
- Der Kiureghian, A. & Ditlevsen, O. (2009), *Aleatory or epistemic? Does it matter?*, DOI 10.1016/j.strusafe.2008.06.020.
- Lorenz, E. N. (1963), *Deterministic Nonperiodic Flow*, DOI 10.1175/1520-0469(1963)020<0130:DNF>2.0.CO;2.
- Brier, G. W. (1950), *Verification of Forecasts Expressed in Terms of Probability*, DOI 10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2.
- Langer, E. J. (1975), *The Illusion of Control*, DOI 10.1037/0022-3514.32.2.311.
- Baron, J. & Hershey, J. C. (1988), *Outcome Bias in Decision Evaluation*, DOI 10.1037/0022-3514.54.4.569.
- Tversky, A. & Kahneman, D. (1971), *Belief in the Law of Small Numbers*, DOI 10.1037/h0031322.
- Bolton, G. E., Brandts, J. & Ockenfels, A. (2005), *Fair Procedures: Evidence from Games Involving Lotteries*, DOI 10.1111/j.1468-0297.2005.01032.x.
- Fehr, E. & Schmidt, K. M. (1999), *A Theory of Fairness, Competition, and Cooperation*, DOI 10.1162/003355399556151.
- Shannon, C. E. (1948), *A Mathematical Theory of Communication*, DOI 10.1002/j.1538-7305.1948.tb01338.x / 10.1002/j.1538-7305.1948.tb00917.x.

These sources constrain and falsify R22; they do not replace Game-specific causal analysis.

---

# 2. Core term separation

| Term | Working meaning | Not equivalent to |
| --- | --- | --- |
| **Uncertainty** | More than one materially plausible state/model/outcome remains open from a specified perspective at a specified time. | Randomness. |
| **Ignorance** | Missing relevant knowledge/model structure, possibly too weak even to assign useful probabilities. | A known probability distribution. |
| **Probability** | Quantitative measure/distribution assigned to alternatives under a model or belief state. | Truth, randomness, confidence in every sense. |
| **Randomness** | A realization/selection mechanism treated at the relevant model boundary as not fixed by the conditioning state available to that model. | Unpredictability in general. |
| **Stochasticity** | Model-level transition/output structure represented by probability distributions over multiple possible realizations. | Physical indeterminism necessarily. |
| **Chance** | Neutral game-facing term for an outcome component not selected by the relevant participant/policy and resolved from uncertain alternatives. | Luck or unfairness. |
| **Ambiguity** | Uncertainty about the probability model, distribution, parameters or even which model applies. | Known-risk probability. |
| **Determinism** | Given complete authoritative state and rules at the chosen model boundary, the next state/outcome is uniquely determined. | Predictability. |
| **Predictability** | Ability of a bounded predictor to forecast relevant future properties accurately enough. | Determinism. |
| **Risk** | Exposure to materially valued consequence distributions under uncertainty, especially where adverse outcomes matter. | Probability alone, variance alone. |
| **Variance** | A numerical measure of dispersion around a mean under a specified distribution. | Risk, tail severity, subjective stakes. |
| **Expected Value** | Probability-weighted mean of a represented outcome variable. | Distribution, utility, safety, fairness. |
| **Luck** | Retrospective attribution that a realized valued outcome depended materially on factors outside the relevant participant's control/skill/knowledge. | Randomness itself. |
| **Fairness** | Normative/experienced judgment about whether rules, procedures, opportunities, information, uncertainty and outcomes are acceptably justified. | Equality, symmetry, balance. |
| **Procedural Fairness** | Fairness of the mechanism/process used to reach an outcome. | Equality of realized outcomes. |
| **Perceived Fairness** | Participant's fairness judgment given their beliefs and evidence. | Authoritative mechanical fairness. |
| **Outcome Equality** | Similar/equal realized allocation/results. | Fairness. |
| **Symmetry** | Participants receive structurally identical rules/resources/roles. | Fairness or balance. |

Strong compact separation:

```text
Uncertainty != Randomness != Unpredictability
Probability != Uncertainty itself
Risk != Variance != ExpectedValue
Luck != Chance mechanism
Fairness != Symmetry != OutcomeEquality
DecisionQuality != OutcomeQuality
```

---

# 3. Uncertainty — perspective, object and time matter

A useful R22 definition is:

```text
Uncertainty(subject/model, X, t) =
multiple materially plausible values/states/models of X
remain open at time t under accessible evidence and model.
```

This means uncertainty is incomplete without specifying:

```text
Who / which model is uncertain?
About what?
At what time?
Given what information?
At what abstraction boundary?
```

## 3.1 World branching versus epistemic spread

Two distinct structures:

```text
WorldBranching:
under the chosen authoritative model, same conditioning state/action
can resolve to multiple next states.
```

```text
EpistemicSpread:
the Subject/player does not know which current state/model/outcome is true,
even if authoritative reality is already fixed.
```

They can coexist.

## 3.2 Uncertainty can exist with no randomness

Examples:

```text
Chess opponent's next move
hidden deterministic trap
fog-of-war army position
unknown puzzle rule
chaotic deterministic simulation
unseen shuffled-deck order after seed/state is fixed
```

Therefore R7's old statement is preserved and strengthened:

```text
Randomness is only one source of uncertainty.
```

## 3.3 Randomness can exist with little meaningful uncertainty

If a random cosmetic particle has no decision relevance:

```text
Randomness high
Player-relevant uncertainty low
```

Thus:

```text
RandomnessAmount != PlayableUncertainty
```

---

# 4. Uncertainty Topology

R22 introduces a more useful representation than a scalar “uncertainty level.”

```text
UncertaintyTopology = {
  Bearer,
  Object,
  Source,
  ModelBoundary,
  Reducibility,
  RealizationTime,
  Observability,
  Controllability,
  Stakes,
  UpdatePath
}
```

## 4.1 Bearer

```text
Player
Subject
Faction
Designer
World model
AI model
```

Different bearers may have different uncertainty about the same fact.

## 4.2 Object

```text
current state
future outcome
rule
capability
opponent policy
probability distribution
meaning/interpretation
```

## 4.3 Source

```text
hidden information
randomized transition
other Subject policy
computational complexity
chaotic sensitivity
model ambiguity
semantic ambiguity
generative sampling
```

## 4.4 Reducibility

Can uncertainty be reduced by:

```text
observation
scouting
experimentation
learning
waiting
calculation
communication
buying information
```

or is variation intentionally irreducible within the current game model?

## 4.5 Realization time

```text
before choice
after choice but before commitment
at commitment
after commitment
continually during control
```

This strongly changes agency and risk.

## 4.6 Controllability

Can the player:

```text
avoid
hedge
insure
diversify
probe
reroll
reduce variance
increase information
change exposure
```

Uncertainty and control are independent dimensions.

---

# 5. Epistemic versus aleatory uncertainty

R22 uses the distinction pragmatically.

## 5.1 Epistemic uncertainty

```text
EpistemicUncertainty =
uncertainty attributable to missing knowledge,
state, parameters or model structure at the current boundary.
```

Examples:

```text
unknown enemy location
unknown card identity
unknown damage formula
unknown model reliability
```

It may be reducible.

## 5.2 Aleatory uncertainty

```text
AleatoryUncertainty =
variability represented as irreducible random realization
within the current model boundary.
```

Examples:

```text
die roll
probabilistic hit resolution
random spawn under a declared distribution
```

## 5.3 The boundary is model-relative

A digital game's PRNG is deterministic under complete seed/state.

At engine level:

```text
seed + state + algorithm
→ unique result
```

At player-facing rules level:

```text
attack
→ 20% crit / 80% normal
```

The same system is:

```text
deterministic at one model boundary
stochastic at another.
```

Therefore:

```text
GameRandomness != PhysicalIndeterminism
```

## 5.4 Earlier randomness can become later epistemic uncertainty

A deck is shuffled randomly once.

After shuffle, deck order may be fixed.

For the player:

```text
future draws remain unknown
```

but current uncertainty is primarily epistemic about a fixed hidden order.

Source history and current uncertainty type must not be collapsed.

---

# 6. Determinism — uniqueness is not predictability

```text
Determinism =
complete state + rules
uniquely determine the next state/outcome.
```

This says nothing about computational accessibility.

## 6.1 Hidden deterministic state

A deterministic system may feel random because the player lacks state.

```text
UnknownSeed
+ DeterministicPRNG
→ PlayerUncertainty
```

## 6.2 Computational unpredictability

Chess is deterministic but difficult to predict because the future depends on a huge policy/search space.

## 6.3 Chaotic unpredictability

A deterministic dynamical system can amplify tiny state differences until bounded prediction becomes impractical.

## 6.4 Strategic unpredictability

Other Subjects can choose among policies even in deterministic rules.

## 6.5 Semantic unpredictability

A language model or interpreter can be difficult to predict because mappings from prompt/context to output are complex and under-specified, even when implementation is technically deterministic at a low level.

Core rule:

```text
Determinism answers:
“Is one future fixed by the full model state?”

Predictability answers:
“Can this predictor know enough to forecast the relevant future?”
```

---

# 7. Probability — representation, not ontology

R22 uses a deliberately neutral definition:

```text
Probability =
a quantitative distribution/measure assigned to uncertain alternatives
under a specified model or belief state.
```

It may represent:

```text
frequency model
propensity model
subjective belief
Bayesian posterior
designer transition rule
empirical estimate
```

Game foundations do not need to settle the philosophy of probability.

## 7.1 Probability must have provenance

```text
“30%”
```

is incomplete without knowing:

```text
30% according to what model?
measured from what data?
conditioned on what state?
for whose belief?
with what uncertainty about the estimate?
```

## 7.2 Probability is not confidence in every sense

A model can output:

```text
P(A)=0.7
```

while being uncertain whether its own model is well-specified.

This is second-order/model uncertainty, not captured automatically by the point probability.

## 7.3 Exact percentages are optional player-facing representation

A game can expose uncertainty through:

```text
ranges
qualitative bands
frequency cues
history
animation
spatial uncertainty
expert statements
confidence intervals
```

without showing exact numerical probabilities.

The requirement is useful mental-model calibration, not spreadsheet UI.

---

# 8. Ignorance and ambiguity

## 8.1 Ignorance

```text
Ignorance =
insufficient relevant knowledge/model structure.
```

Sometimes the player cannot even enumerate meaningful alternatives.

Example:

```text
“What does this alien artifact do?”
```

before any evidence.

## 8.2 Ambiguity

```text
Ambiguity =
uncertainty about probabilities/model/parameters,
not merely uncertainty about which outcome will realize.
```

Compare:

```text
Known risk:
20% poison chance

Ambiguity:
poison chance somewhere between 5–50%, source unreliable
```

## 8.3 Mystery often relies on epistemic uncertainty, not RNG

A fixed culprit can generate deep uncertainty if evidence is partial.

Therefore Casefile-style mystery is a canonical counterexample to:

```text
Uncertainty requires stochastic world truth.
```

---

# 9. Randomness and stochasticity

## 9.1 Game-level randomized resolution

R22 defines player-relevant randomness semantically:

```text
RandomizedResolution =
under the player-relevant conditioning state,
resolution samples/selects among multiple outcome alternatives.
```

Implementation can use:

```text
PRNG
server seed
hardware RNG
pre-shuffled table
procedural generator
```

without changing the high-level game semantics.

## 9.2 Stochastic transition model

```text
P(s' | s, a)
```

represents multiple possible next states given current represented state/action.

## 9.3 Randomness can live in different places

```text
setup
available options
hidden information
transition resolution
opponent behavior
timing/order
reward
content generation
```

Where randomness enters matters more than “RNG amount.”

---

# 10. Realization timing — before choice versus after commitment

This is one of R22's highest-yield design distinctions.

## 10.1 Pre-choice realized uncertainty

A random event happens and becomes visible before the player's decision.

```text
Random setup
→ observe result
→ decide
```

Examples:

```text
random map
card draw before play
weather revealed before route selection
```

Primary skill:

```text
adaptation
```

## 10.2 Hidden pre-existing uncertainty

State is already fixed but concealed.

```text
hidden card
trap
fog-of-war unit
```

Primary skills:

```text
inference
scouting
risk management
```

## 10.3 Post-commit randomized resolution

```text
choose action
→ commit
→ random outcome resolves
```

Examples:

```text
hit roll
critical chance
loot roll after kill
```

Primary problem:

```text
risk-bearing decision
```

## 10.4 Continuous process noise

```text
control
↔ stochastic disturbance
↔ correction
```

Examples:

```text
wind
traction variation
noisy sensor
```

Primary skill:

```text
feedback control / robustness
```

### Core distinction

```text
Randomness before decision
often creates a new question.

Randomness after commitment
often changes how the answer pays off.
```

Neither is inherently superior.

---

# 11. Risk — valued exposure under uncertainty

R7 used the useful early heuristic:

```text
Risk ≈ ProbabilityOfLoss × SubjectiveValueOfLoss
```

R22 now replaces that as a general definition because it collapses too much.

Working definition:

```text
Risk =
exposure to a distribution/set of materially valued consequences
under uncertainty,
especially where adverse outcomes matter.
```

## 11.1 Risk requires stakes

A random coin animation with no consequence:

```text
Uncertainty ✓
Randomness ✓
Risk ≈ none
```

Risk emerges when alternative outcomes matter.

## 11.2 Risk is policy-relative

```text
Risk(policy, state, beliefs)
```

can change when the player:

```text
hedges
scouts
waits
diversifies
uses protection
chooses safer route
```

## 11.3 Risk is not one number by default

Relevant structure includes:

```text
probabilities
loss magnitudes
gain magnitudes
variance
skew
tails
reversibility
correlation
path dependence
controllability
ambiguity
```

## 11.4 Downside risk versus symmetric dispersion

Variance treats positive and negative deviations symmetrically.

Players often do not.

A high-upside volatile choice and a catastrophic-tail choice can have similar variance but very different meaning.

Therefore:

```text
Variance != Risk
```

---

# 12. Expected value — mean is not the distribution

```text
E[X] = Σ p_i x_i
```

is useful but compressive.

Two gambles can share expected value while differing in:

```text
variance
tail risk
skew
minimum outcome
maximum outcome
probability of ruin
path dependence
reversibility
```

Therefore:

```text
ExpectedValue != Distribution
```

## 12.1 Expected value is not expected utility automatically

If Subject value is nonlinear/contextual:

```text
E[value(X)]
!= value(E[X])
```

and R18's late-scalarization rule remains active.

## 12.2 One-shot significance

Expected value becomes especially misleading when:

```text
stakes are existential
repetition is impossible
bankruptcy/ruin stops future play
```

A +EV policy can still be unacceptable under hard survival constraints.

## 12.3 Distributional choice

A better R22 question is often:

> Which consequence distribution does this policy create, and which properties of that distribution matter to this Subject/player?

---

# 13. Variance, tails, skew and path

## 13.1 Variance

Variance is one dispersion summary.

It says little by itself about:

```text
direction of deviations
catastrophic tails
asymmetry
threshold crossing
sequence/path
```

## 13.2 Tail risk

Rare events can dominate experience when consequences are severe.

```text
1% total wipe
```

may matter much more than many small fluctuations.

## 13.3 Skew

Two systems can have same mean/variance but different shapes:

```text
many small wins + rare huge loss
versus
many small losses + rare huge win
```

These create different emotions and strategies.

## 13.4 Path dependence

Same final expected wealth/state does not imply same playable risk if one path can trigger:

```text
bankruptcy
injury
irreversible loss
reputation collapse
mission failure
```

before recovery.

## 13.5 Correlation

Diversification only works when risks are not perfectly coupled.

Resource/economy games can become richer when players reason about correlated failure rather than merely independent dice.

---

# 14. Risk preference — do not collapse Subject into expected-value maximizer

R18 already rejects universal scalar utility as ontology.

R22 strengthens this under uncertainty.

Subjects/players may care about:

```text
reference point
loss avoidance
probability of ruin
certainty
ambiguity
upside potential
regret
responsibility
social consequences
```

Therefore:

```text
Highest EV
!= universally preferred policy
```

## 14.1 Risk aversion is not fearfulness

A Subject can rationally reject variance because:

```text
survival constraint
limited resources
irreversible downside
future optionality
```

## 14.2 Risk seeking can be local

A losing Subject may rationally/behaviorally accept more variance because only a high-upside branch preserves a valued future.

## 14.3 Ambiguity preference is separate

A player may prefer known 30% risk over unknown 10–50% risk even when estimated means align.

This is not captured by simple variance alone.

---

# 15. Luck — retrospective attribution, not a mechanism

R22 proposes:

```text
Luck =
retrospective attribution that a realized valued outcome
depended materially on factors outside the relevant participant's
control, skill or available knowledge.
```

## 15.1 Luck can arise without random mechanics

Examples:

```text
opponent unexpectedly blunders
hidden deterministic trap misses you
another faction happens to attack your rival
server-selected deterministic seed favors your spawn
```

From the participant perspective these may reasonably be described as luck.

Therefore:

```text
Luck != Randomness
```

## 15.2 Randomness can occur without meaningful luck

A random ambient bird direction with no stakes is random but not usefully “lucky.”

## 15.3 Luck is observer-relative

What one player calls luck, another informed observer may attribute to hidden skill or information.

Thus:

```text
LuckAttribution depends on the causal model available to the observer.
```

---

# 16. Outcome Contribution Topology

R21 introduced ControlContributionTopology.

R22 adds:

```text
OutcomeContributionTopology =
which factors materially shaped the realized outcome
and at which causal stage.
```

Possible contributors:

```text
player policy
player execution skill
opponent policy
teammate policy
hidden state
stochastic realization
system/environment dynamics
resource constraints
information quality
AI interpretation
```

## 16.1 Why this matters

A single scalar:

```text
“60% skill / 40% luck”
```

usually destroys useful structure.

Instead ask:

```text
Which decisions shifted the distribution?
Which variables selected this sample?
Which causes were knowable?
Which causes were controllable?
```

## 16.2 Outcome contribution can vary by timescale

One hand of poker can be luck-dominated.

A long match/session/career can still be skill-sensitive if better policy systematically changes the outcome distribution.

---

# 17. Decision Quality versus Outcome Quality

This is a core R22 law.

```text
DecisionQuality =
quality of a choice given information, model, objectives and constraints
available at decision time.
```

```text
OutcomeQuality =
value/quality of the realized consequence.
```

Therefore:

```text
GoodDecision + BadLuck → BadOutcome
BadDecision + GoodLuck → GoodOutcome
```

and:

```text
DecisionQuality != OutcomeQuality
```

## 17.1 Outcome bias

Human evaluators often use the realized outcome to retrospectively judge whether the decision was good.

Games that want learning should provide enough causal evidence to resist this collapse.

## 17.2 Ex ante versus ex post evaluation

```text
Ex ante:
Was the policy justified before realization?

Ex post:
What actually happened?
```

Both matter; they answer different questions.

---

# 18. Skill under uncertainty — shift distributions, not guarantee samples

R21 defined Skill as learned capacity for reliably better task performance.

R22 refines this under randomness:

```text
SkillUnderUncertainty =
learned ability to improve the distribution of relevant outcomes
or the quality of decisions under uncertainty,
not necessarily to win every realization.
```

## 18.1 Policy skill

A better player may:

```text
increase win probability
reduce ruin probability
improve expected value
improve worst-case outcomes
adapt better after realization
```

## 18.2 Sample outcome is noisy evidence of skill

One win/loss may tell little.

Repeated evidence, controlled comparisons or causal replay can improve attribution.

## 18.3 Skill can include variance management

Skill is not only choosing higher mean.

It can include:

```text
hedging
position sizing
insurance
information purchase
reserve management
safe routing
```

## 18.4 Skill can choose variance intentionally

When behind, a skilled player may choose a higher-variance line because low-variance play cannot recover the position.

Thus:

```text
VariancePreference is state-dependent.
```

---

# 19. Illusion of control and perceived luck

R21 showed Sense of Agency can diverge from Objective Control.

R22 adds random environments.

## 19.1 Skill cues can inflate perceived control

Choice, familiarity, competition and active participation can make chance mechanisms feel more controllable than they are.

## 19.2 Ritual can emerge around randomness

Players may create causal stories around:

```text
button timing
opening animations
favorite locations
streaks
```

without real effect.

This can be harmless fantasy or harmful mislearning depending on stakes.

## 19.3 Hidden manipulation is especially dangerous

If a game secretly alters odds while presenting them as stable, players cannot calibrate a causal model.

That is not merely “randomness”; it is an information/procedural-fairness problem.

---

# 20. Randomness perception — correct RNG can look wrong

Human intuition about random sequences is imperfect.

Players often expect randomness to alternate more than true independent samples do.

Real random sequences naturally produce:

```text
clusters
streaks
repeats
```

## 20.1 Statistical correctness != perceived fairness

A fair independent RNG can generate five misses in a row.

Players may interpret this as:

```text
bug
rigging
bad balance
personal curse
```

## 20.2 Pity systems / shuffle bags change the process

Designers sometimes reduce streaks by introducing memory:

```text
sampling without replacement
bad-luck protection
pseudo-random distribution
```

This can improve experience but must be recognized as a different stochastic process, not “more truly random.”

## 20.3 Random-looking and random are different

A deterministic sequence designed to appear irregular may look random.

A truly randomized sequence may look suspiciously patterned.

Therefore:

```text
PerceivedRandomness != StatisticalRandomness
```

---

# 21. Learnable uncertainty

R7 introduced:

```text
Unknown + Evidence + Learnability
```

R22 deepens it.

```text
LearnableUncertainty =
uncertainty whose structure can be updated through evidence,
experience, experimentation or disclosed rules.
```

## 21.1 Learning need not eliminate uncertainty

Poker players do not learn the hidden card before reveal; they learn distributions, ranges and policies.

## 21.2 Calibration

A useful player model is not one that always predicts correctly.

It should be calibrated enough that:

```text
rare events feel rare
common events feel common
uncertain events remain uncertain
```

## 21.3 Feedback after resolution

Where appropriate, games can reveal:

```text
roll/result
relevant modifier
hidden state after expiry
why action failed
```

so players can update the correct causal layer.

## 21.4 Mystery exception

Do not reveal everything merely for calibration.

Mystery can preserve hidden truth while providing evidence sufficient for model revision.

---

# 22. Information acquisition under uncertainty

R17's information model becomes central:

```text
WorldTruth
→ Signal
→ Observation
→ Belief
→ Policy
```

Uncertainty creates value for information.

## 22.1 Information value is policy-relative

A clue is valuable when it changes a decision.

```text
InformationValue
≈ potential improvement in reachable policy/outcome
```

not merely entropy reduction.

## 22.2 Scouting and probing

Actions can be taken primarily to reduce uncertainty rather than immediately gain reward.

```text
probe
→ observation
→ belief update
→ better later action
```

This is an exploration/exploitation connection.

## 22.3 Information can reduce risk or increase it

Discovering a threat can reveal that the situation is worse than believed.

Knowledge reduces epistemic uncertainty, not necessarily downside exposure.

---

# 23. Fairness — normative structure, not one metric

Working definition:

```text
Fairness =
judgment that rules, procedures, opportunities, information,
uncertainty and outcomes are acceptably justified
relative to the relevant social/game contract.
```

This is intentionally plural.

## 23.1 Procedural fairness

Questions:

```text
Were rules consistent?
Was the random process applied as declared?
Was authority impartial?
Were decisions made under legitimate procedure?
```

## 23.2 Opportunity / ex ante fairness

```text
Did participants have justified access to meaningful chances/strategies?
```

Identical chances are one mechanism, not a universal requirement.

## 23.3 Informational fairness

```text
Were relevant uncertainty/rules/cues disclosed or inferable
at the level promised by the experience?
```

Hidden information can be fair if hiding is part of the rules.

## 23.4 Causal / skill fairness

```text
Do outcomes respond enough to player decisions/skill
for the claimed competitive/mastery contract?
```

A party game can intentionally answer “not much.”

An esport-like mastery game usually needs a stronger answer.

## 23.5 Distributive fairness

```text
Are rewards/costs/outcomes distributed in a justified way?
```

## 23.6 Perceived fairness

Players judge from beliefs, not engine truth.

A mechanically fair process can feel unfair if feedback/probability structure is opaque.

---

# 24. Fairness != equality != symmetry != balance

## 24.1 Outcome equality

```text
all players receive same reward
```

can be fair or unfair depending on context.

## 24.2 Symmetry

```text
same starting rules/resources
```

can create fairness, but asymmetric games can also be fair through role compensation, alternation or different win conditions.

## 24.3 Balance

Balance concerns relative viability/power/performance structure.

A balanced game can still use an unfair process.

An intentionally asymmetric but fair game need not have equal local power.

Therefore:

```text
Fairness != Balance
Fairness != Symmetry
Fairness != Equality
```

---

# 25. Fair procedure can produce unequal outcome

Consider a fair lottery:

```text
Each player gets 50% chance.
Winner receives all reward.
```

Outcome:

```text
100 / 0
```

is maximally unequal, yet the procedure may still be accepted as fair.

Conversely:

```text
rigged procedure
→ coincidentally equal outcome
```

can remain unfair.

Thus:

```text
ProceduralFairness != OutcomeEquality
```

This is one of R22's strongest fairness separations.

---

# 26. The uncertainty contract

Players implicitly learn a contract about uncertainty:

```text
What is random?
What is hidden?
What can be learned?
What can be controlled?
When is chance resolved?
How severe can outcomes be?
Are odds stable?
Can I mitigate exposure?
```

R22 calls this:

```text
UncertaintyContract
```

## 26.1 Fair bad beat

A player can make a strong decision and lose to a known tail event.

That can be:

```text
painful ✓
unlucky ✓
fair ✓
```

if the uncertainty contract was clear enough.

## 26.2 Unfair-feeling surprise

A low-probability catastrophe that the game never made inferable may feel like authorial punishment rather than risk.

## 26.3 Dynamic odds

Changing probabilities can be fair if change rules are part of the contract and observable/inferable.

Hidden rubber-banding presented as fixed physics can create a procedural/information mismatch.

---

# 27. Agency under uncertainty

Uncertainty does not eliminate agency.

It changes the target of control.

Instead of controlling exact outcomes, players may control:

```text
exposure
odds
information
hedging
position
fallbacks
variance
recovery options
```

## 27.1 Distributional agency

R22 introduces:

```text
DistributionalAgency =
ability to intentionally change the distribution/set
of meaningful future outcomes without selecting the exact realization.
```

Example:

```text
cover
→ hit chance decreases
```

The player does not choose whether the bullet misses, but changes the distribution.

## 27.2 Robust agency

Players may choose policies that perform acceptably across many possible states rather than optimize one forecast.

```text
robustness
```

is another form of agency under uncertainty.

## 27.3 Information agency

Players can choose to reduce uncertainty before acting.

```text
scout
inspect
ask
simulate
```

## 27.4 Agency is harmed when uncertainty overwhelms policy sensitivity

If all decisions produce nearly identical outcome distributions:

```text
ActionCausality ↓
```

and the game becomes luck-dominated at that timescale.

---

# 28. Skill–luck decomposition is scale-relative

A system can be:

```text
high luck per event
high skill over many events
```

Examples include many card and probabilistic strategy games.

## 28.1 Timescale matters

Ask:

```text
per action?
per turn?
per match?
per campaign?
across many matches?
```

## 28.2 Skill signal-to-noise

A useful conceptual relation:

```text
SkillSignal =
how much better policy shifts outcome distribution
relative to uncontrolled variation
```

Do not assume this needs one scalar metric in design.

## 28.3 Short sessions can intentionally increase luck

Luck can:

```text
create upset potential
maintain uncertainty
help weaker players occasionally win
create stories
```

but may reduce mastery attribution.

This is a trade-off, not a universal defect.

---

# 29. Randomness and tension

R7 defined:

```text
Tension = valued unresolved instability
```

Randomness can increase tension when:

```text
stakes matter
possible outcomes are legible enough
commitment exists
resolution is pending
```

But:

```text
More variance != More tension
```

Extreme opaque randomness can destroy anticipation because outcomes feel arbitrary.

A useful pattern:

```text
Known possibility space
+ uncertain realization
+ meaningful stake
+ limited control
→ anticipation
```

---

# 30. Strategic uncertainty

R19 adds another source:

```text
other Subjects choose policies
```

This uncertainty is not necessarily random.

## 30.1 Mixed strategy

A strategic Subject may deliberately randomize policy to remain unpredictable.

Here randomness is endogenous strategy, not environmental chance.

## 30.2 Type uncertainty

Opponent goals/capabilities/types may be unknown.

## 30.3 Policy uncertainty

Even known type may choose different actions.

## 30.4 Reputation reduces some uncertainty

History can make opponent policy more predictable, but overconfidence in reputation can be exploited.

Thus R13/R17/R19 converge:

```text
History
→ Belief
→ reduced/reshaped strategic uncertainty
```

---

# 31. Resource and economic risk

R14's resource model becomes dynamic under uncertainty.

Resources can be used to:

```text
absorb loss
buy information
hedge
insure
diversify
hold reserves
purchase optionality
```

## 31.1 Optionality matters under uncertainty

A resource is more valuable when it preserves future choices across multiple possible states.

## 31.2 Ruin changes everything

When loss destroys future participation/options:

```text
Risk is path-sensitive.
```

Mean return alone is inadequate.

## 31.3 Insurance converts distribution

Insurance does not eliminate uncertainty; it transforms consequence distribution by exchanging known cost for reduced downside.

This can be a playable economic mechanic.

---

# 32. Generative systems — sampling uncertainty versus epistemic uncertainty

Generative AI adds several uncertainty types that should not be merged.

## 32.1 Sampling variation

Same/similar prompt may produce different outputs because generation samples alternatives.

```text
SamplingUncertainty
```

## 32.2 Epistemic/model uncertainty

The model may not know a fact or may have weak evidence.

```text
KnowledgeUncertainty
```

## 32.3 Interpretation ambiguity

The user instruction may have multiple plausible meanings.

```text
SemanticAmbiguity
```

## 32.4 Tool/environment uncertainty

The model may not know current external state until observing it.

```text
ExternalStateUncertainty
```

## 32.5 These require different responses

```text
Sampling variation
→ maybe resample / constrain

Knowledge uncertainty
→ seek evidence / state confidence

Instruction ambiguity
→ infer cautiously / expose interpretation when consequential

External state uncertainty
→ observe authoritative source
```

One generic “confidence score” is insufficient.

---

# 33. Generated answer != authoritative truth

A major R22 AI rule:

```text
SampledOutput
!=
WorldTruth
```

This extends R17:

```text
Truth != Signal != Observation != Belief != Statement
```

For AI:

```text
World / Source Truth
→ retrieved evidence
→ model belief/inference
→ generated statement
```

## 33.1 False certainty is an information-policy failure

If a generative system presents weak inference as certain world state, epistemic uncertainty is erased from the surface but not reality.

## 33.2 Over-disclaimer is also poor design

Constant generic uncertainty warnings create noise.

Uncertainty communication should be:

```text
localized
consequence-sensitive
evidence-linked
```

## 33.3 AI game generation

Generated narrative/world outcomes can use stochastic variation, but authoritative causal state should remain exact where downstream consistency requires it.

```text
Surface variation
!= Semantic uncertainty
```

---

# 34. Fairness in generative / Agent systems

Agent systems introduce new fairness problems:

```text
unequal model quality
opaque inference
hidden tool access
inconsistent policy
non-repeatable judgment
biased information exposure
```

## 34.1 Procedural consistency

If the same authoritative rule should apply to all actors, a model's prose should not silently redefine it per case.

## 34.2 Bounded discretion

Some experiences intentionally want soft judgment.

Then fairness requires:

```text
scope of discretion
review/appeal where needed
consistent constraints
provenance
```

not pretending every outcome is deterministic.

## 34.3 Seed/replay evidence

For research/competitive contexts, retaining random seed or authoritative resolution evidence can make uncertain outcomes auditable without exposing hidden state prematurely.

---

# 35. Playable Uncertainty

R22 adds:

```text
PlayableUncertainty =
uncertainty whose relevant alternatives/sources can be
partially modeled, investigated, anticipated or acted around,
and whose resolution provides useful causal evidence.
```

Player need not know exact odds.

But they need enough structure to ask meaningful questions such as:

```text
What might happen?
What evidence changes my belief?
What can I do to reduce exposure?
What can I hedge?
Which uncertainty is irreducible?
```

## 35.1 Unplayable uncertainty

```text
unknown
+ no evidence
+ no mitigation
+ no stable distribution
+ no attribution after outcome
```

often feels arbitrary rather than tense.

---

# 36. Playable Risk

```text
PlayableRisk =
valued uncertain consequence exposure
that players can understand enough to choose,
mitigate, hedge, accept, reject or deliberately increase.
```

Risk is especially playable when there are meaningful operations on it:

```text
scout
insure
reserve
diversify
commit
retreat
reroll
seek information
```

## 36.1 Risk without agency

A random unavoidable catastrophe may create surprise but weak Risk gameplay.

## 36.2 Risk without exact probabilities

A dark forest can be risky through learned cues, even if no “23% wolf chance” is shown.

---

# 37. Minimum sufficient uncertainty complexity

Not a maturity ladder.

## UC0 — Deterministic / fully known local consequence

```text
state/action
→ predictable outcome
```

Uncertainty may still exist strategically elsewhere.

## UC1 — Hidden deterministic state

```text
world fixed
player belief uncertain
```

Examples:

```text
mystery
fog of war
hidden cards
```

## UC2 — Known stochastic resolution

```text
known/inferable distribution
→ random realization
```

Examples:

```text
dice
hit chance
random draw
```

## UC3 — Learnable model uncertainty

```text
probabilities/parameters initially uncertain
→ evidence updates model
```

## UC4 — Strategic / endogenous uncertainty

```text
other adaptive Subjects
+ hidden intent/type/policy
```

## UC5 — Multi-source uncertain ecology

```text
hidden state
+ stochastic transition
+ strategic Subjects
+ changing model
+ information acquisition/hedging
```

### Core rule

```text
UncertaintyComplexity should increase
only when it creates a new playable decision/inference/risk distinction.
```

---

# 38. Cross-form falsification tests

## 38.1 Chess

```text
Deterministic rules
No RNG required
High future uncertainty
High strategic uncertainty
```

Therefore:

```text
Uncertainty != Randomness
Determinism != Predictability
```

## 38.2 Poker

Combines:

```text
random deal history
hidden fixed cards
probability
strategic deception
risk management
```

After cards are dealt, much uncertainty is epistemic even though randomness created the hidden state.

## 38.3 Casefile / mystery

Culprit can be fully authored/fixed.

Uncertainty comes from evidence distribution and belief.

Deep uncertainty needs no stochastic truth.

## 38.4 Roguelike random map

Randomness before many decisions can create adaptation and replay variation.

Once map region is revealed, uncertainty converts into known topology.

## 38.5 XCOM-like hit probability

Player chooses position/target before post-commit stochastic hit resolution.

Skill lies partly in changing distributions and planning for misses, not guaranteeing shots.

A 95% miss can be:

```text
unlucky
painful
mechanically fair
```

if odds/process are truthful.

## 38.6 Fighting game

Typically low explicit RNG but high uncertainty from opponent policy, timing and imperfect prediction.

This refutes “competitive uncertainty requires randomness.”

## 38.7 Party game

Large luck contribution may be intentional to create upset potential, stories and accessibility.

Low skill attribution is not automatically a defect.

## 38.8 Deckbuilder

Random draw occurs before many decisions.

Skill can include deck construction that changes future draw distributions.

This is DistributionalAgency.

## 38.9 Loot system

Reward randomness after action can produce anticipation, but if reward variance dominates all progression it can weaken ActionCausality and fairness.

## 38.10 Strategy with fog of war

No stochastic combat is required for strong risk; hidden enemy state creates epistemic uncertainty and information-value gameplay.

## 38.11 Economy / market

Price uncertainty can arise from other Subjects, exogenous shocks and hidden information.

Risk management, optionality and diversification can be player skills.

## 38.12 Social deduction

Uncertainty is primarily about Subject roles/statements/policies.

Probability may be implicit rather than numerical.

## 38.13 AI companion

Player uncertainty can concern:

```text
how command will be interpreted
what plan Agent chooses
whether tool state changed
```

This is not the same as random output generation.

## 38.14 Generative narrative

Surface text sampling may vary while canonical semantic state stays deterministic/hard.

This can provide variation without destabilizing causal history.

## 38.15 Procedurally generated world

A seed can make the entire world deterministic before play while the player experiences exploration uncertainty.

Canonical example:

```text
World deterministic
Player epistemically uncertain
```

---

# 39. Major collapse / failure modes

## 39.1 Uncertainty = randomness collapse

Failure: every unknown is solved with RNG.

Result: mystery/strategy/model uncertainty replaced by noise.

## 39.2 Randomness = unpredictability collapse

Failure: deterministic complex systems misclassified as random.

Result: wrong debugging and wrong player-facing explanation.

## 39.3 Determinism = predictability collapse

Failure: because seed/rules are fixed, assume players can forecast outcomes.

Result: bounded cognition/information ignored.

## 39.4 Probability = truth collapse

Failure: one model's 70% displayed as ontological fact.

Result: model uncertainty/provenance disappears.

## 39.5 Exact percentage = legibility collapse

Failure: assume every uncertainty needs numeric odds.

Result: mystery/fantasy/UI quality can degrade.

## 39.6 Risk = probability collapse

Failure: 1% and 90% only compared by chance without consequence magnitude.

Result: stakes disappear.

## 39.7 Risk = variance collapse

Failure: symmetric dispersion used as universal downside measure.

Result: tails/skew/ruin ignored.

## 39.8 Expected value = decision quality collapse

Failure: highest mean always labeled best.

Result: constraints, risk preference, ruin and ambiguity ignored.

## 39.9 Outcome = decision quality collapse

Failure: lucky win proves smart choice; unlucky loss proves bad choice.

Result: players learn noise.

## 39.10 Luck = randomness collapse

Failure: only RNG can create luck.

Result: exogenous deterministic/strategic contingency ignored.

## 39.11 Randomness = unfairness collapse

Failure: any chance is considered unfair.

Result: fair lotteries, card games and adaptation systems misclassified.

## 39.12 Fairness = equal outcome collapse

Failure: unequal result automatically unfair.

Result: competition and fair lotteries become impossible to describe.

## 39.13 Fairness = symmetry collapse

Failure: asymmetric roles automatically unfair.

Result: legitimate compensated asymmetry ignored.

## 39.14 Fairness = balance collapse

Failure: equal win rate means fair process.

Result: hidden manipulation can pass as fairness.

## 39.15 Statistically fair = perceived fair collapse

Failure: mathematically correct RNG assumed self-explanatory.

Result: streak perception and causal opacity ignored.

## 39.16 Pity system = true randomness collapse

Failure: streak-control system described as independent RNG.

Result: player mental model becomes false.

## 39.17 More variance = more tension collapse

Failure: increase outcome spread mechanically.

Result: arbitrary chaos rather than anticipation.

## 39.18 More uncertainty = more depth collapse

Failure: hide information without adding inference/mitigation.

Result: blind guessing.

## 39.19 Reveal everything = fairness collapse

Failure: eliminate uncertainty to make rules “clear.”

Result: mystery, bluffing and exploration die.

## 39.20 Hidden odds manipulation

Failure: probabilities change secretly while UI implies stability.

Result: calibration and procedural trust break.

## 39.21 One sample = probability evidence collapse

Failure: event occurred, therefore forecast was wrong.

Result: probability reasoning impossible.

## 39.22 Random reward dominates action

Failure: outcome variance overwhelms policy effect.

Result: ActionCausality and mastery attribution collapse.

## 39.23 Bad-luck protection without semantic model

Failure: hidden pity changes odds but players reason as independent samples.

Result: behavior/expectation mismatch.

## 39.24 Generative sampling = knowledge uncertainty collapse

Failure: model can produce variants, therefore it “doesn't know.”

Result: sampling and epistemic uncertainty confused.

## 39.25 Model confidence = world truth collapse

Failure: generated confidence treated as authority.

Result: hallucination becomes world state.

## 39.26 Constant uncertainty disclaimers

Failure: every AI statement wrapped in generic caveats.

Result: signal drowned; consequence-sensitive uncertainty not communicated.

## 39.27 Skill = guaranteed success collapse

Failure: if good player can still lose, system considered unskilled.

Result: probabilistic strategic skill misunderstood.

## 39.28 Luck = no agency collapse

Failure: any uncontrolled contribution negates meaningful decisions.

Result: distributional agency ignored.

## 39.29 Entropy = fun collapse

Failure: maximize information entropy as engagement proxy.

Result: stakes, meaning and learnability ignored.

## 39.30 Random generation = replayability collapse

Failure: more seeds/content assumed to create replay value.

Result: many equivalent worlds with little new decision structure.

---

# 40. R22 connections back to R1–R21

## R1 — GameForm

Randomized/procedural content is only one uncertainty source. Time, information, strategy, control and World state can create uncertainty without RNG.

## R2 / R5 / R6 — Player Value

Uncertainty can support curiosity, tension, mastery, surprise, story and replayability; none scale automatically with entropy/variance.

## R3 — Mechanics

A mechanic can expose deterministic or stochastic resolution. Random resolution should be modeled as one causal stage, not as a synonym for mechanic depth.

## R4 — Loops

Uncertainty turns loops into repeated belief/update structures:

```text
Belief → Choice → Realization → Feedback → Belief update
```

## R7 — Tension

R7's “Randomness is only one subset of uncertainty” is preserved. R22 replaces the overly general `Risk ≈ ProbabilityOfLoss × SubjectiveValueOfLoss` heuristic with distributional risk exposure.

## R8 — Narrative

Narrative suspense can come from epistemic uncertainty about fixed truth; generated plot randomness is optional.

## R9 — World

World authority may be deterministic or stochastic. Player uncertainty belongs to observer/model state, not automatically World truth.

## R10 — Subject / Agent

Subjects may hold beliefs/distributions/ambiguity about state and other policies. They need not maximize expected value.

## R11 — Agency

Uncertainty shifts agency from selecting exact outcome toward changing distributions, information and exposure.

## R12 — Feedback / learning

Probabilistic systems need causal/probability feedback sufficient for calibration without necessarily exposing all hidden information.

## R13 — History

History provides samples and reputation evidence but small samples can mislead. Repeated outcomes can update beliefs or create false streak narratives.

## R14 — Resource

Reserves, insurance, diversification and optionality transform consequence distributions under uncertainty.

## R15 — Institution

Institutions can reduce uncertainty by stabilizing expectations and can define fair procedures for lotteries, disputes and risk sharing.

## R16 — Topology

Unknown map regions are epistemic uncertainty. Hazard distribution across space creates risk topology.

## R17 — Information

R22 is deeply dependent on R17: uncertainty is always relative to truth/signal/observation/belief boundaries.

## R18 — Motivation / utility

Expected value and utility remain representations, not universal motivation. Risk/ambiguity preference can be contextual and multi-objective.

## R19 — Strategy

Opponent-policy uncertainty is endogenous and may involve deliberate mixing, bluffing and reputation.

## R20 — Creation

Generative variation can introduce creative possibilities but also sampling/evaluation uncertainty. More generated variance is not more creativity.

## R21 — Control

ActionCausality under uncertainty becomes distributional: player intent can change odds without choosing the sample. Outcome attribution must separate choice from chance.

---

# 41. New high-yield abstractions

## 41.1 Uncertainty Topology

```text
Who is uncertain
about what
from which source
at which model boundary
with what reducibility
revealed when
and controllable how?
```

## 41.2 Outcome Contribution Topology

```text
Which factors shaped this outcome:
choice / skill / opponent / hidden state / random draw / system dynamics / information?
```

## 41.3 Distributional Agency

```text
Player can change outcome distributions
without selecting exact realization.
```

## 41.4 DecisionQuality != OutcomeQuality

Evaluate choice using information/constraints available before realization, not one lucky/unlucky sample.

## 41.5 Skill shifts distributions

```text
Skill under uncertainty
= systematically improve outcome distributions / decision quality,
not guarantee every sample.
```

## 41.6 Randomness placement matters

```text
before decision → adaptation context
after commitment → risk-bearing resolution
during control → disturbance/correction
```

## 41.7 Risk is distributional

```text
Risk = valued exposure to uncertain consequence distributions
```

not one probability×loss scalar.

## 41.8 Uncertainty Contract

Players learn what is hidden/random/learnable/control-sensitive and judge fairness relative to that contract.

## 41.9 Fairness is plural

```text
procedural
opportunity
informational
causal/skill
distributive
perceived
```

must not be collapsed.

## 41.10 Model-relative randomness

A PRNG game can be deterministic under full engine state and stochastic under the player-facing model.

## 41.11 Playable Uncertainty

```text
Unknown becomes game structure when players can model/investigate/act around it.
```

## 41.12 Sampled output is not truth

Generative variation, epistemic uncertainty and semantic ambiguity require different treatment.

---

# 42. Direct answers to the R22 continuation questions

### What distinguishes uncertainty, ignorance, probability and randomness?

Uncertainty is openness among plausible alternatives relative to a perspective. Ignorance is missing relevant knowledge/model structure. Probability is a quantitative representation over alternatives. Randomness is one mechanism/source by which alternatives are realized under a model.

### What distinguishes epistemic and aleatory uncertainty?

Epistemic uncertainty comes from missing knowledge/state/model and may be reducible. Aleatory uncertainty is variability represented as irreducible inside the current model. The classification can change with model boundary and information.

### Can deterministic systems be unpredictable?

Yes. Hidden state, strategic opponents, computational complexity and chaotic sensitivity can make a deterministic future impractical to forecast for bounded players.

### What is Risk?

Exposure to materially valued consequence distributions under uncertainty, particularly downside. Probability, severity, tails, reversibility, correlation, controllability and ambiguity may all matter.

### What is Luck?

A retrospective attribution that a valued realized outcome depended materially on factors outside the relevant participant's control/skill/knowledge. It does not require a literal RNG call.

### How do random input and random output differ?

Randomness realized before decision tends to create an adaptation problem; randomness resolved after commitment tends to create a risk-bearing problem. Hidden pre-existing state creates inference/scouting problems. Continuous noise creates control/robustness problems.

### Why is Expected Value insufficient?

It is only a mean. It discards variance, skew, tails, ruin thresholds, path dependence, reversibility and Subject-specific values.

### When does randomness destroy agency?

When uncontrolled variation dominates policy sensitivity at the timescale that matters, so meaningful decisions barely change outcome distributions and failures cannot be attributed/learned from.

### How can skill exist with luck?

Skill can improve distributions, reduce ruin, manage variance, gather information and adapt after realization even though any individual sample can still go badly.

### What is Fairness relative to symmetry/equality/balance?

Fairness is a normative/process judgment. Symmetry means identical structures; equality means similar outcomes; balance concerns relative viability/power. They can support fairness but are neither necessary nor sufficient.

### Can a bad outcome be fair?

Yes. A known fair procedure can generate an unlucky adverse result. Procedural fairness and outcome quality are separate.

### How should uncertainty be exposed without percentages everywhere?

Through consistent cues, ranges, histories, evidence, qualitative confidence and post-resolution feedback sufficient for player calibration at the intended abstraction level.

### How should generative systems represent uncertainty?

Separate sampling variation, knowledge uncertainty, instruction ambiguity and unknown external state. Seek evidence for epistemic gaps, constrain/resample sampling variation, and do not convert generated confidence into authoritative truth.

### How does R22 connect to R21 ActionCausality?

Under uncertainty, participant action may change the **distribution** rather than choose the exact outcome. ActionCausality therefore becomes compatible with chance: the player can causally improve odds while still losing a realization.

---

# 43. Explicit non-conclusions

R22 does **not** establish that:

- every game needs randomness;
- uncertainty requires RNG;
- deterministic games are predictable;
- stochastic games are necessarily unpredictable;
- epistemic uncertainty is always reducible in practice;
- aleatory uncertainty is metaphysically irreducible;
- exact probabilities must be shown;
- expected value is useless;
- highest expected value is always best;
- variance is always bad;
- lower variance is always safer in every relevant sense;
- random outcomes are unfair;
- equal outcomes are fair;
- symmetric games are automatically fair;
- balanced win rates prove procedural fairness;
- a good decision should always win;
- a bad decision cannot win;
- one outcome is enough to evaluate a probability forecast;
- luck implies absence of skill;
- skill implies absence of luck;
- more randomness means more replayability;
- more variance means more tension;
- more entropy means more fun;
- pity systems are inherently deceptive;
- hidden information is unfair;
- generative sampling means the model lacks knowledge;
- model confidence is authoritative reality;
- every AI uncertainty should become a visible numeric confidence score.

The governing criterion remains player-facing causal value.

---

# 44. R22 synthesis

The deepest compression of R22 is:

```text
Uncertainty is not randomness.

Uncertainty exists whenever, for a specified participant/model/time,
more than one materially plausible state, model or outcome remains open.
```

Randomness is only one source/representation of that openness.

The compact uncertainty stack is:

```text
World / Model / Hidden State
        ↓
Signals / Evidence
        ↓
Belief / Probability / Ambiguity
        ↓
Choice / Policy
        ↓
Exposure to Consequence Distribution
        ↓
Realization
        ↓
Outcome
        ↓
Attribution:
Skill? Choice? Opponent? Hidden State? Chance?
        ↓
Learning / Calibration / New Belief
        ↺
```

R22's strongest action rule is:

```text
Do not evaluate uncertain decisions by one realized sample.
```

The strongest agency rule is:

```text
Under uncertainty, agency often means changing distributions,
information and exposure — not selecting exact outcomes.
```

The strongest fairness rule is:

```text
A fair process can create an unequal or unlucky outcome.
An equal outcome can come from an unfair process.
```

The strongest generative-system rule is:

```text
Sampling variation
!= Knowledge uncertainty
!= Instruction ambiguity
!= Unknown external state
```

R22 adds:

```text
UncertaintyTopology
OutcomeContributionTopology
DistributionalAgency
UncertaintyContract
PlayableUncertainty
PlayableRisk
```

to the foundation vocabulary.

---

# 45. Unresolved questions left by R22

With uncertainty isolated, one major GameForm dimension remains conspicuously under-modeled: **Time**.

Important unresolved questions include:

1. What is Game Time relative to real/world/simulation/player time?
2. What is Sequence, and when does order itself create causality or strategy?
3. How do simultaneity, turn-taking, phases, ticks and asynchronous action differ?
4. What is Duration relative to timing and pace?
5. What is Tempo relative to action frequency, decision density and world speed?
6. What is Rhythm, and how can patterned timing create skill/expectation beyond average speed?
7. What are cooldowns, wind-up, recovery and commitment windows as temporal constraints?
8. How do deadlines and time pressure alter choice rather than merely increase difficulty?
9. What is initiative/turn order, and when does first-move/last-move advantage emerge?
10. How should concurrent actions be resolved fairly and causally?
11. What is waiting as a meaningful action versus dead time?
12. How do persistence/offline progress/asynchrony alter agency and social coordination?
13. How do temporal reversibility, undo, rewind and save/load change commitment and consequence?
14. How should Agent systems operate across continuous real time, turns and asynchronous long-horizon tasks?
15. How do latency and response time from R21 differ from game-world temporal structure?
16. How do probability and risk evolve through time — hazard rate, deadlines, decay and information arrival?

---

# 46. Exact next foundation round

The next foundation round should be:

```text
R23 — Time, Sequence, Simultaneity, Duration, Timing, Rhythm, Turn, Cooldown, Deadline and Temporal Agency
```

The transition is:

```text
R22:
What changes when future states and outcomes cannot be known exactly?

→ R23:
How are actions and consequences ordered through time,
and how does temporal structure itself create choice, skill, coordination and commitment?
```

This round should connect R4 loops, R7 pacing/time pressure, R13 history/persistence, R19 repeated interaction, R21 responsiveness and R22 risk without collapsing Time into real-time action speed.

Do not select a product before R23 and the remaining obvious foundation dimensions have been examined and later synthesized.
