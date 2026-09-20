---
schema_version: 1
id: game.practical-concept-reconstruction.r0
title: Ordivon Game — Practical Concept Reconstruction R0 / Utility Map
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Begins post-foundation practical reconstruction after GDF3 freeze. Reintroduces useful mid-level Game concepts only as derived operational abstractions, workflows, policy surfaces, audit views, role templates or UI/authoring vocabulary. Maps 37 concepts by utility, reuse, Agent value, derivability, persistence need and misuse risk. Selects Operational Role & Authority Toolkit as the highest-leverage next reconstruction round while keeping GDF0-GDF3 frozen.
evidence_status: derived
readiness: R0_COMPLETE
applies_to:
  - ordivon-game
related:
  - game.authoritative-case-determination-foundations.v1
  - game.play-game-deep-foundations.v1
  - game.action-control-skill-foundations.v1
  - game.challenge-failure-mastery-foundations.v1
---
# Ordivon Game — Practical Concept Reconstruction R0

## 0. Why practical reconstruction is legitimate

The Deep Foundations programme deliberately deleted many concepts as:

```text
not primitive
not universal
not independently irreducible
```

That does **not** imply:

```text
useless
forbidden
should never appear in code/UI/tools
```

Those are different questions.

A practical abstraction can be excellent even when it is fully reducible to lower semantics.

Examples already familiar in engineering include:

```text
VerificationReceipt
Replay
MissionStatus
AvailableAction
Role
Permission/Profile
```

None needs to be a metaphysical primitive to save enormous implementation, authoring and debugging cost.

The correct post-foundation move is therefore:

```text
Foundation deletion
!= practical vocabulary deletion.
```

Instead:

```text
frozen semantic substrate
→ reconstruct useful derived abstractions
→ preserve traceability and anti-collapse laws
→ expose ergonomic surfaces to humans and Agents
```

---

# 1. The new optimization target

Foundations optimized mainly for:

```text
irreducibility
counterfactual correctness
owner clarity
minimal ontology
```

Practical reconstruction adds another legitimate objective:

```text
UTILITY
```

A practical concept earns its place when it materially reduces one or more of:

```text
authoring cost
query cost
coordination cost
reasoning/context cost
UI cognitive load
Agent prompt/tool complexity
audit/explanation cost
workflow ambiguity
policy configuration cost
```

while remaining traceable to authoritative lower semantics.

---

# 2. The key rule: convenience may be lossy, but not secretly authoritative

A useful UI can display:

```text
Participants
Judges
Spectators
Appealable
Final
GM
Moderator
```

without pretending those labels are bottom ontology.

The danger appears only when a convenience label silently begins to imply hidden facts such as:

```text
Participant → Player
Judge → all authority
Spectator → no causal influence
Final → true forever
GM → one atomic capability
Popular convention → binding rule
```

Therefore every reconstructed concept must know what it hides.

---

# 3. Practical Reconstruction Contract

Every concept considered for stabilization should answer eight questions.

## PRC-1 — PracticalPurpose

```text
What cost does this concept reduce?
```

If there is no clear user/Agent/operator benefit, do not reconstruct it merely because the word is familiar.

## PRC-2 — SemanticSources

```text
Which frozen F/GDF semantics make it true?
```

A practical concept cannot become a new truth authority merely because it is easier to consume.

## PRC-3 — HiddenDistinctions

```text
What distinctions does the shorthand suppress?
```

For example:

```text
ParticipantView hides exact role/access/authority topology.
```

## PRC-4 — AuthorityRule

```text
What authority is this concept allowed to imply?
```

Most UI labels imply none by themselves.

## PRC-5 — CurrentnessRule

```text
How do time, version, scope or replacement invalidate the abstraction?
```

## PRC-6 — PersistenceRule

Default:

```text
derive, do not persist.
```

Persist only if at least one of these matters:

```text
identity
workflow
history/audit
coordination across actors/Agents
performance/caching with explicit invalidation
```

## PRC-7 — DrillDownRule

When correctness matters, tools must make it possible to recover the lower authoritative semantics.

A Human-facing label may say:

```text
Judge
```

