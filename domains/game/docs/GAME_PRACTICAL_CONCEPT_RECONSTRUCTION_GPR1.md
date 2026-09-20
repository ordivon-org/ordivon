---
schema_version: 1
id: game.practical-concept-reconstruction.gpr1
title: Ordivon Game — GPR1 Operational Role & Authority Toolkit
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Reconstructs the highest-priority post-foundation practical toolkit for Role and Authority without reopening GDF0-GDF3. Stabilizes RoleAssignment as a practical source relation; DelegationGrant and explicit appointment/replacement change receipts as conditional workflow records; AuthoritySeparationPolicy as a configurable policy interface; and ScopedAuthorityEdge, AuthorityProfile, AgentAuthorityManifest, RoleCausalAccessProfile and ParticipationAuthorityTopology as normalized derived projections. Rejects a second generic authority source-of-truth, global rank/tree, authority=capability/legality, implicit subdelegation and the generalization of Station Zero's one-shot AuthorityGrant into delegation. Forty cross-regime cases, seventeen executable probes and twenty-seven audit checks pass.
evidence_status: strong
readiness: GPR1_COMPLETE
applies_to:
  - ordivon-game
related:
  - game.practical-concept-reconstruction.r0
  - game.authoritative-case-determination-foundations.v1
---
# Ordivon Game — GPR1 Operational Role & Authority Toolkit

## 0. Scope

GPR0 identified the highest-leverage practical cluster:

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

GPR1 asks a narrower question than Foundations:

> What practical contracts should Ordivon Game expose so Humans and Agents can author, inspect, delegate, debug and consume role/authority structure cheaply, while the frozen semantic substrate remains authoritative?

This round does **not** reopen:

```text
GDF0 Play / Game
GDF1 Action / Control / Skill
GDF2 Challenge / Failure / Mastery
GDF3 Authoritative Case Determination
```

and does not yet introduce generic implementation types into the product runtime.

---

# 1. Main result

The correct practical architecture is **not**:

```text
one universal Authority table
+ one Role enum
+ one global permission hierarchy
```

It is:

```text
heterogeneous owner-local authority sources
        ↓
normalized effective authority projection
        ↓
Human / Agent profiles, manifests and topology views
```

with a small number of durable workflow records only where identity/history really matter.

The central GPR1 decision is therefore:

```text
SOURCE / WORKFLOW
-----------------
RoleAssignmentRecord
DelegationGrantRecord          when delegation exists
RoleAssignmentChangeReceipt    when appointment/replacement workflow exists
AuthoritySeparationPolicy      owner-local policy source

DERIVED
-------
ScopedAuthorityEdge
AuthorityProfile
AgentAuthorityManifest
RoleCausalAccessProfile
ParticipationAuthorityTopology
```

This boundary prevents a practical toolkit from becoming a second competing source of Game authority.

---

# 2. Why `ScopedAuthorityEdge` should be derived rather than generic source truth

R0 left open whether `ScopedAuthorityEdge` should itself be persisted as the universal authority record.

GPR1 rejects that design.

Real authority can originate from materially different sources:

```text
constitutive Game rule
role template
current RoleAssignment
direct entity grant
self-authored practice commitment
delegation
live-operations policy
tournament regulation
moderation policy
local GameForm rule
```

Forcing all of these to become one source-table ontology would lose source-specific lifecycle and ownership semantics.

Instead, each source should compile/project to one normalized query form:

```text
ScopedAuthorityEdge
```

The edge is therefore analogous to a materialized semantic view:

```text
source authority facts
→ effective current edge
```

not:

```text
cached edge
→ authority becomes true because cache says so.
```

Frozen practical law:

```text
DerivedAuthorityCache
!= independent authority source.
```

---

# 3. RoleAssignmentRecord

## 3.1 Why reconstruct it

`Role` survived the foundations programme as an important relational/institutional/narrative position, while:

```text
Role != Occupant.
```

In practice, however, the assignment relation often has real identity/history/coordination value.

Examples:

```text
Alice is Judge for Match 42
Agent X is Moderator for Channel A
Bob is Commander for Mission M
Human H occupies GM-facilitator role for Session S
```

So GPR1 stabilizes:

```text
RoleAssignmentRecord
```

as a practical source relation.

## 3.2 Minimum contract

