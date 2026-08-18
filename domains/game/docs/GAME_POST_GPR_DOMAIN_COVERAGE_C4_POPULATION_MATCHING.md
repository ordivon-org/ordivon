---
schema_version: 1
id: game.post-gpr-domain-coverage.c4-population-matching
title: Ordivon Game — Fresh Coverage C4: Population / Matching / Play-Opportunity Formation Falsification
profile: research
lifecycle: active
source_role: research
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Fresh post-GPR destructive pass over population ecology, queue availability, pairing, matchmaking, team formation and synthetic population assembly. Population supply is causally real because it changes which play opportunities and opponent/team configurations are reachable, but matching is a heterogeneous owner-local selection mechanism rather than a Game primitive. After subtracting C1 GameInstance constitution, GDF0 PlayPractice/EffectiveRuleTopology, R19 strategic/team relations, R22 fairness, GDF2 opponent-condition challenge scope, GPR6 Human/Agent participation distinctions, Network queue/latency capacity, Social/Institutional population membership, and general matching/mechanism-design theory, no independent Game foundation responsibility survives. A PlayOpportunityFormationView / MatchFormationDiagnostic remains a strong cross-cutting practical/research abstraction that explicitly separates candidate supply, eligibility/constraints, selection objective/policy, proposal/selection, and downstream C1 constitution. No GDF4/GPR8 or engineering route is admitted.
evidence_status: strong-local
readiness: C4_REDUCED_NO_NEW_FOUNDATION_ROUTE_NOT_SELECTED
applies_to:
  - ordivon-game
related:
  - game.post-gpr-domain-coverage.c1-instance-constitution
  - game.post-gpr-domain-coverage.c2-evaluation-comparability
  - game.post-gpr-domain-coverage.c3-dynamics-emergence
  - game.play-game-deep-foundations.v1
---
# Ordivon Game — Fresh Coverage C4: Population / Matching / Play-Opportunity Formation Falsification

## 0. Boundary

This is not GDF4 and not GPR8.

C4 attacks the historical residual:

```text
population size/composition
queue/time-zone availability
rating distribution
role scarcity
party/network structure
migration/churn
smurf/bot prevalence
matchmaker policy
opponent/team diversity
pairing
team formation
backfill
```

The null model is deliberately broad:

```text
C4
= external/social population state
+ Network/queue/latency availability
+ GamePractice / EffectiveRuleTopology
+ R19 relation/team/competition semantics
+ R22 fairness semantics
+ GDF2 opponent/team-conditioned challenge
+ GPR6 participation/control-realization distinctions
+ general matching / mechanism-design / queueing theory
+ C1 GameInstance constitution after selection becomes operative.
```

The question is not whether population matters.
It does.

The question is whether Game owns another irreducible foundation responsibility between population supply and concrete GameInstance constitution.

---

# 1. First correction — Population is causally real

Old H4 correctly observed:

```text
same local rules
+ same focal player capability
+ different available population
→ different reachable play.
```

An empty queue can prevent a PvP encounter entirely.
A thin population can force wide skill bands.
Role scarcity can block a role-constrained team.
A synthetic filler can make an otherwise unavailable encounter possible.

Therefore:

```text
PopulationAvailability
is not merely analytics metadata.
```

But causal relevance does not yet establish a Game foundation.

---

# 2. Candidate deletion pass

## Population primitive

Population is a scoped collection/distribution of entities or participation candidates.
It exists in ecology, markets, networks, institutions and social systems.

Delete as Game primitive.

## Queue primitive

A queue is an operational scheduling/availability mechanism.
Many physical/tabletop/persistent GameForms have none.

Delete as Game primitive.

## Matchmaking primitive

The word covers very different mechanisms:

```text
player ↔ player
team ↔ team
player ↔ level/content
party ↔ party
role-constrained team assembly
manual/tournament pairing
backfill into running match
```

Delete universal ontology.

## Pool primitive

A pool is one implementation/practice grouping of candidates.
Delete as universal Game source.

## RatingBand primitive

One matching criterion among many; rating itself is model-relative from C2.
Delete as foundation.

## FairMatch primitive

Fairness can mean procedural fairness, equalized win probability, role equity, latency parity, resource symmetry or other owner-local criteria.
EOMM also demonstrates that engagement can be optimized instead of equal-skill fairness.

Delete universal `Good/FairMatch` foundation.

## TeamFormation primitive

Team formation is a generic matching/mechanism-design problem across domains.
Game supplies team semantics and constraints.
Delete as Game primitive.

