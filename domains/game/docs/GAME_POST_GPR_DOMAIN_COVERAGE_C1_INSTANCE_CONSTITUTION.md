---
schema_version: 1
id: game.post-gpr-domain-coverage.c1-instance-constitution
title: Ordivon Game — Fresh Coverage C1: GameInstance Constitution / Participation Lifecycle Falsification
profile: research
lifecycle: active
source_role: research
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Fresh post-GPR whole-Game coverage subround attacking the newly discovered GameInstance constitution / encounter assembly / participation lifecycle candidate. Cross-regime falsifiers show that instance existence, participant presence, participant membership, role occupancy, continuation, termination and restart are distinct. Most candidate nouns reduce to F1-F9, GDF0 GameInstance, R23/R24 currentness/identity and GPR1/GPR6 role/participation views, but one Game-owned downstream responsibility remains: keeping constitution basis, current participation composition and instance-continuity boundary jointly queryable. This does not reopen GDF0 and does not admit GDF4/GPR8; it promotes C1 only to a strong foundation-unclosed candidate pending comparison against the rest of the fresh coverage map.
evidence_status: strong-local
readiness: C1_FALSIFICATION_COMPLETE_ROUTE_NOT_SELECTED
applies_to:
  - ordivon-game
related:
  - game.play-game-deep-foundations.v1
  - game.practical-concept-reconstruction.gpr1
  - game.practical-concept-reconstruction.gpr6
  - game.practical-concept-reconstruction.gpr0-gpr7-final-closeout-handoff
---
# Ordivon Game — Fresh Coverage C1: GameInstance Constitution / Participation Lifecycle Falsification

## 0. Boundary

This is **not GDF4** and **not GPR8**.

The fresh whole-Game search identified an outside-residual candidate:

```text
C1 — GameInstance Constitution / Encounter Assembly / Participation Lifecycle
```

The task of this subround is deliberately destructive:

```text
try to reduce C1 completely into
F1-F9
+ GDF0 GameInstance / GameStructure / EffectiveRuleTopology
+ R23 Time
+ R24 Identity / continuity
+ GPR1 RoleAssignment / authority
+ GPR6 ParticipantView
```

Only a recurrent Game-owned obligation that survives those reductions may remain as a candidate downstream foundation responsibility.

Frozen state remains:

```text
R1-R29 / F1-F9 = frozen
GDF0-GDF3       = frozen
R0/GPR1-GPR7    = completed research history

NextGPR            = UNKNOWN
NextPracticalRoute = UNKNOWN
NextFoundation     = UNKNOWN
```

---

# 1. The initial candidate was too broad

The first rough vocabulary included:

```text
session
lobby
roster
matchmaking
encounter assembly
participation admission
start
join / leave
substitution
drop-in / drop-out
forfeit / surrender
abandonment
termination
restart
instance continuity
```

This list is intentionally **not** preserved as ontology.

Several terms immediately fail universality:

```text
Lobby       = implementation/practice mechanism, not required by all GameForms.
Matchmaking = one source of composition, not instance identity.
Roster      = useful in some team/institutional games, absent in many solitary/open games.
Session     = may contain zero, one or many GameInstances; one GameInstance may cross sessions.
Presence    = not necessary for a constituted GameInstance to have begun.
StartEvent  = regime-specific; clock start, kick-off, first turn, authoritative creation and other mechanisms differ.
```

So C1 is not a missing noun family.

The real candidate must be expressed as responsibility.

---

# 2. Why GDF0 does not already close the problem

GDF0 freezes:

```text
GameInstance
= one concrete enactment/history under an effective GameStructure.
```

That successfully separates:

```text
GameStructure != GameArtifact != GameInstance != GameCategory
```

But this definition does not itself answer:

```text
What makes this concrete enactment authoritative/current?
Which participants/roles/configuration constitute it now?
Can a participant be absent but still bound to the instance?
When may a participant leave while the instance survives?
When does replacement preserve the instance?
When does interruption preserve the instance?
When does a restart terminate the old instance and create another?
What source decides that boundary?
```

