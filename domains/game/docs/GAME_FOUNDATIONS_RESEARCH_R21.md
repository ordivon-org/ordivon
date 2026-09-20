---
schema_version: 1
id: game.foundations-research.r21
title: Ordivon Game Foundations Research — R21 Embodiment, Control, Input, Skill, Affordance, Game Feel and Presence
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
summary: Canonical R21 decomposition of Embodiment, Body, Avatar, Presence, Control, Input, Command, Delegation, Skill, Affordance, Action Resolution, Responsiveness, Feedback, Game Feel, Friction, Automation and Sense of Agency across action, strategy, creative, social and generative game forms.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.r18
  - game.foundations-research.r19
  - game.foundations-research.r20
  - game.foundations-research.map
  - game.foundations-research.continuation
  - game.core-research.reset
---
# Ordivon Game Foundations Research — R21 Embodiment, Control, Input, Skill, Affordance, Game Feel and Presence

## 0. Status and boundary

R21 continues the foundation programme after R1–R20. It is a **research record**, not a product specification and not a G0–G8 promotion.

R20 asked:

> How does a participant intentionally shape new Form, and which decisions make that Form attributable to them?

R21 asks:

> How does participant intent become controlled action through an interface, body or delegated executor, and why do some consequences feel like “I did that” while others feel system-authored?

The overloaded terms under attack are:

```text
Embodiment
Body
Avatar
Control Locus
Presence
Control
Input
Command
Direct Manipulation
Delegation
Automation
Shared Control
Motor Skill
Cognitive Skill
Affordance
Capability
Action Legality
Control Mapping
Action Resolution
Responsiveness
Latency
Feedback
Game Feel
Friction
Sense of Agency
Body Ownership
Self-location
```

The starting warnings are:

```text
Input != Action
Action != Outcome
Control != Agency
Objective control != Sense of Agency
Sense of Agency != Body Ownership
Avatar != Body
Body != Character model
Embodiment != Presence
Presence != Immersion hardware
Direct manipulation != More agency by definition
More buttons != More control
More control bandwidth != More player value
Lower latency != Always better feel
Automation != Agency loss by definition
Shared control != Player control divided by a fixed percentage
Affordance != UI hint
Capability != Affordance != Legality
Game Feel != Visual polish
```

No product is selected by R21.

---

# 1. External anchors and what they do — and do not — establish

R21 triangulates direct-manipulation HCI, motor-control research, experimental work on sense of agency, ecological affordance research, virtual-body ownership experiments, mixed-initiative interaction and shared-control studies. These sources pressure-test the model; none supplies a complete Game ontology.

## 1.1 Direct manipulation — why visible, incremental and reversible control feels powerful

Shneiderman's direct-manipulation work identified a family of interaction properties including visibility of the object of interest, rapid/incremental/reversible actions and replacing complex command syntax with operations directly on visible objects.

Game lesson:

```text
Control can become easier to learn when
Action representation
is close to
Perceived object/state transformation.
```

But directness is not a universal optimum. Strategy, programming, orchestration and delegation can become more powerful precisely by operating at a higher semantic level.

Therefore:

```text
Directness != Agency
```

## 1.2 Motor control uses prediction, not reaction alone

Wolpert, Ghahramani and Jordan's sensorimotor experiments provided evidence supporting internal-model accounts in which the nervous system predicts aspects of movement dynamics rather than controlling only through slow retrospective correction.

Game lesson:

```text
Learned Control Feel depends partly on prediction:
“What will this input do next?”
```

Stable dynamics and timely feedback therefore matter because the player learns a control model, not merely a button dictionary.

## 1.3 Sense of agency can be measured separately from objective causation

Haggard, Clark and Kalogeras showed an intentional-binding effect: perceived timing of voluntary actions and their effects shifted toward one another in awareness, unlike involuntary movements. Later experiments show that action–outcome delay can reduce explicit agency judgments.

Game lesson:

```text
Objective causal link
and
experienced authorship of an action/outcome
are related but not identical.
```

This is the action-domain analogue of R20's distinction between causal authorship and mere surface production.

## 1.4 Ownership and agency are dissociable

Kalckert and Ehrsson manipulated a moving rubber hand and found that ownership and agency can be experimentally dissociated: passive movement can preserve ownership while reducing agency, while other manipulations can affect ownership differently from agency.

Game lesson:

```text
“This body is mine”
and
“I caused this movement”
are separate dimensions.
```

A player can identify with a character while having weak moment-to-moment control, or control an external tool strongly without treating it as part of the self.

## 1.5 Virtual embodiment can recruit body ownership

Slater and colleagues demonstrated that immersive first-person virtual-body manipulations can induce body-transfer/ownership effects under controlled conditions.

Game lesson:

```text
Embodiment is not merely visual resemblance.
Perspective, multisensory correlation and control contingencies can alter bodily self-attribution.
```

R21 does not conclude that stronger body illusion is always better Game value.

## 1.6 Affordances are relational

Warren's stair-climbing experiments showed that perceived climbability boundaries scaled with the relation between environmental structure and the participant's body dimensions, rather than with absolute stair height alone.

Game lesson:

```text
Affordance is not a property of the object alone.
It is a relation between environment and actor capability.
```

The same ledge can afford crossing for one body/capability and not another.

## 1.7 Shared control can increase performance while changing agency in non-monotonic ways

Wen, Yamashita and Asama studied continuous action with computer assistance that suppressed erroneous commands. In difficult/uncertain conditions, assistance improved performance and could increase reported sense of agency despite reducing exact command-to-action correspondence.

Game lesson:

```text
Raw control share ↓
does not imply
Sense of Agency ↓
```

if assistance preserves the participant's higher-level intention and makes outcomes feel more successfully caused by that intention.

Other shared-control work also shows that more autonomy can reduce agency in some settings. Therefore the relation is conditional, not monotonic.

## 1.8 Mixed initiative reframes automation as authority allocation

Horvitz's mixed-initiative work argues for coupling direct manipulation and automated services rather than treating them as mutually exclusive categories.

Game lesson:

```text
The right question is not:
“Manual or automated?”

It is:
“Which layer of intent, choice, execution and correction belongs to whom?”
```

### Reference anchors used in this round

- Shneiderman, B. (1983), *Direct Manipulation: A Step Beyond Programming Languages*.
- Wolpert, D. M., Ghahramani, Z. & Jordan, M. I. (1995), *An Internal Model for Sensorimotor Integration*.
- Haggard, P., Clark, S. & Kalogeras, J. (2002), *Voluntary action and conscious awareness*.
- Haggard and related intentional-action experiments on prediction, action–outcome timing and agency.
- Warren, W. H. (1984), *Perceiving affordances: Visual guidance of stair climbing*.
- Slater, M., Spanlang, B., Sanchez-Vives, M. V. & Blanke, O. (2010), *First Person Experience of Body Transfer in Virtual Reality*.
- Kalckert, A. & Ehrsson, H. H. (2012), *Moving a Rubber Hand that Feels Like Your Own: A Dissociation of Ownership and Agency*.
- Wen, W., Yamashita, A. & Asama, H. (2015), *The Sense of Agency during Continuous Action: Performance Is More Important than Action-Feedback Association*.
- Horvitz, E. (1999), *Principles of Mixed-Initiative User Interfaces*.
- later human–machine shared-control studies used as contemporary pressure tests rather than universal laws.

These are evidence sources and counterexamples, not authorities over Ordivon Game semantics.

---

# 2. Core term separation

