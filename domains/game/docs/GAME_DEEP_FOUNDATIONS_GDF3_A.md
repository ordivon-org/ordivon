---
schema_version: 1
id: game.deep-foundations.gdf3-a
title: Ordivon Game Deep Foundations — GDF3-A Participation / Role / Mediation / Adjudication Term Separation & Counterfactual Inventory
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Opens residual-selected GDF3 after the whole-Game domain-coverage search. Separates Entity, Subject, Role, Player and scope-qualified Participant; rejects Participant and ParticipationRole as new primitives; rejects Mediation as one mechanism; separates spectator/audience/advisor/referee/verifier/GM/operator/director functions; establishes that role labels can bundle separable channels and one entity can hold multiple conflicting roles; retains Game-relative role/authority topology and adjudication as deeper research targets. No frozen foundation reopen is triggered.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.domain-coverage-search
  - game.play-game-deep-foundations.v1
  - game.action-control-skill-foundations.v1
  - game.challenge-failure-mastery-foundations.v1
  - game.foundations-research.r24
  - game.foundations-research.r29
---
# Ordivon Game Deep Foundations — GDF3-A

## 0. Why GDF3-A begins by trying to delete `Participant`

The whole-Game coverage search did not select GDF3 because the corpus lacked words such as `player`, `spectator`, `referee`, `GM`, `operator` or `director`.

It selected this branch because the corpus lacked one coherent answer to a deeper question:

```text
Who can participate in a Game / GamePractice,
through which role,
with what observation / action / evaluation / adjudication / change authority,
and how can those roles compose or change?
```

The danger is obvious: a weak ontology would immediately invent a hierarchy such as:

```text
Participant
├── Player
├── Spectator
├── Referee
├── GM
└── Operator
```

and mistake vocabulary for structure.

GDF3-A instead starts from deletion.

Canonical evidence/probes:

```text
evidence/gdf3-a/term-role-matrix.json
evidence/gdf3-a/participation-role-probes.json
scripts/gdf3-a/participation-role-probes.mjs
scripts/gdf3-a/audit-gdf3-a.mjs
```

The first result is already strong:

```text
Participant != EntityKind.
ParticipationRole != new primitive by default.
Mediation != one mechanism.
```

---

# 1. Upstream constraints are stronger than they first appear

R24 already defined:

```text
Role =
relational / institutional / narrative position
carrying some combination of
expectations, rights, duties, permissions, capabilities and function.
```

and established:

```text
Role != Occupant
OneEntity can occupy MultipleRoles
```

R29 then established:

```text
Player = a role at the system boundary,
not necessarily a World Subject.

Player != Character != Subject.
```

Therefore GDF3 is **not allowed** to solve the residual by saying:

```text
Player / Referee / GM / Spectator
= four new entity types.
```

The burden is narrower:

> identify the Game-specific causal/authority relations among occupants, roles and GameStructure/Practice scopes that the generic R24 Role model did not deeply reconstruct.

---

# 2. Entity, Subject, Role, Player and Participant must remain separate

## 2.1 Entity

```text
Entity = authoritative referent.
```

It answers:

```text
which thing/person/system is this?
```

It does not answer:

```text
what Game-relative role does it currently occupy?
```

---

## 2.2 Subject

R29's Subject composition concerns a locus with enough subject-side machinery to support some combination of:

```text
observation
representation/belief
evaluation/motive
policy/action
history/learning
```

A referee need not be represented as a diegetic Subject.
A software adjudicator need not be a Subject in the rich sense.
A Player can operate through several Subjects.

Therefore:

```text
Subject != Participant
Subject != Player
Subject != Role
```

---

## 2.3 Role

R24's generic Role survives intact.

GDF3-A does not create a new role ontology.

Instead it asks how Role becomes Game-relative through scoped assignments of:

```text
observation rights
proposal/action channels
evaluation rights
adjudication authority
verification authority
enforcement/governance authority
world/content/rule-change authority
```

These dimensions are candidate research coordinates, not a frozen exhaustive list.

---