```text
assignmentId
occupantRef
roleRef
scopeRefs
validFrom
validUntilOrOpen
assignmentBasisRefs
provenanceRefs
```

Optional:

```text
supersedesAssignmentId
displayLabel
```

## 3.3 What it deliberately does not mean

```text
RoleAssignment != AuthorityGrant
RoleAssignment != CapabilityGrant
RoleAssignment != ControlGrant
RoleAssignment != identity transformation
```

A role template may cause authority edges to derive for its occupant, but that is a separate relation whose provenance must be visible.

This keeps labels ergonomic without making them magical.

---

# 4. Role currentness and replacement

A RoleAssignment is current only inside its declared scope/time and while no authoritative ending/superseding transition invalidates it.

For example:

```text
Alice → Judge / Match 1 / [T0,T10)
Bob   → Judge / Match 1 / [T10,...)
```

At T10:

```text
role identity may continue
occupant changes
```

Therefore:

```text
RoleContinuity != OccupantContinuity.
```

Any authority derived **via Alice's assignment** ends with that assignment.

But an authority grant issued directly to Alice does not automatically transfer to Bob.

This is a crucial practical guard:

```text
Replacement != AuthorityTransferByIdentity.
```

---

# 5. AppointmentReplacementRecord compresses further

R0 treated `AppointmentReplacementRecord` as a candidate workflow object.

GPR1 finds it should not compete with `RoleAssignmentRecord` as a second canonical role object.

The useful practical form is better described as:

```text
RoleAssignmentChangeReceipt
```

used only when an explicit appointment/replacement workflow needs audit or coordination.

Minimum:

```text
changeId
changeKind = appointment | replacement | end
roleRef
scopeRefs
oldAssignmentIdOrNull
newAssignmentIdOrNull
effectiveAt
authorityBasisRefs
provenanceRefs
```

Thus:

```text
Appointment / Replacement
= lifecycle workflow over RoleAssignment
```

not independent ontology.

Also preserve:

```text
AppointmentAuthority
!= CaseAuthority
!= RuleChangeAuthority
!= EnforcementAuthority.
```

---

# 6. ScopedAuthorityEdge — normalized effective view

The strongest practical abstraction in the branch remains:

```text
ScopedAuthorityEdge
```

but its role is now precise.

It answers:

> Under the queried context/currentness, what operation can this holder authoritatively bind/change/decide, over what target and scope, and from what source?

## Minimum normalized shape

```text
edgeIdOrDigest
holderRef
operationKey
targetSelectorRefOrAny
scopeRefs
activationConditionRefs
validFrom
validUntilOrOpen
authoritySourceRefs
derivationRefs
```

Optional:

```text
viaRoleAssignmentIds
operationFamily
humanReadableScopeSummary
```

The minimum shape is a query contract, not a required database schema.

---

# 7. Open operation keys, not one universal authority enum

GDF3-B found recurring operation families such as:

```text
observe / receive
advise / recommend
propose
decide / rule
execute / enforce
verify / certify
review / override
change rule / policy
change dynamics
appoint / replace / delegate
allocate access / eligibility
```

These are excellent **UI/query families**.

But GPR1 does not freeze them as the exhaustive semantic operation vocabulary.

Instead use namespaced owner-local keys such as:

```text
game.action.admit
game.case.decide
game.case.review
game.rule.change
game.result.certify
game.sanction.enforce
station-zero.directive.issue
my-game.encounter.reseed
```

with an optional broad `operationFamily` for grouping/display.

This gives cross-Game tooling common structure without constraining future GameForms to today's vocabulary.

---

# 8. Scope must not recreate a hierarchy

The obvious practical temptation is:

```text
scope = global > tournament > match > object
```

and then infer:

```text
broader = stronger.
```

GDF3 already proved that false.

An entity may have:

```text
global rule-change authority
```

while another has:

```text
local final match ruling authority.
```

Neither is universally “above” the other.

Therefore GPR1 freezes a practical rule:

```text
scopeRefs resolve through owner-local scope semantics.
```

They may refer to dimensions such as:

```text
practice
run/session
match
team/faction
spatial zone
category
rule version
object class
specific object
phase
```

but there is no required universal scope tree/lattice.

Cross-Game tools may display a scope summary; actual matching remains owner-local and source-traceable.

---

# 9. AuthorityProfile

Humans and Agents should not repeatedly traverse every raw authority source.

