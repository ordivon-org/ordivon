# Ordivon Media Foundations — MF8-E Autonomy, Initiative, Intentionality, World Model & Self Model

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 52 at start  
**Input:** MF0–MF7 frozen; MF8-A/B/C/D complete/provisional.  
**Status:** **MF8-E COMPLETE / PROVISIONAL AUTONOMY-INTENT-MODEL ONTOLOGY. MF8 Agency Foundations are not frozen yet.**  
**Next:** MF8-F — Learning, Adaptation, Development & Plasticity.

---

# 0. Purpose

MF8-A already warned that `Autonomy ≠ Agency`, and MF8-D made delegation, decision authority and policy adoption explicit. MF8-E now reconstructs five heavily overloaded families:

```text
Autonomy
Initiative / Proactivity
Intentionality / Intention
World Model
Self Model
```

The main danger is modern `agentic` vocabulary collapsing all of these into one scalar notion of `more autonomous`.

This round asks:

1. Autonomous with respect to **what domain, whose intervention, and which kind of governance**?
2. Does dependency on resources/environment reduce autonomy by itself?
3. What makes initiative more than timer/event-triggered execution?
4. Is proactivity just non-reactivity?
5. What separates semantic/representational aboutness from practical intention-to-act?
6. What makes an intention more than a goal, choice or decision?
7. Does agency require an internal world model?
8. What exactly must a representation model to count as a world model?
9. What makes a model a **self** model rather than an analyst's model of the bearer?
10. Do self-model, self-awareness, metacognition and sense of agency coincide?

---

# 1. Frozen substrate consumed, not reopened

MF8-E preserves:

```text
Agent ≠ Controller
Agency ≠ Control
Agency ≠ Autonomy
Policy ≠ Intent
Goal ≠ Intention
Decision ≠ Intention
Commitment ≠ Intention
Representation ≠ World
Model ≠ World Copy
AgentRoleStanding ≠ AgencyStanding
AgencyStanding ≠ SenseOfAgency
```

MF3 already provides `RepStanding` / `RepActive`; MF7 provides bearer identity/persistence/control; MF8-B/C/D provide source, action, evaluation, choice, decision, commitment, policy and plan.

### E8-001
**No MF0–MF7 FoundationReopenCondition is triggered at MF8-E entry.**

---

# 2. Autonomy is not independence

A bearer can depend strongly on an environment while retaining substantial practical autonomy.

Examples:

```text
organism depends on oxygen / nutrients
human depends on social infrastructure
software depends on hardware / electricity / network
institution depends on members / law / resources
```

These dependencies are not automatically governance relations.

MF8-E therefore separates:

```text
Existential / Resource Dependence
Causal Dependence
Informational Dependence
Capability Dependence
Authority Dependence
Governance Dependence
Constitutive Dependence
Social Dependence
```

### E8-002
**Dependence ≠ low autonomy by identity.**

### E8-003
**Autonomy ≠ isolation.** Interaction, dependence and cooperation can coexist with autonomy.

### E8-004
The relevant autonomy question is usually not `does B depend on anything?` but `which bearer/organization governs domain D, and which external interventions/permissions are required to set, revise, veto, authorize or trigger it?`

---

# 3. GovernanceStanding and DependenceStanding

Provisional primitives:

```text
GovernanceStanding(G, B, D | Σ)
```

holds when mechanism/role/organization G has grounded standing for bearer/system B as setting, revising, constraining, vetoing, authorizing, triggering or maintaining practical domain D.

And:

```text
DependenceStanding(B, X, D | Σ)
```

holds when B's operation in domain D materially requires external condition/actor/resource X under the declared horizon and boundary.

### E8-005
Governance and dependence must be represented separately.

A system can be:

```text
resource-dependent
but decision-autonomous
```

or:

```text
resource-independent locally
but policy-governed externally.
```

---

# 4. AutonomyProfile, not `Autonomy = scalar`

MF8-E defines autonomy as a **typed governance/dependence profile**.

```text
AutonomyProfile(B | Σ) = <
  ActionSelectionAutonomy,
  DecisionAutonomy,
  PolicyAutonomy,
  GoalAutonomy,
  Evaluative/NormAutonomy,
  Agenda/InitiativeAutonomy,
  InformationAcquisitionAutonomy,
  ResourceAutonomy,
  AuthorityAutonomy,
  Boundary/ConstitutiveAutonomy,
  TemporalContinuationAutonomy,
  SelfRevisionAutonomy?,
  ExternalOverride/Veto Structure,
  Escalation Requirements,
  Dependence Profile,
  Scope / Horizon / Provenance
>
```

### E8-006
**Autonomy is multidimensional and domain-relative.**

### E8-007
A single global `autonomy level` can be useful as an engineering summary only if its aggregation rule and underlying dimensions remain recoverable; it is not a foundation primitive.

---

# 5. Autonomy dimensions

## 5.1 Action-selection autonomy

Who governs immediate action choice inside an already-given domain?

```text
Externally commanded every action
< delegated local action selection
< locally governed broad action selection
```

## 5.2 Decision autonomy

Can B settle practical questions within domain D without contemporaneous external approval?

## 5.3 Policy autonomy

Can B select, modify, replace or suspend the policy that governs future choices?

## 5.4 Goal autonomy

Can B generate, adopt, reject, revise or prioritize goals rather than merely receive fixed goals?

## 5.5 Evaluative / norm autonomy

Where do criteria of better/worse, acceptable/unacceptable, permitted/forbidden come from, and can B revise them?

## 5.6 Agenda / initiative autonomy

Who determines what practical issue becomes active and when?

## 5.7 Information-acquisition autonomy

Can B actively decide what to sense/query/search/inspect, rather than receive only preselected inputs?

## 5.8 Resource autonomy

Can B obtain, allocate, reserve or release relevant resources within scope?

## 5.9 Authority autonomy

