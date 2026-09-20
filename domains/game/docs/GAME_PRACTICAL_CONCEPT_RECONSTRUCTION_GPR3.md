---
schema_version: 1
id: game.practical-concept-reconstruction.gpr3
title: Ordivon Game — GPR3 Evidence / Norm / Explanation Toolkit
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Reconstructs practical evidence, norm-application, interpretation, precedent, convention, discretion, verification and determination-explanation tooling over frozen GDF0-GDF3 plus GPR1/GPR2. Reuses existing World/history/observation/replay/verification provenance rather than creating a second Evidence store. Stabilizes EvidenceBundleForCase, NormApplicationView, ConventionStatusView, DiscretionEnvelope, VerificationView and DeterminationExplanationView as derived projections; InterpretiveCommitmentRecord as a conditional GDF0 source adapter only when authoritative adoption changes EffectiveRuleTopology; and PrecedentLink as a conditional typed relation whose citation/similarity never creates binding force by itself. Fifty-eight cross-regime cases, twenty-seven executable probes and forty audit checks pass.
evidence_status: strong
readiness: GPR3_COMPLETE
applies_to:
  - ordivon-game
related:
  - game.practical-concept-reconstruction.gpr1
  - game.practical-concept-reconstruction.gpr2
  - game.authoritative-case-determination-foundations.v1
---
# Ordivon Game — GPR3 Evidence / Norm / Explanation Toolkit

## 0. Scope

GPR3 reconstructs the R0 P3 family:

```text
EvidenceBundleForCase
NormApplicationView
InterpretiveCommitment
PrecedentLink
ConventionStatusView
DiscretionEnvelope
VerificationView
```

and adds one composition-level consumer:

```text
DeterminationExplanationView
```

because the practical reason to recover these concepts is not to create more ontology; it is to let Humans and Agents answer:

```text
What information mattered?
What was verified?
Which current rule/evaluation basis applied?
Was an interpretation formally adopted?
Did a prior case matter, and with what force?
Is this common practice or actually constitutive?
What residual discretion remained?
Why is the current determination what it is?
```

GDF0-GDF3 remain frozen.

---

# 1. Main result

The naive reconstruction would be:

```text
Evidence table
Norm table
Precedent table
Convention table
Discretion table
Explanation table
```

GPR3 rejects that architecture.

Current Ordivon already has strong lower sources:

```text
World state/history
World events
observations
artifacts/digests
RunEvidenceGraph
VerificationReceipt
ruleset id/version
GPR1 authority/currentness
GPR2 determination/basis references
```

The correct practical architecture is instead:

```text
AUTHORITATIVE / OWNER-LOCAL SOURCES
World / history / observation / artifacts / verification
GDF0 current rule topology
GPR1 authority
GPR2 determination + basis refs
observed-practice data
        │
        ├───────────────┐
        ↓               ↓
EvidenceBundle      NormApplicationView
        │               │
        │        ┌──────┼───────────┐
        │        ↓      ↓           ↓
        │  Interpretation Precedent Convention
        │        │      │           │
        │        └──────┼───────────┘
        │               ↓
        │       DiscretionEnvelope
        │               │
        └───────┬───────┘
                ↓
     DeterminationExplanationView
```

Only two concepts can sometimes justify durable relation/source identity:

```text
InterpretiveCommitmentRecord
PrecedentLink
```

and even these remain subordinate to current authority/GDF0 semantics.

---

# 2. Evidence is a use relation, not an intrinsic thing

GDF3 correctly rejected an `Evidence` primitive.

GPR3 makes the practical positive version explicit:

```text
EvidenceIsRelativeToQuestionOrUse.
```

A replay frame, screenshot, testimony, sensor reading, World event or verification receipt is not intrinsically “Evidence” in every context.

It becomes evidence **for a question/claim/determination** when a practice or analysis uses it that way.

For example, one replay frame might:

```text
support claim A
contradict claim B
be irrelevant to claim C
```

without changing source identity.

Therefore:

```text
EvidenceItem
!= permanent intrinsic type.
```

---

# 3. EvidenceBundleForCase

GPR3 stabilizes:

```text
EvidenceBundleForCase
```

as a **derived case-relative view**.