while an audit/tool surface can expand it into:

```text
RoleAssignment
+ ScopedAuthorityEdges
+ currentness/provenance
```

## PRC-8 — OwnerBoundary

The reconstruction must still respect Game / World / Human / Media / Social / GeneralReasoning ownership.

---

# 4. Eight practical representation forms

Not every useful concept deserves the same implementation form.

## A. `semantic_alias`

A readable name over lower semantics.

Examples:

```text
Participant
Spectator
Final
Official
```

Usually never persisted independently.

## B. `derived_query_view`

A recomputable projection.

Examples:

```text
AuthorityProfile
DecisionLineage
ParticipationAuthorityTopology
FinalityStatus
```

## C. `typed_operational_record`

A durable object when identity/currentness/history matter.

Examples:

```text
RoleAssignment
DelegationGrant
AuthoritativeDeterminationRecord
EnforcementRecord
```

## D. `workflow_object`

A persistent lifecycle coordination object.

Examples:

```text
ReviewRequest
AppealRequest
RemedyPlan
```

## E. `policy_surface`

Declarative configuration interpreted over lower semantics.

Examples:

```text
AuthoritySeparationPolicy
Review policy
DiscretionEnvelope constraints
```

## F. `ui_authoring_projection`

A lossy author/editor/operator concept.

Examples:

```text
GM
Judge
Moderator
Participant list
```

## G. `audit_trace`

A provenance/history/evidence surface.

Examples:

```text
DecisionLineage
DeterminationBasisTrace
VerificationView
EvidenceBundleForCase
```

## H. `local_pattern`

Reusable only in GameForms where the bundle makes sense.

Examples:

```text
GameMasterRoleBundle
RefereeJudgeRoleBundle
ExperienceManagerRoleBundle
```

---

# 5. Tier system

R0 places concepts into four practical tiers.

## T1 — Cross-Game Toolkit

High repeated value across materially different GameForms.

These are the strongest candidates for stable Game tooling contracts.

## T2 — Conditional Toolkit

High value within substantial families of GameForms, but must not be instantiated universally.

## T3 — UI / Authoring Vocabulary

Excellent cognitive compression, deliberately lossy, never canonical semantic truth by identity.

## T4 — Local / Caution

Useful natural-language vocabulary but too misleading to stabilize broadly.

---

# 6. R0 inventory result

R0 maps:

```text
37 concepts
```

into:

```text
T1 Cross-Game Toolkit       15
T2 Conditional Toolkit      17
T3 UI/Authoring Vocabulary   4
T4 Local/Caution             1
```

This already answers the central question:

> Yes, most of the useful GDF3 vocabulary can be reconstructed; the correct reconstruction form is simply not “new foundation primitive.”

---

# 7. T1 — Operational Role & Authority concepts

This is the highest-value cluster.

## RoleAssignment

Practical value: **very high**.

Why it should exist:

```text
people and Agents reason naturally in roles
role assignment has identity/currentness
persistent assignment is useful for workflows
```

But:

```text
RoleAssignment != AuthorityGrant
Role != Occupant
```

Recommended form:

```text
typed operational record
+ derived query view
```

---

## ScopedAuthorityEdge

This is probably the single most valuable abstraction recovered from GDF3-B.

A practical edge can answer:

```text
holder/role assignment
operation
object/domain
scope
activation condition
currentness/time
binding status
authority source/provenance
```

It supports:

```text
action admission
rule change
review
delegation
moderation
GM authority
Agent permission
live operations
tournament control
```

without requiring a hierarchy.

Recommended:

```text
STABILIZE
```

---

## AuthorityProfile

Humans and Agents should rarely need to manually traverse dozens of authority edges.

A derived profile can answer:

```text
What can X currently observe?
What can X advise?
What can X decide?
What can X change?
What can X review?
What can X enforce?
```

This is a perfect example of:

```text
not foundational
but extremely useful.
```

It must remain a projection, because:

```text
AuthorityProfile != one global authority rank.
```

---

## AgentAuthorityManifest

For Agent-first systems, an even more focused projection is justified:

```text
Agent X may:
  propose actions
  bind action admissions
  change rules
  adjudicate cases
  enforce consequences
  appoint/replace others
```

with exact scopes/currentness.

This removes a large amount of prompt/tool ambiguity.

Strong rule:

```text
ModelIdentity != AuthorityManifest.
```

The manifest comes from current Game authority relations, not the model name.

---

## RoleCausalAccessProfile

This should answer a broader question than authority:

```text
What can this role/entity currently perceive, influence, control, propose, decide or affect?
```

It is especially useful for:

```text
Player
spectator
coach
assistant Agent
NPC controller
moderator
operator
GM
```

Strong guard:

```text
CausalAccess != BindingAuthority.
```

---

## ParticipationAuthorityTopology

Foundation verdict:

```text
not independent responsibility
```

Practical verdict:

```text
excellent visualization/debugging abstraction.
```

It can power:

```text
authority graph inspectors
role editors
Agent permission visualization
security/debug panels
tournament administration views
```

Recommended form:

```text
derived view only
```

not stored canonical truth.

---

## AuthoritySeparationPolicy

GDF3 rejected universal separation-of-duties laws.

But a GamePractice may deliberately require:

```text
case adjudicator cannot review own ruling
rule changer cannot retroactively certify without second authority
moderator classifier cannot enforce directly
```

That should become:

```text
policy surface
```

not ontology.

This is an excellent example where a rejected universal law becomes a powerful configurable tool.

---

## DelegationGrant

`Delegation` failed as primitive.

But in practice we very often need a durable event/object such as:

```text
A delegates operation O
within scope S
to B
until T
```

plus:

```text
revoke
expire
replace
inspect provenance
```

That is a real workflow need.

Therefore reconstruct:

```text
DelegationGrant
```

as a durable authority transition/workflow record.

Never infer unspecified authority.

---

## AppointmentReplacementRecord

Likewise:

```text
appoint judge
replace moderator
swap GM
assign temporary operator
```

are highly practical transitions.

But:

```text
AppointmentAuthority != CaseAuthority
Replacement != Delegation
```

So a conditional workflow object is appropriate.

---

# 8. T1/T2 — Case determination & contestability concepts

The second major reconstruction family directly operationalizes GDF3.

## AuthoritativeDeterminationRecord

The frozen foundation says what must remain semantically distinguishable.

A practical runtime/tooling object can instantiate it as:

```text
DeterminationRecord
```

when the GameForm actually has an independently meaningful binding case status.

It may contain practical identifiers/backpointers for:

```text
target
status/result
binding authority/currentness/provenance
material basis references
```

This is not a new foundation; it is the obvious operational realization of the frozen contract.

---

## DeterminationBasisTrace

When explanation matters, a compact trace can expose:

```text
case/history/evidence basis
norm/evaluation/application basis
```

without storing a chain-of-thought or universal reasoning proof.

This is especially useful for Agents because it enables:

```text
why did status change?
which source changed?
which rule version mattered?
```

without turning rationale text into authority.

---

## CaseDeterminationBoundaryDiagnostic

This should become a stable development/audit query.

Question:

```text
Is this merely ordinary direct execution,
or does an independently meaningful binding case status exist?
```

This has exceptionally high utility because it prevents schema inflation.

Recommended:

```text
stable diagnostic
```

with no persistence.

---

## ReviewRequest

`Review` is not primitive.

But a user/system may still need to create:

```text
review request
```

with identity and lifecycle:

```text
requested
admitted/rejected
assigned
resolved
withdrawn/expired
```

This is a workflow object, not ontology.

---

## AppealRequest

Likewise, appeal is an excellent practical workflow concept in applicable GameForms.

But:

```text
Appeal != Review by identity
Appeal != GuaranteedCorrection
```

Its semantics come from current review policy/authority.

---

## ReviewContestabilityProfile

A highly useful query can answer:

```text
Can this determination be reviewed?
By whom?
Until when?
What can the reviewer change?
Does review stay execution?
Can enforcement continue meanwhile?
```

This is much more useful operationally than a primitive Boolean `appealable`.

---

## DecisionLineage

This should absolutely be reconstructed.

Foundation result:

```text
DecisionLineage = derived
```

Practical result:

```text
DecisionLineage = excellent audit tool
```

Example view:

```text
D0 original
↓ reviewed_by
D1 modified
↓ superseded_by
D2 current
```

Because the underlying events remain authoritative, this view is safe and cheap.

---

## OfficialStatus / Certification View

Users naturally want to ask:

```text
Is this run official?
Is this result certified?
Is this score current?
Is this player eligible?
```

These are excellent derived aliases over authoritative determinations.

Guard:

```text
Official != True.
```

---

# 9. Evidence / norm / explanation toolkit

This family is extremely useful but has higher misuse risk.

## EvidenceBundleForCase

A review UI or Agent often needs:

```text
replay
logs
measurements
reports
screenshots
state snapshots
```

in one place.

So reconstruct an `EvidenceBundleForCase` workflow/audit object.

But its name must encode the relational nature:

```text
EvidenceFor(case/question)
```

not:

```text
Evidence = truth.
```

The bundle may be:

```text
incomplete
contested
superseded
misleading
```

and must retain provenance.

---

## NormApplicationView

For rule-heavy practices, a Human/Agent explanation surface should answer:

```text
which current norm/evaluation source applied?
which version?
which exception/priority?
which adopted interpretation?
which precedent/convention mattered?
what discretion remained?
```

This is highly useful.

But it remains:

```text
view
```

not universal logic engine.

---

## InterpretiveCommitment

If unchanged text acquires a standing adopted interpretation, future Game semantics can change.

A persistent operational record may therefore be useful:

```text
InterpretiveCommitment
```

with:

```text
scope
currentness
source authority
prospective/retroactive application
```

Guard:

```text
private interpretation != adopted commitment.
```

---

## PrecedentLink

Retrieval/tooling often benefits from saying:

```text
current case cites prior case P
```

But a safe link needs:

```text
relevance/similarity basis
current status
scope/currentness
authority force
```

not simply:

```text
priorCaseId
```

Therefore PrecedentLink is useful, but guard-heavy.

---

## ConventionStatusView

A useful tool can explicitly compare:

```text
commonly observed practice
vs
currently recognized/adopted practice
```

This prevents the frequent operational error:

```text
popular = binding.
```

---

## DiscretionEnvelope

This should be reconstructed for:

```text
bounded Agent behavior
judge tooling
policy tests
authoring
```

It can expose:

```text
currently permitted result region
```

without pretending every choice is legal or arbitrary.

---

## VerificationView

The existing Game engineering already demonstrates the value of verification receipts.

A stable practical distinction should be:

```text
Verification
→ evidence/provenance about execution/result
```

not:

```text
Verification = adjudication
Verification = WorldTruth
```

A verification result can later become determination basis.

That separation should become explicit rather than removing verification terminology.

---

# 10. Enforcement / remedy reconstruction

GDF3 proved:

```text
Determination != Enforcement.
```

That actually makes `EnforcementRecord` more useful, not less.

A tooling system can separately answer:

```text
What was decided?
What consequence was ordered?
What consequence was attempted?
What actually happened?
```

This supports:

```text
failed enforcement
partial enforcement
irreversible consequence
later reversal
repair/remedy
```

without corrupting determination identity.

A `RemedyPlan` is similarly useful in practices that need:

```text
restart
restore
sanction
record correction
compensation
follow-up action
```

---

# 11. Role bundle templates: rebuild the familiar names safely

This is where we recover familiar Game vocabulary without destroying the deeper model.

## Referee / Judge

Reconstruct as:

```text
RefereeJudgeRoleBundle
```

A composable template over:

```text
observation/access
current-case authority
review authority or absence
rule-change authority or absence
enforcement authority or absence
```

The label `Judge` is useful.
The hidden authority topology remains explicit underneath.

---

## Game Master / Dungeon Master

Reconstruct as a **composable role template**, not one atomic role.

Possible components:

```text
world presentation
world generation
NPC control
semantic interpretation
case adjudication
facilitation
experience steering
```

A Game can select only the components it needs.

This is especially useful for Agent GM systems.

Instead of:

```text
Agent.role = GM
```