Can B act/decide without requesting permission or escalation, within the declared authority domain?

## 5.10 Boundary / constitutive autonomy

Does the bearer participate in generating/maintaining its own organization/identity conditions, rather than merely being externally assembled and maintained?

## 5.11 Temporal continuation autonomy

Can B sustain goal/action organization across time without continuous external prompting or reinitialization?

## 5.12 Self-revision autonomy

Can B alter relevant internal policy/model/decision structures? Full learning/plasticity ontology is deferred to MF8-F.

### E8-008
No one autonomy dimension implies all others.

---

# 6. Software-agent autonomy versus constitutive autonomy

Wooldridge & Jennings' classic weak notion treats autonomy operationally: agents operate without direct human/other intervention and have some control over actions/internal state; they separately identify reactivity and pro-activeness. This is a legitimate **operational/software autonomy route**.

Biological/enactive traditions such as Di Paolo & Iizuka and Barandiaran/Di Paolo/Rohde use a stronger **constitutive/organizational autonomy route** tied to self-sustaining identity, normativity and adaptive regulation.

MF8-E refuses to collapse them:

```text
Operational AutonomyStanding
≠ Constitutive AutonomyStanding
```

### E8-009
A software system can have high operational autonomy without constituting its own viability/norms.

### E8-010
A living system can have strong constitutive autonomy while remaining heavily dependent on environmental resources.

### E8-011
Claims of `autonomous agent` must declare standing route and domain.

---

# 7. Delegated autonomy is not fake autonomy

Suppose a principal assigns:

```text
Goal: keep service latency below threshold
Norm: never modify customer records
Authority: may restart services and scale resources
```

The delegated agent may have:

```text
Action Autonomy       high
Decision Autonomy     high within domain
Policy Autonomy       moderate
Goal Autonomy         low
Norm Autonomy         low
Resource Autonomy     bounded
Authority Autonomy    bounded
```

### E8-012
**Externally assigned goals do not imply zero action/decision autonomy.**

### E8-013
**High action autonomy does not imply goal or norm autonomy.**

### E8-014
Delegation is therefore best represented as a boundary on the autonomy vector, not a binary `autonomous/non-autonomous` switch.

---

# 8. Initiative requires a trigger ontology

`It started by itself` is too weak.

MF8-E distinguishes:

```text
ExternalCommandTrigger
ExternalEventTrigger
ScheduledTrigger
InternalStateTrigger
Goal/CommitmentMonitoringTrigger
NormViolationTrigger
OpportunityDetectionTrigger
SelfGeneratedAgendaTrigger
```

A timer can cause execution without establishing rich initiative.

A sensor event can trigger action while the bearer still has substantial initiative in what goal/response it activates.

### E8-015
**Trigger source ≠ agenda source ≠ goal source.**

---

# 9. ActivationStanding versus InitiativeStanding

Neutral primitive:

```text
ActivationStanding(e, B | T, Σ)
```

when trigger/process T starts, resumes or escalates practical process e for B.

Stronger:

```text
InitiativeStanding(e, B | Σ)
 = ActivationStanding
 + Bearer-relative AgentialSourceStanding
 + Persistent Goal/Norm/Commitment relevance
 + Agenda/Timing governance attributable to B
 + no requirement for a contemporaneous external directive that specifies this episode
 + scope/provenance
```

### E8-016
**Activation ≠ Initiative.**

### E8-017
A cron job has scheduled activation; that alone does not establish initiative.

### E8-018
A delegated agent can show genuine operational initiative by monitoring conditions and activating appropriate goal-directed work without a new human command, even if the higher-level goal was externally assigned.

---

# 10. Initiative itself is multidimensional

Provisional profile:

```text
InitiativeProfile = <
  TriggerAutonomy,
  AgendaGeneration,
  GoalInitiation,
  TimingInitiation,
  OptionGeneration,
  InformationSeekingInitiation,
  MeansInitiation,
  EscalationInitiation,
  SelfRepairInitiation,
  PersistenceWithoutPrompt,
  Provenance / Scope
>
```

### E8-019
A system can have timing initiative without goal initiative.

### E8-020
A system can have means initiative under delegated goals.

### E8-021
A system can generate new subgoals without possessing authority to revise terminal goals.

---

# 11. Reactivity and initiative are not opposites

Wooldridge & Jennings distinguish reactivity from pro-activeness, but a concrete bearer may exhibit both.

A perceived event can:

```text
trigger monitoring
→ activate a standing commitment
→ generate alternatives
→ initiate a multi-step response
```

This is causally event-triggered yet can still involve substantial initiative in agenda/means/decision organization.

### E8-022
**Reactive trigger ≠ purely reactive practical organization.**

### E8-023
**Initiative ≠ absence of environmental causation.**

### E8-024
Bearer-level `reactive` and `proactive` should be treated as behavioral/practical profiles rather than mutually exclusive natural kinds.

---

# 12. ProactivityStanding

Provisional:

```text
ProactivityStanding(e, B | G, H, Σ)
```

holds when B initiates or maintains action/decision/information-seeking in service of goal/commitment G with respect to anticipated, temporally extended or not-yet-immediate conditions over horizon H, rather than only emitting a direct response to a currently imposed command or perturbation.

### E8-025
Proactivity normally implies some initiative profile but does not require goal autonomy.

### E8-026
Proactivity does not universally require an explicit predictive WorldModelStanding; learned cue-policy structure, schedules or standing commitments can support anticipatory behavior with weak/no explicit world model.

### E8-027
A scheduled preventive task can have weak formal proactivity but low agenda/timing autonomy if its entire activation structure was externally fixed.

---

# 13. Intentionality is overloaded before intention begins

MF8-E separates:

```text
Intentionality_aboutness
Practical IntentionStanding
IntentionalActionStanding
Goal/Purpose Standing
Experienced Intention / Agency
```

The first belongs primarily to MF3 representation/content.

