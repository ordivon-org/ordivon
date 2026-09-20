---
schema_version: 1
id: game.deep-foundations.gdf3-c
title: Ordivon Game Deep Foundations — GDF3-C Adjudication / Interpretation / Review / Contestability
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Continues residual-selected GDF3 after GDF3-A/B compressed Participant and ParticipationAuthorityTopology. Starts from deterministic GameAction admission as the zero model, then falsifies it across contested evidence, final-but-fallible referee decisions, VAR review/reversal, tournament appeals, TTRPG open-intent resolution, speedrun category disputes, judged performance, post-hoc certification, moderation and Agent language/rule interpretation. Rejects Evidence, Interpretation, Review, Appeal, Finality, Contestability and Reversal as new primitives; establishes Finality != Truth, Review != Replay, Reversal != HistoryErasure != FullRollback, and retains an AdjudicationCaseContract as the first distinct Game-owned GDF3 responsibility candidate. No new F1-F9 primitive or upstream foundation reopen is triggered.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf3-a
  - game.deep-foundations.gdf3-b
  - game.play-game-deep-foundations.v1
  - game.action-control-skill-foundations.v1
  - game.challenge-failure-mastery-foundations.v1
  - game.foundations-research.r17
  - game.foundations-research.r29
---
# Ordivon Game Deep Foundations — GDF3-C

## 0. C begins from the cheapest possible model

GDF3-A deleted `Participant` and `Mediation` as new primitives.
GDF3-B then deleted `ParticipationAuthorityTopology` as an independent foundation responsibility by reconstructing it from ordinary Role/Relation/Time/Authority/Provenance plus GDF1 action/contribution semantics.

The strongest residual was narrower:

```text
Adjudication / Interpretation / Review / Contestability
```

C therefore starts with the cheapest model rather than assuming adjudication needs a rich institution.

```text
CanonicalState
+ CandidateAction/Event
+ CurrentRule
→ deterministic predicate/classification
→ Admit / Reject / Result
→ transition
```

Call this:

```text
DeterministicAdmission
```

It is sufficient for many digital cases.

Example:

```text
doorLocked = true
hasKey = false

rule:
open allowed iff !doorLocked || hasKey

candidate:
open door

→ REJECT
```

There is no need to invent:

```text
Evidence objects
Appeal system
Interpretive tribunal
Decision history
```

for this case.

C's first question is therefore:

> What repeated Game-relevant counterexample requires something beyond deterministic rule/action admission?

Canonical evidence/probes:

```text
evidence/gdf3-c/adjudication-term-case-matrix.json
evidence/gdf3-c/adjudication-probes.json
scripts/gdf3-c/adjudication-probes.mjs
scripts/gdf3-c/audit-gdf3-c.mjs
```

---

# 1. Deterministic admission is a limiting case, not all adjudication

The zero model works when enough of the following are true:

```text
relevant state is already authoritative/directly available
applicable rule/version is fixed
predicate is sufficiently closed
case identity is obvious
no contested evidence matters
no independent review relation matters
```

But GDF3-C repeatedly finds cases where these can vary independently:

```text
what happened?
what evidence is admitted?
what claim/question is being decided?
which rule/norm applies?
how is an open predicate classified?
who has authority to bind the result?
is that result reviewable?
what happens if it is reversed?
```

Therefore:

```text
DeterministicAdmission != UniversalAdjudicationModel.
```

This does **not** reopen GDF1.
GDF1's GameActionContract already correctly separates candidate/admission/execution/consequence.

C adds a different downstream responsibility for cases where authoritative status determination itself is a meaningful Game/Practice process.

---

# 2. Not every rule execution is adjudication

An overreaction would be:

```text
anything that applies a rule
= adjudication
```

Then:

```text
collision solver
damage formula
cooldown check
path legality
RNG table
physics integration
```

would all become adjudicators.

That destroys explanatory value.

C therefore uses a stronger domain boundary:

> An `AdjudicationCase` exists when a Game/PlayPractice treats some action, event, history, claim, performance, status or prior determination as a **case/question requiring an authoritative determination**, and changes in its admitted basis, applicable norm/evaluation basis, decision authority, determination/currentness or review lineage can create player/practice-relevant counterfactuals distinct from ordinary execution.

This is a research boundary, not a universal implementation requirement.

A direct deterministic rule transition can remain ordinary GDF1/GDF0 execution.

---

# 3. Observation != Evidence

An observation is observer/system-relative acquisition or representation.

```text
camera frame
sensor trace
witness memory
log line
replay
model output
```

None becomes `Evidence` merely by existing.

Evidence is relational:

```text
Evidence
=
some observation / record / testimony / trace / artifact / derived representation
admitted or treated as relevant support
with respect to a declared case question/claim/procedure.
```

The same observation can be relevant to one case question and irrelevant to another.

Example:

```text
Observation:
player crossed line at t = 10.2

Question A:
was player out of bounds?

Question B:
was player late relative to a 9.0 deadline?
```

