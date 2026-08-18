---
schema_version: 1
id: game.practical-concept-reconstruction.gpr6
title: Ordivon Game — GPR6 Participation / Human-Agent Vocabulary Views
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Completes the six R0 practical reconstruction priority clusters by rebuilding Participant, Spectator, Audience, Human/Agent/controller and Rule/Standard vocabulary entirely as derived scope-qualified views and descriptive labels over frozen Game semantics. Stabilizes ParticipantView, SpectatorView, AudienceView, ControlRealizationView, NormVocabularyView and VocabularyCompatibilityDiagnostic. Finds no new canonical source or foundation responsibility. Current Station Zero controllerKind is retained as useful local shorthand but rejected as generic ontology because it mixes Player/control-principal and Agent/policy realization dimensions; single-player remains compatible with many Agent/policy-controlled actors. Rule/Standard remain authoring language over EffectiveRuleTopology and NormApplicationView, not universal schema kinds. Seventy-two stress cases, forty-six executable probes and forty-nine audit checks pass. GPR1-GPR6 planned clusters are complete; NextGPR is UNKNOWN pending practical-reconstruction closeout/residual coverage search.
evidence_status: strong
readiness: GPR6_COMPLETE
applies_to:
  - ordivon-game
related:
  - game.practical-concept-reconstruction.gpr1
  - game.practical-concept-reconstruction.gpr2
  - game.practical-concept-reconstruction.gpr3
  - game.practical-concept-reconstruction.gpr4
  - game.practical-concept-reconstruction.gpr5
---
# Ordivon Game — GPR6 Participation / Human-Agent Vocabulary Views

## 0. Scope

GPR6 reconstructs the final R0 P6 family:

```text
Participant
Spectator
Audience
Human / Agent / Policy / controller vocabulary
Rule / Standard labels
```

One R0 P6 concept is deliberately not revisited:

```text
FinalityStatusView
```

because GPR2 already reconstructed and stabilized it.

The GPR6 question is:

> How can Ordivon expose natural Human/Agent-facing words for participation, spectatorship, audience, control realization and norm language without recreating the exact primitive/category collapses that GDF0/GDF3 falsified?

GDF0-GDF3 remain frozen.

---

# 1. Main result

GPR6 finds **zero new canonical sources**.

Every recovered concept survives as:

```text
derived view
query projection
descriptive label
UI/authoring vocabulary
terminology diagnostic
```

The final architecture is:

```text
Entity / RoleAssignment / Player
GPR1 causal access + authority
GDF1 control contribution
GameForm / PlayPractice / event scope
World / Media observation
controller/delegation/provenance
GDF0 EffectiveRuleTopology
GPR3 NormApplicationView
        │
        ├── ParticipantView
        ├── SpectatorView
        ├── AudienceView
        ├── ControlRealizationView
        ├── NormVocabularyView
        └── VocabularyCompatibilityDiagnostic
```

No new:

```text
Participant table
Audience Subject
Controller ontology
Rule/Standard primitive
```

is justified.

---

# 2. Participant comes back as a query, not an entity kind

GDF3-A rejected:

```text
entity.isParticipant = true
```

because the same entity may be:

```text
participant in tournament
not participant in current match
participant in community
not participant in gameplay enactment
```

GPR6 reconstructs the useful positive form:

```text
ParticipantView(entity, scope, currentness)
```

Therefore:

```text
Participant != EntityKind
ParticipantIsScopeQualified.
```

---

# 3. ParticipantView

GPR6 stabilizes:

```text
ParticipantView
```

as a derived, scope-qualified view.

Inputs:

```text
entityOrHolderRef
participationScopeRef
contextRef
asOfCurrentness
requested descriptors optional
```

Possible output:

```text
scope
applicable descriptor labels
RoleAssignments
observation channels
communication/influence channels
proposal/contribution channels
control contribution
direct GameAction control
evaluation/performance relations
binding authority
practice membership/registration
source refs
participationViewDigest
```

---

# 4. There is no universal `isParticipant`

