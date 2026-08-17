---
schema_version: 1
id: game.deep-foundations.gdf3-b
title: Ordivon Game Deep Foundations — GDF3-B Participation Topology / Authority Decomposition
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Continues residual-selected GDF3 after GDF3-A. Attacks ParticipationAuthorityTopology as a candidate independent responsibility by reconstructing delegation, recommendation, aggregation, appeal, replacement, multiple final authorities, post-hoc verification, adaptive game management and Agent role fusion through existing Role/Relation/Time/Authority/Provenance plus GDF1 action/contribution semantics. Rejects global authority rank/tree, delegation/aggregation/role-conflict primitives and ParticipationAuthorityTopology as independent foundation. Retains only scope/time/operation-bound authority relations as a derived domain projection and narrows the surviving residual to Adjudication / Interpretation / Review / Contestability. No upstream foundation reopen is triggered.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf3-a
  - game.play-game-deep-foundations.v1
  - game.action-control-skill-foundations.v1
  - game.challenge-failure-mastery-foundations.v1
  - game.foundations-research.r24
  - game.foundations-research.r29
---
# Ordivon Game Deep Foundations — GDF3-B

## 0. B asks whether A's strongest candidate can be deleted

GDF3-A ended with a deliberately provisional object:

```text
ParticipationAuthorityTopology
```

roughly meaning:

```text
who/what occupies which Game-relative role
+ what it can observe / propose / act / evaluate / adjudicate / change
+ which outputs are merely contributory and which are binding
+ how authority aggregates / delegates / reviews / conflicts
```

That description is useful.

But usefulness does not establish foundation independence.

B therefore asks:

> Can every materially important GDF3-A counterfactual be represented cleanly using the already-frozen substrate—R24 Role, F3 Relation, F5 Time, F6 Authority/Provenance, GDF0 rule/practice authority and GDF1 action/contribution contracts—plus a small case-decision/adjudication view?

If yes:

```text
ParticipationAuthorityTopology
= derived projection / query surface
```

not a new Game-owned foundation responsibility.

Canonical evidence/probes:

```text
evidence/gdf3-b/authority-decomposition.json
evidence/gdf3-b/authority-topology-probes.json
scripts/gdf3-b/authority-topology-probes.mjs
scripts/gdf3-b/audit-gdf3-b.mjs
```

B's answer after 18 cross-regime cases is:

```text
YES — topology compresses.
```

But one deeper residual does not:

```text
Adjudication / Interpretation / Review / Contestability.
```

---

# 1. Authority is a relation, not a scalar possessed by a role

A weak model says:

```text
Player.authority = 30
Judge.authority = 70
HeadJudge.authority = 100
Operator.authority = 120
```

or:

```text
Operator > HeadJudge > Judge > Player > Spectator
```

B falsifies both.

Real practices repeatedly require different authorities over different operations and scopes.

Examples:

```text
Referee
→ final authority over match facts / case rulings

IFAB / competition authority
→ authority over rules / competition structure

VAR
→ evidence/review contribution under a restricted protocol

Tournament Organizer
→ logistics / appointment / exceptional replacement authority

Head Judge
→ tournament case adjudication / appeal authority

Player
→ Player GameAction authority in a player slot
```

No one number captures these relations.

Strong law:

```text
Authority != GlobalRank.
```

---

# 2. Minimal compression candidate — ScopedAuthorityEdge

B does **not** propose a new F10 primitive.

It uses a research representation of already-frozen F3/F5/F6/F4 semantics:

```text
ScopedAuthorityEdge =
(
  holder / RoleAssignment,
  operation,
  object-or-consequence domain,
  scope,
  activation condition,
  valid time/currentness,
  binding status,
  authority source,
  provenance
)
```

This can be serialized in many ways.

The important point is semantic:

> An authority statement is incomplete unless it says what operation may bind what consequence, under what scope/currentness/source.

Thus:

```text
"X has authority"
```

is generally too weak for serious Game analysis.

---

# 3. RoleAssignment != AuthorityGrant

R24 already proved:

```text
Role != Occupant.
```

B adds another separation:

```text
RoleAssignment != AuthorityGrant.
```

Why?

A role label can remain constant while:

```text
currentness changes
scope changes
qualifying conditions change
a temporary substitute takes over
an appeal judge is designated
an official is suspended/replaced
one of several role-holders owns a particular flight/table/domain
```