It answers:

> Which source records/materials are currently offered, used, contested, excluded, superseded or unresolved in relation to this question/determination/contest?

Inputs:

```text
determinationRefOrQuestionRef
contestRequestRef optional
contextRef
asOfCurrentness
```

Each item may expose:

```text
sourceRef
sourceKind
payloadOrContentDigest
provenanceRefs
currentnessOrCaptureSummary
targetClaimOrQuestionRefs
useKeyOrBasisRole
useStatus
verificationViewRefs
ownerScopeRefs
```

---

# 4. EvidenceBundle should reference, not copy

Current Ordivon already retains digest-bound facts and artifacts.

So a practical bundle should normally say:

```text
sourceRef = world-event:e123
payloadDigest = sha256:...
```

rather than duplicate the complete event inside a new `evidence_items` store.

Default:

```text
reference source identity + digest + use relation
```

Only snapshot when necessary, for example:

```text
external source can mutate
source may disappear
currentness at time-of-determination must remain auditable
```

This yields a strong law:

```text
EvidenceBundle != DuplicateTruthStore.
```

---

# 5. Evidence use status is useful

A case workflow may need to distinguish:

```text
offered_or_candidate
used_as_basis
contested
excluded_or_not_used
superseded
unknown_or_unresolved
```

These are **workflow/use statuses**, not truth statuses.

For example:

```text
contested
```

means:

```text
someone/practice disputes its reliability/relevance/use
```

not:

```text
source is false.
```

Likewise:

```text
excluded
```

may mean deadline/procedure disallowed use, not that the content is factually false.

---

# 6. Bundle completeness is not automatic

A UI showing five evidence items must not silently imply:

```text
these are all possible relevant facts.
```

Unless a concrete practice explicitly guarantees closed evidence collection, GPR3 keeps:

```text
EvidenceBundle completeness = NOT ASSUMED.
```

This is important for Agents because a compact evidence view can otherwise create false epistemic closure.

A future UI can label:

```text
basis items
currently submitted items
retained relevant sources
```

rather than claiming completeness.

---

# 7. Current RunEvidenceGraph is already a strong lower substrate

The repository currently has:

```text
ordivon.game.run-evidence-graph
```

covering:

```text
World states/events
Team rounds/contexts/proposals
Tick plans
messages
authority decisions/grants
Host contracts/events
dispatch
observation
effects
```

with digest-bound nodes and typed edges.

This is valuable.

But GPR3 classifies it as:

```text
STRONG_PROVENANCE_HISTORY_GRAPH_NOT_CASE_EVIDENCE_ONTOLOGY
```

The name `EvidenceNode` is engineering vocabulary.

It does **not** imply:

```text
every node is Evidence for every case.
```

Instead:

```text
RunEvidenceGraph
→ source/provenance index
→ EvidenceBundleForCase selects/relates relevant nodes
```

when a concrete case exists.

---

# 8. Current Mission Control `EvidenceView` should remain local

Mission Control already exposes stages:

```text
Observed
Assessed · unverified
Proposed
Executing
Verified
```

This is excellent product UX for following specialist activity.

But it is not a universal case evidence lifecycle.

GPR3 classifies it as:

```text
PRODUCT_UX_EVIDENCE_STAGE_PROJECTION
```

because:

```text
Observed → Assessed → Proposed → Executing → Verified
```

describes a particular action/planning pipeline.

A tournament appeal, TTRPG ruling or speedrun certification does not need those same stages.

So the local projection survives unchanged.

---

# 9. Current replay diagnosis is good evidence discipline

`RunDiagnosis` already distinguishes:

```text
VERIFIED_DIRECT
VERIFIED_CONTRIBUTOR
COUNTERFACTUAL_SENSITIVE
CONTEXT_ONLY
```

This is a strong example of useful mid-level epistemic labels.

Notably, current code explicitly says things like:

```text
verified contributor, not unique cause
bounded sensitivity, not proof of unique cause
```

That is exactly the practical discipline GPR3 wants.

Classification:

```text
BOUNDED_ANALYTIC_CLAIM_WITH_EVIDENCE_REFERENCES
```

A DiagnosisClaim is:

```text
derived analysis
```

not:

```text
WorldTruth primitive
AuthoritativeDetermination
```

by identity.

---

# 10. VerificationView

Current Ordivon already has real verification sources.

GPR3 therefore does **not** invent a new verification record.

It stabilizes:

```text
VerificationView
```

as a derived adapter over existing owner-local verification records.

Useful output:

```text
verificationKindOrMethodKey
subjectRefs
verificationScope
statusOrAcceptedResult
checkOrResultSummaries
observationOrEvidenceRefs
methodAndVersionRefs
currentnessOrDigestBindings
provenanceRefs
possibleDeterminationBasisRefs
```

---

# 11. Verification success is always method-scoped

Suppose a receipt says:

```text
digest integrity checks passed
```

Then what has been established is roughly:

```text
this source passed these declared integrity checks
```

not:

```text
every statement about the run is true.
```

Similarly:

```text
execution effect verification succeeded
```

is not identical to:

```text
run is officially valid in category X.
```

Therefore:

```text
VerificationSuccess
= success under declared method/scope
```

not universal truth.

---

# 12. Verification remains distinct from certification and adjudication

GPR2 already established:

```text
Verification != Certification
Verification != Adjudication
```

GPR3 makes that operationally consumable.

For example:

```text
VerificationReceipt V
```

may enter:

```text
EvidenceBundleForCase
```

and then become:

```text
caseBasisRef = V
```

for:

```text
AuthoritativeDeterminationRecord C
operation = game.result.certify
```

So:

```text
Verification
→ possible basis
→ Certification determination
```

rather than identity collapse.

---

# 13. VerificationView is useful even when no adjudication exists

This is important for current Station Zero.

The existing execution pipeline needs verification whether or not GPR2 case determination exists.

Therefore:

```text
VerificationView
```

is the only GPR3 concept with clearly demonstrated current cross-cutting consumer value.

It can support:

```text
execution diagnostics
replay inspection
Host contract inspection
Agent tool summaries
```

without requiring any new adjudication subsystem.

---

# 14. Provider telemetry is not automatically Game-case evidence

Current DeepSeek integration retains:

```text
latency
HTTP status
model
finish reason
token counts
cache hits
candidate/directive
errors
```

This is valuable operational provenance.

Classification:

```text
PROVIDER_OPERATIONAL_TELEMETRY_PROVENANCE
```

It may become relevant to a Game case such as:

```text
Was an Agent response produced by approved provider/version?
Was a generation outage responsible for a procedural issue?
```

But absent such a question:

```text
ProviderTelemetry
!= GameCaseEvidenceByIdentity.
```

---

# 15. Agent rationale is useful but must remain weak

Current Station Zero asks DeepSeek for a short operational rationale and explicitly forbids chain-of-thought.

That is good practical design.

GPR3 classifies current rationale as:

```text
BOUNDED_OPERATIONAL_EXPLANATION_NOT_NORM_REASONING
```

A rationale can help answer:

```text
Why did this Agent choose candidate A?
```

but does not establish:

```text
A was legal
A was authoritative
A was factually correct
this interpretation binds future cases
```

Therefore:

```text
Rationale != DeterminationBasisByIdentity
Rationale != NormApplicationByIdentity.
```

---

# 16. NormApplicationView

GDF3-D found that `NormApplicationBasis` is useful but derived.

GPR3 reconstructs the practical consumer surface as:

```text
NormApplicationView
```

Question:

> Under the current practice/scope/currentness, what rule/evaluation/application basis is actually operative for this target/question?

Possible output:

```text
currentRuleOrEvaluationSourceRefs
sourceVersionAndCurrentness
explicitExceptionOrDefeaterRefs
priorityOrResolutionRelationRefs
adoptedInterpretiveCommitmentRefs
recognizedPriorCaseUseRefs
recognizedConventionRefs
purposeOrEthosRefsWhenOperative
discretionEnvelopeRefOrSummaryWhenMaterial
authorityAndProvenanceRefs
applicationBasisDigest
```

---

# 17. NormApplicationView can be very sparse

For a closed executable case, the useful answer may be just:

```text
ruleset = station-zero-core@3
relevant predicate = X
```

There is no reason to fabricate:

```text
precedent
ethos
interpretation
balancing test
discretion
```

