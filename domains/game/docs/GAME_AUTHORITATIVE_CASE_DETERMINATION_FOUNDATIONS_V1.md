---
schema_version: 1
id: game.authoritative-case-determination-foundations.v1
title: Ordivon Game — Authoritative Case Determination Foundations v1
profile: research
lifecycle: frozen
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Frozen GDF3 foundations after A-F. Freezes exactly one Game-owned responsibility contract—AuthoritativeCaseDeterminationContract—with three obligations: determination target/status, binding F5/F6 authority/currentness/provenance, and typed determination-basis provenance when case/evidence and norm/evaluation/application bases can vary independently. It is not a new semantic primitive. Ordinary deterministic execution is outside the contract unless an independently meaningful binding case status exists. Review lineage, norm-application detail, authority-topology views and discretion remain derived; enforcement belongs to ordinary transition/GDF0/GDF1 semantics. Human, synthetic, collective and solitary role-fused adjudication share the same semantic contract. Nine FoundationReopenConditions govern reopening.
readiness: FROZEN_V1
applies_to:
  - ordivon-game
related:
  - game.play-game-deep-foundations.v1
  - game.action-control-skill-foundations.v1
  - game.challenge-failure-mastery-foundations.v1
  - game.foundations-research.r29
---
# Ordivon Game — Authoritative Case Determination Foundations v1

## 0. Scope

This v1 freezes the minimum Game-owned responsibility needed to reason correctly about:

```text
referee/judge rulings
open-case action resolution
post-hoc certification
judged score/status
review/reversal
moderation-like case status
Agent-mediated case determination
self-authored/solitary certification
other Game/PlayPractice binding case statuses
```

without creating a new adjudication ontology.

It consumes frozen:

```text
R1-R29 / F1-F9
Play / Game Deep Foundations v1
Action / Control / Skill Foundations v1
Challenge / Failure / Mastery Foundations v1
```

especially:

```text
F2 State
F3 Relation
F4 Transition/Constraint
F5 Time/Currentness
F6 Authority/Provenance
F7 Observation/Representation
F8 Evaluation
F9 Action/Policy/Control
GDF0 EffectiveRuleTopology
GDF1 GameActionContract
```

The item frozen below is a **domain responsibility contract**, not a new semantic primitive.

---

# 1. Frozen responsibility ACD-1 — AuthoritativeCaseDeterminationContract

Apply this contract when a Game/PlayPractice exposes an:

```text
independently meaningful current binding case status
```

A case status is independently meaningful when its:

```text
target/content
binding authority/currentness
or materially relevant determination basis
```

can matter independently from underlying direct execution/event/history semantics.

When the contract applies, preserve enough structure to satisfy the following three obligations.

---

# 2. Obligation ACD-O1 — DeterminationTargetAndStatus

The model must be able to answer:

```text
What is being authoritatively determined?
What current status/result binds?
```

Possible targets include:

```text
action legality/admission
incident status
run/category status
record certification
performance score/status
violation status
contest/result status
qualification/eligibility status
prior determination under review
```

No separate `Case` object is required.

The target may be represented as the object/target of an ordinary F3 relation or F2/F4 status transition.

Strong law:

```text
BareStatusToken != DeterminationIdentity.
```

For example `VALID` without a target does not distinguish action validity, category validity or record certification.

---

# 3. Obligation ACD-O2 — BindingAuthorityAndCurrentness

If a result is called authoritative, the model must be able to resolve enough ordinary F5/F6 structure to answer:

```text
Who/what currently has binding authority for this determination operation?
In what scope?
At what time/version/currentness?
From what authority/provenance source?
```

This does **not** create a GDF3 `DecisionAuthority` primitive.

It consumes ordinary scoped authority relations.

Strong laws:

```text
Classification != BindingDetermination
Correctness != Authority
RoleLabel != AuthorityGrant
RuleChangeAuthority != CaseRulingAuthority
CaseRulingAuthority != EnforcementAuthority
AppointmentAuthority != CaseRulingAuthority
Agent/ModelIdentity != OutputAuthority
```

Same entity may hold several of these authorities in different scopes/operations.

---

# 4. External institution is not required

Binding authority is a relation inside the queried Game/PlayPractice, not a synonym for external bureaucracy.

A solitary/self-authored practice can distinguish:

```text
tentative private belief
```

from:

```text
a declared current self-maintained certification/ruling treated as binding for that practice.
```

Therefore:

```text
ExternalInstitution != necessary condition for PlayPractice authority.
```