Provisional mapping:

```text
AboutnessStanding(V, Θ | Σ)
```

holds when representational/content standing V is directed toward or stands for target/content domain Θ under a grounded semantic route.

### E8-028
**Intentionality_aboutness ≠ IntentionToAct.**

### E8-029
A map/model/sentence can be about Paris without intending to go to Paris.

### E8-030
An agent can intend to act without representing every semantic object implicated by the action explicitly.

MF3 remains frozen.

---

# 14. Intentional stance ≠ target intentional state

Wooldridge & Jennings review the intentional-system tradition in which beliefs/desires/intents can be useful explanatory abstractions for complex systems. They also note that even simple systems can sometimes receive coherent intentional descriptions.

MF8-E therefore preserves:

```text
IntentionalStanceAscription
≠ Grounded Target IntentionalStateStanding
```

### E8-031
A useful belief/desire/intention vocabulary can be an analyst/explanatory model without proving that the target has corresponding constitutive internal standings.

### E8-032
Conversely, formal BDI/intention structures can have genuine formal/operational standing even when psychological/conscious interpretation is unwarranted.

---

# 15. IntentionStanding — practical commitment, not desire

MF8-D gave us DecisionStanding, CommitmentStanding and PlanStanding. MF8-E can now define:

```text
IntentionStanding(I, B, A | Σ)
 = Action/Practical Target A
 + Adopted Decision/Commitment Standing
 + Future-or-ongoing Practical Guidance
 + Means/Plan/Policy coordination pressure as applicable
 + Persistence across time
 + Reconsideration/Drop Conditions
 + Attribution to B
 + Standing Route / Scope
```

An intention is thus a bearer-relative practical commitment toward doing, maintaining, refraining from, or bringing about some action-relevant target, where the commitment organizes subsequent practical reasoning/action until fulfilled, failed, revised or dropped under appropriate conditions.

### E8-033
**Intention ≠ Desire/Want.** A bearer may intend what it does not currently want.

### E8-034
**Intention ≠ Goal.** Goals can exist without adoption as one's practical commitment; intentions normally bind the bearer toward action/realization.

### E8-035
**Intention ≠ Decision.** A decision can settle classification/authorization/delegation without forming an intention to personally act.

### E8-036
**Intention ≠ Commitment universally.** Commitments can be institutional/legal/non-actional; intention is action/practical-target directed.

### E8-037
**Intention ≠ Plan.** An intention can exist with only a partial or absent explicit plan; a plan proposal can exist without being intended/adopted.

Bratman's planning theory treats intentions as elements of partial plans that organize practical reasoning over time; Cohen & Levesque formalize intention through choice plus commitment and explicit conditions under which goals may be dropped. MF8-E preserves these as strong intention routes rather than universal identity claims.

---

# 16. Prior intention versus intention-in-action

A bearer need not form a long-lived explicit prior intention before every intentional action.

MF8-E therefore distinguishes:

```text
PriorIntentionStanding
  temporally persistent intention formed before action initiation

CurrentActionIntentionStanding
  action-guiding practical commitment operative during initiation/execution
```

### E8-038
**IntentionalActionStanding does not universally require a long-lived prior intention token.**

### E8-039
Habitual/skill execution can be embedded within a higher-level intention while low-level motor corrections lack separately represented intentions.

This preserves MF8-B's action hierarchy.

---

# 17. IntentionalActionStanding

Provisional profile:

```text
IntentionalActionStanding(A, B | I, Σ)
 = AgentialActionStanding(A,B)
 + relevant IntentionStanding I
 + guidance/fit relation between I and A
 + declared granularity
```

### E8-040
**IntentionalAction ≠ all Action.**

### E8-041
**Foreseen side effect ≠ Intended effect by identity.** A consequence can be predicted and knowingly tolerated without being the practical target of intention.

This is one reason intention must not collapse into prediction/world model content.

---

# 18. WorldModelStanding — broad core

`World model` is also overloaded. MF8-E first defines a broad representational standing:

```text
WorldModelStanding(M, B | W, Σ)
```

holds when model/representation M has grounded standing for bearer/system B as representing some action/perception-relevant structure of external/environmental domain W—entities, relations, states, regularities, affordances, causal/transition structure, uncertainty, or other world-relevant organization—under an explicit standing route.

This is a specialization of MF3 Model/Representation standing.

### E8-042
**WorldModelStanding ≠ World.**

### E8-043
**WorldModelStanding ≠ complete world copy.** It can be partial, task-relative, lossy and uncertain.

### E8-044
**WorldModelStanding does not require consciousness or language.**

---

# 19. World-model profiles

A world model may emphasize different contents:

```text
Static Structural Model
Spatial Map
Object/Entity Model
Relational Model
Transition/Dynamics Model
Causal Model
Action-Conditional Consequence Model
Affordance Model
Other-Agent Model
Institutional/Social Model
Uncertainty Model
Generative Predictive Model
```

MF8-E distinguishes:

```text
WorldModelStanding
WorldModelRepresentation
WorldModelEstimate
WorldModelActiveUse
```

### E8-045
A stored/grounded model can have WorldModelStanding even while not currently used.

### E8-046
Active planning/simulation/prediction using it is a richer `WorldModelActiveUse` profile.

---

# 20. Predictor ≠ WorldModel automatically

A predictor can forecast token sequences, sensor values or labels without grounded world-content standing.

Conversely, a learned transition model can qualify as a narrow world model when its represented variables have grounded environment/state/action-consequence standing.

### E8-047
**Prediction ability ≠ WorldModelStanding.**

### E8-048
**WorldModelStanding ≠ explicit symbolic ontology.** Latent models can qualify if their representational/target standing is independently grounded.

### E8-049
**Latent decodability alone remains insufficient**, by MF3.

---

# 21. Model-based and model-free are formal/operational routes