This is explanatory/responsibility depth over an existing target, not evidence for a new GDF0 target level.

---

# 3. Falsifier family A — constitution is not physical presence

## C1-F1 — FIDE scheduled start with absent player

Hold fixed:

```text
players assigned
board/rules/event
scheduled start time
```

Vary:

```text
one player's physical presence at the board.
```

FIDE competitive rules start White's clock at the determined start time; event default-time rules then govern late arrival/loss.

Therefore:

```text
PhysicalPresenceAtStart
!= GameInstanceExistenceByIdentity.
```

A GameInstance may be constituted by practice/event assignment + authoritative start semantics even while one participant is not currently present/acting.

Reduction:

```text
presence      -> World/observation state
player binding -> relation/role/practice assignment
start currentness -> Time + Authority
```

No new primitive survives.

But a query over only `currently present entities` would reconstruct the wrong instance constitution.

---

# 4. Falsifier family B — pre-instance eligibility is not current membership

## C1-F2 — football named substitutes

Current football rules distinguish:

```text
named player
named substitute
substitute not named before the match
outside agent
```

and a substitute not named by the required time may not participate in the match.

Thus:

```text
EligibleForPossibleParticipation
!= CurrentPlayerMembership
!= PhysicalPresence
!= OutsideAgent.
```

GDF3 may determine a disputed eligibility status.
GPR1 may represent role/authority relations.
But neither one alone states which admitted participation basis belongs to this instance.

The distinction is Game-local because it changes who may enter this exact enactment.

---

# 5. Falsifier family C — membership can change while instance identity remains

## C1-F3 — football substitution

Football gives a sharp transition boundary:

```text
substitute enters
→ replacement completes
→ former substitute becomes player
→ replaced player becomes substituted player
```

The match remains the same match.

Therefore:

```text
ParticipantSetContinuity
!= GameInstanceIdentity.
```

and:

```text
RoleOccupantContinuity
!= GameInstanceIdentity.
```

This is already compatible with GPR1:

```text
RoleContinuity != OccupantContinuity.
```

The new residual is not a `Substitution` primitive. It is the GameInstance-level consequence of that change:

```text
which composition transition preserves the same instance,
and what Game-local state/rights/history follow the transition?
```

---

# 6. Falsifier family D — minimum composition can be a continuation condition

## C1-F4 — football minimum player threshold

Football can prohibit a match from starting or continuing below a minimum team size; current rules also distinguish temporary off-field cases from true loss of sufficient players.

This falsifies:

```text
OnceStarted -> AlwaysSameInstanceUntilOrdinaryOutcome
```

and:

```text
ParticipantDeparture = merely local actor state
```

because composition itself can become a condition on whether the GameInstance remains continuable.

But the numeric threshold is obviously owner-local:

```text
seven players in football
!= universal Game threshold.
```

So no `MinimumParticipantCount` primitive survives.

What survives is a conditional relation:

```text
CurrentConstitution
→ InstanceContinuationDisposition
```

under effective Game/Practice authority.

---

# 7. Falsifier family E — departure need not terminate the instance

## C1-F5 — multiplayer Magic player leaves

Current Magic rules explicitly allow multiplayer games to continue after one or more players leave.

Leaving also has immediate causal consequences:

```text
owned objects leave
control effects end
some objects cease/exile
priority/turn handling changes
```

Therefore:

```text
ParticipantDeparture
!= GameInstanceTerminationByIdentity
```

and more strongly:

```text
MembershipTransition
can rewrite current Game state/topology
while preserving GameInstance identity.
```

This is more than a roster display concern.

A useful model must be able to relate:

```text
membership transition
→ current participants/roles
→ surviving state/ownership/control consequences
→ same-instance continuation.
```

The lower object/control effects remain ordinary GameStructure transitions; the constitution layer need only retain their participation/continuity significance.

---

# 8. Falsifier family F — a player can end their participation but not necessarily the whole game

## C1-F6 — concession / team semantics

