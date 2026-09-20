---
schema_version: 1
id: game.deep-foundations.gdf2-c
title: Ordivon Game Deep Foundations — GDF2-C Challenge Surface Operationalization & Identifiability
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Tests whether GDF2-B's CapabilityOutcomeSurface is empirically/structurally identifiable. Demonstrates observational equivalence under aggregate pass rates, population-selection reversals, logistic gauge equivalence, hidden heterogeneity versus within-controller randomness, multidimensional capability compensation, average-assistance ambiguity and opponent-matrix ambiguity. Demotes CapabilityOutcomeSurface from latent Game object to a probe-relative research model family and introduces explicit observation/intervention designs, identified claims, equivalence classes and identification status. Recovery is reconstructed as authoritative RecoveryTransitionSet plus query-specific cost projection. No frozen foundation reopen is triggered.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf2-b
  - game.action-control-skill-foundations.v1
---
# Ordivon Game Deep Foundations — GDF2-C

## 0. C's attack

B replaced one scalar `difficulty` with a richer response-surface model.

That creates a new danger:

> Have we discovered a useful Game relation, or merely invented a latent object that any finite dataset can be fitted to after the fact?

C therefore asks a stricter question:

```text
What properties of challenge are actually identifiable
from which observations and interventions?
```

Canonical artifacts:

```text
evidence/gdf2-c/identifiability-model.json
evidence/gdf2-c/identifiability-probes.json
scripts/gdf2-c/identifiability-probes.mjs
scripts/gdf2-c/audit-identifiability.mjs
```

---

# 1. CapabilityOutcomeSurface is not directly observed

B wrote:

```text
P(relevant outcome | SkillProfile/policy, ChallengeConditionSpec)
```

as a useful conceptual surface.

C now demotes its ontological status.

In real data we normally observe only sparse projections such as:

```text
pass/fail
score
trajectory
completion time
population aggregate
selected policy runs
```

and we rarely observe the complete SkillProfile, exogenous process, hidden history, opponent policy state and counterfactual outcomes simultaneously.

Therefore:

```text
CapabilityOutcomeSurface
!= directly observed Game object.
```

It is a **research model family** constrained by probes.

---

# 2. Aggregate pass rate has severe observational non-identifiability

C's first executable counterexample constructs two radically different latent relations.

Model A:

```text
steep capability-sensitive response curve
+ symmetric population around the threshold
```

Model B:

```text
flat P(success)=0.5
independent of capability
```

Both produce:

```text
aggregate pass rate = 50%.
```

Therefore:

```text
AggregatePassRate
does not identify
CapabilityThreshold / Discrimination / SkillDependence.
```

The same observed statistic is compatible with different mechanisms.

---

# 3. Population selection can reverse apparent difficulty ordering

Suppose:

```text
Level Easy
→ seen by a broad novice-heavy population

Level Hard
→ only reached by selected experts
```

The hard level can show a **higher observed pass rate** than the easier level.

The executable probe creates exactly this reversal.

When both surfaces are re-evaluated under a shared reference capability distribution, the expected ordering returns.

Thus:

```text
ObservedPassRate
=
ChallengeRelation × SelectedPopulation/HistoryProjection
```

not content difficulty.

This matches external automated-playtesting work showing that modeling the evolving player population—skill, persistence and earlier churn—improves difficulty/churn prediction because the population reaching later levels is selected rather than fixed.

---

# 4. This gives us a new required object: ChallengeObservationDesign

Any empirical difficulty/challenge claim must state at least enough of:

```text
which outcomes were observed
which population/policy family was sampled
selection/censoring rules
whether trials repeat within the same controller
capability proxies or known synthetic policy identities
seed/exogenous control
opponent distribution
mapping/assistance configuration
history/knowledge state
```

Otherwise a fitted challenge parameter can be impossible to interpret.

# **ChallengeObservationDesign**

is therefore an evidence contract, not a Game ontology primitive.

---

