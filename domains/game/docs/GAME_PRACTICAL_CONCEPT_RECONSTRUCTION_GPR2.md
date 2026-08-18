---
schema_version: 1
id: game.practical-concept-reconstruction.gpr2
title: Ordivon Game — GPR2 Case Determination & Contestability Toolkit
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Reconstructs practical determination, contestability, review, appeal, lineage, official-status, certification and finality tooling over frozen GDF3 and GPR1 authority. Stabilizes AuthoritativeDeterminationRecord as a conditional source record only where CaseDeterminationBoundary applies; ContestRequestRecord as the optional generic contest workflow source; ReviewRequest/AppealRequest as practice-defined views; and DeterminationBasisTrace, ReviewContestabilityProfile, DecisionLineage, OfficialStatusView, CertificationView and FinalityStatusView as derived projections. Explicitly prevents current Station Zero proposal review, verification, provider decisions, authority-policy decisions and direct World terminal status from being misclassified as adjudication. Fifty-two cross-regime cases, twenty-five executable probes and thirty-six audit checks pass.
evidence_status: strong
readiness: GPR2_COMPLETE
applies_to:
  - ordivon-game
related:
  - game.practical-concept-reconstruction.gpr1
  - game.authoritative-case-determination-foundations.v1
---
# Ordivon Game — GPR2 Case Determination & Contestability Toolkit

## 0. Scope

GPR2 reconstructs the R0 P2 family:

```text
AuthoritativeDeterminationRecord
DeterminationBasisTrace
CaseDeterminationBoundaryDiagnostic
ReviewRequest
AppealRequest
ReviewContestabilityProfile
DecisionLineage
OfficialStatus / Certification
```

and also makes `FinalityStatusView` explicit because practical contestability cannot be consumed cleanly without a Human/Agent-facing current-finality projection.

This is practical reconstruction, not GDF3 reopening.

The frozen GDF3 core remains exactly:

```text
AuthoritativeCaseDeterminationContract
  1. DeterminationTargetAndStatus
  2. BindingAuthorityAndCurrentness
  3. TypedDeterminationBasisWhenMaterial
```

No new semantic primitive is introduced.

---

# 1. Main result

The practical architecture is:

```text
                GPR1 authority / policy
                        ↓
        AuthoritativeDeterminationRecord
                 ↙              ↘
     basis/source refs        lineage relations
            ↓                      ↓
DeterminationBasisTrace       DecisionLineage
                                     ↓
                              OfficialStatusView
                                     ↓
                          CertificationView when applicable

Current determination + GPR1 authority + contest policy
                        ↓
             ReviewContestabilityProfile
                        ↓
              FinalityStatusView
                        ↑
              ContestRequestRecord
                 ↙                ↘
       ReviewRequestView      AppealRequestView
```

The source layer remains sparse.

Persist only when the practice actually has:

```text
independently meaningful binding case status
or
contest/request workflow identity
```

Everything else should usually remain derived.

---

# 2. AuthoritativeDeterminationRecord

GDF3 established that authoritative case determination is a responsibility contract, not a new ontology primitive.

GPR2 now gives that responsibility a practical operational form:

```text
AuthoritativeDeterminationRecord
```

but **only when the frozen CaseDeterminationBoundary applies**.

Minimum practical shape:

```text
determinationId
determinationOperationKey
targetRefOrSelector
statusPayload
scopeRefs
effectiveAt
bindingAuthorityEvidenceRefs
authorityStateDigestOrCurrentnessEvidence
provenanceRefs
```

Optional when material:

```text
effectiveUntilOrOpen
caseBasisRefs
normOrEvaluationBasisRefs
relatedPriorDeterminationRefs
lineageRelationKeys
displaySummary
```

This is intentionally less than a universal `Case` aggregate.

No mandatory:

```text
EvidenceSet
Judge object
Appeal object
rationale
natural-language reasoning
institution
review layer
enforcement record
```

is required.

---

# 3. The determination record must remain conditional

A naive practical reconstruction would attach a `DeterminationRecord` to every result.

That would undo GDF3.

GPR2 therefore freezes:

```text
ordinary direct execution
ordinary action admission
execution verification
provider/model choice
pre-commit proposal review
```

as **not requiring** determination records by default.

The record is admitted only when the Game/PlayPractice exposes an independently meaningful binding status whose:

```text
content/status
binding authority/currentness
or material basis
```

can matter independently from the underlying event/action/history.

---