| Term | Working meaning | Not equivalent to |
| --- | --- | --- |
| **Intent** | Participant's current desired action/effect/direction at the relevant control layer. | Input signal, executed action. |
| **Input** | Observable signal supplied to the system: button, stick, pointer movement, speech, text, gesture, gaze, etc. | Intent or authoritative action. |
| **Command** | Interpreted semantic instruction that specifies an action/goal/constraint at some abstraction level. | Physical input event. |
| **Control Mapping** | Function/process mapping input or command into candidate system action/control signal. | World resolution or consequence. |
| **Action Resolution** | Authoritative application of capability, rules, environment and competing effects to determine what actually happens. | Input mapping. |
| **Control** | Causal capacity to influence action/state/outcome through an available mapping. | Agency, freedom, ownership. |
| **Control Locus** | Entity/state/surface through which participant control is projected into the system. | Necessarily an avatar/body. |
| **Body** | A self-relevant action–perception substrate whose state shapes sensing, capability, vulnerability and spatial/reference relations. | Character model, avatar asset. |
| **Avatar** | Represented in-world proxy associated with a participant/subject. | Necessarily experienced body. |
| **Embodiment** | Integration/experience of perceiving and acting through a body as a locus of self-location, ownership and/or agency. | Presence, identification, camera view. |
| **Presence** | Felt situatedness in a mediated world/situation such that it functions as the current locus of perception/action/concern. | Embodiment, graphical fidelity. |
| **Sense of Agency** | Subjective experience/belief that one's intention/action caused or controlled an action/outcome. | Objective control. |
| **Body Ownership** | Experience that a body/body-part belongs to oneself. | Sense of agency. |
| **Self-location** | Experienced location of oneself relative to a body/world. | Camera coordinates. |
| **Capability** | What an actor/system can actually execute under its current abilities/resources. | Affordance or legality. |
| **Affordance** | Action possibility arising from relation between actor capability and environment structure. | Button prompt or object property alone. |
| **Perceived Affordance** | Actor/player belief about what actions the situation affords. | Actual affordance. |
| **Action Legality** | Whether authoritative rules/admission permit an otherwise describable/capable action now. | Physical affordance. |
| **Skill** | Learned ability to produce reliably better task-relevant action/decision through practice and adaptation. | Difficulty, complexity, knowledge alone. |
| **Motor Skill** | Skill in temporally/spatially controlling continuous or discrete movement through action–feedback loops. | Strategic choice quality. |
| **Cognitive/Decision Skill** | Skill in selecting, planning, predicting or reasoning among actions. | Motor execution. |
| **Responsiveness** | How promptly, predictably and proportionately system state/feedback responds to participant control. | Latency alone. |
| **Game Feel** | Moment-to-moment phenomenology produced by control mapping, dynamics, timing, feedback, resistance, audiovisual expression and consequence. | Polish, animation quality alone. |
| **Friction** | Effort/cost/resistance between intent and desired state change. | Always bad UX. |
| **Automation** | System assumes execution/decision work that could otherwise belong to participant/controller. | Full autonomy necessarily. |
| **Delegation** | Participant specifies higher-level intent/goal/constraint while another policy chooses lower-level means. | No control or no agency. |
| **Shared Control** | Multiple controllers jointly influence one action/state trajectory at overlapping or layered control scopes. | Fixed 50/50 authority split. |

Strong compact separations:

```text
Intent != Input != Command != Action != Outcome
Control != SenseOfAgency
Avatar != Body
BodyOwnership != Agency
Affordance != Capability != Legality
Latency != Responsiveness
Automation != Delegation != SharedControl
```

---

# 3. The minimal intent-to-consequence chain

R21 proposes the smallest general control chain as:

```text
Intent
→ Control Expression
→ Input / Command
→ Interpretation / Mapping
→ Candidate Action
→ Capability / Legality / World Resolution
→ Executed Action
→ Consequence
→ Feedback / Perception
→ Attribution
→ Learning / Updated Intent
↺
```

This chain works for:

```text
button press
mouse drag
steering wheel
RTS order
text command
natural-language request
AI delegation
creative manipulation
```

## 3.1 Control Expression

`Control Expression` is the participant's chosen way to externalize intent.

Examples:

```text
Intent: move there
Expression: analog stick direction

Intent: focus fire on target
Expression: select squad + click target

Intent: build a gothic tower
Expression: direct placement / sketch / text command / delegated goal
```

The same Intent can be expressed at different abstraction levels.

## 3.2 Interpretation

Some interfaces barely interpret:

```text
stick x/y
→ acceleration vector
```

Others heavily interpret:

```text
“get us out safely”
→ infer goal + plan + execute many actions
```

Interpretation depth is a major control variable.

## 3.3 Resolution

Even correctly interpreted control may fail because:

```text
insufficient capability
rule prohibition
resource shortage
collision
opponent interference
uncertainty
world dynamics
```

Thus:

```text
InputSucceeded
!= ActionSucceeded
!= GoalSucceeded
```

---

# 4. Objective Control, Action Causality and Sense of Agency

R20 introduced Authorial Causality for artifacts.

R21 introduces the action analogue:

```text
ActionCausality =
important properties of an action/outcome
counterfactually depend on participant intent/control.
```

Ask:

> If the participant had issued a meaningfully different intent/control input, which important properties of the resulting action or trajectory would differ?

## 4.1 Objective control

```text
ObjectiveControl =
actual causal influence over relevant system/action variables.
```

It can be narrow or broad.

A racing player may directly control steering/throttle but not tire simulation.

A commander may control goals/formations but not individual foot placement.

## 4.2 Sense of agency

```text
SenseOfAgency =
experienced attribution that “my intention/action caused this.”
```

It depends on more than objective control.

Relevant cues include:

```text
intent–outcome match
prediction
contingency
timing
feedback
performance
knowledge of assistance
context
```

## 4.3 Action causality does not require direct motor control

A player can have strong ActionCausality over:

```text
army strategy
factory policy
conversation outcome
AI companion task
```

without directly generating every low-level motion.

Therefore:

```text
MotorControlShare != ActionCausality
```

## 4.4 Agency can exist at different layers

One result can have layered agency:

```text
Strategic agency:
I chose the objective.

Tactical agency:
I chose the route/method.

Motor agency:
I executed the movement.

Outcome agency:
My intervention caused success/failure.
```

A system may preserve one while automating another.

---

# 5. Control Locus — a more general primitive than Avatar

Many Game forms have no meaningful avatar.

Examples:

```text
Tetris piece
cursor
camera
army
civilization
factory
conversation persona
abstract card hand
policy editor
```

R21 therefore introduces:

```text
ControlLocus =
the entity/state/surface through which participant intent
is projected into authoritative system change.
```

A Control Locus may be:

```text
single body
vehicle
cursor
selected unit
team
camera
organization
text persona
construction tool
world-level policy
```

## 5.1 Control locus can move

A strategy game can shift:

```text
Army-level command
→ unit selection
→ placement tool
→ diplomacy screen
```

without implying the player changes “body” each time.

## 5.2 Multiple control loci

A player can control several loci simultaneously or hierarchically.

```text
Commander
→ squads
→ units
```

This is distributed control, not necessarily multi-body embodiment.

---

# 6. Body — capability, sensing, vulnerability and reference frame

R21 uses a stricter Body concept than “anything controlled.”

```text
Body =
a self-relevant action–perception substrate whose state
constrains capability, sensing, vulnerability and self/world reference.
```

A body typically has some combination of:

```text
sensor locus
actuator locus
spatial extent
capabilities
movement constraints
vulnerability
action costs
orientation/reference frame
persistent condition
```