## 2.4 Player

R29 already made Player structural:

```text
Player = system-boundary role.
```

GDF3-A sharpens only the anti-collapse boundary:

```text
Player != any causally relevant entity.
Player != Controller by identity.
Player != Subject by identity.
Player != Participant generally.
```

A referee can causally determine a score without being a Player.
An AI Director can causally alter the next encounter without being a Player.
A coach can causally change a player's policy without holding the player's GameAction authority.

GDF3-A therefore does **not** redefine Player as `all causal participants`.

A later round may need a stronger positive Player criterion, but A does not force one.

---

## 2.5 Participant

`Participant` fails as one unqualified ontological class.

Why?

The same person can be described as:

```text
participant in the event
participant in the PlayPractice
participant in the tournament
participant in the current GameInstance
participant in gameplay/enactment
```

with different truth values.

A passive livestream viewer may participate in the event/community while having no GameAction or adjudication authority.
A referee participates in the match structure without playing for either team.
A remote tournament administrator may participate institutionally without entering the field/world.

Therefore GDF3-A adopts only:

```text
Participant = scope-qualified descriptor.
```

Never store/use:

```text
participant = true
```

without a scope and participation relation when the distinction matters.

Strong law candidate:

```text
ParticipationScope matters.
```

But `ParticipationScope` is not yet frozen as a new object; it can likely be represented through existing Relation + Authority + Role + GameStructure/Practice references.

---

# 3. First executable falsifier — spectator → audience participant

Constructed paired case:

```text
same Entity E
same stream
same observation channel

t0:
  E watches only

t1:
  E's cheer/jeer/vote is admitted
  into an aggregation/control path
  that changes a Game parameter/action candidate
```

Entity identity does not change.
The Game-relative causal channel does.

Therefore:

```text
EntityIdentity != ParticipationRole/Relation
Spectator != causal nonparticipant by identity
Observation != exhaustive role description
```

Audience-participation research provides real systems with exactly this boundary: audience members can meaningfully affect gameplay, including through aggregate signals that alter AI behavior.

This does **not** imply every spectator is a Player.

It implies the spectator/player boundary is not recoverable from `isWatching` alone.

---

# 4. Audience is not one Subject

The natural modeling error for Twitch-Plays-Pokémon-like or audience-participation systems is:

```text
Audience = one giant Agent/Subject.
```

That is unnecessary in many cases.

A sufficient model may be:

```text
Many Entities
→ individual contribution signals
→ aggregation rule
→ one candidate control/action/parameter update
```

The aggregate can have causal force without possessing:

```text
one belief state
one motive structure
one memory
one policy
one identity
```

Therefore:

```text
CollectiveCausalContribution != CollectiveSubject by identity.
```

This reuses GDF1 `ControlContributionTopology` where audience input becomes control.

GDF3 should add no collective-mind primitive merely because many entities contribute to one Game effect.

---

# 5. Passive spectator, active audience and Player are not a scalar ladder

A tempting model is:

```text
spectator --more agency--> audience participant --more agency--> player
```

GDF3-A rejects that as a universal hierarchy.

Why?

A referee can have enormous consequence authority with no Player GameAction role.
A judge can determine evaluation while never controlling the performer.
A coach can strongly alter policy through information but have no admitted GameAction.
A broadcaster can frame audience information while lacking formal rule authority.

The relevant structure is multidimensional.

Candidate dimensions include:

```text
Observe
Inform / Advise
ProposeAction
ExecuteAction
Evaluate
Adjudicate
Verify
Enforce
ModifyContent
ModifyRules
AllocateAccess
AdaptGame
```

This is currently a probe vocabulary, not a frozen channel enumeration.

---

# 6. Referee is the strongest anti-Player counterexample

Association football makes the role separation unusually explicit.

The Laws assign the referee authority to enforce the Laws for the match and make final decisions on facts connected with play.
Other match officials and VAR can provide information/assistance, but final decision authority remains with the referee under the protocol.

This gives a clean decomposition:

```text
Rule source
!= event evidence
!= assistant/VAR recommendation
!= final ruling authority
!= enforcement/consequence
```

The same physical event can receive different official classification/ruling and therefore different authoritative match history.

That is a genuine Game counterfactual.

But it requires no new F1-F9 primitive:

```text
Event/evidence
+ Representation/interpretation
+ Rule/constraint
+ scoped Authority/Provenance
→ Ruling
→ admitted transition/history/evaluation consequence
```

The missing work is domain structure, not semantic substrate.

---

# 7. Rule != Interpretation != Ruling != Enforcement != Appeal

GDF0 deeply modeled EffectiveRuleTopology and rule authority/currentness.

GDF3-A now finds that a rule-governed practice may additionally separate at least these functions:

## Rule

General/current normative or transition standard.

## Interpretation / Classification

Mapping evidence/case into a meaning/category relevant to the rule.

Example:

```text
Did this contact satisfy the foul criterion?
Does this speedrun technique count as a forbidden glitch?
What GameAction does this natural-language intent denote?
```

Interpretation can remain non-authoritative.

## Ruling

A case-level authoritative determination under a declared scope.

```text
Ruling != belief/opinion by identity.
```

Its binding force comes from current authority.

## Enforcement / Realization

Applying sanctions, score changes, access changes, restart/continuation or other consequences.

The adjudicator and enforcer can differ.

## Review / Appeal

A process that can inspect or challenge an earlier ruling under a different authority/currentness rule.

GDF3-A does not yet freeze `Appeal` as universally required; many games intentionally have no appeal layer.

The key law is separation, not mandatory presence.

---

# 8. `Adjudication` survives deletion, but only as a process family

Unlike `Participant`, `Adjudication` survives the first deletion round.

Reason:

Across materially different practices, there is a repeated case-level problem:

```text
Evidence / Proposal / Event
+ applicable Rule/Evaluation
+ Interpretation/Classification
+ scoped decision Authority
→ binding case determination
```

Examples:

```text
football referee
combat-sport judge
TTRPG rules decision
speedrun record/category verification
natural-language action admission
moderation case decision
```

But A refuses to freeze:

```text
Adjudication = one algorithm
Adjudicator = one role
Adjudication = human judgment
Adjudication = enforcement
Adjudication = finality
```

A deterministic engine may adjudicate some actions automatically.
A human may adjudicate ambiguous residuals.
A committee may rule on records after the GameInstance.

Therefore `AdjudicationProcessFamily` is retained for deeper B/C falsification.

---

# 9. Game Master destroys the idea that a named role is one atomic function

The Game Master is a high-value counterexample because one occupant can bundle functions that other GameForms assign to separate entities/systems.

TTRPG practice and research associate GM/DM roles with combinations of:

```text
world/situation presentation
story facilitation
NPC/actor control
rule knowledge
rule dispute adjudication
communication facilitation
content/world generation
experience steering
```

Official D&D descriptions likewise characterize the DM as narrator, rules referee and controller of a cast of characters/creatures.

Therefore:

```text
GameMaster != one primitive function.
NamedRole != ResponsibilityUnit.
```

The same is true in the opposite direction:

```text
one ResponsibilityUnit
may be distributed across several roles/entities.
```

Football's referee + assistants + VAR is the mirror-image case.

This produces one of GDF3-A's strongest structural laws:

```text
RoleLabel != ResponsibilityTopology.
```

---

# 10. Occupant, role, responsibility and authority must be four different questions

For any GDF3 case ask separately:

```text
1. Occupant:
   which Entity/system currently holds something?

2. Role:
   what recognized relational/institutional/Game position is occupied?

3. Responsibility/function:
   what operation is performed?

4. Authority:
   whose result binds which consequence at this scope/time?
```

Example:

```text
VAR
Occupant: official V
Role: video match official
Function: inspect replay / identify reviewable issue / advise
Authority: can recommend review; not final match ruling authority
```

versus:

```text
Referee
Occupant: official R
Role: referee
Function: observe / interpret / decide / enforce
Authority: final ruling at declared match scope
```

