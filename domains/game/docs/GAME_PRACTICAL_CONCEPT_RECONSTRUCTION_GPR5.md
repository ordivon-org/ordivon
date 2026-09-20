---
schema_version: 1
id: game.practical-concept-reconstruction.gpr5
title: Ordivon Game — GPR5 Role Bundle Templates
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Reconstructs familiar high-level Game roles as optional authoring/template families over GPR1-GPR4 rather than semantic primitives or hidden authority sources. Stabilizes RoleBundleTemplateDefinition, RoleBundleInstantiationPlan, RoleBundleManifest, RoleBundleCompositionView and RoleBundleCompatibilityDiagnostic; reconstructs Referee/Judge, GameMaster, Coach/Advisor, Moderator, Operator and ExperienceManager as configurable responsibility-slice presets. Current Station Zero engineer/medic/security/coordinator roles prove local role-template value while roleId, controllerKind, capability, objective doctrine and authority remain separable. Seventy cross-regime stress cases, forty executable probes and forty-one audit checks pass.
evidence_status: strong
readiness: GPR5_COMPLETE
applies_to:
  - ordivon-game
related:
  - game.practical-concept-reconstruction.gpr1
  - game.practical-concept-reconstruction.gpr2
  - game.practical-concept-reconstruction.gpr3
  - game.practical-concept-reconstruction.gpr4
---
# Ordivon Game — GPR5 Role Bundle Templates

## 0. Scope

GPR5 reconstructs R0 P5:

```text
Referee / Judge
Game Master
Coach / Advisor
Moderator
Operator
Experience Manager
```

These concepts are clearly too useful to discard.

But GDF3/GPR1 already established that familiar role labels are not sufficient semantic foundations for:

```text
authority
control
capability
observation
review
rule change
enforcement
remedy
```

So the practical question is:

> How can Ordivon expose familiar, productive high-level roles to designers, players and Agents without making the role label itself a hidden permission system?

No frozen foundation is reopened.

---

# 1. Main result

The answer is:

```text
RoleBundleTemplate
=
authoring / configuration preset
```

not:

```text
RoleBundleTemplate
=
authority source.
```

The resulting architecture is:

```text
RoleBundleTemplateDefinition
        │
        ↓
RoleBundleInstantiationPlan
        │
        ├── local RoleAssignment
        ├── causal access policy
        ├── capability/tool config
        ├── control config
        ├── GPR1 authority sources
        ├── GPR2 determination/review ops
        ├── GPR3 explanation/norm interfaces
        └── GPR4 enforcement/remedy ops
                │
                ↓
        actual current sources
                │
                ↓
        RoleBundleManifest
```

For multi-role systems:

```text
RoleBundleCompositionView
```

explains how responsibilities are fused or split.

For authoring safety:

```text
RoleBundleCompatibilityDiagnostic
```

checks hidden grants and mismatches.

---

# 2. The central law: no hidden grants

Every role template freezes this default:

```text
NO_HIDDEN_GRANTS
```

Selecting:

```text
Judge
GM
Moderator
Operator
Coach
Experience Manager
```

must **not** by itself create:

```text
observation access
control
capability
tool access
authority
rule change power
case authority
review authority
enforcement authority
remedy authority
```

Strong laws:

```text
RoleBundleTemplate != RoleAssignment
RoleBundleTemplate != AuthorityGrant
RoleBundleTemplate != CapabilityGrant
RoleBundleTemplate != ControlGrant
TemplateSelection != EffectiveAuthority
```

---

# 3. Why role bundles are still worth keeping

Rejecting role labels as semantic primitives does not mean making designers work directly with dozens of raw authority edges.

Human authoring wants language like:

```text
This Agent is the tactical advisor.
This Human is the head judge.
This service is the tournament operator.
This model is the encounter director.
```

That language compresses recurring configurations.

So the role bundle is a **practical macro**:

```text
familiar label
→ expected responsibility slices
→ required source/config checklist
→ generated runtime manifest
```

This follows the programme-wide pattern:

```text
thin semantics underneath
rich ergonomic concepts above.
```

---

# 4. RoleBundleTemplateDefinition

GPR5 stabilizes:

```text
RoleBundleTemplateDefinition
```

as an optional authoring preset.

Minimum practical fields:

```text
templateId
displayLabel
purpose
responsibilitySlices
defaultAdmissionPolicy
ownerBoundaryRefs
provenance/version
```