## SyntheticPopulation primitive

Human/bot/Agent identity is already separated by GPR6.
Delete Agent-era population kind.

---

# 3. Falsifier A — empty queue changes play without changing GameStructure

## C4-F1 — population availability

Hold fixed:

```text
GameStructure
focal player
focal player capability
matching policy
network quality per candidate
```

Vary only:

```text
compatible candidate supply.
```

One region/time produces a match; another cannot.

Therefore:

```text
SameGameStructure
!= SameAvailablePlayOpportunitySet.
```

This establishes a real availability layer.

But candidate supply is not uniquely Game-owned: it is a population/resource/availability fact consumed by the GamePractice.

---

# 4. Falsifier B — same population, different pairing rules, different opponents

## C4-F2 — FIDE Swiss pairing

Current FIDE Swiss systems can constrain pairing using:

```text
score groups
prior encounters
colour history/preferences
float history
bye history
competition-specific team ordering
```

Hold the tournament participants/results fixed and change the admitted pairing procedure or criteria ordering.
Different legal pairings can result.

Therefore:

```text
PopulationState
!= PairingByIdentity
```

and:

```text
Pairing
= current practice policy over candidate relations.
```

This is already expressible through EffectiveRuleTopology + relations/history/currentness.

---

# 5. Falsifier C — unmatched participant need not leave the larger GamePractice

## C4-F3 — pairing-allocated bye

In Swiss systems an odd candidate count can produce a participant with:

```text
no opponent
no game colour
```

while the tournament practice may still award a declared bye result/points and preserve tournament participation.

Therefore:

```text
UnmatchedThisRound
!= NotParticipantInPractice
!= RemovedFromPopulation.
```

This is a strong anti-collapse between:

```text
practice membership
round opportunity
concrete GameInstance participation.
```

GDF0 PlayPractice and C1 GameInstance constitution already provide the needed levels.

---

# 6. Falsifier D — team pairing is distinct from team internal constitution

## C4-F4 — team tournament pairing

Current FIDE team pairing rules explicitly allow competition-specific handling of team strength and note that team members can be substituted or shifted between boards.

Thus:

```text
TeamPairedAgainstOpponent
!= FinalBoardOrRoleCompositionByIdentity.
```

Pairing can select team-vs-team opportunity while local/team practice later determines internal lineup/board allocation.

C1 owns the concrete instance composition boundary; C4 does not need a new team-instance primitive.

---

# 7. Falsifier E — match proposal is not GameInstance constitution

## C4-F5 — Open Match MatchFunction

Open Match defines a Match Function as logic that:

```text
queries tickets from pools
applies a MatchProfile / criteria
returns match proposals/results.
```

The proposal is still part of matchmaking orchestration.
A Director subsequently assigns tickets to a game server/connection target.

Therefore:

```text
MatchProposal
!= GameInstanceConstitutionByIdentity.
```

This maps cleanly onto C1:

```text
candidate/proposal selection
→ admitted downstream constitution basis if current GamePractice accepts it
→ concrete GameInstance.
```

---

# 8. Falsifier F — multiple overlapping proposals can exist before selection

## C4-F6 — proposal collision/evaluation

Open Match 1 explicitly supported multiple MatchFunctions producing overlapping proposals containing the same ticket; an Evaluator selected non-overlapping result Matches. Open Match 2 moved collision resolution responsibility into developer matchmaker code rather than treating one framework policy as universal.

Therefore:

```text
CandidateProposalMembership
!= FinalSelectedOpportunityByIdentity
```

and the resolution policy is owner-local.

This is strong evidence against `Match` as one universal source-of-truth object before constitution.

---

# 9. Falsifier G — there is no universal objective called good matchmaking

## C4-F7 — fairness vs engagement

EOMM explicitly challenges the assumption that equal-skill/fair matchmaking always optimizes player engagement and formulates matchmaking under a different objective.

Therefore:

```text
EqualSkill
!= GoodMatchByIdentity
```

and:

```text
MatchQuality
is objective-relative.
```

C2 already established the general comparison/evaluation discipline.
C4 consumes an explicit selection objective; it does not create one universal metric.

---

# 10. Falsifier H — team formation has generic mechanism-design structure

## C4-F8 — preference/welfare/equity team formation

General team-formation research studies mechanisms over:

```text
agent preferences
incentive compatibility
social welfare
fairness/equity
coalition structure
```

without requiring Game semantics.

Therefore the core team-formation optimization problem is cross-domain.

Game owns:

```text
team roles
legal composition constraints
Game-relative objectives
```