Same observation.
Different evidentiary relation.

Therefore:

```text
Observation != Evidence by identity.
```

No new Evidence primitive is needed: F7 Representation plus F3 relation/F6 provenance and case scope are enough.

---

# 4. Evidence != Fact != WorldTruth

This is one of C's most important separations.

Suppose authoritative modeled WorldTruth says:

```text
contactOccurred = true
```

but available evidence is:

```text
occluded camera
witness saw no contact
```

A case finder may establish:

```text
contact not established
```

while underlying modeled truth remains:

```text
contact occurred
```

Later replay evidence may change the finding.

Therefore:

```text
Evidence != WorldTruth
CaseFinding != WorldTruth
```

and:

```text
More/BetterEvidence
may change
AuthoritativeCaseFinding
without changing underlying history.
```

This does not claim every Game has hidden objective WorldTruth.
It only requires that whenever WorldTruth and case finding are separately modeled, they must not be silently collapsed.

---

# 5. Claim != Fact

A claim is a proposition whose status may be at issue or supplied as input.

Examples:

```text
"the ball crossed the line"
"the runner used a prohibited glitch"
"this card interaction is legal"
"the player intended to attack the guard"
"this routine contains element X"
```

A claim may be:

```text
true
false
uncertain
inadmissible
irrelevant
unproven
accepted by practice authority
rejected on review
```

Therefore:

```text
Claim != Fact
Claim != Evidence
Claim != Ruling
```

An Agent-generated statement remains a claim/proposal at its admitted authority level.

---

# 6. Official case fact != metaphysical truth

Football provides a decisive real practice pressure.

The Laws grant the referee final authority over facts connected with play within the match, while the same rules framework explicitly acknowledges that referees are human and can make mistakes.

This forces the distinction:

```text
OfficialCaseFact / FinalMatchDetermination
!= WorldTruth / objective correctness
```

A Game model must be able to represent:

```text
official result = X
```

while also, if evidence/world model supports it, representing:

```text
actual event = Y
```

without contradiction.

Strong law:

```text
Finality != Truth.
```

---

# 7. RuleRepresentation != ApplicableNormBasis

GDF0 already froze:

```text
RuleRepresentation != RuleAuthority
RuleProposal != RuleAuthority
RuleBelief != CurrentRuleTruth
```

C extends the consumption boundary:

```text
all available rule text
!= the norm basis actually applicable to this case.
```

A case may depend on:

```text
current ruleset version
competition overlay
category rule
exception
local practice convention
self-imposed commitment
precedent/interpretive practice
current evaluation criteria
```

Therefore C uses the derived contract view:

```text
ApplicableNormBasis
```

meaning:

> the current authoritative rule/norm/standard/convention/evaluation basis treated as governing or relevant to the case.

It is not a new primitive.

---

# 8. `Interpretation` fails as one atomic stage

A tempting pipeline is:

```text
Evidence
→ Interpretation
→ Ruling
```

C rejects this as too coarse.

`Interpretation` can refer to several different operations:

```text
semantic interpretation:
  what does this natural-language proposal mean?

case characterization:
  what kind of event is this?

norm interpretation:
  what does this rule/standard mean here?

norm selection:
  which rule/exception applies?

classification:
  does the case satisfy category/predicate P?

argument/evidence interpretation:
  what weight/relevance should a piece of evidence have?
```

These can influence one another iteratively.

A norm hypothesis may determine which evidence matters.
New evidence may change case characterization.
A review may keep evidence fixed and change interpretation.

Therefore:

```text
InterpretationPrimitive = REJECTED.
```

C does not freeze a mandatory linear reasoning pipeline.

---

# 9. Classification != Ruling

Suppose an analyst/system says:

```text
"this looks like a reckless challenge"
```

and the current referee says the same thing.

Semantic content can match.
Binding status can differ.

Therefore:

```text
Classification != AuthoritativeDetermination.
```

Likewise:

```text
ModelPrediction != Ruling
CommunityOpinion != Ruling
ExpertAdvice != Ruling
```

unless the practice grants that output the relevant decision authority.

---

# 10. Rationale != Evidence != Authority

An adjudicator may provide reasons.
An Agent may generate an elaborate chain-of-thought-like explanation.
A rules article may explain why a classification is plausible.

None of these distinctions licenses:

```text
GeneratedRationale = Evidence
GeneratedRationale = Authority
GeneratedRationale = Truth
```

C therefore retains only a broad optional/provenance-bearing view:

```text
RationaleOrReasoningBasis
```

It may be:

```text
deterministic predicate
rule trace
argument set
classification explanation
precedent reference
human reason statement
opaque authorized procedure
```

A Game foundation must preserve the case outcome and authority even when full reasoning is not available.

---

# 11. The surviving core: AuthoritativeDetermination

After deleting the overloaded terms, one repeated Game-local responsibility remains:

```text
some Case
receives
an authoritative determination
under a current Game/Practice authority.
```

Examples:

```text
ACTION_ADMITTED
FOUL
NO_FOUL
VALID_RECORD
INVALID_RECORD
ELEMENT_VALUE_X
VIOLATION
NO_VIOLATION
CATEGORY_ELIGIBLE
DISQUALIFIED
```

The result need not be metaphysically true.
It is authoritative because current practice grants it binding consequence at the declared scope.

Therefore:

```text
AuthoritativeDetermination != WorldTruth
AuthoritativeDetermination != Enforcement
AuthoritativeDetermination != Finality
```

It is a typed case-level result using existing F1-F9 semantics, not a new semantic coordinate.

---

# 12. Ruling != Enforcement

GDF3-B established this structurally; C confirms it inside case resolution.

Example:

```text
Judge determines:
DISQUALIFIED

record system update fails
```

The determination still exists.
Enforcement/effectuation did not complete.

Or:

```text
Referee rules foul
→ restart/sanction later applied
```

Thus:

```text
AuthoritativeDetermination
!= EnforcementOrEffectuation.
```

This matters for:

```text
appeal before enforcement
execution failure
delayed sanction
partial remedy
record correction
```

---

# 13. Review != Replay

A review is not simply:

```text
run the same decision function again with the same input.
```

A review may differ in:

```text
evidence
norm selection
interpretation
classification
procedure
authority
scope
standard of review
```

Most importantly, a decision can change **without new evidence** if the reviewing authority changes the interpretation/classification of the same basis.

Constructed falsifier:

```text
EvidenceDigest = E1

D0:
interpretation A → INVALID

Review:
no new evidence
interpretation B → VALID
```

Therefore:

```text
Review != Replay.
```

---

# 14. Appeal != Review by identity

An appeal is a practice-recognized path/request invoking review under conditions such as:

```text
standing
eligible requester
time window
grounds
procedure
review authority
```

But review can also be:

```text
automatic
VAR-initiated recommendation
system-triggered
supervisory
post-hoc audit
```

without participant appeal.

Therefore:

```text
Appeal != Review.
```

And:

```text
Appeal != GuaranteedErrorCorrection.
```

An appeal can uphold the original determination.

---

# 15. Contestability is a topology, not a primitive

Two identical determinations can differ in challengeability.

Hold decision content fixed:

```text
OUT
```

At time t0:

```text
review path available
```

At t1 after a procedural cutoff:

```text
review path unavailable
```

Nothing about the content changed.
Contestability changed.

Therefore:

```text
Contestability != DecisionContent.
```

But C does not admit a new `Contestability` primitive.

It is a derived query over:

```text
current decision
review/appeal transitions
standing/conditions
scope/time
review authority
```

Hence:

```text
ReviewContestabilityTopology
= derived view.
```

---

# 16. Finality is derived from the review horizon

GDF3-B already rejected FinalAuthority as a global scalar.
C now rejects `Finality` as intrinsic truth/correctness.

Working research interpretation:

```text
Finality(case, determination, scope, time, horizon)
=
no further currently admitted review/override transition
inside the queried adjudicative horizon.
```

A determination can be:

```text
final for this match
but later historically criticized;

final for this tournament
but superseded by later policy;

final for a category record
until a new evidence/review process is admitted.
```

So:

```text
Finality != Truth
Finality != Correctness
Finality != EternalImmutability
```

---

# 17. DecisionLineage is required as a derived view

The simplest mutable-slot model is:

```text
decision = PENALTY

review occurs

decision = NO_PENALTY
```

This loses critical history.

C instead requires the ability to reconstruct:

```text
D0:
PENALTY
source = live referee decision
current = false

D1:
NO_PENALTY
source = referee after VAR review
supersedes = D0
current = true
```

The old decision is no longer current.
But it existed and may explain intervening actions.

Therefore:

```text
DecisionLineage
= derived adjudicative history view.
```

It need not be a dedicated storage object if ordinary event/provenance history already provides the information.

---

# 18. Reversal != HistoryErasure

If D1 reverses D0:

```text
D0 did not cease to have historically occurred.
```

People may have:

```text
stopped play
changed strategy
received information
acted on D0
incurred costs
```

before reversal.

Therefore:

```text
Reversal != HistoryErasure.
```

The current authoritative determination can change while the decision/event history remains intact.

---

# 19. Reversal != FullRollback

IFAB's VAR protocol provides a particularly strong real-world falsifier.

When play continues after an incident and the original incident decision is later changed, disciplinary action arising during the post-incident period is generally not automatically cancelled, subject to specified exceptions.

Thus a system can have:

```text
D0
→ intervening trajectory C1, C2, C3
→ Review
→ D1 supersedes D0
```

without:

```text
undo(C1, C2, C3) universally.
```

Therefore:

```text
Reversal != FullRollback.
```

A practice may prescribe:

```text
prospective correction
partial compensation
record correction
specific rollback
no rollback
```

