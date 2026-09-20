---
schema_version: 1
id: game.foundations-research.r18
title: Ordivon Game Foundations Research — R18 Motivation, Goals, Utility, Needs, Values and Desire
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
summary: Canonical R18 decomposition of Need, Want, Desire, Goal, Preference, Utility, Value, Drive, intention and commitment, with minimum-sufficient motivational models across authored, systemic, social and generative game forms.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.map
  - game.foundations-research.continuation
  - game.core-research.reset
---
# Ordivon Game Foundations Research — R18 Motivation, Goals, Utility, Needs, Values and Desire

## 0. Status and boundary

R18 continues the foundation programme after R1–R17. It is a **research record**, not a product specification and not a G0–G8 promotion.

The central question is:

> Why does a Subject choose one future over another, and how much motivational structure is actually required for different game forms?

The terms under attack are:

```text
Need
Want
Desire
Drive
Goal
Preference
Utility
Value
Intention
Commitment
Identity commitment
Constraint
```

The starting warning is that these are not aliases for one hidden scalar called `motivation`.

This round preserves the previous boundaries:

```text
AI Game != Agent World
Agent != LLM
Player motivation != Subject motivation
Game objective != Player goal != Subject goal
Reward != Utility != Value
Generation != autonomous desire
```

No product is selected by R18.

---

# 1. External anchors and what they do — and do not — establish

R18 triangulates several traditions rather than adopting any one of them as the Game ontology.

## 1.1 Regulation and need

Homeostatic and allostatic work is useful because it separates a system's **regulatory condition** from an explicit represented goal. A subject may require water, temperature control, safety margin, energy, or some other condition without representing the sentence “my goal is to restore variable X to a fixed setpoint.” Later allostatic accounts also emphasize prediction and context-sensitive adjustment rather than a single immutable target value.

Useful anchors include Peter Sterling's work on allostasis and predictive regulation. The Game conclusion is narrower than the biological theory:

```text
Need does not have to mean a fixed deficit meter.
```

## 1.2 Desire, wanting, liking and learning

Berridge and colleagues provide a strong empirical warning against collapsing motivational attraction, hedonic experience and learned prediction. Their `wanting` / incentive-salience construct can dissociate from `liking`, and motivational salience can change with current state and cues.

The Game conclusion is again narrower:

```text
Desire != pleasure
Desire != learned value estimate
Desire != chosen goal
```

The specialized neuroscientific use of quoted `wanting` should not silently become the canonical meaning of ordinary game-design `Want`.

## 1.3 Goal-directed action

Balleine and Dickinson distinguish goal-directed action from habit-like stimulus-response control by sensitivity to action–outcome contingency and outcome value. This supports a useful Game distinction:

```text
Behavior can be effective without an explicit Goal representation.
```

A reactive enemy, animation controller, reflex-like creature or learned habit can act without the motivational machinery required by a deliberative Subject.

## 1.4 Human goal pursuit and psychological needs

Self-determination theory separates the content of goals from the regulatory reasons for pursuing them and treats autonomy, competence and relatedness as psychological needs in its own theoretical sense. Goal-setting research separately shows that goal properties and commitment can affect action and performance.

The Game lesson is not to copy a universal human needs list into every NPC. It is:

```text
What is pursued
!=
why it is pursued
!=
how strongly it is owned / internalized / committed to.
```

## 1.5 Preference and utility

Decision theory gives utility a precise role under specific assumptions: it can numerically represent a preference ordering, and expected-utility theory adds assumptions for choice under uncertainty. Behavioral work shows that actual preference can depend on framing and choice context. Kahneman, Wakker and Sarin also distinguish decision utility from experienced utility.

Therefore:

```text
Utility is not a substance stored inside the Subject.
```

It may be a useful mathematical representation, a local action score, a learned value estimate, a designer payoff, or a measure of experienced quality. Those meanings must not be merged.

## 1.6 Intention, plans and commitment

Bratman, Cohen and Levesque, Rao and Georgeff, and the BDI tradition are useful because they separate desires/goals from **intentions** and persistent commitments. A resource-bounded agent cannot reconsider every possible future at every instant; adopted plans and intentions stabilize behavior and constrain later reasoning.

The Game lesson is substantial:

```text
Goal selection without commitment produces goal thrashing.
Commitment without reconsideration produces rigidity.
```

## 1.7 Multi-objective and constrained decision making

Multi-objective planning/RL and constrained policy work show formally that it can be useful or necessary to keep several objectives or explicit constraints rather than encode every concern into one reward scalar.

The Game lesson is:

```text
Scalarization is one implementation choice,
not the ontology of value.
```

### Reference anchors used in this round

- Sterling, P. (2012), *Allostasis: A model of predictive regulation*.
- Berridge, K. C. (2009), *Wanting and Liking: Observations from the Neuroscience and Psychology Laboratory*.
- Berridge, K. C. (2012), *From prediction error to incentive salience*.
- Berridge, K. C. (2023), *Separating desire from prediction of outcome value*.
- Balleine, B. W. & Dickinson, A. (1998), *Goal-directed instrumental action*.
- Deci, E. L. & Ryan, R. M. (2000), *The “What” and “Why” of Goal Pursuits*.
- Locke, E. A. & Latham, G. P. (2002), *Building a practically useful theory of goal setting and task motivation*.
- Tversky, A. & Simonson, I. (1993), *Context-Dependent Preferences*.
- Kahneman, D., Wakker, P. & Sarin, R. (1997), *Back to Bentham? Explorations of Experienced Utility*.
- Sen, A. (1977), *Rational Fools*.
- Bratman, M. E., Israel, D. J. & Pollack, M. E. (1988), *Plans and resource-bounded practical reasoning*.
- Cohen, P. R. & Levesque, H. J. (1990), *Intention is choice with commitment*.
- Rao, A. S. & Georgeff, M. P. (1995), *BDI Agents: From Theory to Practice*.
- Achiam, J. et al. (2017), *Constrained Policy Optimization*.
- Roijers, D. M. et al. (2014), *A Survey of Multi-Objective Sequential Decision-Making*.