Magic permits a player to concede at any time; that player immediately leaves. In multiplayer team variants, team/game termination depends on the variant and remaining team members.

Thus:

```text
IndividualParticipationEnd
!= GameInstanceEnd
```

and:

```text
IndividualOutcome
!= TeamOutcome
!= InstanceOutcome.
```

GDF2 already protects failure/outcome attribution from this collapse.
C1 adds no new outcome primitive.

It does show that one instance lifecycle can contain participant-local terminal events before instance-global terminality.

---

# 9. Falsifier family G — interruption can preserve instance identity

## C1-F7 — adjourned chess game

FIDE's adjournment rules preserve enough state to resume:

```text
position
clock times
sealed move / move relation
player identity
```

A period with no active enactment therefore need not terminate the GameInstance.

Freeze the negative law:

```text
ContinuousRuntimeOrContinuousPresence
!= necessary for GameInstance continuity.
```

This also prevents Runtime process identity from becoming GameInstance identity.

---

# 10. Falsifier family H — inability to restore constitutive state can force new instance

## C1-F8 — chess resumption failure

FIDE's adjournment procedure distinguishes:

```text
restorable position/history
→ continue the game
```

from:

```text
position cannot be re-established
→ game annulled
→ new game played
```

This is one of C1's strongest tests.

It proves:

```text
same players
+ same competition
+ same rules
+ intended continuation
```

do not by themselves force:

```text
same GameInstance.
```

A GamePractice can require preservation/reconstruction of specified constitutive state/history for instance continuity.

The exact required state is regime-local.
The existence of an authoritative continuity boundary is recurrent.

---

# 11. Falsifier family I — explicit restart can create a new GameInstance despite material continuity

## C1-F9 — Magic restart

Current Magic rules state that when a game is restarted:

```text
the current game immediately ends
remaining players begin a new game
```

while some game materials can be carried into the new game under the restart procedure.

Therefore:

```text
MaterialContinuity
!= GameInstanceIdentity
```

and:

```text
ParticipantContinuity
!= GameInstanceIdentity.
```

This is exactly the kind of case R24's general identity discipline predicts, but Game needs a local answer to:

```text
which transition is same-instance continuation
versus new-instance creation.
```

---

# 12. Falsifier family J — online backfill makes membership lifecycle a real runtime concern

## C1-F10 — join-in-progress / backfill

Current Unity Matchmaker documentation explicitly supports:

```text
start before all desired players are present
players leave after start
new compatible players join an already-started match
server updates the backfill membership state
```

This is implementation evidence, not semantic authority.

It demonstrates that real online GameForms require a lifecycle where:

```text
server/session continuity
membership continuity
GameInstance continuity
```

must not be assumed identical.

Game owns the semantic question:

```text
Does this admitted late participant become part of the same GameInstance,
with what initial state/history/access/obligations?
```

Runtime/Network/Matchmaker own the delivery mechanism.

---

# 13. Falsifier family K — synthetic composition is not a new instance primitive

## C1-F11 — Human/synthetic population composition

Current online games can place bots and Humans in the same broad matchmaking regime; current Fortnite support explicitly states that bot encounters can vary with skill-based matchmaking.

This pressures composition because:

```text
same mode / same rules
+ different Human/synthetic participant composition
→ different concrete encounter.
```

But it does **not** require:

```text
SyntheticParticipant primitive
AgentGameInstance primitive
AI-native instance type.
```

GPR6 already gives:

```text
Player != Human
Player != Agent
ControlPrincipal != RealizationSubstrate
```

So Agent era changes composition topology, not the semantic substrate.

---

# 14. Falsifier family L — role fusion/replacement is not instance constitution by itself

## C1-F12 — Human/Agent/GM/controller replacement

Consider one slot/role across three variants:

```text
Human occupant
Agent occupant
Human+Agent shared realization
```

If effective Game/Practice authority treats the role assignment as a legal replacement inside the same instance, provider/substrate identity alone does not create a new GameInstance.

