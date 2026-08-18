# Ordivon Media Deep Foundations — Round D-C: Interface / Affordance / Action-Coupling Reducibility

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817`  
**Parent:** `media-round-d-b-operative-executable-mediation-reducibility-20260818.md`  
**Fresh-continent pressure:** C-U2 — Interface / Affordance / Action-Coupling Standing  
**Status:** **direct destructive audit; no MF10 admitted**

---

# 0. Question

Round C recovered Interface / Affordance / Action-Coupling as a fresh continent because MF5 had already deeply reconstructed action-space/affordance, while Media/HCI interface standing had never received a direct whole-domain closure.

D-B then established:

```text
AffordanceStanding ≠ OperationBindingStanding
```

and left Interface independent.

D-C asks:

> **Does an Interface introduce a Media-specific primitive beyond actor-relative affordance/action possibility, representation/signification, perceptual discoverability, operation binding, input/output channels, feedback, state/mode and system boundary/composition?**

Or is Interface a high-value derived coupling standing over those existing relations?

---

# 1. Existing frozen substrate

MF5 already freezes:

```text
Physical Space ≠ Configuration Space ≠ Action Space
Connected ≠ Reachable ≠ Controllable
Possible Action ≠ Affordance ≠ Chosen Action
Affordance ≠ object-intrinsic property
Affordance ≠ geometric reachability
Action possibility is state/capability/environment relative
```

MF5-G also already states:

```text
Designed interface space can be both representational and action-spatial.
```

D-B freezes:

```text
AffordanceStanding ≠ OperationBindingStanding
DirectiveContent ≠ OperationBinding ≠ CurrentEligibility ≠ Activation ≠ Execution ≠ Effect
```

Therefore D-C must not merely restate Gibson/Norman-style affordance language.

---

# 2. Mandatory term separation

Do not collapse:

```text
System Boundary
Interface Boundary
Interface Specification
Interface Realization
Interface Token/Surface
Input Channel
Output Channel
Control Surface
Interaction Technique
Action Possibility
Affordance
Presented Action Cue / Signifier
Perceived Affordance / Perceived Action Possibility
Discoverability
Learnability
Visibility
Focusability
Operability
Enabledness
Operation Binding
Capability
Permission
Activation
Feedback
Feedforward
Mode
Context
State
Mapping
Directness
Immediacy
Reversibility
Constraint
Compatibility
Interoperability
Interaction Episode
```

Especially:

```text
Affordance ≠ Signifier
Affordance ≠ Discoverability
Discoverability ≠ Operability
Perceivable ≠ Operable
Operable ≠ Enabled for this actor/state
Enabled ≠ Authorized
Authorized ≠ Capable
Action Cue ≠ Operation Binding
Operation Binding ≠ Feedback
Interface ≠ Visual UI
Interface ≠ Representation only
Interface ≠ Operation only
Interface ≠ Interaction occurrence
Interface ≠ Boundary by identity
```

---

# 3. Working interface candidate

A provisional derived standing:

```text
InterfaceStanding(I, A, B | Σ)
```

when a scoped boundary/coupling between roles/systems `A` and `B` has grounded, repeatable mappings through which admissible distinctions, actions, state observations or control consequences can cross that boundary under some protocol/physical/practice/system organization.

This can include:

```text
input mappings
output mappings
action mappings
feedback/feedforward
state/mode conditions
capability/authority constraints
representation/perceptual cues
```

but no single modality or human consumer is mandatory.

---

# 4. Interface ≠ visual screen

Hard cases:

```text
keyboard
physical knob
haptic controller
voice interface
command line
API
hardware bus
socket/connector
screen-reader accessibility tree
robot teleoperation control
agent tool surface
```

Thus:

```text
VisualPresentation
```

is optional.

Any foundation requiring a visible GUI fails immediately.

---

# 5. Interface ≠ current interaction occurrence

An API can possess a standing interface specification and implementation while idle.

A button remains part of an interface when nobody presses it.

Therefore:

```text
InterfaceStanding
≠ ActiveInteractionEpisode
```

This mirrors MF3 standing/activation distinctions.

---

# 6. Interface type/specification ≠ realization

A published API/ABI/UI specification can define:

```text
operations
input types
state properties
error behaviors
roles
```

before a conformant implementation exists.

Conversely a de facto interface can exist operationally without a public formal specification.

Thus:

```text
InterfaceSpecification
≠ InterfaceRealization
```

B-C protocol/specification distinctions apply.

---

# 7. Realization ≠ availability to a particular actor

An interface can be implemented but inaccessible because:

```text
permission
network reachability
physical access
missing device
unsupported modality
actor capability
current mode/state
```

Therefore:

```text
InterfaceRealized
↛ ActorCanUseNow
```

---

# 8. Affordance is actor/environment relation, not interface appearance

MF5-F already freezes affordance as actor-environment/action-type/context relative.

A handle can afford pulling for one actor but not another because of:

```text
strength
size
reach
tool use
motor capability
```

The visible shape is evidence/cue, not the affordance itself.

Therefore:

```text
AffordanceStanding
≠ Appearance
```

---

# 9. Presented action cue / signifier ≠ affordance

A UI can visually suggest clicking through:

```text
button shape
underline
icon
hover treatment
label
```

while the operation is disabled/nonexistent.

Conversely an action can be possible without an obvious cue.

Therefore D-C prefers:

```text
PresentedActionCue / Signifier
```

for perceptible design evidence, keeping `Affordance` for the actual actor-environment action possibility relation.

---

# 10. WAI-ARIA disabled hard case — perceivable ≠ operable

Current WAI-ARIA explicitly defines `aria-disabled` as a state in which an element remains perceivable but is not editable/otherwise operable.

This gives a standards-level destructive case:

```text
PerceivableControl
≠ CurrentOperableControl
```

No theory that identifies interface perception with action availability survives.

---

# 11. Disabled but focusable hard case — discoverability ≠ operability

W3C Authoring Practices notes that disabled controls can intentionally remain focusable when discoverability matters, including toolbar/menu/listbox/tab cases.

Thus:

```text
Discoverable = YES
Operable = NO
```

can be a deliberate design state.

Therefore:

```text
Discoverability
≠ Enabledness/Operability
```

---

# 12. Hidden but operable hard case — operability ≠ discoverability

Keyboard shortcuts, undocumented gestures, hidden APIs or screen-reader-only controls can be operative while not visually discoverable.

Therefore:

```text
Operability = YES
VisualDiscoverability = NO
```

is ordinary.

Interface standing cannot require visible signification.

---

# 13. False action cue hard case

A decorative element can look like a button but have no operation binding.

Thus:

```text
PresentedActionCue
↛ OperationBinding
```

This is the classic false-affordance/signifier failure under precise typed terminology.

---

# 14. Hidden affordance hard case

A draggable object may be draggable despite no visible cue; a secret keyboard shortcut can invoke a command; an API may expose an operation known only through documentation.

Thus:

```text
Affordance/OperationPossibility
↛ PerceptualDiscoverability
```

Discoverability is evidence/access, not constitution.

---

# 15. WHATWG activation behavior — interface action is typed

The HTML Living Standard defines activation behavior for some elements and allows user activation through keyboard, voice, mouse and other routes that result in the element's activation behavior.

Therefore one operation/action can be reachable through multiple input modalities.

```text
InputModalityIdentity
≠ InterfaceOperationIdentity
```

---

# 16. Same visible button, different action semantics

Current HTML defines button types/commands with different behaviors such as:

```text
submit
reset
button/no default action
request-close
show-modal
custom command
```

Hence:

```text
ButtonAppearance/Role
↛ UniqueOperationSemantics
```

D-B operation binding remains required.

---

# 17. Command validity ≠ current state executability

The current HTML standard explicitly notes that command validity can be defined independently of current element state; a command event can be dispatched even when the target cannot execute that command in its current state.

Therefore:

```text
InterfaceCommandSemantics
≠ CurrentStateExecutionFeasibility
```

This is a direct bridge between InterfaceStanding and D-B ExecutionEligibilityProfile.

---

# 18. Disabled element retains role/state representation

A disabled button can still be represented to assistive technology as:

```text
role = button
state = disabled
label = ...
```

while activation is unavailable.

Thus:

```text
RepresentedControlIdentity
≠ CurrentActionAvailability
```

MF3 + MF7 separation survives.

---

# 19. Focusability ≠ actionability

An element can receive focus yet not currently execute an action.

Focus is a navigation/selection state inside an interface, not evidence of current operative binding/effect.

```text
Focused
≠ Enabled
≠ Activated
```

---

# 20. Visibility ≠ focusability

Screen-reader/keyboard navigation can expose elements differently from visual layout.

A visually hidden or off-screen control may still be programmatically represented, while a visible element may not be keyboard focusable.

Therefore interface visibility is modality/channel relative.

---

# 21. One interface can expose different action sets to different actors

Because action possibilities depend on capability/authority/context:

```text
ActionSet(UserA) ≠ ActionSet(UserB)
```

for the same UI/API realization.

Examples:

```text
admin vs viewer
mouse user vs switch-control user
robot with gripper vs camera-only agent
authenticated vs anonymous principal
```

Therefore interface action space is actor/profile relative.

---

# 22. Permission ≠ affordance in the broad physical sense

A user may physically be able to press a button but be unauthorized to invoke the bound operation.

Conversely an authorized actor may lack physical/accessibility capability to activate the control.

Thus:

```text
PhysicalActionPossibility
≠ AuthorizedActionPossibility
```

Both are useful typed profiles.

---

# 23. Capability change can alter interface affordance without UI change

MF5 already shows tool/capability changes alter affordances while environment is fixed.

In interface context:

```text
assistive technology added
hand injury
voice input enabled
robot tool attached
credential added
```

can change feasible actions without changing visual surface bytes.

Therefore:

```text
InterfaceSurfaceIdentity
≠ ActorActionSetIdentity
```

---

# 24. Interface state/mode changes action mapping

The same key/button/gesture can perform different operations in:

```text
insert vs command mode
selection vs editing mode
armed vs safe mode
modal dialog vs background
vehicle drive vs reverse
agent tool context A vs B
```

Therefore:

```text
SameInputToken
≠ SameOperationMapping
```

without declared mode/state.

---

# 25. Mode is not interface identity

An interface can persist through changing modes.

Thus:

```text
InterfaceStanding
≠ CurrentMode
```

Mode is a state variable influencing mappings/availability.

---

# 26. Mode errors are mapping/context failures, not new primitives

When an actor expects mapping `a→O1` but the system is in mode where `a→O2`, the failure is explainable through:

```text
actor model
system state
presented cues
actual operation binding
feedback
```

No hidden `InterfaceMeaning` atom is needed.

---

# 27. Feedforward ≠ feedback

An interface can provide information before action about:

```text
possible action
expected effect
current constraints
```

and after action about:

```text
activation
progress
result
error
state change
```

Therefore distinguish:

```text
Feedforward / Action Cue
Feedback / Consequence Evidence
```

They solve different uncertainty.

---

# 28. Feedback ≠ effect

A system can produce an effect without adequate feedback.

Conversely it can display feedback/error without producing intended target effect.

Thus:

```text
TargetEffect
≠ FeedbackRepresentation
```

MF1/MF3 + D-B effect trace remain separate.

---

# 29. Immediate feedback is not constitutive

Remote/asynchronous interfaces may have delayed feedback.

An interface can exist despite high latency, though usability/control quality may degrade.

Thus:

```text
InterfaceStanding
↛ ImmediateFeedback
```

MF6 handles delay.

---

# 30. Reversibility is not constitutive

Shneiderman's direct-manipulation tradition emphasizes rapid, incremental, reversible actions and visible objects/effects as a powerful interaction style.

But irreversible actions—send, fire, delete without recovery, emergency stop—still occur through interfaces.

Therefore:

```text
Reversibility
```

is a valuable interaction-quality/profile dimension, not interface constitution.

---

# 31. Direct manipulation is a subtype/profile, not Interface itself

Shneiderman's primary 1983 account emphasizes continuous representation of objects/actions, physical/direct manipulation rather than command syntax, and rapid incremental visible feedback.

These features distinguish a family of interfaces.

But command-line, voice, batch, API, switch and haptic interfaces remain interfaces without satisfying the full direct-manipulation profile.

Thus:

```text
DirectManipulation
≠ Interface universally
```

---

# 32. Directness is not one scalar primitive

An interaction can be `direct` along some dimensions and mediated along others:

```text
motor mapping
semantic distance
spatial correspondence
time delay
number of intermediate representations
control authority
```

Therefore avoid one unqualified `directness` scalar.

---

# 33. Programmatic and direct manipulation can coexist

Systems such as Sketch-n-Sketch demonstrate programmatic generation plus direct manipulation of output with synchronized program updates.

Thus:

```text
ProgrammaticInterface
```

and:

```text
DirectManipulationInterface
```

are not mutually exclusive natural kinds.

Interface compositions can support multiple action routes over the same object/state.

---

# 34. Interface ≠ input-only channel

An input-only view misses:

```text
state presentation
feedback
error signaling
progress
availability cues
```

while output-only displays may lack control.

InterfaceStanding can be unidirectional or bidirectional depending scope, but interactive interfaces often compose both directions.

---

# 35. Bidirectionality is not universal

A one-way sensor interface or status display can be an interface between systems without enabling reciprocal action.

Therefore:

```text
InterfaceStanding
↛ BidirectionalInteraction
```

Interaction is a richer case.

---

# 36. Interface ≠ communication by identity

A control surface can map action to state transitions without rich communicative intent.

A communication channel can exist without exposing controllable operations.

Therefore:

```text
Interface
≠ Communication
```

B-A remains separate.

---

# 37. Interface ≠ protocol by identity

A protocol can specify message/state semantics across an interface.

But a physical handle or haptic coupling can mediate action without a public symbolic protocol.

Conversely a protocol can exist as a specification before any interface realization.

Thus B-C remains distinct.

---

# 38. Interface ≠ operation binding by identity

D-B already provides:

```text
pressable no-op
hidden API operation
```

as opposite counterexamples.

An interface includes a broader boundary/coupling/exposure state than a single operation binding.

---

# 39. Interface ≠ affordance by identity

An environment affords many actions that are not interface-mediated.

A staircase affords climbing; a chair affords sitting.

Therefore:

```text
Affordance
```

is generic action-space ontology, not Media Interface ontology.

InterfaceStanding is one structured way of organizing/exposing/mapping action/perception across a boundary.

---

# 40. Affordance can exist outside Media

Natural terrain, body morphology and tools create affordances without any need for Media standing.

Therefore any Interface foundation defined as `affordance` would overclaim ownership.

MF5 remains the generic owner.

---

# 41. Interface can exist with little/no human-perceived affordance

Machine APIs, hardware buses and agent tool schemas can be interfaces while no human perceptual system directly encounters them.

Thus:

```text
HumanPerceivedAffordance
```

is not constitutive.

---

# 42. Machine interface does not require representation for every signal

A hardware pin/bus/control line can map electrical distinctions to state transitions without rich representation.

Thus InterfaceStanding can exist below MF3.

MF0/MF1/MF4/MF7 suffice for some machine interfaces.

---

# 43. API interface is representational/operative but not spatially perceptual

An API can define:

```text
operations
arguments
responses
errors
state constraints
```

without any necessary human spatial layout.

Thus:

```text
Interface
↛ Physical/Visual Action Space
```

although formal action/state-space structure remains.

---

# 44. Agent tool surface hard case

An artificial agent can receive a set of declared tools/capabilities.

The interface may include:

```text
tool names
schemas
descriptions
constraints
result channels
errors
```

Yet the agent's actual usable action set also depends on runtime capability, permission, state and policy.

Therefore:

```text
PresentedToolSet
≠ EffectiveActionSet
```

This is the Agent-era version of perceivable-but-disabled UI.

---

# 45. Agent can have hidden effective capabilities

A runtime may possess operations not surfaced to the current model/agent.

Thus:

```text
RuntimeCapabilitySet
≠ ExposedInterfaceCapabilitySet
```

Interface is a selective boundary, not the total capability of either side.

---

# 46. Interface performs selection/compression over capability

A system may support hundreds of internal operations while exposing a few high-level actions.

Thus interface design can:

```text
hide
aggregate
compose
rename
constrain
parameterize
```

underlying capabilities.

MF4 composition + D-B operation mapping handle this.

---

# 47. High-level interface action can compile to many low-level operations

`Save`, `Send`, `Deploy`, or an agent tool may fan out into many execution steps.

Therefore:

```text
InterfaceActionIdentity
≠ LowLevelExecutionTraceIdentity
```

D-B ActivationExecutionTrace remains needed.

---

# 48. Many interface actions can realize one underlying operation

Mouse click, keyboard shortcut, voice command and API invocation may all map to the same semantic operation.

Thus interface realization/mapping and operation identity are orthogonal.

---

# 49. Haptic interface hard case — visuality not required

Teleoperation research demonstrates interfaces combining visual, auditory and haptic channels; haptic feedback can materially change manipulation performance.

This is sufficient to reject any visual-only Interface ontology.

The relevant standing is cross-modal input/output coupling, not screen geometry.

---

# 50. Tactile/conversational accessibility hard case

Interactive tactile models for blind users combine touch, haptic feedback and conversational interaction.

This demonstrates that:

```text
interface action/perception coupling
```

can be distributed across modalities and consumer capabilities.

Visual discoverability is only one specialization.

---

# 51. Sensory substitution does not collapse interface modality

MF5-E already shows tactile input can carry camera-derived spatial structure while phenomenal modality remains an additional question.

Thus an interface can preserve task/action information across modality transformation without preserving sensory phenomenology.

B-M transformation profiles apply.

---

# 52. Voice interface hard case

Voice can expose an interface through linguistic utterance rather than persistent visible controls.

Action possibilities may be:

```text
known from convention/help
inferred
suggested by prompts
undiscoverable
```

Thus persistent visible surface is not required.

---

# 53. Conversational interface has open-ended surface but bounded capability

A language model may accept arbitrary natural-language strings while only a subset map to available actions.

Therefore:

```text
InputExpressionSpace
≠ EffectiveOperationSpace
```

This is a critical Agent/HCI distinction.

---

# 54. Natural language flexibility does not create infinite affordance

The fact that a user can ask anything does not mean the system can do anything.

Thus:

```text
LinguisticRequestPossibility
≠ ActionCapability
```

D-B capability separation remains central.

---

# 55. Interface feedback can be implicit

A physical control can provide:

```text
resistance
movement
sound
state change
```

without an explicit message saying `success`.

Therefore FeedbackStanding need not be representational/linguistic.

MF1/MF2/MF7 can support nonrepresentational feedback.

---

# 56. Interface feedback can be false/stale

A UI can show success while backend action failed, or show old state while target changed.

Therefore:

```text
FeedbackRepresentation
≠ TargetStateTruth
```

MF3 truth/provenance + MF7 state observation are required.

---

# 57. Latent interface state matters

Two identical-looking controls can differ because of:

```text
focus
mode
permissions
connection
selection
armed state
hidden target
session context
```

Thus visible state is not complete interface state.

---

# 58. Interface state can be partly distributed

Action availability can depend jointly on:

```text
client UI state
server state
principal authority
network reachability
tool/runtime state
external world state
```

No single screen-local state is sufficient.

InterfaceStanding can therefore be cross-system relational.

---

# 59. Interface boundary is not necessarily physical boundary

A software interface may exist inside one process.

A physical control interface may bridge human/device.

A protocol interface may bridge organizations.

Thus:

```text
InterfaceBoundary
≠ PhysicalSurfaceBoundary universally
```

MF4 boundary/composition owns the generic boundary standing.

---

# 60. Physical boundary alone is not interface

A wall between two systems is a boundary but not automatically an interface.

Need grounded exchange/mapping/coupling across the boundary.

Thus:

```text
Boundary
↛ Interface
```

This mirrors D-A anti-mere-causation discipline.

---

# 61. Coupling alone can still be too broad

Two mechanically touching objects are coupled.

If every causal coupling became Interface, the concept collapses into generic physics.

Therefore InterfaceStanding needs an organized/typed boundary relation in which distinctions/actions/states are admissibly exchanged or mapped under a system/practice/design role.

---

# 62. Interface can be intentionally designed but design is not necessary universally

A de facto interface can emerge through stable operational coupling/use without a formal designer.

Examples:

```text
adapted tool use
de facto protocol
repurposed control surface
```

Thus:

```text
Designed
```

is one grounding route, not universal constitution.

---

# 63. Interface can be asymmetric

One side may send commands while receiving only coarse status.

An API/provider controls semantics more than client.

A human can manipulate a device that cannot reciprocally model the human.

Therefore:

```text
Interface(A,B)
```

need not be symmetric in capabilities/information/control.

---

# 64. Interface can be many-to-many

Shared dashboards, public APIs, multi-touch surfaces and multi-agent tool environments can connect many bearers.

Therefore two-endpoint point-to-point interface is not universal.

MF4 composition handles multiplicity.

---

# 65. Interface can be nested/layered

Example:

```text
user
→ GUI
→ application API
→ service API
→ runtime/device interface
→ physical actuator
```

Each layer can have its own mappings/errors/feedback.

Thus:

```text
OneTaskInteraction
≠ OneInterfaceLayer
```

---

# 66. Interface failure can occur at different layers

A visible button can work locally while server API fails; API can work while actuator is unavailable.

Therefore interface failure attribution requires layer/path identity.

D-B execution trace + Network/Runtime evidence remain necessary.

---

# 67. Interface ≠ interoperability

Two systems can each expose interfaces yet fail to interoperate because schemas/capabilities/semantics mismatch.

Conversely an adapter can create interoperability across unlike interfaces.

B-C remains generic owner of interoperability.

---

# 68. Interface evolution/versioning is real

Mappings can change across versions while surface names remain stable.

Thus:

```text
InterfaceNameIdentity
≠ InterfaceSemanticIdentity
```

Version/context must be preserved.

---

# 69. Backward compatibility is not interface identity

A new interface version may remain compatible while adding/removing/deprecating operations.

Thus continuity/compatibility are profile relations, not strict identity.

MF7/B-C handle them.

---

# 70. Deprecated control can remain represented but no longer recommended

A control/API operation can still exist while marked deprecated.

Therefore:

```text
Exists
≠ Recommended
≠ FutureSupported
```

Evaluation/status must be typed.

---

# 71. Error messaging is interface output, not operation effect

An error response communicates why an action was not completed.

Thus:

```text
ErrorFeedback
```

can be successful interface behavior while target operation failed.

This is a useful anti-collapse case.

---

# 72. Interface quality ≠ interface existence

A confusing, inaccessible, slow or dangerous interface is still an interface.

Therefore:

```text
Usability
Accessibility
Discoverability
Safety
Efficiency
Satisfaction
```

are evaluation/profile dimensions, not constitutive existence.

---

# 73. Directness ≠ quality universally

Direct manipulation can be excellent for some tasks, while command/programmatic interfaces outperform it for abstraction, automation, repeatability or scale.

Thus directness should not become a universal goodness criterion.

---

# 74. Accessibility ≠ one modality translation problem only

Accessibility can change the action route itself:

```text
keyboard instead of pointer
voice instead of touch
screen reader semantics instead of visual layout
switch control instead of direct manipulation
```

Thus accessibility concerns actor capability × interface mapping, not only B-M content remediation.

---

# 75. Interface can create/remap action space

A remote-control interface can make distant device actions available; a GUI can expose operations not physically manipulable at the target surface; an API can compose complex operations.

Therefore interface can alter an actor's **effective action possibility structure** without altering physical geometry.

MF5 already supports capability/tool-expanded action space.

---

# 76. Interface does not own generic action-space ontology

The fact that interface changes effective action possibilities does not move ActionSpace from MF5 into Media.

Media Interface is one mechanism that changes/exposes action capability.

Ownership remains:

```text
MF5 generic action possibility
D-C interface mapping/exposure profile
D-B operation binding
```

---

# 77. Interface can constrain action as much as enable it

Menus, forms, schemas and physical gates can restrict available actions.

Thus:

```text
Interface
≠ CapabilityExpansion only
```

It can:

```text
expose
hide
aggregate
forbid
sequence
parameterize
```

operations.

---

# 78. Constraint can be representational or mechanical

A form can prevent invalid input through software validation; a keyed connector can physically prevent incorrect insertion.

Both are interface constraints, but only some are directive representations.

MF3 remains optional.

---

# 79. Constraint ≠ authority

A UI may disable an operation because of usability state, not permission.

A user may be authorized but temporarily blocked by validation/preconditions.

Thus:

```text
Disabled
≠ Unauthorized
```

This is a critical engineering distinction.

---

# 80. Presented capability ≠ effective capability

A UI/API can advertise an action that fails at runtime.

Conversely hidden runtime capability may not be exposed.

Therefore interface descriptions must distinguish:

```text
PresentedActionSet
EffectiveAvailableActionSet
UnderlyingCapabilitySet
```

---

# 81. Effective action set is time/state relative

Because capability, mode, resources and permissions vary:

```text
EffectiveActionSet(t1) ≠ EffectiveActionSet(t2)
```

while interface identity persists.

MF6/MF7 state/time apply.

---

# 82. Interface can have uncertain action mapping

Probabilistic gesture recognizers, language interfaces or learned controllers may map input to operations stochastically/uncertainly.

Therefore deterministic mapping is not required.

A profile should preserve confidence/error distribution where relevant.

---

# 83. Ambiguous input does not erase interface standing

Voice/gesture input can be ambiguous; system disambiguation/confirmation can be part of interface dynamics.

Thus exact one-to-one mapping is not constitutive.

---

# 84. Confirmation is a separate interaction stage

An interface may require:

```text
input
interpretation
preview
confirmation
commit
```

before operation admission.

Therefore user intention/gesture and committed operation are distinct events.

---

# 85. Undo is a new operation, not metaphysical reversal

An undo interface typically issues a compensating/restorative transition under recorded history.

It need not literally erase historical occurrence.

Thus:

```text
UndoAvailability
≠ PastActionNeverOccurred
```

MF7 history/continuation applies.

---

# 86. Interface can mediate epistemic action

External representations can be manipulated to aid reasoning (MF3 RI-28).

An interface can expose actions whose purpose is to transform representation for cognition rather than external world effect.

Therefore:

```text
InterfaceAction
↛ ExternalWorldAction
```

---

# 87. Interface can mediate purely representational transformations

Zoom, sort, filter, pan, highlight may change only representation/view state.

They are still legitimate interface actions.

D-B target scope handles internal/representation-state transitions.

---

# 88. Interface can mediate institutional actions

`Approve`, `sign`, `publish`, `grant access` can alter institutional standings, not merely physical state.

Institution/Host owns authority/status consequences; interface merely supplies a route.

---

# 89. Interface can mediate social actions

`Follow`, `like`, `block`, `message` can alter relational/social states.

Human/Institution owns social standing; Media owns representation/action route specialization.

No new social primitive is imported.

---

# 90. Interface can mediate financial actions

`buy`, `bid`, `transfer` controls may create financial/contractual effects.

Finance/Institution owns value/claim standing.

Interface routing does not transfer domain ownership.

---

# 91. Interface is a cross-owner boundary object in modeling terms

Because one interface can simultaneously expose:

```text
representational state
runtime capabilities
network operations
institutional permissions
financial actions
physical controls
```

its ontology is necessarily compositional/cross-owner.

That increases practical importance but decreases plausibility as a single primitive.

---

# 92. Proposed `InterfaceStandingProfile`

```text
InterfaceStandingProfile(I | Σ) = <
  Boundary/Participants,
  Interface Specification?,
  Interface Realization,
  Input Channels,
  Output/Feedback Channels,
  Presented/Represented Action Set?,
  Effective Action Set,
  Operation Bindings,
  Actor Capability Assumptions,
  Authority/Permission Assumptions?,
  Current Mode/State,
  Mapping Rules / Uncertainty,
  Feedforward/Action Cues?,
  Discoverability Profile?,
  Feedback Profile?,
  Constraints/Guards,
  Temporal/Latency Profile,
  Layer/Dependency Relations,
  Provenance/Version,
  Evidence,
  Uncertainty,
  Scope