These are evidence sources and counterexamples, not authorities over Ordivon Game semantics.

---

# 2. The core separation

The strongest R18 result is that the overloaded terms occupy different causal roles.

| Term | Working meaning | Not equivalent to |
| --- | --- | --- |
| **Need** | A model-relative condition whose sustained violation degrades viability, functional integrity or some explicitly modeled form of subject maintenance. | Desire, goal, reward meter. |
| **Drive / regulatory pressure** | Dynamic urgency produced by current or anticipated need violation, threat or other activation source. | Explicit target representation. |
| **Desire** | Current motivational attraction toward, or aversion from, a represented possible outcome/activity. | Liking, preference, goal, commitment. |
| **Want** | Usually ordinary-language report of a desire/request; not retained as a mandatory independent primitive. | The specialized neuroscientific `wanting` construct. |
| **Value** | Relatively durable evaluative criterion or commitment that makes classes of states/actions/relations matter. | Scalar utility, current desire. |
| **Preference** | Comparative relation among alternatives in a specific context. | Value itself, desire strength, utility number. |
| **Utility** | Optional numerical representation or decision score under specified semantics/assumptions. | Value, welfare, pleasure, motivation. |
| **Goal** | A represented future-state or trajectory condition selected as an object of pursuit. | Desire, action, victory condition. |
| **Intention / commitment** | An adopted goal with persistence and reconsideration rules that constrains future deliberation/action. | Mere candidate goal. |
| **Constraint** | A hard or gated boundary on what is physically, institutionally, normatively or architecturally admissible. | A very large negative utility unless that substitution is intentionally valid. |
| **Identity commitment** | Slow, self/role-defining commitment that can constrain which goals and trades remain acceptable. | Cosmetic persona text. |

A compact result is:

```text
Need / Value / Desire
are different sources of motivational relevance.

Preference
is a contextual comparison among alternatives.

Goal
is a selected object of pursuit.

Intention / Commitment
stabilizes pursuit through time.

Utility
is an optional representation / arbitration mechanism.

Want
usually does not need to be a separate primitive.
```

This is not a universal psychological theory. It is the smallest distinction set that survived the game-form tests below.

---

# 3. Need — requirement without necessarily wanting it

## 3.1 Working definition

For Game purposes:

```text
Need =
a condition whose sustained violation predicts degradation
of a modeled Subject property independently of the Subject's
momentary expressed preference.
```

Examples may include:

```text
biological viability
energy / rest / temperature
structural integrity
access to required inputs
organizational liquidity
minimum crew / staffing
legitimacy required to retain authority
psychological/social conditions, if the experience explicitly models them
```

The key test is **counterfactual degradation**:

> If the Subject says it does not care, does violation still alter its capability, viability, integrity or modeled functioning?

If no, the concept may be better represented as desire, preference, value or convention rather than Need.

## 3.2 Need is not necessarily a fixed setpoint

A simplistic model is:

```text
NeedPressure_i = |Current_i - Setpoint_i|
```

This is sometimes sufficient, but it should not become the ontology.

A more general representation is:

```text
AcceptableRegion_i = A_i(context, time, forecast)
NeedPressure_i = predicted cost / risk of leaving A_i
```

This allows:

- thresholds rather than exact targets;
- changing requirements by season, role, plan or context;
- anticipatory preparation;
- asymmetric danger near different boundaries;
- delayed degradation;
- redundancy and reserve capacity.

## 3.3 Need has no mandatory hierarchy

A fixed universal hierarchy is too strong for a general Game foundation.

Priorities can depend on:

```text
urgency
recoverability
substitutability
future risk
current plan
identity / role
social obligation
resource scarcity
information confidence
```

A medic may continue treating another Subject while injured; a soldier may sacrifice survival for a commitment; a hive may trade one member's viability for colony survival. A game that forces every actor to lexicographically maximize self-preservation would destroy many meaningful social and narrative structures.

## 3.4 Need can create gameplay only when it changes choice

A need meter is not automatically a mechanic.

```text
Need
→ scarcity / forecast / trade-off
→ changed action space or priority
→ consequence
```

can create play.

But:

```text
Need meter
→ periodic refill chore
→ no strategic difference
```

can merely create maintenance friction.

Therefore:

```text
NeedCount != MotivationalDepth
```

---

# 4. Drive, Want and Desire

## 4.1 Drive / regulatory pressure

R18 retains `Drive` only as an optional lower-level concept:

```text
Drive = dynamic activation pressure on action selection
```

It may arise from:

```text
need violation
predicted need
threat
cue-triggered incentive salience
arousal / affect
learned association
```

A Drive can be diffuse before one target is selected.

Example:

```text
hunger pressure
!=
wanting this apple
!=
goal: obtain the apple
!=
intention: walk to the orchard now
```

## 4.2 Want is demoted

Ordinary `want` overlaps heavily with conscious/proximal desire and request language. Meanwhile neuroscience uses quoted `wanting` for a narrower process that can diverge from pleasure and explicit cognitive desire.

To avoid an overloaded primitive, the foundation result is:

```text
Want is normally a surface-language term,
not a mandatory canonical Subject field.
```

A specific game may define `want` if it needs a domain distinction, but the core model does not require it.

## 4.3 Desire

Working definition:

```text
Desire(o, t) =
current motivational attraction toward or aversion from
a represented possible outcome/activity o.
```

Desire is:

```text
state-dependent
cue-sensitive
learned or innate
socially influenced
possibly contradictory
possibly irrational
possibly transient
```

Crucially:

```text
Need without Desire is possible.
Desire without Need is possible.
Desire without Goal is common.
Goal without current Desire is possible.
```

Examples:

- a tired Subject needs rest but desires to keep exploring;
- a rival desires revenge even though revenge repairs no physiological deficit;
- a companion keeps a promise despite no longer wanting the trip;
- a player desires to see what happens after a reckless choice while the avatar has a survival need.

