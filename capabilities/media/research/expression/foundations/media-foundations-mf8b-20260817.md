# Ordivon Media Foundations — MF8-B Action, Behavior & Action Ownership

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 48 at start  
**Input:** MF0–MF7 frozen; MF8-A complete/provisional.  
**Status:** **MF8-B COMPLETE / PROVISIONAL ACTION ONTOLOGY. MF8 Agency Foundations are not frozen yet.**  
**Next:** MF8-C — Goal, Need, Want, Preference, Utility & Value.

---

# 0. Purpose

MF8-A left a deliberate circularity risk:

```text
AgencyStanding candidate
  includes ActionOwnershipStanding

but

ActionStanding
  might be defined as `what an agent does`
```

That would make:

```text
Agency → Action → Agency
```

foundationally useless.

MF8-B therefore reconstructs **token-level action** without presupposing a previously certified Agent bearer. Agency can then be reconstructed dispositionally as a persistent organization capable of generating/owning such action tokens under evaluative orientation.

The central questions are:

1. What separates behavior from action?
2. What separates action source, authorship, ownership, execution and responsibility?
3. Can a failed attempt remain an action?
4. Can omission be action despite no overt movement?
5. What happens under reflex, habit, coercion, remote control and delegation?
6. Can action exist without conscious intention, deliberation or metaphysical alternative possibilities?
7. How do action tokens compose across scales, tools and collectives?

---

# 1. Frozen substrate consumed, not reopened

MF8-B preserves MF7:

```text
StateTransition ≠ Action
Dynamics ≠ Action
Cause ≠ Control
Control ≠ Agency
Command ≠ Actuation ≠ TargetEffect
Authority ≠ Capability ≠ Action ≠ Effect
Continuation ≠ Identity
```

MF8-A additionally established:

```text
AgentRoleStanding ≠ AgencyStanding
Behavior ≠ Action
ControlOccurrence ≠ Action
ActionAttempt ≠ Effect
Cause ≠ ActionOwnership
AgencyStanding ≠ Sense/JudgementOfAgency
```

### B8-001
**No MF0–MF7 FoundationReopenCondition is triggered at MF8-B entry.**

---

# 2. `Action` is itself an overloaded term

The word appears in incompatible roles:

```text
physics:        action functional
neuroscience:   motor action / action potential
control:        control action
RL/MDP:         member of an action space
software:       command / operation / API action
law:            legal act
language:       speech act
ethology:       action pattern
philosophy:     agential / intentional action
ordinary use:   something someone did
```

MF8-B therefore introduces:

```text
ActionRoleStanding(X, R | Σ)
```

A candidate X has ActionRoleStanding when a formal, disciplinary, computational, institutional or operational schema constitutes/recruits X as an `action` alternative, command, operation or act under role R.

### B8-002
**ActionRoleStanding ≠ AgentialActionStanding.**

An RL `action`, API `action`, motor-control `action` or legal `act` may be perfectly legitimate inside its standing route without proving that the target bearer is an autonomous agent.

### B8-003
Bare vocabulary such as `action = 3` or `agent took action` is under-specified until its standing route is declared.

---

# 3. BehaviorStanding

`Behavior` also must remain agency-neutral.

Provisional primitive:

```text
BehaviorStanding(E, B | Σ)
```

An occurrence/process E has BehaviorStanding for bearer/system B when it is non-arbitrarily attributed, constituted or modeled as a temporally/event-wise organized activity, response, output pattern or mode of B at a declared behavioral scale and boundary.

BehaviorStanding can be:

```text
physical/material
biological
motor
computational
organizational
formal/simulated
observational/ethological
hybrid
```

and does **not** require:

- agency;
- goal;
- intention;
- consciousness;
- choice;
- evaluative ownership.

Examples include:

- a reflex;
- a material stress-response curve under engineering `behavior` vocabulary;
- a network protocol's retry behavior;
- a bacterium's movement pattern;
- an application's failure behavior;
- an involuntary movement.

### B8-004
**BehaviorStanding is bearer/activity standing, not action authorship.**

### B8-005
`Behavior ≠ mere state transition`: transitions can occur without being organized/recruited as bearer behavior at the declared scale.

### B8-006
`Action` is not universally a subset of overt Behavior because internal actions and omissions may have ActionStanding without a corresponding externally visible movement.

---

