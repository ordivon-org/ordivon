---
schema_version: 1
id: game.deep-foundations.gdf1-e
title: Ordivon Game Deep Foundations — GDF1-E Embodiment / Body / Tool / Avatar Structural Falsification
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Falsifies Embodiment as a single Game construct. Separates biological body, sensor/effector envelope, morphology, avatar representation, control locus, collision body, vulnerability body, tool/vehicle mediation and Human ownership/agency/self-location. Matched probes show visual avatar, collision reachability and vulnerability can vary independently; tool/remote control can extend action without ownership/anatomical continuity. Introduces a sparse optional ActionCouplingProfile as a derived Game-owned structural projection while handing experiential embodiment and body-schema mechanisms to Human/Media. No R29/GDF0 reopen is triggered.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf1-d
  - game.play-game-deep-foundations.v1
---
# Ordivon Game Deep Foundations — GDF1-E

## 0. E asks whether `Embodiment` is even one thing

D established a tension:

```text
Chess / RTS / synthetic control
→ Skill does not require embodiment as a universal condition.

VR / sport / tool / vehicle / accessibility
→ body/tool configuration can change reachable action, sensing and dynamics structurally.
```

So E does not ask:

```text
Does embodiment improve immersion?
```

It asks:

> Which relations historically bundled under `embodiment` have distinct causal roles, and which of them must Game own?

Canonical matrix/probes:

```text
evidence/gdf1-e/embodiment-dissociation-matrix.json
evidence/gdf1-e/embodiment-falsifiers.json
scripts/gdf1-e/embodiment-falsifiers.mjs
scripts/gdf1-e/audit-embodiment.mjs
```

---

# 1. `Embodiment` fails immediately as one Game variable

At minimum we must separate:

```text
BiologicalBody
Morphology
SensorEnvelope
EffectorEnvelope
InputEffector
AvatarAppearance / Representation
ControlLocus
CollisionBody
VulnerabilityBody
Tool / Vehicle Mediation
Peripersonal / action-space representation
Body ownership
Self-location
Sense of agency
```

These are not stylistic variants of one construct.

They occupy different owner layers and produce different counterfactuals.

Therefore:

```text
Embodiment as one Game construct
→ REJECTED.
```

The ordinary word remains useful in prose only if its target is explicitly qualified.

---

# 2. Biological body != Game structural body

The human body contributes:

```text
morphology
sensorimotor capability
fatigue/injury
proprioception
biomechanics
```

in physical/body-tracked forms.

But a conventional platformer may resolve action through:

```text
virtual collision capsule
virtual velocity
virtual reach
```

that does not equal the player's biological morphology.

Chess may need almost none of it for the core Skill claim.

Therefore:

```text
BiologicalBody != StructuralActionBody.
```

And because `StructuralActionBody` still sounds like a single entity, E will decompose it further rather than freeze that noun.

---

# 3. Body scale can be structurally causal

Warren & Whang's aperture experiments show a concrete embodied-action relation: locomotor transitions/passability depend on body-scaled relations such as aperture width relative to shoulder width, not merely absolute environment geometry.

This is exactly the kind of evidence D anticipated.

If Game rules/physics consume a body/collision geometry, changing that geometry can change:

```text
which passages are traversable
whether rotation/crouch is required
collision risk
reachable state transitions
```

Therefore morphology/collision scale can be a genuine Game structural input.

But that does **not** make visual avatar scale identical to morphology.

---

# 4. Avatar appearance != collision body

E's first matched structural probe holds collision width fixed while visually rescaling the avatar.

```text
avatar mesh scale: 1.0 → 0.5
collision width:   0.8 → 0.8
```

Passability is unchanged in the declared Game model.

Second probe holds visual avatar fixed while changing collision width:

```text
avatar mesh scale: 1.0 → 1.0
collision width:   0.8 → 1.2
```

Passability changes.

Therefore:

```text
AvatarAppearance != CollisionBody.
```