Sutton's Dyna work explicitly separates acting through learned policy/value structures from planning using a learned model of world transitions/rewards; later model-based/model-free literature similarly distinguishes flexible model-based control from computationally cheaper learned action-value/habit-like control.

MF8-E therefore uses:

```text
FormalModelBasedStanding
FormalModelFreeStanding
```

but preserves:

### E8-050
**Model-free ≠ representation-free by identity.** It means no explicit environment transition/reward model is used in the relevant formal planning sense, not that the system contains no representational structure whatsoever.

### E8-051
**Model-based ≠ generally intelligent/agentic by identity.** A predictor/controller can contain a world model without rich agency.

---

# 22. Minimal agency does not require an explicit world model

This is a major falsification question.

Evidence/theory cuts against making explicit world-model possession constitutive:

- Brooks' `Intelligence without Representation` demonstrates a serious architectural program for competent situated behavior without a centralized representational world model.
- Barandiaran/Di Paolo/Rohde's E. coli discussion explicitly notes that spatial structure evident to an observer need not be accessible to the bacterium as spatial representation.
- model-free/habit-like action control can support selection without online world-model planning.

### E8-052
**Explicit WorldModelStanding is NOT a universal constituent of minimal AgencyStanding.**

### E8-053
Minimal agency still requires world-sensitive coupling/discrimination sufficient for source/guidance/action, but `world-sensitive organization` must not be renamed `world model` without MF3 representation standing.

### E8-054
World modeling is instead a major **agency richness/capability profile**, especially for counterfactual planning, flexible replanning, prediction and long-horizon reasoning.

---

# 23. World model locus: internal, external, shared

`Internal world model` is only one profile.

Distinguish:

```text
Internal Model
Externally Stored but Operationally Recruited Model
Shared/Institutional Model
Tool-Accessible Model
Analyst Model of the Bearer/Environment
```

### E8-055
A model need not be spatially inside a physical body to participate in a larger agent/system's active practical organization, but the integration/authority/recruitment route must be declared.

### E8-056
Analyst-accessible environmental data does not become the bearer's world model merely because the analyst can use it to predict the bearer.

---

# 24. SelfModelStanding

A self model is not the self/bearer.

Provisional:

```text
SelfModelStanding(M_s, B | S, Σ)
```

holds when representation/model M_s has grounded standing **for B's own practical/perceptual/cognitive organization** as representing some aspect of bearer B-as-target—its body, boundary, state, capabilities, morphology, dynamics, policies, goals, knowledge limits, action effects, identity or social role—under a declared self-model route S.

### E8-057
**BearerIdentityStanding ≠ SelfModelStanding.**

### E8-058
**SelfStateStanding ≠ SelfModelStanding.** Merely having internal state does not mean representing oneself.

### E8-059
**ExternalModelOf(B) ≠ B's SelfModelStanding** unless the model is operationally recruited into B's own organization under the relevant standing route.

---

# 25. Self-model profiles

Possible typed profiles include:

```text
Body / Morphology Model
Kinematic/Dynamic Self Model
Capability Model
Resource/Safety Model
Policy/Behavior Model
Goal/Commitment Model
Epistemic/Knowledge-Limit Model
Agency/Authorship Model
Identity/Continuity Model
Social/Role Self Model
Narrative/Reflective Self Model
Phenomenal Self Model
```

### E8-060
No one self-model profile implies all others.

### E8-061
A robot can possess a body-dynamics self model without possessing a narrative, phenomenal or moral self-concept.

---

# 26. Self-modeling has concrete non-conscious cases

Bongard, Zykov & Lipson (2006) demonstrated robots that infer/update models of their own morphology and use those models to generate compensatory behavior after damage. Later robot self-modeling work explicitly uses predictive models of the robot's own dynamics/morphology for planning and adaptation.

This establishes a clear non-human standing route:

```text
SelfModelStanding
without
PhenomenalSelf / ConsciousSelfAwareness
```

### E8-062
**SelfModel ≠ SelfAwareness.**

### E8-063
**SelfModel ≠ Consciousness.**

### E8-064
**SelfModel ≠ SenseOfAgency.** A system can model its body/capabilities without having an experience/judgement of authorship.

---

# 27. Self-model correctness is separate from standing

A self model can be wrong, stale or incomplete.

```text
SelfModelStanding
≠ SelfModelAccuracy
```

### E8-065
A mistaken self-model remains a self model if it has the appropriate grounded representational/use standing.

### E8-066
Damage/adaptation cases are especially useful because model mismatch and model update can be independently tested against the bearer.

---

# 28. `I` tokens and self-reference do not prove SelfModelStanding

A linguistic system can emit first-person pronouns because of discourse convention or training distribution.

```text
FirstPersonToken
≠ SelfReferenceStanding automatically
≠ SelfModelStanding
≠ SelfAwareness
```

### E8-067
Self-reference claims require grounding: what bearer does the token refer to, what properties are represented, how is the representation updated, and how does it guide bearer-relative reasoning/action?

### E8-068
A system can also have a functional body/capability self model without ever producing the word `I`.

---

# 29. World model and self model can overlap

A self model may be embedded in a world model:

```text
WorldModel
  contains
    EnvironmentModel
    SelfModel
    OtherAgentModels
```

But this decomposition is not universal.

### E8-069
**SelfModel ≠ WorldModel by identity.**

### E8-070
WorldModel can exist with no explicit self-representation.

### E8-071
SelfModel can be narrow (e.g. body dynamics) without a broad model of the environment.

---

# 30. Self/world distinction can exist without self model

A system may have a physical/organizational boundary and differential sensorimotor coupling between `inside` and `outside` without representing that boundary as a self/world distinction.

### E8-072
**BearerBoundaryStanding ≠ represented self/world boundary.**

### E8-073
Minimal agency therefore does not require an explicit SelfModelStanding merely because agency requires an individuated bearer.

This prevents MF4/MF7 identity from being silently promoted into MF3 representation.