A Human, Agent, group, deterministic system or solitary player may occupy the relevant authority role if current practice relations make it so.

---

# 5. Obligation ACD-O3 — TypedDeterminationBasisWhenMaterial

Do not require a universal evidence or reasoning schema.

However, when materially different counterfactuals depend on changing:

```text
case/evidence/canonical-state basis
```

versus changing:

```text
norm/evaluation/application basis
```

preserve enough typed provenance to distinguish them.

Examples:

```text
same run history + different category norm → different certification
same norm + different replay/evidence → different incident ruling
same performance + changed evaluation code → different score
same evidence + changed adopted interpretation → different determination
```

Strong law:

```text
UntypedBasisBag may be insufficient when basis families vary independently.
```

This obligation is conditional.

A closed digital resolver may need only:

```text
canonical state
+ current executable norm
→ result
```

without explicit EvidenceSet or NormApplication object.

---

# 6. Frozen CaseDeterminationBoundary

Ordinary deterministic execution is **not** adjudication by identity.

Examples that need not instantiate the contract:

```text
collision solver
damage formula
cooldown check
closed action legality predicate
physics integration
```

when the output is merely direct current transition/admission semantics.

The same deterministic mechanism **can** instantiate the contract if the Game/Practice gives its output independently meaningful current binding status, for example:

```text
official winner
persistent certification
appealable match result
qualification status
```

Therefore:

```text
Determinism != boundary criterion
Human judgment != boundary criterion
Dispute != boundary criterion
Reviewability != boundary criterion
```

The boundary is whether independently meaningful binding case-status semantics exist.

---

# 7. Determination is not WorldTruth

A current official/practice determination can differ from a richer model of the underlying event/history.

Therefore:

```text
OfficialCaseStatus != WorldTruth
CaseFinding != WorldTruth
Finality != Truth/Correctness
```

Game owns the current binding Game/PlayPractice status.
World owns underlying reality/history/causal counterfactuals.

---

# 8. Determination is not evidence, classification or recommendation

Possible upstream contributions include:

```text
observation
measurement
replay
classification
semantic interpretation
recommendation
precedent argument
community report
model rationale
```

None is binding by identity.

Frozen laws:

```text
Observation != Evidence by identity
Evidence != Claim != WorldTruth
Classification != AuthoritativeDetermination
Interpretation != AuthoritativeDetermination
Recommendation != AuthoritativeDetermination
ModelConfidence != Authority
NaturalLanguageInterpretation != AuthoritativeEffect
```

Binding status comes from current practice authority, not informational content alone.

---

# 9. Determination is not enforcement

A binding ruling may exist even if enforcement:

```text
fails
is delayed
is partial
is implemented by another authority
is later reversed
```

Conversely, one implementation step may both determine and enforce.

That does not erase their semantic separability under counterfactual substitution.

Therefore:

```text
AuthoritativeDetermination != Enforcement.
```

Enforcement/remedy/consequence remains ordinary F4/GDF0/GDF1 transition semantics.

No enforcement object is frozen into ACD.

---

# 10. Review and decision lineage remain derived

Review can change a current determination while preserving the earlier determination as history.

Represent ordinary events such as:

```text
D0
D1 supersedes D0
```

with time/currentness/provenance.

Then derive:

```text
DecisionLineage
ReviewContestabilityTopology
```

as queries/views.

No Review, Appeal, Finality or DecisionLineage primitive is required.

Frozen laws:

```text
Review != Replay
Appeal != GuaranteedCorrection
Reversal != HistoryErasure
Reversal != FullRollback
Finality != Truth/Correctness
```

---

# 11. Rule/norm application remains upstream/derived

GDF3 does not freeze a universal normative reasoning engine.

Current norm basis may involve:

```text
formal rule
standard
evaluation criterion
explicit exception
priority relation
adopted interpretation
current convention
recognized prior case/precedent
purpose/spirit clause
bounded discretion
```

When current authority makes such a relation constitutive of Game semantics, it belongs to GDF0 EffectiveRuleTopology and may appear in typed determination-basis provenance.

Strong laws:

```text
RuleRepresentation != EffectiveRuleTopology
PriorDecision != BindingPrecedent
ConventionFrequency != Authority
Discretion != Arbitrariness
StableRuleRepresentation != StableEffectiveRuleTopology
```

---

# 12. Participation / role / mediation compression

The GDF3 research branch began from a much larger Participation / Role / Mediation / Adjudication continent.

The following did **not** survive as independent foundations:

```text
Participant primitive
Mediation primitive
ParticipationAuthorityTopology responsibility
GlobalAuthorityHierarchy
Delegation primitive
CollectiveAuthority primitive
RoleConflict primitive
```

Keep ordinary:

```text
Entity
Role
RoleAssignment
scoped operation-specific authority relations
```

and derived views when useful.

Strong laws:

```text
Entity != Role != Subject != Player
Participant is scope-qualified, not universal primitive
RoleLabel != ResponsibilityTopology
RoleAssignment != AuthorityGrant
Contribution != BindingAuthority
Advice/Recommendation != Delegation
Authority != GlobalRank
AuthorityTopology != Tree by necessity
```

---

# 13. Human / Agent / collective / solitary neutrality

The frozen contract is substrate-neutral.

Under the same authority/currentness/basis structure:

```text
Human adjudicator
Synthetic adjudicator
committee/aggregation process
solitary self-maintained practice
```

can all produce an authoritative case determination.

No HumanJudge or AIJudge primitive exists.

Same model/entity can hold multiple authority operations:

```text
proposal
interpretation
rule change
case determination
enforcement
```

without semantic fusion.

Frozen law:

```text
SameEntityOrModel != SameAuthorityOperation.
```

---

# 14. Derived research views — useful, not frozen core

The following remain useful projections/views:

```text
RoleAssignment
ScopedAuthorityEdge
RoleCausalAccessProfile
ParticipationAuthorityTopology
ReviewContestabilityTopology
DecisionLineage
NormApplicationBasis detail
InterpretiveCommitment
DiscretionEnvelope
CaseDeterminationBoundary diagnostic
```

They may evolve without reopening v1 unless a frozen law is contradicted.

---

# 15. Explicitly rejected as new primitive or independent responsibility

```text
Participant
Mediation
ParticipationAuthorityTopology
GlobalAuthorityHierarchy
Delegation
CollectiveAuthority
RoleConflict
Evidence
Fact
Interpretation
Classification
Review
Appeal
Contestability
Finality
ReversalAsRollback
NormApplication
Rule
Standard
PurposeEthos
ExceptionDefeater
NormConflict
Precedent
Convention
Discretion
OpenTexture
InterpretiveChange
Retroactivity
HumanJudge
AIJudge
DecisionLineage
Enforcement
```

These labels may remain useful locally; they are not new semantic coordinates/foundations in this v1.

---

# 16. Frozen minimal anti-collapse law set

## Identity / role / authority

```text
Entity != Role != Subject != Player
Participant is scope-qualified, not universal primitive
RoleLabel != ResponsibilityTopology
RoleAssignment != AuthorityGrant
Contribution/Advice/Recommendation != BindingAuthority
Authority != GlobalRank
AuthorityTopology != Tree by necessity
RuleChangeAuthority != CaseRulingAuthority != EnforcementAuthority
AppointmentAuthority != CaseRulingAuthority
SameEntityOrModel != SameAuthorityOperation
```

## Truth / evidence / determination

```text
OfficialCaseStatus != WorldTruth
Observation != Evidence by identity
Evidence != Claim != WorldTruth
Classification/Interpretation/Recommendation != AuthoritativeDetermination by identity
Correctness/ModelConfidence != Authority
NaturalLanguageInterpretation != AuthoritativeEffect
```

## Review / enforcement / history

```text
AuthoritativeDetermination != Enforcement
Finality != Truth/Correctness
Review != Replay
Reversal != HistoryErasure
Reversal != FullRollback
```

## Norm/practice

```text
PriorDecision != BindingPrecedent
ConventionFrequency != Authority
Discretion != Arbitrariness/UnlimitedAuthority
StableRuleRepresentation != StableEffectiveRuleTopology
```

## Boundary

```text
DeterministicExecution != Adjudication by identity
AutomaticExecution != NonAdjudicative by identity
ExternalInstitution != necessary condition for binding PlayPractice authority
```

---

# 17. Explicit owner boundaries

## Game owns

```text
minimum responsibility for independently meaningful current binding Game/PlayPractice case status
case-determination anti-collapse boundary
```

## GDF0 owns

```text
EffectiveRuleTopology
current norm/evaluation structure
rule-change authority/currentness
```

## GDF1 owns

```text
candidate action
admission
execution
consequence
```

## World owns

```text
underlying event/history/reality
causal counterfactuals
```

## Media owns

```text
signals
observation/perception mechanisms
representation support
```

## Human owns

```text
cognition
subjective judgment
fairness perception
experience/acceptance
```