## 6.1 Body as possibility boundary

The Body changes what futures are reachable.

```text
Body
→ capability set
→ affordances
→ topology access
→ risk
→ action cost
```

This connects R11 Agency, R14 Resource, R16 Topology and R17 Information.

## 6.2 Body can be nonhuman

```text
car
spaceship
animal
robot
cloud of units
```

may function as a body when they become the player's/Subject's integrated action–perception locus.

## 6.3 Not every vehicle is a body

A vehicle can be:

```text
tool
resource
control locus
embodied extension
```

depending on experience and integration.

Avoid forcing one ontology.

---

# 7. Avatar — representation is not embodiment

```text
Avatar =
represented in-world proxy associated with a participant.
```

It can represent:

```text
identity
location
state
social presence
capability
```

But:

```text
Avatar ✓
Embodiment ✗ possible
```

For example, a player can direct a third-person character more like a strategic piece than a body.

Conversely:

```text
Embodied control feeling
```

can arise around a vehicle/tool even if it is not anthropomorphic.

Therefore:

```text
HumanoidRepresentation != Embodiment
```

---

# 8. Embodiment — self-model integration, not just control

R21 defines:

```text
Embodiment =
integration/experience of perceiving and acting through a Body
as a locus of self-location, body ownership and/or agency.
```

The components can vary independently.

## 8.1 Embodiment profile

```text
EmbodimentProfile = {
  SelfLocation,
  BodyOwnership,
  MotorAgency,
  SensoryContingency,
  Vulnerability / Stakes,
  MorphologicalIdentification
}
```

No one scalar is sufficient.

## 8.2 Ownership and agency can dissociate

A body can feel:

```text
mine but not controlled by me
```

or an external object can feel:

```text
strongly controlled by me but not mine
```

This is experimentally important and Game-design relevant.

## 8.3 Embodiment without realism

Embodiment may depend more on consistent contingency and action–perception coupling than photorealistic anatomy.

Thus:

```text
VisualFidelity != EmbodimentStrength
```

## 8.4 Do text/strategy games have embodiment?

Do not inflate the term.

A text persona can have:

```text
identity
role perspective
control locus
narrative self-model
```

without strong sensorimotor embodiment.

A strategy commander may be spatially/situationally present without a body.

Use `Control Locus`, `Role Identification` or `Perspective` unless Body/self-location/ownership relations are genuinely player-facing.

---

# 9. Presence — situatedness, not body ownership

R21 uses Presence in the limited sense:

```text
Presence =
felt situatedness in the mediated world/situation
such that it functions as the participant's current locus
of perception, action and concern.
```

## 9.1 Presence can exist without body ownership

Examples:

```text
first-person camera with invisible body
strategy table
textual scene
strong audio environment
```

can create forms of situatedness without a virtual-body illusion.

## 9.2 Embodiment can strengthen presence, but they remain distinct

Embodied body transfer can intensify “being there,” but R21 does not collapse them.

```text
Presence != Embodiment
```

## 9.3 Presence is not graphical realism

Presence can arise from:

```text
contingent response
consistent spatial/world rules
attention
stakes
sensory coherence
social/world consequence
```

while high visual fidelity with poor responsiveness may feel detached.

---

# 10. Input — a signal, not the action

Input can be:

```text
button
key
stick
mouse
pointer
touch
gesture
gaze
voice
text
brain signal
```

Input is simply observable control evidence.

## 10.1 Input vocabulary

```text
InputVocabulary =
which signals the interface can distinguish.
```

More signals do not guarantee more meaningful control.

```text
InputCount != ControlDepth
```

## 10.2 Input bandwidth

```text
InputBandwidth =
rate / resolution of distinguishable control information.
```

High bandwidth supports continuous skilled control but can increase physical/cognitive burden.

## 10.3 Semantic bandwidth

Natural language has huge apparent semantic bandwidth, but interpretation uncertainty is high.

Thus:

```text
Large Input Space
!= High Control Fidelity
```

A six-button fighting game can offer more precise control than open-ended language for the actions it cares about.

---

# 11. Command — control at a semantic layer

```text
Command =
an interpreted instruction specifying action, goal or constraint
at a chosen abstraction layer.
```

Examples:

```text
“move unit to X”
“hold this position”
“protect civilians”
“make this more tense”
“build a bridge here”
```

## 11.1 Command does not specify means necessarily

```text
Command
→ lower-level planner/policy chooses execution
```

The higher the abstraction, the greater the interpretation/delegation burden.

## 11.2 Command agency

A player can have strong agency when:

```text
command meaning is predictable
constraints are explicit
execution remains faithful
failure is attributable
feedback shows what happened
```

Thus:

```text
IndirectControl != WeakAgency by definition
```

---

# 12. Direct manipulation, command, delegation and autonomous execution

These should be a spectrum of control topology, not a hierarchy.

## 12.1 Direct manipulation

```text
Participant directly changes or continuously steers
visible object/state representations.
```

Strengths:

```text
fast feedback
local predictability
continuous correction
low semantic interpretation burden
```

## 12.2 Discrete command

```text
Participant selects a semantic action;
system executes predefined means.
```

## 12.3 Delegation

```text
Participant specifies goal / constraints / priorities;
executor chooses substantial means.
```

## 12.4 Autonomous execution

```text
System selects goals and/or means without requiring
participant direction at that control layer.
```

## 12.5 Supervision

```text
System acts autonomously;
participant monitors, intervenes, corrects or approves.
```

## 12.6 Shared control

```text
Human and system simultaneously or sequentially influence
an overlapping trajectory/control variable.
```

Example:

```text
Human steering intent
+
automatic collision avoidance
→ final steering trajectory
```

### Core rule

```text
Control mode should match the player-value layer.
```

Do not direct-manipulate what should feel strategic; do not delegate what should feel skillful.

---

# 13. Control Granularity and Control Horizon

R21 introduces two useful axes.

## 13.1 Control granularity

```text
Fine:
continuous steering / exact placement

Medium:
discrete action / target / formation

Coarse:
goal / policy / value / constraint
```

## 13.2 Control horizon

```text
Immediate:
this frame / second / move

Tactical:
next local sequence

Strategic:
longer trajectory / policy
```

A system can expose:

```text
coarse long-horizon agency
+
fine low-level automation
```

without reducing overall player authorship if the intended experience is command rather than execution.

## 13.3 Control layer mismatch

Failure occurs when the interface exposes control at the wrong level.

Examples:

```text
strategy game forces repetitive unit micromanagement
precision action game auto-aims the intended mastery problem away
creative tool asks text prompts for fine spatial adjustment better served by direct manipulation
```

---

# 14. Control Mapping — the learned relation between expression and action

```text
ControlMapping:
Input / Command
→ Candidate Action
```

Mapping dimensions include:

```text
semantic correspondence
gain/sensitivity
spatial correspondence
temporal correspondence
context dependence
state dependence
reversibility
predictability
```

## 14.1 Natural mapping is not mandatory

A mapping can feel excellent after learning even if arbitrary.

Examples:

```text
WASD
fighting-game motion inputs
rhythm-game lanes
flight controls
```

What matters for mastery is often:

```text
stable
predictable
responsive
expressive
```

rather than physically “natural.”

## 14.2 Mapping should preserve relevant intent

A useful concept:

```text
IntentFidelity =
how reliably the mapping/executor preserves
the distinctions in participant intent that matter to the experience.
```

If two meaningfully different intentions regularly collapse to the same action, agency shrinks.