Each responsibility slice can contain:

```text
sliceKey
purpose
causalAccessNeeds
toolOrCapabilityHints
authorityOperationIntentKeys
controlOrActionIntentKeys
relatedToolkitRefs
defaultEnabled
separationHints
```

The key phrase is:

```text
IntentKeys / Hints
```

not grants.

---

# 5. Responsibility slices are the real reusable unit

A broad role label is useful because it tends to recur as a bundle of smaller responsibilities.

Examples:

```text
observe case
classify
recommend
propose action
control entity
decide case
review case
interpret rule
change rule
verify result
issue consequence
execute consequence
approve remedy
steer pacing
schedule content
```

These slices can be:

```text
combined
omitted
split across holders
shared across holders
reused under different display labels
```

Therefore:

```text
TemplateLabel != ResponsibilityTopology.
```

---

# 6. RoleBundleInstantiationPlan

When a designer chooses a template, Ordivon should not immediately mutate authority.

Instead GPR5 reconstructs:

```text
RoleBundleInstantiationPlan
```

which answers:

> What concrete local sources/configuration would be needed to realize this role bundle here?

Possible output:

```text
required RoleAssignment
required observation/access changes
required authority operation specs
required control/capability/tool specs
required separation-policy checks
unsatisfied dependencies
owner-local bindings
planDigest
```

This is a **derived authoring plan**.

Strong:

```text
InstantiationPlan != AdmittedAuthority.
```

---

# 7. Partial role realization is legitimate

A template is not a checklist that must always be fully enabled.

Example:

```text
GameMaster template
```

may contain:

```text
facilitation
world presentation
NPC control
interpretation
case adjudication
rule change
experience steering
```

A specific GameForm may intentionally instantiate only:

```text
world presentation
NPC control
```

while rules and adjudication are fully automated.

That is not an incomplete GM implementation.

It is a legitimate local GM variant.

---

# 8. RoleBundleManifest

Once actual local sources exist, Humans and Agents need a compact current answer:

> What does this holder actually do and have authority to do now?

So GPR5 stabilizes:

```text
RoleBundleManifest
```

as a derived current view.

It may expose:

```text
displayLabels
roleAssignmentRefs
activeResponsibilitySlices
causalAccessSummary
effectiveAuthorityOperations
conditionalAuthorityOperations
controlOrCapabilitySummary
toolSummary
separationPolicySummary
sourceRefs
bundleStateDigest
```

This is the runtime-safe version of the friendly role label.

---

# 9. Manifest truth flows upward from sources

Suppose the UI says:

```text
Role: Head Judge
```

but actual authority sources only contain:

```text
game.case.decide
```

and not:

```text
game.case.review
```

Then the manifest must show:

```text
case_decide = effective
case_review = not established
```

rather than granting review power because the display label says Head Judge.

Therefore:

```text
RoleBundleManifest
= projection of actual current sources
```

not projection of expectations attached to the word.

---

# 10. Same label can mean different bundles

The word:

```text
Referee
```

means materially different things in:

```text
football
chess
speedrunning
e-sports
TTRPG
social deduction
```

One may:

```text
signal only
```

another:

```text
decide cases
```

another:

```text
certify results
```

another:

```text
decide + enforce
```

So GPR5 freezes:

```text
SameDisplayLabelCanMapToDifferentLocalBundles.
```

---

# 11. Different labels can also mean the same operational bundle

Conversely:

```text
Judge
Arbiter
Official
Referee
Game Marshal
```

could map to functionally equivalent responsibility/authority slices in different games.

Therefore:

```text
DifferentDisplayLabelsCanMapToEquivalentOperationalBundles.
```

This supports localization and genre vocabulary without semantic duplication.

---

# 12. RoleBundleCompositionView

One holder may wear several hats.

Example:

```text
same Human:
Moderator
+ Operator
```

or:

```text
same GM:
Narrator
+ NPC controller
+ Case adjudicator
```

GPR5 reconstructs:

```text
RoleBundleCompositionView
```

to show:

```text
holders
bundle/slice refs
shared slices
distinct slices
effective operation mappings
causal access mappings
separation conflicts
unassigned responsibilities
```

---

# 13. Composition does not union authority

This is crucial.

If a holder has labels:

```text
Moderator
Operator
```

we must not compute:

```text
all Moderator powers
UNION
all Operator powers
```

from template catalogs.

Instead:

```text
labels/templates
→ authoring expectations only
actual current sources
→ effective operations
```

Therefore:

```text
TemplateComposition != AuthorityUnion.
```

---

# 14. Template inheritance does not grant authority either

Authoring may want:

```text
HeadJudge extends Judge
```

This can safely reuse:

```text
UI labels
responsibility slice suggestions
tooling defaults
documentation
```

But it cannot mean:

```text
copy all parent's effective authority into child holder.
```

Thus:

```text
TemplateInheritance != ImplicitGrant.
```

Inheritance belongs to authoring reuse, not authority semantics.

---

# 15. RoleBundleCompatibilityDiagnostic

Because friendly role labels are so easy to over-trust, GPR5 stabilizes a dedicated diagnostic.

It looks for mistakes such as:

```text
template selected but no authority source
authority without required capability/tool
capability/control without required authority
missing observation channel
case authority confused with review authority
case authority confused with rule-change authority
determination confused with enforcement
reversal confused with remedy
self-review policy conflict
provider/model identity used as authority source
template inheritance would create implicit grant
same-label scope/currentness ambiguity
```

Possible dispositions:

```text
compatible
compatible_with_optional_gaps
blocked_missing_source
blocked_policy_conflict
unresolved_owner_semantics
```

---

# 16. Diagnostic is not a permission engine

The diagnostic can say:

```text
This Judge template asks for case-review responsibility,
but holder currently lacks game.case.review authority.
```

It cannot itself grant the missing authority.

Therefore:

```text
Diagnostic != AuthoritySource.
```

Its role is to make authoring assumptions visible before runtime.

---

# 17. Referee / Judge template family

GPR5 reconstructs:

```text
RefereeJudge
```

as one template family with variants such as:

```text
signal_or_assistant_official
first_instance_case_decider
reviewer_or_head_judge
certifying_official
fused_decide_and_enforce_local_variant
```

Useful responsibility slices:

```text
observe_case
classify_or_recommend
case_decide
case_review
certify
enforce
```

No slice is universally implied by the label.

---

# 18. Assistant referee is a decisive counterexample

An assistant official may:

```text
observe
signal
recommend
```

while having no authority to create the final binding determination.

This immediately falsifies:

```text
Referee label → CaseAuthority.
```

So:

```text
RefereeLabel != CaseAuthority.
```

---

# 19. Head Judge does not require global rank

A floor official might have:

```text
game.case.decide
```

while a head judge has:

```text
game.case.review
```

This does not require:

```text
Head Judge > Floor Judge
```

as one scalar hierarchy.

They hold different operations.

GPR1 already supplies the correct model.

---

# 20. Judge does not imply enforcement

One system can be:

```text
case decision
```

and another:

```text
consequence execution
```

Therefore:

```text
JudgeLabel != EnforcementAuthority.
```

Small games may intentionally fuse them, but that is an explicit composition, not a property of the word Judge.

---

# 21. Game Master template family

GDF3-A already found that “GM” hides a bundle.

GPR5 now reconstructs that bundle operationally.

Variant families can include:

```text
facilitator_only
world_presenter_and_npc_controller
case_adjudicating_gm
rules_steward_gm
experience_director
co_gm_split
```

Possible slices:

```text
facilitate_session
present_or_generate_world
control_npcs_or_world_entities
interpret_rules
case_adjudicate
change_rules
steer_experience
```

---

# 22. GM != Omnipotence

This is the strongest GM guard:

```text
GMLabel != Omnipotence.
```

A GM may lack:

```text
rule-change power
case authority
review authority
world rewrite capability
player control
```

in some systems.

Other systems may explicitly grant many of these.

The template accommodates both without pretending one definition is universal.

---

# 23. World control and case authority remain separate

A GM may control:

```text
NPCs
weather
encounter events
hidden information presentation
```

while rules are executed by a deterministic engine and case decisions are automated.

Thus:

```text
GMWorldControl != CaseAuthority.
```

This is particularly important in Agent-mediated games where an LLM may narrate World content but must not silently alter constitutive rules.

---

# 24. Co-GM becomes easy to model

Instead of one giant GM object:

```text
GM {
  all powers...
}
```

we can split:

```text
GM-A:
  world presentation
  NPC control

GM-B:
  case adjudication
  rules interpretation
```

