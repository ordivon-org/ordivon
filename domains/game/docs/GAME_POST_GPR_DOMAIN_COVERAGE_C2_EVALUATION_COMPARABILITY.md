---
schema_version: 1
id: game.post-gpr-domain-coverage.c2-evaluation-comparability
title: Ordivon Game — Fresh Coverage C2: Cross-Instance Evaluation / Comparability Falsification
profile: research
lifecycle: active
source_role: research
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Fresh post-GPR destructive pass over score/rating/rank/record/leaderboard/performance-comparability. Cross-regime tests show that raw result, score, rank, rating, record status, mastery and cross-instance comparison are distinct; comparability is always purpose/basis/condition/model relative rather than one intrinsic Game relation. After subtracting GDF0 evaluation, GDF2 challenge/mastery/transfer conditions, GDF3 authoritative score/status/record determination, GPR7 comparison views and Social/Institutional legitimacy, no independent Game foundation responsibility survives. A reusable ComparisonClaimView pattern remains potentially useful as a cross-cutting practical/research abstraction, but no GPR8, new Foundation or implementation is admitted.
evidence_status: strong-local
readiness: C2_REDUCED_NO_NEW_FOUNDATION_ROUTE_NOT_SELECTED
applies_to:
  - ordivon-game
related:
  - game.challenge-failure-mastery-foundations.v1
  - game.authoritative-case-determination-foundations.v1
  - game.practical-concept-reconstruction.gpr7
  - game.post-gpr-domain-coverage.c1-instance-constitution
---
# Ordivon Game — Fresh Coverage C2: Cross-Instance Evaluation / Comparability Falsification

## 0. Boundary

This is not GDF4 and not GPR8.

C2 asks whether Game needs a new deep responsibility for:

```text
score
rating
rank
record
leaderboard
performance
cross-instance comparison
normalization
comparability
```

The null model is intentionally aggressive:

```text
C2 = existing Evaluation/Representation relations
   + GDF0 layered evaluation
   + GDF2 Challenge/Mastery conditions and transfer discipline
   + GDF3 official score/status/record determination
   + GPR7 ChallengeComparison/MasteryEvidence views
   + Social/Institutional rank legitimacy
   + ordinary research/statistical models
```

Only a recurrent Game-owned obligation that cannot be expressed by these layers may survive.

---

# 1. Candidate deletion pass

## Score

A score is an owner-local representation of some evaluation/result under declared semantics.

```text
Score != Value
Score != Skill
Score != Mastery
Score != Rank
Score != Record
Score != WorldTruth
```

Delete as foundation.

## Rating

A rating is a model-derived estimate/projection, commonly from outcomes plus assumptions about opponent strength, uncertainty, temporal change or other covariates.

```text
Rating != observed performance
Rating != intrinsic skill truth
```

Delete as foundation.

## Rank

Rank is an ordering under an explicit comparison/tie-break procedure.
Same primary score can yield different ranks under different admissible procedures.

Delete as foundation.

## Record

A record is a practice/institution-recognized comparison/status claim over eligible evidence/conditions.
GDF3 already owns binding record certification when CaseDeterminationBoundary applies.

Delete as foundation.

## Leaderboard

A leaderboard is a presentation/query surface over ranking/status sources.

Delete as ontology/foundation.

## Normalization

Normalization is one transformation mechanism used to support a specific comparison objective.
There is no universal normalization across GameForms.

Delete as foundation.

## Comparable boolean

Two observations may be comparable for one question and not another.

```text
Comparable(A,B) without purpose/basis/scope
= underspecified.
```

Delete universal boolean.

---

# 2. Falsifier A — same primary result, different rank

## C2-F1 — FIDE tournament tie-break selection

FIDE's 2026 tie-break regulations allow tournament rules to choose an ordered tie-break list. Available methods can depend on direct encounters, wins, progressive scores, opponent scores, opponent ratings, performance ratings, match/game points and other declared bases.

Therefore two participants can have:

```text
same primary tournament score
```

while different legitimate competition rules produce different final ordering.

Thus:

```text
PrimaryScore != RankByIdentity
Rank != intrinsic property of performance
```

Reduction:

```text
F8 Evaluation
+ F6 Authority/Provenance
+ current tournament/practice rules
+ GDF3 determination when official status is case-determined
```

No new foundation remains.

---