# 4. CaseDeterminationBoundaryDiagnostic

This frozen GDF3 diagnostic is valuable enough to stabilize as a practical developer tool.

Input questions:

```text
Is there an independently meaningful binding status?
Can that status change while underlying history remains fixed?
Can authority/currentness change while history remains fixed?
Can material basis change the binding status without rewriting history?
```

Output:

```text
applies
not_required
unresolved_owner_semantics
```

Positive signals include:

```text
official winner changes without replaying match
run certification changes without rewriting run history
case ruling changes after review
category status changes under new norm basis
```

Negative signals include:

```text
collision result
ordinary damage formula
action legality predicate
execution verification
pre-commit plan review
Agent candidate selection
```

Critically, these are **not** boundary criteria:

```text
Human vs synthetic
deterministic vs discretionary
disputed vs undisputed
reviewable vs unreviewable
institutional vs solitary
```

---

# 5. Append / supersede rather than rewrite

A practical determination system benefits from durable historical identity.

Suppose:

```text
D0: FOUL
```

and review later produces:

```text
D1: NO_FOUL
```

The correct history is not:

```text
edit D0 in place until it says NO_FOUL
```

but conceptually:

```text
D0 = historical determination
D1 = later determination
D1 reverses / supersedes D0
```

so that:

```text
current official status = D1
history still contains D0
```

This preserves:

```text
Reversal != HistoryErasure.
```

A concrete implementation need not literally be event-sourced, but the semantic history must remain recoverable when audit/currentness matters.

---

# 6. DeterminationBasisTrace

GDF3 rejected universal `Evidence`, `Fact`, `NormApplication` and full reasoning objects.

But practical audit still needs to answer:

```text
What did this determination depend on?
```

So GPR2 stabilizes:

```text
DeterminationBasisTrace
```

as a derived audit projection.

When counterfactually material, it keeps two families distinguishable:

```text
case / evidence / canonical-state basis
```

versus:

```text
norm / evaluation / application basis
```

Example:

```text
same rule + new replay evidence
```

must be distinguishable from:

```text
same replay + new rule/category interpretation
```

because they represent different reasons for status change.

---

# 7. Basis trace is not chain-of-thought

This is especially important for Agent-era systems.

A useful basis trace might say:

```text
caseBasisRefs:
  replay:v2
  timing-log:17

normBasisRefs:
  speedrun-category:any-percent:v5
```

It need not expose:

```text
private hidden reasoning
full natural-language rationale
chain-of-thought
```

Therefore:

```text
DeterminationBasisTrace
!= ReasoningTranscript
!= ChainOfThought.
```

It preserves provenance, not an internal cognitive trace.

---

# 8. ReviewRequest and AppealRequest compress into one generic workflow source

R0 listed both:

```text
ReviewRequest
AppealRequest
```

as possible workflow objects.

GPR2 finds a more reusable structure:

```text
ContestRequestRecord
```

as the optional generic source/workflow identity.

Minimum:

```text
requestId
channelKey
requesterRef
targetDeterminationRefs
requestedAt
requestScopeRefs
requestBasisRefs
provenanceRefs
```

Optional:

```text
requestedTargetAspects
requestedReliefOrOutcomeClass
deadlineEvidenceRefs
relatedRequestRefs
displayReason
```

The owner-local `channelKey` can express:

```text
game.case.review
game.case.appeal
game.case.protest
game.case.reconsideration
tournament.category.challenge
moderation.case.escalation
```

without forcing one universal taxonomy.

---

# 9. Why Review and Appeal remain separate user concepts

Although they can share one workflow substrate, GPR2 does **not** collapse their meanings universally.

We reconstruct:

```text
ReviewRequestView
AppealRequestView
```

as practice-defined projections over `ContestRequestRecord`.

This preserves:

```text
Appeal != Review by universal identity.
```

A local appeal may mean:

```text
narrow error review
de novo hearing
party protest
escalation to another authority
category challenge
```

while another review process may be automatic and not appeal-initiated at all.

Shared workflow machinery does not imply universal semantic identity.

---

# 10. Request lifecycle

A contest request needs practical workflow identity because users and Agents need to know where it is.

Useful projection states:

```text
submitted
admitted
rejected
withdrawn
expired
resolved
unresolved_or_conflicted
```

But the critical separations are:

```text
RequestSubmission != ReviewAdmission
ReviewAdmission != ReviewOutcome
```

A user filing an appeal does not change the ruling by itself.

A request being admitted also does not mean the ruling has been reversed.