# 31. World/Self model active-use profiles

Models matter to agency differently depending on how they are recruited.

MF8-E distinguishes:

```text
RepresentedOnly
StateEstimationUse
PredictionUse
CounterfactualSimulationUse
PlanningUse
ControlUse
ExplanationUse
CommunicationUse
SelfDiagnosisUse
ReconsiderationUse
```

### E8-074
Possessing a model is not the same as using it for choice/planning.

### E8-075
Using a model for one domain does not imply broad model-based agency elsewhere.

### E8-076
Model richness and model use should therefore be recorded separately.

---

# 32. Internal simulation and counterfactual action

Sutton's Dyna architecture and modern `world model` work illustrate one powerful use route:

```text
WorldModel
 + candidate actions
→ internally generated possible consequences
→ evaluation / planning
→ policy/action revision
```

Ha & Schmidhuber's `World Models` provides a clear engineered case where a compressed generative environment model can support policy learning within internally generated trajectories.

### E8-077
**Internal simulation is a strong WorldModelActiveUse profile but not the definition of all WorldModelStanding.**

### E8-078
Counterfactual planning does not require the model to be complete or perfectly accurate.

### E8-079
`Hallucinated/dreamed trajectory` remains model-generated representation, not actual world history; MF3/MF6 remain active.

---

# 33. Model uncertainty and epistemic separation

A serious world/self model claim needs:

```text
Model Content
Model Confidence / Uncertainty
Observed Evidence
Prediction/Simulation Output
Actual Outcome
Model Error
Update Provenance
```

separated.

### E8-080
**Model prediction ≠ observed future.**

### E8-081
**Self-model prediction ≠ actual capability.**

### E8-082
A system can choose based on a false world/self model; the resulting action may remain genuinely intentional/agentic while being mistaken.

---

# 34. World model does not imply intention

A weather simulator, digital twin or physics predictor can have rich WorldModelStanding while having no practical IntentionStanding.

Conversely, a simple agent may intend to approach/avoid something using a highly compressed reactive policy with no explicit world model.

### E8-083
**WorldModel ≠ Intention.**

### E8-084
**Prediction ≠ Goal ≠ Intention.**

### E8-085
Knowing/representing what will probably happen does not mean intending that outcome.

This also preserves the distinction between intended consequences and merely foreseen side effects.

---

# 35. Self model does not imply autonomy

A system can accurately model its own body, capabilities or failure probabilities while remaining externally commanded in every action.

### E8-086
**SelfModelStanding ≠ ActionAutonomy.**

### E8-087
**SelfModelStanding ≠ GoalAutonomy.**

### E8-088
Self-modeling can increase capability for autonomous operation, diagnosis or adaptation, but that is an empirical/architectural relation, not an ontological identity.

---

# 36. Autonomy can exist without explicit self model

Operational autonomy only requires the relevant practical governance standing, not necessarily an explicit model of `my autonomy` or `myself`.

Similarly, constitutive biological autonomy can be grounded in organizational self-maintenance without a symbolic self-representation.

### E8-089
**AutonomyStanding ≠ SelfModelStanding.**

### E8-090
A self-maintaining bearer does not thereby represent itself as self-maintaining.

---

# 37. Initiative can exist without explicit world model

Consider:

```text
standing commitment: periodically inspect nest / cache / queue
learned cue: if early warning signal appears, begin preventive action
```

These can support anticipatory or initiative-rich behavior without explicit counterfactual simulation.

### E8-091
**Initiative/Proactivity ≠ WorldModel by identity.**

### E8-092
Rich model-based anticipation is one stronger proactivity route, not the minimal definition.

---

# 38. Initiative can exist under external goals

This is a decisive delegated-agent case.

```text
Principal sets goal G
Delegate continuously monitors environment
Delegate notices opportunity/risk
Delegate generates subgoal/options
Delegate initiates action without new command
```

The system can have:

```text
GoalAutonomy             low
Agenda/InitiativeAutonomy high
MeansAutonomy            high
DecisionAutonomy         high within domain
```

### E8-093
**Initiative ≠ GoalAutonomy.**

### E8-094
**Externally assigned goals can support internally initiated delegated action.**

---

# 39. Initiative versus timer hard boundary

Case A:

```text
cron: every 10 min run script X
```

Case B:

```text
agent: maintain objective G;
monitor multiple signals;
when risk/opportunity evidence crosses a context-sensitive criterion,
construct response options and activate one.
```

Both avoid contemporaneous human intervention, but their profiles differ sharply.

Case A may have:

```text
ScheduledActivation yes
Timing predetermined externally
Agenda predetermined externally
Goal generation none
Option generation minimal/none
```

Case B may have:

```text
MonitoringTrigger yes
Agenda activation bearer-governed
Option generation bearer-governed
Means selection bearer-governed
```

### E8-095
**`Runs without a human click` is insufficient evidence of InitiativeStanding.**

---

# 40. Self-triggering is also too weak

A system can contain an internal oscillator that triggers behavior. That is endogenous causal origin but may have no evaluative/action-source standing.

### E8-096
**EndogenousTrigger ≠ Initiative.**

### E8-097
MF8-C's intrinsic/endogenous distinction applies directly: internal causal origin must not be promoted to self-generated practical purpose.

---

# 41. Intention provenance

Intentions can arise through different routes:

```text
Self-generated practical intention
Adopted external request
Delegated role commitment
Institutional intention role
Learned/habit-supported intention
Formal BDI IntentionRoleStanding
Observer-attributed intention
```

### E8-098
An externally proposed action can become B's genuine IntentionStanding if B's decision/commitment organization adopts it.

### E8-099
**External origin ≠ no intention** after valid adoption.

### E8-100
But merely receiving an instruction does not establish intention if the bearer neither adopts nor is constituted by a role that gives the instruction practical commitment standing.

---

