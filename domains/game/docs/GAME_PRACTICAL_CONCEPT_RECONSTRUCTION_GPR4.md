---
schema_version: 1
id: game.practical-concept-reconstruction.gpr4
title: Ordivon Game — GPR4 Enforcement / Remedy Toolkit
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Reconstructs practical enforcement and remedy over frozen GDF0-GDF3 plus GPR1-GPR3. Rejects a generic second executor and instead separates authoritative consequence directive, concrete enforcement attempt, actual World effect, derived enforcement status, corrective remedy plan/status and a cross-layer audit timeline. Existing TeamEffect/Dispatch/Observation/Verification/idempotent recovery are classified as strong generic execution substrate, not enforcement by identity. Remedy is forward corrective work and may restore, substitute, compensate or explicitly preserve irreversibility; it is never automatic rollback/history erasure. Sixty cross-regime stress cases, twenty-nine executable probes and thirty-seven audit checks pass.
evidence_status: strong
readiness: GPR4_COMPLETE
applies_to:
  - ordivon-game
related:
  - game.practical-concept-reconstruction.gpr1
  - game.practical-concept-reconstruction.gpr2
  - game.practical-concept-reconstruction.gpr3
  - game.authoritative-case-determination-foundations.v1
---
# Ordivon Game — GPR4 Enforcement / Remedy Toolkit

## 0. Scope

GPR4 reconstructs R0 P4:

```text
EnforcementRecord
RemedyPlan
```

but does not assume those initial names survive intact.

The frozen GDF3 law is:

```text
AuthoritativeDetermination != Enforcement.
```

GPR4 asks:

> Once a binding determination or practice says that some consequence should occur, what practical structure is needed to distinguish the ordered consequence, attempts to realize it, what actually happened in the World, and any later corrective work?

No GDF0-GDF3 foundation is reopened.

---

# 1. Main result

The naive model:

```text
EnforcementRecord {
  ruling
  executor
  status
  result
  remedy
}
```

is too collapsed.

GPR4 stabilizes this decomposition:

```text
GPR2 AuthoritativeDetermination
          │
          ↓
ConsequenceDirectiveRecord
          │
          ↓
EnforcementAttemptRecord
          │
          ↓
ordinary GDF1 / execution / dispatch
          │
          ↓
World history / observation / verification
          │
          ↓
RealizedConsequenceView
          │
          ↓
EnforcementStatusView

review / reversal / execution error / harm
          │
          ↓
RemedyPlanRecord
          │
          ↓
ordinary execution or new directives
          │
          ↓
RemedyStatusView
```

A derived `EnforcementRemedyTimeline` can expose the complete history without merging semantic event types.

---

# 2. Enforcement is not another executor

Current Game already owns effect realization through ordinary mechanisms:

```text
GameAction
TeamEffect
Dispatch
World transition
Observation
Verification
```

A generic enforcement subsystem should **not** implement another path such as:

```text
EnforcementExecutor.apply(...)
```

that competes with the World/action executor.

Instead:

```text
Enforcement
= authoritative consequence workflow
  linked to ordinary execution.
```

This is the central GPR4 architectural decision.

---

# 3. Same operation can be ordinary action or enforcement

Suppose an operation removes an item.

It could be:

```text
ordinary gameplay trade
consumption
scripted hazard
player discard
administrative consequence
corrective restoration workflow
```

The operation name does not tell us whether it is enforcement.

Therefore:

```text
OrdinaryExecution != EnforcementByOperationName.
```

Enforcement comes from its relation to a current authoritative directive/practice, not from verbs such as:

```text
remove
restrict
restore
repair
```

---

# 4. ConsequenceDirectiveRecord

The first practical source is:

```text
ConsequenceDirectiveRecord
```

It represents:

> An authoritative instruction that a consequence should be attempted or maintained.

Minimum practical fields:

```text
directiveId
sourceDeterminationRefsOrPracticeBasisRefs
directiveOperationKey
targetRefsOrSelectors
desiredConsequenceSpecRefOrPayload
scopeRefs
effectiveFrom
effectiveUntilOrOpen
enforcementAuthorityBasisRefs
provenanceRefs
```

Optional:

```text
priority/scheduling
stay policy
revocation/supersession
executor eligibility
display summary
```

---

# 5. A directive should exist only when the order itself matters

Not every consequence needs a directive record.

For example:

```text
player attacks enemy
→ current rule immediately reduces health
```

is ordinary direct Game execution.

No separate:

```text
ConsequenceDirectiveRecord
```

is useful.

But if:

```text
referee ruling
→ player should receive consequence C
→ another system/person may execute C later
```

then the directive has independent:

```text
identity
currentness
authority
scheduling
stay/revocation
execution status
```

and deserves a record.

---

# 6. Determination != directive

A determination answers:

```text
What binding case status holds?
```

A consequence directive answers:

```text
What consequence should now be effectuated?
```

One determination can produce:

```text
zero directives
one directive
multiple directives
```

For example, one result could lead to:

```text
official score correction
+ temporary gameplay restriction
```

as separate directive identities.

Thus:

```text
Determination != ConsequenceDirective by identity.
```

---

# 7. Enforcement authority remains separate

GPR1 already proved operation-specific authority.

GPR4 consumes it.

Someone who may decide a case need not be allowed to execute the consequence.

Likewise an executor may be technically capable without possessing authority.

Therefore:

```text
DeterminationAuthority
!= EnforcementAuthority
!= ExecutorCapability.
```

No `Judge > Moderator > Operator` global rank is needed.

---

# 8. EnforcementAttemptRecord

A directive still does not say whether anyone actually tried to realize it.

GPR4 therefore stabilizes:

```text
EnforcementAttemptRecord
```

as a conditional execution-link record.

Minimum:

```text
attemptId
directiveRef
attemptedAt
executorRef
executionAuthorityEvidenceRefs
executionRequestOrActionRefs
requiredStateOrCurrentnessRefs
idempotencyOrAttemptIdentityRef
provenanceRefs
```

Optional:

```text
retryOfAttemptRef
parentAttemptRef
scheduledFor
cancellation/abort refs
```

---

# 9. Attempt records link to execution; they do not copy execution

The attempt should point to:

```text
GameAction
Dispatch
World command
execution request
```

rather than duplicating their payload and result.

The actual result continues to belong to:

```text
ordinary execution
World history
observation
verification
```

Therefore:

```text
EnforcementAttemptRecord
= workflow identity + execution linkage
```

not a new executor truth record.

---

# 10. Attempt != success

This distinction is basic but operationally crucial.

A legitimate attempt may become:

```text
rejected because World is stale
executor unavailable
interrupted
contested
no effect
partially effective
unknown after network loss
```

So:

```text
Attempt != Success
Attempt != RealizedConsequence.
```

A directive may remain active after a failed attempt.

---

# 11. Retry is not necessarily repeated enforcement

Current Game already demonstrates a valuable exact property:

```text
World effect committed
response lost
same command retried
→ idempotent recovery returns retained result
→ no second World effect
```

GPR4 generalizes:

```text
Retry != DuplicateConsequenceByIdentity
IdempotentRecovery != RepeatedEnforcementByIdentity.
```

A future EnforcementAttempt must therefore preserve attempt/idempotency identity strongly enough to distinguish:

```text
retry/reconciliation
```

from:

```text
new independent enforcement attempt.
```

---

# 12. Current TeamEffect is not a consequence directive

Current `TeamEffect` contains:

```text
effectId
tickPlanId
requiredWorldRevision
requiredWorldDigest
status
```

This is excellent execution preparation/currentness infrastructure.

But it is used for ordinary team gameplay.

GPR4 classifies it:

```text
GENERIC_EXECUTION_EFFECT_PREPARATION_NOT_ENFORCEMENT_DIRECTIVE
```

A future consequence directive may compile into or reference a TeamEffect-like execution object.

