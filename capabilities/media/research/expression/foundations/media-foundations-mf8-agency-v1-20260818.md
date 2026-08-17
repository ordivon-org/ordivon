# Ordivon Media Foundations — MF8 Agency Foundations v1

**Frozen:** 2026-08-18  
**Authority:** MF8-A→MF8-I  
**Status:** **FROZEN v1**  
**Reopen only via:** FRC-A1→FRC-A11 defined below.

---

# 1. Canonical minimal agency standing

```text
AgencyStanding_v1(B | Route, H, Σ)
 = ScopedBearerContinuityStanding(B | H, Σ)
 + AgentialSourceOrganizationStanding(B | H, Σ)
 + EvaluativeOrientationStanding(B | Route, Σ)
 + AgentialGuidance/RegulationStanding(B | Route, H, Σ)
 + AgentialActionDomainStanding(B | H, Σ)
 + CapacityAcrossH to instantiate AgentialActionStanding tokens
 + StandingRoute
 + Scope
 + Evidence/Provenance/Uncertainty
```

Interpretation:

> A system has AgencyStanding only when there is a sufficiently individuated bearer across the relevant agency horizon, whose organization is an attributable source of activity, for which some distinctions have grounded evaluative/practical standing, and whose source activity is regulated in relation to those distinctions through a genuine bearer-attributable action domain.

Agency is route-indexed and scope-relative; it is not one scalar essence score.

---

# 2. Scoped bearer continuity

```text
ScopedBearerContinuityStanding(B | H, Σ)
 = Bearer/Boundary Standing
 + Identity Criterion
 + Continuation Relation over H
 + permitted identity-preserving transformations
 + termination/fission/fusion rules as applicable
 + scope/provenance
```

`H` is the agency-relevant horizon, not an assumption of indefinite lifetime.

Therefore:

```text
Agency persistence ≠ long lifetime
Agency persistence ≠ component constancy
Agency persistence ≠ uninterrupted activity
```

Ephemeral/task-bounded agents are permitted if the bearer remains identifiable across the relevant episode.

---

# 3. Agential source organization

```text
AgentialSourceStanding(S, B, D | Σ)
```

requires a bearer-attributable organized source that non-trivially governs initiation, modulation, maintenance, suppression, termination or redirection of activity in domain D.

It is not:

```text
passive causal transmission
bare effector relation
mere external triggering
metaphysical first cause
randomness
```

Hence:

```text
ExternalTrigger ≠ ExternalAuthorship
Determinism ≠ NoAgency
Randomness ≠ Agency
DistributedSource ≠ NoSource
```

---

# 4. Evaluative orientation

```text
EvaluativeOrientationStanding(B | Route, Σ)
```

requires grounded relations under which some relevant distinctions matter as, for example:

```text
better / worse
viable / non-viable
attractive / aversive
acceptable / unacceptable
goal-relevant / goal-defeating
permitted / forbidden
need-satisfying / need-threatening
```

Permitted provenance routes:

```text
Constitutive / Viability-Grounded
Endogenous Organized
Learned / Internalized
Adopted
Delegated
Designed-and-Operationally-Constituted
Institutional / Role-Constituted
Hybrid
```

Observer-imputed or designer-intended purpose alone is insufficient unless it has grounded standing in the target bearer/role organization.

Agency does **not** universally require intrinsic biological normativity.

---

# 5. Agential guidance / regulation

```text
AgentialRegulationStanding(R, B, D | K, Σ)
```

holds when B's source organization modulates, maintains, suppresses, initiates, terminates or redirects coupling/activity/action-domain D in relation to grounded evaluative/practical distinctions K.

It can be:

```text
discrete or continuous
deterministic or stochastic
reactive or proactive
fixed or learned
centralized or distributed
internal or artifact-extended
```

It does not universally require:

```text
ChoiceStanding
multiple represented alternatives
DecisionStanding
deliberation
planning
WorldModelStanding
SelfModelStanding
consciousness
learning
```

`AgentialRegulationStanding ≠ ControlStanding` by identity. Control-loop structure alone is insufficient; bearer/source/evaluative/guidance standing must be independently grounded.

---

# 6. Action domain and action token

```text
AgentialActionDomainStanding(D, B | Σ)
```

is a non-empty domain of possible bearer-attributable regulation/action episodes at the declared granularity and horizon.

The domain may be continuous or highly constrained and need not form a current ChoiceAlternativeDomain.

Canonical action token:

```text
AgentialActionStanding(A, B | Σ)
 = ScopedBearerContinuityStanding
 + ActionEpisode/Attempt
 + AgentialSourceStanding
 + AgentialGuidanceStanding
 + ActionAttributionStanding
 + ActionDomain/Granularity
 + Temporal Scope
 + Standing Route
 + Evidence/Provenance
```