GPR1 therefore stabilizes:

```text
AuthorityProfile(holder, context, asOf)
```

as a derived view.

It can return:

```text
effectiveEdges
conditionalEdges
authorityPolicyConstraints
conflictsOrUnknowns
authorityStateDigest
sourceRefs
```

A specific authority check should support at least:

```text
effective
conditional
not_established
blocked_by_authority_policy
conflicted_or_unknown
```

This is deliberately more precise than a Boolean:

```text
hasPermission = true / false
```

because conditional authority, unresolved source state and separation policy are real practical states.

---

# 10. Why `not_established` is better than universal `deny`

Absence of one effective edge does not prove metaphysical impossibility.

Possible reasons include:

```text
no authority source exists
source is unavailable
scope is wrong
activation condition unresolved
another authority source has not been loaded
local owner treats absence as deny
local owner permits via a different rule
```

So a generic cross-Game authority query should prefer:

```text
not_established
```

over claiming universal denial semantics.

A local admission/policy layer can then turn that into an actual deny if its rules demand it.

---

# 11. Authority != Capability

This becomes one of GPR1's most important practical laws.

Example:

```text
Chief Engineer has authority to authorize reactor repair
```

but may lack:

```text
physical repair capability.
```

Conversely:

```text
Agent process can technically edit the rule file
```

but lacks:

```text
Game rule-change authority.
```

Therefore:

```text
Authority != Capability.
```

A combined product UI can show both, but the toolkit must never infer one from the other.

---

# 12. Authority != Action Legality

Even stronger:

```text
AuthorityProfile
!= GameAction admission.
```

A holder may have authority to make some class of decision while a requested action is currently impossible/illegal due to:

```text
World state
Game rule
resource constraint
capability constraint
stale revision
wrong target
```

Those remain GDF0/GDF1 responsibilities.

So an Agent-facing tool might expose:

```text
AuthorityManifest: may propose/authorize operation X
```

while the action tool later returns:

```text
REJECTED: current action illegal
```

without contradiction.

This prevents the practical authority layer from turning into a universal permissions engine.

---

# 13. AgentAuthorityManifest

For Agent-first systems, the highest-value consumer projection is:

```text
AgentAuthorityManifest
```

It provides a bounded current snapshot answering:

```text
What may this Agent currently bind, decide, change, review or enforce?
```

Minimum:

```text
principalRef
contextRef
authorityStateDigest
generatedAtCurrentness
effectiveOperations
conditionalOperations
sourceRefs
manifestDigest
```

Per operation:

```text
operationKey
targetOrScopeSummary
disposition
conditionsOrApprovals
validUntilOrCurrentnessBoundary
sourceRefs
```

---

# 14. AgentAuthorityManifest must fail stale

An authority manifest is a **derived snapshot**.

Suppose at T0:

```text
Agent X may review Match 1
```

and manifest M1 is generated.

At T1:

```text
delegation revoked
```

Then M1 must not remain silently valid.

A relevant authority source/currentness change must alter:

```text
authorityStateDigest
```

and therefore the usable manifest identity/digest.

This makes Agent authority analogous to other digest/currentness-bound inputs already used in Ordivon engineering.

Strong law:

```text
StaleAuthorityManifest
!= current authority evidence.
```

---

# 15. AgentAuthorityManifest is not an action manifest

This distinction is critical enough to repeat:

```text
AgentAuthorityManifest
!= legal action set
!= capability set
!= available action set
!= GameAction admission.
```

An Agent needs all of these layers for different reasons.

The authority manifest answers only the authority question.

This keeps the tool compact and semantically honest.

---

# 16. RoleCausalAccessProfile

Authority alone does not explain how a role participates in a Game.

GPR1 therefore stabilizes a multi-axis view:

```text
RoleCausalAccessProfile
```

with dimensions such as:

```text
observationAccess
communicationChannels
adviceOrProposalChannels
controlOrExecutionAccess
bindingAuthorityEdges
```

This profile is especially useful for:

```text
Player
spectator
coach
GM
moderator
operator
companion Agent
NPC controller
assistant Agent
```

because it prevents one scalar “access level.”

Examples:

```text
Coach:
  observe = broad
  advise = yes
  control = no
  bind = no

Referee:
  observe = incident/replay
  decide = yes
  enforce = maybe no

Automation:
  observe = sensor state
  control = sanction system
  decide = no
```