or any other composition.

Thus:

```text
CoGM != SharedAllAuthority.
```

---

# 25. Coach / Advisor template family

GPR5 reconstructs:

```text
CoachAdvisor
```

as nonbinding by default.

Variants:

```text
spectating_coach
tactical_advisor
strategy_analyst
agent_assistant
delegated_controller_extension
```

Core slices:

```text
observe
analyze
recommend
propose_action
delegated_control optional
```

---

# 26. Coach != Controller

A coach can observe and recommend while having zero action control.

Even when the coach can submit candidate actions:

```text
ProposalRight != ActionControl.
```

If the player later delegates control, then control comes from the explicit delegation/source.

Therefore:

```text
Coach != Controller
Recommendation != Delegation
Advisor != DecisionAuthority.
```

---

# 27. AI advisor becomes straightforward

An Agent can have:

```text
broad observation tools
analysis tools
search/replay tools
recommendation output
```

without any binding authority.

That means Ordivon can safely create very powerful advisory Agents without turning tool access into governance.

Strong:

```text
ToolAccess != Authority.
```

---

# 28. Moderator template family

Moderation is another classic collapsed role.

GPR5 reconstructs variants:

```text
classifier_or_triage
case_moderator
appeal_reviewer
policy_steward
enforcement_operator
fused_small_community_moderator
```

Slices:

```text
classify_or_triage
decide_case
review_case
change_policy
issue_consequence_directive
execute_consequence
coordinate_remedy
```

---

# 29. Moderator != All Governance Authority

A classifier may only label candidate cases.

A case moderator may determine violation status.

A reviewer may hear appeals.

A policy steward may change future rules.

An enforcement operator may apply consequences.

Therefore:

```text
ModeratorLabel != AllGovernanceAuthority.
```

This is exactly the decomposition GPR1-GPR4 were built to support.

---

# 30. Small communities may still fuse moderator slices

The practical framework must not over-govern.

A small private server can intentionally use one Human as:

```text
classifier
case decider
enforcer
```

This is valid when explicit.

A separation policy can warn if a particular practice forbids self-review or requires another holder.

The framework exposes the fusion; it does not universally prohibit it.

---

# 31. Operator template family

GPR5 reconstructs:

```text
Operator
```

as a primarily technical/effectuation family.

Variants:

```text
technical_executor
live_ops_operator
tournament_operator
world_admin
recovery_operator
policy_authorized_operator
```

Slices:

```text
observe_system
execute_authorized_action
verify_effect
maintain_or_recover_service
change_live_configuration
change_policy_or_rules optional
```

---

# 32. Write access != normative authority

An Operator may possess extremely powerful technical tools.

For example:

```text
World mutation API
database access
live configuration write
service restart
```

That does not imply authority to decide:

```text
who should be penalized
what rule should exist
what official status should be recorded
```

Therefore:

```text
WriteCapability != NormativeAuthority.
```

This is one of the most important safety properties of the Operator template.

---

# 33. Technical recovery remains separate from Game remedy

GPR4 already established:

```text
TechnicalRecovery != GameRemedy.
```

So an Operator who:

```text
restores database
recovers service
reconciles dispatch
```

is not thereby a Remedy authority.

Likewise a Remedy authority may authorize compensation while another Operator executes the technical mutation.

---

# 34. Experience Manager template family

This was one of the most ambiguous R0 role bundles.

GPR5 reconstructs it as:

```text
ExperienceManager
```

covering variants such as:

```text
pacing_director
difficulty_adapter
content_curator
encounter_director
session_flow_manager
agent_experience_manager
```

Possible slices:

```text
observe_experience_signals
recommend_adjustment
adjust_pacing_or_content
adjust_difficulty_parameters
spawn_or_schedule_content
change_constitutive_rules optional
```

---

# 35. Experience Manager does not imply omniscience

It may use:

```text
performance metrics
session state
explicit player signals
bounded telemetry
```

without having perfect access to:

```text
player mind
true preference
future enjoyment
```

Therefore:

```text
ExperienceManager != OmniscientPlayerModel.
```

This prevents a high-level UX term from smuggling in a Human-model foundation claim.

---

# 36. Experience steering != adjudication

An experience manager may:

```text
slow encounter pacing
spawn aid
adjust bounded difficulty
change content sequencing
```