This definition does not presuppose AgencyStanding, avoiding `Agency ↔ Action` circularity.

AgencyStanding is then the standing of a bearer whose organization can instantiate such action tokens across relevant conditions/horizon.

---

# 7. Choice is not constitutive

MF8-D's stronger ChoiceStanding remains valid where applicable, but:

```text
Agency ≠ Choice
```

A minimal agent may regulate ongoing activity continuously or habitually without a current domain of two or more live choice alternatives.

Choice, Decision, Commitment, Intention, Policy and Plan are richer practical-organization profiles.

---

# 8. Autonomy is a profile, not an extra minimal constituent

Autonomy remains multidimensional:

```text
Action
Decision
Policy
Goal
Norm/Value
Agenda/Initiative
Information
Resource
Authority
Boundary/Constitutive
Temporal Continuation
Self-Revision
```

Minimal bearer governance is already captured by source + guidance + regulation.

Therefore:

```text
Agency ≠ high autonomy on every dimension
DelegatedGoal ≠ NoAgency
LowGoalAutonomy ≠ NoActionAgency
```

AutonomyProfile describes governance/dependence distribution rather than defining the minimal core again.

---

# 9. Standing routes

## Constitutive / biological route

Self-constituting individuality, activity source and viability/normativity-grounded regulation.

## Practical / behavioral route

Persistent bearer-level source/evaluative/guidance/action organization, with endogenous, learned, adopted or other grounded practical standing.

## Delegated operational route

Goals/norms/authority may be supplied externally, while the bearer locally governs actions within a constituted task/authority domain.

## Formal / operational route

A system satisfies declared formal agent conditions in a model/architecture. This route remains explicitly tagged and does not silently imply biological/psychological agency.

## Institutional / collective route

A CollectiveBearerStanding has group-level evaluative orientation, source/regulation and action standing through organizational constitution.

## Represented / inferred route

Agency is attributed in an observer/model representation; this remains weaker than independently grounded target AgencyStanding.

Routes may overlap. No route is frozen as the metaphysical master route for all others.

---

# 10. Agent role firewall

```text
AgentRoleStanding ≠ AgencyStanding
```

Examples such as a variable named `agent`, an RL agent slot, a scheduler worker, a game actor or LLM endpoint do not acquire target AgencyStanding by nomenclature.

Conversely, an organism or institution need not be represented as an `agent` to possess AgencyStanding.

---

# 11. Thermostat boundary

MF8 v1 freezes neither universal claim:

```text
Thermostat = Agent
Thermostat = NonAgent
```

It freezes the decomposition:

```text
ControlStanding                   strong
Reference/Setpoint Standing       strong
DesignedPurpose Standing          possible
FormalAgentRoleStanding           possible
ConstitutiveBiologicalAgency      unsupported
ThinOperationalAgency             route/evidence-sensitive
RichPracticalAgency               not established by simple loop alone
```

This prevents both controller inflation and arbitrary complexity thresholds.

---

# 12. Optional/richness profiles

Not universally constitutive:

```text
Choice / Decision / Commitment / Policy / Plan
AutonomyProfile
Initiative / Proactivity
Intention
WorldModel / SelfModel
Learning / Adaptation / Plasticity / Development
SelfModification / MetaLearning
Responsibility / Accountability / Liability
Collective / Institutional Organization
Experience / Consciousness [deferred MF9]
```

Agency may be enriched, weakened or specialized along these dimensions without redefining the minimal core.

---

# 13. Key boundary cases

```text
Rock
  → no AgencyStanding

Passive relay/amplifier
  → transformation/control path, no agency by default

Cron/one-shot script
  → scheduled execution alone, no agency

Thermostat
  → controller certain; thin operational agency route-sensitive

E. coli
  → strong constitutive minimal-agency candidate

Reflex arc
  → usually nested mechanism, not separate agent by default

Habitual human action
  → agency can survive without renewed deliberative choice

Frozen RL policy
  → learning not required if bearer/evaluation/regulation/action standing persists

Stateless LLM model artifact
  → no automatic AgencyStanding

Persistent tool-using LLM harness
  → strong delegated operational agency candidate when task bearer, goals, state, authority and actions are grounded

Market/crowd/flock
  → coordination/emergence not collective agency by default

Persistent integrated colony
  → collective-agency candidate

Corporation/constituted committee
  → strong institutional collective-agency candidate
```

---

# 14. Collective agency

Collective agency uses the same structural schema at a different bearer scale:

```text
CollectiveAgencyStanding(G | Route, H, Σ)
 = AgencyStanding_v1
   with CollectiveBearerStanding
   + collective-level source/evaluative/regulation/action constitution
```

Therefore:

```text
Plurality ≠ CollectiveBearer
Coordination ≠ CollectiveAgency
JointAction ≠ PersistentCollectiveAgency
CollectiveCapability ≠ CollectiveAgency
CollectiveAgency ≠ CollectiveConsciousness
```

Group and member agency/responsibility can coexist.

---

# 15. Canonical non-collapse rules

```text
AgentRoleStanding ≠ AgencyStanding
Control ≠ Agency
Automation ≠ Agency
SelfOrganization ≠ Agency
```

```text
Agency ≠ Choice
Agency ≠ Decision
Agency ≠ Plan
Agency ≠ Learning
Agency ≠ Intelligence
Agency ≠ AutonomyScalar
```

```text
DesignedPurpose ≠ BearerEvaluativeStanding automatically
RewardSignal ≠ intrinsic ValueStanding
UtilityFunction ≠ EvaluativeOrientation by identity
```

```text
ExternalTrigger ≠ ExternalAuthorship
DelegatedGoal ≠ NoAgency
Determinism ≠ NoAgency
Randomness ≠ Agency
```

```text
WorldModel ≠ Agency
SelfModel ≠ Agency
SenseOfAgency ≠ AgencyStanding
```

```text
MoralResponsibility ≠ Agency
LegalPersonhood ≠ Agency
CollectiveConsciousness ≠ CollectiveAgency
```

---

# 16. Evidence requirements

A serious agency claim should expose:

```text
AgencyClaim = <
  Bearer,
  Route,
  Horizon,
  Boundary/Continuity Evidence,
  Source Organization Evidence,
  Evaluative Orientation / Provenance,
  Guidance/Regulation Evidence,
  Action Domain,
  Action Attribution Evidence,
  Optional Profiles,
  Uncertainty,
  Scope
>
```

Evidence tests include:

1. boundary/identity intervention;
2. source/bypass perturbation;
3. guidance/evaluative sensitivity;
4. suppression/cancellation/maintenance evidence;
5. action attribution and granularity tests;
6. observer/designer-purpose firewall;
7. delegation/authority provenance;
8. distributed/nested source tests;
9. temporal continuation across the claimed horizon;
10. cross-domain counterexamples.

---

# 17. FoundationReopenConditions

## FRC-A1 — Bearer Boundary Failure
A robust agency case cannot be represented with ScopedBearerContinuityStanding without circularly presupposing agency.

## FRC-A2 — Source Failure
A clear agent lacks defensible bearer-attributable source organization, or clear non-agents systematically satisfy it.

## FRC-A3 — Evaluative Orientation Failure
A clear agent has no grounded evaluative/practical orientation whatsoever, or the criterion systematically over-includes non-agents.

## FRC-A4 — Regulation/Guidance Failure
A clear agent lacks evaluatively guided regulation/action, or clear non-agents systematically satisfy the relation.

## FRC-A5 — Action Attribution Failure
AgentialActionStanding cannot be grounded non-circularly or fails clear agent action cases.

## FRC-A6 — Delegated Artificial Agency Failure
Strong artificial/delegated cases cannot be represented without either biological intrinsic normativity or mere observer purpose.

## FRC-A7 — Collective Scale Failure
Genuine group agency cannot be represented as AgencyStanding at CollectiveBearer scale, or the schema systematically promotes ordinary aggregates.

## FRC-A8 — Horizon/Continuity Failure
Clear ephemeral agency exists with no meaningful bearer continuation even across its own action episode.

## FRC-A9 — Representation Necessity Failure
Later work shows representation/world/self model is necessary for every genuine agency route.

## FRC-A10 — Experience/Consciousness Necessity Failure
MF9 demonstrates phenomenal experience/consciousness is constitutively necessary for AgencyStanding.

## FRC-A11 — Cross-Domain Empirical Failure
New natural, artificial, institutional or collective evidence systematically defeats the v1 core.

Only a named concrete FRC reopens MF8.

---

# 18. Freeze statement

MF8-A→I completed:

```text
ontology/term separation
action/source/ownership
evaluative foundations
choice/decision/policy/plan
autonomy/initiative/intention/world/self models
learning/adaptation/development/plasticity
responsibility/accountability/liability
collective/joint/institutional agency
global falsification and reconstruction
```

MF8-I made three material corrections before freeze:

```text
Choice/PracticalSelection
  → removed from universal core
  → replaced by AgentialRegulation/Guidance

PersistentBearer
  → ScopedBearerContinuityStanding

AutonomyProfile
  → moved from universal constituent to governance/dependence profile
```

No MF0–MF7 FoundationReopenCondition was demonstrated.

**MF8 Agency Foundations v1 is frozen.**

Next foundational frontier: **MF9 — Experience Foundations**.