# 4. Resolve the Agency↔Action circularity

MF8-B changes the dependency direction.

Do **not** define:

```text
Action = event caused by an already-established Agent
```

Instead define token-level action relations first, then define Agency as a persistent bearer-level capacity/profile over such relations.

The dependency becomes:

```text
Bearer organization
    ↓
ActionSourceStanding
+ ActionGuidanceStanding
+ ActionEngagement/Attempt
+ Typed ActionAttributionStanding
    ↓
AgentialActionStanding(token)
    ↓ repeated/capacity-level organization
AgencyStanding(bearer)
```

### B8-007
**ActionStanding does not presuppose globally certified AgencyStanding.**

### B8-008
Agency becomes primarily a bearer/dispositional organization; action is primarily token/episode standing.

---

# 5. ActionSourceStanding

Provisional primitive:

```text
ActionSourceStanding(S, A, B | Σ)
```

holds when an organized process/source S attributable to bearer B non-trivially governs the initiation, selection, shaping, maintenance, suppression or termination of candidate action episode A, such that B is more than a passive transmission path, externally displaced object or bare effector.

Important qualifications:

1. `source` does **not** mean metaphysical first cause;
2. an action can be stimulus-triggered;
3. an action can be commanded/delegated;
4. deterministic organization is allowed;
5. environmental constraints may be strong;
6. source standing may be distributed across subsystems;
7. source standing is scale-relative.

### B8-009
**External causation does not negate ActionSourceStanding.** Almost every real action is environmentally conditioned.

### B8-010
**Passive causal transmission does not establish ActionSourceStanding.**

### B8-011
Intervention/counterfactual sensitivity of the bearer's organized source is important evidence for source standing but not a metaphysical constitutive requirement that must always be experimentally accessible.

---

# 6. ActionGuidanceStanding

Source alone is too weak: an internally generated spasm can have an endogenous neural source while lacking ordinary action standing.

MF8-B therefore introduces:

```text
ActionGuidanceStanding(G, A, B | Σ)
```

when an organization G attributable to, accepted by, delegated through or constitutively governing B gives the candidate episode A **action relevance**—for example through a policy, norm, learned disposition, value, goal, need, rule, commitment, instruction, task role or other evaluative/action-selection structure.

This does not settle MF8-C's value ontology. It only requires that action production is organized as doing/withholding/maintaining something under a typed action-guiding relation rather than being generic internal causation.

Guidance provenance must remain explicit:

```text
intrinsic / viability-grounded
learned / sedimented
explicit goal-directed
designed
externally instructed
delegated
institutional
habitual / skill-based
represented / observer-attributed
```

### B8-012
**Current explicit goal representation is not constitutive to all action.**

### B8-013
**Guidance provenance ≠ ownership provenance.** An external command can guide an action that is still locally authored; a direct actuator signal can bypass local authorship entirely.

---

# 7. Action engagement, attempt, execution and effect

One of the most important reconstructions is a staged action stack:

```text
Candidate / Action Possibility
        ↓
ActionEngagementStanding
        ↓
ActionAttemptStanding
        ↓ optional realization route
Execution / Actuation Standing
        ↓ optional consequence
Target Effect
        ↓ criterion-relative evaluation
Success / Failure
```

## 7.1 ActionEngagementStanding

```text
ActionEngagementStanding(B, A | Σ)
```

means B's action-producing organization actually recruits, activates, maintains, suppresses or commits the relevant action channel toward A.

This is more general than a discrete `release` event because many actions are continuous.

## 7.2 ActionAttemptStanding

```text
ActionAttemptStanding(A, B | Σ)
 = ActionSourceStanding
 + ActionGuidanceStanding
 + ActionEngagementStanding
 + Temporal/Action Scope
```

An attempt does not require successful motor execution or external effect.

### B8-014
A paralyzed subject can attempt to move despite absent limb movement.

### B8-015
A command rejected by an actuator can still be part of an upstream action attempt.

### B8-016
**Attempt ≠ Execution ≠ Effect ≠ Success.**

This directly consumes MF7's command/actuation/effect firewall.

---

# 8. AgentialActionStanding — provisional token core

MF8-B's core candidate is:

```text
AgentialActionStanding(A, B | Σ)
 = Declared Bearer/Boundary
 + Action Episode / Attempt
 + ActionSourceStanding
 + ActionGuidanceStanding
 + Typed ActionAttributionStanding
 + Action Domain / Granularity
 + Temporal / Occurrence Scope
 + Standing Route
 + Evidence / Provenance
```

This definition intentionally does **not** require:

```text
conscious intention
explicit belief/desire
language
planning
online deliberation
learning
stochastic choice
metaphysical free will
successful effect
overt movement
moral responsibility
```

### B8-017
**Agential action is sourced and guided action standing, not movement plus anthropomorphic interpretation.**

### B8-018
Actual alternative possibilities are not universally constitutive to a token action. Severe constraint can coexist with genuine performance; autonomy and responsibility are profiled separately.

### B8-019
The final minimal threshold remains provisional until later MF8 falsification.

---

# 9. `Action ownership` is not one primitive

MF8-A used `ActionOwnershipStanding` provisionally. MF8-B finds this phrase still too compressed.

A single action token can involve different bearers in different relations:

```text
Causal Source
Agential Author
Performer / Executor
Effector / Body / Tool
Principal / Delegator
Beneficiary
Experiential Owner
Role / Institutional Owner
Responsible / Accountable Party
```

These frequently diverge.

MF8-B replaces bare ownership with:

```text
ActionAttributionStanding(A, B, R | Σ)
```

where R declares the attribution route.

Key routes:

```text
SourceStanding
AuthorshipStanding
PerformanceStanding
ExecutionStanding
EffectorStanding
Principal/DelegationStanding
InstitutionalAttributionStanding
ExperientialAgencyStanding
ResponsibilityStanding
```

### B8-020
**ActionOwnershipStanding is henceforth a typed family/profile, not a single unqualified relation.**

### B8-021
`body moved` does not prove `body owner authored action`.

### B8-022
`person authored action` does not prove `person bears sole institutional/legal/moral responsibility`.

---

# 10. Authorship versus source versus execution

MF8-B uses `ActionAuthorshipStanding` for the stronger token relation:

```text
ActionAuthorshipStanding(A, B | Σ)
```

when B's action-producing organization is a grounded action source for A and the token is generated/accepted/maintained under B-relative action guidance rather than merely passing through B's body/tool/channel.

This admits:

- deterministic action;
- delegated action;
- habitual action;
- automatic skilled action;
- constrained action;

while rejecting automatic authorship from:

- externally moving a limb;
- a robot acting as pure remote actuator;
- a wire transmitting a command;
- an effect occurring downstream of a failed/altered actuation path.

### B8-023
**Authorship ≠ physical origin.**

### B8-024
**Authorship ≠ execution.** A person may author an action implemented by a tool; a device may execute without authoring.

### B8-025
Authorship can be nested/distributed across scales rather than always belonging to exactly one indivisible locus.

---

# 11. Counterfactual/source tests — evidence, not metaphysics

MF8-B proposes a falsification battery for source/authorship claims.

## T1 — Internal governance intervention

If relevant internal policy/guidance/source organization changes while external trigger is held sufficiently fixed, does action selection/initiation/maintenance change systematically?

## T2 — Bypass test

Can the same effector movement be produced while bypassing the candidate source organization? If yes, movement identity cannot establish authorship.

## T3 — Perturbation localization

Perturb source organization versus actuator versus environment. Do these perturbations dissociate selection, execution and effect?

## T4 — Suppression/cancellation

Can the bearer withhold, stop, redirect or modulate the episode under some admissible conditions? This is strong evidence of action governance but **not universally required** for every token.

## T5 — Guidance sensitivity

Does the episode vary with relevant policy/norm/task/value/learned guidance rather than merely with physical forcing?

## T6 — Provenance test

Is the alleged goal/policy/guidance intrinsic, learned, delegated, designed or merely observer-imputed?

### B8-026
No single counterfactual test is universally necessary or sufficient; together they constitute an evidence profile.

### B8-027
Counterfactual evidence must not be confused with a requirement for metaphysical alternative possibilities.

---

# 12. Involuntary movement and reflex

This is a decisive hard case.

A bearer can have AgencyStanding while a specific bearer-linked movement lacks token-level authorship.

```text
AgentBearer
 ≠ every bearer movement is Action
```

Examples:

- externally induced movement;
- startle;
- spinal reflex;
- spasm;
- seizure;
- alien/anarchic hand phenomena.