we can eventually support:

```text
GM preset
→ explicit capabilities + authority edges
```

which is far safer and more flexible.

---

## Coach / Advisor

Recover the human-friendly role while preserving:

```text
Advice != Control
Influence != BindingAuthority.
```

Good for:

```text
assistive play
party companions
strategic advisors
teaching systems
Agent copilots
```

---

## Moderator

A moderation role bundle can compose:

```text
receive reports
inspect evidence
classify
adjudicate case
apply enforcement
review
```

with any subset.

This avoids the common mistake that one `moderator` Boolean automatically grants all operations.

---

## Operator

Useful for:

```text
live service
server operations
tournament control
configuration
appointment/replacement
```

but always scope-specific.

---

## Experience Manager / Director

Useful for:

```text
adaptive difficulty
encounter selection
spawn/content pacing
narrative steering
```

but:

```text
ExperienceManagement != Player
ExperienceManagement != Adjudication by identity
GameAdaptation != SubjectLearning.
```

---

# 12. UI vocabulary: Participant should come back

`Participant` was correctly rejected as universal ontology.

But as a UI/query concept it is excellent.

Examples:

```text
Participants in this match
Participants visible to this player
Active participants
Observed participants
```

The correct reconstruction is:

```text
ParticipantView(scope/query)
```

computed from:

```text
Entity
RoleAssignment
causal/access/currentness relations
```

not stored as:

```text
entity.isParticipant = true
```

This gives us the ergonomic word without semantic damage.

---

# 13. Spectator and Audience should also return as views

These are strong human mental models.

## SpectatorView

Useful to query entities in an observational role.

But drill-down must reveal causal channels such as:

```text
vote
chat
report
bet
stream interaction
```

because:

```text
Spectator != causal nonparticipant.
```

## AudienceView

Useful as a collection/presentation projection.

But:

```text
Audience != CollectiveSubject
Audience != CollectiveAuthority.
```

---

# 14. Finality is a good UI concept

Players/operators absolutely understand:

```text
pending
reviewable
final
superseded
```

So `FinalityStatus` should be reconstructed.

But calculate it from current:

```text
review topology
currentness
DecisionLineage
```

rather than persist a metaphysical `isFinal` truth.

Guard:

```text
Final != True
Final != Correct
Final != ImmutableForever.
```

---

# 15. Rule / Standard should mostly stay ordinary language

This is the strongest caution case.

People find these words useful.

But stabilizing schema categories such as:

```text
kind = rule | standard
```

would reintroduce a false universal binary.

Therefore:

```text
RuleStandardLabels
= descriptive/authoring vocabulary only
```

unless a particular GameForm explicitly defines local meanings.

---

# 16. What “reconstruct” does not mean

This programme is **not**:

```text
create 37 new database tables
create 37 interfaces
create one giant Game ontology
give every GameForm every workflow
```

Instead, reconstruction can mean:

```text
one useful query name
one view
one UI card
one composable role preset
one workflow object
one audit projection
one policy file
```

depending on the concept.

The representation must be proportional to real utility.

---

# 17. Persistence policy

A strong practical rule emerges.

## Prefer derived

Use derived views for:

```text
ParticipantView
AuthorityProfile
RoleCausalAccessProfile
ParticipationAuthorityTopology
DecisionLineage
FinalityStatus
ConventionStatus
CaseDeterminationBoundary
```

when source state/events are available.

## Persist when lifecycle matters

Use durable operational records for:

```text
RoleAssignment
ScopedAuthorityEdge when explicit grants are source truth
DelegationGrant
AuthoritativeDeterminationRecord
ReviewRequest
AppealRequest
InterpretiveCommitment
EnforcementRecord
```

when their identity/history is itself operationally relevant.

This is more precise than either:

```text
persist everything
```

or:

```text
never materialize derived concepts.
```

---

# 18. Agent-first practical design rule

The deepest semantic layer should not be the only tool interface exposed to Agents.

An Agent forced to reason every turn from raw F1-F9 will waste context and introduce errors.

Instead:

```text
thin semantic core
→ rich derived tool surfaces
→ drill down only when needed
```