If practice rules instead require a fresh start after replacement, the same physical substitution creates a new instance.

Therefore:

```text
OccupantOrProviderChange
!= GameInstanceChangeByIdentity.
```

C1 must consume explicit owner-local continuity semantics rather than infer them from Human/Agent labels.

---

# 15. Candidate deletion pass

## Delete `Session`

A session may contain multiple games.
An adjourned game may span multiple sessions.
A persistent world may have no useful session boundary.

```text
Session != GameInstance.
```

Verdict: engineering/practice vocabulary only.

## Delete `Lobby`

Solitary board games, sports and direct-start systems need none.

Verdict: engineering/UI mechanism.

## Delete `Roster` as universal source

Some games have named rosters; others have dynamic/open participation or one participant.

Verdict: local source/view when useful.

## Delete `Matchmaking`

Self-selection, tournament pairing, manual seating, random allocation and persistent-world entry all produce constitution without one matchmaking mechanism.

Verdict: Population/Network/engineering cross-cutting mechanism.

## Delete `Presence`

FIDE absence case falsifies identity.

Verdict: World/observation state consumed by local rules.

## Delete universal `StartEvent`

Different practices start by clock, action, signal, authoritative creation or other condition.

Verdict: owner-local transition/currentness.

## Delete universal `TerminationReason` enum

Win, loss, resignation, forfeit, abandonment, disconnection, invalid constitution, restart and external authority are not one closed list across GameForms.

Verdict: open owner-local reasons over a generic lifecycle disposition.

---

# 16. What survives reduction

After deleting the candidate nouns, C1 still leaves one recurrent responsibility family:

```text
GameInstanceConstitutionResponsibility
```

This is **not frozen** and the name is provisional.

It asks a Game owner to keep three things jointly resolvable when they materially matter.

## Obligation A — Constitution Basis / Currentness

For this concrete instance:

```text
which GameStructure / rule-practice configuration applies?
which initial/current constitutive state matters?
which participation/role assignments or admission bases bind?
which authority/currentness makes those facts operative?
```

This is not a demand for one stored `InstanceManifest`.
It is an information responsibility over heterogeneous owner-local sources.

## Obligation B — Participation Composition / Transition

At the queried time/scope:

```text
who/what is admitted or bound to the instance?
which roles/teams/seats/control principals are current?
who is active / absent / departed / substituted where such distinctions matter?
which transition changed composition?
```

Again:

```text
ParticipantView can be a derived consumer,
not the source of constitution truth.
```

## Obligation C — Instance Continuity Boundary

For a relevant change/interruption/restart:

```text
does the same GameInstance continue?
end normally?
end by resignation/forfeit/abandonment?
become non-continuable?
get annulled?
restart as a new GameInstance?
remain unresolved pending authority?
```

with source/authority/currentness/provenance sufficient to explain the answer.

This obligation is the strongest residual produced by C1.

---

# 17. Why the three obligations must stay linked

A model with only current participants cannot distinguish:

```text
late but still bound player
vs
never-admitted outsider.
```

A model with only RoleAssignment cannot distinguish:

```text
role replacement inside same instance
vs
replacement requiring new instance.
```

A model with only GameState cannot distinguish:

```text
restored state of the same adjourned game
vs
a copied state used to begin a new game.
```

A model with only GDF3 determination cannot distinguish:

```text
a binding eligibility ruling
vs
the downstream constitution transition that actually admits/rejects participation.
```

Therefore the surviving value is not a new atom.
It is a Game-owned **joint responsibility boundary**.

---

# 18. Relation to existing frozen work

## GDF0

Owns the target:

```text
GameInstance
```

C1 deepens its constitution/continuity mechanics.
It does not add a target beyond structure/enactment/practice/category/external coupling.

## R23 Time

Supplies:

```text
start/end/currentness
interruption/resumption
temporal mapping
```

but temporal relation alone does not decide GameInstance identity.

## R24 Identity

Supplies the generic discipline:

```text
continuity is authority/domain-relative
```