not a universal theory of matching agents into groups.

---

# 11. Falsifier I — network latency can dominate otherwise valid matching

## C4-F9 — skill-equivalent but network-incompatible candidates

Hold fixed:

```text
skill/rating compatibility
Game roles
player preferences
```

vary:

```text
latency/region/connectivity/capacity.
```

A technically poor or unreachable encounter may be rejected despite excellent Game-side fit.

Therefore:

```text
GameMatchCompatibility
!= NetworkFeasibility.
```

Network owns the transport/capacity truth.
Game/match policy may consume it as a criterion.

No Game foundation should absorb Network feasibility.

---

# 12. Falsifier J — party/social structure can constrain matching without becoming Game identity

## C4-F10 — premade party / social grouping

A set of participants may request or require joint placement.

The relevant facts can include:

```text
party membership
friend/social relation
shared preference
team constraint
```

These relations influence candidate grouping but do not define Player/GameInstance identity.

Thus:

```text
PartyMembership
!= TeamRoleByIdentity
!= GameInstanceMembershipByIdentity.
```

Social/Practice relation + matching policy + downstream C1 is sufficient.

---

# 13. Falsifier K — role scarcity is a constraint, not a new population ontology

## C4-F11 — tank/healer/DPS-style constrained assembly

Open Match examples permit separate pools/filters for roles, demonstrating the common case where candidate supply is partitioned by Game-specific role requirements.

If one required role has no candidate, formation may fail despite many total queued players.

Therefore:

```text
PopulationCount
!= FeasibleTeamFormationByIdentity.
```

But the residual is simply:

```text
candidate supply
+ GameStructure role/composition constraint
+ matching mechanism.
```

No `RolePopulation` primitive is needed.

---

# 14. Falsifier L — Human/bot/Agent filler changes availability, not semantic substrate

## C4-F12 — synthetic filler

A bot or Agent can:

```text
fill an opponent slot
fill a team role
backfill a departed participant
create a synthetic-only population.
```

This may radically alter play availability.

But GPR6 already freezes:

```text
Player != Human
Player != Agent
ControlPrincipal != RealizationSubstrate.
```

C1 already handles admitted composition/substitution.

Thus:

```text
SyntheticPopulation
!= new Game foundation kind.
```

Agent era changes supply/composition economics, not the basic ontology.

---

# 15. Falsifier M — the word matchmaking is polysemous even inside games

## C4-F13 — Foldit player-level matchmaking

Foldit research calls player-to-level selection `player-level matchmaking` and uses player/level ratings to choose content suited to the player.

This is not player-vs-player population matching at all.
It is a Dynamic Difficulty / content-selection mechanism.

Therefore:

```text
MatchmakingLabel
!= ParticipantPopulationMechanismByIdentity.
```

This is a strong term-separation result.

The player↔content case belongs primarily to Adaptive Experience / GDF2 challenge selection rather than C4 population formation.

---

# 16. Falsifier N — persistent/open worlds can have population causality without discrete matching

## C4-F14 — open-ended persistent co-presence

A persistent world may have:

```text
population density
migration
faction distribution
time-zone effects
local role scarcity
```

that change reachable interaction without any discrete queue or matchmaker producing `matches`.

Therefore:

```text
PopulationCausality
!= MatchmakingNecessity.
```

This kills any foundation centered on the implementation noun `matchmaker`.

Population remains an external/current practice condition consumed by Game semantics.

---

# 17. Falsifier O — population drift changes challenge/evidence scope

## C4-F15 — opponent distribution shift

Hold nominal mode/rules fixed while the active opponent population shifts:

```text
novice-heavy
expert-heavy
bot-heavy
one-strategy dominated
diverse/nontransitive.
```

The focal player's expected challenge and performance evidence can change.

Therefore:

```text
SameModeLabel
!= SameOpponentConditionDistribution
!= SameChallengeAssessment.
```

But GDF2 already explicitly scopes challenge/mastery to opponent/team conditions and treats opponent-distribution changes as transfer questions.

No new C4 foundation remains here.

---

# 18. Falsifier P — smurf/bot prevalence is partly integrity/identity, not generic matching

## C4-F16 — population representation quality

Suppose matchmaking consumes a claimed rating/identity while participants strategically misrepresent skill or use prohibited automation.

The resulting poor match is not necessarily evidence that population/matching semantics are wrong.
It can arise from:

```text
identity/provenance failure
integrity violation
model estimation failure
rule violation
```