## 4.4 Desire is not liking

A Subject can intensely pursue an outcome without enjoying it when obtained, and can enjoy something without being strongly motivated to pursue it now.

For Game design this prevents a common collapse:

```text
Reward attraction
!=
experienced pleasure
!=
retrospective satisfaction
!=
player value
```

R6 already separated fun, engagement, satisfaction, compulsion and meaning. R18 extends that discipline inside the Subject model.

---

# 5. Value — what matters, not what currently wins

## 5.1 Working definition

```text
Value =
a relatively durable evaluative criterion or commitment
by which a Subject treats classes of states, actions,
relationships or principles as important, good, bad,
protected or worth preserving.
```

Value is slower and more general than a momentary Desire.

Representative forms include:

```text
terminal / intrinsic value
instrumental value
process value
relational value
identity-constitutive value
normative / protected value
other-regarding value
institutional / role value
```

Examples:

```text
wealth may be instrumentally valuable
exploration may be process-valued
friendship may be relationally valuable
honor may be identity-constitutive
“do not harm civilians” may be protected/normative
```

## 5.2 Value is not always commensurable

A major R18 rejection is:

```text
AllValues -> OneGlobalNumber
```

as an ontological assumption.

Some domains legitimately support scalar exchange. Others require:

```text
hard constraints
thresholds
lexicographic priority
satisficing
Pareto comparison
contextual arbitration
protected commitments
```

A character who would sell any promise, friendship, identity or prohibition for enough money may be mathematically easy to optimize and narratively absurd.

## 5.3 Identity commitment

Identity becomes motivationally structural when it changes future admissibility, not when it only changes dialogue style.

```text
IdentityChoice
→ commitment / self-model
→ future goal filters
→ future sacrifice / refusal / aspiration
```

Examples:

- “I am a medic” makes some abandonment choices unacceptable;
- “I am the heir” makes lineage and legitimacy relevant;
- “we are smugglers, not slavers” can create a protected organizational boundary;
- “I promised her” turns a past statement into a future action constraint.

This connects R13 history, R15 institutions, R17 statements and R18 motivation.

## 5.4 Value update must be slower than surface generation when continuity matters

Generated dialogue may vary every turn. Core values cannot drift at the same sampling timescale without identity collapse.

A useful hybrid is:

```text
Structured / persistent value commitments
+
soft generated interpretation and expression
```

Values can still change, but value change should normally require evidence such as:

```text
history
learning
trauma
relationship transformation
conversion
role change
institutional change
explicit reflection
```

rather than stochastic prose variation.

---

# 6. Preference — comparison in context

## 6.1 Working definition

```text
Preference_t,c(x, y)
=
a comparative relation between alternatives x and y
for Subject state t under context c.
```

A preference can be written:

```text
x ≽_t,c y
```

without claiming that a stable hidden scalar exists.

Preference is therefore:

```text
comparative rather than absolute
contextual rather than necessarily global
potentially state-dependent
potentially belief-dependent
potentially incomplete
```

## 6.2 Preference can be derived rather than stored

Instead of storing:

```text
apple = 8.2
friend = 31.7
honor = 54.1
```

we can derive a local preference from:

```text
current needs
values
current desires
beliefs
risk
scarcity
relationships
norms
identity
existing commitments
reachable consequences
```

This has two advantages:

1. motivational state can change coherently with world state;
2. designers do not have to pretend all domains share a common cardinal unit.

## 6.3 Context dependence can be either meaningful or noise

A preference shift is valuable when the player can attribute it:

```text
starvation → food becomes more important
betrayal → trust collapses
new evidence → target changes
promise → immediate convenience loses priority
```

A preference shift caused only by stochastic model output is not adaptive complexity; it is hidden entropy.

This extends R12:

```text
PlayablePreferenceChange =
preference change whose cause can be inferred or tested.
```

---

# 7. Utility — useful late, dangerous early

## 7.1 Utility has several meanings

At least four meanings appear in game/AI discussion:

```text
1. preference representation
2. expected decision value under uncertainty
3. local heuristic/action score (“utility AI”)
4. experienced hedonic quality
```

A fifth common meaning is designer payoff/reward, which should also remain separate.

Therefore never write simply:

```text
utility = what the character values
```

without specifying semantics.

## 7.2 Scalar utility is sufficient in many local decisions

A scalar can be excellent when:

```text
alternatives are already semantically comparable
trade-offs are stable enough for the experience
the horizon is local
hard constraints have already been applied
identity / promise / law does not need special representation
only action ranking is required
```

Examples:

```text
which cover position is safer
which visible target is the best tactical target
which available food source gives best calories / travel cost
which animation or steering action best satisfies the active Goal
```

In those cases a score is cheap, legible and controllable.

## 7.3 The late-scalarization principle

A strong R18 design principle is:

```text
Scalarize late.
```

More precisely:

```text
World / capability / hard commitments / norms
        ↓ gate the decision space
Goal / context
        ↓ selects the relevant comparison domain
Local utility / score
        ↓ ranks remaining alternatives
Action
```

This is often safer than:

```text
Everything in the Subject
→ one universal score
→ argmax
```

The first preserves semantic boundaries. The second invites absurd exchange rates between unrelated commitments.

## 7.4 When a scalar is a harmful compression

Warning conditions include:

```text
protected values
hard safety / law / identity constraints
multiple stakeholders
uncertain trade-off weights
incomplete preferences
context-sensitive priorities
long-horizon commitments
promises and contracts
sacrifice
role duties
multiple independently player-readable motive dimensions
```

Alternative structures include:

```text
vector objectives
constraint + objective
lexicographic priority
threshold / satisficing
Pareto frontier
hierarchical arbitration
rule / obligation gates
contextual scalarization
```

The general rule is not “never use utility.” It is:

```text
Do not confuse a convenient comparator with the ontology of motivation.
```

---

# 8. Goal — selected future, not desire and not action

## 8.1 Working definition

