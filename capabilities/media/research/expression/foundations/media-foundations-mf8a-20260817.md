# Ordivon Media Foundations — MF8-A Agency Ontology & Term Separation

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 47 at start  
**Input:** MF0–MF7 frozen as current v1 substrate.  
**Status:** **MF8-A COMPLETE / PROVISIONAL ONTOLOGY. MF8 Agency Foundations are not frozen yet.**  
**Next:** MF8-B — Action, Behavior & Action Ownership.

---

# 0. Purpose

MF8-A begins Agency Foundations without reopening MF0–MF7. The task is not to choose one historical definition of `agent`; it is to separate several concepts that different fields routinely collapse:

```text
AgentRole
Agent
Agency
Action
Action Ownership
Control
Goal
Choice
Decision
Policy
Plan
Autonomy
Initiative
Intentionality
Sense of Agency
Learning
Adaptation
Responsibility
Collective Agency
```

The opening question inherited from MF7 is:

> What makes a stateful, controlled, adaptive system acquire AgencyStanding rather than merely exhibiting control, regulation, goal-shaped trajectories, self-organization or externally interpreted purposiveness?

MF8-A's first result is that this question is malformed if `agent` is treated as one untyped boolean natural kind. Software-agent engineering, reinforcement-learning interfaces, biological autonomy, philosophy of action, phenomenological sense of agency and institutional/collective agency use overlapping but non-identical standings.

---

# 1. Frozen MF7 boundary consumed, not reopened

MF8-A preserves:

```text
Agent ≠ Controller
Agency ≠ Control
Action ≠ StateTransition
Goal ≠ Attractor
Goal ≠ Setpoint
Policy ≠ Intent
SelfOrganization ≠ Agency
Coordination ≠ CollectiveAgency
CollectiveBehavior ≠ CollectiveGoal
```

MF7 already supplies:

- Bearer/Boundary;
- ConfigurationStanding;
- EvolutionStanding;
- ContinuationStanding / identity criteria;
- ControlStanding;
- macro/collective standing;
- command/actuation/effect separation;
- provenance and standing routes.

Agency must be layered on top of these rather than injected back into them.

### A8-001
**No FoundationReopenCondition is triggered at the start of MF8-A.**

### A8-002
In particular, no current case requires `ControlStanding` to contain goals, values, intentions, free choice or consciousness.

---

# 2. Literature collision: `agent` is not one settled scientific primitive

Classic software-agent work uses a deliberately operational notion. Wooldridge & Jennings distinguish a weak agent notion around autonomy, social ability, reactivity and pro-activeness; Franklin & Graesser likewise seek to distinguish autonomous agents from arbitrary programs by situated, temporally extended sensing/action organization.

Natural-agency work attacks exactly this looseness. Barandiaran, Di Paolo & Rohde argue that genuine agency requires individuality, interactional asymmetry and normativity, and characterize agency through autonomous organization adaptively regulating environment coupling. Di Paolo separately argues that self-organization/autopoiesis alone is insufficient for sense-making; adaptivity with respect to viability conditions matters.

Philosophy of action asks when an occurrence is an action attributable to an agent rather than mere movement; Davidson's reasons/action account is one influential higher-level causal-rational model, but reason responsiveness cannot be assumed for minimal biological/artificial agency.

Cognitive neuroscience separately studies the *sense* or attribution of agency. Synofzik, Vosgerau & Newen explicitly separate non-conceptual feeling of agency from conceptual judgement of agency. Therefore experience/attribution of authorship cannot define agency itself.

Collective-agency theory asks when an organized group may be treated as a unified agent rather than merely an aggregate of individual agents; List & Pettit explicitly make group organization central to this question.

### A8-003
**Different literatures are often defining different standings, not merely disagreeing about one hidden scalar property.**

### A8-004
MF8 therefore rejects `isAgent: boolean` as the foundational representation.

---

# 3. First firewall: AgentRoleStanding ≠ AgencyStanding

A system can occupy the `agent` side of a formal interface without thereby establishing target-grounded agency.