# 3. Falsifier B — same win, different rating update

## C2-F2 — FIDE rating update

FIDE rating change uses the game score relative to an expected score derived from rating difference, then multiplies aggregate deviation by a K development coefficient.

So:

```text
same binary win
+ different opponent rating
or different player K/state
→ different rating update.
```

Therefore:

```text
GameOutcome != RatingDeltaByIdentity
Rating != direct score accumulation
```

The rating is a model/procedure result over historical comparisons.

This belongs to research/competition-operation tooling, not a missing Game primitive.

---

# 4. Falsifier C — same match outcome, different skill model

## C2-F3 — TrueSkill vs TrueSkill2

Basic TrueSkill infers uncertain latent skill from relative team outcomes and intentionally need not use score margin. TrueSkill2 incorporates additional covariates such as experience, squad membership, kills, quitting tendency and cross-mode skill and produces materially different predictive estimates.

Therefore:

```text
same match history
+ different admitted inference model
→ different rating/skill belief.
```

So:

```text
RatingEstimate
= model-relative representation
not Game-world skill truth.
```

This strongly reduces C2 toward F7 Representation + declared model/provenance rather than a new Game foundation.

---

# 5. Falsifier D — individual metric can conflict with team objective

## C2-F4 — team objective vs auxiliary individual score

TrueSkill's published design rationale explicitly warns that optimizing kills, K/D or flag carries can distort behavior away from a team objective; the system therefore bases the core team skill update on team outcome in that setting.

Thus:

```text
IndividualPerformanceMetric
!= TeamObjectiveContributionByIdentity
```

and:

```text
BetterAuxiliaryScore
!= BetterPerformanceForEveryEvaluationQuestion.
```

This is already compatible with GDF2 attribution and GDF1 contribution topology.

No generic performance scalar survives.

---

# 6. Falsifier E — same raw athletic result, different comparison status

## C2-F5 — wind and record/ranking conditions

World Athletics distinguishes raw performance from record/legal/ranking treatment. Sprint/jump performance can be wind-affected; ranking rules can apply wind modifications, while record/legal eligibility uses declared conditions and thresholds.

Therefore:

```text
RawTimeOrDistance
!= RecordComparabilityByIdentity
!= RankingScoreByIdentity.
```

This provides a non-digital pressure case:

```text
measurement
+ environmental condition
+ competition rules
+ comparison purpose
→ different admissible comparison claims.
```

GDF3 already handles binding record/status determination where relevant.
The remaining statistical transformation is not uniquely Game-owned.

---

# 7. Falsifier F — the same raw performance may support several legitimate comparison questions

## C2-F6 — athletics ranking vs world-record eligibility

A performance can be unusable for one status/record purpose while still usable, possibly with correction, for another ranking purpose.

So:

```text
EligibleForComparisonPurposeP1
!= EligibleForComparisonPurposeP2.
```

This kills a universal:

```text
performance.isComparable = true/false
```

The correct object is a scoped claim.

---

# 8. Falsifier G — adaptive challenge destroys naive score comparability

## C2-F7 — personalized DDA

Dynamic difficulty and personalized content systems explicitly alter level/challenge conditions based on player models and prior performance.

Hold:

```text
completion rate / success count
```

fixed while varying:

```text
served challenge distribution
player-conditioned generation policy
```

The same apparent success statistic need not imply the same capability or challenge exposure.

Thus:

```text
SameOutcomeStatistic
!= SamePerformanceConditions
!= SameSkillEvidence.
```

GDF2 already requires challenge/mastery scope and transfer across changed conditions rather than assumption.

Therefore adaptive GameForms strengthen existing GDF2 discipline; they do not establish C2 as a new foundation.

---

# 9. Falsifier H — patch/opponent/assistance transformation

## C2-F8 — same nominal task after environment transformation

GDF2 already freezes that changes in:

```text
patch
ruleset
mapping
opponent distribution
assistance
evaluation
```

are transformations whose transfer must be established rather than assumed.

Therefore:

```text
SameTaskLabel
!= SameComparisonRegion.
```

C2 cannot claim this as new evidence; it is already closed locally by GDF2/GPR7 for challenge/mastery comparisons.

---

# 10. Falsifier I — same performance, changed evaluation code

## C2-F9 — judged performance

GDF3 already pressure-tested cases where the same underlying performance can receive a different official score/status when the current evaluation code or authoritative interpretation changes.

