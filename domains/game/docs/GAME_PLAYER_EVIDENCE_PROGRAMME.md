---
schema_version: 1
id: game.player-evidence-programme
title: Ordivon Game — Player Evidence Programme
profile: research
lifecycle: active
source_role: canonical-supporting-model
visibility: public
owners:
  - ordivon-game
updated: 2026-08-28
summary: Practical evidence ecology for deciding which player, population, synthetic, expert, telemetry, qualitative or experimental evidence can support which game-development claim. Separates evidence subject, method, measure, claim, horizon, transport scope and authority rather than treating Human-vs-Machine or playtest-passed as sufficient evidence semantics.
evidence_status: derived
readiness: CURRENT
applies_to:
  - ordivon-game
related:
  - game.development-core
  - game.development-case-pressure-tests
  - game.content-progression-architecture
---
# Ordivon Game — Player Evidence Programme

## 0. Boundary

This model exists to answer:

> What evidence should change the current development decision, and how far may that evidence legitimately generalize?

It does not create a Human model, player database, analytics service, recruitment service or universal research bureaucracy.

```text
PlayerEvidenceProgramme
!= HumanTruthStore
!= TelemetryPlatform
!= ResearchDepartment
!= ProductAuthority
```

The strongest correction is:

```text
EvidenceSubject != Method != Measure != Claim
```

Examples:

```text
Human subject + telemetry method + completion measure
!= enjoyment claim

Human subject + interview + stated purchase intent
!= future purchase behavior

Synthetic Agent + completion measure
!= Human difficulty identity

Randomized player experiment + D7 retention
= causal evidence about that intervention's D7 effect in the sampled/eligible population
!= proof that the game became more fun
```

## 1. Start from the decision, not the available data

Every evidence activity should begin with a blocked or revisable decision.

```text
DecisionToInform
→ ClaimNeeded
→ EvidenceSubject / Population
→ Method
→ Measure / Observation
→ Analysis
→ ScopedStanding
→ Decision
→ ReopenCondition
```

This deliberately rejects:

```text
we have telemetry → find a story
we have a community → send a survey
we have Agents → simulate players
we reached G4 → run a playtest
```

Mature Games User Research independently emphasizes selecting a method from a concrete research objective rather than convenience, and distinguishes measurement from understanding as well as behaviour from opinion.

## 2. Claim families

Do not ask whether evidence is simply “Human” or “real.” Name the claim.

### C1 — Usability / Actionability

Questions such as:

```text
Can the target player do what they intend?
Can they find the relevant control/path/object?
Where do they become blocked?
```

Strong carriers:

- observed target-player behaviour;
- task success/failure and interaction traces;
- contextual interview after/around the event;
- expert analysis as prior/hypothesis generation, not player evidence by identity.

### C2 — Understanding / Mental Model / Learning

Questions such as:

```text
What does the player think happened?
Do they understand the rule/cause/objective?
Can they predict what should happen next?
Does learning retain or transfer later?
```

Strong carriers may require:

- observed action under a situation that requires the distinction;
- careful probing/interview;
- prediction/explanation tasks;
- delayed retention/transfer when the claim is learning rather than immediate performance.

Important:

```text
ImmediatePerformance != Learning
PracticeSuccess != Retention
Retention != Transfer
```

This reuses GDF1/GDF2 learning/skill evidence boundaries rather than creating another learning ontology.

### C3 — Experience / Appeal / Meaning

Questions such as:

```text
Was this tense, satisfying, confusing, boring, expressive, moving, funny, attached, curious?
Does the experience match the intended fantasy/value?
```

Relevant evidence includes:

- Human self-report;
- behaviour interpreted in context;
- observation + careful interview;
- validated survey instruments where appropriate;
- longitudinal/return behaviour only as a separate behavioural signal.

Strong guard:

```text
BehaviourProxy != PhenomenologicalTruth
Retention != Fun
SessionLength != Enjoyment
Purchase != Love
```

No machine trajectory can directly close this claim family.

### C4 — Balance / Challenge / Strategy / Fairness

Questions such as:

```text
Which strategies dominate?
Who succeeds under which condition?
Does one faction/build/weapon systematically outperform another?
How does challenge change across target populations?
```

Useful evidence can combine:

- deterministic simulation;
- synthetic policies/Agents;
- Human play traces;
- telemetry at scale;
- controlled parameter/variant experiments.

But preserve:

```text
AggregateWinRate != Mechanism
ObservedDifficulty != IntrinsicDifficulty
SelectedPopulation != TargetPopulation
FairOutcomeRate != PerceivedFairness
```

This reuses the GDF2 population-selection/identifiability findings.

### C5 — Population Behaviour / Ecology

Questions such as:

```text
Where do players churn?
What routes/modes/builds are used?
Who returns on D1/D7/D30?
How does behaviour vary by platform/cohort/history?
```

Telemetry/analytics is strong for scale and distribution.

It is primarily descriptive unless an intervention design supports causal identification.

### C6 — Population Causal Effect

Questions such as:

```text
Did changing onboarding X cause a change in retention Y?
Did matchmaking variant A alter session completion?
Did price/configuration treatment change conversion?
```

Randomized/controlled field experiments are strong carriers when eligibility, assignment, intervention, metric, exposure and analysis are valid.

Roblox and PlayFab both operationalize this regime through controlled variants and telemetry.

Strong guard:

```text
Intervention → MetricEffect
!=
Intervention → PlayerValue by identity
```

Interpretation still needs a product-value claim and often qualitative follow-up.

### C7 — Accessibility / Population-Specific Fit

Questions such as:

```text
Can a relevant player population perceive, control, understand and complete the intended interaction under its actual access conditions?
```

The target population is constitutive of the claim. Evidence from an unrelated population does not transport automatically.

Accessibility is not one after-the-fact checklist; it may constrain D2/D3/D6 from early development.

## 3. Evidence carrier taxonomy

### E1 — Expert / heuristic analysis

Subject: expert/researcher, not target player.

Good for:

- identifying probable usability/understanding risks;
- generating hypotheses;
- catching known design failures before recruitment;
- prioritizing what to test.

Does not prove:

```text
TargetPlayerActuallyFails
TargetPlayerActuallyUnderstands
TargetPlayerActuallyFeelsX
```

Player Research explicitly treats expert analysis as an early, design-intent-relative method that should sit in a broader mixed-method programme.

### E2 — Observed Human play

Strong for actual behaviour in the test context:

```text
what they did
where they stopped
what they selected
what they failed/succeeded at
```

Weak alone for latent explanation:

```text
why they did it
what they believed
what they felt
```

Observation is therefore often paired with careful probing.

### E3 — Human interview / contextual probe

Strong for:

- current interpretation;
- remembered rationale;
- expectations;
- meaning;
- subjective experience.

Risks:

```text
question-induced attention
post-hoc rationalization
social desirability
memory error
prediction-of-future-behaviour error
```

A player's statement is evidence about the player's report/worldview, not automatic truth about the causal mechanism or future behaviour.

### E4 — Survey / psychometric self-report

Strong for quantitative self-report when instrument, sampling and context are appropriate.

It measures reported experience/opinion, not observed behaviour.

Sample size and statistical precision matter for measurement claims, but:

```text
LargeN != ValidQuestion
LargeN != RepresentativePopulation
LargeN != CausalIdentification
```

### E5 — Human telemetry / analytics

Strong for:

- distributions;
- funnels;
- usage;
- completion/failure;
- retention/churn;
- cohort/platform/version differences;
- large-horizon behaviour.

Weak alone for why.

Games User Research guidance explicitly recommends pairing measured results with research insight when explanation is needed.

### E6 — Controlled Human experiment

Strong for scoped causal effects when:

```text
eligibility/population
assignment
intervention
exposure
metric
analysis
version/currentness
```

are valid.

Examples include lab experiments, matched treatments and live A/B tests.

Causal scope remains the intervention + measure + sampled population/context.

### E7 — Longitudinal Human evidence

Required when the claim itself concerns:

```text
learning
retention/transfer
habit
relationship
long-horizon progression
cross-session meaning
```

A one-session study cannot establish a months-long claim by narrative extrapolation.

### E8 — Synthetic policy / Agent / simulation

Strong for:

- reachability;
- invariant violations;
- degenerate strategies;
- combinatorial coverage;
- causal mechanism probes;
- relative parameter sensitivity;
- automated regression;
- some calibrated relative-difficulty predictions.