>
```

This is the central derived reconstruction.

---

# 93. Proposed `ActionExposureProfile`

```text
ActionExposureProfile(I, Actor | t, Σ) = <
  Underlying Capability Set,
  Interface-Exposed Action Set,
  Presented/Signified Action Set,
  Discoverable Action Set,
  Perceived/Inferred Action Set?,
  Current Enabled Action Set,
  Authorized Action Set?,
  Effectively Executable Action Set,
  Actor Physical/Sensory/Cognitive Capability,
  Mode/State,
  Known Mismatches,
  Evidence,
  Uncertainty
>
```

This directly prevents the common collapse:

```text
what UI shows = what actor can do
```

---

# 94. Proposed `InterfaceMappingProfile`

```text
InterfaceMappingProfile(M | Σ) = <
  Input Event/Pattern,
  Context/Mode,
  Interpretation/Recognition?,
  Bound Operation/Transition,
  Parameters,
  Preconditions,
  Confirmation/Commit Stage?,
  Feedback Route,
  Error/Recovery Route,
  Stochasticity/Ambiguity?,
  Version,
  Evidence
>
```

---

# 95. Proposed `InterfaceFeedbackProfile`

```text
InterfaceFeedbackProfile(F | Σ) = <
  Trigger/Operation Stage,
  Feedback Modality,
  Represented/Indicated State,
  Source of Evidence,
  Latency,
  Fidelity/Truth Relation,
  Progress vs Completion vs Error,
  Actor Accessibility,
  Persistence,
  Uncertainty