Therefore C4 must not absorb cheating/smurfing/bot-detection as one population primitive.
Integrity remains an independent cross-cutting candidate.

---

# 19. What survives subtraction

A useful derived family survives:

```text
PlayOpportunityFormationView
MatchFormationDiagnostic
```

The important decomposition is:

```text
1. CandidateSupply
   who/what is currently available or eligible to be considered?

2. CandidateFacts / Constraints
   role, rating/model output, party relation, prior encounter,
   network feasibility, time/currentness, practice eligibility, etc.

3. SelectionPurpose / Objective
   fairness, wait time, engagement, learning challenge,
   role satisfaction, tournament pairing quality, owner-local objective.

4. SelectionPolicy / Mechanism
   pairing algorithm, match function, manual selection,
   randomization, preference mechanism, backfill policy, etc.

5. Proposal / CandidateGrouping
   one or more possible pairings/teams/content assignments.

6. SelectedOpportunity
   the chosen candidate relation/grouping under current policy.

7. DownstreamConstitutionStatus
   proposed only | selected | assigned | admitted into C1 constitution |
   rejected/superseded/expired.
```

This decomposition is practically valuable precisely because it prevents:

```text
queue ticket
match proposal
selected match
server assignment
GameInstance
```

from collapsing into one object.

---

# 20. Why the residual does not become a new Game foundation

The surviving structure decomposes across existing owners:

```text
Population/Social/Institutional
→ candidate existence, membership, social relation, external eligibility

Network/Runtime
→ queue transport, latency, region, capacity, service execution

General matching/mechanism design
→ candidate selection algorithms and optimization theory

Game
→ Game-specific role/team/opponent constraints,
   Game-relative selection objective/policy where constitutive,
   EffectiveRuleTopology/currentness,
   relevance to challenge/value

C1
→ when a selected opportunity becomes authoritative/current
   concrete GameInstance constitution.
```

There is no remaining Game-owned responsibility that cannot be stated as:

```text
current practice policy over external/current candidate facts
→ selected relation/proposal
→ C1 if adopted into an instance.
```

This is ordinary F1-F9 relation/policy/authority semantics plus existing downstream foundations.

---

# 21. Important separation from C1

C4 and C1 are adjacent but not identical.

```text
C4:
what candidate play opportunities/groupings are produced or selected
from current supply under current policy?

C1:
what makes this concrete GameInstance current/constituted,
who is bound to it,
and does it continue/end/restart?
```

Strong laws:

```text
CandidateSupply != GameInstanceMembership
QueueTicket != ParticipantByIdentity
MatchProposal != GameInstance
SelectedOpportunity != ConstitutedInstanceByIdentity
ServerAssignment != GameInstanceByIdentity
```

A local system may collapse steps for convenience, but foundations must not infer those identities universally.

---

# 22. Ownership boundary

## Game owns

```text
Game-relative eligibility/role/team/opponent constraints
practice-authorized pairing/matching policy where it is constitutive
selection objectives with Game meaning
relationship between selected opportunity and downstream Game practice
Game-relative consequences of opponent/team distribution
```

## Population / Social / Institutional owns

```text
who exists/is registered/is socially grouped
population migration/churn
community membership
external credentials/league membership
social preference relations
```

## Network / Runtime owns

```text
queue/service mechanics
latency/region/reachability
capacity
server allocation
technical backfill execution
```

## Cross-domain matching/mechanism-design owns

```text
matching markets
assignment algorithms
coalition/team formation optimization
queueing tradeoffs
incentive compatibility
welfare/fairness optimization methods
```

## C1 owns downstream

```text
actual concrete GameInstance constitution/currentness/membership/continuity.
```

---

# 23. Practical reconstruction verdict

C4 has a stronger practical consumer story than C2/C3 because online/tournament systems routinely need to debug:

```text
why no match formed
why these candidates were selected
why another proposal lost
why a role could not be filled
whether assignment has actually become instance membership
```

So:

```text
PlayOpportunityFormationView
MatchFormationDiagnostic
```

are high-value future tooling patterns.

But Ordivon Game currently has no demonstrated cross-product consumer requiring a generic persistent source layer.

The safe default remains:

```text
derived diagnostic over owner-local matchmaker/tournament/practice sources
```

not:

```text
universal Match/Queue/Population database.
```

Verdict:

```text
strong newly-discovered practical/cross-cutting gap = YES
GPR admission                                     = NO
new Game foundation                               = NO
engineering implementation                        = NOT YET PROVEN
```

---

# 24. Agent-era result

Agent era greatly changes population economics:

```text
near-zero-cost synthetic opponents
elastic bot population
Agent teammates
synthetic-only leagues
rapid replacement/backfill
shared-model correlated policies
```

But the tested distinctions remain representable through:

```text
candidate relations
ControlRealizationView
Player/Human/Agent separation
matching policy
C1 constitution
```

No `SyntheticPopulation` primitive appears.

One important residual is intentionally not absorbed:

```text
correlated/shared-model population behavior
```

may affect population diversity and dynamics, but its generic mechanism belongs to population/statistical/Agent-system analysis, not a new Game identity kind.

---

# 25. Foundation reopen audit

```text
R1-R29 / F1-F9 = NOT REOPENED
GDF0            = NOT REOPENED
GDF1            = NOT REOPENED
GDF2            = NOT REOPENED
GDF3            = NOT REOPENED
```

No new semantic coordinate is required.

GDF0 remains capable of representing pairing/matching rules inside EffectiveRuleTopology/PlayPractice where constitutive.
GDF2 already consumes opponent/team distribution in challenge/mastery scope.
C1 now closes the downstream instance-constitution distinction that old H4 lacked.

---

# 26. C4 final classification

```text
C4 destructive pass = COMPLETE

Population primitive       = REJECTED
Queue primitive            = REJECTED
Matchmaking primitive      = REJECTED
Pool primitive             = REJECTED
RatingBand primitive       = REJECTED
Fair/GoodMatch primitive   = REJECTED
TeamFormation primitive    = REJECTED
SyntheticPopulation kind   = REJECTED

PlayOpportunityFormationView / MatchFormationDiagnostic
= STRONG USEFUL CROSS-CUTTING PRACTICAL/RESEARCH ABSTRACTION

Independent Game foundation responsibility
= DOES NOT SURVIVE SUBTRACTION

C4 classification
= CROSS-CUTTING
  + STRONG NEWLY-DISCOVERED PRACTICAL GAP
  + SPLIT ACROSS GAME / SOCIAL / NETWORK / GENERAL MATCHING
  + DOWNSTREAM CONSTITUTION OWNED BY C1
  + NOT GENUINELY NEW GAME FOUNDATION
  + NOT ROUTE SELECTED
```

---

# 27. Relative update after C1-C4

```text
C1 GameInstance Constitution / Continuity
= SURVIVES as strong Game-owned downstream foundation candidate

C2 Evaluation / Comparability
= REDUCED

C3 Dynamics / Emergence
= REDUCED

C4 Population / Matching
= REDUCED
```

C4's strongest new contribution is not a new foundation but a clean boundary:

```text
population availability
→ opportunity formation / selection
→ C1 constitution
```

with external owner facts kept explicit.

---

# 28. External evidence anchors

Representative primary/current anchors:

```text
Open Match documentation — MatchFunction, MatchProfile/Pools/Tickets, proposals, Evaluator/Director/Assignments; demonstrates pluggable owner-local matchmaking logic and proposal/assignment separation.
FIDE Handbook 2026 Swiss pairing systems — scoregroups, compatibility criteria, byes, colour preferences, team-specific pairing rules and competition-local team ordering.
Chen et al. (2017), EOMM — engagement-optimized matchmaking; equal-skill/fair matchmaking is not a universal objective.
Wright & Vorobeychik (AAAI 2015) — mechanism design for team formation over preferences, welfare, equity and incentive compatibility; demonstrates cross-domain team-formation theory.
Stoneman, Miller & Cooper (AIIDE 2022) — Foldit player-level matchmaking as player-to-level DDA, demonstrating matchmaking term polysemy.
Kuboki et al. (AIIDE 2025) — rating uncertainty/early mismatch pressure in competitive online matchmaking.
```

These are falsifiers and mechanism examples, not Ordivon ontology sources.

---

# 29. Frontier after C4

```text
C1 GameInstance Constitution / Continuity
= strong foundation-unclosed candidate

C2 Evaluation / Comparability
= reduced

C3 Dynamics / Emergence
= reduced

C4 Population / Matching
= reduced; strong cross-cutting practical gap

Adaptive Experience Management
= foundation-unclosed

Meta-practice / Extended Apparatus
= foundation-unclosed

GameStructure lineage/versioning
= partial / may feed C1 and Adaptive

Integrity / cheating / exploit
= unresolved cross-cutting

unknown continents
= OPEN
```

Still:

```text
NextGPR            = UNKNOWN
NextPracticalRoute = UNKNOWN
NextFoundation     = UNKNOWN
```