without authority to decide:

```text
whether a run is officially valid
whether a player violated a rule
whether a prior ruling should be reversed
```

So:

```text
ExperienceSteering != CaseAuthority.
```

---

# 37. Difficulty adjustment != rule change by identity

A Game may explicitly expose:

```text
enemy health multiplier
spawn pacing
hint rate
resource assistance
```

as adaptive parameters.

Changing one of those does not necessarily modify the constitutive EffectiveRuleTopology in the same sense as changing:

```text
victory condition
legal action set
category definition
```

Therefore:

```text
DifficultyAdjustment != RuleChangeByIdentity.
```

Owner-local semantics decide which parameters are constitutive.

---

# 38. Optimization objective != player value

An Experience Manager might optimize:

```text
session completion
retention
time-on-task
challenge target
safety constraint
```

These metrics do not equal:

```text
PlayerValue
Human welfare
preference
fun
```

by identity.

So:

```text
OptimizationObjective != PlayerValueByIdentity.
```

This keeps experience steering operationally useful without overclaiming what it knows about the player.

---

# 39. Human / Agent substrate remains orthogonal

Every template family can in principle be occupied by:

```text
Human
Agent
policy engine
committee
hybrid system
```

if the concrete GameForm supports it.

Authority still comes from local sources.

Therefore:

```text
HumanSubstrate != AuthorityByIdentity
AgentSubstrate != AuthorityByIdentity
ProviderIdentity != RoleAuthority.
```

---

# 40. Provider substitution should not rewrite role semantics

Suppose an Agent Moderator or GM switches:

```text
Provider A → Provider B
```

while:

```text
same semantic holder
same RoleAssignment
same effective authority
same scope/currentness
```

remain.

Then the role-bundle semantics need not change.

The provider may affect quality/performance, but not semantic authority by identity.

---

# 41. Same model can hold multiple semantic role bundles

One physical model instance can generate outputs for:

```text
Narrator role
Judge role
Advisor role
NPC role
```

if the Harness/runtime separates their semantic principals and contexts.

GPR5 preserves:

```text
SameModel != SameRoleBundleAuthority.
```

This is particularly important in Agent-era Game systems.

---

# 42. Current Station Zero proves local role-template value

The current repository has:

```text
engineer
medic
security
coordinator
```

These labels are already operationally valuable.

They affect:

```text
objective routing
Agent doctrine
context construction
risk preference
responsibility defaults
UI identity
```

So the role-template pattern is not hypothetical.

GPR5 classifies current `ActorRole` as:

```text
LOCAL_SPECIALIST_DOCTRINE_OBJECTIVE_PROFILE
```

---

# 43. But current Engineer/Medic/Security are not generic authority roles

Current profile contains separately:

```text
role
providerOrder
observationPolicyId
authorityPolicyId
riskPreferenceId
```

and the World actor separately has capabilities.

This is already structurally healthy.

The role influences doctrine/objectives/context, but authority is evaluated through an explicit local policy.

Therefore current roles should not be mechanically converted into GPR5 generic role-bundle records.

---

# 44. Coordinator is a local orchestration role

Current `coordinator`:

```text
sees the whole objective graph
owns a coordination task
wraps team execution
```

but that does not mean:

```text
universal commander
GM
global authority root
```

GPR5 classifies it:

```text
LOCAL_ORCHESTRATION_TASK_ROLE
```

This is another example where a local role label is useful precisely because it remains local.

---

# 45. Station Zero `roleId` and `controllerKind` are correctly separate

Current actor state contains both:

```text
roleId
controllerKind
```

and separately:

```text
capabilityIds
traitIds
equipment
faction
```

So:

```text
Engineer
```

and:

```text
Agent-controlled
```

are not the same property.

Classification:

```text
roleId = DIEGETIC_OPERATIONAL_ROLE_LABEL_WITH_SEPARATE_CAPABILITIES
controllerKind = CONTROL_LOCUS_OR_REALIZATION_SUBSTRATE_NOT_ROLE
```

This is directly aligned with GPR5.

---

# 46. Standing Order is another strong anti-hidden-grant example

Current Station Zero tests explicitly establish:

```text
standing orders bind player strategy
without granting direct World mutation
```

This is exactly the principle role bundles need.

A high-level authoring concept can shape:

```text
context
priority
responsibility
policy
```

without automatically becoming low-level action authority.