This is foundational for Game analysis because many engines already make these technically separable, but the research consequence is deeper: visual self-representation and authoritative action geometry are different evidence targets.

---

# 5. Yet visual avatar/body changes can matter to Human perception

The previous section does not imply that avatar appearance is causally irrelevant.

Virtual-body experiments show that participants can experience ownership over surrogate/virtual bodies and that transformed virtual-body properties can alter perception or behavior.

Banakou, Groten & Slater's child-body experiment found that adults embodied in a child-sized virtual body overestimated object sizes relative to comparison conditions.

Petkova & Ehrsson and related work show that first-person perspective plus correlated multisensory information can induce ownership over artificial/other bodies.

Therefore:

```text
AvatarAppearance
can affect Human perception/ownership/evaluation
without being identical to authoritative Game morphology/collision geometry.
```

Owner split:

```text
Media owns representation/signal properties.
Human owns ownership/body-perception mechanisms.
Game owns any rule/control/evaluation consequences coupled to those properties.
```

---

# 6. Collision body != vulnerability body

Many Games silently collapse:

```text
where I can physically pass
```

and:

```text
where I can be damaged / hit / detected.
```

They need not be identical.

E's probe keeps movement collision fixed while changing vulnerability width.

Result:

```text
passability remains the same
damage exposure changes.
```

Therefore:

```text
CollisionBody != VulnerabilityBody.
```

A visual avatar can differ from both.

This distinction matters for:

```text
fighting hit/hurt boxes
stealth detection volumes
vehicle collision/damage zones
boss weak points
cover systems
VR body hit regions
```

without requiring any subjective embodiment claim.

---

# 7. Sensor envelope != effector envelope

`What can I perceive?` and `What can I reach/control?` are independent constraints.

A controlled subject can have:

```text
long visual/sensor range + short action reach
short sensor range + long blind/delegated action reach
```

The probe changes sensor range while holding effector reach fixed.

Thus:

```text
SensorEnvelope != EffectorEnvelope.
```

This matters because body/tool/avatar discussions often focus only on movement geometry while information access can be the more important embodied/control constraint.

Media owns lower signal/perception mechanisms; Game owns which authoritative information/action distinctions are available under the current configuration.

---

# 8. Tool use kills `body boundary = anatomical skin`

Tool-use research provides a particularly useful pressure case.

Cardinali et al. report tool-use-dependent changes in body representation for action.

Canzoneri et al. report tool-use-related changes in both peripersonal-space and body-representation measures after reaching with a long tool.

For GDF1 the key inference is structural and intentionally weaker:

```text
A tool can extend/transform the subject's effective action envelope.
```

E's probe:

```text
bare arm reach = 0.7
tool-mediated reach = 1.7
```

with no structural requirement that the participant subjectively owns the tool as a body part.

Therefore:

```text
ToolExtension != BodyOwnership.
```

---

# 9. Tool / vehicle should not be renamed `body`

It would be tempting to say:

```text
car becomes body
sword becomes arm
cursor becomes hand
```

But this recreates the same collapse.

A tool/vehicle may mediate:

```text
reach
dynamics
inertia
sensor placement
control transfer function
collision/vulnerability
```

while remaining experientially external.

Conversely, a virtual body may be strongly owned while possessing little independent tool-like dynamics.

Therefore E retains:

# **ToolVehicleMediation**

as a structural relation, not a body-identity claim.

---

# 10. Remote control kills anatomical continuity as a requirement

Mine & Yokosawa's virtual-hand experiments provide strong negative pressure against anatomical-continuity assumptions.

They report that hand-centered/peripersonal spatial effects can shift toward a remote, disconnected controlled hand avatar.

E does not convert this Human perceptual result into a Game ontology law.

It uses the weaker conclusion:

```text
an action-centered controlled locus need not be anatomically contiguous with the biological body.
```

The executable probe places input effector and control locus far apart, with no anatomical connection, while preserving effective GameAction.

Therefore:

```text
ControlLocus != AnatomicalBodyLocation.
```

and:

```text
RemoteControl != StructuralSelfLocation.
```