Unity ML-Agents explicitly lists automated build testing and pre-release design evaluation among its uses.

But:

```text
SyntheticSubject != HumanSubject
SyntheticCompletion != HumanUsability
SyntheticPreference != HumanPreference
SyntheticDifficulty != HumanDifficulty by identity
```

Synthetic evidence is not “worse Human evidence.” It is a different evidence carrier.

### E9 — Community / naturalistic qualitative evidence

Examples:

- support tickets;
- forums/social/community discussions;
- reviews;
- creator feedback;
- open beta feedback.

Strength:

- ecological context;
- unprompted issues;
- long-horizon phenomena;
- rare edge cases.

Risks:

- self-selection;
- unknown denominator;
- vocal-minority effects;
- version/context ambiguity;
- strategic/performative communication.

Use as discovery/triangulation unless the sampling structure justifies stronger inference.

## 4. The Player Evidence Contract

A material study or evidence read should be able to expose:

```text
PlayerEvidenceContract =
DecisionToInform
+ ClaimFamily
+ ClaimStatement
+ EvidenceSubject
+ TargetPopulation / Context
+ Recruitment / Eligibility
+ GameVersion / Condition
+ EvidenceHorizon
+ Method
+ Intervention / Control when applicable
+ Measures / Observations
+ SamplePlan
+ AnalysisPlan
+ DecisionRule
+ TransportScope
+ KnownBias / Limitation
+ Provenance
+ ResultStanding
+ ReopenCondition
```

Do not persist this universally by default. It is an operation-relative view until repeated workflow pressure justifies an executable store.

## 5. Result standing is scoped, not a scalar grade

Use claim-local standing such as:

```text
SUPPORTED_WITHIN_SCOPE
CONTRADICTED_WITHIN_SCOPE
INCONCLUSIVE
NOT_IDENTIFIED
NOT_OBSERVED
STALE_TO_VERSION
TRANSPORT_UNRESOLVED
```

Avoid:

```text
EvidenceScore = 87/100
```

because evidence can be strong for one claim and irrelevant for another.

Example:

```text
A/B test:
D1 retention +8% with valid randomization

SUPPORTED_WITHIN_SCOPE:
causal D1 metric effect for eligible population/version/window

NOT_IDENTIFIED:
why the effect occurred
whether enjoyment increased
whether D30 improved
whether another population would respond similarly
```

## 6. Sample size is decision-relative

There is no universal “correct number of playtesters.”

Games User Research practice offers pragmatic starting points such as small repeated qualitative rounds for discovering usability problems and larger samples for measurement, while explicitly warning against magic-number use.

Current rule:

```text
SamplePlan = f(
Claim,
PopulationHeterogeneity,
Method,
ExpectedEffect / issue prevalence,
PrecisionNeeded,
DecisionCost,
EvidenceHorizon,
PracticalBudget
)
```

Important distinctions:

```text
SmallN qualitative discovery
!= population prevalence estimate

LargeN survey
!= deep causal explanation

One repeated severe usability defect
may justify repair
without population prevalence inference
```

Iteration often dominates one giant early test: fix clear problems, then retest the changed reality.

## 7. Population transport and selection

Every Human/population finding is conditional on who was able and willing to produce the evidence.

Track where material:

```text
Population / cohort
platform/device
region/language
prior genre/game experience
accessibility needs
skill/capability history
session history
social configuration
assistance/settings
version/build
survivorship / earlier churn
```

Critical law inherited from GDF2:

```text
PopulationAtLateContent
is selected by earlier game/history.
```

A level's observed completion rate among survivors cannot be transported to all new players without analysis.

## 8. Evidence horizon must match the claim horizon

Reuse D4/D5:

```text
interaction
encounter
session
run
campaign
cross-session
population/time-window
```

Examples:

```text
Can player find Dash button?       → interaction
Does boss teach mechanic?          → encounter/session
Does knowledge structure cohere?   → campaign
Does practice transfer tomorrow?   → cross-session
Does onboarding alter D7?          → population/time-window
```

Do not stop a study before the claimed phenomenon could exist.

## 9. Mixed methods are claim decomposition, not ritual triangulation