The two should not be identified.

---

# 13. Current TeamDispatch is not enforcement by identity

`TeamDispatch` provides:

```text
execution request identity
command id
status
World event link
error
```

and Host dispatch also provides:

```text
executorId
idempotencyKey
requiredStateRefs
expectedObservationKind
```

This is precisely the sort of lower mechanism an `EnforcementAttemptRecord` should reuse.

Classification:

```text
GENERIC_EXECUTION_DISPATCH_NOT_ENFORCEMENT_ATTEMPT_BY_IDENTITY
```

because ordinary gameplay also dispatches.

---

# 14. Observation is the first strong realized-effect source

Current Team observation records:

```text
dispatch
WorldEvent
post-state digest
intent command ids
verified intent ids
facts
verification success
```

This is excellent lower evidence for:

```text
What actually happened?
```

GPR4 classifies:

```text
TeamObservation
= GENERIC_REALIZED_EFFECT_EVIDENCE
```

A future enforcement layer should consume it rather than invent its own result truth.

---

# 15. RealizedConsequenceView

GPR4 stabilizes:

```text
RealizedConsequenceView
```

as a derived comparison between:

```text
desired consequence
```

and:

```text
actual World effects.
```

Possible output:

```text
desiredConsequenceSummary
observedEffectRefs
verifiedEffectRefs
realizationClass
missingOrUnexpectedEffects
irreversibleOrNonRestorableEffectsWhenKnown
sourceRefs
```

Useful classes:

```text
not_observed
no_effect
partial
as_directed
deviated_or_over_enforced
unknown_or_unverified
```

---

# 16. World history remains authoritative

The RealizedConsequenceView must never become another source of what happened.

The truth direction is:

```text
World/history/facts/observation
→ RealizedConsequenceView
```

not:

```text
RealizedConsequenceView.status = success
→ assume World changed.
```

Therefore:

```text
WorldHistoryRemainsSourceOfRealizedEffectTruth.
```

---

# 17. Dispatch success != consequence success

An execution dispatch can succeed while the desired consequence fails.

Examples:

```text
target disappeared
condition changed
operation returns no effect
only some targets changed
extra unintended effect occurred
```

So:

```text
DispatchSucceeded
!= DesiredConsequenceRealizedByIdentity.
```

This validates the separate realization comparison.

---

# 18. Verification success can still be narrower than directive satisfaction

A verification method may prove:

```text
command produced retained World event
all selected intents were verified
record digest is intact
```

without proving every desired consequence goal.

Therefore:

```text
VerificationSuccess
!= FullConsequenceSatisfactionByIdentity.
```

GPR3's `VerificationView` feeds GPR4; it does not replace consequence evaluation.

---

# 19. Partial enforcement != partial determination

Suppose a determination orders three independent consequences and only two are realized.

The source determination may still be completely valid/current.

So:

```text
PartialEnforcement
!= PartialDetermination.
```

This distinction is essential for audit and retry logic.

---

# 20. Failed enforcement != invalid determination

Likewise:

```text
executor unavailable
stale state
technical failure
blocked target
```

can prevent enforcement without changing the underlying authoritative status.

Therefore:

```text
FailedEnforcement != InvalidDetermination.
```

A later attempt may legitimately succeed.

---

# 21. EnforcementStatusView

Humans and Agents need one current answer to:

```text
Has this ordered consequence actually happened?
```

GPR4 therefore stabilizes:

```text
EnforcementStatusView
```

Possible states:

```text
pending_or_not_attempted
scheduled_or_deferred
stayed_or_suspended
attempting_or_unknown
partially_realized
realized_as_directed
realized_with_deviation
failed_or_unrealized
revoked_or_superseded
conflicted_or_unresolved
```

This is a derived workflow view over directive + attempts + actual execution evidence.

---

# 22. Stay does not erase determination or directive

A contestability policy may temporarily stop execution.

This means:

```text
EnforcementStatus = stayed_or_suspended
```

not necessarily:

```text
Determination = erased
Directive never existed.
```

Therefore:

```text
Stay != DeterminationErasure.
```

The current directive may be suspended, not deleted.

---

# 23. Revocation after realization does not undo the World

Suppose a directive is executed at T1.

At T2 review reverses it.

Changing current directive state to:

```text
revoked_or_superseded
```

cannot make the T1 event disappear.

Therefore:

```text
RevocationOfFutureEnforcement
!= UndoOfPastEffect.
```

This is where remedy begins.

---

# 24. Remedy is not rollback

This is the central P4 correction.

A naive model says:

```text
wrong consequence
→ rollback
```

But many Game effects are:

```text
irreversible
socially observed
strategy-altering
resource-consuming
time-dependent
competition-dependent
```

Even when state variables can be numerically restored, the original history cannot always be recreated.

Therefore:

```text
Remedy != Rollback
Remedy != HistoryErasure
Restoration != ExactHistoricalReversal.
```

---

# 25. RemedyPlanRecord

GPR4 stabilizes:

```text
RemedyPlanRecord
```

as a conditional corrective workflow.

Minimum:

```text
remedyPlanId
triggerRefs
correctiveGoalRefsOrSpecs
scopeRefs
effectiveFrom
remedyAuthorityBasisRefs
provenanceRefs
```

Optional:

```text
affected subjects
candidate corrective actions
priority/sequencing
non-restorable facts
compensation/substitute goals
completion policy
supersession
```

---

# 26. Remedy is goal-directed forward correction

The most useful general model is:

```text
current damaged/incorrect situation
+ recognized corrective goals
+ current constraints
→ forward corrective action
```

rather than:

```text
rewind history.
```

A remedy may be:

```text
restore state
replace object
correct official record
repeat/replay opportunity
compensate value
remove future restriction
issue substitute benefit
acknowledge unrepairable loss
```

depending on current practice.

---

# 27. Compensation is a first-class remedy form

Suppose a player loses an opportunity that cannot be replayed.

Exact restoration is impossible.

A practice may instead provide:

```text
rematch
ranking adjustment
substitute reward
future benefit
other compensation
```

Thus:

```text
CompensationCanBeRemedyWithoutRestoration.
```

This is not an exception; it is a central reason Remedy must not equal rollback.

---

# 28. Correct determination can still require remedy

A useful counterexample:

```text
determination = correct
ordered consequence = correct
enforcement implementation targets wrong entity
```

Now the original determination does not need reversal.

But the erroneous execution may require correction.

Therefore:

```text
CorrectDeterminationCanStillRequireRemedyForExecutionError.
```

Remedy cannot be modeled only as a child of reversal.

---

# 29. Conversely, faithful enforcement can later require remedy

Another case:

```text
D0 was current and binding
executor faithfully realized D0
later review reverses D0
```

The enforcement may have been procedurally correct at the time.

Yet its realized effects may now justify corrective work.

Thus:

```text
Enforcement correctness at T1
```

and:

```text
current remedial need at T2
```

are distinct questions.

---

# 30. Remedy authority remains separate

The actor authorized to decide a case may differ from the actor authorized to:

```text
approve compensation
restore records
change inventory
schedule rematch
```

Therefore:

```text
CaseAuthority
ReviewAuthority
EnforcementAuthority
RemedyAuthority
ExecutionCapability
```

can all differ.

GPR1 already provides the correct substrate; GPR4 introduces no new global hierarchy.

---

# 31. Remedy actions should reuse ordinary execution too

GPR4 does not create:

```text
RemedyExecutor
```

as a parallel physical effect system.

Actual corrective operations should still use:

```text
GDF1 action/execution
World transition
normal dispatch
verification
```

If the practice treats the corrective goal as an authoritative directive, it can use:

```text
RemedyPlan
→ ConsequenceDirective
→ EnforcementAttempt
→ ordinary execution
```

This keeps one effect-realization path.

---

# 32. RemedyPlan != realized remedy

A plan can be:

```text
approved
scheduled
attempted
blocked
partially completed
superseded
```

without its goals being satisfied.

Therefore:

```text
RemedyPlan != RealizedRemedy.
```

GPR4 stabilizes a separate `RemedyStatusView`.

---

# 33. RemedyStatusView

Useful states:

```text
planned
in_progress
partially_satisfied
satisfied_as_planned
satisfied_by_substitute_or_compensation
blocked_or_impossible
abandoned_or_superseded
unknown_or_unverified
```

Output can include:

```text
goal satisfaction
corrective actions/directives
realized effects
remaining irreversibility/loss
compensation
verification
source refs
remedyStateDigest
```

This makes incomplete correction explicit.

---

# 34. Partial remedy should expose irreversibility

Example:

```text
item restored = yes
lost match time restored = impossible
```

The view should say:

```text
partially_satisfied
remaining loss = lost opportunity/time
```

rather than pretending:

```text
rollback complete.
```

This is especially important in competitive and persistent games.

---

# 35. A remedy can itself fail or over-correct

Corrective execution is still execution.

It can:

```text
fail
partially work
hit wrong target
produce excess compensation
become stale
```

So remedy is not a magic trusted operation.

It still needs ordinary:

```text
currentness
execution
observation
verification
```

boundaries.

---

# 36. Reversal does not universally create a right to remedy

Some practices may define:

```text
review can correct official record
but irreversible historical gameplay remains as played
```

with no compensation.

GPR4 therefore does **not** freeze:

```text
Reversal → RemedyPlan always.
```

Remedy entitlement and corrective goals are owner-local practice semantics.

---

# 37. Current Station Zero `repair` is not Remedy

Current Game has:

```text
repair
field-repair
support-civilian-recovery
```

These are normal Game operations/objectives.

They are not responses to an erroneous determination/enforcement merely because English uses the word `repair` or `recovery`.

Classification:

```text
ORDINARY_GAMEPLAY_REPAIR_NOT_REMEDY
```

Strong law:

```text
RepairAction != RemedyByIdentity.
```

---

# 38. Technical rollback is not Game remedy

Current storage tests correctly guarantee:

```text
pre-commit failure
→ no partial World effect escapes
```

This is transactional atomicity.

It is **not**:

```text
Game remedy after a realized consequence.
```

Therefore:

```text
TechnicalRollback != GameRemedyByIdentity.
```

This prevents a common cross-layer terminology error.

---

# 39. Technical recovery is also not remedy

Current Game also supports:

```text
after-commit response failure
→ recover retained committed event
→ idempotent retry
```

This is technical recovery/reconciliation.

It does not mean the Game is correcting an unjust/incorrect consequence.

Its practical value for GPR4 is instead:

```text
proof that retries can preserve one-effect semantics.
```

---

# 40. Station Zero intent statuses are valuable lower patterns

Current resolution distinguishes:

```text
executed
interrupted
invalidated
contested
no_effect
```

This is excellent evidence that:

```text
attempt
```

and:

```text
realized effect
```

should remain separate.

But these statuses describe ordinary tactical actions.

They should not be renamed globally as enforcement states.

---

# 41. Continuous consequences need interval realization

Not every directive is a one-shot transition.

Example:

```text
maintain restriction for interval T0–T10
```

A single success event at T0 does not prove complete realization.

The `RealizedConsequenceView` may need to compare:

```text
desired maintained condition
```

against World state/history over an interval.

This is another reason to separate directive from action attempt.

---

# 42. Conflicting directives should fail visible

Two current authority sources may apparently order incompatible consequences.

GPR4 must not resolve this through:

```text
latest timestamp wins
broader scope wins
higher role label wins
```

unless owner-local policy says so.

Instead:

```text
EnforcementStatusView = conflicted_or_unresolved
```

until current authority/policy resolves it.

GPR1's anti-global-rank discipline survives intact.

---

# 43. Agent execution remains substrate-neutral

An Agent can:

```text
propose directive
execute directive
verify effect
propose remedy
```