A UI may safely display:

```text
Participants in this match
Tournament participants
Observed participants
Active gameplay participants
```

because the query names the scope.

Unsafe:

```text
Participant: true
```

when downstream code assumes that means:

```text
Player
GameAction controller
subject
judge
community member
```

all at once.

---

# 5. Participation is multidimensional

GDF3 used exploratory channels such as:

```text
Observe
Advise
Propose
Execute
Evaluate
Adjudicate
Verify
Enforce
ModifyContent
ModifyRules
AdaptGame
```

GPR6 keeps the lesson but **does not freeze this list**.

The practical rule is:

```text
participation channel families remain open / namespaced / owner-local
```

because future GameForms may expose channels not in the current list.

---

# 6. Participant is not a scalar ladder

Reject:

```text
nonparticipant
→ spectator
→ active participant
→ player
→ powerful participant
```

A referee may have major case authority and no Player action control.

A coach may strongly change Player policy and no binding authority.

A viewer may cause aggregate Game parameter changes without becoming Player.

Thus:

```text
no universal participation scalar
```

is required.

---

# 7. Player remains independent

R29 remains intact:

```text
Player = system-boundary role
```

A Player may:

```text
control one Subject
control many Subjects
edit World
make meta-decisions
observe without diegetic embodiment
```

ParticipantView does not replace Player.

Strong:

```text
Player != ParticipantByUniversalIdentity.
```

---

# 8. Causal components are not participants by identity

A physics engine changes play.

RNG changes outcomes.

A scheduler changes event ordering.

A damage resolver changes state.

Calling all of these:

```text
Participants
```

would destroy the word's practical value.

Therefore:

```text
CausalGameComponent != ParticipantByIdentity.
```

Participation remains a scoped practice/role/relation description, not causation alone.

---

# 9. Spectator comes back as an observation-centered view

`Spectator` is an excellent Human mental model.

GPR6 stabilizes:

```text
SpectatorView
```

as a derived observational-role view.

The required starting relation is:

```text
observation of a Game event/practice
```

but observation is not an exhaustive role description.

---

# 10. SpectatorView

Possible output:

```text
observation channels
visibility/latency
expression/chat channels
report/advice channels
aggregate contribution channels
direct control channels
binding authority
stake/affiliation
presentation labels
source refs
spectatorViewDigest
```

Possible lossy labels:

```text
passive_spectator
expressive_spectator
reporting_or_advisory_spectator
causal_audience_contributor
spectator_with_other_role
```

These are presentation labels, not ontology.

---

# 11. Spectator != causal nonparticipant

Paired case:

```text
T0:
viewer watches

T1:
same viewer's vote
enters aggregation
changes AI strength
```

The entity remains the same.

The channel changes.

Therefore:

```text
Spectator != CausalNonparticipantByIdentity.
```

This is one of the strongest GDF3 findings now made practical.

---

# 12. Expression is not control

A spectator may:

```text
chat
cheer
report
comment
```

without having control authority.

Therefore:

```text
Expression != ControlByIdentity
ReportOrAdvice != AuthorityByIdentity.
```

The view should expose both rather than compress them into “interactive spectator”.

---

# 13. Spectator and Player can coexist

A streamer may simultaneously:

```text
be Player
observe another player's feed
broadcast
read chat
```

There is no contradiction.

These are scoped relations and roles.

So GPR6 does not define:

```text
Spectator XOR Player.
```

---

# 14. Audience comes back as collection + aggregation

`Audience` is useful, but GDF3 rejected:

```text
Audience = one giant Subject.
```

GPR6 reconstructs:

```text
AudienceView
```

as a derived collection/aggregation view.

---

# 15. AudienceView

Possible output:

```text
audience scope kind
member refs or cohort descriptor
observation channel summary
member contribution channels
aggregation mechanisms
aggregate outputs
aggregate control contribution
collective authority only if independently established
heterogeneity/conflict
source refs
audienceViewDigest
```

Useful Game-side scope kinds:

```text
game_session_or_event
broadcast_or_stream
play_practice_or_community
owner_local_custom
```

---

# 16. Audience != CollectiveSubject

Many viewers may contribute:

```text
vote A
vote B
vote B
vote C
```

An aggregation rule produces:

```text
B
```

This does not establish one collective:

```text
belief
memory
desire
policy
identity
```

Therefore:

```text
Audience != CollectiveSubjectByIdentity
AggregateContribution != CollectiveMind.
```

---

# 17. Audience != CollectiveAuthority

Likewise, an audience vote causing a parameter change does not automatically mean the audience possesses:

```text
rule authority
case authority
control authority
```

If a GamePractice explicitly says:

```text
majority audience vote changes Rule X
```

then authority may exist through the explicit current aggregation/authority semantics.

But:

```text
Audience label alone
```

does not supply it.

---

# 18. Aggregate control does not become member-level control

Suppose ten thousand viewers vote and one aggregate output controls an AI parameter.

It can be correct to say:

```text
Audience aggregate contributes to control.
```

It is not necessarily correct to say:

```text
Every viewer controls the AI directly.
```

Therefore:

```text
AggregateControlContribution
!= MemberLevelControlByIdentity.
```

GDF1 ControlContributionTopology remains the proper lower substrate.

---

# 19. Audience heterogeneity must remain visible

A dangerous compression is:

```text
The audience wants X.
```

when the actual distribution is:

```text
45% X
40% Y
15% Z
```

AudienceView should retain:

```text
heterogeneity
conflict
aggregation mechanism
```

when materially relevant.

No collective preference is inferred merely because a UI needs one aggregate result.

---

# 20. “Audience” is itself polysemous

The current repo exposes at least three different uses of the word:

```text
live Game/broadcast audience
product target audience
document audience/readership
```

GPR6 explicitly separates them.

---

# 21. Product target audience is not Game audience

A product research statement such as:

```text
target audience = tactical strategy players
```

belongs to:

```text
Product / Market / user-research scope
```

not the live Game audience relation.

Classification:

```text
PRODUCT_USER_COHORT_NOT_LIVE_GAME_AUDIENCE
```

This prevents a surprisingly easy metadata collision.

---

# 22. Documentation `audience:` is not Game audience

Many current docs contain frontmatter like:

```text
audience:
  - player
  - agent
  - developer
```

That means:

```text
intended document readership
```

not:

```text
these entities are spectators of a GameInstance.
```

Classification:

```text
DOCUMENT_READERSHIP_METADATA_NOT_GAME_AUDIENCE
```

Strong:

```text
DocumentAudience != GameAudienceByIdentity.
```

---

# 23. Human / Agent vocabulary needs a different reconstruction

The practical problem is not only participation.

Current Game and future Agent systems naturally need labels such as:

```text
Human-controlled
Agent-controlled
Policy-controlled
Hybrid control
Player-controlled
```

These are useful, but they currently risk mixing:

```text
semantic principal
Player boundary
control locus
realization substrate
model/provider
cognition mechanism
authority
```

GPR6 therefore reconstructs a dedicated view.

---

# 24. ControlRealizationView

GPR6 stabilizes:

```text
ControlRealizationView
```

as a derived principal/substrate view.

Inputs:

```text
controlled target or role
context
currentness
```

Output:

```text
semantic control principals
Player-boundary / role refs
control locus
action/control channels
realization substrate labels
controller/policy refs
provider/model refs
delegation refs
direct vs supervisory control
authority summary
source refs
controlRealizationDigest
```

---

# 25. Control principal != realization substrate

This is the central control-vocabulary distinction.

Example:

```text
Control principal:
  Player / Mission Control

Local realization:
  Agent specialist
```

The Player retains strategic supervisory control while an Agent realizes local actions.

Therefore:

```text
ControlPrincipal != RealizationSubstrate.
```

---

# 26. Useful realization labels

A practical UI can safely expose labels such as:

```text
human_realized
model_agent_realized
deterministic_policy_realized
script_or_fsm_realized
planner_or_search_realized
hybrid_realized
uncontrolled_or_none
unknown_or_owner_local
```