by rule.

C must preserve that as consequence semantics rather than assume transactional time travel.

---

# 20. Correction != restoration of a counterfactual world

A wrong ruling can have path-dependent effects that cannot be fully repaired.

Examples:

```text
lost time
changed player strategy
revealed hidden information
fatigue
social/reputational impact
subsequent tactical choices
```

Even if current official record is corrected, there may be no unique state equivalent to:

```text
"what would have happened had the original error never occurred"
```

Therefore:

```text
DecisionCorrection
!= CounterfactualWorldRestoration.
```

This is a general dynamics/causality issue; World owns the lower counterfactual substrate.
Game owns which remedy/current record the practice authoritatively recognizes.

---

# 21. Post-hoc verification is adjudication without changing the original run

Speedrun verification is a clean case where adjudication happens after ordinary gameplay.

```text
RunHistory = H
```

Later:

```text
Verifier / category authority
→ VALID_RECORD
```

or:

```text
INVALID_RECORD
```

This changes:

```text
OfficialPracticeRecord
```

not necessarily:

```text
original GameInstance trajectory.
```

Therefore:

```text
Adjudication != live action admission only.
```

This is one major reason GDF1 GameActionContract alone cannot absorb GDF3-C.

---

# 22. Speedrun category disputes show rule predicates can be practice-open

`Glitchless` appears simple until a community must decide whether a technique counts as a glitch, exploit, intended mechanic, sequence break or permitted optimization.

The executable artifact alone does not settle the category rule.

Community voting/practice can determine the current category boundary.
The same run can therefore receive different category status under different current rules/practice times.

Thus:

```text
ExecutableMechanicTruth
!= CategoryLegality by identity.
```

and:

```text
RuleWord("glitch")
!= automatically closed predicate.
```

This residual points directly toward GDF3-D.

---

# 23. TTRPG open intent is adjudication near the action boundary

A player may say:

```text
"I wedge the shield into the gears,
then use the collapsing bridge to swing behind the guard."
```

No exhaustive button/action table may exist for that exact expression.

The facilitator/system may need to decide:

```text
what action(s) are being attempted?
what world facts/affordances matter?
which rule/check/evaluation applies?
what uncertainty must be resolved?
what consequence follows?
```

This is close to GDF1 GameAction admission but cannot collapse:

```text
NaturalLanguageIntent = GameAction
```

GDF0 already forbids:

```text
NaturalLanguageIntent != AuthoritativeEffect.
```

C adds:

```text
SemanticInterpretation
→ CandidateMeaning / CandidateAction
→ current authority admission/adjudication
→ consequence.
```

The interpretation itself can remain nonbinding.

---

# 24. Natural-language action systems make interpretation uncertainty operational

Current language-based game companions already use explicit confidence/interpretation machinery to decompose complex player commands and infer intent.

This is a useful Agent-era pressure test because:

```text
one utterance
→ multiple plausible action plans / referents / temporal structures
```

Thus:

```text
Utterance != Intent
IntentInterpretation != GameActionAdmission
ModelConfidence != Authority
```

A Game may choose to:

```text
execute highest-confidence interpretation automatically
ask for clarification
present candidate interpretations
restrict effects to safe subset
route to an adjudicator
```

Those are design/practice choices over existing authority semantics.

---

# 25. Model fluency != rule correctness

Current game-rule-understanding research provides direct pressure against treating language-model output as authoritative merely because it is coherent.

Models can fail at:

```text
rule application
rule interaction
evaluation/modification
out-of-distribution rulesets
```

and improve under targeted training.

Therefore:

```text
FluentRuleExplanation != CorrectRuleApplication
ModelConfidence != CurrentRuleTruth
```

This strengthens, rather than replaces, GDF0's Agent-era guard:

```text
RuleProposal != RuleAuthority.
```

---

# 26. Generated rules remain candidates until authority adopts them

Suppose an Agent generates:

```text
R2 = proposed new rule
```

while current authoritative rule is:

```text
R1
```

The Agent may also explain why R2 is desirable.

Still:

```text
GeneratedRuleRepresentation(R2)
!= CurrentRuleTruth(R2).
```

Only an authorized adoption/change transition can make R2 current at the relevant scope.

If the same Agent also owns rule-change authority, that authority relation—not generation—is what binds the change.

---

# 27. Judged performance shows support evidence != decision authority

Gymnastics provides another useful regime.

Technology can supply:

```text
3D reconstruction
angle/distance measurements
element-recognition support
replay/visualization
```

in inquiry/blocked-score contexts.

The practice can still assign final valuation/decision responsibility to a Superior Jury or other current judging authority.

Therefore:

```text
MeasurementSupport != AdjudicativeAuthority.
```

This is structurally the same separation as:

```text
VAR replay != referee final authority.
```

The lower perception/measurement science remains Media/World/technical-owner territory.
Game consumes the evidence/authority relation.

---