Example:

```text
get_authority_profile(agent-X)
```

may be much better than requiring an Agent to reconstruct 25 authority relations manually.

But the tool result should retain references/provenance sufficient to inspect those relations if challenged.

Thus:

```text
Agent-friendly compression
+ semantic drill-down
```

is the target.

---

# 19. Six practical reconstruction clusters

R0 groups the 37 concepts into six work families.

## P1 — Operational Role & Authority Toolkit

```text
RoleAssignment
ScopedAuthorityEdge
AuthorityProfile
AgentAuthorityManifest
RoleCausalAccessProfile
ParticipationAuthorityTopology
AuthoritySeparationPolicy
DelegationGrant
AppointmentReplacementRecord
```

Priority:

```text
HIGHEST
```

## P2 — Case Determination & Contestability Toolkit

```text
AuthoritativeDeterminationRecord
DeterminationBasisTrace
CaseDeterminationBoundaryDiagnostic
ReviewRequest
AppealRequest
ReviewContestabilityProfile
DecisionLineage
OfficialStatusCertificationView
```

Priority:

```text
HIGH
```

## P3 — Evidence / Norm / Explanation Toolkit

```text
EvidenceBundleForCase
NormApplicationView
InterpretiveCommitment
PrecedentLink
ConventionStatusView
DiscretionEnvelope
VerificationView
```

Priority:

```text
HIGH, BUT CONDITIONAL/GUARD-HEAVY
```

## P4 — Enforcement / Remedy Toolkit

```text
EnforcementRecord
RemedyPlan
```

## P5 — Role Bundle Templates

```text
Referee/Judge
GameMaster
Coach/Advisor
Moderator
Operator
ExperienceManager
```

## P6 — Human/Agent Vocabulary Views

```text
Participant
Spectator
Audience
Finality
Rule/Standard labels
```

---

# 20. Why P1 should come first

P1 wins the first focused reconstruction round because it is upstream of nearly everything else.

To build a safe:

```text
Judge
GM
Moderator
Review workflow
Delegation workflow
Agent action admission
Rule-change tool
```

we need to answer first:

```text
who occupies what role?
what operation is authorized?
in what scope?
for how long?
from what source?
what can be observed/controlled/influenced?
```

That is exactly P1.

P1 also has:

```text
very high cross-Game reuse
very high Agent utility
high cognitive compression
low-to-moderate misuse risk
strong derivation from frozen foundations
```

Therefore R0 selects:


enum GPR1 — Operational Role & Authority Toolkit

before rebuilding review, GM, evidence or precedent tooling.

---

# 21. Expected GPR1 research questions

GPR1 should not immediately implement a schema.

It should reconstruct the practical contracts for:

```text
RoleAssignment
ScopedAuthorityEdge
AuthorityProfile
AgentAuthorityManifest
RoleCausalAccessProfile
ParticipationAuthorityTopology
AuthoritySeparationPolicy
DelegationGrant
AppointmentReplacementRecord
```

and answer:

```text
Which are source records vs derived views?
What is the minimum stable field set?
How should scope be represented without one global hierarchy?
How should grants/revocation/expiry/delegation/replacement work?
How does an Agent query effective authority cheaply?
How do role presets expand into explicit authority without becoming truth authority?
What must be auditable?
Which concepts can share one generic relation representation?
Which ergonomic APIs/views are worth stabilizing?
```

Only after this should we decide whether implementation work is warranted.

---

# 22. R0 result

```text
Can deleted/non-foundational concepts be rebuilt?
YES.

Should they return as foundations?
NO.

Should many return as practical Game tools?
YES.
```

The strongest recovered principle is:

```text
Minimal semantic core
!= minimal usable vocabulary.
```

A strong Ordivon Game should have:

```text
small foundations
rich derived operational toolkit
clear provenance/drill-down
conditional workflows
human/Agent-friendly language
```

rather than exposing raw ontology everywhere.

---

# 23. Exact next round

```text
GPR1 — Operational Role & Authority Toolkit
```

GDF0-GDF3 remain frozen.

GPR1 is practical reconstruction, not foundation reopening and not yet implementation audit.