Human experiments also distinguish voluntary from externally induced movement at the level of action experience: Haggard, Clark & Kalogeras (2002) found different intentional-binding patterns for voluntary versus TMS-induced involuntary movement. Clinical work on anarchic/alien hand and agency misattribution similarly demonstrates that bodily movement, motor generation and conscious/agential attribution can dissociate.

### B8-028
**Effector ownership ≠ action authorship.**

### B8-029
**Endogenous motor generation ≠ agential action by itself.**

### B8-030
MF8-B does not legislate that every reflex is non-action in every biological theory. `Reflex action` may have a legitimate motor/ethological ActionRoleStanding, and organism-scale normative integration may support stronger attribution in some cases.

The correct rule is:

> Reflex vocabulary does not automatically transfer to AgentialActionStanding; source/guidance/attribution must be established at the declared scale.

---

# 13. Habit and automatic skill

A second hard case attacks the idea that all actions require current deliberative goal control.

Balleine & Dickinson distinguish goal-directed instrumental control from stimulus-response habit mechanisms; devaluation/contingency paradigms show that behavior can shift from current outcome-sensitive control toward learned habitual control.

MF8-B therefore preserves:

```text
GoalDirectedAction ≠ AllAction
HabitualControl ≠ NoOwnership automatically
Automatic ≠ Involuntary
Skilled ≠ Deliberative
```

### B8-031
A learned policy/disposition can provide ActionGuidanceStanding even when the agent is not online-computing an explicit outcome utility.

### B8-032
Automatic skilled sub-processes can participate in a higher-level owned action without each low-level motor correction becoming a separately intended action token.

### B8-033
Habit reduces or changes a goal-directedness profile; it does not by itself erase bearer/source attribution.

This becomes important for humans, animals and artificial policies alike.

---

# 14. Coercion, command, compulsion and constraint

These must not be collapsed.

```text
Environmental Constraint
≠ Instruction
≠ Authority Command
≠ Coercion
≠ Physical Compulsion
```

Provisional distinctions:

- **Instruction:** supplies information/action guidance.
- **Authority command:** instruction backed by a role/authority relation.
- **Coercion:** another actor changes stakes/options through threat or imposed costs while the subject may still retain local action-source organization.
- **Physical compulsion:** external force/process directly produces or overrides bodily behavior, potentially bypassing authorship.
- **Constraint:** limits feasibility without necessarily involving another agent.

Caspar et al. (2016) found that coercive orders reduced implicit measures of sense of agency relative to free choice for otherwise similar harmful keypress actions. This is evidence that coercion changes agency experience/control profile, not evidence that commanded behavior ceases to be action by definition.

### B8-034
**Coercion can reduce autonomy and experiential agency without automatically erasing ActionAuthorshipStanding.**

### B8-035
**Physical compulsion can erase or bypass authorship while leaving body movement/effect intact.**

### B8-036
Responsibility consequences require a later normative layer and cannot be read directly from ActionStanding.

---

# 15. Remote control, tools and delegated action

Remote control provides perhaps the cleanest source/effector dissociation.

Case:

```text
Human operator
  → command
  → communication channel
  → robot controller
  → actuator
  → target effect
```

Possible standings:

```text
operator:       macro ActionAuthorship
robot body:     Execution/EffectorStanding
robot controller: ControlStanding
```

but if the robot additionally performs autonomous obstacle avoidance, local replanning or goal arbitration:

```text
operator authors one higher-level action constraint/goal
robot may author lower-level/local actions
```

### B8-037
**Tool use does not transfer authorship to the tool merely because the tool realizes the effect.**

### B8-038
**Autonomous subsystems can introduce nested authorship rather than forcing a binary human-versus-machine owner.**

### B8-039
Delegation can create several simultaneous attribution routes: performer, operational author, principal and institution need not be identical.

This directly prepares later responsibility and collective-agency work.

---

# 16. Action scale and hierarchical decomposition

Actions are not naturally atomic.

Example:

```text
write report
  ├─ open editor
  ├─ compose paragraph
  ├─ type sentence
  └─ press keys
       └─ motor corrections
```

At different scales, different processes have ActionRole/AgentialAction standing.

MF8-B introduces:

```text
ActionDecompositionStanding(A, {a_i}, Relation, Scale | Σ)
```

for grounded relations between macro action and subactions/implementation episodes.

