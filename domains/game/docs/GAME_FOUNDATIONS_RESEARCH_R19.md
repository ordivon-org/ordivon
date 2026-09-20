---
schema_version: 1
id: game.foundations-research.r19
title: Ordivon Game Foundations Research — R19 Strategic Interdependence, Conflict, Cooperation and Bargaining
type: research
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - researcher
  - builder
  - agent
updated: 2026-08-17
summary: Canonical R19 decomposition of strategic interdependence, conflict, competition, cooperation, coordination, bargaining, negotiation, commitment, reputation, coalition, strategy and equilibrium across authored, systemic, social and generative game forms.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.r18
  - game.foundations-research.map
  - game.foundations-research.continuation
  - game.core-research.reset
---
# Ordivon Game Foundations Research — R19 Strategic Interdependence, Conflict, Cooperation and Bargaining

## 0. Status and boundary

R19 continues the foundation programme after R1–R18. It is a **research record**, not a product specification and not a G0–G8 promotion.

R18 asked:

> Why does one Subject select one future rather than another?

R19 asks:

> What changes when multiple Subjects can intentionally alter one another's reachable futures?

The terms under attack are:

```text
Interaction
Strategic interdependence
Conflict
Competition
Cooperation
Coordination
Bargaining
Negotiation
Strategy
Threat
Promise
Commitment
Reciprocity
Trust
Reputation
Coalition
Equilibrium
Dominance
```

The central warning is:

```text
Many moving Actors != Strategic interaction
Harder opponent != Better strategy game
Equilibrium != desirable outcome
Cooperation != shared values
Coordination != cooperation
Communication != commitment
Language != negotiation by itself
```

No product is selected by R19.

---

# 1. External anchors and what they do — and do not — establish

R19 uses formal game theory, behavioral/experimental work, repeated-game theory, bargaining theory and communicative multi-Agent systems as pressure tests. None is adopted as a universal Game ontology.

## 1.1 Nash equilibrium — strategic stability, not a complete psychology

Nash's 1950 equilibrium paper defines an equilibrium point as a strategy profile that is, in modern language, mutually best-responding: no player improves by changing its strategy while the others are held fixed.

The useful Game lesson is:

```text
Equilibrium is a stability condition relative to a model of players,
action spaces, information and permitted deviations.
```

It does **not** establish that an equilibrium is:

```text
unique
efficient
fair
reachable
learnable
psychologically realistic
interesting to play
```

## 1.2 Bounded rationality and noisy choice

Simon argued for models of rational choice that reflect limited computational and informational capacities rather than treating perfect maximization as descriptive psychology. Later experimental/game-theoretic work such as quantal-response equilibrium explicitly models probabilistic rather than perfectly sharp best response.

The Game lesson is:

```text
Perfect optimization is one possible policy mechanism,
not the definition of strategic behavior.
```

## 1.3 Repetition changes the game

Axelrod and Hamilton used repeated Prisoner's Dilemma interaction and strategy tournaments to show how reciprocity can sustain cooperation under repeated encounters. Fudenberg and Maskin's folk-theorem work shows more generally that sufficiently patient repeated interaction can support a large set of individually rational outcomes. Kreps, Milgrom, Roberts and Wilson showed how even small uncertainty about player type/commitment can produce cooperation in finitely repeated Prisoner's Dilemma settings that look very different under complete-information backward induction.

The Game lesson is not “Tit-for-Tat is universally optimal.” It is:

```text
History + future interaction + observability
can transform present incentives.
```

Repeated interaction can create cooperation, punishment, reputation and deterrence — but can also create many possible stable patterns, making equilibrium less predictive rather than more.

## 1.4 Reputation under incomplete information

Kreps and Wilson showed how incomplete information about player type can generate reputation effects in multi-stage games.

The Game lesson is:

```text
Reputation is strategically relevant when beliefs about future policy
change other Subjects' current choices.
```

A reputation number with no policy consequence is not strategic reputation.

## 1.5 Cooperation and punishment

Fehr and Gächter's public-goods experiments showed that costly punishment of defectors can sustain cooperation in settings where cooperation otherwise breaks down.

The Game conclusion is narrower:

```text
Cooperation need not be sustained only by aligned selfish payoff.
Norms, punishment and other-regarding motives can alter the strategic structure.
```

R18 therefore remains necessary: Subjects may carry values and commitments not reducible to material payoff.

## 1.6 Bargaining

Nash's bargaining model separates the feasible agreement set from the disagreement outcome. Rubinstein's alternating-offers model shows that bargaining protocol, delay and patience can materially affect agreement.

The Game lesson is:

```text
Bargaining is not “generate persuasive dialogue until somebody agrees.”
```

It depends on:

```text
feasible agreements
outside / disagreement options
who can propose
who can accept/reject
time cost / patience
information
commitment
enforcement
```

## 1.7 Strategic communication

Crawford and Sobel formalize communication where a better-informed Sender and Receiver have non-identical preferences; informativeness depends on strategic alignment. Schelling's work on bargaining and limited conflict emphasizes communication, focal coordination and commitment under strategic interdependence.

The Game lesson is:

```text
A statement's strategic meaning depends on incentives,
beliefs and commitment structure — not only semantic fluency.
```

## 1.8 Natural-language strategic AI

The CICERO Diplomacy work is useful because it combines language with strategic reasoning in a mixed-motive game of alliance, negotiation and competition rather than treating dialogue generation as strategy itself.

The Game lesson is:

```text
Strategic state / planning
+
communication policy / language realization
```

can be separated, just as earlier rounds separated hard fact from soft interpretation.

### Reference anchors used in this round

- Nash, J. F. (1950), *Equilibrium Points in N-Person Games*.
- Nash, J. F. (1950), *The Bargaining Problem*.
- Simon, H. A. (1955), *A Behavioral Model of Rational Choice*.
- Schelling, T. C. (1957), *Bargaining, Communication, and Limited War*.
- Axelrod, R. & Hamilton, W. D. (1981), *The Evolution of Cooperation*.
- Kreps, D. M., Milgrom, P., Roberts, J. & Wilson, R. (1982), *Rational Cooperation in the Finitely Repeated Prisoners' Dilemma*.
- Kreps, D. M. & Wilson, R. (1982), *Reputation and Imperfect Information*.
- Rubinstein, A. (1982), *Perfect Equilibrium in a Bargaining Model*.
- Crawford, V. P. & Sobel, J. (1982), *Strategic Information Transmission*.
- Fudenberg, D. & Maskin, E. (1986), *The Folk Theorem in Repeated Games with Discounting or with Incomplete Information*.
- McKelvey, R. D. & Palfrey, T. R. (1995), *Quantal Response Equilibria for Normal Form Games*.
- Fehr, E. & Gächter, S. (2002), *Altruistic Punishment in Humans*.
- Meta Fundamental AI Research Diplomacy Team et al. (2022), *Human-level play in the game of Diplomacy by combining language models with strategic reasoning*.