---

# 11. Control locus != self-location

A player can control:

```text
remote drone
RTS squad
cursor
vehicle
remote hand
```

without the Game needing to assert:

```text
"the player is located there".
```

Self-location is a Human experiential/body-representation target unless the Game explicitly uses a subject-location semantics.

Lenggenhager et al.'s full-body illusion work shows that multisensory manipulations can shift reported self-location toward a virtual body.

That provides positive evidence that self-location is a manipulable Human target—precisely why Game should not equate it with objective control locus.

Thus:

```text
ControlLocus != SelfLocationExperience.
```

---

# 12. Ownership != agency != objective control

Kalckert & Ehrsson provide one of E's strongest empirical dissociations.

Their moving-rubber-hand experiments varied movement mode, synchrony and anatomical congruence.

Key pattern:

```text
passive movement
→ ownership can remain while agency falls;

anatomically incongruent but actively controlled hand
→ agency can remain while ownership falls.
```

So:

```text
BodyOwnership != SenseOfAgency.
```

And GDF1 already established:

```text
ObjectiveControl != SenseOfAgency.
```

Therefore the final separation is:

```text
ObjectiveControl
!= SenseOfAgency
!= BodyOwnership
!= SelfLocationExperience.
```

They can interact, but no one is evidence for the others by identity.

---

# 13. `EmbodimentExperience` was still too compressed

A-D sometimes used `EmbodimentExperience` as one Human-side target.

E now finds that this is itself too broad for precise research.

At minimum Human research may need separate claims about:

```text
BodyOwnership
SenseOfAgency
SelfLocation
BodySize/shape representation
Peripersonal/action-space representation
```

Therefore GDF1 should stop freezing or measuring a single `Embodiment score` unless a study explicitly defines what composite it means.

Strong guard:

```text
EmbodimentScore != universal experiential variable.
```

---

# 14. Does `ControlAccessProfile + GameStructure + SRVS` already suffice?

E's answer is nuanced.

## Expressively: mostly yes

R29/GDF0 can already represent:

```text
body/tool entities
morphology states
sensor/effector relations
control mappings
collision/vulnerability constraints
remote control relations
authoritative consequences
```

No new semantic primitive is required.

## Explanatorily/operationally: ControlAccessProfile alone is too narrow

It records which action distinctions are reachable/executable.

It does not by itself make salient whether a body/tool configuration changes:

```text
observation/sensing
reach/effector geometry
control dynamics/inertia
collision/passability
vulnerability/consequence
remote/tool mediation
```

So E earns one derived projection.

---

# 15. New candidate: ActionCouplingProfile

# **ActionCouplingProfile**

Definition:

> A sparse projection of the current body/tool/control relations whose intervention can change the attribution target's observation, reachable GameActions, control dynamics or authoritative consequences under one declared SkillScope.

Possible fields, only when relevant:

```text
subject/controller attribution
sensor envelope
effector envelope
control mapping
control locus
morphology/reach geometry
tool/vehicle mediation
collision geometry
vulnerability/consequence geometry
dynamic/inertial constraints
provenance/currentness
```

This is deliberately **not** called `EmbodiedAgent` or `GameBody`.

Why?

Because:

```text
Chess
→ may need almost none of the embodied fields.

VR climbing
→ may need many.

Racing
→ may need vehicle/tool dynamics but no body ownership.
```

Thus it is conditional and sparse.

---

# 16. ActionCouplingProfile is not a new ontology primitive

It is a derived view over:

```text
F1 Entity/Reference
F2 State
F3 Relation
F4 Constraint/Transition
F5 Time
F6 Authority/Provenance
F7 Observation
F8 Evaluation
F9 Action/Capability/Control
```

Its value is explanatory compression:

> When body/tool configuration changes skill/action, which structural coupling actually changed?

This keeps Game from importing Human body-schema vocabulary into core ontology.

Status:

```text
N1 candidate.
```

---

# 17. Owner boundary after E

## Game owns