# 5. Even response-model coordinates have gauge freedom

IRT itself provides an important epistemic warning.

Location/ability and discrimination parameters are not automatically absolute physical coordinates.

In common response models, translating/scaling latent ability and item parameters together can preserve exactly the same response probabilities; richer guessing/asymptote models bring additional identifiability/estimation problems.

C's executable logistic probe performs a simple scale/location transformation while leaving response probability exactly invariant.

Therefore:

```text
AbsoluteDifficultyLocation
and
AbsoluteCapabilityScale
require a reference/gauge convention.
```

GDF2 must not mistake one fitted coordinate system for intrinsic Game reality.

---

# 6. New concept: ChallengeEquivalenceClass

Given current observations/interventions, several distinct latent explanations may remain compatible with all evidence.

Instead of choosing one silently, C requires:

# **ChallengeEquivalenceClass**

> the set of materially distinct response/recovery explanations still indistinguishable under the current ChallengeObservationDesign + ChallengeInterventionSet.

This is the correct answer when evidence is insufficient.

It is better to say:

```text
threshold-shift vs hidden-population-selection unresolved
```

than to report a fake precise difficulty parameter.

---

# 7. Interventions are therefore first-class evidence

General causal-identifiability research shows the same broad epistemic pattern in a mathematically sharper setting: observational distributions can be compatible with multiple latent causal structures, while suitable interventions refine or sometimes identify the model.

GDF2 does not import any one theorem as a universal Game theorem.

It adopts the discipline:

```text
If two challenge explanations make the same observational prediction,
search for the cheapest intervention that makes them diverge.
```

This is exactly compatible with Ordivon's existing ProbeTransformation methodology.

---

# 8. ChallengeInterventionSet

C freezes no intervention taxonomy yet, but identifies a practical probe family.

## P0 — StructuralReachabilityProbe

Use exact Game rules/action/transition/horizon knowledge to establish that a target is reachable or unreachable.

This can identify **structural infeasibility** without any Human sample—provided the model is complete enough for the claim.

## P1 — ControlledCapabilitySweep

Run multiple known/constructed policy capability profiles against the exact same condition.

This probes threshold/discrimination directions.

Synthetic agents are useful here because they can be controlled/repeated.

But:

```text
SyntheticCapability != HumanSkillProfile.
```

## P2 — RepeatedSameControllerSeedSweep

Repeat the same controller/policy under controlled or observed exogenous seeds.

This helps distinguish:

```text
within-controller outcome randomness
```

from

```text
between-controller hidden heterogeneity.
```

## P3 — MappingAssistIntervention

Change exactly one mapping/assist dimension while preserving the rest.

This identifies causal response-shape changes under that assist transformation.

## P4 — OpponentCrossPlayMatrix

Cross controlled target policies against multiple controlled opponents.

This exposes matchup structure hidden by aggregate ratings.

## P5 — HistoryKnowledgeIntervention

Hold artifact/rules fixed and intervene on retained knowledge/history.

## P6 — RecoveryTransitionIntervention

Change checkpoint/reset/revival/history preservation while holding immediate challenge fixed.

## P7 — PopulationTransportAudit

Reweight/standardize comparisons to a shared observed capability/history distribution where possible.

None is universally sufficient alone.

---

# 9. One-shot variance does not identify randomness

Suppose one observation per participant produces 50% success.

Explanation A:

```text
half the controllers deterministically succeed
half deterministically fail
```

Explanation B:

```text
every controller has 50% stochastic success
```

One-shot aggregate data are identical.

Repeat the **same controller** many times:

```text
A → near-zero within-controller variance
B → high within-controller variance
```

in the constructed probe.

Therefore:

```text
ObservedVariance
!= SkillIndependentRandomness
```

unless attribution/repetition/seed structure supports that claim.

This reconstructs B's `SkillIndependentOutcomeComponent` into a more cautious:

# **AttributionResidualClass**

until intervention identifies its source.

---