### B8-040
**Macro action ownership does not imply that every micro control update is a separately intended action.**

### B8-041
**Micro execution causation does not determine macro authorship.**

### B8-042
Action granularity is therefore constitutive to a well-formed ActionClaim.

---

# 17. Internal action and omission

If action required visible motion/effect, two important classes would be lost.

## 17.1 Internal/epistemic action

Candidates include:

- shifting attention intentionally;
- rehearsing information;
- querying memory;
- changing an internal computational workspace;
- deliberate simulation/search;
- modifying one's own policy/configuration where genuinely action-guided.

MF8-B does not yet freeze which mental processes qualify, but **external actuation is not constitutive**.

## 17.2 Omission

Mere non-occurrence is not action:

```text
Nothing happened
 ≠ omission action
```

Provisional:

```text
OmissiveActionStanding(O, B | Σ)
```

requires at least:

```text
relevant actionable/opportunity context
+ bearer-relative action guidance
+ governed withholding/suppression/non-initiation
+ typed attribution
+ temporal scope
```

### B8-043
**Action ≠ movement.** A governed withholding can carry action standing.

### B8-044
A formal `NOOP` action has ActionRoleStanding automatically inside a formal action space, but target OmissiveActionStanding still requires grounding.

### B8-045
Omission is a powerful falsifier against `Action = state change caused by agent`.

No MF7 reopen follows: MF7 transition/change remains neutral, while MF8 action standing is a higher-level relation.

---

# 18. Sense of agency and target authorship remain separate

MF8-A already established:

```text
AgencyStanding
≠ FeelingOfAgency
≠ JudgementOfAgency
```

MF8-B sharpens this at token level:

```text
ActionAuthorshipStanding
≠ ExperiencedAuthorship
≠ ReportedAuthorship
≠ ObserverAttribution
```

Daprati et al. (1997) showed that participants can misattribute viewed hand actions, with stronger impairments in some schizophrenia groups. Haggard et al. (2002) and Caspar et al. (2016) likewise show that agency experience varies with action-generation/coercion conditions.

### B8-046
A real action can be misexperienced as not one's own.

### B8-047
A non-authored event can be experienced/judged as one's own.

### B8-048
Perceptual/experiential evidence therefore supports an AgencyExperience profile, not target authorship by identity.

MF2/MF3 remain frozen.

---

# 19. Goal-directed action is a stronger profile

Davidson's classic causal-rational account treats reasons as causes that rationalize intentional action. This remains a powerful model for reflective human action, but MF8-B does not universalize belief-desire reasoning to minimal biological/artificial agency.

Define provisionally:

```text
IntentionalActionProfile
GoalDirectedActionProfile
ReasonResponsiveActionProfile
DeliberativeActionProfile
```

as progressively richer typed profiles over the minimal action core.

### B8-049
**IntentionalAction ≠ all AgentialAction.**

### B8-050
**Reason-rationalized action is a richer standing route, not the definition of all biological/software action.**

### B8-051
MF8-C/D must later determine exactly how goals, preferences, decisions and intentions enrich ActionGuidanceStanding.

---

# 20. Action identity through time

MF7 identity/persistence is consumed directly.

Distinguish:

```text
ActionType
ActionToken
ActionAttempt
ActionExecutionEpisode
ActionEffect
ActionOutcome
ActionHistory/Record
```

### B8-052
Repeating the same action type creates a new token unless a declared continuation criterion says otherwise.

### B8-053
An interrupted/retried operation may be one continuing action, a failed action plus new action, or several subactions depending declared identity criterion.

### B8-054
`same command bytes` does not establish same action token.

### B8-055
Action can have initiation, maintenance, cancellation, completion and effect windows that do not coincide temporally.

No MF6/MF7 reopen is required.

---

# 21. Joint action versus collective agency

MF8-B does not preempt the later collective-agency round.

A joint episode can involve several individually authored contributions:

```text
JointActionStanding
 ≠ CollectiveAgencyStanding
```

Two people carrying a table may participate in a coordinated joint action without requiring a new group-agent bearer. Conversely, a corporation may support institutional/collective action attribution through organization beyond simple simultaneous coordination.

### B8-056
**JointAction ≠ shared intention universally.** Some coordinated action can be asymmetric, delegated or role-structured.

### B8-057
**JointAction ≠ CollectiveAgent.**