## 14.3 Mapping can be adaptive

Adaptive controls may help accessibility/performance, but if the mapping changes invisibly:

```text
learned prediction breaks
→ attribution breaks
→ mastery breaks
```

Adaptation should therefore be legible, bounded or inferable when skill learning matters.

---

# 15. Action Resolution — Game authority lives after input

The player does not directly write World truth merely because input is accepted.

```text
CandidateAction
→ admission / capability / rule / environment / conflict resolution
→ ExecutedAction
→ Consequence
```

This preserves R9 World authority and R19 strategic interaction.

## 15.1 Why missed actions matter

A missed attack can mean:

```text
input not read
mapping error
candidate illegal
stamina insufficient
target moved
dodge/parry
random resolution
latency
```

If these collapse to identical feedback, the player cannot learn control.

## 15.2 Resolution legibility

```text
Good feedback should expose the causal layer
at which intended action diverged from outcome.
```

This is R12 attribution applied to control.

---

# 16. Responsiveness — more than latency

R21 defines:

```text
Responsiveness =
how promptly, predictably and proportionately
system action/feedback changes in response to participant control.
```

Components:

```text
input acquisition delay
processing delay
simulation step
actuation onset
feedback onset
control gain
predictability
continuity
```

## 16.1 Latency

Latency matters, but:

```text
Latency != Responsiveness
```

A low-latency but highly unpredictable mapping can feel worse than a slightly delayed but stable one.

## 16.2 Expected latency

Some fantasy/material systems require delay:

```text
heavy hammer wind-up
large ship turning
spell casting
bureaucratic command
```

The important property is often:

```text
intentional delay
+ anticipatory cue
+ consistent consequence
```

not minimum milliseconds.

## 16.3 Hidden latency is especially damaging

If action delay varies unpredictably without world explanation:

```text
prediction error
→ correction overshoot
→ attribution uncertainty
→ weak control feel
```

---

# 17. Feedback — close the control loop

Control requires usable consequence information.

```text
Action
→ World Change
→ Signal
→ Observation
→ Attribution
→ Correction
```

Feedback can communicate:

```text
action admitted
actuation started
progress
action blocked
impact
error source
resource cost
world consequence
future state change
```

## 17.1 Feedback timing

Immediate feedback can confirm control before the final consequence resolves.

Example:

```text
button press
→ wind-up starts immediately
→ attack lands later
```

This can preserve responsiveness despite delayed outcome.

## 17.2 Multimodal feedback

```text
visual
sound
animation
camera
haptic
text
world reaction
```

may all reinforce the same causal event.

But redundant spectacle without causal information is not necessarily useful.

## 17.3 Feedback fidelity

```text
FeedbackFidelity =
how accurately feedback distinguishes relevant causal states.
```

A loud impact sound for a non-hit creates feel in the short term but damages mental-model accuracy.

---

# 18. Affordance — actor–environment relation

R21 uses a strict relational definition:

```text
Affordance(a, e) =
action possibility enabled by the relation between
Actor a's capability and Environment e's structure/state.
```

Examples:

```text
ledge affords climbing for tall/jumping actor
small gap affords passage for small body
cover affords concealment for crouching actor
terminal affords hacking for actor with tool/skill
```

## 18.1 Affordance is not an object tag alone

```text
“climbable = true”
```

is an implementation shortcut, not the full concept.

The same object may afford different actions to different actors.

## 18.2 Actual vs perceived affordance

```text
ActualAffordance
!= PerceivedAffordance
```

A player can:

```text
miss a real possibility
believe an impossible action is possible
learn capability boundaries through failure
```

This links R17 Belief to action.

## 18.3 Affordance vs capability vs legality

Example:

```text
Actor can physically jump 2m.        → Capability
Gap geometry is within jump range.   → Affordance
Rule forbids jumping while carrying. → Legality
Player believes jump is possible.    → PerceivedAffordance
```

Keeping these distinct prevents opaque action rejection.

## 18.4 Affordance cues

Visual/audio/textual cues can make affordances legible, but:

```text
Cue != Affordance
```

A yellow paint stripe is information about possibility, not the possibility itself.

---

# 19. Skill — learned control, not arbitrary difficulty

```text
Skill =
learned capacity to produce reliably better task-relevant performance
through improved perception, prediction, choice, execution or correction.
```

R21 separates several layers.

## 19.1 Perceptual skill

```text
notice relevant signals / affordances / timing
```

## 19.2 Predictive/model skill

```text
anticipate system/world response
```

## 19.3 Decision skill

```text
select effective action/policy
```

## 19.4 Motor/execution skill

```text
produce precise timing / trajectory / sequence
```

## 19.5 Coordination skill

```text
combine multiple control channels / actors / timing relations
```

## 19.6 Meta-control skill

```text
choose when to direct-manipulate, delegate, automate or intervene
```

AI-rich games may make this increasingly relevant.

## 19.7 Difficulty does not guarantee skill

```text
random punishment
opaque controls
unpredictable latency
```

can increase failure without supporting learnable improvement.

Thus:

```text
Difficulty != SkillDepth
```

---

# 20. Sensorimotor skill — continuous prediction and correction

Continuous action games often create a fast loop:

```text
Perceive
→ Predict
→ Motor command
→ Motion
→ Feedback
→ Error correction
↺
```

The player learns:

```text
control gain
inertia
timing
collision envelope
animation lock
resource timing
```

## 20.1 Skill requires stable learnable dynamics

If the same control state gives arbitrary outcomes, practice cannot build a useful internal model.

```text
Learnability
requires
some causal regularity.
```

## 20.2 Mastery can make action feel automatic

Practice may reduce conscious deliberation while improving performance.

This means:

```text
Less conscious attention
!= Less skill
```

and possibly even:

```text
less explicit agency salience
```

while control remains highly skilled.

Do not measure mastery solely by how cognitively effortful action feels.

---

# 21. Cognitive and strategic skill — control without motor complexity

A turn-based game may have near-zero motor demand but enormous control depth.

Skill can lie in:

```text
model building
prediction
resource planning
risk assessment
strategic inference
creative composition
```

Therefore:

```text
MotorDifficulty != GameSkill
```

This keeps R21 from collapsing Game foundations into action-game theory.

---

# 22. Game Feel — a control-loop phenomenon, not polish

“Game Feel” is used loosely in design discourse. R21 adopts a working decomposition rather than treating it as one mystical property.

```text
GameFeel =
experienced quality of moment-to-moment action–response coupling
arising from:
Control Mapping
+ Dynamics / Resistance
+ Timing / Responsiveness
+ Feedback
+ Sensory Expression
+ Consequence / Stakes
```

## 22.1 Control feel vs spectacle

Particles, screenshake and sound can amplify feel, but if the underlying action mapping is inconsistent:

```text
Presentation cannot fully repair broken causality.
```

## 22.2 Dynamics matter

```text
acceleration
inertia
friction
recoil
wind-up
recovery
momentum
```

create temporal/material structure.

Instant response is not the same fantasy as heavy response.

## 22.3 Anticipation matters

A delayed action can feel responsive if the system immediately acknowledges intent and clearly enters a predictable trajectory.

```text
Intent
→ immediate anticipation cue
→ delayed physical consequence
```

## 22.4 Consequence matters

A beautifully animated hit that does not alter relevant world state can feel hollow.

```text
SensoryImpact != ConsequentialImpact
```

Strong feel often aligns both.

## 22.5 Game Feel can exist outside action games

Examples:

```text
snappy card placement
responsive city-building placement
clear RTS order acknowledgement
fast undo in creative tool
text system that visibly parses and commits commands
```

The temporal scale differs, but action–response phenomenology remains.

---

# 23. Friction — resistance can be value or waste

```text
Friction =
effort, delay, uncertainty or resistance between intent and desired state change.
```

R21 separates types.

## 23.1 Material friction

```text
heavy object
tight steering
resource-limited spell
recoil
terrain
```

Can support embodiment, fantasy and skill.

## 23.2 Execution friction

```text
precise timing
combo execution
manual aiming
```

Can create mastery when intended.

## 23.3 Cognitive friction

```text
reasoning
planning
interpretation
```

Can be gameplay or overhead depending on goal.

## 23.4 Interface friction

```text
menu nesting
unclear bindings
repetitive clicks
input lag
```

Usually weak player value unless intentionally expressive/material.

## 23.5 Coordination friction

```text
communicating / synchronizing with others
```

may be gameplay in co-op systems.

## 23.6 Administrative friction

```text
confirmation spam
inventory bureaucracy
manual cleanup
```

usually automation candidates.

### Core rule

```text
Preserve resistance that carries the intended skill/fantasy/question.
Remove resistance that only obstructs access to it.
```

---

# 24. Automation — control work moves, but agency may or may not

Automation transfers some transformation/decision burden from participant to system.

The crucial question is:

```text
Which distinctions in participant Intent remain causally effective?
```

## 24.1 Automation can preserve higher-level agency

Example:

```text
Player chooses destination and route policy.
Autopilot handles steering micro-corrections.
```

If intended value is navigation/strategy, agency may remain strong.

## 24.2 Automation can erase intended skill

If intended value is manual driving, the same autopilot may destroy the game.

## 24.3 Automation can improve agency under noisy control

Wen-style assistance suggests a key possibility:

```text
remove low-level erroneous commands
→ outcome matches user's higher-level intention better
→ performance and experienced agency can improve
```

Therefore:

```text
Agency is not proportional to raw motor authority.
```

## 24.4 Automation can also weaken agency

If system contribution becomes:

```text
unpredictable
opaque
misaligned
uninterruptible
```

then the participant may lose attribution and control.

## 24.5 The correct automation target

```text
Automate low-value control work
while preserving value-bearing intent distinctions.
```

This is R20's automation boundary translated into action.

---

# 25. Delegation — agency can move upward in abstraction

Delegation means:

```text
Participant selects Goal / Constraints / Priorities
→ Executor selects Means
```

Examples:

```text
RTS squad order
colony worker assignment
AI companion task
navigation autopilot
natural-language “secure this room without casualties”
```

## 25.1 Delegated agency

The user can retain agency if:

```text
goal selection matters
constraints are preserved
executor behavior is predictable enough
failures are legible
intervention/revocation exists where needed
```

## 25.2 Delegation debt

High-level commands create:

```text
interpretation debt
planning debt
exception-handling debt
attribution debt
```

especially with generative/Agent executors.

## 25.3 Delegation without semantic fidelity

A model can produce competent behavior that violates the user's intended constraint.

```text
Goal success
!= Intent success
```

Example:

```text
“save the hostage”
→ executor destroys half the building
```

may succeed on one metric while failing delegated agency.

---

# 26. Shared control — a topology, not a percentage

R21 introduces:

```text
ControlContributionTopology =
who controls which variable / layer / time interval
in the action trajectory.
```

Contributors may be:

```text
player
AI assistant
physics
script
teammate
institution/rules
```

## 26.1 Layered shared control

```text
Human:
goal + direction

AI:
obstacle avoidance

World:
traction / collision
```

This cannot be faithfully summarized as “player has 70% control.”

## 26.2 Blended shared control

Two policies can combine continuously:

```text
u_final = blend(u_human, u_assist)
```

but R21 does not assume linear blending is always correct.

## 26.3 Supervisory shared control

```text
AI acts
Human approves/intervenes
```

## 26.4 Handoff

Control can transfer explicitly:

```text
manual ↔ autopilot
player ↔ companion
human ↔ model
```

Handoff state must be legible when responsibility matters.

---

# 27. Intent Fidelity — the key AI/control variable

R21 proposes:

```text
IntentFidelity =
degree to which distinctions in participant intent
that matter to the experience survive
interpretation, mapping, planning and execution.
```

This can be decomposed:

```text
Goal fidelity
Constraint fidelity
Style/manner fidelity
Timing fidelity
Target fidelity
Risk tolerance fidelity
Stop/revoke fidelity
```

## 27.1 Why intent fidelity beats raw action matching

A shared-control system may deliberately alter exact low-level commands while preserving:

```text
where the user wanted to go
what they wanted to avoid
what outcome they valued
```

and thereby preserve or increase higher-level agency.

## 27.2 Natural-language control

Natural language is powerful because it can express high-level intent.

But it adds:

```text
ambiguity
underspecification
hallucinated assumptions
hidden planning
```

Therefore:

```text
LanguageFluency != IntentFidelity
```

---

# 28. Control Predictability and Counterfactual Learnability

R12's legibility principle applies directly.

A player needs a model of:

```text
If I do X in state S,
what family of outcomes should I expect?
```

R21 calls this:

```text
ControlPredictability
```

## 28.1 Determinism is not required

Stochastic games can remain learnable if distributions/causes are stable enough.

```text
Predictable distribution
can support skill
without deterministic outcome.
```

This becomes a bridge to R22.

## 28.2 Hidden assistance harms learnability if it changes mapping

If aim assist, auto-correction or AI intervention varies unpredictably:

```text
player cannot tell
what their own action caused
```

## 28.3 Legible assistance can become part of the control model

```text
“collision assist corrected right”
```

may allow players to learn the shared controller rather than fight invisible intervention.

---

# 29. Error, failure and repair

Control feels meaningful partly because error is attributable and repairable.

## 29.1 Error types

```text
Input error
Interpretation error
Execution error
Prediction error
World/opponent interference
System fault
```

## 29.2 Good failure teaches the layer

```text
Missed because timing late
```

supports motor learning.

```text
Command rejected because target unavailable
```

supports semantic learning.

```text
AI deviated because safety constraint activated
```

supports shared-control learning.

## 29.3 Bad failure is causally opaque

```text
Nothing happened.
```

provides almost no useful model update.

---

# 30. Action ownership, responsibility and consequence

R21 avoids using “ownership” casually because Body Ownership and R14 ownership already have specific meanings.

For actions use:

```text
ActionAttribution
Responsibility
SenseOfAgency
ActionCausality
```

## 30.1 Responsibility can exceed motor control

A commander can be responsible for an order carried out autonomously.

An AI-assisted driver can remain responsible for selecting risky policy even if low-level control is automated.

Thus:

```text
Responsibility != MotorControlShare
```

## 30.2 Responsibility needs legible authority

If automation secretly overrides the user, moral/strategic responsibility becomes ambiguous.

Game systems should clarify authority when consequence/meaning depends on it.

---

# 31. Presence and stakes

Presence is strengthened when the world is not merely displayed but responds to the participant as a situated locus.

Relevant contributors can include:

```text
consistent spatial reference
responsive world
persistent consequences
body/control contingency
social acknowledgement
risk/vulnerability
attention
```

## 31.1 Vulnerability can deepen embodiment/presence

If damage/state applies to the controlled body and changes future capability:

```text
Body state
→ future action space
```

then the body is more than a cosmetic proxy.

## 31.2 Presence without risk is possible