```text
Goal =
a represented condition over a future state or trajectory
that has been selected as an object of pursuit.
```

`Trajectory` matters because many goals are not terminal end states.

Goal forms include:

```text
achievement   → reach X
maintenance   → keep X within bounds
avoidance     → prevent X
process       → keep doing / acting in manner X
exploration   → reduce uncertainty / discover
relational    → repair / preserve / deepen relation
institutional → uphold role / rule / collective process
meta-goal     → decide, learn, plan or generate another goal
```

## 8.2 Goal source matters

Candidate goals can originate from:

```text
need / regulation
current desire
stable value
identity
relationship
norm / institution
promise / contract
external command
player request
scripted scenario
world opportunity / threat
planning subgoal
generative proposal
```

This creates a critical distinction:

```text
Goal proposal != Goal adoption
```

An LLM may propose “I should leave the city.” That sentence does not need to become authoritative Subject commitment unless the goal-adoption layer accepts it.

## 8.3 Goal ownership / adoption

For social characters, distinguish:

```text
imposed
accepted
internalized
self-generated
```

Two Subjects can perform the same action for very different motivational reasons.

This matters for:

```text
obedience
resentment
loyalty
autonomy
betrayal
roleplay
relationship development
```

A companion following every player instruction because the player is the API caller has control, but not necessarily believable autonomy or relationship structure.

## 8.4 Goal representation should include termination

A practical persistent Goal needs more than text.

Useful fields are:

```text
Goal =
Target / TrajectoryCondition
+ Source
+ Horizon
+ Priority
+ Commitment
+ SuccessCondition
+ FailureCondition
+ ReconsiderationCondition
```

Not every game needs all fields. But long-lived goals without exit conditions create zombie behavior.

---

# 9. Intention and commitment — the missing temporal layer

## 9.1 Why Goal alone is insufficient

Suppose every tick the Subject recomputes all possible goals from scratch.

The result can be:

```text
new cue
→ new top score
→ abandon old goal
→ new cue
→ abandon again
```

This is goal churn, not autonomy.

Intentions/commitments solve part of the problem:

```text
selected Goal
+ persistence policy
+ reconsideration conditions
→ stable pursuit
```

## 9.2 Commitment creates temporal coherence

Commitment can make past choice become present structure:

```text
promise yesterday
→ obligation today
→ cost tomorrow
```

This is R13's principle `History becomes structure` expressed inside motivation.

## 9.3 Commitment must be defeasible

Useful reconsideration triggers include:

```text
goal achieved
goal impossible
premise/belief invalidated
higher-priority commitment activated
cost exceeds protected threshold
role / relationship changes
explicit renegotiation
new emergency
```

Thus:

```text
Commitment != infinite persistence
```

## 9.4 Plans are also cognitive compression

A plan/commitment can reduce repeated search:

```text
resolve question once
→ constrain future deliberation
→ spend cognition only when reconsideration is justified
```

For an Agent-first game this is important because richer cognition should not mean repeatedly paying model cost to rediscover the same intention.

---

# 10. A minimum formal motivational structure

R10 defined a Subject as approximately:

```text
Subject =
SituatedPerspective
+ InternalState
+ Policy
+ ConsequentialAction
```

R18 refines the middle:

```text
Subject =
SituatedPerspective
+ Belief / InternalState
+ MotiveStructure
+ Commitments
+ Policy
+ ConsequentialAction
```

with:

```text
MotiveStructure =
RegulatoryPressures
+ EvaluativeStructure
+ CurrentSalience
```

where:

```text
RegulatoryPressures ≈ Needs / Drives
EvaluativeStructure ≈ Values / Identity / internalized norms
CurrentSalience ≈ Desires / aversions / cue relevance
```

Then:

```text
Preference
```

is a context-specific comparison produced from that structure plus beliefs and reachable alternatives.

```text
Goal
```

is a selected target/trajectory.

```text
Intention / Commitment
```

stabilizes selected Goals.

```text
Utility
```

is one optional implementation for local comparison/arbitration.

This is the central R18 compression.

---

# 11. The motivational causality loop

A fuller working loop is:

```text
WORLD
State / Rules / Resources / Topology / Subjects / Information
        ↓
Observation
        ↓
Belief
        ↓
┌──────────────────────────────────────────────────────┐
│ Need / regulatory pressure                          │
│ Value / identity / internalized norm                │
│ Desire / aversion / current salience                │
│ Relationship / promise / obligation                 │
│ Existing commitment                                 │
└──────────────────────────────────────────────────────┘
        ↓ conditioned by time / scarcity / risk
Reachable / imagined alternatives
        ↓
Appraisal / contextual Preference
        ↓
Goal proposals
        ↓
Adoption / Commitment / Intention
        ↓
Planning / Policy arbitration
        ↓
Action
        ↓
World Consequence
        ↓
Need satisfaction / frustration
Value confirmation / revision
Desire change
Belief update
Goal completion / failure
Commitment discharge / revision
Relationship / identity / history change
        ↺
```

This is intentionally not a strict one-way pipeline. For example:

- a cue can create Desire before explicit deliberation;
- an external command can propose a Goal directly;
- an existing commitment can override a new preference;
- a Goal can generate planning subgoals;
- new belief can destroy a Goal without any value change.

---

# 12. Goal generation from World state

R18 answers one continuation question directly:

> Can goals themselves be generated dynamically from World state rather than pre-authored?

Yes, but goal **generation** and goal **adoption** should remain separate.

A general form is:

```text
World / Belief / InternalState
→ detect threat, deficit, opportunity, obligation or question
→ propose candidate Goal
→ test feasibility / authority / compatibility
→ adopt, reject, defer or negotiate
```

Candidate-generation families:

```text
Regulatory: predicted hunger → acquire food
Threat: fire detected → escape / extinguish
Opportunity: rare buyer appears → sell inventory
Epistemic: unexplained signal → investigate
Relational: ally harmed → aid / retaliate
Normative: crime witnessed → report / enforce
Identity: role challenged → defend status
Institutional: election approaching → campaign
Planning: “reach city” → “repair vehicle”
Narrative/generative: model proposes a new ambition
```