### B8-058
Later collective agency must independently establish a collective bearer/source/guidance/attribution organization.

---

# 22. Hard-case audit

## HC-B1 — Rock pushed by wind

```text
state/dynamics/change        yes
causal source in wind        yes
rock BehaviorStanding        perhaps under material-behavior vocabulary
rock ActionSourceStanding    no grounded evidence
AgentialActionStanding       no
```

PASS.

## HC-B2 — Thermostat switching relay

```text
ControlStanding              yes
ActionRoleStanding           possible
BehaviorStanding             yes
ActionSource/Guidance         formal operational candidate
full/autonomous agency       not established merely from control
```

MF8-B intentionally does not use the relay switch alone to settle the thermostat's final AgencyStanding threshold.

PASS.

## HC-B3 — Human arm moved externally

Body/effector movement exists; subject authorship may not.

PASS: proves `body movement ≠ action authorship`.

## HC-B4 — Spinal withdrawal reflex

Bearer-linked biological behavior exists. AgentialActionStanding depends on declared scale and evidence for organism-level source/guidance integration; `reflex action` terminology alone is insufficient.

PASS without dogmatic binary classification.

## HC-B5 — Habitual keypress

Online outcome evaluation can be weak while acquired action policy/history continues to organize behavior.

PASS: `goal-directedness ≠ action constitution`.

## HC-B6 — Coerced keypress

Action source may remain with subject while autonomy, alternatives and sense of agency are reduced.

PASS: `coercion ≠ physical compulsion ≠ no action`.

## HC-B7 — Hand physically forced onto button

Effect occurs through subject's body, but source/authorship can be external.

PASS.

## HC-B8 — Remote robot

Robot executes; human may author. If robot locally replans, nested authorship becomes possible.

PASS.

## HC-B9 — Paralyzed attempt

No external movement/effect; action attempt still possible if action engagement/source/guidance are grounded.

PASS: `attempt ≠ effect`.

## HC-B10 — Deliberate withholding

No overt movement, yet omissive action can be grounded under opportunity + guidance + governed withholding.

PASS: `action ≠ change`.

## HC-B11 — Alien/anarchic hand

Bodily movement and conscious/agential attribution can dissociate.

PASS: `effector ownership ≠ authorship ≠ experienced agency`.

## HC-B12 — RL `NOOP`

Formal ActionRoleStanding is clear; target agential omission requires separate grounding.

PASS: representation/formal firewall survives.

## HC-B13 — Script executing scheduled command

Behavior/action-role standing may be formal; initiative by schedule alone does not establish stronger target authorship/agency.

PASS.

## HC-B14 — Human using autonomous coding/tool agent

One episode can contain user principal/delegation standing, system-local action authorship, tool execution and downstream effects. Attribution must be typed rather than assigned to one magical `owner`.

PASS as architecture-neutral ontology case.

---

# 23. Provisional ActionProfile v0

```text
ActionProfile = <
  ActionToken/Type,
  Bearer/Boundary,
  ActionRoleStanding?,
  BehaviorMapping?,
  ActionSourceStanding,
  ActionGuidanceStanding,
  Guidance Provenance,
  ActionEngagement/Attempt,
  Execution/Actuation Route?,
  Target Effect/Outcome?,
  Success Criterion?,
  Attribution Routes {
    Authorship?,
    Performer?,
    Executor?,
    Effector?,
    Principal/Delegator?,
    Institutional?,
    Experiential?,
    Responsibility?
  },
  Action Domain,
  Granularity/Hierarchy,
  Internal/External/Omissive?,
  Reactive/Habitual/GoalDirected/Intentional?,
  Constraint/Command/Coercion Context?,
  Autonomy Profile?,
  Joint/Collective Context?,
  Temporal Scope,
  Identity/Continuation Criterion,
  Standing Route,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### B8-059
A bare `X did Y` claim is ontologically compressed; serious use should expose the attribution route and action scale.

---

# 24. Provisional ActionClaim v0

```text
ActionClaim = <
  Candidate Episode,
  Declared Bearer,
  Action Standing Route,
  ActionSource Evidence,
  ActionGuidance Evidence,
  Engagement/Attempt Evidence,
  Attribution Route(s),
  Execution/Effect Evidence?,
  Granularity/Scale,
  Temporal Scope,
  Constraint/Delegation Context?,
  Uncertainty,
  Provenance