Conversely, some authority can be granted directly through a practice rule without requiring a richly named role.

Therefore do not infer a complete power set from:

```text
role = "judge"
role = "GM"
role = "moderator"
```

Role is a relation-bearing position.
Authority is a scoped relation about binding consequences.

---

# 4. Contribution and authority are separate axes

A large fraction of the GDF3 residual disappears once we stop asking only:

```text
Who caused the outcome?
```

and ask instead:

```text
Who contributed what?
Who was authorized to bind what?
```

Possible contribution forms include:

```text
evidence
observation
advice
recommendation
proposal
vote/control contribution
```

A contribution can strongly alter the eventual result without itself being binding.

Therefore:

```text
CausalContribution != DecisionAuthority.
```

This is the general form behind:

```text
VAR → referee
coach → player
spectator report → judge
advisor → decision-maker
audience vote → aggregation/admission rule
```

---

# 5. IFAB gives the cleanest recommendation-vs-finality falsifier

Current IFAB Law 6 says other match officials assist the referee but the final decision remains with the referee.
The VAR protocol similarly restricts VAR to checks/review recommendations within specified incident classes while the referee makes the final decision.

This yields:

```text
Evidence / Recommendation
!= FinalRulingAuthority.
```

The distinction survives even if:

```text
same replay footage
same rule text
same incident
```

are held fixed.

What changes is the authority relation attached to the output.

This counterexample alone kills:

```text
whoever has best information = authority
whoever recommends = decision-maker
whoever detects error = final adjudicator
```

---

# 6. "Final authority" is scope-relative, not globally maximal

The phrase `final authority` is dangerous if interpreted globally.

Magic tournament policy gives an especially strong counterexample.
The Head Judge is final for appeals/rulings in the tournament scope, but:

```text
Tournament Organizer
can hold distinct appointment/replacement authority;

Wizards / tournament policy source
can change the governing tournament rules;

large events can have multiple Head Judges,
including partitioned flights/scopes,
each with final ruling authority where assigned.
```

Therefore:

```text
FinalAuthority
!= globally highest entity.
```

A better operational interpretation is:

> For decision D under current scope S/time t, there is no currently admitted further review/override transition inside the queried adjudication horizon.

Thus:

```text
Finality = property of Decision × Scope × ReviewTopology × Currentness
```

not a permanent intrinsic property of a person/role.

B does not freeze this exact formula yet; C must attack review/finality more deeply.

---

# 7. Authority topology is not necessarily a tree

A fixed hierarchy assumes:

```text
one root
one parent per authority
one total/partial upward ordering
```

Real cases violate this.

### Disjoint final scopes

```text
HeadJudge-A → flight A
HeadJudge-B → flight B
```

Both can be final without one outranking the other in the relevant case scope.

### Orthogonal authorities

```text
Tournament Organizer
→ appoint/replace staff

Head Judge
→ adjudicate cases
```

Neither relation implies a universal ordering across every operation.

### Rule versus case authority

```text
Rules authority
→ changes general policy/ruleset

Case adjudicator
→ applies current rule to current case
```

Again orthogonal.

Therefore:

```text
AuthorityTopology != Tree by identity.
AuthorityTopology != TotalOrder.
```

Typed graph/relation views are sufficient.

---

# 8. Delegation != advice != recommendation != assistance

These are commonly collapsed in Agent systems.

B separates them.

## Advice / recommendation

```text
A supplies information/evaluation/proposal to B.
B retains binding authority.
```

Example:

```text
coach → player
VAR → referee
```

## Delegation

A current authority source intentionally authorizes another holder to exercise some binding operation under a limited scope/condition/time.

A serious delegation claim therefore needs at least:

```text
source authority
recipient
operation/domain
scope
currentness/expiry
conditions
```

But B finds no need for `Delegation` as a new semantic primitive.

It can be represented as:

```text
an authority-bearing transition
that creates/changes another ScopedAuthorityEdge.
```

Therefore:

```text
DelegationPrimitive = REJECTED.
```

---

# 9. Delegation != replacement

Magic and IFAB provide useful pressure here.

A Head Judge may temporarily transfer duties.
A competition rule may define who replaces an incapacitated referee.
A Tournament Organizer may replace a Head Judge under exceptional conditions.

These can produce similar end states:

```text
new occupant currently exercises authority
```

while having different provenance.