This decomposition survives both analogue and automated cases.

---

# 11. Coach/advisor proves causal influence is not direct GameAction

Suppose:

```text
Coach observes opponent
→ sends advice
→ Player changes policy
→ Player executes action
```

The coach is causally important.

But if the practice does not grant the coach direct control:

```text
CoachAction != PlayerGameAction
```

and:

```text
InfluenceOnPolicy != ControlOfGameAction by identity.
```

This matters because a naïve `ParticipationCausalAccess` model could accidentally classify every causal influence as player action.

GDF3 must retain the attribution chain.

It also means external advice can be constitutive or prohibited depending on practice rules:

```text
same advice content
+ different tournament coaching rule
→ legal support vs violation.
```

Again, authority/practice scope matters.

---

# 12. Operator/moderator is scope-dependent, not always inside or outside Game

An MMO/platform operator may:

```text
ban an account
restore an item
reverse an exploit gain
modify rules
patch content
schedule an event
change matchmaking eligibility
moderate communication
```

Some of these act on:

```text
platform/practice access
```

rather than diegetic World state.

Others can alter effective GameStructure directly.

Therefore:

```text
Operator != WorldSubject
Operator != ExternalOnly
```

The correct test comes from GDF0 constitutive overlays:

> Does changing the operator/moderator role assignment or its current authority change admissible action, evaluation, transition interpretation, valid evidence/history, role meaning, or effective Game constraints?

If yes at the queried scope, the relation is Game-constitutive.
If not, it may remain surrounding platform/social causation.

No universal `inside/outside` bit is sufficient.

---

# 13. Experience manager / AI Director breaks `Game = fixed environment + adaptive Subjects`

R27 modeled:

```text
experience
→ retained Subject change
→ later policy/capability difference
```

Experience Management gives the inverse causal loop:

```text
Game observes Player/Game state
→ builds/uses a Player model or management state
→ selects a management policy
→ changes running-game dynamics/content/parameters
→ later Player/Game trajectory changes
```

Thue & Bulitko explicitly formalized procedural game adaptation as modifying game dynamics during play, including via changes to transition structure; later work presents experience managers as agents embedded in a game that tune running-game parameters toward designer goals.

Therefore:

```text
SubjectLearning != GameAdaptation.
```

and:

```text
ExperienceManager != Player
ExperienceManager != Opponent by identity
```

But another critical result follows:

```text
CausalGameComponent != Participant by identity.
```

If every game subsystem that changes play is called a Participant, then physics, RNG, scheduler and damage resolver also become participants and the term loses discriminatory value.

So GDF3 must distinguish:

```text
Game-internal causal function
```

from

```text
recognized participation role/relation.
```

This is one reason `Participant = anything with causal access` is rejected.

---

# 14. `Mediation` fails as one foundation construct

The word `mediation` initially looked attractive because GM, referee, UI, interpreter, moderator and director all sit “between” something and something else.

But cross-case attack shows several unrelated mechanisms:

```text
ControlMapping mediation
  input → GameAction candidate

Perceptual/media mediation
  World/signal → participant observation

Semantic interpretation
  open expression → candidate meaning/action

Adjudication
  evidence/case + rule → binding ruling

Social facilitation
  participants → coordinated interaction

Experience management
  player/game observation → game adaptation

Governance/moderation
  practice claim/behavior → sanction/access/change
```

These do not share one sufficient mechanism beyond generic relation/transition.

Therefore:

```text
MediationAsPrimitive = REJECTED.
```

GDF3 should use the specific process name instead of treating `mediation` as explanatory.

---

# 15. Role transition needs no new primitive

Spectator → active audience participant is a real transition.

Player → coach is a real transition.

Player → temporary referee in a casual game may be a real transition.

But R24 + F5/F6 already provide enough substrate:

```text
same Entity
+ time-indexed RoleAssignment relation
+ changed rights/authority/currentness
```

Therefore:

```text
RoleTransitionPrimitive = not admitted.
```

Likewise `RoleComposition` needs no primitive:

```text
one Entity
→ occupies Role A + Role B + Role C
```

with potential authority conflicts represented as relations/constraints.

The deep issue is not existence of composition.
It is how Game should reason about the consequences and conflicts of composed authority.

---

# 16. Role-fused Agent is the strongest Agent-era pressure test

Imagine one synthetic Agent instance acts as:

```text
Player/controller
+
legality interpreter
+
final adjudicator
```

Nothing in Entity identity prevents this.

But the configuration has radically different integrity properties from:

```text
Player Agent
+
independent adjudicator
```

because the same implementation/occupant can:

```text
propose action
interpret ambiguous action
rule on legality
```

This may be intentionally valid in one GameForm and unacceptable in another.

Therefore:

```text
SameEntity != SameRole
SameModel != SameAuthority
RoleFusion != AuthorityEquivalence
```

and:

```text
ConflictOfInterest cannot be detected from Entity identity alone.
```

Agent-era systems make role/authority topology operationally urgent, but the distinction predates Agents in referees, GMs and platform operators.

So novelty is mostly **N1/N2 configuration pressure**, not an Agent-only N3 ontology.

---

# 17. Production Agent still does not become a Game participant automatically

A Studio/production Agent can:

```text
generate a map
write dialogue
balance a table
suggest rules
```

before runtime.

That does not make it a participant in the later GameInstance.

R29 still governs:

```text
Generation → Candidate
Authority admission → Consequence
```

Only when a production/runtime system is given current GamePractice/GameStructure authority—e.g. modifying content/rules during play—does GDF3 need to model the relevant runtime role/function.

Therefore:

```text
ProductionContribution != RuntimeParticipation.
```

---

# 18. Game-constitutive role is a relation test, not a category list

GDF3-A does not declare:

```text
Players, referees and GMs are inside the Game;
spectators, coaches and operators are outside.
```

That fails across regimes.

Instead reuse GDF0's constitutive-overlay test.

A role relation is **Game-constitutive at a queried scope** when changing that current role assignment/authority changes one or more relevant GameStructure semantics such as:

```text
admissible action
role/object meaning
evaluation/score validity
timing/phase semantics
transition interpretation
valid evidence/history/record
rule/currentness/change authority
```

This is a derived test, not a new primitive.

Examples:

```text
passive audience member
→ often not current GameStructure-constitutive

APG voting audience
→ control relation can become constitutive

referee
→ adjudication authority constitutive

speedrun verifier after run
→ category/record validity constitutive to the practice record, not necessarily to original executable transition

operator patch authority
→ constitutive when patch changes current rules/content
```

The scope must therefore be explicit.

---

# 19. Player remains special without becoming universal supertype

One possible overreaction would be:

```text
Player was too narrow.
Delete Player and replace everything with Participant.
```

GDF3-A rejects this.

Player remains a useful Game-specific boundary role because Game design repeatedly asks:

```text
whose choices are being solicited as gameplay?
whose causal access carries the player-value hypothesis?
whose action/interpretation/expression is evaluated as play?
```

Referee/judge/operator roles answer different questions.

So:

```text
Player is retained.
Participant does not replace Player.
```

But Player itself remains scope/practice recognized rather than reduced to:

```text
human
controller
avatar owner
button presser
subjective experiencer
```

---

# 20. Candidate derived view — RoleCausalAccessProfile

The executable probe uses a deliberately provisional profile:

```text
Observe
ProposeGameAction
ExecuteGameAction
Advise
Evaluate
Adjudicate
VerifyHistory
Enforce
GenerateWorldContent
ModifyRules
ModifyContent
AllocateAccess
AdaptGame
```

The purpose is not to freeze this 13-dimensional vector.

The purpose is to test whether different roles remain distinguishable when represented as scoped channels + authority.

They do.

Examples:

```text
Spectator:
  Observe

Coach:
  Observe + Advise

Player:
  Observe + GameAction channels

VAR-like assistant:
  Observe + Evaluate + Verify
  but no final ruling

Referee:
  Observe + Evaluate + Adjudicate + some Enforcement

GM:
  several channels bundled

Director:
  Observe/Evaluate + AdaptGame
```