Creative or contemplative experiences may create situatedness without threat.

Risk is one contributor, not a requirement.

---

# 32. Minimum sufficient embodiment/control complexity

Not a maturity ladder. Use the lowest level that creates the intended player-facing distinction.

## EC0 — Abstract selection

```text
Choose among symbolic actions.
```

No body or continuous control required.

Examples:

```text
card game
turn-based menu
```

## EC1 — Control locus + discrete mapping

```text
Input/command
→ visible state/action
```

Examples:

```text
cursor
piece movement
basic platform input
```

## EC2 — Learnable dynamic control

```text
continuous/discrete motor mapping
+ timing/dynamics
+ rapid feedback
```

Examples:

```text
platformer
vehicle
shooter
rhythm
```

## EC3 — Embodied body loop

```text
EC2
+ body/self-location/vulnerability/ownership-relevant cues
```

Useful when bodily presence matters.

## EC4 — Shared/delegated control

```text
multiple control contributors
+ explicit authority/intent preservation
+ intervention/handoff
```

Examples:

```text
AI companion command
assistive steering
squad delegation
```

## EC5 — Meta-control / configurable control ecology

```text
player chooses/configures who controls which layer
and can reshape control topology itself.
```

Examples:

```text
programmable automation
delegation policies
role assignment
adaptive assist configuration
```

### Core rule

```text
ControlComplexity should increase
only when it creates a new playable agency/skill distinction.
```

---

# 33. Cross-form falsification tests

## 33.1 Chess

Chess has:

```text
strong agency
strong strategic skill
almost no motor skill requirement
no avatar embodiment required
```

Conclusion:

```text
Agency != Embodiment
Skill != MotorSkill
```

## 33.2 Platformer

Player value can strongly depend on:

```text
mapping
jump arc
acceleration
timing
collision
feedback
```

Here R21 is central.

Automating jump timing could destroy intended skill even if completion rate improves.

## 33.3 Fighting game

Strategic choices and motor execution are tightly coupled.

```text
DecisionSkill
+
ExecutionSkill
+
Timing
+
Opponent model
```

A control scheme can simplify execution while preserving strategic mind games — or erase meaningful distinctions if too aggressive.

## 33.4 Racing/vehicle

A vehicle can become an embodied control locus through stable dynamics and predictive sensorimotor coupling even without humanoid form.

Assists such as traction control may preserve high-level driving intent while automating low-level stabilization.

Whether this helps depends on intended mastery.

## 33.5 RTS

Player controls:

```text
selection
commands
formations
goals
```

while units execute motion.

Strong agency exists at command level with low motor embodiment.

Micromanagement is valuable only if execution/timing is intended skill.

## 33.6 Colony sim

Delegated actors can preserve player agency through:

```text
priorities
policies
zones
roles
```

Player does not need to puppeteer each worker.

## 33.7 Creative editor

Direct manipulation often improves local spatial authorial causality:

```text
drag object
→ object moves immediately
```

while AI generation may operate at coarse semantic layers.

Strong systems may combine both.

## 33.8 Text adventure

Control is semantic and discrete:

```text
text command
→ interpretation
→ world resolution
```

There may be almost no sensorimotor embodiment, but agency can be high if parsing and consequence are faithful/legible.

## 33.9 SillyTavern-like Persona interaction

The user's control locus can be:

```text
own character voice
scene direction
relationship stance
meta-instruction
```

Natural language provides high semantic expressiveness but weak hard control unless the system distinguishes:

```text
statement
intent
proposal
world authority
```

R17/R19 remain necessary.

## 33.10 AI companion

Player says:

```text
“watch the north door; don't engage unless seen”
```

Strong delegated agency requires preserving:

```text
target
constraint
engagement threshold
revocability
feedback
```

The companion need not execute the exact motor policy the player would have chosen.

## 33.11 Autoplay

Autoplay can preserve:

```text
progress
spectacle
strategy set earlier
```

but removes moment-to-moment action agency.

That can be correct if action execution is not the current consumption goal.

## 33.12 Turn-based generative game

A player can have high agency with seconds of model latency if:

```text
turn commitment is explicit
system acknowledges request state
result arrives predictably
causality is legible
```

Low real-time responsiveness is not always necessary.

## 33.13 VR body experience

Embodiment may depend on:

```text
first-person perspective
visuomotor contingency
body ownership cues
self-location
```

but stronger embodiment does not guarantee better mechanics, challenge or meaning.

## 33.14 Accessibility assistance

Auto-aim, timing assistance, remapping or command compression can increase the set of players able to express intended decisions.

```text
Raw execution burden ↓
can yield
Agency access ↑
```

if value-bearing distinctions remain.

---

# 34. Playable Control

R21 adds another Playable-X member.

```text
PlayableControl =
a control relation whose relevant mappings, constraints,
assistance and consequences can be learned/predicted,
and whose meaningful outcome differences remain sensitive
to participant intent.
```

A powerful control system fails player-facing value when:

```text
it interprets too much invisibly
changes mappings unpredictably
hides assist authority
or removes intended skill distinctions
```

## 34.1 Playable Embodiment

R21 also uses:

```text
PlayableEmbodiment =
body/self-location/agency relations that materially alter
perception, capability, risk, identity or action choices
and remain experientially legible.
```

A decorative first-person body with no causal relevance can be visually rich but gameplay-thin.

---

# 35. Control Contribution Topology

R20 introduced Creative Contribution Topology.

R21 introduces the action analogue:

```text
ControlContributionTopology =
which participant/system controls which
intent, variable, action layer, time interval or correction path.
```

Possible nodes:

```text
Player
AI assistant
NPC policy
Physics
Script
Other player
Institution/rule
```

Possible edge targets:

```text
Goal selection
Target selection
Path planning
Timing
Trajectory
Safety correction
Action admission
Outcome resolution
Feedback
```

## 35.1 Why topology beats “percent control”

Example:

```text
Player:
100% goal
100% target
30% steering micro-correction

AI:
70% collision correction
0% goal
```

A single `player_control = 65%` scalar destroys the relevant structure.

---

# 36. Generative/Agent control debts

R21 adds new debts to the generative stack.

```text
Generated Command Interpretation
→ semantic fidelity debt

Delegated Goal
→ planning / exception debt

Autonomous Action
→ attribution / responsibility debt

Adaptive Assist
→ mapping-legibility debt

Generated Animation / Feedback
→ causal-truthfulness debt

AI Correction
→ skill-preservation debt

Shared Control
→ authority / handoff debt

Embodied Agent Avatar
→ ownership / contingency consistency debt
```

Again:

```text
More capable automation
moves scarcity toward
intent preservation, legibility, intervention and attribution.
```

---

# 37. Major collapse / failure modes

## 37.1 Input = intent collapse

Failure: assume button/text literally equals intended meaning.

Result: interpretation errors become invisible.

## 37.2 Input = action collapse

Failure: accepted input treated as guaranteed world action.

Result: capability/rule/world resolution becomes incoherent.

## 37.3 Objective control = agency collapse

Failure: causal control percentage treated as subjective agency.

Result: misses prediction, performance, interpretation and attribution.

## 37.4 Agency = ownership collapse

Failure: controlling a body means feeling it is one's body.

Result: ignores experimentally separable dimensions.

## 37.5 Avatar = body collapse

Failure: any player representation is assumed embodied.

Result: conflates strategic proxies with self-body experience.

## 37.6 Embodiment = presence collapse

Failure: bodily ownership and situatedness treated as one thing.

Result: cannot reason about bodiless presence or weak presence despite avatar ownership.