```text
Delegation
→ authority derives through an authorized transfer by current holder/source

Replacement
→ authority assignment changes under a separate appointment/substitution rule
```

No new primitives are required, because the difference lives in:

```text
source
transition provenance
currentness
role assignment
```

which F3/F4/F5/F6 already preserve.

---

# 10. Authority can be conditional even while the role remains occupied

Current authority is often conditional.

Examples:

```text
VAR may intervene only for specified reviewable incident classes.

A referee may lose ability to revise an earlier decision after specified restart/end boundaries,
subject to explicit exceptions.

A substitute official gains authority only after incapacity/substitution conditions are met.

A coach may communicate only in permitted periods/practices.

An Agent tool may be allowed to adjudicate only low-risk action categories.
```

Therefore:

```text
RoleAssignment alone != CurrentAuthority.
```

A sufficient authority representation needs:

```text
scope + condition + currentness
```

when those distinctions alter consequence.

---

# 11. Review authority is not first-instance authority

Magic's appeal structure is especially useful.

A Floor Judge can issue an initial ruling.
A player may appeal that ruling to the Head Judge.
The Head Judge may uphold or overturn it, and the Head Judge/authorized appeals judge is final at that event scope.

This yields:

```text
FirstInstanceRulingAuthority
!= ReviewOverrideAuthority.
```

The same entity *can* sometimes hold both, but the operations remain conceptually distinct.

Why this matters:

```text
review requires a prior decision/claim as input;
first-instance adjudication does not.
```

Thus review cannot be reduced to merely "more authority".
It is a different transition relation over decision history.

This surviving structure is one reason C must focus on adjudication/review rather than more participant-role ontology.

---

# 12. Appeal is not a universal infinite authority chain

Magic policy also falsifies the intuition:

```text
any decision can always be escalated upward again.
```

The current appeal system defines a most-authoritative event-level ruling boundary.
Likewise IFAB limits when VAR review is available and when decisions can be revised.

Therefore:

```text
Contestability != infinite revisability.
Reviewability != non-finality forever.
```

A GamePractice may intentionally choose:

```text
no review
one review layer
conditional review
multi-stage review
post-hoc certification only
```

C must model these possibilities without assuming that more review is always better.

---

# 13. Rule-change authority != case-ruling authority

This distinction survives every compression attempt.

Hold fixed:

```text
current evidence
current player action
current incident
```

Compare:

```text
Authority A:
  may change the general rule for future/current version

Authority B:
  may decide whether the current incident satisfies the current rule
```

They alter different objects and future sets.

Therefore:

```text
RuleChangeAuthority != CaseRulingAuthority.
```

R29/F6 can represent both through scoped authority.
No new semantic primitive is needed.

But GDF3 must preserve the distinction because Agent-native systems increasingly let one model perform both functions.

---

# 14. Ruling != enforcement

A binding determination need not be physically/technically realized by the same role/system.

Examples:

```text
judge rules
→ scorekeeper records result

referee rules
→ game restarts / sanction is applied

moderator decides violation
→ account system executes suspension

appeals board reverses result
→ ranking database updates record
```

Therefore:

```text
DecisionAuthority != Effectuation/EnforcementAuthority.
```

In software this distinction may collapse implementation-wise into one transaction.
Semantically it remains useful when:

```text
execution can fail
decision can be appealed before execution
separate audit/provenance matters
```

GDF3 does not create a separate enforcement foundation; F4/F6 and owner-specific execution contracts suffice.

---

# 15. Verification != original World/GameInstance history

Post-hoc practices create a subtle but important separation.

Suppose a speedrun trajectory has already happened and is preserved as history H.
Later a verifier decides:

```text
VALID under category C
```

or:

```text
INVALID under category C
```

The practice record/recognition changes.
The original historical trajectory need not.

Thus:

```text
OriginalHistory
!= CertifiedPracticeRecord.
```

and:

```text
VerificationDecision
!= rewriting the original GameInstance by identity.
```

This keeps R13/R24/R28 authority layers intact and avoids retroactively mutating World truth when only category/record recognition changed.

---

# 16. Aggregation needs no collective authority primitive

Audience voting, jury/judge panels and team contribution can produce one binding output from many contributors.

Weak model:

```text
many people contribute
→ collective entity has authority
```

B rejects that inference.

A sufficient generic pattern is:

```text
Contributor_1 ... Contributor_n
→ admissible contributions
→ AggregationRule / DecisionProcedure
→ candidate/binding result
```

Authority may attach to:

```text
the contribution right of each member
and/or
the aggregation procedure's admitted result
```

without requiring:

```text
one CollectiveSubject
one CollectiveAuthority substance
```

Therefore:

```text
AggregationPrimitive = REJECTED.
```

This reuses ordinary relation/transition structure and GDF1 contribution topology where the output controls GameAction.

---

# 17. Aggregation rule itself can be the decisive counterfactual

Hold individual votes fixed:

```text
60 A
40 B
```

Change only aggregation rule:

```text
simple majority → A
supermajority threshold 2/3 → no decision
random weighted draw → possibly B
unanimity → no decision
```

The binding Game result changes.

Therefore:

```text
MemberContributions alone != CollectiveOutcome.
```

The authoritative transition/admission rule matters.

Again this is ordinary F4 + F6 structure, not a new participation primitive.

---

# 18. Advice can be causally powerful but remain non-binding

Consider a coach:

```text
observes opponent
→ sends advice
→ player changes policy
→ player wins
```

The advice may be counterfactually decisive.

But:

```text
Coach did not thereby acquire Player GameAction authority.
```

Even stronger:

```text
same advice
+ competition where coaching is allowed
→ legitimate contribution

same advice
+ competition where outside assistance is prohibited
→ violation / inadmissible contribution
```

So the key dimensions are:

```text
Contribution
+ admissibility/current practice rule
+ binding authority
```

not raw causal influence.

---

# 19. Spectator reporting shows observation can enter authority processes without becoming adjudication

Magic tournament policy gives spectators responsibilities and allows them, under specified conditions, to alert judges to suspected violations.

This is structurally useful:

```text
Spectator observes event
→ reports/elevates evidence
→ Judge/official adjudicates
```

Therefore:

```text
CanInitiateEvidenceEscalation
!= CanRuleOnCase.
```

This reinforces GDF3-A's result:

```text
Spectator != causal irrelevance
```

without collapsing spectator into Player or Judge.

---

# 20. Multiple DMs do not require a new multi-authority ontology

Current D&D Dungeon Master's Guide explicitly includes `Multiple DMs` as an operating case alongside narration and outcome resolution.

That matters because one named role family can have:

```text
several occupants
partitioned content/world domains
alternating temporal authority
shared preparation but separate session authority
```

The exact practice can vary.

But no new foundation object follows.

Represent:

```text
DM Role
+ Occupant A / Occupant B
+ scope/currentness assignments
+ current authority sources
```

and preserve conflicts when needed.

This is enough unless a future counterexample requires something beyond relation/time/authority.

---

# 21. Role conflict is not a primitive and not always a defect

One Entity may simultaneously have:

```text
Player authority
Adjudication authority
Content generation authority
Operator authority
```

A weak security-inspired reaction would declare:

```text
role fusion = invalid
```

GDF3-B rejects that as universal.

TTRPG GM practice intentionally fuses:

```text
world/content production
NPC control
rules adjudication
facilitation
```

while many competitive contexts intentionally separate player and judge authority.

Therefore:

```text
RoleConflict != co-location by identity.
```

Instead:

> A practice has an integrity/separation constraint when co-location of specified grants creates a counterfactual the practice intends to prohibit or render independently reviewable.

Thus `SeparationOfAuthorityConstraint` is a useful derived practice rule, not a universal foundation primitive.

---

# 22. Agent-era role fusion makes separation policy explicit

Agents make authority composition cheap.

One model can simultaneously:

```text
interpret player intent
propose NPC action
generate content
classify legality
score quality
moderate text
adapt difficulty
```

The question is not:

```text
Is one model allowed to do many things?
```

but:

```text
Which outputs are authoritative at which scope?
Which must be independently sourced/reviewed?
Which are proposals/evidence only?
Which authority combinations violate the current practice contract?
```

Therefore:

```text
ModelBoundary != AuthorityBoundary.
```

This is a major Agent-era operational consequence of GDF3-B.

---

# 23. Human/synthetic substrate does not determine authority semantics

Suppose a human referee and deterministic/software adjudicator receive:

```text
same rule source
same evidence contract
same case scope
same binding authority
same reviewability
```

Replacing one with the other changes implementation and perhaps legitimacy/experience, but does not automatically require different Game semantics.

Therefore:

```text
HumanAuthority != one ontology
SyntheticAuthority != another ontology
```

Authority validity comes from the current practice/rule/institution relation.

But:

```text
same functional accuracy
!= same legitimacy by identity.
```

R28 legitimacy/social acceptance remains separate.

This protects both directions:

```text
human does not mean authoritative automatically;
AI does not mean illegitimate automatically.
```

---

# 24. Adaptive experience manager fits the same authority decomposition

Experience-management research models AI agents/systems that tune a running game toward designer goals and, in procedural adaptation, can alter the game's dynamics/transition function.

B tests whether this requires a special `DirectorAuthority` primitive.

It does not.

Represent:

```text
ExperienceManager
has current authority to
AdaptGame(operation)
within AuthorizedDynamicsScope
under Designer/Practice source
```

This remains distinct from:

```text
Player GameAction authority
Opponent policy
Case adjudication
Rule-author authority
```

Thus GDF3-A's H5 residual can currently be consumed by ordinary scoped authority relations.

No independent adaptive-stewardship foundation is forced yet.

---

# 25. Authority scope is multi-level

GDF3-B finds at least four recurring scopes:

```text
GameInstance
GameStructure / ruleset-version
PlayPractice / category / tournament
Platform / institution
```

The same event can have different authorities at different levels.

Example:

```text
GameInstance:
  engine/referee resolves current action/event

Tournament/Practice:
  Head Judge or verifier rules on tournament/category validity

Ruleset:
  rules authority publishes current rule version

Platform:
  operator controls account/access/moderation
```

Do not collapse these to one `game authority`.

But these are ordinary typed scopes, not new primitive levels.

---

# 26. Scope nesting does not imply authority inheritance

A platform operator may control access to a tournament without being able to reverse a match fact under the tournament rules.
A rules publisher may change future rules without deciding the current disputed event.
A Head Judge may issue a final tournament ruling without controlling platform account ownership.

Therefore:

```text
BroaderScope != StrongerAuthority by identity.
```

and:

```text
Contains(scope A, scope B)
!= authority(A) dominates authority(B).
```

Authority inheritance must be explicit if the practice wants it.

---

# 27. Currentness/version is part of authority semantics

A role or rule may be historically valid but no longer current.

Examples:

```text
old tournament rules
retired judge assignment
superseded patch
past speedrun category definition
former moderator
previous DM for an earlier session
```

Therefore:

```text
HistoricalAuthority != CurrentAuthority.
```

R29/F6 already owns provenance/currentness.
GDF3 merely requires consumption discipline.

---

# 28. Authority source matters separately from holder

Two identical rulings from the same person can differ if one is issued:

```text
as current referee
```

and one:

```text
as private commentator after the match.
```

Same utterance.
Same person.
Different source/role/currentness relation.
Different binding consequence.

Therefore:

```text
HolderIdentity != AuthoritySource.
```

This is another reason `same Agent/model` is irrelevant to semantic binding without provenance.

---

# 29. A compact authority query that survives B

For any claimed Game authority, ask:

```text
WHO/HOLDER?
  Which current RoleAssignment / entity / system?

OPERATION?
  Observe/evidence? Recommend? Decide? Review? Enforce?
  Change rule/content/dynamics? Appoint/delegate? Allocate access?

OBJECT/DOMAIN?
  Which action/event/record/rule/content/access relation?

SCOPE?
  GameInstance / role slot / category / tournament / ruleset / platform?

CONDITION?
  What activates/limits it?

CURRENTNESS?
  Which time/version/window?

BINDING STATUS?
  Evidence/proposal/advice vs admitted binding result?

SOURCE/PROVENANCE?
  Which rule/practice/institution/delegation produced the authority?
```

This is a **research query template**.
It is not a mandated storage schema.

---

# 30. RoleCausalAccessProfile compresses

GDF3-A retained a provisional RoleCausalAccessProfile.

B now finds it does not need independent semantics.

It is simply a query:

```text
For RoleAssignment R at scope/time S,
collect current typed contribution + authority edges.
```

Therefore:

```text
RoleCausalAccessProfile
= derived projection.
```

No foundation contract is required for the profile itself.

---

# 31. ParticipationAuthorityTopology also compresses

This is B's central verdict.

Across:

```text
spectator evidence escalation
coach advice
VAR recommendation
referee ruling
Head Judge appeal
multiple Head Judges
replacement/delegation
audience aggregation
speedrun verification
operator governance
experience manager adaptation
role-fused Agent
```

all player-relevant counterfactuals can be reconstructed using:

```text
Role/RoleAssignment
+ typed Relation
+ scoped Authority/Provenance
+ Time/currentness
+ Rule/Transition semantics
+ GDF1 action/contribution attribution where action/control is involved
+ case-decision history when adjudication occurs
```

Therefore:

```text
ParticipationAuthorityTopology
!= independent Game foundation responsibility.
```

It remains a useful derived view across those relations.

---

# 32. Why this is not a failure of GDF3

GDF3 was opened because an important part of Game reality was structurally homeless in our deep research.

Finding that the residual compresses is success.

A/B have established several durable anti-collapse laws that R1-R29 had not tested deeply:

```text
RoleLabel != ResponsibilityTopology
RoleAssignment != AuthorityGrant
Contribution != Authority
Advice/Recommendation != Delegation
Finality != GlobalRank
AuthorityTopology != Tree
RuleChangeAuthority != CaseRulingAuthority
Ruling != Enforcement
Verification != original history
BroaderScope != StrongerAuthority
ModelBoundary != AuthorityBoundary
```

Those distinctions improve the world model even though they do not create a new primitive.

---

# 33. What refuses to compress cleanly: adjudication itself

The authority graph can say:

```text
who may decide
who may review
who may enforce
```

but it does not yet explain the internal case-resolution problem:

```text
What is the case?
What evidence counts?
Which rule/norm applies?
How is an open/ambiguous event interpreted/classified?
What makes one determination binding?
When can it be contested/reopened?
What does reversal do to already-produced consequences/history?
```

This appears in:

```text
referee decisions
TTRPG semantic action resolution
speedrun glitch/category disputes
card-game judge rulings
moderation decisions
natural-language GameAction admission
AI-generated rule/content interpretation
post-hoc record certification
```

That is not merely more participant topology.

It is a repeated **case interpretation → authoritative determination → review/contestability** problem.

Hence the residual survives.

---

# 34. Adjudication cannot yet be reduced to ordinary deterministic GameAction admission

GDF1 already has:

```text
Attempt/CandidateAction
→ admission/current legality
→ ExecutedGameAction
```

For many digital games, this can be deterministic and fully specified.

But GDF3 cases include:

```text
ambiguous natural-language intent
partial/contested evidence
socially interpreted category rules
conflicting testimony
open-text rules
judged performance quality
rule exceptions / spirit-of-game considerations
review/appeal of previous rulings
```

The question is not merely whether a candidate action passes a fixed predicate.

C must test whether all of these can still be represented through a generalized `AdjudicationContract`, or whether several distinct process families remain.

---

# 35. Contestability survives because authority alone cannot tell us whether a ruling is challengeable

Two decisions can be equally authoritative when issued yet differ in:

```text
review window
eligible appellant/requester
review grounds
review evidence
review authority
number of review stages
whether enforcement pauses
what reversal can repair
```

Thus:

```text
Authority != Contestability.
```

But B does not yet promote Contestability to a foundation object.

It is retained as part of the C falsifier space.

---

# 36. Agent-era pressure on adjudication is stronger than on role ontology

Agent-native games create cheap semantic openness:

```text
free-form player intent
procedural/generated rule descriptions
Agent-mediated negotiation
AI referee/GM
runtime content/rule generation
```

R29 already says:

```text
Generation / language proposal
→ Candidate
→ Authority admission
→ Consequence
```

The unresolved part is exactly the admission/adjudication boundary:

```text
how evidence and interpretation become authoritative
without silently making model output = World truth.
```

Thus Agent-era evidence strengthens GDF3-C rather than reopening F1-F9.

---

# 37. External evidence anchors used in B

Representative anchors:

```text
IFAB Laws of the Game — Law 5, Law 6, VAR Protocol
- referee final case authority
- other officials/VAR assistance/recommendation
- restricted review conditions
- replacement/currentness rules

Magic: The Gathering Tournament Rules / Rules Resources
- explicit tournament roles
- Head Judge as final judicial authority
- appeals from floor judges
- temporary transfer of duties
- Tournament Organizer replacement authority
- multiple Head Judges / partitioned scopes
- spectator reporting responsibilities

D&D Dungeon Master's Guide (2024)
- explicit support for Multiple DMs
- separates running-game concerns such as narration and resolving outcomes

Thue & Bulitko (2012, 2018)
- experience management can alter running-game dynamics
- manager can be modeled as embedded in the game
```