Only structural/action consequences such as:

```text
ControlLocus
GameAction mapping/admission
sensor/action availability contract
morphology/reach geometry when authoritative
collision/passability
vulnerability/damage/exposure geometry
tool/vehicle mediation
dynamic/inertial action constraints
ActionCouplingProfile as a derived projection
```

## Human owns

```text
biological body mechanisms
proprioception/interoception
body schema/body representation
peripersonal-space representation mechanisms
body ownership
self-location experience
sense of agency mechanism
felt embodiment
```

## Media owns

```text
visual/audio/haptic avatar representation
body rendering
perspective/scale cues
multisensory signal presentation
```

## World owns

actual physical/material constraints when play consumes real-world body/tool properties.

Game couples to all three owner domains without absorbing them.

---

# 18. Avatar receives a much cleaner role

An `Avatar` should primarily be treated as a representation/reference role unless the current Game additionally binds it to:

```text
control locus
collision body
vulnerability body
identity/role
camera/self-location convention
```

Those are **relations**, not automatic consequences of being an avatar.

Hence:

```text
Avatar != ControlLocus
Avatar != CollisionBody
Avatar != VulnerabilityBody
Avatar != OwnedBody
Avatar != PlayerIdentity
```

Any Game may deliberately bind several together, but the model must not assume the binding universally.

---

# 19. Vehicle embodiment becomes much easier to explain

Instead of asking:

> Does the player become the car?

GDF1 can ask:

```text
Does vehicle state define the controlled locus?
Does vehicle geometry define collision/vulnerability?
Do vehicle sensors alter information access?
Do vehicle dynamics define the skill-relevant control transfer function?
Does the Human experience ownership/self-location there?
```

The first four are Game structural questions.

The last is Human evidence.

This decomposition is much more useful than arguing whether a vehicle `counts as a body`.

---

# 20. Accessibility gets the same clarification

An adapted input device can alter:

```text
InputEffector
ControlMapping
ControlAccessProfile
```

without changing:

```text
Avatar
CollisionBody
VulnerabilityBody
GameAction semantics
```

A motion-control accessibility adaptation may additionally change sensor/effector envelopes.

Therefore accessibility is not `less embodiment` or `more abstraction` by default.

It is a concrete transformation of ActionCouplingProfile dimensions.

---

# 21. E survival verdict

```text
Embodiment as single Game construct
→ REJECT.

BiologicalBody
→ Human/World source, not Game identity.

Avatar
→ RETAIN as representation role; no automatic control/body semantics.

ControlLocus
→ RETAIN strong Game-local candidate.

ControlAccessProfile
→ RETAIN derived, but insufficient alone.

ActionCouplingProfile
→ INTRODUCE as sparse derived/core-candidate projection.

CollisionBody
→ RETAIN derived structural role.

VulnerabilityBody
→ RETAIN derived structural role.

ToolVehicleMediation
→ RETAIN derived structural role.

BodyOwnership / SelfLocation / SenseOfAgency
→ HANDOFF Human experiential targets.

BodySchema / PeripersonalSpace mechanisms
→ HANDOFF Human/Media interface research.
```

---

# 22. Strongest E laws

```text
Embodiment != one variable.

BiologicalBody != InputEffector != ControlLocus.

AvatarAppearance != CollisionBody != VulnerabilityBody.

SensorEnvelope != EffectorEnvelope.

ControlLocus != SelfLocationExperience.

ObjectiveControl != SenseOfAgency != BodyOwnership.

ToolExtension != BodyOwnership.

AnatomicalContinuity != requirement for remote Game control.

StructuralBodyCoupling != ExperientialEmbodiment.

ControlAccessProfile != complete ActionCouplingProfile.
```

---

# 23. Discovery ledger after E

## N0 external pressure

```text
body-scaled morphology affects aperture affordances/action transitions;
tool use can reshape body/action-space representations;
remote disconnected controlled hands can shift peripersonal spatial representation;
ownership and agency can be experimentally dissociated;
full-body multisensory manipulations can alter self-location;
virtual-body ownership/scale can alter perception.
```