Thus:

```text
Instruction/Doctrine != DirectWorldAuthority.
```

---

# 47. Player Mission Control is not universally GM/Judge/Operator

Current player-facing controls can:

```text
approve a specific proposal
deny a proposal
redirect objective
pause/resume/cancel Actor task
choose provider
change local authority policy
send message
```

These are concrete Station Zero boundary controls.

They do not imply the universal identity:

```text
Player = GM
Player = Judge
Player = Operator
Player = RuleAuthority
```

GPR5 classifies them:

```text
LOCAL_PLAYER_BOUNDARY_CONTROL_AND_ONE_SHOT_AUTHORITY_WORKFLOWS
```

---

# 48. Casefile demonstrates yet another role meaning

Casefile people have role strings such as:

```text
Archive technician
Lab systems engineer
Dock mechanic
Galley steward
```

These are:

```text
diegetic occupation/presentation labels
```

not authority templates.

Classification:

```text
DIEGETIC_PRESENTATION_OCCUPATION_LABEL
```

This reinforces that the word `role` itself is polysemous at the practical layer.

---

# 49. DeepSeek role doctrine is guidance, not authority

Current Station Zero Agent prompt says roughly:

```text
Engineers prioritize systems...
Medics prioritize wounded people...
Security prioritizes protection...
```

This is useful role doctrine.

But the prompt does not grant:

```text
new legal actions
new World mutation power
new rule authority
```

Classification:

```text
AGENT_CONTEXT_DOCTRINE_HINT_NOT_AUTHORITY_SOURCE
```

This is a good pattern to keep.

---

# 50. Role attribute in current authority policy remains local

Current `AuthorityDecision` evidence includes:

```text
subject.role
capabilities
mandate
```

as attributes.

That is fine.

A local ABAC-style policy may use role as one input.

But GPR5 rejects promoting:

```text
role = engineer
```

into a universal cross-Game authority grant.

Thus:

```text
Role attribute may influence local policy
!= role label is authority source.
```

---

# 51. Current implementation verdict

There are two different conclusions:

```text
PROVEN_LOCAL_ROLE_TEMPLATE_VALUE
```

because Station Zero clearly benefits from role profiles.

But:

```text
currentGenericFrameworkNeed
= NOT_YET_PROVEN
```

because there is not yet a real portfolio of GameForms consuming:

```text
Judge
GM
Moderator
Operator
ExperienceManager
```

through one shared generic system.

So:

```text
broadImplementationNow = false.
```

---

# 52. Why we should not refactor current role enums yet

A generic framework today could easily make current code worse by replacing:

```text
ActorRole = engineer | medic | security | coordinator
```

with a large abstraction whose current consumer does not need it.

The research instead provides a future-compatible interpretation:

```text
current roles = good local templates
```

and a generic contract for later GameForms.

No mechanical migration is implied.

---

# 53. Safe immediate practical candidates

The lowest-risk future consumption is not persistence refactoring.

It is tooling such as:

```text
RoleBundleManifest-like debug projection
```

built from current:

```text
role
capabilities
controller kind
observation policy
authority policy
current authority decision/config
```

for Agent/debug surfaces.

Likewise useful:

```text
role/controller/capability/authority terminology diagnostics
```

without changing existing sources.

---

# 54. Five generic practical contracts

| Contract | Verdict |
| --- | --- |
| RoleBundleTemplateDefinition | **optional authoring preset** |
| RoleBundleInstantiationPlan | **derived authoring plan** |
| RoleBundleManifest | **derived current Human/Agent view** |
| RoleBundleCompositionView | **derived composition view** |
| RoleBundleCompatibilityDiagnostic | **derived authoring audit** |

No new authority primitive is created.

---

# 55. Six reconstructed template families

| Template family | Core practical use |
| --- | --- |
| Referee / Judge | observation, case determination, review, certification, optional effectuation |
| Game Master | facilitation, world presentation/control, interpretation, adjudication, rules stewardship, experience steering |
| Coach / Advisor | observation, analysis, recommendation, proposal, optional delegated control |
| Moderator | classification, determination, review, policy, consequence, remedy coordination |
| Operator | technical observation, execution, verification, configuration, recovery |
| Experience Manager | pacing, difficulty/content adaptation, encounter/session steering |

Each is a template family, not one fixed responsibility definition.

---