Thus:

```text
Performance != OfficialScoreByIdentity.
```

This is explicitly already-covered, not a C2 residual.

---

# 11. Falsifier J — scoreless/open-ended GameForms

## C2-F10 — expressive/sandbox/pretend/open-ended play

Many GameForms have no useful global cross-instance ordering at all.
They may support local evaluation, projects, style, challenge or meaning without a canonical leaderboard.

Therefore:

```text
CrossInstanceComparability
!= necessary condition for GameInstance/GameStructure.
```

Any C2 contract must be conditional on an actual comparison purpose.
This strongly argues against foundation-level universality.

---

# 12. Falsifier K — multi-objective comparison has no natural total order

## C2-F11 — strategy/creative/team performance

Two performances may trade off:

```text
speed
accuracy
resource efficiency
robustness
style
risk
team contribution
```

without one authoritative weighting.

A total ordering exists only when the current practice/query declares one or an institutional rule binds one.

Thus:

```text
MultipleEvaluationDimensions
!= NaturalScalarOrder.
```

R18/R20/R22/GDF2 already reject universal score collapse.

---

# 13. Falsifier L — incomplete evidence does not become incomparable by identity

## C2-F12 — uncertain comparison

Suppose two performances have the same declared comparison basis but one lacks opponent-condition, wind, assistance or version evidence.

The correct state may be:

```text
comparison unresolved / evidence insufficient
```

rather than:

```text
metaphysically incomparable.
```

Therefore:

```text
ComparabilityQuestion
!= ComparisonAnswer
!= EvidenceSufficiency.
```

GPR3 evidence/verification and GDF3 determination already provide the source/status discipline needed where authority matters.

---

# 14. What remains after subtraction

After removing score/rank/rating/record/leaderboard/normalization as primitives, C2 leaves a useful generic pattern:

```text
ComparisonClaim
```

with something like:

```text
ComparisonPurpose / Question
ComparedTargetRefs
EvaluationBasis / CriterionRefs
Condition / Population / Version / Assistance scope
TransformationOrNormalizationRefs when used
Aggregation / Ordering rule when used
Uncertainty / evidence sufficiency
Currentness / provenance
Result = ordered | tied | incomparable-for-purpose | unresolved
```

But this pattern is not uniquely Game-owned.

The same structure appears in:

```text
science
benchmarking
finance
sports statistics
model evaluation
education
operations research
```

Game supplies Game-local targets/criteria/conditions.
The comparison/measurement logic itself is cross-domain.

---

# 15. Why C2 does NOT survive as a new Game foundation responsibility

C1 survived because Game itself must decide whether a concrete GameInstance continues, ends or becomes a new instance.

C2 is different.

For any C2 case, after specifying the question:

```text
Game provides:
  Game-relative outcome/evaluation semantics
  rules/currentness
  challenge/skill/mastery scope
  authoritative status when applicable

Comparison layer provides:
  chosen comparison question
  statistical/model transformation
  ordering/aggregation
  uncertainty/evidence treatment
```

The latter does not require a specifically Game-owned foundation.

Strong result:

```text
Game owns comparison inputs where Game semantics matter.
Game does not own a universal science of comparability.
```

---

# 16. Existing Ordivon coverage is already sufficient at the Game boundary

## GDF0

Already separates:

```text
GameGoal
ParticipationPurpose
PlayerValue
ExternalStake
```

and permits plural/dynamic/non-scalar evaluation.

## GDF2

Already requires scoped challenge/mastery claims and rejects score/rank as mastery identity.
It explicitly makes patch/opponent/mapping/assistance/evaluation changes transfer questions.

## GPR7

Already stabilizes:

```text
ChallengeComparisonView
MasteryEvidenceView
```

and allows two conditions to be incomparable for a declared question.

## GDF3

Already owns authoritative score/status/record/eligibility determinations when independent binding case status exists.

## Social / Institutional

Owns social rank, credential and broader recognition legitimacy.

Therefore C2 does not expose a missing Game responsibility analogous to C1.

---

# 17. Practical reconstruction verdict

A broader cross-domain/tooling abstraction could someday be useful:

```text
ComparisonClaimView
ComparisonBasisDiagnostic
```

But Game currently has no evidence that such a generic layer reduces enough real consumer cost beyond existing GPR7/GDF3/local metrics.