when none exists.

Therefore:

```text
closed deterministic norm application
→ sparse NormApplicationView
```

is valid.

A rich view is conditional, not a maturity metric.

---

# 18. NormApplicationView is not a universal reasoner

GPR3 explicitly rejects turning this into:

```text
one Game legal reasoning engine
```

Different GamePractices may resolve norms through:

```text
executable predicates
ordered rules
human judgement
category rules
convention
purpose clauses
precedent
hybrid procedures
```

The view exposes **what operative basis exists**.

It does not require Ordivon Game to implement a universal defeasible logic or jurisprudence engine.

Thus:

```text
NormApplicationView != UniversalReasoningEngine.
```

---

# 19. Current ruleset version binding is already a norm-source input

Current Game metadata explicitly retains:

```text
rulesetId
rulesetVersion
```

and execution/replay resolves exact versions.

This is a strong practical source for:

```text
current executable rule representation
```

But current repository also contains different product paths retaining v3/v4 contracts.

That reinforces an important rule:

```text
never infer one global current ruleset from repository name alone.
```

NormApplicationView must carry exact owner-local version/currentness references.

---

# 20. RuleRepresentation != EffectiveRuleTopology

One of the strongest frozen GDF0/GDF3 results remains essential here:

```text
StableRuleRepresentation
!= StableEffectiveRuleTopology.
```

The text/code bytes can remain unchanged while current practice adopts a new interpretation that changes Game semantics.

Conversely, representation can change editorially without changing effective semantics.

So `NormApplicationView` must not reduce to:

```text
show rulebook text.
```

It needs current adoption/currentness context.

---

# 21. InterpretiveCommitmentRecord

This concept does justify a conditional durable form.

GPR3 stabilizes:

```text
InterpretiveCommitmentRecord
```

as a **conditional GDF0 source adapter**.

Minimum:

```text
commitmentId
representationRefs
interpretationRefOrStatement
scopeRefs
effectiveFrom
effectiveUntilOrOpen
adoptingAuthorityEvidenceRefs
provenanceRefs
effectiveRuleTopologyChangeRef
```

Optional:

```text
supersedesCommitmentRefs
prospectiveOrRetroactiveScopeSummary
displayRationale
```

---

# 22. Why it is called a source adapter rather than independent truth

The mere existence of:

```text
InterpretiveCommitmentRecord
```

must not make an interpretation binding.

For constitutive effect, the interpretation must be admitted under current:

```text
standing interpretive authority
rule-change authority
or other owner-defined authority
```

and correspond to a GDF0:

```text
EffectiveRuleTopology change.
```

Therefore:

```text
InterpretiveCommitmentRecord
!= EffectiveRuleTopology by identity.
```

The record provides practical identity/history/provenance.

GDF0 remains semantic authority.

---

# 23. Private interpretation remains private

These do not become commitments automatically:

```text
player opinion
moderator opinion
LLM interpretation
one-off explanation
community post
```

Even a highly persuasive interpretation remains:

```text
candidate / private / advisory
```

until the relevant current practice admits it.

Thus:

```text
PrivateInterpretation != InterpretiveCommitment
InterpretationText != AuthoritativeEffect.
```

---

# 24. One case ruling does not automatically become standing interpretation

A referee or GM may have authority to resolve:

```text
Case K
```

without authority to bind:

```text
all future cases of type K.
```

So:

```text
CaseRulingAuthority
!= StandingInterpretiveAuthority.
```

This distinction is especially important for Agent judges: one Agent-generated binding ruling should not silently rewrite future Game semantics.

---

# 25. Interpretation can be prospective or retrospective

A practice may adopt an interpretation:

```text
for future runs only
```

or:

```text
apply it to historical records/categories
```

GPR3 keeps this as scope/currentness metadata.

Retrospective normative status change still does **not** mean:

```text
old World events are rewritten.
```

It changes current interpretation/status over retained history.

---

# 26. PrecedentLink

GDF3-D established:

```text
PriorDecision != BindingPrecedent.
```

GPR3 still finds the relation highly useful operationally.

So it reconstructs:

```text
PrecedentLink
```

as a conditional typed relation/view or record.

Minimum if persisted:

```text
linkId
priorDeterminationRef
currentTargetOrDeterminationRef
useKey
scopeRefs
validFrom
validUntilOrOpen
recognitionOrAuthorityBasisRefs
provenanceRefs
```

---

# 27. Precedent is current use, not prior-case essence

A prior determination does not possess eternal `precedent=true` identity.

Instead, a current case/practice may treat it as:

```text
cited
analogized
distinguished
persuasive
recognized as currently precedential
```

within a scope/currentness.

This is why `PrecedentLink` is relational.

The same prior case may be:

```text
important in Category A
irrelevant in Category B
superseded after Rule Version 5
```

without contradiction.

---

# 28. Citation and similarity do not create authority

These are explicitly distinct:

```text
Citation != BindingForce
Similarity != PrecedentAuthority.
```

An embedding model may retrieve a highly similar prior case.

That is useful retrieval.

It does not establish current normative force.

Likewise a determination citing an earlier case may be explanatory only.

Binding force resolves through current:

```text
GDF0 practice semantics
GPR1 authority/currentness
```

not vector similarity or citation count.

---

# 29. PrecedentLink persistence should be conditional

If a determination already contains:

```text
normOrEvaluationBasisRefs = [prior determination P]
```

and no additional lifecycle matters, a link can be derived.

Persist a `PrecedentLink` only when the fact of current use itself needs:

```text
identity
history
supersession
explicit distinguishing
scope/currentness
```

This continues the programme-wide rule:

```text
persist lifecycle, derive projection.
```

---

# 30. ConventionStatusView

Convention is another concept with enormous practical value and high misuse risk.

GPR3 reconstructs:

```text
ConventionStatusView
```

specifically to separate:

```text
what people commonly do
```

from:

```text
what current practice recognizes as constitutive.
```

Possible output:

```text
observedPracticeEvidenceRefs
coverageOrFrequencySummary
recognitionStatus
recognitionAuthorityRefs
constitutiveEffectRefs
scopeAndCurrentness
conflictOrUncertaintySummary
sourceRefs
```

---

# 31. Convention frequency != authority

The view can safely expose cases such as:

```text
90% of players use Technique T
recognitionStatus = observed_only
```

and:

```text
5% of play uses Procedure P
recognitionStatus = constitutive_current
```

if current tournament/practice authority explicitly adopted P.

Therefore:

```text
Popularity != ConstitutiveEffect
ConventionFrequency != Authority.
```

This is much more useful than either ignoring convention or treating popularity as rule truth.

---

# 32. Suggested convention recognition states

A practical view can use:

```text
observed_only
recognized_nonconstitutive
constitutive_current
contested_or_mixed
unknown_or_insufficient_evidence
```

These are query/UI states.

They are not new universal ontology.

In particular:

```text
constitutive_current
```

must be traceable to current authority/GDF0 effective semantic change.

---

# 33. Community disagreement is scope, not necessarily contradiction

Suppose:

```text
Community A uses technique T
Community B forbids technique T
```

There need not be one global answer.

Different PlayPractices may have different:

```text
scope
lineage
recognition authority
EffectiveRuleTopology
```

So `ConventionStatusView` should support:

```text
contested_or_mixed
```

or separate scoped views rather than forcing one universal convention.

---

# 34. DiscretionEnvelope

GDF3-D retained `DiscretionEnvelope` as derived.

GPR3 now makes it practical.

It answers:

> After current authority, rules, constraints and norm application are accounted for, what residual determination/choice space remains for this holder in this context?

Possible output:

```text
envelopeRepresentationKind
admittedChoiceOrOutcomeRefsWhenEnumerable
constraintOrPredicateRefsWhenNotEnumerable
conditionalChoiceRefs
forbiddenOrOutsideEnvelopeRefsWhenKnown
residualUnknowns
scopeAndCurrentness
sourceRefs
envelopeDigest
```

---

# 35. Discretion can have multiple representation forms

Not every envelope can be enumerated.

GPR3 allows:

```text
enumerated
predicate_or_constraint_bounded
qualitative_bounded
unknown_or_unresolved
```

Examples:

### Enumerated

```text
UPHOLD
MODIFY
REVERSE
```

### Predicate bounded