---

# 11. A request does not carry reviewer authority

The requester may be:

```text
player
team
coach
moderator
system
operator
```

but reviewer authority comes from GPR1's current authority/policy substrate.

Therefore:

```text
RequesterIdentity != ReviewAuthority.
```

The `ContestRequestRecord` should not silently contain a field such as:

```text
reviewer = X
```

and thereby make X authoritative.

A reviewer assignment can exist operationally, but its binding authority must resolve through current authority sources/profile.

---

# 12. ReviewContestabilityProfile

This becomes the most useful practical query of GPR2.

Question:

> What can currently be contested about this determination, through which channels, by whom, until when, by what authority and with what interim effects?

Inputs:

```text
determinationRef
requesterRef or requester class optional
contextRef
asOfCurrentness
```

Outputs:

```text
contestabilityState
availableChannels
eligibleRequesterRules
reviewAuthorityOperationKeysAndSourceRefs
targetableAspects
deadlineOrCurrentnessBoundaries
stayOrInterimEffectPolicy
possibleDispositionFamilies
sourceRefs
contestabilityStateDigest
```

Useful states:

```text
open
conditional
closed_within_queried_scope
not_applicable
unresolved_or_conflicted
```

---

# 13. Review can target different layers

The phrase “review the decision” hides multiple distinct targets.

A practical profile should be able to expose, when relevant:

```text
determination content/status
case/evidence basis
norm/evaluation/application basis
procedure
binding authority/currentness
enforcement/remedy relation
```

This does not create six new primitives.

It is a UI/tooling decomposition that prevents ambiguity.

For example:

```text
review evidence only
```

is materially different from:

```text
review whether the correct category rule version applied.
```

---

# 14. Review authority consumes GPR1 rather than duplicating it

GPR2 deliberately does not create:

```text
ReviewerAuthorityRecord
AppealAuthorityRecord
HeadJudgeAuthorityRecord
```

Instead a contestability profile resolves an operation such as:

```text
game.case.review
```

through GPR1:

```text
ScopedAuthorityEdge
AuthorityProfile
AuthoritySeparationPolicy
```

This means:

```text
original case authority
review authority
rule-change authority
enforcement authority
```

remain independently configurable.

---

# 15. Contest request does not automatically stay a determination or enforcement

This is a common practical mistake.

Suppose:

```text
Appeal submitted
```

There are at least two valid local policies:

```text
A: sanction continues until appeal succeeds
B: admitted appeal temporarily stays sanction
```

Therefore:

```text
ContestRequest existence
!= automatic stay.
```

The interim effect belongs in:

```text
ReviewContestabilityProfile.stayOrInterimEffectPolicy
```

or another owner-local consequence policy.

This also preserves:

```text
AuthoritativeDetermination != Enforcement.
```

---

# 16. DecisionLineage should be a graph, not a chain

GDF3 already kept DecisionLineage derived.

GPR2 strengthens its practical form:

```text
DecisionLineage = derived graph
```

not necessarily:

```text
D0 → D1 → D2 → D3
```

Why?

Because real practices may contain:

```text
parallel scope/category determinations
separate disciplinary and result review
conflicting current claims awaiting resolution
one new determination referencing multiple earlier records
```

So useful output includes:

```text
nodes
typedRelations
currentDeterminationRefsByScope
historicalDeterminationRefs
branchOrConflictMarkers
sourceRefs
```

---

# 17. Useful lineage relation vocabulary

UI/tools can use relation families such as:

```text
reviews
upholds
modifies
reverses
supersedes
reclassifies
```

but GPR2 does not freeze them as exhaustive ontology.

Local GameForms may add more precise relation keys.

The invariant is that the relationship remains reconstructable enough to distinguish current/historical determinations and explain status transitions.

---

# 18. Review != Replay

A review can use:

```text
same evidence
new evidence
new measurement
new applicable norm
new authority
new procedure
```

without replaying the original event.

Likewise replaying an event does not automatically constitute review.

Therefore:

```text
Review != Replay.
```

This matters directly to current Ordivon because `Replay` already has a strong engineering meaning.

GPR2 must not overload it.

---

# 19. Reversal does not erase World history

Suppose an incident happened and a foul ruling caused gameplay consequences.

Later review reverses the foul ruling.

The Game may or may not be able to restore every consequence.

So:

```text
Reversal != HistoryErasure
Reversal != FullRollback.
```

The lineage changes official determination status.