>
```

### B8-060
Evidence for effect alone is insufficient to establish ActionClaim.

### B8-061
Evidence for command alone is insufficient to establish execution, authorship or effect.

### B8-062
Experienced agency alone is insufficient to establish target authorship.

---

# 25. Revised AgencyStanding candidate v0.2

MF8-B resolves MF8-A's circularity by revising the candidate dependency:

```text
AgencyStanding(B | Σ)
 = Individuated/Persistent Bearer
 + Persistent Agential Source Organization
 + EvaluativeOrientationStanding
 + Action Domain/Repertoire
 + Capacity to instantiate AgentialActionStanding tokens
 + Autonomy/Delegation Profile
 + Standing Route
 + Scope
```

where `AgentialActionStanding(token)` is defined independently by MF8-B rather than by first asserting AgencyStanding.

### B8-063
**Agency is a persistent bearer-level capacity/organization; action is token/episode standing.**

### B8-064
This is a substantive refinement of MF8-A but does not reopen MF0–MF7.

### B8-065
`Action ownership` in MF8-A is replaced by the typed ActionAttribution family rather than one scalar/boolean ownership relation.

---

# 26. Final MF8-B non-collapse stack

```text
ActionRoleStanding ≠ AgentialActionStanding
BehaviorStanding ≠ AgentialActionStanding
StateTransition ≠ Action
Movement ≠ Action
Change ≠ Action
```

```text
Cause ≠ ActionSourceStanding
Control ≠ ActionAuthorship
Command ≠ Action
Actuation ≠ ActionAuthorship
Effect ≠ Action
Success ≠ Action
```

```text
ActionAttempt ≠ Execution
Execution ≠ Effect
Effect ≠ OutcomeEvaluation
```

```text
Source ≠ Author
Author ≠ Performer
Performer ≠ Effector
Author ≠ Principal
Principal ≠ ResponsibleParty
```

```text
BodyOwnership ≠ ActionAuthorship
ActionAuthorship ≠ ExperiencedAgency
ExperiencedAgency ≠ ReportedAgency
```

```text
GoalDirectedAction ≠ AllAction
Habitual ≠ NonAction by identity
Automatic ≠ Involuntary
Reactive ≠ NonAction
```

```text
Constraint ≠ Command
Command ≠ Coercion
Coercion ≠ PhysicalCompulsion
```

```text
JointAction ≠ CollectiveAgency
ToolExecution ≠ ToolAuthorship
Delegation ≠ LossOfAllLocalAuthorship
```

```text
Omission ≠ MereAbsence
Action ≠ OvertMovement
```

---

# 27. FoundationReopen audit

MF8-B actively attacks FRC-A1:

> Does genuine action force State, Dynamics or Control to be redefined?

Result: **no**.

Why:

- state transition remains a neutral occurrence/change relation;
- action adds source/guidance/attribution standing above transitions;
- control remains controller-governed influence and can exist without action authorship;
- command/actuation/effect separation survives and becomes essential;
- omission/action-attempt cases do not require transition to become action;
- source/authorship can be represented without inserting goals/free will into ControlStanding.

### B8-066
**FRC-A1 is NOT triggered.**

No other MF0–MF7 reopen condition appears.

Potential future FRC-A1 trigger remains only if later goal/choice/collective-agency work uncovers a genuine case that cannot be expressed without changing the constitutive State/Dynamics/Control cores.

---

# 28. Evidence anchors

Primary/authoritative anchors used in this round:

1. **Donald Davidson (1963), `Actions, Reasons, and Causes`, Journal of Philosophy 60(23), DOI `10.2307/2023177`.** Used as a canonical richer account of intentional/reason-rationalized action; MF8-B does not universalize it to all minimal agency.
2. **Patrick Haggard, Sam Clark & Jeri Kalogeras (2002), `Voluntary action and conscious awareness`, Nature Neuroscience 5, DOI `10.1038/nn827`.** Voluntary action and TMS-induced involuntary movement show different intentional-binding patterns; used to separate movement from voluntary/action-experience profiles.
3. **Elisabeth Pacherie (2008), `The phenomenology of action: a conceptual framework`, Cognition 107, DOI `10.1016/j.cognition.2007.09.003`.** Used to preserve distinctions among aspects of action phenomenology rather than equating subjective ownership with target authorship.
4. **Emilie A. Caspar, Julia F. Christensen, Axel Cleeremans & Patrick Haggard (2016), `Coercion Changes the Sense of Agency in the Human Brain`, Current Biology 26, DOI `10.1016/j.cub.2015.12.067`.** Coercion reduces implicit sense-of-agency measures; used to separate coercion, experiential agency, authorship and responsibility.
5. **Bernard W. Balleine & Anthony Dickinson (1998), `Goal-directed instrumental action: contingency and incentive learning and their cortical substrates`, Neuropharmacology 37, DOI `10.1016/S0028-3908(98)00033-1`.** Distinguishes goal-directed instrumental control from stimulus-response habit mechanisms; used against `all action = online goal-directed deliberation`.
6. **Anthony Dickinson, D. J. Nicholas & Christopher D. Adams (1983), `The effect of the instrumental training contingency on susceptibility to reinforcer devaluation`, Quarterly Journal of Experimental Psychology B 35, DOI `10.1080/14640748308400912`.** Empirical devaluation/contingency work underlying goal-directed versus habitual control distinctions.
7. **Sergio Della Sala, Clelia Marchetti & Hans Spinnler (1991), `Right-sided anarchic (alien) hand: a longitudinal study`, Neuropsychologia 29, DOI `10.1016/0028-3932(91)90081-I`.** Clinical dissociation used to stress that bodily movement/effector ownership and agential attribution can diverge.
8. **Elena Daprati et al. (1997), `Looking for the agent: an investigation into consciousness of action and self-consciousness in schizophrenic patients`, Cognition 65, DOI `10.1016/S0010-0277(97)00039-5`.** Action-source attribution can be experimentally dissociated/misattributed; supports perceived-versus-target agency firewall.
9. **Xabier E. Barandiaran, Ezequiel Di Paolo & Marieke Rohde (2009), `Defining Agency: Individuality, Normativity, Asymmetry, and Spatio-temporality in Action`, Adaptive Behavior 17, DOI `10.1177/1059712309343819`.** Active-source/normativity framework remains an important minimal natural-agency falsifier and motivates source/guidance separation.

The evidence does **not** decide one universal philosophical theory of action. MF8-B uses cross-domain dissociations to keep the ontology typed where the literature itself distinguishes phenomena.

---

# 29. MF8-B verdict

The deepest result is not `action = intentional movement`.

It is:

```text
ACTION TOKEN
 = bearer-relative episode/attempt
 + grounded ActionSourceStanding
 + grounded ActionGuidanceStanding
 + action engagement
 + typed attribution/authorship
 + declared granularity/time/standing route