# 42. Formal BDI intention versus target psychological intention

Artificial-agent logics legitimately define formal beliefs, desires/goals and intentions. Cohen & Levesque provide one classic formalization; Wooldridge & Jennings survey this family.

MF8-E preserves:

```text
FormalIntentionRoleStanding
OperationalIntentionStanding
PsychologicalIntentionStanding
Phenomenal/ExperiencedIntention
```

### E8-101
Formal/operational intention can be real at its standing route without implying phenomenal consciousness.

### E8-102
Psychological/phenomenal intention cannot be inferred merely from a variable named `intention`.

---

# 43. World-model evidence battery

A claim that B possesses WorldModelStanding should be attacked through:

## W1 — Target grounding
What environmental/world domain does model content stand for?

## W2 — Structural sensitivity
Do model states/relations change systematically with relevant target-world distinctions?

## W3 — Intervention/prediction
Does changing candidate action/world condition alter model predictions in target-relevant ways?

## W4 — Counterfactual use
Can the representation support consequences for states/actions not currently occurring?

## W5 — Transfer/replanning
Does updated model information alter planning/choice flexibly without relearning every action from scratch?

## W6 — Representation firewall
Could observed performance be explained by cached policy, interpolation or analyst decodability without target model standing?

## W7 — Error/update
Can prediction error relative to observations be identified separately from model output and update the model through a grounded route?

### E8-103
No one test is universally necessary/sufficient for every world-model route, but together they discipline the claim.

---

# 44. Self-model evidence battery

## S1 — Self target
Does represented content refer to B itself rather than merely the environment?

## S2 — Counterfactual self intervention
Do predicted consequences vary with candidate changes to B's own morphology/state/capability/action?

## S3 — Damage/capability mismatch
Can the model detect or adapt to discrepancy between expected and actual self dynamics?

## S4 — Self-specific practical use
Does self-model content change B's planning/control/resource allocation/diagnosis?

## S5 — External-model firewall
Is the representation operationally recruited by B, rather than existing only in the analyst's model?

## S6 — Linguistic firewall
Can self-model standing be demonstrated independently of first-person language/report?

### E8-104
Robot morphology/self-dynamics experiments provide especially strong S2–S4 evidence routes.

---

# 45. Hard-case audit

## HC-E1 — Rock depends on gravity/environment
Dependence exists; no practical governance/autonomy follows. **PASS:** dependence/autonomy distinction.

## HC-E2 — Thermostat
Operational control can run without human intervention and therefore has a weak engineering autonomy description; goal/norm autonomy and constitutive autonomy remain unestablished. **PASS.**

## HC-E3 — Cron job
ScheduledActivation yes; initiative not established merely by autonomous timing. **PASS.**

## HC-E4 — Event-driven script
ExternalEventTrigger plus deterministic response; may have operational reactivity but low agenda/option initiative. **PASS.**

## HC-E5 — Delegated monitoring agent
Externally assigned goal but bearer-governed monitoring, option generation and bounded decision/action initiation. **PASS:** high initiative/action autonomy can coexist with low goal autonomy.

## HC-E6 — Bacterium chemotaxis
Strong minimal biological agency candidate under prior rounds; explicit spatial WorldModelStanding not required and observer-visible gradient geometry need not be represented by the bacterium. **PASS.**

## HC-E7 — Brooks-style reactive robot
Competent situated behavior without centralized representational world model attacks world-model necessity. **PASS without claiming all representation is absent in every interpretation.**

## HC-E8 — Dyna/model-based agent
Learned transition/reward model actively used for planning. Strong formal WorldModelStanding/ActiveUse. **PASS.**

## HC-E9 — Model-free RL agent
Formal policy/value standing can guide action without explicit transition world model. **PASS:** model-free ≠ no agency and ≠ no representation whatsoever.

## HC-E10 — Weather predictor
Rich world/environment model; no goal/intention/action source required. **PASS:** world model ≠ agency.

## HC-E11 — Robot morphology self-model
Predictive model of own body/dynamics used for compensatory action. SelfModelStanding yes; consciousness/self-awareness not entailed. **PASS.**

## HC-E12 — LLM says `I am tired`
First-person linguistic form exists; no self-model or physiological tiredness follows without grounding. **PASS.**

## HC-E13 — Human intends bitter medicine
Want/liking may be negative; decision/commitment/health goal support intention. **PASS:** intention ≠ desire.

## HC-E14 — Foreseen side effect
Bearer intends action A, predicts side effect S, accepts S but does not organize action toward S as target. **PASS:** prediction ≠ intention.

## HC-E15 — Plan proposal generated by AI, human adopts it
AI PlanProposalStanding; human decision/adoption can create human Plan/IntentionStanding; AI may separately hold delegated operational intentions if configured. **PASS.**

## HC-E16 — Institutionally delegated approval bot
High bounded Decision/Authority/Action autonomy with externally supplied policy, goals and norms. **PASS:** autonomy vector beats scalar label.

---

# 46. Provisional AutonomyClaim v0

```text
AutonomyClaim = <
  Bearer/Role,
  Autonomy Domain,
  Governance Source,
  What can be set/revised/vetoed/authorized/triggered?,
  External Intervention Requirement,
  Approval/Escalation Structure,
  Override/Veto Structure,
  Resource/Information Dependencies,
  Goal/Norm Provenance,
  Temporal Horizon,
  Boundary/Standing Route,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### E8-105
Bare `B is autonomous` is under-specified unless the autonomy domain and governance/dependence structure are supplied.

---

# 47. Provisional InitiativeClaim v0

```text
InitiativeClaim = <
  Episode/Agenda,
  Bearer,
  Trigger Route,
  Agenda Source,
  Goal/Commitment Source,
  Timing Governance,
  Option/Means Generation,
  Need for Contemporary External Directive?,
  Persistence Profile,
  Delegation Context,
  Evidence/Provenance,
  Scope