World correction/remedy remains a separate F4/GDF0/GDF1 concern.

---

# 20. OfficialStatusView

Humans and Agents need a simple answer to:

```text
What is the current official/practice status?
```

So GPR2 reconstructs:

```text
OfficialStatusView
```

from:

```text
DecisionLineage
+ current determination authority/currentness
+ query scope/category
```

Possible output:

```text
targetRef
scopeOrCategoryRef
currentStatusPayload
currentDeterminationRef
effectiveAt/currentness summary
contestability summary
sourceRefs
```

This is deliberately derived.

---

# 21. Official != True

An official status can be:

```text
binding
current
final within current process
```

and still be factually mistaken.

Therefore the UI can safely say:

```text
Official result: Player A wins
```

only if the semantics remain:

```text
current practice status
```

not:

```text
metaphysical truth about everything that happened.
```

Strong law:

```text
OfficialCaseStatus != WorldTruth.
```

---

# 22. Multiple official statuses can coexist by scope

The same speedrun may be:

```text
VALID — Any%
INVALID — No Major Glitches
```

without contradiction.

Likewise one event can have different status under:

```text
match result
conduct policy
record category
eligibility process
```

Therefore `OfficialStatusView` must always be scope/category aware.

A global `official=true` flag is insufficient.

---

# 23. CertificationView must be separated from OfficialStatusView

R0 initially grouped:

```text
OfficialStatusCertificationView
```

GPR2 splits it.

Why?

Because:

```text
referee foul ruling
```

can be official without being a certification workflow.

Certification is a specialized determination operation such as:

```text
game.result.certify
game.record.certify
game.category.verify-and-certify
```

So:

```text
OfficialStatusView = generic current binding status projection
CertificationView = specialized projection when certification semantics apply
```

Strong law:

```text
OfficialStatus != Certification by identity.
```

---

# 24. Verification != Certification

This is particularly important because current Ordivon Game already has `VerificationReceipt`.

A verification receipt says something like:

```text
observed effect matches expected retained execution facts
```

A certification determination says:

```text
this run/result currently has binding official status in category C
```

The former may be evidence for the latter.

But:

```text
Verification != CertificationByIdentity.
```

This lets us keep existing verification machinery exactly where it belongs.

---

# 25. FinalityStatusView

`Final` is too useful a UI word to discard.

GPR2 therefore reconstructs it as a derived query:

```text
FinalityStatusView
```

with states such as:

```text
pending_or_not_current
current_and_contestable
current_and_conditionally_contestable
current_and_closed_within_queried_scope
superseded_or_historical
unresolved_or_conflicted
```

The key wording is:

```text
closed_within_queried_scope
```

not:

```text
immutable forever.
```

---

# 26. Finality != Truth / Correctness / Eternal Immutability

A ruling can be:

```text
currently final
```

but wrong.

A later rule/policy change can create a new review channel.

That does not rewrite what the previous process considered final at the time.

So:

```text
Finality != Truth
Finality != Correctness
Finality != EternalImmutability.
```

This makes `Final` safe as a user-facing shorthand.

---

# 27. Current Station Zero — proposal review

The current product uses `proposal-review` heavily.

But its semantics are:

```text
Agent/team proposes action
player inspects pending proposal
player may approve/deny/intervene
then action may be committed
```

There is no prior independent authoritative case status being reviewed.

So GPR2 classifies this as:

```text
PRE_COMMIT_PROPOSAL_REVIEW_NOT_CASE_REVIEW
```

This is not a defect.

It simply means the same natural-language word `review` names a different workflow.

Strong practical guard:

```text
ProposalReview != CaseReviewByIdentity.
```

---

# 28. Current Station Zero — VerificationReceipt

Current World and embedded Host verification validate execution/effect evidence.

This is valuable and should remain.

Classification:

```text
EXECUTION_VERIFICATION_EVIDENCE_NOT_CERTIFICATION
```

A future tournament/speedrun/certification GameForm could use a VerificationReceipt as:

```text
caseBasisRef
```

inside an `AuthoritativeDeterminationRecord`.

But the receipt itself remains verification.

---

# 29. Current Station Zero — AuthorityDecision

Current `AuthorityDecision` returns:

```text
permit
require-human
deny
```

for an action candidate under a local authority policy.

That is:

```text
ACTION_AUTHORITY_POLICY_DECISION_NOT_CASE_DETERMINATION
```

because it resolves whether/how an action may proceed rather than establishing an independent official case status.

Thus:

```text
AuthorityDecision != CaseDeterminationByIdentity.
```

---

# 30. Current Agent/provider decisions are also not case determinations

A model can produce:

```text
candidate choice
confidence
rationale
directive choice
```

These remain cognition/policy outputs.

Without current binding case authority and the GDF3 boundary:

```text
ProviderDecision != AuthoritativeDeterminationByIdentity.
```

Model fluency, confidence or rationale does not alter this.

---

# 31. Current World mission status is not automatically a determination

Station Zero's:

```text
running
victory
failure
```

is currently generated directly by authoritative deterministic World transition semantics.

There is not presently a second practice layer saying:

```text
World says victory
but official status separately says pending certification
```

Therefore current classification is:

```text
AUTHORITATIVE_WORLD_STATE_NOT_SEPARATE_CASE_DETERMINATION
```

This is another protection against over-modeling.

If a future GameForm introduces independent certification/record status, then GPR2 becomes relevant.

---

# 32. Current Replay/Diagnosis is not DecisionLineage

Ordivon Game already reconstructs replay/evidence/authority chains and counterfactual diagnosis.

That is not the same as:

```text
DecisionLineage
```

because there are currently no multiple superseding authoritative case determinations to connect.

Classification:

```text
DERIVED_HISTORY_DIAGNOSIS_NOT_DECISION_LINEAGE
```

Again, no refactor is justified merely because both are graphs over history.

---

# 33. Deterministic official results remain valid GPR2 consumers

One of the most important GDF3 results survives practical reconstruction:

```text
DeterministicExecution != AdjudicationByIdentity.
```

A deterministic tournament calculator can produce a GPR2 determination if its output is the independently meaningful official result.

A deterministic collision solver need not.

The dividing line is role in the practice, not algorithmic determinism.

---

# 34. Solitary practice remains supported

A single player can define a practice in which:

```text
explicit self-check
→ binding certification for personal challenge record
```

That can legitimately use an `AuthoritativeDeterminationRecord`.

But:

```text
private guess: maybe I violated the rule
```

is still just a belief/classification.

So GPR2 preserves:

```text
ExternalInstitution != NecessaryForBindingPracticeStatus.
```

---

# 35. Agent adjudicators remain substrate-neutral

If an Agent has current GPR1 authority for:

```text
game.case.decide
```

then an output admitted under that operation can become an authoritative determination.

If the same model merely classifies/recommends, it does not.

Similarly:

```text
provider A → provider B
```

need not alter semantic authority if the same role/authority/currentness contract remains.

Thus:

```text
ModelIdentity != OutputAuthority.
```

---

# 36. Review authority may differ from original case authority

Example:

```text
Floor Judge:
  game.case.decide

Head Judge:
  game.case.review
```

The `ReviewContestabilityProfile` resolves the second through GPR1.

No global rank is needed.

This preserves:

```text
ReviewAuthority != OriginalCaseAuthorityByIdentity.
```

---

# 37. Separation policy remains configurable

GPR1 allows:

```text
self_review_prohibited
```

as one optional practice policy.

So:

```text
solitary challenge
```

may allow self-reconsideration,

while:

```text
tournament
```

may require a different reviewer.

GPR2 consumes that policy rather than hard-coding either answer.

---

# 38. Parallel contest channels

A determination may expose multiple independent channels:

```text
result appeal
conduct review
category challenge
technical verification protest
```

with different:

```text
requester eligibility
review authority
deadlines
targetable aspects
interim effects
```

Therefore `ReviewContestabilityProfile` must return a set of available channels rather than one Boolean `appealable`.

This is a strong practical improvement over conventional schemas.

---

# 39. Conflict and unresolved states must be representable

Suppose two authority sources appear to produce incompatible current determinations in the same queried scope.

The toolkit must not silently choose one through:

```text
latest timestamp
largest scope
highest role label
```

unless local policy explicitly defines that resolution.

Instead derived views can report:

```text
unresolved_or_conflicted
```

until owner-local authority/currentness semantics resolve it.

This carries GPR1's anti-global-rank discipline into GPR2.

---

# 40. The 11 GPR2 practical verdicts