# 10. Multidimensional SkillProfile destroys one-dimensional threshold thinking

GDF1 deliberately froze SkillProfile as non-scalar.

C now consumes that seriously.

Suppose outcome depends on:

```text
0.6 × timing
+
0.4 × strategy.
```

Then:

```text
high timing + low strategy
```

and:

```text
lower timing + high strategy
```

can produce the same outcome probability.

The executable probe constructs two such profiles.

Therefore:

```text
One observed outcome
does not identify
one scalar capability location.
```

The threshold is generally a **region/manifold in SkillProfile space**.

---

# 11. Discrimination is directional

At one point in multidimensional SkillProfile space, the outcome may be very sensitive to:

```text
timing
```

but less sensitive to:

```text
strategy
```

or vice versa.

Therefore:

```text
CapabilityDiscriminationProfile
```

must name the probed direction/region.

A single slope is only a one-dimensional projection.

This is why GDF2-C keeps discrimination as an **identified claim type**, not a universal object field.

---

# 12. Observed performance can be nonmonotonic without violating capability monotonicity

A subtle danger:

> If the participant is more capable, shouldn't performance always improve?

Not necessarily for **observed selected behavior**.

A more capable participant can choose:

```text
riskier route
harder self-imposed goal
experimental policy
style optimization
```

and perform worse on one observed criterion.

C's probe constructs:

```text
higher capability option set
+
worse selected policy performance.
```

But if higher capability literally preserves all lower-capability admissible policies and adds options, then:

```text
best attainable performance
```

cannot worsen under the same evaluation/conditions.

Therefore:

```text
ObservedPerformanceMonotonicity
!= CapabilityEnvelopeMonotonicity.
```

This distinction matters for mastery and adaptive challenge.

---

# 13. Assistance is also non-identifiable from one mean improvement

Suppose an assist improves average success by +10%.

That alone cannot tell whether the assist:

```text
shifted the capability threshold
flattened skill discrimination
relocated demand from timing to strategy
```

C constructs two assistance transformations with the same average gain over one sampled population but different low/mid/high capability response patterns.

Thus:

```text
MeanAssistBenefit
does not identify
AssistChallengeTransformation.
```

To identify shape, evaluate matched assistance conditions across multiple controlled capability probes/directions.

This is consistent with experiments/frameworks where task difficulty and haptic/external assistance are independently manipulated rather than treated as one inverse parameter.

---

# 14. Synthetic controllers are useful exactly because they enable interventions

Automated playtesting research shows synthetic/RL agents can correlate with Human completion-rate differences even when their absolute ability does not equal human performance.

GDF2's interpretation is deliberately narrow:

```text
Synthetic controller
→ structural/probe instrument.
```

It can help answer:

```text
Is the condition reachable?
How does outcome change across controlled policy strengths?
Which levels discriminate the chosen synthetic policy family?
How does a mapping or rule intervention move those relations?
```

It cannot establish by identity:

```text
Human experienced difficulty
Human SkillProfile scale
Human PlayerValue
Human learning
```

---

# 15. Opponent aggregate ratings are equally underidentified

C builds two three-policy matchup matrices.

Both have the same aggregate average win rate.

One is roughly transitive.

The other has strong cyclic/nontransitive matchup structure.

Thus:

```text
SameAverageWinRate
!= SameOpponentChallengeStructure.
```

This means a single Elo/MMR-like aggregate statistic may be useful for a narrow matchmaking projection while hiding important matchup-specific difficulty.

To identify the latter we need controlled cross-play or opponent interventions.

---

# 16. Adaptive opponents are not RNG

An opponent's behavior changes **conditionally** on the participant's policy/history.

IID seed noise does not.

Therefore:

```text
OpponentPolicyVariation
!= ExogenousRandomness.
```

OpponentInteractionSurface remains a useful **derived probe model**, but GDF2 should not freeze a whole game-theory ontology here; later GDF6 Strategy/Counterplay/Balance owns deeper opponent-policy structure.