Strong laws:

```text
Observation != Control
Influence != BindingAuthority
Control != Authority
Authority != AbilityToRealizeOutcome.
```

---

# 17. ParticipationAuthorityTopology

The rejected foundation candidate becomes a very good derived graph.

A practical topology view can layer:

```text
1. Entity / RoleAssignment
2. Causal access
3. Effective authority
4. Delegation / assignment provenance
```

This is useful for:

```text
Game design
GM/moderation authoring
Agent debugging
permission inspection
tournament administration
security review
live-operation diagnostics
```

But it must remain clear that:

```text
Graph != Tree
Graph != Rank
Graph != persisted canonical authority truth
Visual adjacency != authority strength.
```

A topology graph is a way to see the model, not another model authority.

---

# 18. AuthoritySeparationPolicy

Foundations rejected universal separation-of-duties requirements.

That does not make separation policy useless.

Many GamePractices reasonably want rules such as:

```text
one adjudicator cannot review own ruling
critical rule change requires second approval
result certification must come from independent authority
moderation classifier cannot directly enforce
```

So GPR1 stabilizes a **policy interface**, not a universal invariant.

Minimum:

```text
policyId
scopeRefs
constraintRules
policyProvenanceRefs
validFrom
validUntilOrOpen
```

Useful standard rule families:

```text
distinct_holder_required
self_review_prohibited
second_authority_required
provenance_independence_required
owner_local_custom_rule
```

Evaluation:

```text
not_applicable
satisfied
violated
unresolved
```

The key is configurability.

A solitary game may legitimately use none of these constraints.

A regulated tournament may use several.

---

# 19. DelegationGrantRecord

Delegation is one of the strongest examples of practical reconstruction.

Foundation result:

```text
DelegationPrimitive = REJECTED.
```

Practical result:

```text
DelegationGrantRecord = HIGH VALUE.
```

When authority really is delegated, the grant has useful lifecycle identity.

Minimum:

```text
delegationId
grantorRef
delegateRef
delegatedOperationKey
targetSelectorRefOrAny
scopeRefs
validFrom
validUntilOrOpen
delegationAuthorityBasisRefs
provenanceRefs
```

Optional:

```text
parentDelegationId
revocationPolicyRef
activationConditionRefs
displayReason
```

---

# 20. Delegating an operation requires delegation authority

One subtle but crucial rule:

```text
authority to perform X
!= authority to delegate X.
```

For example:

```text
Alice may decide Case K
```

does not automatically mean:

```text
Alice may authorize Bob to decide Case K.
```

The delegation must itself have an admitted authority basis.

Thus:

```text
grantor must currently possess authority to delegate
this operation/scope
```

not merely authority to execute the underlying operation.

This preserves GDF3-B's operation separation in practical workflows.

---

# 21. Delegated scope cannot silently expand

A grant cannot produce authority beyond what its admitted delegation basis permits.

If Alice may delegate:

```text
review Match 1 until Turn 10
```

she cannot create:

```text
Bob may review all tournaments forever.
```

The exact scope-matching mechanism remains owner-local, but the cross-Game practical law is:

```text
DelegatedScope
must be admitted by
DelegationAuthorityBasisScope.
```

This is a safe, useful check without one universal scope algebra.

---

# 22. Subdelegation is never implicit

Suppose:

```text
Alice delegates review authority to Bob.
```

This does not automatically imply:

```text
Bob may delegate it to Carol.
```

Subdelegation requires its own authority/basis.

If present, a child delegation should retain:

```text
parentDelegationId
+ current delegation authority basis
```

for audit/provenance.

Therefore:

```text
Delegation != TransitiveDelegationByDefault.
```

---

# 23. Revocation cannot be inferred from grantor identity universally

A common implementation assumption is:

```text
grantor issued it
→ grantor may always revoke it.
```

That is a practice policy, not a universal law.

Some grants may be:

```text
irrevocable for a period
revocable only by another role
revocable by either grantor or supervisor
automatically expired by condition
```

Therefore DelegationGrant carries or resolves a:

```text
revocationPolicyRef
```

when this matters.

Expiry/revocation changes current authority but does not erase historical provenance.

---

# 24. Delegation != one-shot action approval

This became one of GPR1's strongest findings from the actual repository.

Current Station Zero contains an `AuthorityGrant` bound to:

```text
proposalId
actionCandidateId
contextDigest
worldDigest
policyRevision
operationKind
targetId
expiresAtTick
consumedAtTick
issuedBy
```

The grant is:

```text
context/world bound
expires
consumed once
```

This is a strong design for its current purpose.

But semantically it is closer to:

```text
OneShotActionAuthorizationGrant
```

than:

```text
DelegationGrant.
```

It does not transfer a reusable authority operation to the actor.

Therefore GPR1 explicitly rejects generalizing the current type by name alone.

Strong law:

```text
Delegation != OneShotActionApproval.
```

---

# 25. Current Station Zero `ActorProfile.role`

The existing Team domain has:

```text
engineer
medic
security
coordinator
```

and uses those labels for:

```text
objective selection
mandate hints
Agent context
policy attributes
```

This is useful local product structure.

But it is not yet a generic `RoleAssignmentRecord` because it lacks the cross-Game concerns of:

```text
assignment identity
validity interval
scope-independent history
assignment provenance
replacement relation
```

GPR1 therefore does **not** propose mechanically replacing `ActorRole` with a generic framework type.

Instead it classifies it as:

```text
LOCAL_ROLE_CONFIGURATION
```

that could later project into a generic RoleAssignment view if a real consumer needs that interoperability.

---

# 26. Current Station Zero `AuthorityDecision`

Current `AuthorityDecision` binds:

```text
actor
action candidate
context digest
world digest
policy mode/revision
attributes
outcome
reason
```

and can produce:

```text
permit
require-human
deny
```

This is also useful.

But it represents:

```text
contextual policy evaluation for one action candidate
```

not a durable generic authority relation.

Therefore:

```text
AuthorityDecision
!= ScopedAuthorityEdge.
```

A future authority profile can inform such a policy decision, but the concepts should remain distinct.

---

# 27. `require-human` must remain local, not universal

Station Zero's current policy can require explicit Human authority for high-risk actions.

That is a legitimate product rule.

But GDF3 proved:

```text
Human substrate != semantic authority kind.
```

Therefore GPR1 does not promote:

```text
require-human
```

into generic authority semantics.

A different Game might require:

```text
second Agent
committee
player vote
rule-engine certification
server operator
self-authored confirmation
```

The generic concept is:

```text
additional / specific authority condition
```

while Human is one local holder/configuration.

---

# 28. Authority profile vs action-admission pipeline

The current code's `candidateAllowed` is useful evidence for the right boundary.

Conceptually:

```text
candidate
+ authority-policy result
+ one-shot approval if required
→ may proceed
```

But the action still depends on Game/World semantics.

GPR1 generalizes only this discipline:

```text
Authority is an input to admission where relevant,
not the entire admission function.
```

This is the practical counterpart of GDF1/GDF3 owner separation.

---

# 29. Role bundles become safer after GPR1

GPR0 intentionally postponed:

```text
Judge
GM
Moderator
Operator
Coach
ExperienceManager
```

until P1 existed.

We can now see how those bundles should eventually work.

Example:

```text
RefereeJudge preset
→ Role definition/template
→ RoleAssignment
→ source-specific authority rules
→ ScopedAuthorityEdges
→ AuthorityProfile
```

The label remains ergonomic.
The profile remains explicit.

Same for:

```text
GM
Moderator
Operator
```

Thus GPR1 supplies the missing substrate for later P5 role-template reconstruction.

---

# 30. Stress test — solo and self-authored play

A solitary player may occupy:

```text
player
author
certifier
```

roles simultaneously.

GPR1 permits this.

No separation policy is required by default.

The toolkit merely keeps operations distinguishable if the practice cares about them.

This preserves GDF3's conclusion:

```text
ExternalInstitution
!= necessary condition for authority.
```

---

# 31. Stress test — multiplayer peers

Two players may share the same visible label:

```text
Player
```

while having different scoped access/authority due to:

```text
team
faction
object ownership
phase
position
current assignment
```

Therefore a role label alone cannot generate one universal authority profile.

RoleAssignment + owner-local authority sources + normalized projections handle this naturally.

---

# 32. Stress test — coach and spectator

Coach:

```text
observe broad state
recommend action
cannot execute
cannot bind
```

Spectator reporter:

```text
observe
submit report/evidence
cannot decide case
```

These cases validate `RoleCausalAccessProfile` as multi-axis rather than a participant/access scalar.