| Concept | GPR2 verdict |
| --- | --- |
| AuthoritativeDeterminationRecord | **conditional source record** |
| DeterminationBasisTrace | **derived audit view** |
| CaseDeterminationBoundaryDiagnostic | **derived developer diagnostic** |
| ContestRequestRecord | **conditional generic workflow source** |
| ReviewRequestView | **practice-defined view over contest workflow** |
| AppealRequestView | **practice-defined view over contest workflow** |
| ReviewContestabilityProfile | **derived policy + authority view** |
| DecisionLineage | **derived graph, not chain** |
| OfficialStatusView | **derived Human/Agent view** |
| CertificationView | **specialized derived view** |
| FinalityStatusView | **derived UI query** |

This is smaller and cleaner than creating separate canonical objects for every familiar legal/sports workflow word.

---

# 41. Cross-cutting practical law set

```text
OfficialCaseStatus != WorldTruth
AuthoritativeDetermination != Enforcement
Verification != CertificationByIdentity
Verification != AdjudicationByIdentity
ProposalReview != CaseReviewByIdentity
ProviderDecision != AuthoritativeDeterminationByIdentity
AuthorityDecision != CaseDeterminationByIdentity
WorldTerminalState != OfficialCaseDeterminationByIdentity
DeterministicExecution != AdjudicationByIdentity
ReviewRequest != ReviewAdmission
ReviewAdmission != ReviewOutcome
Appeal != ReviewByUniversalIdentity
Appeal != GuaranteedCorrection
Review != Replay
Reversal != HistoryErasure
Reversal != FullRollback
DecisionLineage != SingleChainByNecessity
Finality != Truth
Finality != Correctness
OfficialStatus != CertificationByIdentity
Contestability != DeterminationContent
RequesterIdentity != ReviewAuthority
ReviewAuthority != OriginalCaseAuthorityByIdentity
DeterminationBasisTrace != ChainOfThought
ExternalInstitution != NecessaryForBindingPracticeStatus
```

---

# 42. Why GPR2 should not be implemented broadly yet

Unlike GPR1, which already overlaps strongly with current authority/product mechanics, GPR2 currently has **no proven direct Station Zero consumer**.

Station Zero currently has:

```text
proposal review
one-shot action authorization
execution verification
World victory/failure
replay/diagnosis
```

but no independently persistent official case-status layer with review/appeal/certification lineage.

So adding generic tables such as:

```text
determinations
appeals
reviews
certifications
```

would currently be speculative framework construction.

GPR2 therefore freezes practical contracts but defers broad implementation.

---

# 43. What could be implemented safely before a consumer exists

The lowest-risk immediate candidates are developer/tooling aids:

```text
CaseDeterminationBoundary lint/diagnostic
terminology checks distinguishing proposal review vs case review
terminology checks distinguishing verification vs certification
pure derived views only after a concrete determination source appears
```

No persistent generic adjudication subsystem is currently justified.

---

# 44. Evidence

GPR2 completes:

```text
11 practical contracts
52 cross-regime stress cases
25 executable probes
36 audit checks
25 cross-cutting laws
6 current-engineering classifications
```

Stress coverage includes:

```text
direct physics/action admission
verification
pre-commit review
provider decisions
authority-policy decisions
World terminal states
automated official results
sports/VAR
TTRPG GM
solitary practice
speedrun certification/reclassification
judged scoring
moderation
review uphold/modify/reverse
appeal admission/deadline/de novo/stay
basis changes
Agent adjudication/provider substitution
parallel review channels
conflicting determinations
finality changes
certification revocation
self-review policy
```

No GDF0-GDF3 reopen condition is triggered.

---

# 45. Final architecture

The practical lesson is:

```text
Do not expose raw GDF3 everywhere.
Do not restore Review/Appeal/Finality as ontology.
Do not flatten every 'decision' into adjudication.
```

Instead:

```text
conditional determination source
+ optional generic contest workflow
+ current GPR1 authority/policy
+ rich derived status/lineage/contestability views
```

This gives players, operators and Agents familiar concepts such as:

```text
Official
Certified
Appeal
Review
Final
History
```

while preserving the deeper distinctions that GDF3 established.

---

# 46. Next practical reconstruction round

R0 ranked P3 after Role/Authority and Case/Contestability.

GPR2 now provides the case-status substrate it needs.

The next round is therefore:

```text
GPR3 — Evidence / Norm / Explanation Toolkit
```

Targets:

```text
EvidenceBundleForCase
NormApplicationView
InterpretiveCommitment
PrecedentLink
ConventionStatusView
DiscretionEnvelope
VerificationView
```

GPR3 should specifically determine how much explanation/audit structure is useful without reintroducing `Evidence = Truth`, `Precedent = Authority`, `Convention = Rule`, or a universal norm-reasoning engine.