but none of these becomes authoritative merely because a model produced it.

The relevant boundaries remain:

```text
current authority
currentness
ordinary action admission
actual World effect
verification
```

Provider/model substitution alone need not change enforcement semantics.

---

# 44. Generated status cannot override World truth

A summary Agent might say:

```text
Consequence completed.
```

If the World/history/observation shows no effect, the summary is wrong.

Therefore:

```text
GeneratedEnforcementStatus != WorldEffectTruth.
```

This mirrors GPR3's:

```text
GeneratedExplanation != AuthoritativeEffect.
```

---

# 45. EnforcementRemedyTimeline

For Human/Agent audit, GPR4 reconstructs a derived timeline showing distinct event families:

```text
determination
directive issued/changed
stay/resume
attempt/retry
execution observed
verification
realization status
review/reversal
remedy plan
corrective attempt/effect
remedy status
```

The timeline must preserve labels rather than flatten all of them into generic `events`.

This provides a complete narrative without semantic collapse.

---

# 46. Timeline order is not causation or authority

A timeline is a visualization/audit projection.

It does not establish:

```text
A happened before B
→ A authorized B
→ A caused B
```

Those relations must come from explicit provenance/authority/causal semantics.

Thus:

```text
Chronology != Authority
Chronology != Causation.
```

---

# 47. Seven GPR4 practical verdicts

| Concept | GPR4 verdict |
| --- | --- |
| ConsequenceDirectiveRecord | **conditional source/workflow** |
| EnforcementAttemptRecord | **conditional execution-link record** |
| EnforcementStatusView | **derived workflow view** |
| RealizedConsequenceView | **derived World-effect comparison** |
| RemedyPlanRecord | **conditional corrective workflow** |
| RemedyStatusView | **derived corrective status view** |
| EnforcementRemedyTimeline | **derived audit timeline** |

R0's broad `EnforcementRecord` therefore does **not** survive as one monolithic record.

It decomposes into source/workflow + derived views.

---

# 48. Strong practical law set

```text
AuthoritativeDetermination != Enforcement
DeterminationAuthority != EnforcementAuthorityByIdentity

ConsequenceDirective != EnforcementAttempt
EnforcementAttempt != RealizedWorldEffect
Attempt != Success

DispatchAccepted != EnforcementSucceededByIdentity
DispatchSucceeded != DesiredConsequenceRealizedByIdentity
VerificationSuccess != FullConsequenceSatisfactionByIdentity

FailedEnforcement != InvalidDetermination
PartialEnforcement != PartialDetermination

Stay != DeterminationErasure
RevocationOfFutureEnforcement != UndoOfPastEffect

Retry != DuplicateConsequenceByIdentity
IdempotentRecovery != RepeatedEnforcementByIdentity

OrdinaryExecution != EnforcementByOperationName
RepairAction != RemedyByIdentity
TechnicalRollback != GameRemedyByIdentity

Reversal != AutomaticUndo
Reversal != FullRollback

Remedy != Rollback
Remedy != HistoryErasure
RemedyPlan != RealizedRemedy
Restoration != ExactHistoricalReversal
CompensationCanBeRemedyWithoutRestoration

CorrectDeterminationCanStillRequireRemedyForExecutionError

WorldHistoryRemainsSourceOfRealizedEffectTruth
GeneratedEnforcementStatus != WorldEffectTruth
```

---

# 49. Current engineering audit

## TeamEffect

```text
GENERIC_EXECUTION_EFFECT_PREPARATION_NOT_ENFORCEMENT_DIRECTIVE
```

Keep.

## TeamDispatch

```text
GENERIC_EXECUTION_DISPATCH_NOT_ENFORCEMENT_ATTEMPT_BY_IDENTITY
```

Keep and potentially reuse.

## TeamObservation

```text
GENERIC_REALIZED_EFFECT_EVIDENCE
```

Excellent future source for realization comparison.

## VerificationReceipt

