---
schema_version: 1
id: game.deep-foundations.gdf2-d
title: Ordivon Game Deep Foundations — GDF2-D Failure / Recovery / Learning Opportunity / Mastery Mechanism Falsification
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Attacks the failure/mastery half of GDF2. Reconstructs FailureEvent into evaluation-relative FailureAssessment, separates terminality from failure via authoritative recovery/pursuit continuity, retains RecoveryTransitionSet while keeping severity query-specific, reconstructs LearningOpportunity as a diagnostic/actionable/re-exposable structural profile distinct from actual learning, and reconstructs mastery as an explicit SkillProfile claim contract over declared probe/robustness scope rather than completion/high-score/zero-error. Cross-cases include roguelike death, speedrun criteria, opaque versus diagnostic failure, saturated tasks, assistance attribution, transfer failure and open-ended expressive mastery. No frozen foundation reopen is triggered.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf2-c
  - game.action-control-skill-foundations.v1
---
# Ordivon Game Deep Foundations — GDF2-D

## 0. D switches from `difficulty` to the consequences of not meeting a criterion

A separated failure and mastery vocabulary.
B/C deepened challenge/difficulty and then weakened the latent response-surface ontology.

D now asks:

```text
What is a failure?
When is it terminal?
What makes it potentially useful for learning?
What evidence can justify mastery?
```

The core discipline remains:

```text
structural/evaluation evidence
!= Human learning/experience evidence.
```

Canonical artifacts:

```text
evidence/gdf2-d/failure-mastery-model.json
evidence/gdf2-d/failure-mastery-probes.json
scripts/gdf2-d/failure-mastery-probes.mjs
scripts/gdf2-d/audit-failure-mastery.mjs
```

---

# 1. `FailureEvent` is still too object-like

A provisionalized FailureEvent as criterion nonattainment.

D pushes harder.

The exact same completed run can be:

```text
SUCCESS under: finish the game
FAILURE under: finish under 40:00
```

Nothing in the physical/event history alone contains a universal `failure=true` bit.

Therefore the general construct is better called:

# **FailureAssessment**

> an evaluation/provenance-bound determination that a declared criterion/commitment was not satisfied within a declared scope/horizon.

A Game can still emit an authoritative `run_failed` event.

That event means:

```text
failure according to this Game-local criterion/scope,
```

not metaphysical failure for every participation purpose.

Strong law:

```text
Failure requires EvaluationScope/Horizon.
```

---

# 2. Failure != terminality

Games frequently conflate:

```text
failure
→ death/game-over
→ terminal
→ restart
```

D separates them.

Suppose the same local objective fails.

Case A:

```text
no continuation preserving the same pursuit
```

Case B:

```text
checkpoint recovery
```

Case C:

```text
alternative route still satisfies the same broader commitment
```

The local FailureAssessment can be identical while terminality differs.

So introduce:

# **PursuitTerminalityClaim**

> under the current pursuit identity and horizon, no authoritative continuation/recovery transition preserves pursuit of the same declared commitment.

Thus:

```text
FailureAssessment != PursuitTerminalityClaim.
```

---

# 3. Death remains one of the strongest boundary cases

Roguelike death can simultaneously mean:

```text
run criterion failed
character died
meta-resource gained
new information acquired
broader progression continued
```

Therefore:

```text
Death != universal Failure.
```

Frommel, Klarkowski & Mandryk's mixed-methods study of 182 players provides compatible empirical pressure: players' reports made success/failure goal-relative and distinguished temporary struggle from more enduring/perpetual forms of failure. GDF2 uses this as Human/player evidence for scope sensitivity, not as the source of Game ontology.

---

# 4. RecoveryTransitionSet survives C and becomes stronger in D

The structural Game-owned question after failure/error/setback is:

```text
Which authoritative transitions exist now?
```

Possible transitions:

```text
continue in damaged state
checkpoint restore
revive
full run reset
team rescue
branch to alternate goal
meta-progression then new run
no continuation
```

For each we can structurally track:

```text
next state
state/history preserved
resources preserved/lost
time transition/retry eligibility
information preserved
pursuit identity/criterion continuation
```

This is:

# **RecoveryTransitionSet**

and it survives strongly.

---

# 5. But `failure severity` still refuses to become a scalar

Two transitions:

```text
A:
120s lost
5 resources lost
5% history lost

B:
20s lost
60 resources lost
60% history lost
```

Which is more severe?

No answer exists without a weighting/evaluation query.