## Social / Institutional owns

```text
broader legitimacy
cultural recognition
institutional trust
```

beyond what local GamePractice consumes as current authority.

## General reasoning owns

```text
logic
argumentation
case-based reasoning
precedent computation
epistemology
```

---

# 18. FoundationReopenConditions

Reopen this v1 only when a concrete repeated phenomenon satisfies one of the following.

## ACD-PRC-1 — Determination identity failure

At least two materially different GameForms expose an independently meaningful binding case status whose target/status identity cannot be represented through existing F1-F9 relations plus this contract without adding a new semantic distinction.

## ACD-PRC-2 — Binding authority failure

Repeated cases cannot distinguish advisory/classificatory output from current binding case status using existing F5/F6 scope/currentness/provenance and operation-specific authority relations.

## ACD-PRC-3 — Determination-basis failure

At least two materially different GameForms require a recurring determination-basis distinction beyond typed case/evidence/canonical-state versus norm/evaluation/application provenance, and the missing distinction changes Game counterfactuals.

## ACD-PRC-4 — CaseDeterminationBoundary failure

The frozen boundary repeatedly misclassifies ordinary direct rule execution as adjudication or repeatedly misses independently meaningful binding case statuses across materially different GameForms, and the error cannot be repaired by scope/currentness/authority/basis qualification.

## ACD-PRC-5 — Lineage/review failure

Repeated review/reversal/supersession cases require a non-derived semantic responsibility that cannot be reconstructed from determination events plus ordinary relation/time/authority/provenance history.

## ACD-PRC-6 — Determination-enforcement entanglement failure

At least two materially different GameForms require enforcement/remedy to be constitutive of determination identity in a way not representable through ordinary F4/GDF0/GDF1 transition relations while preserving `Determination != Enforcement` where counterfactually separable.

## ACD-PRC-7 — Role-fusion/substrate failure

Repeated Human/Agent/collective/solitary or role-fused cases require binding case semantics not expressible through existing entity/role/operation-specific authority/currentness relations, rather than merely a new implementation mechanism.

## ACD-PRC-8 — Ownership/generalization failure

At least two materially different downstream GameForms show that the frozen responsibility either belongs to a more general non-Game foundation or misses a Game-native case-status distinction that cannot be handed to World/Media/Human/Social/GeneralReasoning without explanatory loss.

## ACD-PRC-9 — Repeated downstream contradiction

At least two materially different downstream GameForms repeatedly falsify the same frozen ACD law rather than a derived view, local authority policy, representation choice or implementation mechanism.

A new judge, referee type, category rule, appeals UI, moderation tool, Agent model, deterministic resolver, tournament format or self-authored challenge is **not** itself a reopen condition.

---

# 19. Upstream foundation audit

GDF3-A→F does not force changes to:

```text
R29 / F1-F9
GDF0 Play / Game
GDF1 Action / Control / Skill
GDF2 Challenge / Failure / Mastery
```

All tested cases remain representable with the frozen stack.

Therefore:

```text
R29/F1-F9 reopen = NOT TRIGGERED
GDF0 reopen       = NOT TRIGGERED
GDF1 reopen       = NOT TRIGGERED
GDF2 reopen       = NOT TRIGGERED
```

---

# 20. Freeze evidence

Final GDF3-F evidence includes:

```text
48 boundary cases
22 positive
26 negative
10 final attack questions
10 paired counterfactual families
27 executable audit checks
9 FoundationReopenConditions
```

The final attack specifically covers:

```text
deterministic execution vs deterministic official status
referee/judge/review
TTRPG open case
speedrun certification
judged performance
moderation
adaptive systems
aggregation
retroactive classification
solitary/self-authored practice
Human/synthetic substitution
same-Agent role fusion
review/history
failed/fused enforcement
WorldTruth separation
```

No repeated contradiction remains.

---

# 21. Frozen result

```text
Authoritative Case Determination Foundations v1 = FROZEN
```

Exactly one Game-owned responsibility is frozen:

```text
AuthoritativeCaseDeterminationContract
```

with exactly three obligations:

```text
DeterminationTargetAndStatus
BindingAuthorityAndCurrentness
TypedDeterminationBasisWhenMaterial
```

No new F1-F9 semantic primitive is added.

---

# 22. Post-freeze discipline

This v1 does not select the next Game Deep Foundations branch.

After GDF3 freeze, perform a new:

```text
whole-Game unexplored-space / domain-coverage search
```

before admitting any GDF4.

Previously named residuals are evidence hints only, not a queue.