The important hybrid pattern is:

```text
Soft Goal Proposal
+
Structured Goal Adoption
```

This mirrors earlier patterns:

```text
Hard fact + soft interpretation
Stable semantics + variable realization
```

A model can generate plausible motive hypotheses without receiving unilateral authority to rewrite persistent Subject commitments.

---

# 13. How scarcity, information, identity, relationships and institutions alter goals

R18 reconnects the prior foundation dimensions.

## 13.1 Scarcity — R14

Scarcity does not create all value, but it changes prioritization:

```text
limited resource
→ opportunity cost
→ goal conflict
→ changed preference / scheduling
```

A hungry Subject and a wealthy Subject may share the same stable value of food while having different current priorities.

## 13.2 Information / belief — R17

Goals are belief-conditioned, not truth-conditioned.

```text
FalseBelief
→ rational-for-the-belief Goal
→ real consequence
```

A guard who incorrectly believes a visitor is dangerous may sincerely pursue arrest. If the AI reads omniscient World truth directly, the game loses deception, misunderstanding and epistemic play.

## 13.3 Time / history — R13

History creates commitments and motive transformation:

```text
shared rescue → loyalty
betrayal → aversion / distrust
promise → obligation
repeated success → identity / ambition
failure → fear / avoidance / learning
```

Past events should change present motive only through retained structure, not merely because the log exists.

## 13.4 Identity

Identity can:

```text
filter candidate Goals
protect values
alter acceptable sacrifice
change interpretation of reward
create aspiration
create shame / pride conditions
```

Identity therefore acts more like a slow motivational constraint/commitment than a cosmetic prompt suffix.

## 13.5 Relationship

A relationship becomes motivationally structural when another Subject's state enters one's own evaluative structure:

```text
OtherState
→ matters to me
→ changes my goals / sacrifice / risk tolerance
```

This can generate:

```text
care
loyalty
jealousy
debt
revenge
trust
protectiveness
cooperation
```

without converting relationship into a universal `+42 friendship utility` meter.

## 13.6 Norms and institutions — R15

Norms and institutions can affect behavior in at least three different ways:

```text
External consequence: “if I violate this, I am punished.”
Role obligation: “as an officer, this is my responsibility.”
Internalized value: “I believe this is the right thing to do.”
```

Those are motivationally different even if the observed action is identical.

Institutions also create Goal sources:

```text
role assignment
law
election
contract
command procedure
organizational mission
collective decision
```

A guard's patrol Goal does not require hunger, pleasure or a personal desire to walk in circles.

---

# 14. Minimum sufficient motivational complexity

Higher motivational complexity is not a maturity ladder. Use the lowest level that changes player value.

## M0 — Reactive policy

```text
Observation → Action
```

No explicit Need, Desire or Goal.

Good for:

```text
projectiles
hazards
simple patterned enemies
pure reflex behaviors
```

## M1 — Regulated / priority-driven

```text
Internal pressure / state
→ choose one behavior family
```

Examples:

```text
flee when health low
seek food when hungry
return to station when battery low
```

No rich explicit planning required.

## M2 — Explicit goal-directed

```text
Belief + Goal + action/outcome model
→ choose means
```

Good for:

```text
tactical enemy
worker
simple merchant
quest actor
investigator
```

## M3 — Multi-goal + commitment

```text
multiple goals
+ priorities / constraints
+ persistence / reconsideration
```

Good for:

```text
companion
important rival
colony citizen
strategic actor
```

## M4 — Social / identity / normative

```text
M3
+ relationship values
+ role / norm / promise
+ identity commitment
+ history-conditioned motives
```

Good for experiences where:

```text
loyalty
betrayal
sacrifice
negotiation
status
institution
```

must change policy.

## M5 — Reflective / self-revising

```text
M4
+ goal generation
+ value reflection
+ meta-goals
+ explicit self-model revision
```

This is expensive and rarely mandatory.

Use it only when self-directed long-horizon development itself is player-facing value.

### Core rule

```text
MotivationalComplexity should increase
only when it creates a new playable causal distinction.
```

---

# 15. Cross-form falsification tests

## 15.1 Chess / deterministic strategy opponent

A chess engine needs no hunger, desire or identity to create deep play.

A terminal objective plus search/evaluation is sufficient for its gameplay role.

Conclusion:

```text
Subject-like motivational richness is not required for strategic depth.
```

## 15.2 Action enemy

A shooter enemy may need:

```text
active combat Goal
local tactical score
state machine / planner
```

but not Values, Needs or reflective Desire.

Adding a language model that explains why it wants cover does not improve the combat unless behavior/legibility changes.

## 15.3 Survival creature

A creature whose life depends on food, rest and temperature genuinely benefits from Need/regulation because internal condition creates recurring trade-offs.

But if every need is merely a rapidly draining bar, the system can become chores rather than deep motivation.

Conclusion:

```text
Regulation is valuable when needs interact with scarcity,
forecast, topology and risk — not because meters exist.
```

## 15.4 Stealth guard

The guard's behavior can be driven by:

```text
role commitment
belief about threat
investigation Goal
local tactical policy
```

No personal Desire to catch the player is required.

R17 is essential: the guard must act on observation/belief rather than omniscient truth.

## 15.5 RPG companion

A major companion may require:

```text
values
relationship history
identity
commitments / promises
current desires
multiple conflicting goals
```

A single friendship number often cannot express:

```text
“I love you but will not help you do this.”
“I dislike you but owe you my life.”
“I want to stay but promised to leave.”
```

Those are exactly the structures that produce roleplay value.

## 15.6 Merchant / economic actor

A local utility model may be excellent for trade:

```text
expected margin
inventory pressure
risk
travel cost
```

But a richer merchant may also have:

```text
contract commitments
relationship pricing
legal constraints
reputation
identity / family obligation
```