>
```

This preserves:

```text
Feedback ≠ TargetEffect
```

---

# 96. Proposed `InterfaceAffordanceProfile`

Rather than redefine generic affordance:

```text
InterfaceAffordanceProfile(I, Actor, ActionType | Σ) = <
  Generic MF5 AffordanceClaim,
  Interface Surface/Channel,
  Relevant Actor Capability,
  Operation Binding?,
  Current Mode/State,
  Current Enabledness,
  Presented Action Cue?,
  Discoverability?,
  Required Authority?,
  Feedback/Confirmation?,
  Evidence,
  Uncertainty
>
```

The first field remains MF5-owned.

---

# 97. Strongest irreducibility test

Construct A/B identical in:

```text
participants/boundary
all actor capabilities
all generic affordances/action possibilities
all input/output channels
all representation/signifier states
all discoverability/perception states
all operation bindings
all current mode/state
all capability/permission constraints
all mappings/preconditions
all feedback/feedforward
all latency
all protocol/specification/version
all runtime/network realization
all history/provenance
scope
```

and claim:

```text
InterfaceStanding(A) ≠ InterfaceStanding(B)
```

No grounded difference remains.

Any proposed difference alters boundary/composition, mapping, channel, action possibility, representation, state, operation binding, feedback, capability or authority already modeled.

No independent `InterfaceAtom` survives.

---

# 98. Strongest affordance-vs-interface test

World A and B have identical actual actor-environment affordances.

A exposes the action with a visible/focusable/signified control.
B hides the action behind an undocumented shortcut/API.

Then:

```text
GenericAffordanceStanding(A) = GenericAffordanceStanding(B)
```

but:

```text
Discoverability/ActionExposureProfile(A) ≠ B
```

This proves interface exposure is a real derived relation not reducible to affordance alone.

But it is fully representable through MF2/MF3 + mapping/profile relations.

---

# 99. Strongest cue-vs-operability test

A and B show identical button representation.

A is enabled/bound.
B is disabled/no-op.

Then:

```text
PresentedActionCue(A) = PresentedActionCue(B)
```

but:

```text
CurrentEnabledActionSet(A) ≠ B
```

WAI-ARIA/HTML provide standards-level realizations of this distinction.

No new primitive required.

---

# 100. Strongest machine-interface test

Hold machine capabilities/operations fixed.

World A exposes them via a tool/API interface schema to an agent.
World B does not expose them to that agent.

Then:

```text
UnderlyingCapabilitySet(A)=B
```

but:

```text
InterfaceExposedActionSet(A) ≠ B
```

The difference is selective boundary/exposure standing, reducible to MF4 + MF3/B-C + D-B.

---

# 101. Cheapest falsifier matrix

| Proposed universal claim | Cheap counterexample | Result |
| --- | --- | --- |
| Interface = visual UI | API/haptic/voice/CLI | falsified |
| Interface requires active interaction | idle API/button | falsified |
| Specification = realization | spec without implementation / de facto interface | falsified |
| Realization = actor availability | inaccessible/unauthorized interface | falsified |
| Affordance = appearance | capability-relative handle | falsified |
| Signifier = affordance | fake clickable decoration | falsified |
| Perceivable = operable | aria-disabled | falsified |
| Discoverable = operable | focusable disabled menu item | falsified |
| Operable = visually discoverable | hidden shortcut/API | falsified |
| Focusable = actionable | disabled focusable control | falsified |
| Visible = focusable | visible nonfocusable / screen-reader route | falsified |
| Same surface = same actor action set | different capability/credential | falsified |
| Permission = physical affordance | pressable unauthorized control | falsified |
| Same input token = same operation | mode-dependent mapping | falsified |
| Feedforward = feedback | pre-action cue vs post-action evidence | falsified |
| Feedback = target effect | false/stale success indicator | falsified |
| Immediate feedback required | asynchronous/remote interface | falsified |
| Reversibility required | irreversible send/emergency action | falsified |
| Direct manipulation = interface | command/API/voice | falsified |
| One scalar directness | semantically direct but temporally remote case | falsified |
| Interface = communication | noncommunicative control surface | falsified |
| Interface = protocol | physical handle / protocol spec without realization | falsified |
| Interface = operation binding | pressable no-op / hidden API | falsified |
| Interface = affordance | staircase affordance / machine API | falsified |
| Human-perceived affordance required | machine API/bus | falsified |
| Representation required for interface | hardware control line | falsified |
| Spatial visual layout required | API/voice | falsified |
| Bidirectionality required | sensor/status one-way interface | falsified |
| Boundary alone = interface | wall/separation | falsified |
| Any coupling = interface | accidental mechanical contact | falsified |
| Formal design required | de facto stable coupling/interface | falsified |
| Symmetric interface required | command/status asymmetry | falsified |
| Two endpoints required | shared/multi-agent interface | falsified |
| One task = one interface layer | GUI→API→device stack | falsified |
| Interface = interoperability | incompatible interfaces | falsified |
| Interface name = semantic identity | version change | falsified |
| Interface quality = existence | bad/confusing interface | falsified |
| Directness = universal quality | automation/programmatic strengths | falsified |
| Accessibility = content transformation only | alternate action route | falsified |
| Interface only enables, never constrains | forms/guards/menus | falsified |
| Disabled = unauthorized | invalid state/validation block | falsified |
| Presented capability = effective capability | stale/blocked control | falsified |
| Deterministic mapping required | speech/gesture recognizer | falsified |
| One gesture = one committed action | confirmation workflow | falsified |
| Undo erases history | compensating transition | falsified |
| Interface action implies world action | zoom/filter/model manipulation | falsified |
| Presented tool set = runtime capability set | hidden/unavailable tools | falsified |

No foundation-level survivor remains.

---

# 102. Reduction

```text
System/boundary/composition           → MF4
Generic affordance/action possibility → MF5
Perceptual/action cue/discoverability → MF2 + MF3
Interface geometry/hit regions        → MF5 + MF3/MF4
Temporal delay/sequence               → MF6
State/mode/action mapping             → MF7
Operation binding/execution chain     → D-B + MF7
Representation/labels/state semantics → MF3
Interaction episodes                  → MF4 + MF7 + MF8 where agential
Actor action/choice                    → MF8 where genuine
Protocol/interface spec               → B-C + MF3
Remote realization                    → Network
Execution/capability                   → Runtime/Harness
Authority/permission                  → Institution/Host/Security
Accessibility capability              → Human + MF2/MF5 + interface profiles
Domain effects                         → respective owner (Finance/Human/etc.)
```

Interface remains a derived cross-owner boundary/action-coupling reality.

---

# 103. Classification

Canonical D-C result:

```text
Interface / Affordance / Action-Coupling
= SPLIT / REDUCIBLE / CROSS-CUTTING / BOUNDARY-ACTION-EXPOSURE REALITY
= NOT genuinely-new-foundation
```

More precisely:

```text
Generic Affordance
→ MF5