# 28. Judged performance does not require Game to own aesthetic phenomenology

A performance can receive an authoritative score under a practice's criteria without Game claiming:

```text
there is one objective Human aesthetic truth.
```

Game owns:

```text
which evaluation criteria/current rules matter
which observations/evidence are admitted
which judging/aggregation process binds the score
which review/inquiry routes exist
```

Human owns lower subjective experience/appraisal mechanisms.

Therefore:

```text
AuthoritativeScore
!= UniversalAestheticTruth.
```

---

# 29. Adjudication can be defeasible / non-monotonic

A weak evidence model assumes:

```text
more evidence
→ only strengthens the same conclusion.
```

But a new exception/fact can defeat a previous inference.

Constructed example:

```text
E1:
behavior normally violates rule R
→ VIOLATION

E2:
authorized exception applies
→ NO_VIOLATION
```

The new basis does not merely increase confidence.
It changes which inference is warranted.

Therefore:

```text
Adjudication need not be monotonic.
```

Argumentation/non-monotonic reasoning traditions show this is a general reasoning phenomenon, not uniquely Game-native.

Game should not duplicate those general theories.
It needs a contract capable of preserving revised case determination/provenance when such reasoning is used.

---

# 30. Review can target several different things

C rejects a single notion of `the decision was reviewed` without target.

Review may target:

```text
EvidenceBasis
  new replay, corrected log, witness, measurement

CaseFinding
  what event/fact is established?

ApplicableNormBasis
  which rule/version/exception applies?

Interpretation/Classification
  does this conduct satisfy predicate P?

Procedure
  was required process followed?

Authority
  was decision-maker currently empowered?

Determination
  should outcome be upheld/modified/reversed?

Enforcement/Remedy
  what consequence should now apply?
```

A review system need not support every target.

This is why `Review` remains a derived process family rather than a new primitive.

---

# 31. Adjudication is not guaranteed epistemic improvement

A review may:

```text
correct an error
uphold an error
introduce a new error
change interpretation legitimately
resolve ambiguity by authority rather than discover hidden truth
```

Therefore:

```text
Review != TruthConvergence by identity.
```

The foundation should represent authority/currentness/provenance, not promise epistemic perfection.

---

# 32. Formal legality != legitimacy / fairness

A determination may be formally valid under current authority yet socially contested or viewed as unfair.

Conversely, a popular community belief may lack formal authority.

Therefore:

```text
FormalAdjudicativeValidity
!= Legitimacy
!= Fairness
!= PlayerAcceptance
```

R28/social-institutional theory owns lower legitimacy/culture mechanisms.
Human owns subjective fairness/affect where applicable.

GDF3 owns the GamePractice-specific authoritative case structure.

---

# 33. The same Agent can occupy proposer/interpreter/judge roles without semantic collapse

Agent-era systems make this easy:

```text
Agent-X
→ proposes action A1
→ interprets A1 as meaning X
→ decides X is legal
→ executes consequence
```

Entity identity is unchanged.

But each output can carry different status:

```text
proposal: nonbinding
interpretation: nonbinding
ruling: binding because current practice grants decision authority
```

Therefore:

```text
SameModelIdentity
!= SameOutputAuthority.
```

C does not declare such fusion universally invalid.
A competitive practice may prohibit it.
A TTRPG-like facilitator may intentionally fuse it.

The integrity rule remains practice-specific.

---

# 34. Authority over interpretation is itself separable

Some systems may permit:

```text
Agent A proposes semantic parse
Agent B selects classification
Human C issues final ruling
```

Others may collapse all three.

The point is not to create three mandatory roles.

The point is:

```text
semantic/reasoning function
!= binding authority by identity.
```

This distinction prevents generated interpretations from silently becoming Game truth.

---

# 35. The minimum surviving responsibility: AdjudicationCaseContract

After C's deletion pass, one independent Game-owned responsibility candidate survives.

Working contract:

```text
AdjudicationCaseContract
```

A serious adjudicative claim must preserve enough information to answer, where materially relevant:

```text
1. CaseTarget / DecisionQuestion
   What status/action/event/history/claim/performance/prior decision is at issue?

2. CaseBasis
   Which authoritative state and/or admitted observations/evidence/claims/records
   support the determination, with provenance where needed?

3. ApplicableNormBasis
   Which current rule/norm/standard/category/evaluation basis governs the case?

4. DeterminationBasis
   What classification/interpretive/procedural basis connected the case to the result,
   if that basis is externally relevant?
   No universal algorithm is required.

5. DecisionAuthority
   Who/what currently has binding authority over this case and scope?

6. AuthoritativeDetermination
   What result is currently binding?

7. Scope / Currentness / Provenance
   Where/when/version/source is the determination valid?

8. Review / DecisionLineage
   What prior determination does this uphold/modify/reverse/supersede,
   and what further review paths remain, if relevant?

9. Consequence / Enforcement relation
   What current effects are prescribed/applied, without equating determination with execution?
```