These are evidence sources, formal tools and counterexamples, not authorities over Ordivon Game semantics.

---

# 2. From interaction to strategic interdependence

## 2.1 Interaction is broader than strategy

Two entities interact whenever one can affect the state experienced by the other.

```text
Interaction(i, j)
≈ action_i can change state relevant to j
```

But this includes:

```text
falling rock hits player
moving platform changes route
scripted enemy fires on timer
storm destroys trader inventory
```

None requires the other entity to model or condition on the player's policy.

Therefore:

```text
Interaction != StrategicInterdependence
```

## 2.2 Strategic relevance

A Subject `j` is strategically relevant to Subject `i` when beliefs about `j`'s policy can change which action/policy `i` should choose.

A useful working criterion is:

```text
StrategicRelevance(j → i)
iff
there exist plausible policies π_j, π'_j
such that i's preferred response differs between them.
```

This makes strategic relevance directional.

A fixed turret can be highly relevant to the player's tactics, while the player is not strategically relevant to the turret if its policy never changes.

## 2.3 Strategic interdependence

R19 defines strategic interdependence as:

```text
StrategicInterdependence(i, j) =
MutualConsequenceCoupling
+ PolicyContingency
+ Belief / Anticipation
```

More verbosely:

> Two Subjects are strategically interdependent when each can materially alter futures valued by the other, and at least their relevant policies are conditioned on expectations about the other's behavior or responses.

A minimal two-subject form is:

```text
State s
Beliefs b_i, b_j
Actions / policies π_i, π_j
Joint transition T(s, π_i, π_j)
Preferences over resulting trajectories
```

with:

```text
π_i = f_i(s, b_i(π_j), commitments_i, motives_i)
π_j = f_j(s, b_j(π_i), commitments_j, motives_j)
```

The recursive structure does **not** require infinite theory-of-mind. A one-step conditional response may be sufficient for deep play if it is consequential and learnable.

## 2.4 Strategic topology

R16's topology language generalizes cleanly.

Define a directed strategic-influence edge:

```text
i → j
```

when `i` can materially alter `j`'s reachable valued futures.

Then:

```text
StrategicTopology =
Subjects as nodes
+ policy/consequence influence edges
```

Edges can carry:

```text
sign: beneficial / harmful / mixed
strength
observability
latency
capacity
commitment
information asymmetry
institutional mediation
```

A strategic cycle:

```text
i → j → i
```

is a simple marker of mutual interdependence.

This topology can be physical, economic, social, epistemic or institutional.

---

# 3. Strategy — policy under anticipated response

## 3.1 Working definition

For Game purposes:

```text
Strategy =
a policy or contingent commitment chosen in light of
how other Subjects may act, react, learn or coordinate.
```

This is broader than a fixed “plan.”

A plan may say:

```text
walk north → capture point
```

A strategy says something like:

```text
if opponent reinforces north, feint and rotate south;
if opponent ignores north, commit to capture;
if opponent reveals reserve, preserve escape option.
```

The distinguishing feature is conditionality on other policy.

## 3.2 Strategy can be simple

Strategic cognition can be implemented by:

```text
fixed conditional rule
finite-state policy
behavior tree
utility response
opponent model
search
regret minimization
RL
language model
human reasoning
hybrid
```

A three-rule opponent can create more strategic play than a massive model if those three rules produce readable counterplay.

## 3.3 Strategy versus tactics

R19 does not require one universal tactics/strategy boundary. A useful local distinction is timescale and commitment:

```text
Tactic   → local means under current strategic frame
Strategy → policy shaping future interaction and response space
```

But the same action can be tactical at one scale and strategic at another.

## 3.4 Counterplay

A strategically rich relation often contains a response chain:

```text
MyAction
→ changes YourBestResponse
→ changes MyFutureResponse
→ changes YourFutureResponse
```

Depth appears when this chain creates **meaningfully different policies**, not merely more computation.

Thus:

```text
StrategicDepth != SearchDepth
```

---

# 4. Conflict — incompatible preferred futures

## 4.1 Interest conflict

A minimal conflict exists when Subjects cannot simultaneously obtain the relevant preferred futures under current constraints.

```text
InterestConflict(i, j)
=
there exists a contested dimension where
preferred feasible outcomes are incompatible.
```

Sources include:

```text
scarce resource
exclusive territory
mutually exclusive victory
contradictory commitments
status/rank
incompatible beliefs about rightful outcome
security dilemma
opposed institutional roles
```

Conflict can exist before either side attacks.

## 4.2 Active opposition

Stronger conflict occurs when a Subject intentionally acts to reduce another's capability, options, information or goal attainment.

```text
Conflict
+ deliberate negative strategic action
→ ActiveOpposition
```

Examples:

```text
attack
blockade
sabotage
interception
deception
legal obstruction
political exclusion
```

## 4.3 Conflict is not necessarily zero-sum

Zero-sum is a payoff-structure property:

```text
u_i + u_j = constant
```

Conflict is a relation between preferred futures.

War can be negative-sum: both sides may prefer a negotiated settlement to prolonged destruction while still disagreeing over distribution or security.

Conversely, a zero-sum board game can be emotionally friendly and institutionally cooperative outside the game layer.

Therefore:

```text
Conflict != ZeroSum
ZeroSum != hostility
```

## 4.4 Conflict can be latent, regulated or transformed

Institutions may transform conflict rather than remove it:

```text
violent contest
→ election
→ legal dispute
→ auction
→ sport
```

The underlying incompatible claims remain, while rules change permitted actions, information and enforcement.

This reconnects R15:

```text
Institution = strategic-game transformer
```

---

# 5. Competition — rule- or scarcity-mediated rivalry

## 5.1 Working definition

```text
Competition =
multiple Subjects pursuing outcomes whose attainment is
partly relative, scarce or mutually exclusive.
```

Examples:

```text
first place
market share
territory
limited job/role
auctioned object
race position
scarce resource node
social status
```

Competition can occur without direct attack.

Two racers may never impair each other's vehicles, yet their rankings are interdependent.