NOT REQUIRED:
 movement
 successful effect
 conscious intention
 online planning
 stochastic choice
 metaphysical free will
 moral responsibility
```

And:

```text
ACTION OWNERSHIP
is not one primitive.

source / author / performer / executor / effector /
principal / institution / experience / responsibility
must be typed separately.
```

This lets the ontology represent, without collapse:

- failed attempts;
- tool-mediated action;
- remote control;
- nested autonomy;
- habit and skill;
- coercion;
- involuntary movement;
- action misattribution;
- omission;
- internal action candidates;
- hierarchical and joint action.

Most importantly, MF8-B resolves the MF8-A circularity:

```text
AgentialActionStanding(token)
    does not require prior AgencyStanding.

AgencyStanding(bearer)
    can now be reconstructed as persistent capacity/organization
    for producing such sourced, guided, attributable action tokens.
```

---

# 30. Next frontier

Proceed directly to:

```text
MF8-C — Goal, Need, Want, Preference, Utility & Value
```

Primary questions:

1. What is `EvaluativeOrientationStanding` actually made of?
2. How do need, drive, desire/want, preference, value, utility, reward, objective, goal and norm differ?
3. Which of these can be intrinsic/constituted by a bearer and which are necessarily representational or assigned?
4. Can a system have goals without explicit goal representation?
5. How should biological viability, reinforcement-learning reward, economic utility, human preference and institutional objectives coexist without semantic collapse?
6. Does intrinsic normativity require self-maintenance/autonomy, or can other standing routes support it?
7. What provenance tests distinguish observer-imputed teleology from target-grounded evaluative standing?

MF0–MF7 remain frozen unless a named concrete FoundationReopenCondition is demonstrated.