---

# 33. Stress test — TTRPG GM and co-GM

One GM can combine:

```text
world presentation
NPC control
case adjudication
```

while another co-GM handles:

```text
NPC control
content generation
```

with no case authority.

The same display label can therefore compile into different practical profiles.

This confirms the later role-template design should be:

```text
composable preset
```

not atomic semantic role.

---

# 34. Stress test — floor judge / head judge / operator

A tournament can have:

```text
Floor Judge:
  first-instance case authority

Head Judge:
  review/override authority

Operator:
  appointment/replacement authority
```

No useful global rank captures all operation dimensions.

The graph/profiles do.

This is a direct practical proof that:

```text
AuthorityTopology != Tree.
```

---

# 35. Stress test — moderator Agent

An Agent can first be only:

```text
classifier / recommendation source
```

then later receive:

```text
case-decision authority
```

without changing model/provider identity.

The correct change is:

```text
authority sources/profile/manifest
```

not:

```text
model kind.
```

Thus:

```text
SameModelIdentity
+ ChangedAuthoritySource
→ ChangedAuthorityManifest.
```

---

# 36. Stress test — provider substitution

Conversely:

```text
DeepSeek → another model
```

under the same semantic actor/role/authority configuration need not change authority at all.

So:

```text
ProviderChange
!= AuthorityChange by identity.
```

This matters directly for Agent-first resilience and provider interchangeability.

---

# 37. Stress test — authority vs technical capability

A model/process may technically be capable of:

```text
editing rules
calling an admin endpoint
writing a state object
```

while Game authority says:

```text
not authorized.
```

Likewise a Human authority holder may be unable to execute an effect directly.

This validates the separate profile surfaces:

```text
capability
causal access
binding authority
```

and prevents security mechanisms from becoming Game authority by accident.

---

# 38. Stress test — stale manifest

At revision R1:

```text
Agent X has delegated review authority.
```

Manifest:

```text
M1 / authorityStateDigest = D1
```

At revision R2:

```text
grant revoked.
```

New state:

```text
D2 != D1.
```

M1 is no longer valid evidence of current authority.

This validates the digest/currentness boundary for Agent-facing compressed views.

---

# 39. Stress test — overlapping provenance paths

A holder may gain the same operation through:

```text
role template
+ direct grant
+ temporary delegation
```

The effective profile can deduplicate the operation for ergonomics while retaining multiple:

```text
authoritySourceRefs / derivationRefs.
```

The topology view can expose all paths.

This prevents a normalized view from destroying provenance.

---

# 40. Stress test — collective contribution

Audience/jury members may submit votes.

Their causal contribution may be strong.

But unless current practice gives each member binding authority over the official result:

```text
VoteContribution
!= IndividualBindingAuthority.
```

An aggregation rule may produce the official result separately.

The toolkit therefore handles collectives without inventing `CollectiveAuthority` as a primitive.

---

# 41. The nine GPR1 concept verdicts

| R0 concept | GPR1 verdict |
| --- | --- |
| RoleAssignment | **STABILIZE source relation** |
| ScopedAuthorityEdge | **STABILIZE normalized derived view** |
| AuthorityProfile | **STABILIZE derived view** |
| AgentAuthorityManifest | **STABILIZE context-bound derived snapshot** |
| RoleCausalAccessProfile | **STABILIZE derived multi-axis view** |
| ParticipationAuthorityTopology | **STABILIZE derived graph view** |
| AuthoritySeparationPolicy | **STABILIZE policy interface, not universal invariant** |
| DelegationGrant | **STABILIZE conditional source/workflow** |
| AppointmentReplacementRecord | **retain as optional RoleAssignment change receipt** |

This is a much smaller source layer than a naive implementation would produce.

---

# 42. Cross-cutting practical law set

```text
RoleAssignment != AuthorityGrant
RoleLabel != ResponsibilityTopology
Authority != Capability
Authority != ActionLegality
Authority != GlobalRank
AuthorityTopology != Tree
BroaderScope != StrongerAuthority
CausalAccess != BindingAuthority
Observation != Control
Influence != BindingAuthority
SameEntityOrModel != SameAuthorityOperation
Delegation != Replacement
Delegation != OneShotActionApproval
Replacement != AuthorityTransferByIdentity
AgentAuthorityManifest != GameActionAdmission
AuthorityProfile != source of truth
DerivedAuthorityCache != independent authority source
```