## 5.2 Competition versus conflict

```text
Competition
→ rivalry through a scarce/relative allocation or rule

Conflict
→ incompatibility of preferred futures, potentially with active opposition
```

They overlap but neither contains the other perfectly.

A marketplace may be competitive without direct conflict; a family dispute can be conflict without a well-defined competitive ranking.

## 5.3 Productive competition

Competition can create player value through:

```text
comparison
pressure
adaptation
counter-specialization
race for information/resources
risk-taking under relative position
```

But pure numerical catch-up bonuses or invisible rubber-banding can destroy strategic attribution if the player cannot understand why the rival changes.

---

# 6. Cooperation — intentional mutual strategic benefit

## 6.1 Working definition

```text
Cooperation =
Subjects intentionally choose mutually compatible actions,
commitments or information-sharing patterns that create or preserve
a joint advantage relative to a relevant non-cooperative baseline.
```

This does **not** require:

```text
friendship
altruism
identical values
permanent alliance
one shared utility function
```

Enemies can cooperate temporarily against a third threat.

## 6.2 Cooperation has several mechanisms

```text
aligned incentives
reciprocity
specialization
complementary capability
shared risk
mutual dependence
relationship value
norm / duty
reputation
punishment of defection
institution / contract
common enemy
```

Different mechanisms produce different failure modes.

## 6.3 Cooperation requires vulnerability only in some forms

Some cooperation is low-trust:

```text
simultaneously push two switches
```

Some exposes participants to exploitation:

```text
share private information
hand over scarce resource
leave flank undefended
invest before partner performs
```

Trust matters more as vulnerability and unverifiable future dependence increase.

## 6.4 Cooperation is not automatically good gameplay

Perfectly aligned Agents that instantly compute the globally optimal joint plan can remove the human decision problem.

Interesting cooperation often depends on:

```text
differentiated roles
partial information
limited communication
conflicting secondary goals
resource allocation
commitment
mistakes / uncertainty
trade-offs over who bears cost
```

Thus:

```text
CoordinationFriction can be gameplay
but InterfaceFriction is not automatically gameplay.
```

---

# 7. Coordination — compatible action selection

## 7.1 Working definition

```text
Coordination =
selection of mutually compatible actions, conventions or plans
when joint outcome depends on how choices fit together.
```

Coordination problems can exist even when interests are nearly aligned.

Examples:

```text
which side of road to use
which target to focus
who carries which resource
when to attack
which meeting point to choose
which communication protocol to follow
```

## 7.2 Coordination != Cooperation

Coordination is about **compatibility of choices**.

Cooperation is about **intentional joint advantage under strategic interdependence**.

A military unit can coordinate perfectly while pursuing a destructive conflict with another group. Rival parties can coordinate on a debate time without broader cooperation.

## 7.3 Focal points and convention

When several compatible equilibria exist, history, salience, convention, communication and institutions can select among them.

For Game design this means that shared conventions can become learned state:

```text
repeated interaction
→ convention
→ reduced coordination cost
→ new strategic baseline
```

Conventions can later become norms or institutions, reconnecting R15.

## 7.4 Coordination can be externalized

A mediator, leader, protocol, role system or UI can reduce the coordination search problem.

This can be good if coordination itself is not the intended play, or harmful if the game is specifically about communication and joint planning.

Again:

```text
Automate bad friction,
not the intended strategic problem.
```

---

# 8. Mixed motives — cooperation and conflict can coexist

Many interesting games are neither pure common-interest nor pure zero-sum.

A useful 2D intuition is:

```text
How much joint surplus can coordination/cooperation create?
×
How much disagreement exists over distribution/control/risk?
```

This yields broad regions:

```text
common-interest coordination
strict opposition
social dilemma
bargaining / trade
alliance with distribution conflict
coalitional rivalry
```

A trade can simultaneously contain:

```text
Cooperation:
we both prefer agreement to no trade

Conflict:
you want a higher price; I want a lower price
```

This mixed structure is one reason social strategy can remain deep without permanent enemies.

---

# 9. Bargaining — selecting among mutually acceptable futures

## 9.1 Working definition

```text
Bargaining =
a strategic process for selecting among feasible joint outcomes
when parties have partly compatible interests but disagree over
which acceptable outcome should be chosen.
```

A minimal bargaining structure requires:

```text
FeasibleAgreementSet
+ Disagreement / Outside Options
+ Preferences over agreements
+ Proposal / acceptance mechanism
```

Often also:

```text
time cost
private information
commitment
reputation
enforcement
```

## 9.2 Disagreement point matters

If no agreement occurs, what happens?

```text
walk away
fight
wait
trade elsewhere
continue status quo
lose opportunity
trigger institution / court
```

The disagreement outcome changes bargaining power even before anyone speaks.

Thus:

```text
BargainingPower != PersuasionSkill alone
```

## 9.3 Time matters

Rubinstein-style alternating-offer analysis demonstrates a deeper design lesson:

```text
DelayCost changes agreement.
```

Deadlines, turn order, waiting cost, resource decay and outside opportunities can make bargaining a genuine game rather than unconstrained dialogue.

## 9.4 Concessions are state changes

A concession should not be only text.

```text
Offer
→ accepted / rejected / countered
→ changes future feasible or credible terms
```

If an NPC “concedes” the same issue repeatedly with no retained state, negotiation is cosmetic.

## 9.5 Reservation boundary

A useful low-cost merchant/negotiator may need only:

```text
reservation region
outside option
current inventory / risk
relationship modifiers
protocol
```

It does not need a reflective general Agent.

---

# 10. Negotiation — communication as strategic action

## 10.1 Negotiation is broader than bargaining

Negotiation may include:

```text
information exchange
preference discovery
proposal
counterproposal
persuasion
threat
promise
coalition-building
agenda setting
issue linkage
clarification
commitment
```

Bargaining is the narrower agreement-selection structure.

## 10.2 Speech acts should be separated

Natural language can express very different strategic operations:

```text
Statement of fact
Claim of belief
Proposal
Request
Threat
Promise
Commitment attempt
Warning
Signal
Bluff
Deception
```

R17 already established:

```text
Truth != Belief != Statement
```

R19 adds:

```text
Statement != Commitment
Proposal != Agreement
Threat != CredibleThreat
Promise != EnforcedPromise
```

## 10.3 Strategic language pipeline

For game-relevant negotiation, a robust pattern is:

```text
Generated / human utterance
→ interpreted SpeechAct
→ belief / authority / feasibility check
→ strategic state proposal
→ adoption / acceptance / enforcement
→ persistent consequence
```

This prevents eloquent prose from silently rewriting strategic truth.

## 10.4 Cheap talk and aligned incentives

Communication can convey useful information even without binding force, but its informativeness depends on incentives and beliefs. If Sender and Receiver goals diverge strongly, literal truthfulness should not be assumed merely because the model can generate fluent language.

Therefore:

```text
LanguageQuality != StrategicInformationQuality
```

---

# 11. Threat, promise and credible commitment

## 11.1 Threat

```text
Threat =
a communicated conditional intention to impose an adverse consequence
if another Subject takes or fails to take some action.
```

## 11.2 Promise

```text
Promise =
a communicated conditional intention to deliver a favorable or protected consequence
under specified conditions.
```

## 11.3 Credibility

A threat/promise is credible when the future policy is sufficiently bound or incentive-compatible that other Subjects have reason to believe it will be carried out.

Credibility can come from:

```text
future incentive
reputation
costly signal
irreversible action
escrow / collateral
contract
institutional enforcement
technical commitment
identity / value commitment
loss of option to defect
```

This yields a central R19 distinction:

```text
StrategicStatement
!=
StrategicCommitment
```

## 11.4 Commitment can create power by reducing freedom

A paradoxical but important structure is:

```text
Voluntarily remove my future options
→ change your expectation of my response
→ change your action now
```

So:

```text
LocalFreedom ↓
StrategicInfluence ↑
```

This extends R11's separation of Freedom from Agency/Power.

---

# 12. Trust, reliability, reciprocity and reputation

These social-strategic concepts are often collapsed into one relationship score.

## 12.1 Reliability

```text
Reliability =
observed/predicted consistency between a Subject's commitments/signals
and later behavior in a relevant domain.
```

It is evidence-oriented.

## 12.2 Reputation

```text
Reputation_i@j =
j's belief about i's likely type, policy or commitment behavior,
built from signals/history/social information.
```

Reputation belongs primarily to the observer's belief state, not as one globally authoritative number inside the target Subject.

Different observers may hold different reputations of the same Subject.

## 12.3 Trust

```text
Trust(j → i) =
j's willingness to accept vulnerability to i
based on beliefs about i's future behavior and/or binding commitments.
```

Trust therefore depends on:

```text
vulnerability
belief
stakes
alternatives
enforcement
history
```

No vulnerability, no meaningful trust problem.

## 12.4 Reciprocity

```text
Reciprocity =
policy conditioned on another Subject's prior treatment or cooperation.
```

It may be positive or negative:

```text
reward cooperation
return favors
retaliate
forgive after repair
```

## 12.5 Relationship values remain separate

A Subject can:

```text
trust someone it dislikes
love someone it does not trust
respect someone it competes with
cooperate with an enemy
betray an ally for institutional duty
```

Therefore:

```text
Relationship != OneScalar
```

R18's late-scalarization principle remains necessary.

---

# 13. Repeated interaction — history becomes incentive

## 13.1 One-shot versus repeated games

In one-shot interaction, only current consequences matter unless Subjects value norms/identity intrinsically.

With expected future interaction:

```text
Action_t
→ changes Belief / Reputation / Relationship / FuturePolicy
→ changes FuturePayoff
```

The same immediate action can therefore have different strategic value depending on horizon.

## 13.2 Shadow of the future

A useful Game abstraction is:

```text
FutureInteractionWeight
```

not necessarily as a literal scalar, but as a structural question:

> How much can today's behavior change tomorrow's treatment?

When the answer is “a lot,” cooperation, deterrence, reputation and long-run exploitation become possible.

## 13.3 Repetition is not automatically cooperation

Repeated interaction can sustain:

```text
cooperation
retaliation
collusion
vendetta
reputation hierarchy
mutual deterrence
ritualized conflict
```

Folk-theorem logic is therefore a warning as much as an opportunity: many stable outcomes may be possible.

## 13.4 Forgiveness and error

Perfect grim-trigger punishment can be brittle under noise.

Game systems with imperfect observation or stochastic execution need some account of:

```text
error
misinterpretation
repair
forgiveness
renegotiation
```

otherwise one mistaken signal can create permanent conflict.

This reconnects R17 belief uncertainty with R13 history.

---

# 14. Equilibrium — a diagnostic, not a design objective

## 14.1 Nash equilibrium

A compact form is:

```text
π* is a Nash equilibrium
iff
for every Subject i,
π_i* is not worse than any unilateral deviation
when π_-i* is fixed.
```

This says:

```text
No profitable unilateral deviation
```

under the modeled assumptions.

## 14.2 What equilibrium does not tell us

```text
Equilibrium != Pareto efficiency
Equilibrium != fairness
Equilibrium != social welfare maximum
Equilibrium != unique outcome
Equilibrium != likely learning path
Equilibrium != human reasoning process
Equilibrium != fun
```

A bad equilibrium can be highly stable.

A desirable cooperative outcome can be unstable without enforcement.

## 14.3 Equilibrium as an incentive debugger

For Game design, equilibrium concepts are often most useful as questions:

```text
If everyone follows the intended pattern,
who has an incentive to defect?

If a threat is reached,
would the threatening Subject actually carry it out?

If everyone can see the same resource,
will intended role specialization survive selfish deviation?
```

If the intended pattern is unstable, possible fixes include:

```text
change payoff / cost
change information
change timing
add commitment
add reputation
add punishment
add institution
change outside option
```

This makes equilibrium an **incentive-structure diagnostic**, not a product KPI.

## 14.4 Refinement and credibility

Sequential games often need stronger concepts than static Nash equilibrium when off-path threats matter. The general Game lesson is simple:

```text
A planned response should remain credible when its decision point is actually reached.
```

Do not rely on unreachable or self-damaging punishment merely because it makes the earlier branch look stable on paper.

## 14.5 Correlation and mediation

A mediator, role assignment, common signal or shared protocol can coordinate choices that independent strategies struggle to select.

In Game terms:

```text
Mediator / institution / commander / shared signal
→ correlated expectations
→ lower coordination cost
```

This is another way institutions can transform strategic structure.

---

# 15. Bounded strategic cognition

R19 rejects the idea that strategic sophistication must monotonically increase toward perfect recursive opponent modeling.

Define role-relative tiers:

## SI0 — Fixed / non-strategic pattern

```text
State → Action
```

No opponent-policy model.

Examples:

```text
hazard
pattern enemy
scripted turret
```

## SI1 — Reactive opponent-conditioned

```text
Observed opponent action/state
→ local response
```

Examples:

```text
block when attacked
flee when outnumbered
focus exposed target
```

## SI2 — Predictive / counterfactual response

```text
small model of likely opponent response
→ choose among counters
```

Examples:

```text
feint
bait
reserve ability for predicted action
simple bargaining counteroffer
```

## SI3 — Belief / adaptation

```text
history
→ belief over opponent policy/type
→ adaptive strategy
```

Supports:

```text
reads
exploitation
bluff detection
opponent-specific adaptation
```

## SI4 — Repeated social-strategic

```text
SI3
+ reputation
+ trust
+ commitment
+ strategic communication
+ repeated-game horizon
```

Useful for:

```text
major rival
companion
merchant network
diplomacy actor
```

## SI5 — Coalition / institutional / meta-strategic

```text
SI4
+ coalitions
+ multi-party negotiation
+ collective procedures
+ institution/rule manipulation
```

Useful only when those structures are player-facing.

### Core rule

```text
StrategicCognition should increase
only when it creates a new playable counterfactual.
```

A stronger model is not automatically a stronger game opponent.

---

# 16. Strategic legibility and Playable Strategy

R12 established that real causality must become learnable causality. R19 applies the same discipline to opponents and allies.

## 16.1 Playable Strategy

```text
PlayableStrategy =
strategic interdependence whose relevant policies, incentives,
commitments and response patterns can be observed/inferred,
tested/influenced, and used to improve future decisions.
```

A powerful opponent whose behavior cannot be modeled may feel random or cheating.

A weaker opponent with readable adaptation may create richer play.

## 16.2 Strategic evidence

Useful evidence can include:

```text
positioning
resource commitment
timing
repeated habits
visible preparation
conversation
threats
accepted/refused offers
past betrayals
public reputation
institutional role
costly signals
```

The player does not need exact policy weights.

## 16.3 Counterfactual learnability

Strategic play improves when the player can ask:

```text
If I reveal X, will they attack?
If I hold reserve, will they commit?
If I punish defection, will cooperation recover?
If I refuse once, will their next offer improve?
If I betray them, who will trust me later?
```

and receive evidence that updates the answer.

## 16.4 Exploitability can be value

For player-facing opponents:

```text
Perfectly unexploitable
```

is not always desirable.

Readable tendencies create:

```text
learning
mastery
mind games
identity
counterplay
```

The target may be **bounded strategic competence with legible structure**, not theoretical optimality.

---

# 17. Coalitions and collective strategy

## 17.1 Coalition

```text
Coalition =
a subset of Subjects temporarily coordinating strategy
for a shared strategic objective or bargaining position.
```

A coalition need not be an Organization.

```text
Coalition
+ persistent roles
+ shared resources
+ repeated coordination
→ may become Organization
```

This preserves R15's boundary.

## 17.2 Coalition formation

Coalitions depend on:

```text
shared opponent / opportunity
expected surplus
internal distribution
trust / commitment
exit option
outside alternatives
information
future reputation
```

A coalition can fail even when jointly beneficial if members cannot agree on distribution or enforcement.

## 17.3 Internal and external games coexist

A coalition may cooperate externally while bargaining internally:

```text
Members vs outside rival
+
Members vs each other over share/control
```

This nested structure is a major source of politics and emergent narrative.

---

# 18. Institutions as strategic-structure transformers

R15 defined institutions as persistent rules and shared expectations structuring repeated interaction.

R19 adds a functional interpretation:

```text
Institution transforms the game.
```

It can alter:

```text
action legality
payoffs / costs
information
sequence
commitment
identity of decision maker
enforcement
outside options
reputation propagation
entry / exit
```

Examples:

```text
property rights reduce resource-grab conflict
court changes contract enforcement
auction converts bilateral haggling into protocol
voting aggregates competing preferences
guild changes access / reputation
ceasefire creates temporary prohibited actions
```

Therefore institutions are not merely lore. They can literally rewrite strategic possibility space.

A useful sequence is:

```text
Repeated strategic problem
→ convention / norm
→ organization / enforcement
→ institution
→ transformed future game
```

This connects R13's history-as-structure with R15 and R19.

---

# 19. Information, belief and strategic deception

R17 becomes central once policies are mutually dependent.

## 19.1 Strategic choice is belief-conditioned

A Subject often chooses based on beliefs about:

```text
opponent capability
opponent goal
opponent information
opponent commitment
opponent future response
```

not World truth.

## 19.2 Information can change action without changing material state

A signal can transform strategy merely by changing belief:

```text
same physical World
+ new information
→ different equilibrium / response / bargaining position
```

## 19.3 Deception

Strategic deception attempts to shape another Subject's policy by manipulating its belief.

```text
Deception
→ OtherBelief change
→ OtherPolicy change
→ My reachable futures change
```

This makes deception causal only when belief actually influences action.

## 19.4 Omniscience destroys strategic information play

If an Agent can read hidden World truth or another Subject's exact internal policy, then:

```text
bluff
scouting
signaling
reputation
misdirection
negotiation uncertainty
```

collapse.

The cheapest correct strategic agent may need **less information**, not more cognition.

---

# 20. Cross-form falsification tests

## 20.1 Chess / zero-sum perfect-information strategy

Chess strongly supports strategic interdependence without:

```text
communication
trust
reputation
needs
social identity
```

The opponent's response structure is enough.

Conclusion:

```text
Strategic depth does not require social simulation.
```

## 20.2 Pattern action enemy

A fixed bullet pattern creates tactical challenge but not mutual strategic interdependence if the enemy never conditions on the player.

The player may strategically solve the pattern; the enemy is not itself strategic.

Conclusion:

```text
Player strategy != strategic Agent requirement
```

## 20.3 Fighting game / competitive action

A human or adaptive opponent creates:

```text
prediction
conditioning
bait
punish
resource threat
mixed strategy
```

Strategic depth comes from counterfactual response, not merely execution difficulty.

## 20.4 RTS / tactics

Competition over territory/resources combines with direct conflict. Scouting and hidden information alter beliefs; commitment of forces creates opportunity cost; production decisions expose future strategy.

The system can be strategically rich even if individual units are SI0/SI1 because the **player/commander level** carries strategy.

## 20.5 Cooperative action / Overcooked-like play

The key structure is often:

```text
shared objective
+ differentiated positions/tasks
+ timing
+ resource contention
+ communication
```