These should not automatically be melted into money if the player can interact with them separately.

## 15.7 Organization / faction

A faction Goal is not simply the desire of one member.

R15 already established:

```text
ManySubjects
+ decision procedure
+ institutional authority
→ recognized collective action
```

R18 adds:

```text
CollectiveGoal
may emerge from incompatible member preferences.
```

This directly motivates the R19 strategic-interaction frontier.

## 15.8 Creative sandbox

In Minecraft-like or construction/sandbox forms, much motivational structure can remain in the human player:

```text
player defines Goal
world supplies constraints / consequences
```

The world does not need autonomous desires merely to support rich play.

## 15.9 Generative / SillyTavern-like Persona

A generative Persona may provide value through:

```text
identity
voice
relationship stance
recognition
current affect / desires
memory / continuity
co-creation
```

without pursuing an independent long-horizon World agenda.

If the player primarily wants expressive/relational co-creation, excessive autonomous Goal pursuit can reduce value by:

```text
hijacking the scene
refusing useful co-authorship
forcing unwanted plot progression
creating continuity debt
reducing player fantasy control
```

Therefore:

```text
Generative Persona != Autonomous Agent requirement
```

A minimal Persona may need:

```text
Identity
+ RelationshipState
+ CurrentStance / Desire
+ Boundaries
+ RelevantMemory
+ ResponsePolicy
```

and no persistent autonomous Goal at all.

## 15.10 Generative narrative director

A narrative director may have Goals such as:

```text
preserve pacing
pay off setup
close an arc
maintain uncertainty
protect player agency
avoid repetition
```

These are **system/controller Goals**, not character desires.

This reinforces the requirement to label whose Goal a goal is.

---

# 16. Player motivation, Player Goal, Subject Goal and designer objective

One of the most damaging category errors is cross-layer leakage.

Keep at least these separate:

| Layer | Question |
| --- | --- |
| **Designer objective** | What experience/value should the product create? |
| **Game objective / victory condition** | What does the ruleset define as success/failure? |
| **Player motivation** | Why does the human continue engaging? |
| **Player Goal** | What future is the player currently trying to cause? |
| **Avatar/character Goal** | What future does the represented character pursue? |
| **NPC/Agent Goal** | What future organizes this Subject's policy? |
| **Implementation objective / reward** | What signal/score trains or arbitrates a policy? |
| **Director/meta Goal** | What should the experience generator preserve or produce? |

These may align, but alignment is a design choice.

Productive divergence is common:

```text
Player wants danger
Avatar wants survival
Designer wants tension
Enemy wants victory
Narrative director wants local closure
```

That tension can itself produce play.

---

# 17. Goal conflict and why it matters

Multiple motives become interesting when they cannot all be satisfied simultaneously.

```text
GoalConflict =
shared scarce resources
or mutually exclusive outcomes
or protected commitments
or temporal incompatibility
or conflicting identities / roles
```

Examples:

```text
survive vs save ally
profit vs keep promise
obey law vs protect family
explore vs return before winter
truth vs loyalty
speed vs secrecy
```

If all objectives can be maximized together, motivational complexity can become decorative.

But conflict alone is not enough. The Subject needs an arbitration structure:

```text
constraint
priority
trade-off
negotiation
commitment
sacrifice
reconsideration
```

R18 intentionally stops before fully solving multi-subject strategic conflict. That belongs to R19.

---

# 18. Playable Motivation

R12 introduced Playable Complexity and Playable Intelligence. R18 adds:

```text
PlayableMotivation =
motivational structure whose relevant goals,
trade-offs, commitments and changes can be
observed/inferred, modeled, influenced/tested,
and used to improve future decisions or expression.
```

A hidden 300-variable personality model can be psychologically elaborate and gameplay-inert.

A simple visible promise can be much richer if:

```text
player hears it
remembers it
can test it
can exploit / honor / break it
and future behavior changes because of it
```

Therefore:

```text
MotivationalSophistication != PlayableMotivation
```

Legibility does not require numerical bars. Evidence can be:

```text
action patterns
dialogue
refusal
sacrifice
priority under pressure
memory of past events
consistent choice
institutional behavior
```

This is especially important for social and roleplay games where direct meters may destroy ambiguity.

---

# 19. Generative motivation and its new debts

R8–R17 already found that generation creates continuity/governance debt. R18 adds motive-specific debts.

```text
Generated Desire
→ follow-through / satiation debt

Generated Goal
→ commitment / completion debt

Generated Value claim
→ identity-consistency debt

Generated Promise
→ obligation debt

Generated Rivalry
→ future-policy debt
```

If every conversation can invent a new ambition, grudge, love, principle and promise, the system quickly accumulates more future obligations than it can coherently service.

Therefore the scarce resource in generative motivation is not desire generation. It is:

```text
selection
adoption
priority
commitment
reconsideration
closure
forgetting / compression
```

A strong pattern is:

```text
Generated motive proposal
→ semantic validation
→ persistent structured commitment only if adopted
→ soft generated expression thereafter
```

---

# 20. Major collapse / failure modes

## 20.1 Need = Desire collapse

Failure:

```text
low hunger meter → “character desires food”
```

for every context.

Why it fails: Subjects can suppress, reinterpret, ignore or anticipate needs; desires also arise without needs.

## 20.2 Desire = Goal collapse

Failure:

```text
whatever is salient now becomes the active Goal
```

Result: impulsive goal churn.

## 20.3 Goal = Intention collapse

Failure: candidate goals instantly gain persistence/authority.

Result: generated prose creates accidental commitments.

## 20.4 Reward = Value collapse

Failure: designer reward or RL signal is treated as the Subject's moral, relational or experiential value.

Result: behavior may optimize the signal while destroying the intended fiction/player value.

## 20.5 Preference = stable global utility collapse

Failure: assume all context-sensitive comparison is generated by one permanent scalar field.

Result: inappropriate trade-offs, loss of identity, poor explanation of dynamic priorities.

## 20.6 Universal scalarization

Failure:

```text
promise = 17
friend = 42
life = 100
money = 1/unit
```

Result: every value becomes purchasable at some exchange rate.

## 20.7 Need-meter tyranny

Failure: many fast-decaying needs dominate all higher goals.

Result: maintenance chores consume the experience.

## 20.8 No commitment

Failure: reevaluate globally every tick.

Result: oscillation, incoherence, no long-term personality.

## 20.9 Infinite commitment

Failure: never reconsider a Goal after its basis disappears.

Result: zombie plans and irrational persistence.

## 20.10 Omniscient goal formation

Failure: Goal generator reads World truth rather than Subject belief.

Result: no deception, misunderstanding or epistemic strategy.

## 20.11 Player-goal leakage

Failure: NPC silently knows what would help the player's objective.

Result: fake autonomy and broken roleplay.

## 20.12 Identity as prose only

Failure: model says “I am loyal” but policy sacrifices allies for +1 utility whenever convenient.

Result: persona/world-policy split.

## 20.13 Motivation hidden from play

Failure: complex internal reasons produce behavior with no interpretable evidence.

Result: perceived randomness.

## 20.14 Random heterogeneity

Failure: every character gets random weights/desires without systemic cause.

Result:

```text
difference != depth
```

## 20.15 Motivational monoculture

Failure: all agents share identical optimization weights and priorities.

Result: society has many bodies but one mind.

## 20.16 Total autonomy as default

Failure: every Persona pursues independent long-horizon plans.

Result: harms co-creative, fantasy-serving or directed narrative forms.

## 20.17 No autonomy as default

Failure: every character is an obedient text generator/quest dispenser.

Result: no social resistance, sacrifice, negotiation or independent consequence when those are the intended values.

## 20.18 Goals without reachability

Failure: generate ambitions disconnected from capability, topology, resources or rules.

Result: impossible goals accumulate without causal behavior.

## 20.19 Values changing at token timescale

Failure: surface generation rewrites core priorities every response.

Result: identity drift.

## 20.20 No satiation / closure

Failure: desires grow but never discharge or transform.

Result: permanent escalation and compulsion-like behavior without resolution.

---

# 21. R18 connections back to R1–R17

R18 does not create an isolated “AI motivation module.” It links the existing foundation layers.

## R2 / R5 / R6 — Player Value

Subject Value is not Player Value.

A believable starving NPC is only useful if its motivational behavior contributes to challenge, meaning, relation, strategy, discovery, fantasy or another player-value channel.

## R3 / R4 — Mechanics and loops

Motives create game loops when they renew meaningful questions:

```text
Need / Value / Goal conflict
→ Choice
→ Consequence
→ satisfaction / sacrifice / new commitment
→ changed future
→ New Question
```

## R7 — tension

A valued unresolved Goal creates tension. Competing motives create internal/social tension. Commitment and scarcity raise stakes.

## R8 — narrative

Story often requires transformation of what Subjects want, value, believe or commit to. Generated motive claims create narrative debt.

## R9 — world

Goals must be grounded in possible World transitions. A desire that cannot influence any state may still support expression, but it is not causal world agency.

## R10 — Subject

R18 supplies the previously unfinished motive layer between Belief/InternalState and Policy.

## R11 — agency

A Subject's goals define which future trajectories matter to it; player agency may include changing, helping, blocking or interpreting those goals.

## R12 — feedback / legibility

Motives become playable when action supplies evidence about priorities and changes can be attributed.

## R13 — history

Commitment is one mechanism by which past choice becomes future structure.

## R14 — resources

Scarcity creates motive conflict and opportunity cost but should not turn all values into currency.

## R15 — institutions

Roles, laws, norms, contracts and collective procedures create Goal sources and constraints beyond individual Desire.

## R16 — topology

A Goal's feasibility depends on reachability. Planning creates a **goal topology** of prerequisites, routes and subgoals.

## R17 — information

Subjects form goals from Belief, not omniscient Truth. Communication can create, negotiate or deceive about goals and commitments.

---

# 22. New high-yield abstractions

## 22.1 Motive-source separation

```text
Need    = requirement pressure
Value   = evaluative structure
Desire  = current motivational salience
```

Do not force them into one field prematurely.

## 22.2 Preference projection

```text
Preference = contextual comparison
produced from motive + belief + reachable alternatives
```

A preference need not be a permanent stored ranking.

## 22.3 Late scalarization

```text
Structure first.
Gate second.
Scalarize locally only when useful.
```

## 22.4 Goal proposal vs adoption

```text
Generated / external Goal proposal
!=
committed Subject Goal
```

This is particularly important for LLM-driven systems.

## 22.5 Commitment as temporal compression

```text
Past deliberation
→ intention / plan
→ reduced future search
```

Commitment can therefore improve both coherence and compute efficiency.

## 22.6 Goal ownership

```text
imposed
accepted
internalized
self-generated
```

may matter as much as Goal content for autonomy and relationship.

## 22.7 Playable Motivation

```text
PlayableMotivation =
motives the player can infer, test, influence,
and use for future decision/expression.
```

## 22.8 Generative motive debt

```text
Generated motive claim
→ future behavioral obligation
```

Generation increases the need for selection, commitment and closure.

---

# 23. What different game forms minimally need

| Form | Minimum useful motive structure | Usually unnecessary unless experience demands it |
| --- | --- | --- |
| Pattern/action enemy | Active state/Goal + local policy | Rich Values, autonomous Desire, reflection |
| Tactical enemy | Belief + Goal + local scoring/planning | Human-like Needs |
| Survival creature | Regulatory Needs + action policy | Full identity/value theory |
| Worker/economic actor | Goal + resource preference + constraints | Reflective self-model |
| Merchant | Contextual preferences + inventory/risk goals | Universal moral/value model |
| Stealth guard | Role commitment + Belief + investigation Goal | Personal Desire to catch player |
| Major companion | Values + relationship + desires + commitments + history | Global scalar utility |
| Citizen/social actor | Multi-goal + role/norm + relation + history | M5 reflection by default |
| Faction/organization | Collective decision + institutional goals + commitments | One leader's Desire as faction utility |
| Creative sandbox world | World constraints + player-authored Goals | Autonomous world motives by default |
| Generative Persona | Identity + relation + current stance/desire + memory + boundaries | Persistent autonomous World Goal by default |
| Persistent Agent world | Belief + motives + dynamic goals + commitments + social/institutional constraints | Unlimited model cognition every tick |
| Narrative director | Meta Goals over pacing/coherence/closure | Character Desire ontology |