Therefore `RoleCausalAccessProfile` survives as a **derived research view**.

It is not yet frozen because:

```text
channel list may be incomplete;
authority may be more important than function bits;
roles can be conditional/hierarchical;
contribution can be indirect/aggregated;
```

B must attack the representation.

---

# 21. Candidate ParticipationAuthorityTopology

The strongest surviving object after A is not `Participant`.

It is closer to:

```text
ParticipationAuthorityTopology =
who/what occupies which Game-relative role at scope S and time t
+ which observations/proposals/actions/evaluations/rulings/changes
  that role may make
+ which of those are authoritative or merely advisory/evidential
+ how contributions aggregate/delegate/escalate/review
```

This is only a research candidate.

It may compress further into:

```text
Typed RoleAssignment relations
+ DomainAuthority
+ existing ControlContributionTopology
+ Adjudication process
```

If so, no new frozen contract is needed.

GDF3-B should try that compression first.

---

# 22. Adjudication and GameAction remain distinct

GDF1 already gives:

```text
Input/control evidence
→ ActionAttempt/CandidateAction
→ admission/current legality
→ ExecutedGameAction
→ consequence
```

GDF3-A does not duplicate this.

Instead it asks:

```text
who/what has authority over admission/classification/ruling,
under which evidence/rules/currentness?
```

Thus:

```text
GameActionContract != AdjudicationAuthorityTopology.
```

A Player may propose an action.
A resolver may deterministically admit it.
A GM may interpret an open-language proposal.
A referee may rule after an event.

All can use the same F1-F9 substrate while assigning decision authority differently.

No ACS-PRC is triggered.

---

# 23. Verification is not identical to live adjudication

A speedrun or tournament record can be checked after the original play episode.

The verifier may inspect:

```text
video/logs
hardware/software version
category rule set
input evidence
clock/timing evidence
prohibited techniques
```

and then determine whether a record claim is valid under a practice/category.

This can change:

```text
official record/history/recognition
```

without changing the historical executable state trajectory.

Therefore:

```text
WorldHistory != OfficialPracticeRecord by identity.
Verification != LiveGameActionResolution.
```

This connects GDF3 to the preserved Meta-Practice residual but does not force that whole continent into GDF3-A.

---

# 24. Social authority can differ from formal authority

TTRPG groups also pressure the assumption that formal GM/rules authority exhausts effective authority.

An experienced/dominant player may acquire socially recognized expert authority and influence rules interpretation or other players even without formal GM status.

R28/R15 already let us represent legitimacy/convention/social norm.

GDF3 implication:

```text
FormalRoleAuthority != EffectiveInfluence/Legitimacy by identity.
```

Do not silently promote social influence into authoritative Game truth.

But if the group/practice actually delegates adjudication to that player, the current authority relation must change explicitly.

This is another reason `role label` alone is insufficient.

---

# 25. Human/Agent symmetry is only partial

A synthetic system can occupy many Game-relative functional roles:

```text
Player
Coach
Referee/adjudicator
GM/facilitator
Director
Moderator
Verifier
```

provided the GamePractice/System grants the relevant authority.

But:

```text
SyntheticRoleOccupancy != subjective PlayExperience evidence.
```

GDF0's experiential boundary remains intact.

Likewise:

```text
Human occupant != legitimate authority automatically.
```

Authority derives from the GamePractice/Institution/Rule topology, not biological substrate.

---

# 26. Cross-regime matrix