These are **responsibility questions**, not a required object schema.

Many cases can omit fields that create no relevant counterfactual.

---

# 36. Why CaseBasis is broader than EvidenceSet

C deliberately does **not** require every case to build an explicit `EvidenceSet`.

The deterministic zero model can use:

```text
canonical authoritative state directly
```

without an evidentiary dispute.

Other cases may use:

```text
replay
testimony
logs
sensor measurements
recorded run
model-derived classification
prior decisions
```

Thus:

```text
CaseBasis
```

is the broader responsibility notion.

`EvidenceBasis` is a derived view only when evidence relations matter.

This prevents bureaucratizing ordinary digital rule execution.

---

# 37. Why DeterminationBasis is optional / non-prescriptive

C also refuses to require:

```text
one explainable reasoning trace
```

for every adjudication.

A determination may come from:

```text
closed deterministic predicate
formal rule engine
panel aggregation
human judgment
precedent/case-based reasoning
argumentation
hybrid AI/human process
```

Game foundations need to preserve the externally relevant distinctions, not dictate the reasoning substrate.

If reasoning basis affects:

```text
review
legitimacy
reproducibility
scope
classification
```

then it should be represented/provenanced.

Otherwise it may remain opaque.

---

# 38. Why AdjudicationCaseContract is Game-owned rather than generic epistemology

The lower problems of:

```text
truth
perception
sensor accuracy
logic
argumentation
belief revision
legal reasoning
human judgment
```

are cross-domain and not owned by Game.

Game's responsibility is narrower:

> preserve which case determination controls GameStructure/PlayPractice semantics and player-relevant consequences under current rules/authority, without collapsing evidence, truth, rule interpretation, determination, enforcement and review.

That is directly Game-local because it can change:

```text
admissible action
score/result
category validity
record status
continuation/restart
sanction/access
world consequence
player strategy
```

---

# 39. Why GDF0 alone is insufficient

GDF0 correctly freezes:

```text
EffectiveRuleTopology
RuleRepresentation != RuleAuthority
valid evidence/history/verification can be constitutive
scope/currentness/authority matter
```

But it intentionally does not deeply specify how a concrete disputed/open case becomes an authoritative determination or how review/reversal history must be separated.

GDF3-C therefore **consumes** GDF0 without reopening it.

---

# 40. Why GDF1 alone is insufficient

GDF1 GameActionContract correctly handles:

```text
input/control evidence
→ ActionAttempt/CandidateAction
→ admission/current legality
→ ExecutedGameAction
→ consequence
```

This covers C's deterministic action-admission limiting case.

But GDF3-C includes cases where no new player GameAction is being admitted:

```text
post-hoc speedrun certification
Magic judge appeal
football VAR review
judged-performance inquiry
moderation case
record/status review
```

Therefore:

```text
AdjudicationCaseContract != GameActionContract.
```

They interact at the action-admission boundary but have different scope.

No ACS reopen is triggered.

---

# 41. Why GDF2 is not the owner

Adjudication can alter:

```text
failure/success status
score
penalty
challenge conditions
mastery/record recognition
```

but GDF2's Challenge/Failure/Mastery contracts already make evaluation scope/currentness explicit.

GDF3-C only supplies how authoritative case status is determined/reviewed.

No GDF2 contradiction appears.

---

# 42. Cross-regime matrix

| Regime | Case question | Basis | Norm/evaluation | Determination | Review pressure |
| --- | --- | --- | --- | --- | --- |
| closed digital resolver | is action currently legal? | canonical state | executable/current rule | admit/reject | often none |
| natural-language action | what action does utterance denote and is it admissible? | language + context/state | action/rule semantics | candidate/admit/clarify/reject | possible clarification/review |
| football | what happened / what offence category applies? | live observation + officials + replay | Laws + spirit/discretion | referee decision | VAR-limited review |
| Magic tournament | what is legal / what ruling applies? | game state + testimony/rules | CR/MTR/IPG | judge ruling | appeal to HJ |
| TTRPG | what does open intent do? | fiction/world state + player declaration | rules + table practice | GM/system resolution | group/practice-dependent |
| speedrun | is technique/run category-valid? | run/video/logs + category facts | category rules/practice | valid/invalid record | moderator/community process |
| gymnastics/judged sport | what element/score classification applies? | judge observation + support tech | Code/current criteria | score/valuation | inquiry/Superior Jury |
| moderation | does behavior violate current policy? | content/logs/context | platform/game policy | violation/no violation | appeal/review possible |
| Agent-generated rule case | which generated proposal is current/applicable? | generated text + adoption history | current rule authority | accepted/rejected/current | governance-dependent |

The same semantic contract can cover all rows without requiring one adjudication algorithm.

---

# 43. Strongest laws surviving GDF3-C