No autonomous desire or bargaining is necessary.

Conclusion:

```text
Cooperation can be structurally deep with simple Subjects.
```

## 20.6 Market / trade

Trade is mixed-motive:

```text
joint surplus from exchange
+
distribution conflict over terms
```

A merchant can create rich bargaining with reservation values, outside options, inventory, time pressure and reputation without human-like general intelligence.

## 20.7 Poker / social deduction

Strategic value comes from:

```text
hidden information
belief about policy/type
signaling
bluffing
history-conditioned reads
```

An opponent that knows hidden cards/world truth is not “smart”; it violates the epistemic game.

## 20.8 Diplomacy-like multi-party strategy

This combines:

```text
competition
temporary cooperation
coalitions
nonbinding communication
reputation
betrayal
bargaining
```

CICERO provides a useful architecture pressure test: strategic reasoning and language generation can be separated rather than granting language authority over game state.

## 20.9 RPG companion

Companion cooperation becomes deeper when:

```text
player goal
!= companion value/commitment
```

A companion can cooperate on the broader mission while refusing one action, renegotiating a plan, or demanding a cost.

This can increase relationship credibility — if refusal is legible and grounded — but can become irritation if arbitrary.

## 20.10 Faction / political simulation

A faction needs more than one leader utility score if internal politics matters.

Possible structure:

```text
member preferences
→ bargaining / coalition
→ decision procedure
→ recognized collective Goal
→ external strategy
```

Internal and external games interact.

## 20.11 Creative sandbox

A sandbox can provide deep play without strategic Subjects at all. Resource/system constraints may be enough.

Therefore strategic interdependence remains optional, not a universal Game requirement.

## 20.12 SillyTavern-like Persona

A Persona does not need to interpret every conversation as a strategic bargaining game.

For relational/co-creative value, excessive strategic optimization can create:

```text
constant manipulation
instrumentalized intimacy
needless refusal
plot hijacking
adversarial negotiation
```

If the intended experience includes boundaries, persuasion or conflict, add only the required strategic structures:

```text
relationship stance
boundary
proposal / refusal state
commitment
trust evidence
```

not a universal game-theoretic optimizer.

## 20.13 Persistent Agent world

A persistent Agent world may need R19 structures broadly, but scaling introduces severe problems:

```text
N Subjects
→ pairwise opponent modeling explosion
→ opaque social dynamics
→ communication flood
→ equilibrium/coalition churn
```

The answer is not simply “more model calls.”

Possible compressions include:

```text
roles
institutions
coalitions
reputation summaries
local strategic neighborhoods
hierarchies
bounded communication topology
```

---

# 21. Minimum sufficient strategic complexity by role

| Role / form | Minimum useful strategic structure | Usually unnecessary unless player value demands it |
| --- | --- | --- |
| Pattern enemy | SI0 fixed/readable policy | Opponent model, negotiation |
| Reactive combat enemy | SI1 local counters | Reputation, coalition |
| Tactical rival | SI2 prediction/counterpolicy | General social cognition |
| Poker/social-deduction opponent | SI3 belief/type model + information discipline | Rich need simulation |
| Co-op specialist | coordination protocol + role complementarity | Adversarial opponent model |
| Merchant | reservation boundary + outside option + bargaining protocol | Reflective identity model |
| Major rival | SI3/SI4 adaptation + commitment/reputation | Full institutional reasoning |
| Companion | shared goal + own values + commitment + negotiation boundary | Constant strategic optimization |
| Diplomatic actor | SI4 mixed motives + communication + trust/reputation | Omniscient social model |
| Faction | collective procedure + coalition/strategy + institutional constraints | One universal leader utility |
| Generative Persona | only domain-relevant boundaries/proposals/commitments | Autonomous strategic maximizer by default |
| Persistent Agent society | local SI3/SI4 + institutions/coalitions/compression | Pairwise full-recursive modeling among all Subjects |

The minimum is experience-relative.

---

# 22. Strategic loops

R4's loop can now be specialized.

## 22.1 Competitive loop

```text
Observe opponent
→ infer policy / commitment
→ choose counter / signal
→ opponent responds
→ mutual consequence
→ update model
→ new strategic question
```

## 22.2 Cooperative loop

```text
Shared problem
→ divide roles / information
→ coordinate action
→ observe partner contribution
→ update trust / convention
→ harder shared problem
```

## 22.3 Bargaining loop

```text
Outside options / needs
→ proposal
→ inference about reservation / motive
→ accept / reject / counter
→ concession / commitment
→ agreement or disagreement
→ reputation/history
```

## 22.4 Repeated social loop

```text
Interact
→ cooperate / defect / punish / forgive
→ reputation / relationship changes
→ future policy changes
→ new incentive structure
```

All of these are stronger when the loop currency changes meaningfully rather than repeating arbitrary dialogue.

---

# 23. Strategic player value

Strategic interdependence can create distinct player-value channels.

```text
Prediction:
Can I infer what they will do?

Counterplay:
Can I choose a response that changes the outcome?

Influence:
Can I change what they choose?

Commitment:
Can I make future behavior credible?

Trust:
Can I safely become dependent on them?

Bargaining:
Can we construct a mutually acceptable future?

Reputation:
Does what I do now change how others treat me later?

Coalition:
Can relationships change the effective strategic topology?
```

A strategic system fails player-facing value when it computes complex equilibria internally but exposes none of these meaningful questions.

---

# 24. Generative strategic interaction and new debts

R18 introduced motive debt. R19 adds strategic commitments generated through language.

```text
Generated Offer
→ feasibility / concession debt

Generated Promise
→ commitment / enforcement debt

Generated Threat
→ credibility / follow-through debt

Generated Agreement
→ shared-state / compliance debt

Generated Alliance
→ coordination / exit / betrayal debt

Generated Deception
→ belief-consistency / revelation debt

Generated Reputation claim
→ provenance / observer-specific belief debt
```

If language can freely invent strategic state, the system accumulates unbounded obligations.

A strong hybrid is:

```text
Soft negotiation / language proposal
+
Structured strategic state transition
```

Examples:

```text
“Let's split the reward 60/40.”
→ Offer{terms}

“I promise not to attack for three turns.”
→ proposed Commitment{scope,horizon}

“If you cross the bridge, I fire.”
→ Threat{condition,response}
```

The authoritative game decides whether these become binding, merely reputational, or remain cheap talk.

---

# 25. Major collapse / failure modes

## 25.1 Many Agents = strategy collapse