```text
score must remain 7.0–8.0
```

### Qualitative bounded

```text
GM may select a plausible consequence preserving established facts and current safety constraints
```

without pretending there is an exhaustive list.

---

# 36. Authority does not imply discretion

A holder may have authority to decide but only one currently admissible determination exists.

For example:

```text
review authority = YES
current rule requires UPHOLD
```

Then:

```text
DiscretionEnvelope = {UPHOLD}
```

or effectively no residual choice.

Therefore:

```text
Authority != Discretion.
```

This is another reason not to use “Judge” as a magical free-choice role.

---

# 37. Discretion does not imply quality

Suppose three outcomes are valid inside the envelope.

An Agent chooses one.

That means:

```text
choice was within current discretion bounds
```

not:

```text
choice was fair
wise
fun
optimal
socially accepted
factually correct
```

Hence:

```text
WithinDiscretionEnvelope
!= GoodOrCorrect.
```

Human/Agent evaluation remains another layer.

---

# 38. Agent-facing use of DiscretionEnvelope

This concept is especially valuable for Agent adjudicators/GM/moderators.

Instead of prompting:

```text
You have discretion. Decide.
```

we can eventually provide:

```text
current authority operation
current norm basis
admissible outcome set/constraints
forbidden outcomes
unresolved dimensions
```

This converts vague “judgement” into bounded autonomy without pretending the envelope is bottom ontology.

---

# 39. DeterminationExplanationView

The P3 family becomes most useful when composed.

GPR3 therefore stabilizes:

```text
DeterminationExplanationView
```

as a **composite derived explanation packet**.

It can combine:

```text
current OfficialStatus / determination summary
binding authority/currentness summary
DeterminationBasisTrace
EvidenceBundleForCase summary
NormApplicationView summary
Precedent/Convention summaries when material
DiscretionEnvelope summary when material
ReviewContestabilityProfile summary
sourceRefs
explanationStateDigest
```

---

# 40. Explanation view is not source truth

This view exists for usability.

A generated short explanation may say:

```text
Run invalid because verified timing exceeded category limit under current Category v5 interpretation.
```

That is excellent UI/Agent compression.

But:

```text
GeneratedExplanation != AuthoritativeEffect.
```

If the prose is wrong while source refs are correct, the prose should be fixed.

The determination itself does not change because the explanation text changed.

---

# 41. Explanation state needs currentness

Suppose an explanation packet was generated under:

```text
Rule v4
Interpretation I1
Contestability open until T50
```

then Rule v5 is adopted.

The old explanation may remain historically useful but is no longer a current explanation.

Therefore GPR3 recommends an:

```text
explanationStateDigest
```

or equivalent currentness binding over the relevant source set.

This follows the same pattern already useful for AgentAuthorityManifest in GPR1.

---

# 42. Explanation can be lossy if drill-down survives

A small player-facing card should not need to show:

```text
30 evidence refs
10 authority edges
6 precedent links
complete norm topology
```

It may summarize aggressively.

The requirement is:

```text
correctness-critical tooling can drill down to source refs.
```

Thus:

```text
lossy presentation
+ source traceability
```

is permitted and desirable.

---

# 43. No chain-of-thought requirement

GPR2 already rejected full reasoning traces for determination basis.

GPR3 applies that rule across explanation.

Useful explanation artifacts are:

```text
source refs
method/check summaries
rule/version refs
authority/currentness
bounded operational rationale
structured basis distinctions
```

not hidden private reasoning.

So:

```text
DeterminationBasisTrace != ChainOfThought
DeterminationExplanationView does not require ChainOfThought.
```

---

# 44. Casefile is an instructive boundary example

Current `casefile` has:

```text
traces
testimony
confrontations
accusation
```

These are obviously “evidence-like” in player experience.

Yet they are primarily:

```text
Game information/content
```

and the player's task is to infer the culprit.

They are not automatically:

```text
GPR2 official case evidence
```

because no independent institutional adjudication layer is necessary.

This is a valuable practical reminder:

> Evidence vocabulary may be useful inside gameplay even when GDF3 adjudication does not exist.

---

# 45. Evidence toolkit is therefore broader than adjudication but case-relative views remain conditional