```text
Observation != Evidence.

Evidence != Claim != WorldTruth.

CaseFinding != WorldTruth.

RuleRepresentation != ApplicableNormBasis.

Interpretation != one mandatory atomic stage.

Classification != AuthoritativeDetermination.

Rationale != Evidence != Authority.

AuthoritativeDetermination != WorldTruth.

AuthoritativeDetermination != Enforcement.

Review != Replay.

Appeal != Review by identity.

Appeal != GuaranteedCorrection.

Contestability != DecisionContent.

Finality != Truth.
Finality != Correctness.
Finality != EternalImmutability.

Reversal != HistoryErasure.
Reversal != FullRollback.

Verification/Certification != OriginalHistoryRewrite.

NaturalLanguageIntent != AuthoritativeEffect.
IntentInterpretation != GameActionAdmission.

ModelFluency/Confidence != RuleCorrectness/Authority.

GeneratedRuleRepresentation != CurrentRuleTruth.

Measurement/JudgingSupport != DecisionAuthority.

Adjudication may be defeasible/non-monotonic.

SameModelIdentity != SameOutputAuthority.
```

---

# 44. Candidate deletions after C

Reject as new primitives:

```text
EvidencePrimitive
FactPrimitive
InterpretationPrimitive
ClassificationPrimitive
ReviewPrimitive
AppealPrimitive
ContestabilityPrimitive
FinalityScalar / intrinsic final flag
Reversal-as-Rollback primitive
```

All can be represented using existing state/relation/transition/time/authority/representation/evaluation/action semantics plus domain-specific case structure.

---

# 45. Candidate survivors after C

Retain:

```text
AdjudicationCaseContract
  = Game-owned responsibility candidate

AuthoritativeDetermination
  = typed case-level result, not new F1-F9 primitive

DecisionLineage
  = derived view

EvidenceBasis / CaseBasis
  = derived contract view

ApplicableNormBasis
  = derived contract view

ReviewContestabilityTopology
  = derived view

AdjudicationProvenanceGuard
  = anti-collapse requirement rather than separate object
```

Nothing is frozen as final GDF3 v1 yet.

---

# 46. AdjudicationProvenanceGuard

C's repeated Agent/institutional failures suggest one guard worth carrying forward:

```text
Do not infer binding case status from content alone.
```

A serious adjudicative result must preserve enough provenance to distinguish:

```text
who/what produced the result
under what current authority
for which case/scope
using which current norm/evaluation basis
whether it supersedes a prior determination
```

This is an anti-collapse rule, not a new storage object.

---

# 47. Agent-era novelty pressure

Agent-native systems do not force a new semantic coordinate.

They amplify several old adjudication problems:

```text
semantic openness of player intent
probabilistic interpretation
rule generation/modification
one model occupying several roles
model-generated rationale/evidence confusion
runtime changes to content/rules
cheap automated review
```

The strongest Agent-era rule remains:

```text
Model output
→ Candidate / Evidence / Classification / Proposal
at the authority level actually granted

not

Model output
→ WorldTruth / CurrentRuleTruth / BindingDetermination automatically.
```

Agent-era novelty is therefore primarily a pressure multiplier on provenance/adjudication, not an N3 primitive.

---

# 48. External evidence anchors used in C

Representative anchors:

```text
IFAB Laws of the Game 2026/27 — Law 5 and VAR Protocol
- referee final match decision authority
- spirit/discretion
- review scope/currentness
- VAR recommendation vs referee final decision
- decision reversal without universal cancellation of post-incident discipline
- explicit acknowledgement that referees may make mistakes

Magic Tournament Rules / tournament judge practice
- first-instance judge rulings
- Head Judge appeal/finality
- structured review authority

Dungeons & Dragons Dungeon Master's Guide (2024)
- Running the Game includes Resolving Outcomes, Ability Checks,
  Consequences and Improvising Answers

Ricksand (2021), Game Studies
- glitchless speedrun category predicates and community voting/practice
  expose adjudication not reducible to executable mechanics

World Gymnastics Judging Support System
- technology/AI supplies measurement/review support in inquiry/blocked-score cases
- judging authority remains practice-assigned

Bateni, Pratt & Whitehead (AIIDE 2025)
- LLM game-rule application/interaction/evaluation can fail and improve with targeted training

Wei et al. (AAAI 2026), F.A.C.U.L.
- language-based game companion uses confidence-based decomposition/intent interpretation

Dung (1995)
- argumentation/non-monotonic reasoning supplies a general falsifier against monotonic adjudicative inference
```

These sources generate pressure/counterexamples; Ordivon does not adopt their terminology wholesale.

---

# 49. Novelty audit

## N0 — established external structures

```text
adjudication
appeal/review
final-but-fallible decisions
evidence/decision separation
rule interpretation
non-monotonic reasoning
technology-assisted judging
```

are established.

## N1 — Ordivon compression

```text
Finality != Truth
Reversal != HistoryErasure != FullRollback
Interpretation != one stage
CaseBasis broader than EvidenceSet
```

are conservative but important cross-regime separations.