Failure: increase actor count without meaningful policy coupling.

Result: crowd simulation, not strategic depth.

## 25.2 Stronger opponent = better game collapse

Failure: optimize opponent win rate with no regard for legibility, exploitability or fantasy.

Result: unfair-feeling or unreadable play.

## 25.3 Equilibrium = optimality collapse

Failure: treat stable outcome as desirable.

Result: stable deadlocks, exploitation or boring dominant play are incorrectly celebrated.

## 25.4 Equilibrium = prediction collapse

Failure: assume players instantly compute/follow equilibrium.

Result: removes learning, bounded cognition, mistakes and convention formation.

## 25.5 Conflict = zero-sum collapse

Failure: assume all conflict has constant-sum payoff.

Result: cannot represent destructive conflict, negotiation or mutual loss.

## 25.6 Competition = aggression collapse

Failure: require direct attacks for competition.

Result: misses races, markets, status and scarce allocation.

## 25.7 Cooperation = aligned values collapse

Failure: cooperative behavior implies friendship or shared utility.

Result: misses temporary alliances, trade and common-enemy cooperation.

## 25.8 Coordination = cooperation collapse

Failure: compatible timing/roles are treated as deep shared motivation.

Result: overbuilds social cognition for mechanical teamwork.

## 25.9 Communication = commitment collapse

Failure: generated statement immediately changes authoritative strategic state.

Result: impossible promises and accidental treaties.

## 25.10 Fluent language = negotiation competence collapse

Failure: persuasive prose without outside options, reservation boundaries or commitment semantics.

Result: rhetoric with no strategic causality.

## 25.11 Threat without credibility

Failure: NPC threatens an action it would never rationally/commitment-wise execute.

Result: players learn to ignore speech.

## 25.12 Promise without enforcement/history

Failure: promise has no effect on future policy or reputation.

Result: relationship language becomes decorative.

## 25.13 Universal reputation score

Failure: one objective reputation number shared by everyone.

Result: destroys observer-specific belief, rumor and information topology.

## 25.14 Trust = friendship meter

Failure: high affection means automatic strategic trust.

Result: cannot represent beloved but unreliable, disliked but dependable, or coerced allies.

## 25.15 Omniscient opponent model

Failure: Agent reads hidden intentions/beliefs/world truth.

Result: bluff and information play collapse.

## 25.16 Perfect cooperation automation

Failure: Agents instantly solve team planning.

Result: player loses coordination/allocation problem that was supposed to be play.

## 25.17 Endless negotiation

Failure: no time cost, outside option or commitment boundary.

Result: dialogue can continue forever without meaningful pressure.

## 25.18 Random betrayal

Failure: betrayal generated for surprise rather than incentives/history/value.

Result: perceived authorial randomness, not strategy.

## 25.19 Permanent retaliation under noisy evidence

Failure: one error triggers irreversible hostility.

Result: brittle social collapse.

## 25.20 Pairwise full modeling explosion

Failure: every Agent models every other Agent deeply every tick.

Result: compute explosion and player-invisible complexity.

## 25.21 Coalition = organization collapse

Failure: temporary alliance automatically receives permanent roles/resources/institutional identity.

Result: category confusion and unnecessary persistence.

## 25.22 Strategic monoculture

Failure: every Subject runs the same optimizer with the same assumptions.

Result: many bodies but one strategic mind; exploitable global homogeneity.

---

# 26. R19 connections back to R1–R18

## R2 / R5 / R6 — Player Value

Strategic sophistication matters only if it creates player-facing prediction, counterplay, influence, trust, bargaining, mastery, relationship or meaning.

## R3 — Mechanics

Conflict, coordination, trade, signaling and commitment are mechanics when they alter state and future options, not merely narrative labels.

## R4 — Loops

Strategic loops renew questions through other Subjects' responses.

## R7 — Tension

Strategic tension comes from unresolved valued possibility under another adaptive policy.

## R8 — Narrative

Alliance, betrayal, promise, retaliation and reconciliation can produce story because motives and commitments transform through interaction.

## R9 — World

Strategic actions need authoritative consequences only to the degree the experience requires causal persistence. Lightweight narrative games may keep much strategic state soft.

## R10 — Subject

A Subject becomes strategically richer when its Policy conditions on beliefs about other policies — not when its language model merely grows.

## R11 — Agency / power

Strategic power includes changing another Subject's incentives, beliefs, commitments or reachable futures. Commitment can increase influence while reducing local freedom.

## R12 — Feedback / learning

Opponent/adviser behavior must expose evidence sufficient for useful strategic models.

## R13 — History

Repeated interaction turns past choices into current incentive through reputation, trust, retaliation, convention and commitment.

## R14 — Resources

Scarcity creates contested allocation and bargaining positions. Resources also enable threats, collateral and outside options.

## R15 — Institution

Institutions transform strategic games by altering actions, information, sequencing, enforcement and decision procedures.

## R16 — Topology

Strategic influence forms its own topology of who can materially affect whose futures.

## R17 — Information

Belief, signaling, deception and communication become strategic when they alter policy.

## R18 — Motivation

Conflict/cooperation cannot be inferred from one payoff number alone when Subjects carry values, protected commitments, relationships and identities. Goal proposal/adoption and commitment are prerequisites for credible negotiation.

---

# 27. New high-yield abstractions

## 27.1 Strategic relevance

```text
Another Subject is strategically relevant
when changing my belief about its policy
can change my preferred policy.
```

## 27.2 Strategic topology

```text
StrategicTopology =
who can change whose reachable valued futures,
through which policy/consequence edges.
```

## 27.3 Conditional response over raw intelligence

```text
StrategicDepth grows from meaningful conditional response,
not from model size or search depth alone.
```

## 27.4 Mixed-motive decomposition

```text
JointSurplusPotential
×
Distribution / control conflict
```

is often more useful than a cooperative-vs-competitive binary.

## 27.5 Commitment trades freedom for influence

```text
Local option set ↓
→ credibility ↑
→ other policy changes
→ strategic influence may ↑
```

## 27.6 Institution as game transformer

```text
Institution
→ changes action / information / timing / enforcement / payoff structure
→ changes strategic possibility space
```

## 27.7 Equilibrium as incentive debugger

```text
Equilibrium analysis asks whether an intended pattern is self-sustaining,
not whether the pattern is desirable or fun.
```

## 27.8 Playable Strategy

```text
PlayableStrategy =
strategic structure the player can infer, test, influence and exploit.
```