Provisional primitive:

```text
AgentRoleStanding(B, R | Σ)
```

A bearer/component has AgentRoleStanding when a formal, computational, institutional or experimental schema constitutes or recruits it as the acting/decision-bearing side of an interaction, task or delegation relation.

Examples:

- the `agent` in an RL environment API;
- a software process designated as an agent in a multi-agent system;
- a legal representative acting under an assigned role;
- a simulated agent in a game model.

### A8-005
**AgentRoleStanding can be fully legitimate without implying autonomous or intrinsic AgencyStanding.**

### A8-006
`RLAgent`, `SoftwareAgent`, `SimulationAgent` and `LegalAgent` are therefore standing-route claims before they are metaphysical claims.

### A8-007
**Naming a component `agent` does not move an arbitrary program from nominal vocabulary to target AgencyStanding.**

---

# 4. Second firewall: Agent ≠ Agency

MF8-A uses:

```text
Agent = bearer of a declared AgentRole and/or AgencyStanding under scope
Agency = typed standing/capacity relation of that bearer
```

This prevents a category error:

- `agent` is primarily bearer/role language;
- `agency` concerns what kind of source/ownership/evaluative action organization the bearer has.

### A8-008
An agent can temporarily perform no action while retaining agency capacity/standing.

### A8-009
One bearer can have multiple agency standings simultaneously: biological, delegated, institutional, computational or reflective.

### A8-010
A component may have AgentRoleStanding but fail stronger AgencyStanding tests.

---

# 5. Agency core candidate — deliberately provisional

MF8-A does **not** freeze the final minimal agency threshold. It establishes the smallest candidate structure that later rounds must attack:

```text
AgencyStanding(B | Σ)
 ≈ Individuated/Persistent Bearer
 + AgentialSourceStanding
 + EvaluativeOrientationStanding
 + Action-Repertoire / Action-Production Route
 + ActionOwnershipStanding
 + StandingRoute
 + Scope
```

Each term is typed and must carry evidence/provenance.

## 5.1 Individuated/Persistent Bearer

Agency is attributable to a non-arbitrary bearer/system/collective under an identity/continuation criterion supplied by MF4/MF7.

```text
Arbitrary Aggregate ≠ Agent
```

## 5.2 AgentialSourceStanding

Provisional:

```text
AgentialSourceStanding(B, M | Σ)
```

holds when B's own organized mechanism M is a non-trivial locus through which conditions, internal state and action-guiding organization govern which candidate influence/behavior is attempted, rather than B being merely a passive transmission path, externally moved object or bare effector.

This is **not** metaphysical first-cause language. External stimuli, commands, norms and constraints may influence an agent. The issue is whether the bearer's organization materially mediates and governs action production.

## 5.3 EvaluativeOrientationStanding

Agency seems to require more than arbitrary output variation: candidate actions/continuations must be regulated relative to some typed distinction such as:

```text
better / worse
acceptable / unacceptable
needed / harmful
permitted / forbidden
success / failure
preferred / dispreferred
viable / non-viable
```

But the provenance of that evaluative organization must remain explicit:

```text
intrinsic/self-maintained
biological/viability-grounded
designed
externally assigned
delegated
social/institutional
learned
represented/inferred by observer
```

### A8-011
**External assignment of a goal or reward does not become intrinsic value merely because a system optimizes it.**

### A8-012
Evaluative orientation is therefore a typed standing with provenance, not a generic scalar `utility` primitive.

## 5.4 Action repertoire / production route

Agency requires a route through which the bearer can attempt differentiated interventions/behaviors relative to its own state/environment/others. The repertoire can be discrete, continuous, stochastic, deterministic, learned or fixed.

### A8-013
**Agency does not require indeterminism or metaphysical free choice.**

A deterministic policy can still govern different actions under different conditions.

## 5.5 ActionOwnershipStanding

Action ownership is not identical to causal contribution.

```text
Cause ≠ Control ≠ Action Ownership
```

An effect can be caused by a bearer, or transmitted through its actuator, without the action being attributable to that bearer as agential source.