## N2 — candidate synthesis

```text
AdjudicationCaseContract
```

as one Game-owned responsibility spanning:

```text
action admission
sports officiating
TTRPG resolution
speedrun verification
judged performance
moderation
Agent-language/rule cases
```

while treating reasoning substrate as owner-external/replaceable is a useful Ordivon synthesis.

No broad originality claim is made.

## N3

None claimed.

---

# 50. Upstream reopen audit

## R29 / F1-F9

C uses only:

```text
F1 Entity/Reference
F2 State
F3 Relation
F4 Transition/Constraint
F5 Time
F6 Authority/Provenance
F7 Observation/Representation
F8 Evaluation/Motivation
F9 Action/Capability/Policy/Control
```

Examples:

```text
Evidence
= representation + relation + provenance

CaseFinding
= state/representation under authority

Determination
= state/event under authority/currentness

Review
= transition over prior determination

DecisionLineage
= time/provenance relation graph
```

No F10 required.

```text
R29 reopen = NOT TRIGGERED.
```

## GDF0

C consumes EffectiveRuleTopology and constitutive overlays exactly as intended.
It does not reveal a missing Game/Play target class.

```text
GDF0 reopen = NOT TRIGGERED.
```

## GDF1

The action boundary remains:

```text
Intent/Input != CandidateAction != Admission != ExecutedAction != Consequence.
```

Adjudication can implement/mediate admission in open cases without collapsing these terms.

```text
GDF1 ACS reopen = NOT TRIGGERED.
```

## GDF2

No Challenge/Failure/Mastery frozen law is contradicted.

```text
GDF2 reopen = NOT TRIGGERED.
```

---

# 51. C's strongest positive result

A and B mostly deleted candidate ontology.

C is the first GDF3 round where a distinct **Game-owned responsibility** survives deletion:

```text
AdjudicationCaseContract
```

Why it survives:

1. It appears across materially different Game/Practice regimes.
2. It creates player/practice-relevant counterfactuals.
3. GDF1 action admission cannot cover post-hoc/non-action cases.
4. GDF0 rule authority names the substrate but not the case-resolution anti-collapse responsibility.
5. It requires no new F1-F9 coordinate.
6. It remains substrate-neutral: Human, deterministic software or Agent can occupy the role.
7. It separates Game-owned authoritative consequence from generic epistemology/legal reasoning/Human judgment.

This is enough to retain it as a candidate for later GDF3 freeze.

---

# 52. What still prevents GDF3 from freezing

The largest remaining hole is **inside the norm-application step**.

C can say:

```text
CaseBasis
+ ApplicableNormBasis
+ DecisionAuthority
→ AuthoritativeDetermination
```

but has not yet deeply reconstructed what happens when:

```text
rule contains an open-textured predicate
multiple norms conflict
exceptions defeat default rules
precedent/category history matters
"spirit" or ethos matters
practice convention diverges from literal text
new cases were not anticipated
natural-language rule/action semantics are underdetermined
an Agent generates both interpretation and case output
```

This cannot be left implicit before GDF3 freeze.

---

# 53. GDF3-C verdict

```text
GDF3-C = COMPLETE

DeterministicAdmission
= valid limiting case
!= universal adjudication model

Evidence primitive
= REJECTED

Fact primitive
= REJECTED

Interpretation as one stage/primitive
= REJECTED

Review / Appeal primitives
= REJECTED

Contestability primitive
= REJECTED; derived topology

Finality scalar/intrinsic property
= REJECTED

Reversal-as-rollback
= REJECTED

DecisionLineage
= RETAIN as derived view

AdjudicationCaseContract
= RETAIN as Game-owned responsibility candidate

AuthoritativeDetermination
= RETAIN as typed case-level result
  using F1-F9, not F10

R29/GDF0/GDF1/GDF2 reopen
= NO
```

---

# 54. Exact next round

C's residual selection is now sufficiently specific:

```text
GDF3-D — Norm Application / Open Texture / Precedent / Discretion
```

Primary question:

> Can `ApplicableNormBasis + DeterminationBasis` remain a generic opaque slot, or do repeated GameForms require a deeper Game-owned contract for applying incomplete/open/defeasible/precedential rules and standards to novel cases?

D must attack at least:

```text
Rule vs Standard
literal/formal rule vs practice purpose/ethos
open-textured predicate
exception / defeater
conflicting norms
precedent / prior rulings
custom / community convention
discretion
consistency vs case sensitivity
rule change vs interpretation change
retroactive vs prospective interpretive effect
natural-language semantic underdetermination
Agent-generated interpretation/rationale
```

Minimum regimes:

```text
closed digital rule engine as control
football subjective vs factual decisions / spirit of game
Magic corner-case ruling
TTRPG improvisational resolution
speedrun glitchless category
judged performance criteria
moderation policy
Agent natural-language action/rule adjudication
```

No GDF3 foundation should freeze before this residual is attacked.