Therefore:

```text
RecoveryTransitionSet
!= UniversalFailureSeverity.
```

A derived:

# **QuerySpecificRecoveryCostProjection**

can answer questions such as:

```text
time-to-next-attempt
resource attrition
history/progress destruction
social/opportunity interruption
```

but Game foundation should not invent universal weights.

---

# 6. Failure has no intrinsic learning value

This is D's central attack.

Compare two failures with identical count.

## Diagnostic failure

```text
feedback identifies relevant miss
cause is attributable
player can alter action
relevant variable is controllable
retry/re-exposure is available
prior attempt can be compared with next
```

## Opaque random failure

```text
failure signal only
hidden/random cause
no actionable distinction
no controllable correction
```

Both are failures.

Only the first exposes an obvious structural route for learning.

Therefore:

```text
FailureCount != LearningOpportunity.
```

---

# 7. External error-learning research supports exactly this weaker inference

In motor learning, error feedback can function as a teaching signal: Herzfeld and colleagues found that learning-related muscle-command changes resembled earlier feedback responses to error, and individuals with stronger feedback responses learned more from error. This supports the existence of mechanisms that can consume informative errors. It does **not** establish that every error/failure is educational.

Other experiments make the boundary sharper. Children's motor learning depended on the interaction of subjective error estimation and feedback frequency, while feedback after better versus poorer trials can produce different delayed retention outcomes despite similar practice performance.

So:

```text
ErrorOccurred
+ FeedbackPresent
```

is still not enough to identify learning opportunity.

---

# 8. LearningOpportunityProfile

D introduces a deliberately structural/evidence-side construct:

# **LearningOpportunityProfile**

It asks whether the episode exposes distinctions that a learner **could** use later.

Candidate dimensions:

```text
Diagnosticity
AttributionReliability
Actionability
Controllability
ReExposureAccess
ComparabilityMemory
SRVSRelevance
```

These are not added together into a universal score.

They are falsification questions.

For example:

```text
Diagnosticity:
Does the feedback distinguish what went wrong?

Actionability:
Does it suggest a materially different later policy/action?

Controllability:
Can the target influence the relevant variable?

ReExposureAccess:
Can the target encounter/test the distinction again?
```

---

# 9. Opportunity != actual learning

D's executable probe deliberately holds:

```text
SkillProfile before = 0.5
SkillProfile after  = 0.5
```

while a structurally strong LearningOpportunityProfile exists.

Thus:

```text
LearningOpportunity != ActualLearning.
```

Actual Human learning still requires Human-side evidence such as:

```text
retention
transfer
changed future policy/performance
```

under appropriate ProbeTransformations.

The same applies to synthetic/system learning: opportunity is not parameter update or improved policy by identity.

---

# 10. Productive failure is not `failure works`

Kapur's randomized studies found greater conceptual understanding/transfer when learners first attempted problems and often failed before later instruction, compared with instruction-first conditions.

The important GDF2 reading is:

```text
productive failure
=
problem generation/attempt
+
failed/incomplete solution space
+
subsequent instruction/consolidation
```

not:

```text
more failure → more learning.
```

Likewise, deliberate-erring studies include correction after deliberately generated errors.

Therefore GDF2 retains:

```text
FailureEvent != LearningOpportunity
LearningOpportunity != Learning
```

as separate boundaries.

---

# 11. Cheap retry affects opportunity frequency, not skill challenge by identity

A 2-second checkpoint can make it much easier to run:

```text
attempt → feedback → revised attempt
```

loops.

That can increase re-exposure and comparison opportunities.

But B already established:

```text
CheapRetry != EasyChallenge.
```

D adds:

```text
CheapRetry may increase LearningOpportunity access
without decreasing immediate capability demand.
```

Similarly:

```text
HighRecoveryCost
```

can suppress practice/re-exposure while leaving the same immediate challenge surface unchanged.

---

# 12. Mastery has the same compression problem as difficulty

Common usages:

```text
beat the game
get S rank
zero errors
reach top rank
practice until plateau
clear consistently
```

are not equivalent.

D therefore rejects one hidden object:

```text
Mastered = true/false.
```

Instead it asks:

> What exact capability claim are we making, over what condition/probe region?

---

# 13. MasteryClaimSpec

# **MasteryClaimSpec**

must declare enough of:

```text
attribution target
practice / category / evaluation scope
challenge-condition region
criterion
ProbeTransformation set
required robustness dimensions
history / retention horizon
assistance state
identification status
```