C1 is the Game-specific consumer for `GameInstance` identity/continuity.

## GPR1

Supplies:

```text
RoleAssignmentRecord
role currentness
replacement receipts
authority views
```

but a role lifecycle is not GameInstance lifecycle.

## GPR6

Supplies:

```text
ParticipantView(entity, scope, currentness)
```

but the view is intentionally derived and cannot become the source of instance constitution.

## GDF3

Supplies authoritative status when a disputed/official eligibility, record or case determination exists.

But:

```text
AuthoritativeEligibilityStatus
!= downstream participation admission/constitution transition by identity.
```

---

# 19. Ownership boundary

## Game owns

```text
which facts constitute the current concrete GameInstance
which participation transitions alter current Game-relative composition
which transitions preserve/end/restart/annul the GameInstance
Game-local consequences of joining/leaving/substitution where constitutive
```

## Runtime / Network owns

```text
process/session/socket/server identity
transport disconnect/reconnect
backfill service mechanics
technical session recovery
```

A server can survive while a GameInstance ends.
A GameInstance can survive while a process/session ends.

## Social / Institution owns

```text
external registration status
league membership
credential legitimacy
broader organizational standing
```

Game consumes these only where they affect current instance admission/constitution.

## World owns

```text
physical presence
material reality
underlying event facts
```

## Human owns

```text
intent to participate
experience of joining/leaving
social/affective cost
```

## GDF3 case determination owns

```text
binding case status when the participation/eligibility question itself crosses CaseDeterminationBoundary
```

C1 consumes the resulting status into instance constitution when required.

---

# 20. Foundation reopen audit

## GDF0 PRC-2 — missing target class

Not triggered.

C1 does not require a level beyond:

```text
GameStructure / Artifact
GameInstance / Enactment / Practice
Participant experience
Category / external coupling
```

It deepens the already-existing GameInstance target.

## GDF0 PRC-3 — rule/authority failure

Not triggered.

All observed constitution cases remain representable through F1-F9 + EffectiveRuleTopology + owner-local authority/currentness.

## GDF0 PRC-6 — Agent-era primitive failure

Not triggered.

Human/synthetic substitution and mixed populations require explicit role/control/provenance relations, not a new primitive.

## GDF0 PRC-7 — downstream contradiction

Not triggered.

No frozen GDF0 law is contradicted.

## GDF1/GDF2/GDF3

No reopen condition is triggered.

C1 consumes their contracts without falsifying them.

---

# 21. Is this practical reconstruction already?

Not yet.

It would be premature to stabilize objects such as:

```text
GameInstanceManifest
RosterRecord
ParticipationAdmissionRecord
SessionLifecycleRecord
SubstitutionRecord
InstanceTerminationRecord
```

because C1 has only now established the residual responsibility.

Before practical reconstruction, we still need to know whether:

```text
1. this responsibility remains independently useful after comparison with Population/Matching, Meta-practice and GameStructure lineage;
2. a minimal foundation contract can be frozen without hiding owner-local constitution semantics;
3. real consumers need one shared practical projection rather than local implementations.
```

Therefore:

```text
C1 != newly admitted GPR cluster.
```

---

# 22. Is this a genuine foundation-level residual?

Current verdict:

```text
YES — strong candidate at responsibility level,
NO  — not yet an admitted numbered Foundation.
```

Why it survives:

```text
cross-regime recurrence = strong
counterfactual leverage = strong
Game ownership          = strong
reduction to one old practical view = fails
new F1-F9 primitive     = not required
upstream reopen         = not required
cheap falsifiers        = strong
Agent-era leverage      = real but non-exclusive
```

The surviving object is not:

```text
Session
Roster
Lobby
Matchmaking
Presence
```

but approximately:

```text
GameInstance Constitution / Continuity Responsibility
```

This has the same methodological shape as other downstream Deep Foundations:

```text
existing semantic coordinates
+ recurrent Game-owned distinctions that must remain jointly queryable
!= new primitive ontology.
```

---

# 23. Agent-era result