`VerificationView` and provenance tooling can be useful throughout Game engineering.

`EvidenceBundleForCase`, however, should be instantiated only when there is an actual:

```text
question
claim
contest
or determination basis
```

that gives the evidence-use relation meaning.

This avoids converting all world history into a permanent legal dossier.

---

# 46. The eight GPR3 practical verdicts

| Concept | GPR3 verdict |
| --- | --- |
| EvidenceBundleForCase | **derived case-relative view** |
| NormApplicationView | **derived current norm view** |
| InterpretiveCommitmentRecord | **conditional GDF0 source adapter** |
| PrecedentLink | **conditional typed relation/view or record** |
| ConventionStatusView | **derived observed-vs-constitutive view** |
| DiscretionEnvelope | **derived bounded-choice view** |
| VerificationView | **derived adapter over existing verification sources** |
| DeterminationExplanationView | **composite derived explanation view** |

This is a highly asymmetric reconstruction:

```text
6 strongly derived views
2 conditional relation/source forms
0 new primitives
```

---

# 47. Current engineering audit summary

## RunEvidenceGraph

```text
KEEP
```

Excellent provenance substrate.

Do not rename every node into a case-evidence object.

## MissionControl EvidenceView

```text
KEEP LOCAL
```

Useful action-progress UX, not universal evidence taxonomy.

## ReplayDiagnosisClaim

```text
KEEP
```

Strong bounded analytic explanation discipline.

## VerificationReceipt

```text
KEEP AS SOURCE
```

Best current GPR3 consumer substrate.

## DeepSeekEvidenceSnapshot

```text
KEEP OPERATIONAL
```

Provider provenance; only case evidence when actually used for a case question.

## Agent rationale

```text
KEEP BOUNDED
```

Useful explanation; never authority/norm truth.

## Ruleset id/version

```text
KEEP EXACT
```

Strong norm-source version binding.

## Casefile traces/testimony

```text
KEEP AS GAME INFORMATION
```

May be player-facing evidential material without requiring adjudication ontology.

---

# 48. The existing repository does not need a new generic Evidence database

Current Game already has:

```text
digest-bound history
artifact refs
replay graph
verification
World facts
observation envelopes
```

Creating:

```text
evidence_objects
norm_objects
precedent_objects
```

as generic canonical stores now would mostly duplicate existing truth and provenance.

Therefore GPR3 explicitly rejects broad persistence implementation at this stage.

---

# 49. What has proven current implementation value

Unlike GPR2, GPR3 has a partial current consumer.

Proven today:

```text
verification/provenance views are useful
bounded explanation is useful
source digests/currentness are useful
```

Not yet proven:

```text
generic case EvidenceBundle persistence
InterpretiveCommitment subsystem
precedent subsystem
convention subsystem
discretion subsystem
```

So:

```text
partialCurrentConsumerNeed
= PROVEN_FOR_VERIFICATION_AND_PROVENANCE_VIEWS_ONLY
```

---

# 50. Low-risk future engineering candidates

If engineering consumption later begins, the safest initial pieces are:

```text
VerificationView adapter
```

over current World/Host receipts;

```text
terminology guards
```

distinguishing:

```text
source/provenance
evidence use
verification
certification
determination
```

and only after a real GPR2 consumer exists:

```text
EvidenceBundleForCase query
DeterminationExplanationView
```

over existing source refs.

No database migration is currently implied.

---

# 51. Strong practical law set

```text
Evidence != WorldTruth
EvidenceIsRelativeToQuestionOrUse
Observation != EvidenceByIdentity
ReplayEvidenceGraph != CaseEvidenceBundleByIdentity
EvidenceBundle != DuplicateTruthStore

Verification != WorldTruthByIdentity
Verification != CertificationByIdentity
Verification != AdjudicationByIdentity
ProviderTelemetry != GameCaseEvidenceByIdentity

Rationale != DeterminationBasisByIdentity
Rationale != NormApplicationByIdentity

RuleRepresentation != EffectiveRuleTopology
StableRuleRepresentation != StableEffectiveRuleTopology
NormApplicationView != UniversalReasoningEngine

PrivateInterpretation != InterpretiveCommitment
InterpretationText != AuthoritativeEffect

PriorDecision != BindingPrecedent
Similarity != PrecedentAuthority
Citation != BindingForce

ConventionFrequency != Authority
Popularity != ConstitutiveEffect

Discretion != Arbitrariness
Discretion != UnlimitedAuthority
WithinDiscretionEnvelope != GoodOrCorrect

GeneratedExplanation != AuthoritativeEffect
ExplanationView != SourceOfTruth
DeterminationBasisTrace != ChainOfThought
```