Then:

# **CapabilityMasteryClaim**

means:

> the target SkillProfile satisfies that exact claim strongly enough for the stated evidence status.

This is an evidence claim over the already-frozen SkillProfile, not a new metaphysical mastery state.

---

# 14. Nominal success != robust mastery

D constructs two controllers.

Both satisfy:

```text
nominal criterion >= 0.8
```

but:

```text
specialist:
nominal 0.95
retention 0.55
perturbation 0.50
transfer 0.45

robust:
nominal 0.90
retention 0.88
perturbation 0.84
transfer 0.80
```

Which is mastered?

That depends on the MasteryClaimSpec.

If the claim is only:

```text
mastered this nominal condition now
```

both may qualify.

If the claim includes:

```text
retention + perturbation robustness
```

only one does.

Thus:

```text
Mastery requires scope, not one universal robustness checklist.
```

---

# 15. Retention and transfer are not automatically part of every local mastery claim

This point prevents overcorrection.

D does **not** define mastery as:

```text
must transfer everywhere.
```

A speedrunner can legitimately master one exact patch/category while being poor in another game.

A local claim can be narrow.

But:

```text
TaskSpecificMastery
!= GeneralTransferMastery.
```

If transfer is claimed, it must be probed through exact GDF1 `ProbeTransformation` dimensions.

---

# 16. External training evidence makes this scope discipline necessary

Thirty hours of directed Space Fortress training produced durable task-specific performance improvements but did not yield the expected transfer to untrained tasks. This directly blocks:

```text
high trained performance
→ general mastery.
```

A randomized laparoscopic-training study similarly found that overtraining a basic task did not improve retention and provided only limited/inefficient transfer benefits to a more complex task.

And recent feedback-schedule experiments show that similar acquisition improvement can diverge later in retention/transfer.

Therefore:

```text
AcquisitionPerformance
!= RetainedMastery
!= TransferMastery.
```

---

# 17. Zero-error performance is particularly weak mastery evidence under saturation

Suppose a trivial challenge produces:

```text
novice errors = 0
expert errors = 0
```

while unprobed capability differs strongly.

Then:

```text
ZeroError
```

merely tells us the current condition failed to discriminate the profiles.

Therefore:

```text
ZeroError != Mastery.
```

This directly consumes GDF1:

```text
Capability != SkillExpression
ObservedPlateau != SkillCeiling.
```

Mastery evidence requires a condition/probe region that actually exposes the claimed capability distinction.

---

# 18. Demonstration evidence != capability claim

A single spectacular run can be:

```text
luck
one memorized route
assistance
one favorable opponent
peak sample
```

or genuine high capability.

D therefore separates:

# **DemonstratedMasteryEvidence**

from:

# **CapabilityMasteryClaim**

The former is evidence under exact conditions.
The latter is the stronger scoped inference.

C's IdentificationStatus remains binding:

```text
one demonstration
→ evidence sample
not automatically structurally/interventionally identified capability claim.
```

---

# 19. Assistance forces mastery attribution

Assisted joint controller:

```text
criterion = 0.8
assisted performance = 0.95
```

Human after assist removal:

```text
performance = 0.55
```

Then the evidence can support:

```text
JointController mastery under assist
```

but not:

```text
Human-independent mastery
```

by identity.

Therefore:

```text
JointControllerMastery != HumanIndependentMastery.
```

There can also be a legitimate:

```text
skill/mastery of using the coupled assist system
```

if that is the declared attribution target.

---

# 20. Open-ended/expressive mastery does not require completion

Consider:

```text
jazz-like expressive play
sandbox architecture
style-heavy combo routing
creative speed/build optimization
```

There may be no terminal:

```text
MASTERED THE WHOLE DOMAIN
```

event.

But we can still make bounded claims:

```text
robustly produces quality >= criterion
across declared technique/condition probes
```

without claiming a global maximum.

Thus:

```text
Mastery does not require terminal completion.
```

and:

```text
LocalMasteryClaim != ExhaustiveDomainMastery.
```

---

# 21. Social mastery and subjective competence stay separate

A community can grant:

```text
rank
title
credential
recognition
```

according to institutional/community rules.

A Human can feel highly competent.

Neither is identical to a Game-research CapabilityMasteryClaim.

So the A separation survives:

```text
CapabilityMasteryClaim
!= SubjectiveCompetence
!= SocialMastery.
```

These relations can correlate and interact without collapsing ownership.

---