### A8-014
**MF8-B must make ActionOwnershipStanding a first-class relation rather than infer it from motion, control signals or downstream effect.**

---

# 6. Agency must not require its richer descendants

MF8-A rejects the following as universal constituents of minimal agency:

```text
Agency ≠ Consciousness
Agency ≠ Language
Agency ≠ Explicit Belief
Agency ≠ Explicit Desire
Agency ≠ Utility Maximization
Agency ≠ Planning
Agency ≠ World Model
Agency ≠ Self Model
Agency ≠ Learning
Agency ≠ Adaptation
Agency ≠ Stochastic Choice
Agency ≠ Moral Responsibility
Agency ≠ Sense of Agency
```

These can be stronger profiles or later forms.

### A8-015
Requiring explicit reasons would exclude plausible biological/minimal agency cases.

### A8-016
Requiring learning would exclude fixed but genuinely action-capable agents.

### A8-017
Requiring consciousness would collapse natural/artificial agency into a consciousness theory that MF8 neither has nor needs.

---

# 7. Control, behavior, action and effect

MF7 supplies a neutral control/evolution substrate. MF8 adds an agency-sensitive layer.

Provisional stack:

```text
State Transition / Process Occurrence
        ↓
BehaviorOccurrence of bearer
        ↓ optional control route
Controlled / Effector-Mediated Behavior
        ↓ agency-source + ownership standing
Action / Action Attempt
        ↓ optional successful actuation
Target Effect
```

Critical:

```text
Behavior ≠ Action
ControlOccurrence ≠ Action
ActionAttempt ≠ SuccessfulEffect
Command ≠ Actuation ≠ Effect
```

### A8-018
A failed attempt can still be an action.

### A8-019
A successful externally caused effect can fail to be an action of the affected/actuated bearer.

### A8-020
This preserves MF7 without redefining transition or control.

---

# 8. Goal ≠ attractor ≠ setpoint ≠ reward

MF7 already freezes:

```text
Goal ≠ Attractor
Goal ≠ Setpoint
```

MF8-A adds:

```text
Goal ≠ RewardSignal
Goal ≠ UtilityFunction
Goal ≠ Preference
Goal ≠ Need
Goal ≠ Want
```

A dynamical attractor is a continuation/stability structure. A setpoint is a control reference. A reward is a formal/evaluative signal. A utility function is an evaluative representation. None becomes an agent's goal without GoalStanding: a grounded action-guiding/evaluative target relation for the declared bearer/role.

### A8-021
A system may exhibit goal-shaped trajectories without possessing target-grounded GoalStanding.

### A8-022
A formal model may legitimately assign a goal at the model/role layer without proving intrinsic biological/psychological goals.

The Need/Want/Preference/Utility/Value family is deferred to MF8-C.

---

# 9. Choice ≠ decision ≠ policy ≠ action

Provisional separations:

```text
Choice
 = selection relation/outcome among differentiated admissible alternatives

Decision
 = process/commitment that resolves or narrows alternatives under some decision organization

Policy
 = rule/kernel/procedure mapping relevant conditions/information to action distributions or selections

Plan
 = temporally/structurally organized prospective action commitment/constraint structure

Action
 = owned attempted behavior/influence occurrence under AgencyStanding
```

Therefore:

```text
Policy ≠ Choice
Policy ≠ Decision
Policy ≠ Intent
Decision ≠ Action
Choice ≠ FreeWill
```

### A8-023
A deterministic policy can implement choice in an operational sense without requiring indeterminism.

### A8-024
A policy can exist in a controller with no stronger agency claim.

### A8-025
A decision can revise a policy or plan without immediately producing external action.

Detailed reconstruction is deferred to MF8-D.

---

# 10. Autonomy ≠ agency

`Autonomy` is overloaded. MF8-A treats it as a **governance-dependence profile**, not a synonym for agency.

Candidate autonomy dimensions:

```text
Action Autonomy       — who governs immediate action selection?
Policy Autonomy       — who can change the action-selection rule?
Goal Autonomy         — who sets/revises goals?
Norm/Value Autonomy   — where do evaluative criteria come from?
Resource Autonomy     — can the bearer acquire/manage required resources?
Boundary Autonomy     — can it maintain its own organization/identity?
Temporal Autonomy     — can it sustain activity without continuous external command?
Authority Autonomy    — what permissions can it exercise without escalation?
```

### A8-026
**Agency can exist with limited autonomy**, e.g. delegated or institutionally constrained agency.

### A8-027
**Autonomy can exist in an organizational/self-maintaining sense without proving full action agency.**

### A8-028
Therefore `autonomous agent` must report which autonomy dimensions and standing routes are intended.

Biological autonomy theories supply one important route but are not imposed universally on software/institutional agents.

---

# 11. Reactivity and initiative

Classic software-agent work distinguishes reactivity from pro-activeness. MF8-A keeps this as a profile rather than agency constitution.

```text
ReactiveAction
 = action production triggered/organized primarily around current external/internal change

Initiative / Proactivity
 = action initiation not reducible to immediate triggering stimulus, under continuing goals/norms/plans/internal dynamics
```

### A8-029
**Reactive ≠ Non-agent.**

### A8-030
**Proactive ≠ Autonomous by itself.** A scheduled script can initiate activity without richer agency standing.

---

# 12. Intentionality is at least two different concepts

The word `intentionality` must be split immediately:

```text
Intentionality_aboutness
 = representational/mental directedness or aboutness

IntentionalActionStanding
 = action performed under an intention/goal/reason/commitment relation
```

MF3 already prevents representation/content from being assumed merely because information is decodable.

### A8-031
**Representational aboutness ≠ intentional action.**

### A8-032
**Intentional action is a richer agency profile, not the definition of all agency.**

### A8-033
`Intent`/`Intention` should be modeled later as a temporally extended action-guiding commitment state, not as policy by identity.

---

# 13. Agency ≠ sense/judgement of agency

Human cognitive science provides a decisive firewall:

```text
AgencyStanding
 ≠ FeelingOfAgency
 ≠ JudgementOfAgency
 ≠ OwnershipExperience
```

Synofzik et al. distinguish feeling of agency and judgement of agency, demonstrating that authorship experience itself is multi-level and inferentially mediated.

### A8-034
A bearer can have agency while misperceiving authorship.

### A8-035
A subject can experience agency for an event it did not in fact control/own.

### A8-036
Perceived/experienced agency belongs partly to MF2/MF3/experience layers and cannot ground target AgencyStanding by itself.

No MF2/MF3 reopen is required.

---

# 14. Learning and adaptation

Di Paolo's biological account is important because it distinguishes mere self-organization from adaptive regulation relative to viability. But MF8-A does not make learning/adaptation universal agency constituents.

```text
Learning
 = relatively persistent change in internal organization/policy/model/value/etc. as a consequence of information/experience/training/history

Adaptation
 = change/regulation that improves or preserves fit/performance/viability relative to declared criteria and timescale
```

### A8-037
**Learning ≠ Agency.** A passive predictor can learn without acting.

### A8-038
**Adaptation ≠ Agency.** An externally optimized/self-tuning mechanism can adapt without acquiring action ownership/autonomous agency.

### A8-039
Conversely, a fixed policy organism/system may still possess agency.

Biological adaptivity remains strong evidence for intrinsic normative/evaluative standing and will be revisited later.

---

# 15. Responsibility ≠ agency

Responsibility is downstream and stronger.

```text
CausalResponsibility
AgentialResponsibility
RoleResponsibility
LegalResponsibility
MoralResponsibility
Accountability
Liability
```

must remain separate.

### A8-040
Agency may be necessary for some forms of responsibility but is not sufficient for moral/legal responsibility.

### A8-041
Delegated software/institutional agency can coexist with human/institutional accountability located elsewhere.

Responsibility is deferred to a later MF8 round.

---

# 16. Collective agency

MF7 already provides collective bearer/macro standing and rejects arbitrary aggregation.

MF8-A therefore begins from:

```text
Collection ≠ CollectiveBearer
Coordination ≠ CollectiveAgency
Synchronization ≠ CollectiveAgency
SharedGoal ≠ CollectiveAgency
CollectiveBehavior ≠ CollectiveAction by default
```

A collective-agency claim must show a collective-scale bearer/organization through which action source, evaluative orientation, decision/action integration and ownership are grounded at the collective scale.

### A8-042
**Collective agency cannot be inferred by summing individual agency scores.**

### A8-043
A corporation, committee or team can be a candidate collective agent only if organizational structure supports unified collective action/decision standing; mere membership is insufficient.

### A8-044
A flock/swarm can display sophisticated coordination and self-organization without automatically acquiring collective AgencyStanding.

Detailed reconstruction is deferred to MF8-H.

---

# 17. Standing routes versus richness profiles

MF8-A rejects a single linear `agency level` ladder because distinct domains can be incomparable.

Instead separate:

## 17.1 Standing/claim routes

```text
NominalAgentVocabulary
Formal/Interface AgentRoleStanding
Designed/Operational AgencyStanding
Delegated AgencyStanding
Biological/Organismic AgencyStanding
Psychological/Intentional AgencyStanding
Institutional AgencyStanding
Collective AgencyStanding
Represented/Attributed AgencyClaim
```

These routes may coexist.

## 17.2 Richness/profile dimensions

```text
AgencyProfile = <
  Bearer/Boundary,
  Identity/Persistence,
  AgentRoleStanding?,
  AgentialSourceStanding?,
  ActionDomain/Repertoire,
  Sensing/Conditioning Route?,
  Control/Authority Route?,
  EvaluativeOrientationStanding?,
  Evaluative Provenance,
  Goal/Need/Preference/Value Profile?,
  Policy/Decision/Plan Profile?,
  ActionOwnership Profile?,
  Action/Policy/Goal/Norm Autonomy,
  Reactive/Initiative Profile,
  Deterministic/Stochastic/Nondeterministic Selection?,
  WorldModel/SelfModel?,
  Learning/Adaptation?,
  Intentional/Reason-Responsive Profile?,
  Sense/JudgementOfAgency Mapping?,
  Delegation/Responsibility/Accountability?,
  CollectiveScale?,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### A8-045
A thermostat, bacterium, RL policy, corporation and human should not be forced onto one scalar axis.

### A8-046
The right question is **which agency standings and profiles are grounded, through which route, at what scale and scope?**

---

# 18. Hard-case audit

## HC-A — Rock moved by wind

- state/dynamics: yes;
- causal interaction: yes;
- control: no by default;
- agent role: no;
- agency: no grounded source/evaluative/ownership route.

PASS.

## HC-B — Thermostat/PID regulator

- formal state/control: yes;
- setpoint/error regulation: yes;
- free choice/consciousness: unnecessary;
- autonomous biological normativity: not established;
- AgentRoleStanding: possible if a model constitutes it that way;
- richer AgencyStanding: **threshold intentionally unresolved** pending MF8-B/C, but it must never be promoted to `full autonomous agent` merely from feedback control.

PASS as term-separation falsifier.

## HC-C — Remote-controlled robot

- local actuation/effect: yes;
- controller can be external;
- robot body is not automatically the agential source;
- ownership may attach to remote operator/system rather than actuator.

PASS; proves `effect bearer ≠ action owner`.

## HC-D — Scripted cron job

- initiative in the weak temporal sense: yes;
- may execute externally specified commands;
- no conclusion about agency from autonomous scheduling alone.

PASS; proves `initiative ≠ agency`.

## HC-E — RL policy in simulator

- AgentRoleStanding: yes by formal interface;
- reward/policy/action vocabulary: formally legitimate;
- intrinsic value/autonomous agency: not established merely by RL semantics.

PASS; proves `formal agent role ≠ intrinsic agency`.

## HC-F — Bare language model versus deployed tool-using system

- bare model call: no persistent bearer/action authority is guaranteed;
- a larger runtime/harness/tool-authority system can potentially establish operational AgentRole/AgencyStanding if source, ownership, evaluative and delegation relations are grounded;
- model intelligence alone is neither necessary nor sufficient for agency.

PASS as cross-domain boundary test; no engineering prescription follows.

## HC-G — Bacterium / minimal organism

- non-arbitrary biological individuality;
- self-maintenance/viability norm candidates;
- adaptive regulation of environment coupling;
- strong candidate for minimal biological AgencyStanding under Barandiaran/Di Paolo style accounts.

PASS; prevents MF8 from requiring language, planning or reflective intention.

## HC-H — Human reflex / involuntary movement

- bearer has broad agency standing;
- not every bearer movement is therefore an action with ownership;
- individual event ownership must be separately established.

PASS; proves `Agent bearer ≠ every bearer event is Action`.

## HC-I — Swarm/flock

- coupling/coordination/collective pattern: yes;
- collective agency: not automatic.

PASS.

## HC-J — Corporation/committee

- arbitrary aggregation insufficient;
- organized collective decision/action mechanisms can support a genuine collective-agency candidate.

PASS; requires MF4/MF7 collective bearer standing plus MF8 collective source/ownership.

---

# 19. Provisional AgencyClaim v0

```text
AgencyClaim = <
  Bearer,
  Boundary/Scale,
  AgentRoleStanding?,
  AgentialSourceClaim,
  ActionDomain/Repertoire,
  ActionProduction/Control Route,
  EvaluativeOrientationClaim,
  Evaluative Provenance,
  ActionOwnership Claim,
  Autonomy Profile,
  Temporal Persistence/Continuation,
  Delegation/Authority Context?,
  StandingRoute,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### A8-047