So:

```text
newly discovered practical gap = YES, weak-to-moderate
new GPR cluster               = NO
engineering consumption       = NOT PROVEN
```

If future consumers repeatedly need cross-instance comparison outside Challenge/Mastery, the practical pattern can be reconsidered without reopening Foundations.

---

# 18. Agent-era result

Agent-era adaptive/generative systems increase the need to record:

```text
which challenge/content/opponent distribution was actually served
which policy generated it
which evaluation version applied
```

before comparing performance.

But this is evidence for stronger condition/provenance discipline, not a new Agent-era comparison primitive.

Likewise Agent benchmarks can produce rankings that depend on model, sample, environment/version and aggregation. This is a cross-domain evaluation problem rather than Game ontology.

---

# 19. Foundation reopen audit

```text
R1-R29 / F1-F9 = NOT REOPENED
GDF0            = NOT REOPENED
GDF1            = NOT REOPENED
GDF2            = NOT REOPENED
GDF3            = NOT REOPENED
```

No counterexample falsifies:

```text
plural/contextual evaluation
score/rank != mastery
challenge comparison is scoped
official score/status != world truth
```

No new F1-F9 primitive is needed.

---

# 20. C2 final classification

```text
C2 destructive pass = COMPLETE

Score primitive             = REJECTED
Rating primitive            = REJECTED
Rank primitive              = REJECTED
Record primitive            = REJECTED
Leaderboard primitive       = REJECTED
Normalization primitive     = REJECTED
Universal Comparable bool   = REJECTED
Universal total ordering    = REJECTED

ComparisonClaim pattern
= USEFUL CROSS-CUTTING PRACTICAL/RESEARCH ABSTRACTION

Independent Game foundation responsibility
= DOES NOT SURVIVE SUBTRACTION

C2 classification
= CROSS-CUTTING
  + NEWLY-DISCOVERED-PRACTICAL-GAP
  + OWNED-PARTLY-BY-RESEARCH/EVALUATION
  + NOT GENUINELY-NEW-GAME-FOUNDATION
```

No route is selected.

---

# 21. Relative update against C1

After equivalent destructive treatment:

```text
C1 GameInstance Constitution / Continuity
= survives as strong Game-owned downstream foundation candidate

C2 Cross-instance Evaluation / Comparability
= reduces to existing Game semantics + cross-domain comparison/modeling
```

This increases C1's relative residual strength, but still does not admit C1 as the next numbered Foundation because other independent continents remain untested.

---

# 22. External evidence anchors

Representative primary/current anchors:

```text
FIDE Handbook — Play-Off and Tie-Break Regulations effective 1 March 2026.
FIDE Handbook — Rating Regulations, including current rating-difference treatment effective from 1 October 2025.
Microsoft Research — TrueSkill Ranking System; Herbrich & Graepel, TrueSkill Bayesian Skill Rating System.
Microsoft Research — Minka, Cleven & Zaykov, TrueSkill 2.
World Athletics — 2026 World Ranking Rules; wind modification and legal-result treatment.
World Athletics — current certified road-event / record eligibility conditions.
Zook & Riedl (AIIDE 2012) — temporal player model for dynamic difficulty adjustment.
Sarkar & Cooper (AIIDE 2020) — skill chains and rating systems for dynamic difficulty adjustment.
Stoneman, Miller & Cooper (AIIDE 2022) — player-level matchmaking in Foldit.
McConnell & Zhao (AIIDE 2025) — adaptive puzzle generation with player-specific difficulty.
```

These sources are used as falsifiers/examples, not copied as Ordivon ontology.

---

# 23. Frontier after C2

```text
C1 GameInstance Constitution / Continuity
= strong foundation-unclosed candidate

C2 Evaluation / Comparability
= reduced; cross-cutting practical/research pattern

Dynamics / Emergence
= foundation-unclosed

Population / Matching
= foundation-unclosed / cross-owner

Adaptive Experience Management
= foundation-unclosed

Meta-practice / Extended Apparatus
= foundation-unclosed

GameStructure lineage/versioning
= partial / possibly input to C1

Integrity / cheating / exploit
= unresolved cross-cutting

unknown continents
= OPEN
```

Still:

```text
NextGPR            = UNKNOWN
NextPracticalRoute = UNKNOWN
NextFoundation     = UNKNOWN
```