>
```

### E8-106
Initiative evidence must distinguish timer/event/endogenous activation from practical agenda generation/governance.

---

# 48. Provisional IntentionProfile v0

```text
IntentionProfile = <
  Bearer,
  Action/Practical Target,
  Prior/Current-Action Intention?,
  Decision/Adoption Route,
  Commitment Standing,
  Goal/Norm/Need Dependencies,
  Plan/Policy Coordination?,
  Persistence,
  Reconsideration/Drop Conditions,
  Means-End Consequences?,
  Delegated/Institutional/Formal/Psychological Route,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### E8-107
Intention richness and consciousness are separate profiles.

---

# 49. Provisional WorldModelProfile v0

```text
WorldModelProfile = <
  Bearer/System,
  Model Vehicle,
  Target World Domain,
  Content/Relations,
  Static/Dynamic/Causal/Affordance/etc.,
  Internal/External/Shared Locus,
  ModelStanding Route,
  Current Estimate/Uncertainty,
  Active Use {
    state estimation?, prediction?, simulation?, planning?, control?
  },
  Counterfactual Capacity?,
  Error/Update Route?,
  Evidence/Provenance,
  Scope
>
```

### E8-108
World-model richness is not reducible to parameter count or prediction accuracy alone.

---

# 50. Provisional SelfModelProfile v0

```text
SelfModelProfile = <
  Bearer,
  Model Vehicle,
  Self Target Aspect {
    body?, state?, capability?, resource?, policy?, goal?,
    epistemic limit?, agency?, identity?, social role?
  },
  ModelStanding Route,
  Internal/External/Shared Locus,
  Active Use?,
  Accuracy/Calibration?,
  Damage/Mismatch Sensitivity?,
  Update Route?,
  FirstPerson/Reflective/Phenomenal Profile?,
  Evidence/Provenance,
  Scope
>
```

### E8-109
A self model should be typed by **what aspect of self it models** rather than treated as one all-or-nothing faculty.

---

# 51. Revised AgencyStanding candidate v0.5

MF8-E yields:

```text
AgencyStanding(B | Σ)
 = Individuated/Persistent Bearer
 + Persistent Agential Source Organization
 + EvaluativeOrientationStanding
 + Choice/Practical-Selection Organization
 + Action Domain/Repertoire
 + Capacity to instantiate AgentialActionStanding tokens
 + AutonomyProfile
 + Decision/Policy/Plan Profiles as applicable
 + Standing Route
 + Scope
```

with optional/richness profiles:

```text
Initiative/Proactivity Profile
Intention Profile
WorldModel Profile
SelfModel Profile
Reflective/Deliberative Profile
```

### E8-110
AutonomyProfile is included because every serious agency claim should expose governance/dependence dimensions, **not because high autonomy on every dimension is required**.

### E8-111
Minimal AgencyStanding does not require:

```text
high goal autonomy
high norm autonomy
initiative
explicit intention
explicit world model
explicit self model
consciousness
first-person representation
```

### E8-112
Stronger delegated, proactive, planning and reflective forms of agency can be characterized by enrichment along these profiles without redefining minimal agency.

---

# 52. Final MF8-E non-collapse stack

```text
Autonomy ≠ Independence
Dependence ≠ Governance
Agency ≠ Autonomy
OperationalAutonomy ≠ ConstitutiveAutonomy
ActionAutonomy ≠ GoalAutonomy ≠ NormAutonomy
```

```text
Activation ≠ Initiative
EndogenousTrigger ≠ Initiative
ScheduledExecution ≠ Initiative
Initiative ≠ GoalAutonomy
Reactivity ≠ NoInitiative
Proactivity ≠ WorldModel
```

```text
Intentionality_aboutness ≠ IntentionToAct
IntentionalStanceAscription ≠ TargetIntentionStanding
Want ≠ Intention
Goal ≠ Intention
Decision ≠ Intention
Commitment ≠ Intention
Plan ≠ Intention
Prediction ≠ Intention
```

```text
WorldModel ≠ World
WorldModel ≠ PredictionAbility
WorldModel ≠ Policy
WorldModel ≠ Agency
WorldModel ≠ Intention
ModelFree ≠ RepresentationFree
```

```text
BearerIdentity ≠ SelfModel
SelfState ≠ SelfModel
ExternalModelOfB ≠ B's SelfModel
SelfModel ≠ SelfAwareness
SelfModel ≠ Consciousness
SelfModel ≠ SenseOfAgency
SelfModel ≠ Autonomy
FirstPersonToken ≠ SelfModel
```

```text
WorldModelStanding ≠ WorldModelActiveUse
SelfModelStanding ≠ SelfModelAccuracy
ModelPrediction ≠ Observation
```

---

# 53. FoundationReopen audit

MF8-E attacks FRC-A1 and the MF3 representation boundary.

## State / Dynamics / Control

No revision is required:

- autonomy is governance/dependence standing layered over action/decision/control relations;
- initiative concerns activation/agenda/source standing rather than a new dynamics primitive;
- intention is practical commitment/guidance standing layered over decision/plan/action;
- world/self models remain representation/model standings rather than target world/state identity;
- minimal agency can remain reactive/model-light without redefining dynamics/control.

## Representation

MF3 also survives:

- Aboutness, WorldModelStanding and SelfModelStanding consume RepStanding;
- analyst decodability/first-person language do not establish target representations;
- model content remains distinct from referent/world;
- active use remains distinct from standing.

### E8-113
**FRC-A1 is NOT triggered.**

### E8-114
No MF0–MF7 FoundationReopenCondition is currently demonstrated.

---

# 54. Evidence anchors

Primary/authoritative anchors used in MF8-E:

1. **Michael Wooldridge & Nicholas Jennings (1995), `Intelligent Agents: Theory and Practice`, Knowledge Engineering Review 10(2).** Their weak notion explicitly separates autonomy, reactivity and pro-activeness; autonomy involves operation without direct intervention and control over actions/internal state, while pro-activeness is goal-directed initiative. Used as an operational/software-agent standing route, not a universal ontology.
2. **Xabier E. Barandiaran, Ezequiel Di Paolo & Marieke Rohde (2009), `Defining Agency: Individuality, Normativity, Asymmetry, and Spatio-temporality in Action`, Adaptive Behavior 17(5), DOI `10.1177/1059712309343819`.** Strong autonomous-organization route; also supplies the E. coli case where observer-visible spatial structure need not be represented from the bacterium's own perspective.
3. **Ezequiel Di Paolo & Hiroyuki Iizuka (2008), `How (not) to model autonomous behaviour`, BioSystems 91(2), DOI `10.1016/j.biosystems.2007.05.016`.** Autonomy modeled as system organization/self-sustaining identity rather than merely a callable behavioral function.
4. **Marieke Rohde & John Stewart (2008), `Ascriptional and 'genuine' autonomy`, BioSystems 91(2), DOI `10.1016/j.biosystems.2007.05.017`.** Supports maintaining ascribed autonomy claims separately from evidence about target generative organization.
5. **Michael Bratman (1987), `Intention, Plans, and Practical Reason`.** Planning theory: intentions are elements of partial plans that organize future practical reasoning; used to distinguish intention from desire, goal, plan representation and transient choice.
6. **Philip R. Cohen & Hector J. Levesque (1990), `Intention is Choice with Commitment`, Artificial Intelligence 42(2–3), DOI `10.1016/0004-3702(90)90055-5`.** Formal route connecting choice, commitment, goal persistence and intention; demonstrates that intention includes persistence/drop conditions and does not reduce to a selected action token.
7. **Rodney A. Brooks (1991), `Intelligence without Representation`, Artificial Intelligence 47, DOI `10.1016/0004-3702(91)90053-M`.** Used as a hard falsifier against making a centralized explicit world model universal to intelligent/agentic behavior; MF8-E does not infer that every internal process in such architectures is representation-free under all theories.
8. **Richard S. Sutton (1990), `Integrated Architectures for Learning, Planning, and Reacting Based on Approximating Dynamic Programming`.** Dyna provides a clear formal route where a learned model of world transitions/rewards is used for planning alongside reactive/learned action selection.
9. **Nathaniel Daw, Yael Niv & Peter Dayan (2005), `Uncertainty-based competition between prefrontal and dorsolateral striatal systems for behavioral control`, Nature Neuroscience 8, DOI `10.1038/nn1560`.** Model-based versus computationally cheaper model-free/habit-like control as coexisting behavioral-control routes; used against world-model necessity and one-route agency.
10. **David Ha & Jürgen Schmidhuber (2018), `World Models`, arXiv `1803.10122`.** Engineered generative world-model route supporting policy learning in internally generated trajectories.
11. **Josh Bongard, Victor Zykov & Hod Lipson (2006), `Resilient machines through continuous self-modeling`, Science 314, DOI `10.1126/science.1133687`.** Strong non-conscious SelfModelStanding case: a machine models its own morphology/dynamics and uses model updates for compensatory behavior after damage.
12. **Robert Kwiatkowski et al. (2022), `On the Origins of Self-Modeling`, arXiv `2209.02010`.** Explicitly treats self-modeling as predictive modeling of an agent's own dynamics for internal planning/evaluation; used as a modern engineering self-model route.

Competing theories of intentionality, selfhood and autonomy remain competing. MF8-E does not collapse operational software autonomy, biological constitutive autonomy, philosophical intentionality or phenomenal selfhood into one property.

---

# 55. MF8-E verdict

The deepest result is that `autonomous agent with a world model and self model` is not one property bundle.

It decomposes into at least:

```text
AUTONOMY
 = domain-relative governance/dependence profile

INITIATIVE
 = bearer-attributable activation/agenda governance
   under standing goals/norms/commitments
   without a contemporaneous directive specifying the episode

INTENTION
 = adopted action/practical commitment
   that persists and organizes later reasoning/action

WORLD MODEL
 = grounded representation/model of relevant environmental structure

SELF MODEL
 = grounded model, recruited by the bearer,
   of some aspect of that bearer itself
```

Consequently:

> **A delegated AI system can be highly autonomous in action, decision, timing and information acquisition while having externally assigned goals and norms. Calling it simply `high-autonomy` hides the most important structure.**

> **Initiative is not equivalent to running unattended. Timers and event handlers provide activation; initiative requires bearer-relative agenda/source/guidance standing.**

> **Intentionality-aboutness and intention-to-act belong to different ontological families: representation/content versus practical commitment.**

> **World models and self models are powerful enrichments, not universal prerequisites of minimal agency. A model-free or reactive agent can still be agentic; a weather model can be world-rich but non-agentic; a robot can possess a body self-model without self-awareness.**

---

# 56. Next frontier

Proceed directly to:

```text
MF8-F — Learning, Adaptation, Development & Plasticity
```

Primary questions:

1. Learning ≠ adaptation—what standing separates informationally driven change from criterion-relative adaptive change?
2. What distinguishes parameter update, memory accumulation, habituation, conditioning, skill acquisition and structural plasticity?
3. Does adaptation require improvement relative to a criterion, viability region or task?
4. Can learning make agency stronger without being constitutive to agency?
5. What is development versus learning—especially when the bearer itself changes identity/capability structure?
6. How should evolution, ontogeny, online learning and self-modification remain separate?
7. What are policy learning, value learning, model learning, goal learning and norm learning as distinct update domains?
8. When does externally performed training become a capability/standing of the deployed bearer?
9. How should catastrophic forgetting, path dependence and developmental lock-in be represented?
10. Can a system adapt without learning and learn without adaptive benefit?

MF0–MF7 remain frozen unless a named concrete FoundationReopenCondition is demonstrated.