## N1 Ordivon reconstruction

```text
E-A EmbodimentSplit:
structural action coupling vs Human experiential embodiment.

E-B Avatar/Collision/Vulnerability separation.

E-C ActionCouplingProfile.

E-D ToolVehicleMediation without body-identity claim.

E-E ControlLocus/SelfLocation separation.

E-F Conditional structural body coupling:
body/tool variables enter Game only when they causally alter observation,
action reach/dynamics or authoritative consequence.
```

## N2

```text
NONE.
```

## N3

```text
NONE.
```

---

# 24. Foundation reopen audit

E looked like the most likely GDF1 round to expose a new primitive because `body` is such a deep concept.

It did not.

Every structural case can still be represented as entities, states, relations, observations, constraints, authority and action/control.

The apparent need for an Embodiment primitive disappears once:

```text
Avatar
ControlLocus
Morphology
Sensor/Effector
Collision
Vulnerability
Tool mediation
Ownership
Agency
Self-location
```

are separated by target/owner.

Therefore:

```text
R29 FoundationReopenCondition = NOT TRIGGERED
GDF0 PRC-7 = NOT TRIGGERED
```

This is strong evidence against ontology noun inflation.

---

# 25. Does E require another exploratory alphabetic round?

No new unresolved **foundation class** appeared.

The remaining questions are now mostly:

```text
which GDF1 constructs survive final compression?
which are guards vs derived views?
which belong downstream to GDF2/GDF3/GDF5/Human/Media?
what exact GDF1 reopen conditions should exist?
```

Therefore GDF1 should stop exploratory expansion here.

The next round should be:

# **GDF1-F — Final Falsification, Reconstruction & Survival Audit**

It should audit A→E and decide whether Action / Control / Skill Foundations v1 can freeze, including:

```text
DeepActionSeparation
SkillProfile
SkillScope evidence contract
EvaluationCommitmentSet
SkillRelevantVariableSet
ProbeTransformation
ControlContributionTopology
ControlAccessProfile
ActionCouplingProfile
EntryRequirementRegion
SkillExpressionEnvelope
SaturationAttribution
TechniqueFamily disposition
Human/System/Joint attribution
owner boundaries
reopen conditions
```

No further noun expansion should occur unless F finds an explicit contradiction.

---

# Primary evidence anchors emphasized in E

- Warren & Whang (1987), *Visual guidance of walking through apertures: body-scaled information for affordances*, JEP:HPP 13:371–383, DOI 10.1037//0096-1523.13.3.371.
- Cardinali et al. (2009), *Tool-use induces morphological updating of the body schema*, Current Biology 19:R478–R479, DOI 10.1016/j.cub.2009.05.009.
- Canzoneri et al. (2013), *Tool-use reshapes the boundaries of body and peripersonal space representations*, Experimental Brain Research 228:25–42, DOI 10.1007/s00221-013-3532-2.
- Mine & Yokosawa (2021), *Remote hand: Hand-centered peripersonal space transfers to a disconnected hand avatar*, Attention, Perception, & Psychophysics 83:3250–3258, DOI 10.3758/s13414-021-02320-2.
- Kalckert & Ehrsson (2012), *Moving a Rubber Hand that Feels Like Your Own: A Dissociation of Ownership and Agency*, Frontiers in Human Neuroscience 6:40, DOI 10.3389/fnhum.2012.00040.
- Lenggenhager et al. (2007), *Video ergo sum: manipulating bodily self-consciousness*, Science 317:1096–1099, DOI 10.1126/science.1143439.
- Petkova & Ehrsson (2008), *If I were you: perceptual illusion of body swapping*, PLOS ONE 3:e3832, DOI 10.1371/journal.pone.0003832.
- Banakou, Groten & Slater (2013), *Illusory ownership of a virtual child body causes overestimation of object sizes and implicit attitude changes*, PNAS 110:12846–12851, DOI 10.1073/pnas.1306779110.