Do not add methods merely to say a study is “mixed.”

Use complementary carriers when the decision requires different claims:

```text
Telemetry: where are players leaving?
Observation: what happens immediately before leaving?
Interview: what did they think/expect?
Experiment: does treatment X causally change the target metric?
```

The methods answer different questions.

```text
Convergence across methods
can strengthen a causal/product interpretation,
but disagreement is information rather than a study failure.
```

## 10. Pre-study falsification and post-study interpretation

Before evidence collection, name:

```text
what result would change the decision?
what result would not be interpretable?
what known confound would force a rerun?
```

After collection, preserve:

```text
ObservedData
!= Finding
!= Interpretation
!= Decision
```

This mirrors Ordivon's broader owner-truth/projection/decision separation.

## 11. Agent roles in player evidence

Agents can provide major leverage in:

```text
research-objective decomposition
study-plan drafting
instrument/telemetry schema review
participant-session logistics support
transcription
trace alignment
qualitative coding proposals
anomaly detection
cluster/segment proposal
statistical analysis assistance
experiment monitoring
report drafting
retrieval of historical evidence/currentness
```

They can also act as E8 synthetic subjects.

But these are different roles.

```text
ResearchAgent != SyntheticPlayer
AnalyticsAgent != MetricAuthority
ExperimentAgent != ProductDecisionAuthority
```

Agents must preserve provenance to raw evidence and must not silently upgrade:

```text
correlation → causation
report → behaviour
proxy → experience
synthetic → Human
sample → population
old build → current build
```

## 12. Metric authority boundary

Roblox and PlayFab demonstrate increasingly mature experimentation infrastructure: random assignment, variant exposure and outcome telemetry can be operationalized at platform scale.

This creates a stronger need, not a weaker need, for metric semantics.

For each product metric, record conceptually:

```text
MetricName
OperationalDefinition
WhyItMatters
KnownGoodhartRisk
ExpectedTimeHorizon
AffectedPopulation
Countermetrics / Guardrails
InterpretationOwner
```

Examples:

```text
D1 retention
may indicate early product fit / onboarding success
but can also increase through compulsion, social lock-in, notification pressure or other mechanisms.
```

Therefore:

```text
OptimizeMetric
requires
ValueInterpretation + Guardrails
```

not metric maximization by default.

## 13. Development-stage examples without stage authority

### Early concept / preproduction

Useful questions:

- does the target context/problem/fantasy resonate?
- what do prospective players already understand or expect?
- does a cheap prototype expose the intended distinction?

Methods may include interviews, contextual research, concept tests, expert review and small observed prototypes.

### Playable / content construction

Useful questions:

- where do players misunderstand or fail?
- what is actually learned?
- which mechanics are underused?
- does content sequence create intended transfer?

Methods may combine observation, interviews, telemetry, repeated qualitative rounds and synthetic structural probes.

### Late production / beta

Useful questions:

- balance distributions;
- broad appeal/ratings;
- accessibility fit;
- performance across target hardware/population;
- long-session/campaign issues.

Larger quantitative or multi-seat/unmoderated evidence may become appropriate.

### Live / population ecology

Useful questions:

- churn/retention distributions;
- cohort differences;
- causal impact of configuration changes;
- unexpected community meaning/use;
- long-horizon progression/economy.

Telemetry, field experiments and qualitative follow-up become complementary.

No stage mandates one method.

## 14. Current Ordivon consequence

1. Replace generic `C0 Human Canary` as the default operational language with claim-specific Player Evidence Contracts; retain C0 only as historical evidence boundary where referenced.
2. Do not create a player-research database yet.
3. Do not prescribe universal sample sizes in owner authority.
4. Do not require Human evidence for structural questions that synthetic/formal methods can answer better.
5. Do require relevant Human evidence before claiming Human experience, meaning, learning or accessibility fit.
6. Do not let telemetry scale upgrade observational correlation into causality.
7. Do not let randomized metric causality upgrade into Player Value interpretation.
8. Preserve version/currentness and population transport explicitly for any evidence that can change a product decision.
9. Prefer mixed evidence only when the decision genuinely contains multiple claim families.
10. Existing local Game experiments remain apparatus; no new local playable is justified by this programme.