---

# 17. Recovery is partly easier to identify than challenge

B used `ConsequenceRecoveryProfile`.

C finds two layers.

The Game authority can often directly determine:

```text
on failure:
  next state
  checkpoint/reset/revival path
  resources preserved/lost
  history preserved/lost
  retry eligibility/timing
```

These are not latent statistics.

So reconstruct to:

# **RecoveryTransitionSet**

an authoritative structural object/view.

But reducing those transitions to:

```text
failure severity = 7.3
```

still requires weights over:

```text
time
resources
history
social/opportunity cost
```

Therefore:

```text
RecoveryTransitionSet
!= UniversalRecoverySeverityScalar.
```

Any severity is a **QuerySpecificRecoveryCostProjection**.

---

# 18. IdentificationStatus becomes mandatory

C introduces a small epistemic vocabulary for GDF2 claims:

```text
structurally-proven
intervention-identified-under-assumptions
statistically-estimated-under-model
bounded-only
unidentified
```

Examples:

```text
"No admissible path exists under ruleset X and horizon H"
→ structurally-proven, if transition model is complete for claim.

"Assist A reduces timing threshold under matched synthetic policy sweep"
→ intervention-identified-under-assumptions.

"Player pass data fit a 2PL curve"
→ statistically-estimated-under-model.

"RNG vs hidden heterogeneous skill unresolved"
→ unidentified / equivalence class.
```

This is more important than attaching false precision to every challenge metric.

---

# 19. C's main reconstruction

B:

```text
CapabilityOutcomeSurface
```

looked like the central latent object.

C replaces the stronger ontological claim with:

```text
ChallengeConditionSpec
+
ChallengeObservationDesign
+
ChallengeInterventionSet
       │
       ▼
ChallengeResponseModelFamily
       │
       ├─ identified threshold claims
       ├─ identified discrimination claims
       ├─ feasibility claims
       ├─ opponent/attribution claims
       ├─ recovery transitions
       └─ unresolved ChallengeEquivalenceClass
```

The foundation candidate is increasingly an **epistemic/query contract**, not a giant new Game ontology.

---

# 20. Surface verdict after C

```text
CapabilityOutcomeSurface
→ DEMOTE to research model family.

ChallengeConditionSpec
→ STRONGLY RETAIN evidence contract.

CapabilityThresholdRegion
→ RETAIN as criterion/probe-relative identified claim type.

CapabilityDiscriminationProfile
→ RETAIN as directional/probe-relative identified claim type.

FeasibilityRegion
→ STRONGLY RETAIN structural/identified claim.

SkillIndependentOutcomeComponent
→ RECONSTRUCT to AttributionResidualClass until source identified.

OpponentInteractionSurface
→ RETAIN derived probe model.

FunctionalDifficultyProjection
→ RETAIN query-only.

ConsequenceRecoveryProfile
→ RECONSTRUCT:
   RecoveryTransitionSet
   + QuerySpecificRecoveryCostProjection.
```

---

# 21. Strongest C laws

```text
AggregatePassRate does not identify a unique challenge response relation.

SameAggregateOutcome can arise from different response surfaces and populations.

ObservedVariance != SkillIndependentRandomness without attribution probes.

Threshold and discrimination are coordinate/criterion/model/probe relative.

One mean assistance effect does not identify threshold shift vs flattening vs relocation.

Synthetic-agent response != Human SkillProfile by identity.

Population pass rate is challenge relation × selected population/history projection.

Opponent aggregate win rate != matchup-specific challenge structure.

ObservedPerformanceMonotonicity != CapabilityEnvelopeMonotonicity.

RecoveryTransitionSet != universal recovery severity scalar.

Unidentified alternatives must remain explicit as an equivalence class.
```

---

# 22. What is the minimum useful evidence hierarchy?

C now proposes this order:

## Level 0 — Structural analysis

Can prove some:

```text
legality
reachability/infeasibility
recovery transitions
rule/currentness
```