| Regime | Ordinary Player action | Other constitutive role/function | Key GDF3-A pressure |
| --- | --- | --- | --- |
| solitary digital puzzle | Player | software resolver | causal system component need not be participant |
| livestream viewing | streamer Player | passive audience | observation alone does not fix role |
| APG | streamer/player + audience contributors | aggregation layer | spectator→causal participation without avatar control |
| football/sport | players | referee + assistant/VAR | rule/evidence/ruling authority separable |
| judged performance | performer | judges | evaluation authority separate from performance action |
| TTRPG | players | GM bundle | one named role combines several functions |
| coached competition | player/team | coach | indirect policy influence != direct action |
| speedrun | runner | verifier/category authority | cross-instance adjudication/record validity |
| MMO/live service | players | moderator/operator | platform/practice authority can become Game-constitutive |
| adaptive single-player game | Player | AI Director | Game adapts itself; director != Player |
| Human-Agent shared play | Human/Agent roles | shared control resolver | role != contribution share |
| Agent-Agent match | synthetic Players | software adjudicator | Human phenomenology not required for role |
| role-fused Agent system | Agent | player + adjudicator bundle | identity cannot detect authority conflict |
| runtime co-authoring | Player/Agent | rule/content-change authority | authorship can cross into current GameStructure |

No one categorical `participant hierarchy` fits all rows.

---

# 27. Strongest laws surviving GDF3-A

```text
Entity != Role != Subject != Player.

Participant is scope-qualified;
Participant != one entity kind.

Player != all causally relevant Game entities.

RoleLabel != ResponsibilityTopology.

One Entity can occupy multiple roles.
One named role can bundle multiple functions.
One function can be distributed across multiple entities/roles.

Observation != role identity.
Spectator != causal irrelevance by identity.
Audience != one Subject by identity.

InfluenceOnPlayerPolicy != direct GameAction authority.

Rule != Interpretation != Ruling != Enforcement != Review.

Evidence/recommendation authority != final ruling authority.

Game-internal causal function != Participant by identity.

SubjectLearning != GameAdaptation.

ProductionContribution != RuntimeParticipation.

Mediation != one mechanism.
```

These are GDF3-A research results, not yet the final GDF3 freeze contract.

---

# 28. Candidate deletions after A

The following candidates are **rejected now**:

```text
Participant as new primitive/entity kind
ParticipationRole as new semantic primitive
one universal Mediation construct
Audience as mandatory CollectiveSubject
RoleTransition primitive
RoleComposition primitive
```

Reasons:

```text
existing Role/Relation/Time/Authority semantics suffice,
or the term collapses several mechanisms.
```

---

# 29. Candidate survivors after A

Retain for deeper falsification:

```text
RoleCausalAccessProfile
ParticipationAuthorityTopology
GameConstitutiveRoleRelation
AdjudicationProcessFamily
```

But none is frozen.

In particular:

```text
ParticipationAuthorityTopology
```

may still turn out to be only a convenient projection over existing:

```text
RoleAssignment
+ DomainAuthority
+ ControlContributionTopology
+ Rule/Action contracts.
```

B must attack exactly that possibility.

---

# 30. Upstream reopen audit

## R29 / F1-F9

All GDF3-A cases remain representable through:

```text
Entity / Reference
State
Relation
Transition / Constraint
Time
Authority / Provenance
Observation / Representation
Evaluation / Motivation
Action / Capability / Policy / Control
```

No tenth coordinate is required.

```text
R29 FoundationReopenCondition = NOT TRIGGERED.
```

## GDF0

Participant/role distinctions cut across existing:

```text
GameStructure
Enactment
PlayBehavior/Experience
PlayPractice/GameCategory
External coupling
```

and use the existing EffectiveRuleTopology / constitutive-overlay logic.

No missing target level is forced.

```text
GDF0 PRC-2/3/6 = NOT TRIGGERED.
```

## GDF1

GDF3-A preserves:

```text
Input != GameAction != Outcome
ControlMapping
ControlLocus
ControlContribution attribution
```

Audience/shared control can reuse GDF1 rather than overwrite it.

```text
ACS reopen = NOT TRIGGERED.
```

## GDF2

Referee/judge/director roles can alter conditions/evaluation/challenge distributions, but GDF2's scoped Challenge/Failure/Mastery query contracts remain valid.

```text
CFM reopen = NOT TRIGGERED.
```

---

# 31. Novelty audit

Conservative classification:

## N0 — established external structure consumed