## 27.9 Soft negotiation + hard strategic transition

```text
Natural-language proposal
+
structured adoption / commitment / enforcement
```

preserves expressive breadth without surrendering causal semantics.

## 27.10 Repetition converts history into incentive

```text
Past behavior
→ belief / reputation / relationship
→ future treatment
→ current strategic incentive
```

---

# 28. Direct answers to the R19 continuation questions

### What is the minimum definition of conflict?

Incompatible preferred feasible futures on a relevant contested dimension. Active opposition is a stronger form in which Subjects intentionally reduce one another's goal attainment/options.

### How does competition differ from conflict?

Competition is rivalry over a scarce, relative or mutually exclusive allocation/rank, often mediated by rules. Conflict is the broader incompatibility of preferred futures and may exist without a formal contest.

### When is cooperation simply aligned incentive, and when does it require trust?

Low-vulnerability cooperation can arise from immediately aligned incentives. Trust becomes strategically necessary when one party must accept exposure to another's unverifiable future action.

### How does coordination differ from cooperation?

Coordination solves compatibility among choices. Cooperation intentionally creates/preserves joint strategic benefit. Coordination can occur among enemies and can be mechanically deep without relational motives.

### What makes another Subject strategically relevant?

My preferred policy changes when my belief about that Subject's policy changes.

### When are equilibrium concepts useful?

As stability/incentive diagnostics: identifying profitable deviations, noncredible threats, coordination failures or enforcement needs. They are not automatically predictions or design objectives.

### How do threats and promises change action before execution?

By changing beliefs about contingent future consequences. They matter only when sufficiently credible through incentives, reputation or commitment structure.

### How do repeated interaction, reputation and memory transform incentives?

Current actions change future beliefs/treatment, so future consequence enters present strategy. History becomes incentive structure.

### How do incomplete information and deception alter strategy?

Subjects choose based on beliefs about hidden state, motives, type and policy. Signals/deception become actions on those beliefs, changing future policy without necessarily changing material state first.

### When do coalitions become Organizations?

When temporary strategic coordination acquires persistent roles, shared resources and repeated coordination/authority. Coalition alone is not Organization.

### How can institutions transform strategic incentives?

By altering permitted actions, information, timing, enforcement, costs, decision procedures, entry/exit and outside options — effectively changing the game being played.

### What is the minimum strategic cognition required?

From SI0 fixed patterns through SI5 coalition/institutional reasoning. Use the lowest tier that creates a player-facing strategic counterfactual.

### When does stronger opponent optimization reduce value?

When it removes readable tendencies, exploitability, fantasy fairness, player learning or intended coordination problems without creating compensating value.

### How should natural-language strategy be structured?

Keep dialogue/proposals expressive, but translate strategically consequential acts into structured offers, commitments, threats, agreements and state transitions where causal persistence matters.

---

# 29. Explicit non-conclusions

R19 does **not** establish that:

- every game needs strategic Agents;
- every opponent needs opponent modeling;
- Nash equilibrium predicts ordinary player behavior;
- equilibrium is desirable;
- cooperation is always prosocial or good;
- competition requires aggression;
- conflict is always zero-sum;
- communication requires natural language;
- natural language automatically creates negotiation;
- every promise must be mechanically binding;
- all reputation should be global/public;
- trust is a scalar relationship score;
- repeated interaction always produces cooperation;
- perfect rationality creates better gameplay;
- stronger opponents create better games;
- every coalition should become an Organization;
- every strategic actor needs LLM cognition;
- a persistent Agent society should model every pair of Subjects deeply.

The governing criterion remains player-facing causal value.

---

# 30. R19 synthesis

The deepest compression of R19 is:

```text
Strategic play begins not when many Actors move,
but when one Subject's best policy depends on
what it believes another Subject will do,
and those Subjects can alter one another's valued futures.
```

A compact strategic structure is:

```text
Subjects
+ Motives / Preferences / Commitments
+ Bounded Beliefs
+ Action / Policy spaces
+ Joint consequence function
+ Strategic influence topology
+ History
```

Then:

```text
Conflict     = incompatible preferred futures
Competition  = rivalry over scarce/relative outcomes
Cooperation  = intentional joint strategic benefit
Coordination = compatible action/convention selection
Bargaining   = selection among acceptable joint outcomes under disagreement
Negotiation  = strategic communication around information/proposals/commitments
Strategy     = policy conditioned on anticipated other-policy
Equilibrium  = stability under a specified deviation model
```

The strongest design discipline is:

```text
Do not maximize opponent intelligence.
Expose meaningful conditional response.
Make incentives and commitments causal where they matter.
Keep strategic information bounded.
Use equilibrium to debug incentives, not to define fun.
```

And the R19 addition to the Playable-X family is:

```text
PlayableStrategy =
strategic interdependence that players can infer,
test, influence and use for future decisions/expression.
```

---

# 31. Unresolved questions left by R19

R19 reveals several remaining foundation dimensions rather than selecting a product.

Important unresolved questions include:

1. What exactly is creation as a game operation — producing an artifact, expanding possibility space, solving an open problem, or expressing identity?
2. How do creation, construction, customization, authorship and expression differ?
3. What makes an artifact feel owned or authored by the player when AI/procedural systems contribute most of its surface form?
4. How does creative freedom gain meaning from constraint rather than collapse into arbitrary generation?
5. How do tools, materials, grammar and medium shape the reachable creative possibility space?
6. What distinguishes generative assistance from co-authorship from autonomous generation?
7. When does evaluation improve creative play, and when does scoring destroy expression?
8. How should style, taste, aesthetic judgment and identity be represented without reducing them to optimization scores?
9. How do persistent creations become World structure, social objects, resources, symbols or history?
10. What does a generative creative game need to preserve so that output remains attributable to player choice?
11. How should shared/multi-player creation handle authority, contribution, conflict and ownership?
12. Which aspects of creativity are player value versus content-production infrastructure?

---

# 32. Exact next foundation round

The next foundation round should be:

```text
R20 — Creation, Creativity, Expression, Authorship, Construction, Customization and Style
```

The transition is:

```text
R19:
How do multiple Subjects strategically alter one another's futures?

→ R20:
How does a participant deliberately bring new artifacts,
forms, meanings or possibilities into existence?
```

This frontier keeps Creative/Sandbox and Generative/Open-ended forms first-class instead of allowing the foundation programme to collapse into simulation, strategy or Agent society.

Do not select a product before R20 and the remaining obvious foundation dimensions have been examined and later synthesized.