## Level 1 — Synthetic/control interventions

Can probe:

```text
policy/capability sensitivity
rule/remap/assist effects
opponent cross-play
seed/exogenous variance
```

## Level 2 — Human performance evidence

Adds:

```text
actual Human SkillProfile distributions
strategy/history population
accessibility/behavioral adaptation
```

but remains selection/model dependent.

## Level 3 — Human subjective/learning evidence

Required for:

```text
ExperiencedDifficulty
Frustration
Competence
Flow
PlayerValue
Learning
```

No lower level substitutes for a higher-level evidence target.

---

# 23. External research pressure

IRT identifiability research explicitly documents that response-model parameters can be non-unique under translation/scaling and that richer guessing/asymptote models create further estimation/identifiability difficulties. GDF2 uses this as direct warning against intrinsic interpretation of fitted threshold/discrimination coordinates.

Causal-identifiability work provides a broader methodological analogue: observationally equivalent latent explanations can require interventions for identification. GDF2 imports the intervention/equivalence-class discipline, not the theorem's specific linear causal assumptions.

Game automated-playtesting work shows that player-population evolution matters to pass/churn prediction, while synthetic-agent behavior can predict relative human level difficulty even without matching absolute human ability. This strongly supports synthetic agents as controlled probes plus explicit population transport—not synthetic=human identity.

Independent game difficulty/haptic-assistance manipulation demonstrates that task-side challenge and assistance-side capability expression can be experimentally separated.

---

# 24. Novelty ledger

## N0

```text
latent response models possess identifiability/gauge problems;
interventions can refine observational equivalence in causal-identifiability settings;
player population selection affects level difficulty/churn projections;
synthetic agents can be useful relative-difficulty probes without human identity;
difficulty and assistance can be independently manipulated.
```

## N1

```text
ChallengeObservationDesign
ChallengeInterventionSet
IdentifiedChallengeClaim
ChallengeEquivalenceClass
IdentificationStatus
AttributionResidualClass reconstruction
RecoveryTransitionSet + query-cost split
challenge identifiability probe hierarchy
```

## N2

```text
NONE.
```

## N3

```text
NONE.
```

---

# 25. Foundation reopen audit

C does not add a semantic primitive.

Quite the opposite: it **weakens** GDF2's commitment to a latent Surface object and moves more responsibility into:

```text
ProbeTransformation
Authority/Provenance
Observation
Evaluation
SkillProfile/SRVS
```

which are already frozen.

Therefore:

```text
ACS reopen = NOT TRIGGERED
GDF0 reopen = NOT TRIGGERED
R29 reopen = NOT TRIGGERED
```

---

# 26. Exact GDF2-D frontier

C has now operationalized challenge evidence, but GDF2 still has another half:

```text
Failure / Recovery / LearningOpportunity / Mastery.
```

A separated them; B/C focused mainly on challenge/difficulty.

The next round should therefore stop digging further into response curves and attack the other half directly:

# **GDF2-D — Failure / Recovery / Learning Opportunity / Mastery Mechanism Falsification**

Questions:

```text
1. What makes a FailureEvent local, terminal, recoverable or participation-ending?
2. Can failure severity be represented without scalarizing heterogeneous recovery transitions?
3. Which structural conditions create LearningOpportunity rather than merely error/failure exposure?
4. How do feedback informativeness, controllability, retry spacing/cost and variation interact?
5. Is Mastery best a robust-region claim over SkillProfile, or does it require control over perturbation/transfer/recovery?
6. How should mastery work for continuous expressive/open-ended practice?
7. Does repeated zero-error performance prove mastery, or merely saturation/overlearning?
8. How do assistance and joint control affect mastery attribution?
9. How do roguelike death, puzzle reset, competitive loss, sandbox self-imposed failure and synthetic-controller cases attack the model?
```

After D, GDF2 can decide whether another cross-GameForm adversarial round is needed before final reconstruction/freeze.