These describe implementation/control realization.

They do **not** define authority or Player identity.

---

# 27. Player != Human

A synthetic benchmark Agent can occupy the Player role.

Multiple Humans can share one Player role.

One Human can occupy several Player roles in a hot-seat setting.

Therefore:

```text
Player != HumanByIdentity.
```

`Human player` remains a useful ordinary phrase, but the terms are not interchangeable in the semantic model.

---

# 28. Player != Agent either

Likewise an Agent can:

```text
play the Player side
control an opponent
act as a companion
serve as a pacing director
work only in production
```

So:

```text
Agent != PlayerByIdentity.
```

Agent is a technology/substrate/locus description that still needs a semantic role.

---

# 29. Agent-controlled opponent does not create another Player

This is directly demonstrated by current Station Zero.

The product is:

```text
single-player
```

while:

```text
Pirate faction = Agent controlled
Swarm faction = Agent controlled
multiple actors = Agent or policy controlled
```

There is no contradiction.

Strong practical law:

```text
AgentControlledOpponent != AdditionalPlayerByIdentity
PlayerCount != CausallyActiveEntityCount.
```

---

# 30. Current Station Zero `controllerKind` mixes dimensions

Current:

```text
player | agent | policy | none
```

is an effective local product enum.

But generically it mixes:

```text
player
→ semantic control principal / boundary locus

agent / policy
→ realization/cognition substrate
```

So GPR6 classifies it:

```text
LOCAL_MIXED_CONTROL_PRINCIPAL_AND_REALIZATION_SHORTHAND
```

Keep it local.

Do not promote it to universal Game ontology.

---

# 31. This is not a request to refactor Station Zero

The local enum is compact, readable and currently correct enough because Station Zero's GameForm has known constraints.

Replacing it now with a generic multi-dimensional framework would likely add complexity without a concrete consumer.

Therefore:

```text
current local shorthand = KEEP
cross-Game semantic generalization = REJECT
```

This continues the practical-reconstruction discipline.

---

# 32. AgentDecision vs PolicyDecision is provenance, not role ontology

Station Zero separately retains:

```text
AgentDecision
PolicyDecision
```

and `controllerKind`.

This usefully tells us how decisions were generated.

Classification:

```text
LOCAL_CONTROL_REALIZATION_AND_COGNITION_PROVENANCE
```

It does not answer by itself:

```text
is this a Player?
is this a Participant?
does it have authority?
```

---

# 33. Provider identity is even lower-level

A model Agent may switch:

```text
Provider A
→ Provider B
```

while the semantic controller/principal remains the same.

Therefore:

```text
ProviderIdentity != ControlPrincipal.
```

This matches GPR1/GPR5 provider-authority separation.

---

# 34. Hybrid control becomes representable without a new role

A system can use:

```text
Human strategic intent
+ deterministic policy routine control
+ Agent ambiguous-case reasoning
```

for one semantic role.

ControlRealizationView can expose:

```text
principal
channels
delegation
multiple realization substrates
```

without inventing:

```text
HybridPlayer primitive.
```

---

# 35. Production Agent != runtime participant

The Pre-G0 Agent role atlas already separated:

```text
Production Agents
Runtime Game-System Intelligence
World / Subject Agents
```

This distinction remains essential.

A coding Agent that builds the level is not thereby a participant in the shipped GameInstance.

Strong:

```text
ProductionAgent != RuntimeGameParticipantByIdentity.
```

---

# 36. Runtime system intelligence != World Subject

A pacing director or semantic parser may materially affect play.

That does not make it:

```text
NPC
Player
World Subject
```

Therefore:

```text
RuntimeSystemIntelligence != WorldSubjectByIdentity.
```

Again the Agent label is not enough.

---

# 37. Current `require-human` remains local policy vocabulary

Station Zero may return:

```text
require-human
```

for a high-risk proposal.

This is a valid local authority policy outcome.

But it must not become:

```text
Humans always outrank Agents.
```

GPR6 classifies it:

```text
LOCAL_POLICY_ESCALATION_VOCABULARY
```

Strong:

```text
HumanEscalationLabel != UniversalHumanAuthority.
```

---

# 38. `committedBy: player:` / `agent:` is provenance vocabulary

Current records use namespaced audit strings such as:

```text
player:mission-control
agent:pirate-captain:provider
```

These are useful.

But they are:

```text
LOCAL_PROVENANCE_LABELS_NOT_SEMANTIC_ROLE_ONTOLOGY
```

A provenance namespace should not become a universal authority inference rule.

---

# 39. Rule / Standard comes back as ordinary language

GDF3-D falsified:

```text
Rule = closed
Standard = open/discretionary
```

as a universal binary.

But both words are extremely useful to Humans.

GPR6 therefore reconstructs:

```text
NormVocabularyView
```

rather than a `RuleOrStandard` primitive.

---

# 40. NormVocabularyView

Possible output:

```text
display labels
owner-local label definitions
representation refs
EffectiveRuleTopology effects
predicate closure
context sensitivity
measurement burden
exceptions/defeaters
residual discretion
authority/currentness
NormApplication refs
source refs
normVocabularyDigest
```

Common descriptive labels:

```text
rule
standard
guideline
policy
criterion
procedure
convention
condition
owner_local_custom
```

---

# 41. Properties matter more than the Rule/Standard label

Suppose two norms are both called `Rule`.

One can be:

```text
exact threshold
fully executable
no discretion
```

another:

```text
contains “unreasonable delay”
requires contextual judgment
```

The useful semantic difference is in:

```text
closure
context sensitivity
measurement
exception structure
residual discretion
```

not the English noun.

---

# 42. Rule can be open-textured

A detailed formal Rule may contain:

```text
reasonable
excessive
unsporting
substantial
appropriate
```

Therefore:

```text
RuleLabel != ClosedPredicateByIdentity.
```

The label is descriptive.

Application properties remain explicit.

---

# 43. Standard can be precise

Conversely, a locally named Standard may be operationalized as:

```text
value >= 90
```

with no residual discretion in the current case.

Therefore:

```text
StandardLabel != DiscretionByIdentity.
```

This alone kills a universal schema binary.

---

# 44. Local Rule-vs-Standard schemas are still allowed

GPR6 is not banning local enums.

A GameForm can explicitly define:

```text
kind = rule | standard
```

if it owns precise local meanings and downstream behavior.

The restriction is only:

```text
do not universalize that local distinction across all GamePractices.
```

So:

```text
local distinction = allowed
universal semantic primitive = rejected
```

---

# 45. `Policy` is especially polysemous

Current repo uses policy for:

```text
authority policy
observation policy
coordination policy
risk preference
loot policy
retreat behavior
deterministic behavior policy
```

These do not all have the same relationship to Game constitution.

Classification:

```text
HETEROGENEOUS_LOCAL_POLICY_VOCABULARY
```

Therefore:

```text
PolicyLabel != NonConstitutiveByIdentity.
```

---

# 46. Some policies can be constitutive

If a current authority policy materially determines which actions can be admitted under the current GamePractice, it may participate in effective Game semantics.

Another `policy` may merely guide Agent preference among already legal actions.

Same English word.

Different semantic role.

Thus the label cannot answer constitutive status.

---

# 47. Convention follows the same rule

GPR3 already reconstructed `ConventionStatusView`.

GPR6 therefore allows a `convention` label, but preserves:

```text
ConventionLabel != ConstitutiveAuthorityByIdentity.
```

A convention is constitutive only when current recognition/authority makes it operative in EffectiveRuleTopology.

---

# 48. RuleRepresentation remains distinct from rule force

Current Station Zero has exact:

```text
rulesetId
rulesetVersion
```

These are valuable sources.

GPR6 classifies them:

```text
EXACT_RULE_REPRESENTATION_AND_VERSION_SOURCE
```

But:

```text
RuleRepresentation != RuleAuthority
RuleRepresentation != ApplicableNormBasis.
```

The complete current norm view may include local overlays, policies, interpretation or practice semantics.

---

# 49. Current v3/v4 paths reinforce scope/currentness discipline

The repo contains current references to:

```text
station-zero-core v3
station-zero-core v4
```

across different product/compatibility paths.

Therefore a UI saying only:

```text
Rules: station-zero-core
```

may be insufficient.

NormVocabularyView should retain:

```text
owner
scope
version
currentness
```

when correctness matters.

---

# 50. Stable text still does not mean stable effective rules

Frozen law remains:

```text
StableRuleRepresentation
!= StableEffectiveRuleTopology.
```

An authoritative interpretation can change current Game semantics while bytes remain unchanged.

An editorial rewrite can change bytes while effective semantics remain stable.

GPR6 user vocabulary cannot erase this distinction.

---

# 51. Generated rule text remains explanation/proposal

If an Agent says:

```text
“The rule means X.”
```

that can be:

```text
helpful explanation
candidate interpretation
proposed wording
```

but not automatically:

```text
current authoritative rule truth.
```

GPR3/GDF0 authority still controls adoption.

---

# 52. Finality is explicitly not duplicated

R0 P6 also contained `Finality`.

But GPR2 already stabilized:

```text
FinalityStatusView
```

with states such as:

```text
current_and_contestable
current_and_closed_within_queried_scope
superseded_or_historical
unresolved_or_conflicted
```

Therefore GPR6 records:

```text
FINALITY = ALREADY_COMPLETED_IN_GPR2_NOT_REDONE
```

This is deliberate anti-duplication.

---

# 53. VocabularyCompatibilityDiagnostic

Friendly vocabulary is useful precisely because it is lossy.

So GPR6 stabilizes a diagnostic for cases where lossiness becomes dangerous.

Checks include:

```text
participant boolean without scope
participation scalar assumption
spectator assumed passive
Audience treated as one Subject
Audience aggregate treated as authority
product audience confused with live audience
document audience confused with Game audience
Player assumed Human
Agent assumed Player
Agent count used as Player count
control principal confused with substrate
provider identity used as control/authority
production Agent treated as runtime participant
system intelligence treated as World Subject
require-human generalized into Human superiority
Rule/Standard label used as universal schema
Policy label used to infer nonconstitutive status
ruleset representation treated as whole EffectiveRuleTopology
stale vocabulary view used as current source
```

---

# 54. Lossy vocabulary is allowed

The goal is not to force every player UI to display the full semantic graph.

A UI can simply say:

```text
Spectator
Agent-controlled
Rule
Final
```

when that is good product language.

The requirement is:

```text
correctness-critical tooling retains drill-down
and does not infer hidden semantics from the label alone.
```

This is the same design pattern seen in GPR1-GPR5.

---

# 55. Player-facing labels and semantic sources can deliberately differ

Example:

```text
UI:
Agent-controlled
```

Drill-down:

```text
control principal = pirate faction
world role = Captain Veyra
realization = model Agent
provider = DeepSeek X
binding authority = local actor action authority
```

The friendly label is not wrong because it is compressed.

It becomes wrong only if downstream code treats it as the complete semantic source.

---

# 56. Current `playerVisible` replay fields are not participation claims

Replay currently marks some evidence as:

```text
player-visible
```

This is a presentation/knowledge projection.

Classification:

```text
PRESENTATION_VISIBILITY_NOT_PARTICIPATION_ROLE
```

A thing being visible to Player does not make it a Participant.

A Participant need not be visible to Player.

---

# 57. Six final GPR6 contracts

| Contract | Verdict |
| --- | --- |
| ParticipantView | **derived scope-qualified participation view** |
| SpectatorView | **derived observation-centered role view** |
| AudienceView | **derived collection/aggregation view** |
| ControlRealizationView | **derived control-principal/substrate view** |
| NormVocabularyView | **derived authoring/UI vocabulary view** |
| VocabularyCompatibilityDiagnostic | **derived terminology audit** |