## 37.7 More buttons = more control collapse

Failure: input vocabulary used as control-depth proxy.

Result: clutter without meaningful distinctions.

## 37.8 Higher bandwidth = more agency collapse

Failure: continuous input assumed superior to commands.

Result: command/strategy forms undervalued.

## 37.9 Direct manipulation = best interface collapse

Failure: all high-level problems forced into manual manipulation.

Result: micromanagement and scale failure.

## 37.10 Delegation = no agency collapse

Failure: low-level executor chooses means, so player is considered passive.

Result: ignores goal/constraint-level agency.

## 37.11 Automation = agency loss collapse

Failure: any machine correction treated as stealing control.

Result: misses assistance that preserves higher-level intent or accessibility.

## 37.12 Performance = agency collapse

Failure: successful outcome automatically means high agency.

Result: lucky/fully automated success mistaken for player causality.

## 37.13 Intent success = goal success collapse

Failure: goal achieved while manner/constraints violated.

Result: delegation feels unfaithful.

## 37.14 Latency = responsiveness collapse

Failure: one millisecond number defines feel.

Result: ignores predictability, acknowledgement, gain and dynamics.

## 37.15 Lowest latency = best feel collapse

Failure: remove intended anticipation/inertia.

Result: heavy/physical fantasy collapses into twitch response.

## 37.16 Game Feel = polish collapse

Failure: add particles/screenshake without fixing mapping/consequence.

Result: spectacle masks weak causality.

## 37.17 Feedback = decoration collapse

Failure: sensory effects do not truthfully correspond to world consequence.

Result: mental model degrades.

## 37.18 Affordance = cue collapse

Failure: yellow paint/button prompt treated as affordance.

Result: actor–environment capability relation is lost.

## 37.19 Capability = legality collapse

Failure: physically possible and rule-permitted actions conflated.

Result: opaque rejection and inconsistent systems.

## 37.20 Difficulty = skill collapse

Failure: arbitrary execution burden called mastery.

Result: failure without learnable improvement.

## 37.21 Motor skill = all skill collapse

Failure: turn-based/strategic/creative competence discounted.

Result: action-game bias.

## 37.22 Friction = bad collapse

Failure: remove every resistance.

Result: materiality, commitment and skill can disappear.

## 37.23 Friction = depth collapse

Failure: preserve tedious interface work because it is “hard.”

Result: overhead masquerades as mastery.

## 37.24 Adaptive control without legibility

Failure: aim/mapping silently changes.

Result: unstable learning and weak attribution.

## 37.25 Invisible shared control

Failure: player cannot know when system intervened.

Result: responsibility and learning become ambiguous.

## 37.26 Uninterruptible delegation

Failure: user can issue high-level goal but cannot revoke/correct when executor diverges.

Result: nominal agency without operational authority.

## 37.27 Natural-language fluency = control fidelity collapse

Failure: eloquent response mistaken for faithful execution.

Result: semantic drift hidden by prose quality.

## 37.28 Embodiment maximalism

Failure: every game tries to maximize body ownership/presence.

Result: unnecessary hardware/representation complexity and loss of abstract forms.

## 37.29 No-body bias

Failure: abstract games treated as less agentic because they lack avatar embodiment.

Result: confuses sensorimotor presence with meaningful decision control.

## 37.30 Assistance destroys skill by default

Failure: reject accessibility/assist mechanisms without identifying which skill distinctions matter.

Result: exclusion without preserving additional value.

## 37.31 Assistance preserves skill by default

Failure: add strong assistance that solves the intended execution problem.

Result: mastery loop disappears.

## 37.32 Outcome without attribution

Failure: system succeeds/fails but player cannot tell why.

Result: no control learning.

---

# 38. R21 connections back to R1–R20

## R1 — GameForm

Control is already one GameForm axis. R21 shows it is multidimensional: directness, abstraction, granularity, horizon, mapping, embodiment and authority can vary independently.

## R2 / R5 / R6 — Player Value

Control can produce Ability/mastery, Decision power, World participation and Meaning/identity. High responsiveness has no value if the underlying action is not worth doing.

## R3 — Mechanics

Mechanics require an actionable interface from participant intent into state transition. R21 decomposes that interface rather than equating mechanic with button.

## R4 — Loops

Fast control loops and slower command/delegation loops share the same Question → Choice → Consequence → Learning structure at different temporal scales.

## R7 — Difficulty / tension

Execution friction and timing can create tension when learnable and valued; opaque latency/random rejection cannot be justified merely as difficulty.

## R8 — Narrative

Embodied action can intensify narrative consequence, but text/roleplay can retain strong agency without bodily control. Generated action descriptions must preserve causal truth.

## R9 — World

Input does not write World truth. Action Resolution remains World-authoritative.

## R10 — Subject / Agent

A Subject may have Body, control locus and policy, but not every Actor/Agent needs embodiment. Delegated Agent execution can extend player control without becoming player identity.

## R11 — Agency

R21 operationalizes Agency into control layers and ActionCausality. Freedom, input count and direct manipulation remain distinct from meaningful trajectory control.

## R12 — Feedback / learning

Control becomes playable only when mappings, failures and assistance are attributable enough to build a useful mental model.

## R13 — Learning / history

Skill is learned control structure. Repeated action produces internalized mappings, habits, style and possibly automatization.

## R14 — Resource

Bodies/tools/resources constrain capability; control itself can be a scarce capability. Stamina/fuel/time can change affordances.

## R15 — Institution

Authority structures can determine who is allowed to command whom; automation/delegation can be institutional rather than merely technical.

## R16 — Topology

Body/capability changes reachable space. Affordances are local actor–environment reachability relations.

## R17 — Information

Perceived affordance, command interpretation and action feedback depend on bounded belief. UI defines the player's control/observation coupling.

## R18 — Motivation

Intent is not identical to Desire/Goal. Control can express a current intention while longer-term commitment remains elsewhere.

## R19 — Strategy

Command/delegation changes strategic action granularity; shared control can preserve strategic agency while automating tactics.

## R20 — Creation / authorship

Authorial Causality has an action counterpart in ActionCausality. Creative tools distribute control over form; direct manipulation vs generation is a control-allocation question.

---

# 39. New high-yield abstractions

## 39.1 Intent-to-consequence chain

```text
Intent
→ Expression
→ Input / Command
→ Mapping / Interpretation
→ Candidate Action
→ Resolution
→ Consequence
→ Feedback
→ Attribution
→ Learning
```

## 39.2 Action Causality

```text
ActionCausality =
important outcome properties counterfactually depend
on participant intent/control.
```

## 39.3 Control Locus

```text
ControlLocus =
where participant control enters authoritative state change,
without assuming a body/avatar.
```

## 39.4 Intent Fidelity

```text
IntentFidelity =
value-bearing distinctions in participant intent
survive interpretation, planning and execution.
```

## 39.5 Control Contribution Topology

```text
Who controls which layer / variable / time interval
matters more than one “percent human control” scalar.
```

## 39.6 Agency is layer-relative

```text
Strategic agency
Tactical agency
Motor agency
Outcome agency
```

can vary independently.

## 39.7 Agency is not proportional to motor authority

```text
Low-level assist can reduce exact motor control
while preserving or increasing higher-level agency.
```

## 39.8 Affordance is relational

```text
Affordance = ActorCapability × EnvironmentStructure relation
```

not an object tag.

## 39.9 Responsiveness is prediction-friendly response

```text
Responsiveness =
promptness + predictability + proportionality + feedback coherence
```