# 22. D's reconstructed graph

```text
Current Evaluation Commitment / Criterion
                 │
                 ▼
        Performance / History Evidence
                 │
                 ├── Error / Loss / Punishment
                 │
                 ▼
          FailureAssessment
                 │
                 ├── RecoveryTransitionSet
                 │        │
                 │        └── QuerySpecificRecoveryCostProjection
                 │
                 └── PursuitTerminalityClaim

Error/Failure/Success Evidence
          + Feedback / State Evidence
                 │
                 ▼
        LearningOpportunityProfile
                 │
                 │  (does not imply)
                 ▼
       Human/System actual learning
                 │
                 ▼
             SkillProfile
                 │
        MasteryClaimSpec + Probes
                 ▼
        CapabilityMasteryClaim
```

---

# 23. Strongest D laws

```text
Failure requires EvaluationScope/Horizon.

FailureAssessment != PursuitTerminalityClaim.

Death != Failure by identity.

RecoveryTransitionSet != Retry button.

RecoveryTransitionSet != UniversalFailureSeverity.

FailureCount != LearningOpportunity.

LearningOpportunity != ActualLearning.

FeedbackPresence != Diagnosticity.

Diagnosticity without actionability/controllability is insufficient for a strong learning-opportunity claim.

NominalCriterionAttainment != RobustMastery.

DemonstratedMasteryEvidence != CapabilityMasteryClaim.

ZeroError != Mastery.

TaskSpecificMastery != TransferMastery.

JointControllerMastery != HumanIndependentMastery.

Mastery does not require terminal completion or globally maximal capability.
```

---

# 24. D survival verdict

```text
FailureEvent
→ RECONSTRUCT to FailureAssessment + optional authoritative failure signal.

PursuitTerminalityClaim
→ RETAIN candidate.

RecoveryTransitionSet
→ STRONGLY RETAIN candidate.

QuerySpecificRecoveryCostProjection
→ DERIVED QUERY.

LearningOpportunityProfile
→ RETAIN derived/interface candidate.

MasteryClaimSpec
→ STRONGLY RETAIN evidence contract.

CapabilityMasteryClaim
→ RETAIN claim type.

DemonstratedMasteryEvidence
→ RETAIN evidence/guard type.

MasteredBoolean
→ RETIRE.
```

---

# 25. Novelty ledger

## N0

External pressure establishes that:

```text
error feedback can support learning mechanisms;
feedback organization/error estimation matter;
productive failure includes later instruction/correction;
task-specific training gains need not transfer;
overtraining need not improve retention/generalization;
aggregate game score can hide strategy/error structure.
```

## N1

```text
FailureAssessment / PursuitTerminality separation
LearningOpportunityProfile
MasteryClaimSpec
local/open-ended mastery claim reconstruction
RecoveryTransitionSet + query-cost split strengthened
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

# 26. Foundation reopen audit

D's results directly consume frozen:

```text
SkillProfile
ProbeTransformation
Evaluation/Authority/Provenance
State/Transition/History
Capability != Expression
```

No new primitive is required.

No GDF0/GameAction/Skill law is contradicted.

Therefore:

```text
ACS reopen = NOT TRIGGERED
GDF0 reopen = NOT TRIGGERED
R29 reopen = NOT TRIGGERED
```

---

# 27. Does GDF2 now go straight to freeze?

Not yet.

A→D have generated two halves:

```text
Challenge/Difficulty/Identification
Failure/Recovery/LearningOpportunity/Mastery
```

but they have not yet been jointly attacked across the full GameForm corpus.

Several risky questions remain:

```text
Does FailureAssessment work for PvP/team/social failure?
Does LearningOpportunityProfile become an everything-good-about-feedback bag?
Does MasteryClaimSpec become so flexible that every claim can be rescued post hoc?
Does RecoveryTransitionSet survive sandbox/continuous practice where there is no failure transition?
Can challenge + mastery analysis avoid circularly defining the mastery region by expert behavior?
```

Therefore D earns one final adversarial integration round before freeze.

# **GDF2-E — Cross-GameForm Challenge / Failure / Mastery Adversarial Integration**

E should pressure the combined A→D structure across:

```text
precision platforming
puzzle/search
rhythm
racing
competitive PvP/team play
roguelike/permadeath
sandbox/self-authored goals
creative/expressive practice
accessibility assistance
shared autonomy
synthetic controllers
community speedrun/rank practices
```

with an explicit goal of deletion/compression before the final freeze round.