Bare claims such as `X is agentic` are under-specified unless they identify bearer, standing route, action/source relation, evaluative provenance and scope.

---

# 20. Provisional non-collapse stack

```text
AgentRoleStanding ≠ AgencyStanding
Agent ≠ Agency
Agent ≠ Controller
Agency ≠ Control
Agency ≠ Intelligence
Agency ≠ Consciousness
Agency ≠ Autonomy
Agency ≠ Learning
Agency ≠ Adaptation
Agency ≠ SenseOfAgency
```

```text
Behavior ≠ Action
Transition ≠ Action
ControlOccurrence ≠ Action
ActionAttempt ≠ Effect
Cause ≠ ActionOwnership
```

```text
Goal ≠ Attractor
Goal ≠ Setpoint
Goal ≠ Reward
Goal ≠ Utility
Goal ≠ Preference
```

```text
Choice ≠ FreeWill
Choice ≠ Decision
Decision ≠ Policy
Policy ≠ Intent
Plan ≠ Policy
```

```text
SelfOrganization ≠ Agency
Coordination ≠ CollectiveAgency
SharedGoal ≠ CollectiveAgency
CollectiveBehavior ≠ CollectiveAction
```

```text
AgencyStanding
 ≠ FeelingOfAgency
 ≠ JudgementOfAgency
 ≠ RepresentedAgency
```

---

# 21. FoundationReopen audit

No current result forces revision of MF0–MF7.

Especially:

- MF4 provides the non-arbitrary bearer/collective organization substrate;
- MF7 ConfigurationStanding remains unchanged;
- MF7 EvolutionStanding remains unchanged;
- MF7 ControlStanding remains neutral and agency-free;
- MF7 command/actuation/effect separation becomes useful for ActionOwnership;
- MF7 ContinuationStanding supplies agent persistence/identity without defining agency;
- MF2/MF3 remain necessary to separate perceived/represented agency from target agency.

### A8-048
**FRC-A1 is NOT triggered.**

Potential future trigger remains:

> if MF8-B→I discovers a genuine action/agency case that cannot be expressed without changing the constitutive definitions of State, Dynamics or Control rather than adding typed agency relations.

No such case has appeared in MF8-A.

---

# 22. Evidence anchors

Primary/theory anchors used in this round:

1. Michael Wooldridge & Nicholas Jennings (1995), **Intelligent Agents: Theory and Practice**, *Knowledge Engineering Review* 10(2), DOI `10.1017/S0269888900008122` — operational software-agent properties; explicitly shows a weak engineering notion of agency.
2. Stan Franklin & Art Graesser (1996), **Is it an Agent, or just a Program? A Taxonomy for Autonomous Agents** — software-agent taxonomy and temporally extended situated action framing.
3. Xabier E. Barandiaran, Ezequiel Di Paolo & Marieke Rohde (2009), **Defining Agency: Individuality, Normativity, Asymmetry, and Spatio-temporality in Action**, *Adaptive Behavior* 17(5), DOI `10.1177/1059712309343819` — individuality, interactional asymmetry and normativity as genuine-agency requirements.
4. Ezequiel A. Di Paolo (2005), **Autopoiesis, Adaptivity, Teleology, Agency**, *Phenomenology and the Cognitive Sciences* 4(4), DOI `10.1007/s11097-005-9002-y` — adaptivity/viability and intrinsic teleology; self-organization alone is not sufficient for sense-making.
5. Donald Davidson (1963), **Actions, Reasons, and Causes**, *The Journal of Philosophy* 60(23), DOI `10.2307/2023177` — reason/action causal-rationalization account used as a richer reflective-action case, not as minimal agency ontology.
6. Matthis Synofzik, Gottfried Vosgerau & Albert Newen (2008), **Beyond the Comparator Model: A Multifactorial Two-Step Account of Agency**, *Consciousness and Cognition* 17(1), DOI `10.1016/j.concog.2007.03.010` — feeling of agency versus judgement of agency.
7. Christian List & Philip Pettit (2011), **Group Agency: The Possibility, Design, and Status of Corporate Agents**, Oxford University Press, DOI `10.1093/acprof:oso/9780199591565.001.0001` — collective agent as organization-dependent rather than arbitrary aggregate.
8. Alvaro Moreno & Matteo Mossio (2015), **Biological Autonomy: A Philosophical and Theoretical Enquiry**, Springer, DOI `10.1007/978-94-017-9837-2` — biological autonomy as self-producing/self-maintaining organized systems with endogenous norms/goals; treated as one standing route, not universal software-agent definition.

Theories remain competing where they propose different minimal thresholds. MF8-A uses them to define typed separations rather than silently declaring one tradition universally correct.

---

# 23. MF8-A verdict

MF8-A's deepest reconstruction is:

```text
AGENT is not one boolean natural kind.

AgentRoleStanding
  = role/bearer standing inside a formal, computational,
    delegated or institutional interaction schema.

AgencyStanding (candidate)
  = organized bearer
  + agential source relation
  + evaluative orientation with provenance
  + action-production repertoire/route
  + action ownership
  + standing route/scope.

Autonomy / intention / planning / learning / reflection /
responsibility / collective unification
  = stronger or orthogonal profiles, not synonyms for agency.
```

The practical consequence for the remaining foundations is not engineering advice but an ontology discipline:

> **Do not ask only whether something `is an agent`. Ask: what is the bearer, which agent/agency standing is claimed, what makes it an action source rather than a controller/actuator, where do its evaluative criteria come from, what owns the action, how autonomous is each governance layer, and at what scale/scope does the claim hold?**

This prevents thermostats, RL interfaces, organisms, humans, corporations and tool-using AI systems from being either flattened into one category or arbitrarily separated by anthropomorphic criteria.

---

# 24. Next frontier

Proceed to:

```text
MF8-B — Action, Behavior & Action Ownership
```

Primary questions:

1. What turns a bearer-linked process/behavior into an **ActionStanding**?
2. Can action be defined without circularly presupposing full AgencyStanding?
3. How do action source, authorship, ownership, attempt, command, actuation and effect differ?
4. How should reflex, compulsion, habit, automatic skill, remote control, coercion, delegated action and failed action be classified?
5. What counterfactual/source tests distinguish an action owner from a causal conduit or effector?

MF0–MF7 remain frozen unless a concrete FoundationReopenCondition is demonstrated.