These laws are the guard rails that let the practical vocabulary be rich without undoing the Foundations work.

---

# 43. What GPR1 does not standardize

GPR1 intentionally does **not** create one universal:

```text
Role registry
Authority database
scope hierarchy
policy language
permission enum
operation enum
organization model
collective actor model
RBAC system
ABAC system
legal delegation framework
```

A concrete Game may use any of these implementation techniques.

The practical toolkit standardizes only the semantic/query boundaries needed for reuse and safe compression.

---

# 44. RBAC / ABAC are mechanisms, not the model

Current Station Zero's authority evaluator resembles an attribute/policy evaluation:

```text
subject attributes
action attributes
target attributes
environment attributes
policy mode
```

That is a legitimate implementation pattern.

Other Games may prefer:

```text
role grants
capability tokens
ACLs
rule predicates
social/institutional authorization
self-authored practice rules
```

GPR1 should be implementable over all of them.

Thus:

```text
RBAC != authority ontology
ABAC != authority ontology
CapabilityToken != authority ontology.
```

They are possible source/decision mechanisms that can compile to or consume the toolkit views.

---

# 45. Practical API direction — research only

Without committing to implementation, the useful future consumer surface is now visible.

Possible query family:

```text
get_role_assignments(subject/context)
get_authority_profile(holder, context)
check_authority(holder, operation, target, context)
get_agent_authority_manifest(agent, context)
get_role_causal_access(role/holder, context)
get_participation_authority_topology(context)
```

Possible workflow family:

```text
issue_delegation(...)
revoke_delegation(...)
appoint_role(...)
replace_role_occupant(...)
```

But GPR1 does not yet assert that Ordivon Game should implement these exact endpoints.

They are now concrete candidates for a later consumer audit.

---

# 46. Why we should not implement the generic library immediately

The practical contracts are now much clearer, but implementation should still be consumer-driven.

We need to know:

```text
Which actual GameForms need generic role assignment history?
Which need delegation?
Which need topology visualization?
Which Agent consumers benefit materially from an authority manifest?
Can existing local product types project into the views cheaply?
Would a shared library remove duplication or merely introduce framework burden?
```

So GPR1 ends at:

```text
practical contract stabilization
```

not:

```text
repository-wide refactor.
```

---

# 47. Evidence

GPR1 evidence contains:

```text
9 mapped practical contracts
40 cross-regime stress cases
17 executable probes
27 audit checks
17 cross-cutting practical laws
5 current-engineering classification findings
```

Stress regimes include:

```text
solo direct play
self-authored practice
multiplayer peers
commander/specialist delegation
coach/spectator
TTRPG GM/co-GM
tournament judges/operator
moderation
live operations
direct grants
role inheritance/replacement
temporary delegation
expiry/revocation/subdelegation
one-shot approval
provider substitution
same-model role fusion
authority/capability separation
authority/legality separation
incomparable scopes
separation-of-duties
stale manifests
collective voting
```

No FoundationReopenCondition is triggered.

---

# 48. GPR1 result

The final practical architecture is:

```text
               LOCAL SOURCE AUTHORITY
        ┌──────────┬───────────┬─────────────┐
        │ roles    │ rules     │ delegation  │ ...
        └────┬─────┴─────┬─────┴──────┬──────┘
             │           │            │
             └───────────┼────────────┘
                         ↓
              ScopedAuthorityEdge
                         ↓
       ┌─────────────────┼─────────────────┐
       ↓                 ↓                 ↓
AuthorityProfile  AgentAuthorityManifest  Topology
       ↓                                   ↑
RoleCausalAccessProfile ────────────────────┘
```

with:

```text
RoleAssignment
```

providing practical role identity/currentness,

and:

```text
DelegationGrant
RoleAssignmentChangeReceipt
AuthoritySeparationPolicy
```

appearing only when the concrete practice needs those workflows/policies.

---

# 49. Next practical reconstruction round

R0 ranked P2 immediately after P1.

GPR1 now supplies exactly the authority substrate P2 needs.

So the next practical round is:

```text
GPR2 — Case Determination & Contestability Toolkit
```

Candidate reconstruction targets:

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

This is an ordering inside the already-established practical reconstruction map.

It is **not** a new GDF branch or foundation admission.