```text
referee/judge authority separation
GM multifunctionality
audience participation
experience management/adaptive game systems
```

These have substantial pre-existing literature/practice.

## N1 — Ordivon recombination / sharper separation

```text
Participant as scope-qualified descriptor rather than entity class
RoleLabel != ResponsibilityTopology
Game-internal causal component != Participant
```

These are strong internal compressions of existing ideas.

## N2 — potentially useful new synthesis

```text
ParticipationAuthorityTopology
as a single Game research projection spanning
player / spectator / judge / GM / operator / director / Agent role fusion
while keeping action, adjudication and authority typed separately.
```

This may be novel as an Ordivon synthesis, but no broad originality claim is made.

## N3

None claimed.

---

# 32. External evidence anchors used in GDF3-A

Representative anchors:

```text
Tychsen, Hitchens, Brolund & Kavakli (2005), The Game Master.
  GM functionality varies across role-playing platforms and combines several functions.

Tychsen et al. (2006), Live Action Role-Playing Games: Control, Communication,
Storytelling, and MMORPG Similarities.
  Large role-playing practices require multiple management/control functions.

Seering et al. (2017), Audience Participation Games: Blurring the Line Between Player and Spectator.
  Audience members can meaningfully affect gameplay; spectator/player boundary is design-variable.

Paliyawan et al. (2024), Audience participation fighting game.
  Audience cheer/jeer inputs dynamically alter AI strength in an APG.

Thue & Bulitko (2012), Procedural Game Adaptation.
  Running-game dynamics can be changed through an experience-management policy.

Thue & Bulitko (2018), Toward a Unified Understanding of Experience Management.
  Experience managers can be modeled as agents embedded in the running game.

IFAB Laws of the Game, Law 5 / Law 6 / VAR Protocol.
  Referee final authority is separated from assistant/VAR evidence and recommendation roles.

Dungeons & Dragons official Dungeon Master description.
  DM is described as narrator, rules referee and controller of characters/creatures.
```

These are pressure tests, not authorities over Ordivon terminology.

---

# 33. GDF3-A verdict

```text
GDF3-A = COMPLETE

Participant primitive/entity kind = REJECTED
ParticipationRole primitive = REJECTED
Mediation primitive = REJECTED
Collective Audience Subject requirement = REJECTED
RoleTransition/RoleComposition primitives = REJECTED

Player = RETAIN existing R29 boundary-role concept
R24 Role = RETAIN unchanged

RoleCausalAccessProfile = RETAIN as derived research view
ParticipationAuthorityTopology = RETAIN as research candidate
AdjudicationProcessFamily = RETAIN for deeper reconstruction
GameConstitutiveRoleRelation = RETAIN as GDF0-derived test

R29/F1-F9 reopen = NO
GDF0 reopen = NO
GDF1 reopen = NO
GDF2 reopen = NO
```

The important change in our world model is:

```text
Old implicit picture:
Player ↔ Game
with other people/systems as secondary context.

After GDF3-A:
GamePractice / GameStructure
is surrounded and sometimes constituted by a typed topology of
occupants, roles, responsibilities and scoped authorities.

Player is one special boundary role inside that topology,
not the universal template for every causally relevant participant.
```

---

# 34. Exact next round

The surviving uncertainty is now narrower than GDF3-A.

Next:

```text
GDF3-B — Participation Topology / Authority Decomposition
```

Primary attack:

> Can every surviving GDF3 distinction be represented cleanly as existing R24 `RoleAssignment` + F6 `DomainAuthority` + GDF1 contribution/action contracts + a small Adjudication process view, making `ParticipationAuthorityTopology` only a derived convenience? Or do materially different GameForms force an independent Game-owned responsibility contract?

B should stress at least:

```text
role scope/currentness
conditional authority
delegation
aggregation
assistance vs final authority
role conflict / separation of authority
rule-change vs case-ruling authority
live vs post-hoc verification
practice-level vs GameInstance-level authority
human/synthetic interchangeability
```

No GDF3 foundation object should freeze before that attack.