not latency alone.

## 39.10 Game Feel is causal phenomenology

```text
GameFeel =
control mapping + dynamics + timing + feedback + sensory expression + consequence
```

## 39.11 Preserve value-bearing friction

```text
Resistance can carry skill/fantasy/materiality.
Overhead does not become value merely because it is difficult.
```

## 39.12 Playable Control

```text
Control becomes gameplay when mappings and assistance are learnable
and meaningful outcomes remain sensitive to participant intent.
```

---

# 40. Direct answers to the R21 continuation questions

### What counts as embodiment across avatar, cursor, vehicle, camera, army, text persona and abstract policy?

Use `Control Locus` broadly. Reserve `Embodiment` for cases where acting/perceiving through a self-relevant Body involves self-location, ownership and/or agency. A vehicle can become embodied; a cursor or army need not be called a body merely because it is controlled.

### How do Intent, Input, Mapping, Resolution and Feedback differ?

Intent is what the participant means to do; Input/Command is how that intent is expressed; Mapping/Interpretation creates a candidate action; Resolution applies capability/rules/world interaction; Feedback reveals what happened and why.

### What makes a state change feel causally owned by the player?

Not one variable. Strong sense of agency is supported when intention predicts outcome, action–effect contingency is coherent, timing/feedback are usable, assistance is aligned/legible and the result can be attributed to participant intervention.

### How do direct manipulation, command, delegation and autonomous execution differ?

They place participant authority at different abstraction levels. Direct manipulation specifies local transformation; command specifies semantic action; delegation specifies goals/constraints while executor selects means; autonomous execution selects more of both goals and means.

### How does sensorimotor skill differ from symbolic/strategic skill?

Sensorimotor skill depends heavily on fast perception–prediction–execution–feedback loops; symbolic/strategic skill can operate through slow discrete choices and models. Both are genuine skill and can coexist.

### What is Affordance relative to Capability, Perception and Legality?

Capability belongs to the actor; affordance arises from actor–environment fit; perceived affordance is belief about that fit; legality is authoritative permission under current rules.

### What is Game Feel?

A working causal decomposition of moment-to-moment action–response phenomenology: mapping, dynamics/resistance, timing/responsiveness, feedback, sensory expression and consequence. It is not identical to polish.

### When is friction valuable?

When resistance constitutes intended materiality, timing, execution skill, commitment or coordination. It is weak when it merely adds opaque or repetitive access cost.

### How can AI assist control without consuming player value?

Preserve the intent distinctions and skill layer the experience is about. Automate corrections or lower-level execution only when those are not the value-bearing question, and expose intervention/handoff enough for attribution and learning.

### How do embodiment and control change identity/presence?

A stable body/control loop can make capability, vulnerability and self-location personally salient. But role identity and situated presence can exist without strong body ownership, so the dimensions must remain separate.

### What counts as a body in text/generative/strategy forms?

Usually nothing needs to. Use role, perspective, organization or control locus unless the experience genuinely models self-relevant sensing/capability/vulnerability through a body-like substrate.

### How does R21 connect to R20 Authorial Causality?

R20 asks whether artifact properties depend on participant decisions. R21 asks whether action/outcome properties depend on participant intent/control and whether that dependence remains experientially attributable. Both are counterfactual causality plus legibility.

---

# 41. Explicit non-conclusions

R21 does **not** establish that:

- every game needs a body;
- every player representation is an avatar;
- every avatar should be embodied;
- first-person view is inherently more embodied;
- embodiment is required for agency;
- presence requires VR;
- higher presence is always better;
- body ownership and agency are the same;
- more input options create more control;
- direct manipulation is always superior to command;
- command interfaces necessarily reduce agency;
- delegation means the player is passive;
- automation necessarily reduces agency;
- automation necessarily preserves agency;
- shared control can be represented by one percentage;
- lower latency is always better;
- higher responsiveness means instant motion;
- heavier/slower motion is bad feel;
- game feel is audiovisual polish;
- every friction should be removed;
- every friction creates mastery;
- all skill is motor skill;
- difficult controls create deep skill;
- natural mappings are always best;
- natural language provides perfect control fidelity;
- AI assistance should maximize task performance;
- accessibility assistance inherently lowers player authorship;
- strong embodiment requires photorealism;
- abstract/turn-based/text games have weaker agency by definition.

The governing criterion remains player-facing causal value.

---

# 42. R21 synthesis

The deepest compression of R21 is:

```text
Player action is not a button press.

It is a causal chain in which intent is expressed,
interpreted, resolved against the World,
made perceptible through feedback,
and attributed back to the participant.
```

A compact control stack is:

```text
Intent
↓
Control Expression
↓
Input / Command
↓
Control Mapping / Interpretation
↓
Candidate Action
↓
Capability + Affordance + Legality + World Resolution
↓
Executed Action
↓
Consequence
↓
Feedback / Perception
↓
Attribution / Sense of Agency
↓
Learning / Skill / New Intent
↺
```

Embodiment sits around this chain only when a Body becomes a self-relevant action–perception substrate:

```text
Body
= sensing + capability + vulnerability + reference frame
```

R21's strongest control discipline is:

```text
Preserve the player-value layer of Intent.

Do not confuse directness with agency.
Do not confuse automation with agency loss.
Do not confuse performance with authorship of action.
Do not hide which controller caused which relevant consequence.
```

The strongest AI-era design question becomes:

```text
Which meaningful distinctions in the player's Intent
remain causally effective after AI interpretation,
planning, correction and execution?
```

R21 adds:

```text
ActionCausality
ControlLocus
IntentFidelity
ControlContributionTopology
PlayableControl
PlayableEmbodiment
```

to the foundation vocabulary.

---

# 43. Unresolved questions left by R21

R21 makes one adjacent foundational domain unavoidable: games constantly use uncertainty, randomness, probability and risk, but these were previously handled only indirectly through tension, information and strategy.

Important unresolved questions include:

1. What is the difference between uncertainty, ignorance, probability, randomness and unpredictability?
2. What distinguishes aleatory uncertainty from epistemic uncertainty in player experience?
3. What is Risk relative to uncertainty, stakes and controllability?
4. What is Luck, and when is it experienced as fair or unfair?
5. How do deterministic but computationally unpredictable systems differ from stochastic systems?
6. How should players learn probability when exact numbers are hidden or impossible to know?
7. When does randomness increase replayability and when does it destroy agency/skill attribution?
8. How do random input, random transition, random information and random reward differ?
9. How do variance and distribution shape tension differently from mean expected value?
10. What is Fairness relative to symmetry, procedural fairness, perceived fairness and outcome equality?
11. How should games expose uncertainty without turning everything into explicit percentages?
12. How should generative systems represent uncertainty rather than presenting sampled outputs as authoritative confidence?
13. How does uncertainty interact with ActionCausality — when does failure belong to player choice versus chance?
14. How should risk-sensitive Subjects and players differ from expected-utility maximizers?

---

# 44. Exact next foundation round

The next foundation round should be:

```text
R22 — Uncertainty, Probability, Randomness, Risk, Luck, Variance, Determinism and Fairness
```

The transition is:

```text
R21:
How does intent become controlled and attributable action?

→ R22:
What changes when action outcomes, information or future states
cannot be known or controlled exactly?
```

This round should connect R7 tension, R11 agency, R12 learning, R17 belief, R18 utility and R19 strategy without assuming uncertainty is always represented by explicit numeric probabilities.

Do not select a product before R22 and the remaining obvious foundation dimensions have been examined and later synthesized.