Again:

```text
0 new canonical sources
0 new primitives
```

---

# 58. Current engineering audit summary

## StationZeroControllerKind

```text
LOCAL_MIXED_CONTROL_PRINCIPAL_AND_REALIZATION_SHORTHAND
```

Keep local; do not generalize.

## Station Zero single-player label

```text
CONVENTIONAL_PLAYER_BOUNDARY_FORM_LABEL
```

Compatible with many Agent/policy-controlled actors.

## AgentDecision / PolicyDecision

```text
LOCAL_CONTROL_REALIZATION_AND_COGNITION_PROVENANCE
```

Not Player/authority ontology.

## require-human

```text
LOCAL_POLICY_ESCALATION_VOCABULARY
```

Not universal Human supremacy.

## committedBy player:/agent:

```text
LOCAL_PROVENANCE_LABELS_NOT_SEMANTIC_ROLE_ONTOLOGY
```

## Pre-G0 Agent role atlas

```text
STRONG_AGENT_LOCUS_DISAMBIGUATION
```

Production/system/world Agent loci remain distinct.

## docs audience frontmatter

```text
DOCUMENT_READERSHIP_METADATA_NOT_GAME_AUDIENCE
```

## product target audience

```text
PRODUCT_USER_COHORT_NOT_LIVE_GAME_AUDIENCE
```

## ruleset id/version

```text
EXACT_RULE_REPRESENTATION_AND_VERSION_SOURCE
```

not complete EffectiveRuleTopology.

## Team policies

```text
HETEROGENEOUS_LOCAL_POLICY_VOCABULARY
```

## player-visible replay flag

```text
PRESENTATION_VISIBILITY_NOT_PARTICIPATION_ROLE
```

---

# 59. Strong GPR6 practical laws

```text
Participant != EntityKind
ParticipantIsScopeQualified
Player != ParticipantByUniversalIdentity

Spectator != CausalNonparticipantByIdentity
Audience != CollectiveSubjectByIdentity
Audience != CollectiveAuthorityByIdentity
AggregateContribution != CollectiveMind

Observation != Control
InfluenceOnPolicy != ControlOfGameActionByIdentity
Contribution != BindingAuthority
CausalGameComponent != ParticipantByIdentity

Player != HumanByIdentity
Player != AgentByIdentity
Agent != PlayerByIdentity
AgentControlledOpponent != AdditionalPlayerByIdentity
PlayerCount != CausallyActiveEntityCount

ControlPrincipal != RealizationSubstrate
ControllerSubstrate != BindingAuthority
ProviderIdentity != ControlPrincipal

ProductionAgent != RuntimeGameParticipantByIdentity
RuntimeSystemIntelligence != WorldSubjectByIdentity
HumanEscalationLabel != UniversalHumanAuthority

RuleVsStandard != UniversalSemanticBinary
RuleLabel != ClosedPredicateByIdentity
StandardLabel != DiscretionByIdentity
PolicyLabel != NonConstitutiveByIdentity
ConventionLabel != ConstitutiveAuthorityByIdentity

RuleRepresentation != RuleAuthority
RuleRepresentation != ApplicableNormBasis
StableRuleRepresentation != StableEffectiveRuleTopology

DisplayLabel != SemanticSourceOfTruth
DocumentAudience != GameAudienceByIdentity
ProductTargetAudience != LiveGameAudienceByIdentity
```

---

# 60. Implementation conclusion

Current practical value is already proven for:

```text
control-realization labels
Human/Agent terminology disambiguation
Player/product labeling
rule/policy/version presentation
```

So:

```text
currentViewValue
= PROVEN_FOR_CONTROL_REALIZATION_AND_TERMINOLOGY_DISAMBIGUATION
```

But Station Zero has no actual live:

```text
spectator system
audience aggregation
audience-control participation
```

consumer.

Therefore:

```text
currentGenericParticipationConsumerNeed
= NOT_PROVEN
broadImplementationNow = false
```

---

# 61. Safe future engineering candidates