```text
GENERIC_METHOD_SCOPED_EFFECT_VERIFICATION
```

Keep.

## Station Zero intent resolution

```text
ORDINARY_ACTION_REALIZATION_STATUS_FAMILY
```

Useful pattern, not generic enforcement semantics.

## Storage rollback

```text
TECHNICAL_ATOMICITY_NOT_GAME_REMEDY
```

Keep separate.

## After-commit recovery

```text
TECHNICAL_RECOVERY_PROVING_RETRY_NOT_DUPLICATE_EFFECT
```

Strong implementation evidence for future enforcement attempts.

## Station Zero repair

```text
ORDINARY_GAMEPLAY_REPAIR_NOT_REMEDY
```

No relabeling.

## Mission/faction outcome

```text
WORLD_EVALUATION_OUTCOME_NOT_ENFORCEMENT
```

Do not reuse victory/partial/failure as enforcement states.

---

# 50. Implementation conclusion

Current repository has:

```text
strong generic execution substrate = YES
```

but:

```text
current generic enforcement consumer = NOT PROVEN
```

because Station Zero currently lacks a real independent GPR2 case-status workflow that orders and tracks separate consequences.

Therefore:

```text
broadImplementationNow = false.
```

Adding generic tables for:

```text
enforcement directives
attempts
remedies
```

would currently be speculative.

---

# 51. Safe future consumption

When a real judged/moderated/certified GameForm appears, the safest path is:

```text
1. keep existing execution stack
2. add a thin consequence-directive workflow
3. link attempts to existing dispatch/action ids
4. derive realization from existing World/observation/verification
5. add remedy only if practice needs durable corrective lifecycle
```

Do **not** build:

```text
second executor
second World effect store
second verification system
```

for enforcement.

---

# 52. Stress result

GPR4 covers 60 cases across:

```text
direct rule consequences
separate judges/enforcers
capability/authority separation
stale/failed/unknown dispatch
idempotent retry
pre-commit atomic rollback
partial/no-effect/over-enforcement
unexpected effects
method-scoped verification
delay/stay/revocation
review before/after effect
irreversible consequences
restoration/replacement/compensation
record-only correction
wrong-target execution
failed/partial/over-corrective remedy
split remedy authority
solitary/TTRPG practices
ordinary gameplay repair
technical rollback/recovery
Station Zero resolution statuses
multiple attempts/directives/actions
maintained/conditional effects
conflicting directives
Agent substitution/proposals
stale/generated summaries
no-remedy practices
```

All probes pass.

No FoundationReopenCondition is triggered.

---

# 53. GPR1-GPR4 synthesis

We can now describe the practical authoritative-action stack as:

```text
GPR1 — Role / Authority
Who may bind, review, enforce or remedy?

GPR2 — Determination / Contestability
What status currently binds, and can it change?

GPR3 — Evidence / Norm / Explanation
Why does that status bind and on what basis?

GPR4 — Enforcement / Remedy
What should happen because of it, what actually happened, and how can damage be corrected?
```

These are practical layers, not new foundations.

They all compile back down to the frozen semantic substrate plus existing World/action/history/provenance structures.

---

# 54. The broader practical-reconstruction pattern becomes clearer

Again the pattern is:

```text
keep sources thin
persist identity/lifecycle only where it matters
reuse lower execution/history truth
derive rich operational views
```

For GPR4 specifically:

```text
order != attempt != effect != correction.
```

That one separation prevents most of the obvious implementation mistakes.

---

# 55. Next practical reconstruction round

R0 P5 is now ready because GPR1-GPR4 provide the components required for safe role presets.

Next:

```text
GPR5 — Role Bundle Templates
```

Targets:

```text
Referee / Judge
Game Master
Coach / Advisor
Moderator
Operator
Experience Manager
```

The key question will no longer be whether these labels are primitives—they are not—but:

> What composable practical template structure lets designers and Agents use these familiar roles without smuggling hidden observation, control, adjudication, rule-change, enforcement or remedy authority into the label?