Agent era amplifies C1 in three ways.

## Synthetic participant substitution

A Human can be replaced by an Agent or vice versa without provider identity being instance identity.

## Synthetic population assembly

Matchmaking/directors can vary Human/bot/Agent composition per instance.

## Role-realization split

One semantic participant/Player role can be realized by:

```text
Human
Agent
policy
shared Human-Agent controller
```

without changing role identity automatically.

Thus Agent era reinforces:

```text
ParticipantIdentity
!= HumanIdentity
!= AgentIdentity
!= RealizationSubstrate
!= GameInstanceIdentity.
```

It does not trigger a new semantic primitive.

---

# 24. Practical consequences if this survives later comparison

Possible future derived views **only if later admitted** might include:

```text
InstanceConstitutionView
ParticipationLifecycleView
InstanceContinuityDiagnostic
```

They would likely consume:

```text
GameStructure/current ruleset refs
initial/current constitutive state refs
RoleAssignments
ParticipantView
team/seat/slot relations
admission/determination refs
join/leave/replacement transitions
termination/restart refs
currentness/provenance
```

Default should remain:

```text
derive, do not create a second instance truth store.
```

But this is explicitly future practical speculation, not a contract from this round.

---

# 25. C1 final verdict

```text
C1 falsification / reduction pass = COMPLETE

Session primitive                 = REJECTED
Lobby primitive                   = REJECTED
Roster primitive                  = REJECTED
Matchmaking primitive             = REJECTED
Presence-as-membership            = REJECTED
ParticipantSet=InstanceIdentity   = REJECTED
ContinuousRuntime=InstanceIdentity= REJECTED
ParticipantContinuity=InstanceIdentity = REJECTED
MaterialContinuity=InstanceIdentity    = REJECTED

GameInstance Constitution / Continuity Responsibility
= SURVIVES as strong foundation-unclosed candidate

new F1-F9 primitive = NO
GDF0 reopen         = NO
GDF1 reopen         = NO
GDF2 reopen         = NO
GDF3 reopen         = NO
GPR8 admitted       = NO
new numbered GDF    = NO
```

Classification update:

```text
C1:
  from genuinely-new-continent candidate
  → strong genuinely-new-foundation-or-domain-continent candidate
    at downstream responsibility level
```

The whole fresh coverage search is still open.

C1 does **not** win the next route merely because it survived its own test.

---

# 26. External evidence anchors

This round used external anchors only as cross-regime falsifiers; Ordivon semantics remain derived from the comparative analysis rather than copied from any one ruleset or implementation.

Representative primary/current sources:

```text
IFAB — Laws of the Game 2026/27, Law 3 The Players and Law 7 Duration/Abandonment.
FIDE Rules Commission — FIDE Laws of Chess, current published rules; start/default time, resignation and adjournment/resumption rules.
Wizards of the Coast — Magic: The Gathering Comprehensive Rules effective 2026-08-07; Starting the Game, Ending the Game, Multiplayer leaving, Restarting the Game.
Unity Multiplayer Services — Matchmaker Backfill documentation; join-in-progress and replacement after players leave.
Epic Games — Fortnite matchmaking support; skill-based matchmaking includes bot encounters.
Best, Lucas & Gaina (AIIDE 2024) — Game Master AI as an asymmetric/semi-cooperative player-role pressure case.
```

---

# 27. Frontier after C1

Preserve without route selection:

```text
C1 GameInstance Constitution / Continuity = strong foundation-unclosed candidate
C2 Cross-instance Evaluation / Comparability = unresolved cross-cutting/practical candidate
Dynamics / Emergence = foundation-unclosed
Meta-practice / Extended Apparatus = foundation-unclosed
Population / Matching = foundation-unclosed/cross-owner
Adaptive Experience Management = foundation-unclosed
GameStructure lineage/versioning = partial/cross-cutting
Integrity / cheating / exploit = unresolved cross-cutting
other unknown continents = still open
```

Canonical continuation remains:

```text
map first
compare survivors
select last
```