Presented/Perceived Action Cue
→ MF2 + MF3

Discoverability
→ MF2 + representation/navigation evidence

Operation Binding
→ D-B + MF7

Interface Standing
→ MF4 boundary/composition
 + input/output mappings
 + selective action exposure
 + D-B operation bindings
 + MF7 state/mode/feedback

Visual/Haptic/Voice/API/Agent Interface
→ modality/implementation profiles
```

No MF10 is admitted.

---

# 104. FoundationReopen audit

No MF0–MF9 FoundationReopenCondition is triggered.

D-C strongly validates:

```text
MF5 PossibleAction ≠ Affordance ≠ Chosen/ExecutedAction
MF5 actor/capability-relative affordance
MF5 designed interface can be representational + action-spatial
MF3 representation is distinct from control/operation
MF4 boundary/composition is typed rather than one physical surface
MF7 state/mode/control mappings are dynamic
D-B AffordanceStanding ≠ OperationBindingStanding
```

No visual, haptic, accessibility, API or Agent hard case defeats them.

---

# 105. Main methodological result — action exposure is not action possibility

D-C's strongest new rule is:

```text
ActionPossibility
≠ ActionExposure
```

An action can be possible but hidden.
An action can be prominently exposed but disabled/unavailable.

Therefore UI/tool/interface models must represent both:

```text
what can actually be done
```

and:

```text
what the interface communicates/exposes as doable
```

plus their mismatch.

This is a high-value practical concept even though not a new primitive.

---

# 106. Second methodological result — interface is selective boundary governance, not total capability

An interface rarely exposes everything either side can do.

It selects and structures a subset of possible exchanges/actions.

Thus:

```text
UnderlyingCapabilitySet
≠ InterfaceExposedSet
≠ Presented/DiscoverableSet
≠ CurrentlyEnabledSet
```

This matters strongly for agent tool surfaces, APIs and safety boundaries.

---

# 107. Third methodological result — modality is orthogonal to interface ontology

Visual, auditory, tactile, linguistic and machine-only interfaces can realize the same broad interface standing.

Therefore modality-specific UI taxonomies belong to practical profiles, not foundation ontology.

---

# 108. Relationship to Telepresence / Teleaction

D-C closes generic interface/action-exposure standing but not mediated presence.

A teleoperation interface can expose remote actions and feedback while differing radically in:

```text
sensorimotor coupling
latency
remote spatial alignment
body/tool incorporation
sense of presence
social copresence
```

Thus C-U3 remains independently open.

---

# 109. Relationship to Machine-Operational / Invisual Media

After D-B and D-C, most independent foundation pressure from C-U5 is consumed:

```text
machine-only perception      → MF1/MF2
machine interface            → D-C
operation binding/control    → D-B/MF7
representation               → MF3 optional
```

Remaining operational-image issues are primarily political/institutional/epistemic specializations rather than missing Media primitives at this frontier.

---

# 110. Information-gain update

D-C is a **high-information closure** because it resolves the fresh Interface continent without duplicating MF5.

Major additions:

1. `ActionPossibility ≠ ActionExposure`.
2. `PresentedActionSet ≠ DiscoverableSet ≠ EnabledSet ≠ AuthorizedSet ≠ EffectivelyExecutableSet`.
3. Interface is a derived selective boundary/mapping standing, not a visual surface or affordance primitive.
4. Agent tool surfaces are interfaces over capabilities, not identical to capability truth.
5. Feedback, feedforward, action cue and effect remain typed stages.

After D-C, the clearest remaining medium-high fresh-continent pressure is:

```text
Mediated Presence / Telepresence / Teleaction / Distributed Embodiment
```

while Datafication/Legibility remains moderate and Machine-Operational/Invisual Media no longer appears independently foundation-heavy.

This is diagnostic, not a canonical roadmap declaration.

---

# 111. Research anchors

Representative primary/authoritative pressure sources:

- W3C, WAI-ARIA 1.3 (2026 working specification) — `aria-disabled` explicitly separates perceivability from operability and exposes interface roles/states/properties to assistive technologies.
- W3C, ARIA Authoring Practices Guide — disabled controls can intentionally remain focusable to preserve discoverability, directly separating discoverability from operability.
- WHATWG HTML Living Standard (2026) — activation behavior, disabled controls, command semantics and state-dependent command execution provide formal interface/action hard cases.
- Ben Shneiderman, `Direct Manipulation: A Step Beyond Programming Languages` (IEEE Computer, 1983; author-hosted publication metadata) — visibility of objects/actions, rapid incremental reversible action and visible feedback characterize a powerful interaction profile rather than interface ontology as a whole.
- Chugh et al., `Programmatic and Direct Manipulation, Together at Last` (2015) — demonstrates composition of programmatic and direct-manipulation routes over one artifact/state.
- Triantafyllidis et al., `Multimodal Interfaces for Effective Teleoperation` (2020) — visual/auditory/haptic combinations used as cross-modal interface hard cases.
- Reinders et al., `Designing Conversational Multimodal 3D Printed Models with People who are Blind` (2023) — tactile/haptic/conversational interaction used to falsify visual-interface assumptions.
- Frozen Ordivon MF2/MF3/MF4/MF5/MF6/MF7/MF8 plus B-C/B-M/D-B.

These sources are hard cases and empirical/specification evidence, not ontology authorities.

---

# 112. Round D-C closeout

```text
Round D-C target       = Interface / Affordance / Action-Coupling
Result                 = SPLIT / REDUCIBLE / CROSS-CUTTING / BOUNDARY-ACTION-EXPOSURE REALITY
New Media primitive    = NONE
MF10                    = UNKNOWN / NOT ADMITTED
FoundationReopen       = NONE
WholeMediaClosure      = NOT ESTABLISHED
```

Deep result:

> **Interface is real, but it is not a visible surface, not generic affordance, and not operation binding. MF5 already owns actor-relative action possibilities; D-B owns operation binding/execution; MF2/MF3 can represent action cues, labels and discoverability; MF7 owns state/mode/feedback; MF4 owns boundary/composition. The interface-specific derived standing is the selective organization and exposure of mappings across a boundary: which inputs/outputs/actions are exposed, signified, discoverable, enabled, authorized and effectively executable for a particular actor/system under current state. Standards-level disabled-control cases prove `perceivable ≠ operable` and `discoverable ≠ enabled`; hidden APIs and shortcuts prove `operable ≠ discoverable`. Hence the central new rule is `ActionPossibility ≠ ActionExposure`, with a fuller chain `UnderlyingCapabilitySet ≠ InterfaceExposedSet ≠ Presented/DiscoverableSet ≠ CurrentEnabledSet ≠ AuthorizedSet ≠ EffectivelyExecutableSet`. Visual, voice, haptic, API and agent-tool interfaces instantiate different modality profiles of the same derived boundary/action-exposure reality. No Interface or Affordance primitive survives.**

Fresh-continent research remains open.