---

# 52. Deep practical synthesis

GPR3 clarifies a recurring Ordivon design pattern:

```text
source truth should remain specific and authoritative
while explanation surfaces should be rich and composable.
```

So we should not force an Agent to manually inspect:

```text
raw World event
raw verification object
raw rule file
raw authority graph
raw prior cases
```

every time it wants to answer:

```text
Why is this status current?
```

Instead we can eventually expose:

```text
DeterminationExplanationView
```

with drill-down.

That gives ergonomic compression without epistemic collapse.

---

# 53. GPR1–GPR3 now form a coherent stack

```text
GPR1
Role / Authority
    ↓
who may bind what now?

GPR2
Determination / Contestability
    ↓
what status currently binds, and how can it change?

GPR3
Evidence / Norm / Explanation
    ↓
what sources/basis/norm structure explain that status?
```

The layers remain separable:

```text
Authority does not imply correctness.
Determination does not imply truth.
Evidence does not imply determination.
Verification does not imply certification.
Explanation does not create authority.
```

This separation is exactly what lets the practical layer become richer without reopening the foundations.

---

# 54. Stress-test result

GPR3 covers 58 cases across:

```text
raw observations
case-relative evidence use
incomplete/contested/excluded/superseded evidence
mutable/immutable source provenance
verification methods and scopes
provider telemetry
Agent rationale
replay diagnosis
Mission Control evidence stages
Casefile clues/testimony
closed executable norms
interpretive adoption/private interpretation
retroactivity
purpose clauses
exceptions/conflicts
precedent citation/binding/distinguishing/supersession
community conventions
rare constitutive practices
bounded/zero/qualitative discretion
Agent discretion
stale/generated explanation packets
ruleset version splits
verification without adjudication
```

All executable probes pass.

No GDF0-GDF3 reopen condition is triggered.

---

# 55. What GPR3 deliberately does not standardize

GPR3 does not define one universal:

```text
evidence admissibility law
relevance logic
probabilistic belief model
legal proof standard
precedent doctrine
convention detection algorithm
norm conflict calculus
defeasible logic
fairness metric
explanation generator
```

These may belong to:

```text
owner-local GameForm policy
General Reasoning
Human/Social/Institutional layers
specialized implementation
```

depending on the concrete problem.

GPR3 standardizes the practical **boundaries and views**, not the whole theory of reasoning.

---

# 56. Final result

The answer to the practical reconstruction question is strongly positive.

Even concepts that failed as primitives can return safely when their role is explicit:

```text
Evidence
→ relation/view

NormApplication
→ derived current explanation view

InterpretiveCommitment
→ conditional adopted relation feeding GDF0

Precedent
→ current-use relation

Convention
→ observed-vs-recognized view

Discretion
→ bounded residual-choice projection

Verification
→ method-scoped adapter

Explanation
→ lossy composite view with drill-down
```

Thus:

```text
Foundation rejection
!= practical rejection.
```

Instead:

```text
Foundation rejection tells us how NOT to implement the useful concept.
```

---

# 57. Next practical reconstruction round

R0's next cluster is:

```text
P4 — Enforcement / Remedy Toolkit
```

GPR2 established:

```text
Determination != Enforcement.
```

GPR3 now gives us enough explanation/provenance structure to audit what was ordered and why.

So the next round is:

```text
GPR4 — Enforcement / Remedy Toolkit
```

Targets:

```text
EnforcementRecord
RemedyPlan
```

with likely related practical views for:

```text
ordered consequence
attempted consequence
realized consequence
partial/failed enforcement
reversal after irreversible effect
repair/restoration/compensation
```

The key falsifier will be whether these need independent workflow identity or can compress almost entirely into ordinary F4/GDF1 transitions plus determination references.