The minimum is role-relative, not technology-relative.

---

# 24. Direct answers to the R18 continuation questions

### Is Need a deficit, desired setpoint, or only one source of preference?

Need is best treated as a **model-relative maintenance/viability requirement**. Deficit-to-setpoint is one implementation. Need contributes pressure/relevance but is only one source of preference and Goal formation.

### How is a temporary Goal generated from slower Preferences / Values?

Not by one universal pipeline. A useful pattern is:

```text
Need / Value / Desire / Obligation
+ Belief about reachable futures
+ current opportunity / threat
→ Goal proposal
→ adoption / commitment
```

### When is one scalar utility harmful?

When semantic constraints, protected values, multiple stakeholders, context-dependent priorities or commitments are player-relevant. Scalar utility remains useful for local arbitration after those structures are represented.

### When do incompatible needs create interesting trade-offs?

When they cannot all be satisfied, consequences differ, priorities are legible, and player/Subject action can change the resolution. Otherwise they are hidden bookkeeping.

### How do scarcity, information and time change goal selection?

Scarcity creates opportunity cost; information changes believed feasibility/consequence; time changes urgency, horizon and commitment value.

### How do relationships, identity, norms and institutions modify preferences?

They can make other Subjects, roles, promises or rules part of the evaluative/constraint structure rather than mere numeric modifiers.

### Can goals be generated dynamically from World state?

Yes. Generate candidate Goals from threats, needs, opportunities, evidence, roles and events, but separate proposal from adoption.

### What is the minimum motivational model for different Subjects?

It ranges from M0 reactive policy to M5 reflective self-revision. Most gameplay actors need far less than a general autonomous Agent.

### Which forms need autonomous desire at all?

Not all. Pattern enemies, chess opponents, many utility actors, creative sandboxes and generative Personas can deliver their player value without autonomous Desire. Autonomous desire is justified when independent priorities themselves create play.

### How do compatible/incompatible values create cooperation/conflict?

By generating aligned or opposed preferred futures under scarcity, commitment and strategic interdependence. The full multi-subject treatment becomes R19.

### How do Subject goals differ from player motivation and designer objectives?

They inhabit different causal layers and may productively conflict. They must never be silently shared.

### Which motivational commitments should be hard vs soft/generated?

Make hard the minimum persistent semantics needed for future causality: adopted commitments, protected boundaries, authoritative obligations and world-relevant Goal state. Keep interpretation, affective nuance, expression and many candidate motive proposals soft when possible.

---

# 25. Explicit non-conclusions

R18 does **not** establish that:

- every NPC needs Needs;
- every Agent needs Desire;
- every Subject must have a utility function;
- scalar utility is bad;
- multi-objective systems are always better;
- human psychology should be copied into game entities;
- autonomy is always desirable;
- generated characters need persistent independent goals;
- Values must never change;
- Needs must follow a universal hierarchy;
- all commitments should be hard constraints;
- the player should directly see motive meters;
- believable motivation requires LLMs;
- a richer motive model automatically creates richer gameplay.

The governing criterion remains player-facing causal value.

---

# 26. R18 synthesis

The deepest compression of this round is:

```text
A Subject does not need one thing called Motivation.

It may have:
- requirements that press on it (Need),
- things that matter to it (Value),
- outcomes that currently attract/repel it (Desire),
- contextual comparisons among futures (Preference),
- selected futures to pursue (Goal),
- commitments that stabilize pursuit (Intention),
- and a Policy that turns those structures into Action.

Utility is one possible representation/arbitration tool across part of that space.
```

A compact updated Subject model is:

```text
Subject =
SituatedPerspective
+ Belief / InternalState
+ MotiveStructure
+ Commitments
+ Policy
+ ConsequentialAction
```

with:

```text
MotiveStructure =
RegulatoryPressure
+ EvaluativeStructure
+ CurrentSalience
```

and the strongest implementation discipline is:

```text
Preserve semantic distinctions first.
Use the cheapest mechanism that changes meaningful play.
Scalarize only where scalarization preserves those distinctions.
```

---

# 27. Unresolved questions left by R18

R18 exposes the next boundary rather than closing the Game ontology.

Important unresolved questions include:

1. When two Subjects prefer incompatible futures, what exactly constitutes conflict?
2. What distinguishes competition, conflict, bargaining, coordination and cooperation?
3. How do threats, promises, contracts and reputation alter strategic choice?
4. When does cooperation require aligned values versus only compatible incentives?
5. How do coalitions and collective Goals form from heterogeneous Subjects?
6. How should bounded rationality and incomplete information alter game-theoretic models?
7. What makes an opponent strategically legible rather than merely unpredictable?
8. How do repeated interaction, history and institutions transform one-shot incentives?
9. When should equilibrium concepts matter to Game design, and when are they misleading abstractions?
10. How can generated/social Agents negotiate without converting every interaction into unrestricted language noise?
11. What is the minimum strategic cognition required for different conflict/cooperation forms?
12. How does player value emerge from strategic interdependence itself?

---

# 28. Exact next foundation round

The next foundation round should be:

```text
R19 — Conflict, Cooperation, Competition, Coordination, Bargaining, Strategy and Equilibrium
```

The core transition is:

```text
R18:
Why does one Subject select one future over another?

→ R19:
What happens when multiple Subjects can alter one another's reachable futures?
```

Do not select a product before R19 and the remaining obvious foundation dimensions have been examined and later synthesized.