These sources are used as counterexample generators, not as definitions of Ordivon concepts.

---

# 38. Novelty audit

## N0 — established structures

```text
formal adjudication hierarchy/appeal
role delegation/replacement
multiple officials
conditional review
experience management
```

are established in prior practice/literature.

## N1 — Ordivon compression

```text
FinalAuthority != global rank
BroaderScope != stronger authority
RoleAssignment != AuthorityGrant
Authority topology need not be a tree
```

are conservative cross-domain compressions.

## N2 — useful synthesis candidate

```text
ScopedAuthorityEdge query discipline
```

as one common representation spanning players, referees, GMs, operators, audience systems and Agent role fusion is a useful Ordivon synthesis.

But it is explicitly treated as a derived representation over F1-F9, not a new primitive.

## N3

None claimed.

---

# 39. Upstream reopen audit

## R29 / F1-F9

All B counterexamples remain representable through:

```text
F1 Entity/Reference
F2 State
F3 Relation
F4 Transition/Constraint
F5 Time
F6 Authority/Provenance
F7 Observation/Representation
F8 Evaluation
F9 Action/Capability/Policy/Control
```

No new semantic coordinate is required.

```text
R29 reopen = NOT TRIGGERED.
```

## GDF0

EffectiveRuleTopology and constitutive-overlay tests already support:

```text
rule source/currentness
practice/institutional authority
scope-dependent constitutive roles
```

B refines consumption rather than contradicting them.

```text
GDF0 reopen = NOT TRIGGERED.
```

## GDF1

Player/shared/aggregate action contributions still use:

```text
GameActionContract
ControlContributionTopology
ControlMapping/Locus
```

GDF3 does not duplicate them.

```text
GDF1 reopen = NOT TRIGGERED.
```

## GDF2

Changing authority/adaptation can change challenge/evaluation conditions, but Challenge/Failure/Mastery contracts remain scope/currentness-bound as intended.

```text
GDF2 reopen = NOT TRIGGERED.
```

---

# 40. GDF3-B verdict

```text
GDF3-B = COMPLETE

ParticipationAuthorityTopology as independent foundation
= REJECTED / COMPRESSED

RoleCausalAccessProfile
= DERIVED QUERY

GlobalAuthorityRank / fixed authority tree
= REJECTED

Delegation primitive
= REJECTED

Aggregation primitive
= REJECTED

RoleConflict primitive
= REJECTED

FinalAuthority scalar/property
= REJECTED

ScopedAuthorityEdge
= useful derived representation of existing DomainAuthority

SeparationOfAuthorityConstraint
= useful practice-specific derived rule

AdjudicationProcessFamily
= SURVIVES

Review / Contestability
= SURVIVES AS C PRESSURE

R29 / GDF0 / GDF1 / GDF2 reopen
= NO
```

B's deepest result is:

```text
Game does not need a new Participation Authority substance.

It needs exact typed questions about
who may make which kind of contribution or binding change,
under which scope/time/source/condition.

Once those are explicit,
most participation topology is ordinary relation + authority structure.
```

---

# 41. Exact next round

The residual is now sufficiently narrow to choose C without reopening the whole Game coverage map.

Next:

```text
GDF3-C — Adjudication / Interpretation / Review / Contestability
```

Primary question:

> What minimum Game-owned case-resolution responsibility is required when evidence/proposals/events must be interpreted under rules/evaluations before a binding determination is produced, especially when the case is ambiguous, open-ended, disputed or reviewable?

C must attack at least:

```text
Evidence != Fact != Claim
Rule != interpretation
Interpretation != classification
Classification != ruling
Ruling != enforcement
Error correction != appeal
Review != replay
Finality != truth
Reversal != history erasure
Formal legality != legitimacy/fairness
Deterministic admission != all adjudication
Human judge != necessary
AI judge != automatic authority
```

Minimum regimes:

```text
deterministic videogame resolver
natural-language action admission
football/VAR
Magic judge appeal
TTRPG open-intent ruling
judged performance
speedrun record/category dispute
moderation case
Agent-generated rule/content dispute
post-hoc verification
```

Only after C should GDF3 decide whether any adjudication contract deserves freezing.