# 56. Strong cross-cutting law set

```text
RoleBundleTemplate != RoleAssignment
RoleBundleTemplate != AuthorityGrant
RoleBundleTemplate != CapabilityGrant
RoleBundleTemplate != ControlGrant

RoleLabel != ResponsibilityTopology
TemplateSelection != EffectiveAuthority
TemplateComposition != AuthorityUnion
TemplateInheritance != ImplicitGrant

SameHolder != SameAuthorityOperation
SameModel != SameRoleBundleAuthority
ProviderIdentity != RoleAuthority
HumanSubstrate != AuthorityByIdentity
AgentSubstrate != AuthorityByIdentity

ObservationAccess != Control
Control != BindingAuthority
Recommendation != DecisionAuthority

CaseAuthority != ReviewAuthority
CaseAuthority != RuleChangeAuthority
DeterminationAuthority != EnforcementAuthority
ReviewAuthority != RemedyAuthority

WriteCapability != NormativeAuthority
ToolAccess != Authority

GMLabel != Omnipotence
ModeratorLabel != AllGovernanceAuthority
OperatorLabel != GlobalAdminAuthority
CoachLabel != ControllerAuthority
ExperienceManagerLabel != UnboundedAdaptiveAuthority
RefereeLabel != UniversalFinalAuthority

SameDisplayLabelCanMapToDifferentLocalBundles
DifferentDisplayLabelsCanMapToEquivalentOperationalBundles

RoleBundleManifest != SourceOfTruth
StaleRoleBundleManifest != CurrentAuthorityEvidence
```

---

# 57. Stress-test result

GPR5 covers 70 cases across:

```text
assistant/floor/head/automated officials
broad/narrow/co-GM forms
spectating/advisory/delegated coaches
moderation classification/decision/review/policy/enforcement/remedy
technical/live/tournament/recovery operators
pacing/difficulty/content experience managers
same-label/different-Game semantics
different-label/equivalent semantics
localization
temporary/replacement assignments
scope differences
stale manifests
capability/authority/access mismatches
separation conflicts
unassigned/shared responsibilities
Station Zero specialist/coordinator/controller/player/order cases
Casefile diegetic occupations
provider substitution
```

All probes pass.

No FoundationReopenCondition is triggered.

---

# 58. GPR1-GPR5 now form a practical composition ladder

The programme has moved from raw semantic distinctions toward usable authoring language:

```text
GPR1
Role / Authority primitives and projections
        ↓
GPR2
Determination / Contestability
        ↓
GPR3
Evidence / Norm / Explanation
        ↓
GPR4
Enforcement / Remedy
        ↓
GPR5
Role Bundle Templates
```

GPR5 is the first layer that deliberately packages the previous layers into familiar design vocabulary.

This is precisely what practical reconstruction was supposed to achieve.

---

# 59. The deeper pattern

Foundation research removed false equations such as:

```text
Judge = authority
GM = omnipotence
Moderator = governance
Operator = admin power
Coach = control
```

Practical reconstruction does not discard the words.

Instead it gives them a safer form:

```text
friendly role label
+
explicit responsibility slices
+
source-backed manifest
+
compatibility diagnostic
```

So the user gets simplicity at the top without semantic shortcuts underneath.

---

# 60. Final result

The strongest GPR5 formula is:

```text
Role Bundle
=
Ergonomic Macro
not Semantic Grant
```

or more fully:

```text
RoleBundleTemplate
→ authoring expectations

RoleAssignment + access + capability + control + authority sources
→ actual semantics

RoleBundleManifest
→ usable current projection
```

This is compatible with Human-only, Agent-only and mixed GameForms.

---

# 61. Next practical reconstruction round

R0 P6 remains, but part of it has already been consumed elsewhere.

Do **not** redo:

```text
FinalityStatusView
```

because GPR2 already reconstructed it.

The next exact round is:

```text
GPR6 — Participation / Human-Agent Vocabulary Views
```

Primary targets:

```text
ParticipantView
SpectatorView
AudienceView
Human/Agent/substrate display vocabulary
Rule/Standard user-facing labels
```

The key question will be:

> How can we recover familiar words such as participant, spectator, audience, human-controlled, Agent-controlled, rule and standard as practical query/UI vocabulary without rebuilding scalar participation hierarchies, substrate-based authority, or a universal Rule-vs-Standard ontology?