If later useful, low-risk consumption includes:

```text
ControlRealizationView
```

for Agent/debug surfaces;

```text
VocabularyCompatibilityDiagnostic
```

as lint/audit rules;

```text
NormVocabularyView
```

for Human/Agent explanation over exact rule/policy/version sources.

But do not add persistence for Participant/Spectator/Audience until a real GameForm needs those relations.

---

# 62. R0 → GPR6 completion status

The entire planned priority sequence is now complete:

```text
GPR1 — P1 Role & Authority
GPR2 — P2 Case Determination & Contestability
GPR3 — P3 Evidence / Norm / Explanation
GPR4 — P4 Enforcement / Remedy
GPR5 — P5 Role Bundle Templates
GPR6 — P6 Human/Agent Vocabulary Views
```

And:

```text
FinalityStatusView
```

was correctly absorbed into GPR2 rather than duplicated here.

---

# 63. What practical reconstruction achieved

The starting fear was that foundations-first deletion would leave Game with only low-level semantic atoms.

The result is the opposite.

We now have a consistent pattern:

```text
false primitive
↓
foundation deletion
↓
derived operational reconstruction
↓
human/Agent-friendly vocabulary
```

Examples:

```text
Participant
→ scope-qualified view

Judge / GM
→ role-bundle template

Evidence
→ case-relative bundle/view

Precedent
→ current-use relation

Enforcement
→ directive + attempt + realized-effect view

Remedy
→ forward corrective workflow

Rule / Standard
→ descriptive norm vocabulary
```

---

# 64. The practical architecture is now layered

A useful summary is:

```text
FROZEN SEMANTIC SUBSTRATE
F1–F9 + GDF0–GDF3
        ↓

SOURCE-BACKED OPERATIONAL LAYER
RoleAssignment
local authority/control/provenance
Determination
Directive/attempt when needed
        ↓

DERIVED PRACTICAL TOOLKIT
AuthorityProfile
Case status
Evidence / Norm views
Enforcement / Remedy status
Participation / Control realization
        ↓

ERGONOMIC DESIGN LANGUAGE
Judge
GM
Coach
Moderator
Operator
Participant
Spectator
Audience
Agent-controlled
Rule
Standard
Final
```

The top layer can now be rich without making the bottom layer sloppy.

---

# 65. A general reconstruction law emerges

The strongest whole-programme result is:

```text
Useful Concept
!= Primitive Concept
```

and more specifically:

```text
Foundation falsification
should usually determine
HOW a useful concept returns,
not WHETHER Humans may keep using the word.
```

This is a major practical benefit of the deep-foundations work.

---

# 66. Why no GPR7 is admitted now

GPR0 selected six priority clusters.

All six are now complete.

It would be methodologically wrong to take an old residual word and simply declare:

```text
GPR7 = next familiar concept
```

without reassessing the whole practical space.

So GPR6 freezes:

```text
NextGPR = UNKNOWN
```

---

# 67. Exact next route

The next route is not a numbered concept round yet.

It is:

```text
Practical Reconstruction Closeout / Residual Coverage Search
```

The next review should compare:

```text
all 37 R0 concepts
GPR1–GPR6 contracts
concepts absorbed into earlier rounds
concepts intentionally left local
current real consumers
still-missing ergonomic concepts
new gaps exposed by reconstruction itself
```

and classify residuals as:

```text
already reconstructed
absorbed
local-only
owned elsewhere
not useful enough
implementation-consumption concern
genuinely missing practical concept cluster
```

Only the last category can justify a future GPR7.

---

# 68. Final GPR6 result

GPR6 confirms that the practical vocabulary layer can remain natural and rich:

```text
Participants
Spectators
Audience
Human-controlled
Agent-controlled
Rules
Standards
Policies
```

without making any of those words a new foundation.

The final design principle is:

```text
Human-friendly labels at the surface
source-backed distinctions underneath
scope/currentness on every correctness-critical drill-down
```

That completes the originally selected GPR1–GPR6 reconstruction programme.
