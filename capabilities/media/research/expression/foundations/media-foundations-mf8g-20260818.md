# Ordivon Media Foundations — MF8-G Responsibility, Accountability, Credit, Blame & Liability

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 54 at start  
**Input:** MF0–MF7 frozen; MF8-A/B/C/D/E/F complete/provisional.  
**Status:** **MF8-G COMPLETE / PROVISIONAL RESPONSIBILITY ONTOLOGY. MF8 Agency Foundations are not frozen yet.**  
**Next:** MF8-H — Collective Agency, Joint Action & Institutional Agency.

---

# 0. Purpose

MF8-B already decomposed action attribution into source, authorship, performer, executor, effector, principal/delegator, institution, experiential agency and responsibility routes. MF8-D then separated recommender, chooser, decision-maker, authorizer, policy/plan author, principal/delegator, institutional bearer and executor. MF8-E/F added autonomy, knowledge/model, learning and self-revision distinctions.

MF8-G now reconstructs the normative and institutional attribution family:

```text
Causal Contribution / Causal Responsibility
Agential Responsibility
Outcome Responsibility
Role Responsibility
Answerability
Accountability
Forward-Looking Responsibility
Credit
Blame / Culpability
Legal Liability
Repair / Compensation / Remediation Duty
```

The main danger is collapsing these into one sentence:

```text
B was responsible for outcome O.
```

Without a standing route, that sentence is radically ambiguous.

The primary questions are:

1. Is being a cause sufficient for responsibility?
2. Is authorship sufficient?
3. What additional epistemic/control/normative conditions matter?
4. What is the difference between being responsible and being held responsible?
5. Can accountability exist without blame?
6. Can liability exist without moral culpability?
7. Can a bearer deserve blame for an attempt even when no harm occurs?
8. Can a bearer owe repair for harm it did not culpably cause?
9. How should omission, negligence, coercion and foreseeable side effects be represented?
10. How does delegation distribute responsibility across principal, recommender, decision-maker, authorizer and executor?
11. Can a non-conscious artificial system possess operational/role responsibility without moral responsibility?
12. What exactly is a `responsibility gap` once responsibility routes are typed?

---

# 1. Frozen substrate consumed, not reopened

MF8-G preserves:

```text
Cause ≠ ActionSource
ActionSource ≠ Author
Author ≠ Executor
Principal ≠ Author
DecisionMaker ≠ Executor
Authorization ≠ Execution
Agency ≠ MoralResponsibility
Control ≠ Agency
Autonomy ≠ Responsibility
Intention ≠ Outcome
Learning ≠ Agency
```

and adds responsibility-specific firewalls rather than reopening MF0–MF7.

### G8-001
**No MF0–MF7 FoundationReopenCondition is triggered at MF8-G entry.**

---

# 2. ResponsibilityClaim must be typed from the start

Provisional generic form:

```text
ResponsibilityClaim(B, X, R | K, Σ)
```

where:

- `B` = bearer/role to whom responsibility is attributed;
- `X` = action, omission, decision, outcome, risk, duty, system/domain or consequence;
- `R` = responsibility standing route;
- `K` = relevant norm, role, legal rule, causal criterion, epistemic standard or governance framework;
- `Σ` = context, time, scope and provenance.

### G8-002
**Responsibility is not one primitive relation.**

### G8-003
Bare `B is responsible` is under-specified until the bearer, object of responsibility and responsibility route are declared.

---

# 3. CausalContributionStanding

Begin with the weakest relevant route:

```text
CausalContributionStanding(B, O | C, Σ)
```

holds when B's action, omission, state, decision, design, policy, resource provision or other occurrence stands in a grounded causal/contributory relation to outcome O under causal criterion C.

Possible causal routes include:

```text
Direct Production
Necessary Condition
Sufficient Component
Enabling Condition
Opportunity Provision
Risk Increase
Triggering
Sustaining
Preventive Failure / Omission
Counterfactual Contribution
Overdetermining Contribution
Causal Chain / Mediation
```

### G8-004
**Causal contribution ≠ moral responsibility.**

### G8-005
**Causal contribution ≠ legal liability.**

### G8-006
**Causal contribution ≠ blameworthiness.**

A lightning strike, child, unconscious mechanism, non-agent component or blameless actor may causally contribute to harm.

---

# 4. Cause is not one binary switch

Distributed systems create many-hands causation:

```text
Designer
Data provider
Model
Policy author
Operator
Authorizer
Executor
Infrastructure
Environment
```

may all be in the explanatory causal history.

### G8-007
`But-for cause` is not a universal responsibility allocator.

### G8-008
Overdetermination and redundant causal pathways can make a bearer causally relevant even when removing that bearer would not change the outcome under the simplest counterfactual.

### G8-009
Causal analysis should therefore expose contribution route rather than force one `the cause` token.

Legal/philosophical causation traditions similarly distinguish causal explanation from the further attribution of responsibility/liability; causal contribution is often necessary in some legal routes but not itself sufficient for normative responsibility.

---

# 5. ActionResponsibilityStanding

A stronger route concerns responsibility **for one's conduct**:

```text
ActionResponsibilityStanding(B, A | Σ)
```

holds when action/omission A is attributable to B under the relevant AgentialActionStanding/DecisionStanding and the responsibility framework recognizes B as an appropriate bearer of responsibility for that conduct.

This immediately separates:

```text
ResponsibilityForAction
ResponsibilityForOutcome
```

### G8-010
A bearer can be responsible for an action without being responsible for every downstream consequence.

### G8-011
A bearer can be responsible for an attempted action even when the intended outcome never occurs.

Fischer & Ravizza's account is a strong moral-responsibility route: conduct responsibility depends on guidance control, roughly action issuing from the agent's own appropriately reasons-responsive mechanism, while consequence/omission responsibility requires further analysis.

---

# 6. OutcomeResponsibilityStanding

Provisional:

```text
OutcomeResponsibilityStanding(B, O | A, N, Σ)
```

holds when outcome O is normatively/role-legally attributable to B through action/omission A under responsibility norm N, rather than merely belonging somewhere downstream in the causal graph.

Potential factors include:

```text
Causal Contribution
Authorship
Control / Guidance Control
Foreseeability / Knowledge
Intent / Risk Acceptance
Duty / Role Obligation
Proximity / Non-deviance
Intervening Agency
Authority
Competence
Negligence / Recklessness
Consent / Assumption of Responsibility
```

### G8-012
**ResponsibilityForOutcome ≠ ResponsibilityForAction.**

### G8-013
Outcome responsibility can be weakened or broken by causal deviation/intervening events even when action responsibility remains.

### G8-014
Conversely, institutional/legal rules can assign outcome responsibility/repair duties beyond personal moral fault.

---

# 7. AgentialResponsibilityStanding

MF8-G uses a broad non-moral primitive:

```text
AgentialResponsibilityStanding(B, X | Σ)
```

when X is attributable to B as a bearer of AgencyStanding through B's action/decision/commitment/authority organization in a way relevant to evaluation of B's conduct or practical governance.

This is stronger than causal responsibility, but still not identical to moral culpability.

### G8-015
**Agential responsibility ≠ MoralResponsibility.**

### G8-016
A non-conscious or institutionally constituted artificial bearer may possess operational/agential responsibility standing in a bounded domain without being an appropriate target of moral blame.

This is essential for artificial and institutional systems.

---

# 8. RoleResponsibilityStanding

A bearer can be responsible **because of a role**, even before any fault occurs.

```text
RoleResponsibilityStanding(B, D | Role, Σ)
```

holds when bearer B's role validly assigns duties, oversight, maintenance, decision, care, reporting or governance responsibilities over domain D.

Examples:

```text
system owner responsible for backups
captain responsible for vessel safety
board responsible for governance
operator responsible for monitoring
agent responsible for bounded task domain
```

### G8-017
**Role responsibility ≠ causal responsibility.**

### G8-018
**Role responsibility ≠ blameworthiness.** One can satisfy the role completely and remain `responsible for` the domain.

### G8-019
Role responsibility is often forward-looking rather than retrospective.

---

# 9. ForwardLookingResponsibilityStanding

Provisional:

```text
ForwardResponsibilityStanding(B, D | K, Σ)
```

holds when B has a present/future duty or governance charge to monitor, maintain, prevent, decide, repair, improve, respond or otherwise steward domain D under criterion K.

### G8-020
**Forward-looking responsibility ≠ retrospective blame.**

### G8-021
A system can be assigned responsibility to prevent failures even if it did not cause prior failures.

### G8-022
This route is crucial for governance and engineering because responsibility allocation need not wait for harm.

---

# 10. AnswerabilityStanding

`Accountability` is often too broad. First define answerability:

```text
AnswerabilityStanding(B, X | Audience, K, Σ)
```

holds when B is validly required to provide reasons, explanations, evidence, records or justification concerning X to an audience/forum under criterion K.

### G8-023
**Answerability ≠ causal responsibility.**

### G8-024
**Answerability ≠ blame.** A regulator, operator or service owner may owe an explanation for an event even if personally blameless.

### G8-025
Answerability can be institutional/operational even when B lacks consciousness, if B is a role-bearing organization/system that can provide records/explanations through its constituted mechanisms.

---

# 11. AccountabilityStanding

Provisional broader relation:

```text
AccountabilityStanding(B, X | Forum, Standard, Consequence, Σ)
```

holds when B is institutionally/socially/normatively positioned to be called to account for X before a forum, with obligations to disclose/explain/justify and with recognized evaluation, remediation, correction, sanction or consequence mechanisms.

Accountability commonly involves:

```text
Identifiable Accountable Bearer
Forum / Audience
Domain / Decision / Outcome
Applicable Standard
Trace/Evidence Access
Answerability Requirement
Review/Judgment Procedure
Correction / Remedy / Consequence Route
```

### G8-026
**Accountability ≠ Responsibility by identity.**

### G8-027
**Accountability ≠ Punishment.**

### G8-028
**Accountability can exist without blame**, e.g. mandatory explanation, audit, correction and remediation after a blameless failure.

Nissenbaum's computerized-society work is historically important precisely because delegation to computerized systems can obscure accountable bearers and weaken tracing/answerability practices even where technical causation remains present.

---

# 12. Being responsible ≠ being held responsible

MF8-G distinguishes:

```text
ResponsibilityStanding
HoldingResponsibleStanding
```

`HoldingResponsibleStanding(H, B, X | K, Σ)` concerns another bearer/forum H adopting a valid responsibility response toward B regarding X.

Possible holding-responsible responses include:

```text
request explanation
require remediation
criticize
sanction
praise
blame
compensate
remove authority
revise governance
```

### G8-029
**BeingResponsible ≠ BeingHeldResponsible.**

A bearer can be responsible but escape attribution; a bearer can be blamed incorrectly despite lacking the relevant standing.

### G8-030
Responsibility ontology must therefore distinguish target standing from social/institutional attribution practices.

---

# 13. MoralResponsibilityStanding

MF8-G does not attempt to settle all free-will theories. It introduces a route that can host rival theories:

```text
MoralResponsibilityStanding(B, X | MoralFramework, Σ)
```

holds when B is an appropriate target of moral appraisal/holding-responsible practices for X under the declared moral-responsibility framework.

Candidate factors across major traditions include:

```text
Agency / Authorship
Control / Guidance Control
Reasons Responsiveness
Knowledge / Awareness / Foreseeability
Intent / Quality of Will
Competence / Capacity
History / Ownership of Mechanism
Absence or Degree of Coercion
Norm Understanding
Opportunity / Avoidability under some theories
```

### G8-031
MF8-G does not make metaphysical alternative possibilities a universal condition.

Fischer & Ravizza explicitly defend guidance control without requiring regulative control/alternative possibilities, while other moral-responsibility traditions emphasize different conditions.

### G8-032
MoralResponsibilityStanding is therefore theory/framework-relative at this foundation layer where rival theories remain live.

---

# 14. Reactive attitudes and blame

Strawson's `Freedom and Resentment` is a major route for understanding responsibility practices through interpersonal reactive attitudes such as resentment, gratitude, forgiveness and related responses to the quality of another's will.

MF8-G extracts only the structural lesson:

```text
Moral responsibility / blame practice
≠ mere causal attribution.
```

### G8-033
**BlameStanding requires a normatively evaluative route beyond causal contribution.**

### G8-034
Reactive-attitude practice is one important moral-responsibility route, not a universal definition for operational/legal/institutional responsibility.

---

# 15. BlameStanding / CulpabilityStanding

Provisional:

```text
BlameStanding(B, X | N, Σ)
```

holds when B's conduct/attitude/omission regarding X is fittingly negatively appraised under norm N in a way that makes B an appropriate target of blame/culpability, given the relevant agency, epistemic, control, competence and excuse conditions.

### G8-035
**Blame ≠ Responsibility generally.**

### G8-036
**Blame ≠ Harm.** A harmful outcome can be blameless.

### G8-037
**Blame ≠ Causal contribution.** A minor causal contributor may be blameless; an unsuccessful malicious attempt may be blameworthy despite no harmful outcome.

---

# 16. CreditStanding

Positive attribution deserves equal treatment.

```text
CreditStanding(B, X | N, Σ)
```

holds when B is fittingly positively appraised/credited for action, effort, skill, judgment, contribution or outcome X under criterion N.

### G8-038
**Credit ≠ causal contribution.** A lucky contributor may not deserve full credit.

### G8-039
**Credit ≠ outcome success.** A highly competent, well-judged attempt may merit credit despite bad luck.

### G8-040
Moral luck therefore attacks naive `outcome = credit/blame` mappings in both positive and negative directions.

---

# 17. LiabilityStanding

`Liability` is an institutional/legal standing rather than a synonym for moral guilt.

```text
LiabilityStanding(B, X | Legal/InstitutionalRule, Remedy, Σ)
```

holds when an applicable legal/institutional rule makes B subject to a recognized consequence/remedy/obligation because of X—for example compensation, damages, penalty, corrective action or other legal consequence.

### G8-041
**Liability ≠ MoralResponsibility.**

### G8-042
**Liability ≠ Blame.** Strict/vicarious/no-fault liability routes can impose legal consequences without ordinary moral culpability.

### G8-043
**Moral blame ≠ legal liability.** Conduct may be morally objectionable yet outside a particular liability rule.

MF8-G deliberately does not encode one jurisdiction's liability doctrine into Agency Foundations.

---

# 18. Repair / RemediationStanding

A bearer may owe repair even where blame is absent.

```text
RemediationDutyStanding(B, H | Basis, Σ)
```

holds when B has a valid duty to repair, mitigate, restore, compensate, disclose, recall, correct or otherwise respond to harm/problem H under basis `Basis`.

Possible bases:

```text
Causal contribution
Role responsibility
Ownership/control of system
Contract
Institutional assignment
Risk creation
Beneficiary status
Capability to repair
Legal rule
Moral duty
```

### G8-044
**Remediation duty ≠ blameworthiness.**

This is particularly important for complex systems: insisting that only the blameworthy can repair creates governance gaps.

---

# 19. Responsibility condition vector

MF8-G rejects a single responsibility threshold. Instead define evidence/factor dimensions:

```text
ResponsibilityConditionProfile = <
  CausalContribution,
  ActionAuthorship,
  DecisionStanding,
  Authority,
  Control / GuidanceControl,
  Alternative/Intervention Capacity?,
  Knowledge,
  Foreseeability,
  Intent,
  Risk Awareness,
  Competence,
  ReasonResponsiveness,
  RoleDuty,
  NormUnderstanding,
  OpportunityToPrevent,
  OmissionStanding,
  Delegation/Principal Relation,
  Coercion/Compulsion,
  Historical Ownership/Adoption,
  Remediation Capacity,
  Standing Route
>
```

### G8-045
No one factor universally establishes every responsibility route.

---

# 20. EpistemicStanding for responsibility

Separate:

```text
ActualKnowledgeStanding
ReasonableForeseeabilityStanding
RiskAwarenessStanding
IgnoranceStanding
MistakenBeliefStanding
WillfulBlindnessCandidate
InformationAccessStanding
DutyToKnowStanding
```

### G8-046
**Actual knowledge ≠ reasonable foreseeability.**

### G8-047
**No actual knowledge ≠ no responsibility universally**, because negligence/recklessness/duty-to-know routes can matter.

### G8-048
Conversely, unforeseeable consequences can weaken culpability even where causal contribution is clear.

Matthias's AI `responsibility gap` argument centrally turns on this epistemic/control structure: learning systems may create outcomes that operators/designers cannot reasonably predict/control, threatening traditional culpability attribution. Later literature disputes whether this creates a true gap or instead shifts responsibility/control design requirements; MF8-G keeps the dispute open rather than assuming the gap exists by definition.

---

# 21. CompetenceStanding

```text
ResponsibilityCompetenceStanding(B, D | K, Σ)
```

concerns whether B possesses the cognitive/practical/role capacities required by responsibility framework K for domain D.

Depending on route, competence may include:

```text
understanding relevant norms
recognizing reasons/risks
forming intentions
controlling action
communicating explanations
learning from correction
role-qualified expertise
```

### G8-049
**AgencyStanding ≠ moral-responsibility competence.**

### G8-050
A bearer can act/decide agentically while lacking the competence required for moral blame under a particular framework.

### G8-051
Operational role responsibility can require very different competence than moral personhood.

---

# 22. Control for responsibility

MF7 ControlStanding and MF8 autonomy are not automatically responsibility control.

MF8-G distinguishes:

```text
CausalControl
ActionSelectionControl
GuidanceControl
DecisionAuthority
PreventiveControl
Override/VetoControl
SupervisoryControl
RemediationControl
```

### G8-052
**Having causal influence ≠ having responsibility-relevant control.**

### G8-053
A supervisor nominally `in the loop` may lack meaningful preventive/epistemic control if intervention is too late, options are constrained, or information is insufficient.

### G8-054
Responsibility claims based on `human oversight` therefore require evidence about actual epistemic and causal intervention capacity, not the mere existence of a human approval UI.

---

# 23. Authority and responsibility

Authority is another independent dimension.

```text
AuthorityStanding(B, D | Institution, Σ)
```

may grant B power to decide/authorize within D.

### G8-055
**Authority ≠ responsibility by identity.**

A bearer can hold authority yet exercise it competently/blamelessly; another actor may remain responsible for implementation defects.

### G8-056
But authority can generate role/forward responsibility even without direct causal contribution to every event.

### G8-057
Delegation of authority changes responsibility topology and must be tracked explicitly.

---

# 24. Intention and responsibility

MF8-E separated intention from foreseen side effects.

MF8-G preserves:

```text
IntendedOutcome
ForeseenButUnintendedOutcome
RiskedOutcome
UnforeseenOutcome
```

### G8-058
**Intention can strengthen some blame/credit routes but is not universally required for responsibility.**

Negligent or reckless conduct can be responsibility-bearing without intent to cause harm.

### G8-059
A harmful side effect can be responsibility-relevant even when not intended, depending on foreseeability, risk acceptance, duty and control.

---

# 25. NegligenceStanding

Provisional:

```text
NegligenceStanding(B, X | StandardOfCare, Σ)
```

holds when B fails a relevant duty/standard of care through omission, inadequate attention, preparation, monitoring, competence or precaution under circumstances where the standard validly applied.

### G8-060
**Negligence ≠ Intention.**

### G8-061
**Negligence ≠ mere bad outcome.** A bad outcome can occur despite reasonable care.

### G8-062
Negligence requires a standard/duty and evidence that conduct fell below it, not hindsight alone.

---

# 26. RecklessnessStanding

Provisional:

```text
RecklessnessStanding(B, X | RiskStandard, Σ)
```

concerns knowingly/consciously accepting, or under some frameworks culpably disregarding, a substantial relevant risk in violation of the applicable standard.

### G8-063
**Recklessness ≠ negligence by identity.**

### G8-064
Risk awareness and disregard must be kept separate from mere causal risk creation.

---

# 27. Coercion, compulsion and responsibility

MF8-B established:

```text
Coercion ≠ PhysicalCompulsion
```

MF8-G adds responsibility effects.

Under coercion:

- local ActionAuthorship may remain;
- practical alternatives may remain but be severely distorted;
- autonomy may be reduced;
- blame/responsibility may be mitigated depending on threat, options, norms and framework.

Under physical compulsion:

- bearer-level authorship/choice may collapse;
- responsibility for the compelled movement may transfer/shift toward the coercer/forcer.

### G8-065
**Reduced autonomy ≠ automatically zero responsibility.**

### G8-066
**Physical compulsion can undermine authorship more directly than coercive pressure.**

### G8-067
Excuse/mitigation standing must be kept separate from whether the event physically occurred.

---

# 28. ExcuseStanding and JustificationStanding

A complete responsibility ontology must distinguish:

```text
WrongfulActStanding
JustificationStanding
ExcuseStanding
```

Provisional:

```text
JustificationStanding
  conduct is permitted/appropriate under relevant norm despite normally prohibited form

ExcuseStanding
  conduct remains wrongful/problematic but bearer is not fully blameworthy due to competence, coercion, ignorance, incapacity or related conditions
```

### G8-068
**Justification ≠ Excuse.**

### G8-069
Both can alter blame/liability routes without changing causal contribution.

---

# 29. Omission responsibility

MF8-B defined OmissiveActionStanding only when there is opportunity/actionability + guidance + governed withholding + attribution.

MF8-G adds:

```text
OmissionResponsibilityStanding(B, O | Duty, Opportunity, Σ)
```

which requires at minimum a relevant responsibility route such as:

```text
Duty/Role to act
Relevant opportunity/capacity
Knowledge/foreseeability as required
Governed non-action or culpable failure
Causal/preventive relevance as route requires
```

### G8-070
**Mere absence ≠ responsible omission.**

### G8-071
An observer's statement `B could have prevented it` is insufficient unless opportunity, authority, knowledge, duty and actual preventive capacity are established.

---

# 30. Failed attempts and moral luck

Case:

```text
A intends serious harm
A performs blameworthy attempt
random event prevents harm
```

The lack of harmful outcome does not erase action/intention responsibility.

Conversely:

```text
minor negligence
+ extremely unlucky chain
→ huge harm
```

can enlarge outcome while underlying culpability remains a separate question.

### G8-072
**Outcome magnitude ≠ culpability magnitude by identity.**

### G8-073
**AttemptResponsibilityStanding can exist without OutcomeResponsibilityStanding for the prevented harm.**

### G8-074
Credit/blame must preserve the distinction between conduct quality and luck-mediated outcomes.

---

# 31. Foreseen side effects

MF8-E distinguished intention from prediction.

Suppose B intentionally performs A, correctly foresees side effect S, does not intend S, but accepts the risk.

Possible standings:

```text
IntentionForA          yes
PredictionOfS          yes
IntentionForS          no
RiskAcceptanceOfS      maybe yes
CausalContributionToS  maybe yes
OutcomeResponsibility  depends on norm/control/duty
```

### G8-075
**Foreseen ≠ intended.**

### G8-076
But `not intended` does not imply `not responsible`.

---

# 32. Delegation topology

MF8-B/D/E provide the relevant stack:

```text
Principal / Goal Setter
Policy / System Designer
Data/Model Provider
Recommender
Chooser
Decision Maker / Settler
Authorizer
Executor / Effector
Supervisor / Monitor
Institution
```

MF8-G insists that responsibility be evaluated per route.

Possible distribution:

```text
Principal:
  role responsibility + delegation responsibility

Designer:
  design/foreseeability responsibility

Agent:
  local agential/operational responsibility

Human authorizer:
  decision/authorization responsibility

Executor:
  action responsibility

Institution:
  accountability/liability/repair responsibility
```

### G8-077
**Delegation ≠ transfer of all responsibility.**

### G8-078
**Delegation ≠ retention of all responsibility by principal either.** Real delegated local agency/authority can create additional responsibility loci.

### G8-079
Responsibility topology can be many-to-many rather than zero-sum.

---

# 33. Delegation responsibility

Provisional:

```text
DelegationResponsibilityStanding(P, A, D | Σ)
```

concerns P's responsibility for granting A authority/capability over domain D, including reasonable selection, constraints, monitoring, information, escalation and revocation structures under the applicable norm/role.

### G8-080
A principal need not be responsible for every unforeseeable delegated token outcome.

### G8-081
But principal responsibility can arise from irresponsible delegation architecture even when the local delegate authored the immediate action.

This prevents responsibility laundering through delegation.

---

# 34. Recommendation responsibility

A recommender may not settle the decision but can still bear responsibility for recommendation quality.

```text
RecommendationResponsibilityStanding(R, rec | Standard, Σ)
```

may depend on:

```text
epistemic competence
known limitations
calibration
appropriate uncertainty disclosure
conflict-of-interest management
foreseeable reliance
domain scope
```

### G8-082
**No final DecisionStanding ≠ no responsibility whatsoever.**

### G8-083
A recommender can be responsible for negligent/misleading advice while another bearer remains responsible for final authorization.

---

# 35. Authorization responsibility

A human or system with authority to approve may bear responsibility for the authorization act if the role gives genuine settlement power and adequate epistemic/control conditions.

### G8-084
**Rubber-stamp interface ≠ meaningful authorization responsibility automatically.**

If the authorizer lacks time, information, alternatives or actual veto power, the architecture may falsely display responsibility while failing to provide its prerequisites.

### G8-085
Human-in-the-loop labels therefore require concrete analysis of knowledge, control, authority and practical alternatives.

---

# 36. Automation and responsibility gaps

Matthias's `responsibility gap` challenge can now be typed more precisely.

A genuine gap claim must say which route is missing:

```text
Causal attribution gap?
Culpability/blame gap?
Moral accountability gap?
Public/institutional accountability gap?
Legal liability gap?
Forward-responsibility gap?
Remediation gap?
```

### G8-086
**`Responsibility gap` is not one phenomenon.**

### G8-087
A system may have no fitting human blame target yet still have clear legal/institutional accountability and remediation routes.

### G8-088
Conversely, clear causal attribution does not guarantee an accountable forum or remedy.

Later work explicitly distinguishes multiple AI responsibility-gap types rather than one monolithic gap; MF8-G adopts the typed structure while keeping empirical/normative disputes open.

---

# 37. Non-conscious artificial agents

MF8-G permits a layered answer.

An artificial agent can potentially have:

```text
CausalContributionStanding          yes
AgentialActionStanding              yes
OperationalDecisionStanding         yes
RoleResponsibilityStanding          yes
OperationalAnswerabilityStanding    possible
InstitutionalAccountabilityRole     possible
```

without thereby establishing:

```text
Phenomenal consciousness
Moral personhood
Reactive-attitude competence
Moral blameworthiness
Legal personhood
```

### G8-089
**Operational/role responsibility ≠ MoralResponsibility.**

### G8-090
It is therefore unnecessary to choose between the two crude statements `AI is responsible` and `AI can never be responsible`; the standing route decides what is being claimed.

---

# 38. Accountability artifacts and answerability

For artificial/institutional systems, answerability may be realized through artifacts/processes:

```text
audit log
trace
provenance record
model card / limitation record
decision rationale
policy version
approval record
incident report
counterfactual/replay evidence
```

But:

### G8-091
**Traceability artifact ≠ accountability by identity.**

An audit log is evidence infrastructure; accountability additionally requires an accountable bearer, forum, standard and consequence/remediation route.

### G8-092
**Explanation output ≠ answerability satisfaction automatically.** It must address the applicable question/standard with sufficient fidelity and provenance.

---

# 39. Responsibility laundering

Provisional failure pattern:

```text
ResponsibilityLaunderingStanding
```

when an institution/principal uses delegation, automation, formal approval or role fragmentation to make responsibility appear transferred/fulfilled while the delegated bearer lacks the relevant competence/control/accountability standing and the principal/institution retains relevant governance power or duty.

Examples:

```text
`the AI decided` when institution designed and authorized policy
`human approved` when human had no practical veto/information
`vendor is responsible` despite customer-controlled unsafe deployment
```

### G8-093
Responsibility attribution must follow actual standing topology, not interface labels.

---

# 40. Distributed responsibility without dilution to zero

Many-hands systems create a second failure mode:

```text
many contributors
→ each contribution appears small
→ everyone claims no responsibility
```

MF8-G rejects automatic dilution.

### G8-094
Multiple bearers can simultaneously possess distinct or overlapping responsibility standings for one event/domain.

### G8-095
Responsibility is not generally conserved like a fixed quantity that must sum to 1.

### G8-096
Apportionment can be useful in legal/institutional frameworks, but the ontology must not infer `more responsibility for A ⇒ less for B` without an explicit allocation rule.

---

# 41. Collective/institutional responsibility deferred, but institutional routes admitted

Corporations, committees and teams can already bear formal/role/accountability/liability standings under institutional constitution.

However:

```text
InstitutionalResponsibilityStanding
≠ CollectiveAgencyStanding automatically
```

### G8-097
MF8-G admits institutional responsibility routes where the institution is already a valid role/legal bearer, while full collective agency constitution is deferred to MF8-H.

### G8-098
Institutional liability/accountability can exist even if collective moral agency remains theoretically disputed.

---

# 42. Responsibility evidence battery

A serious ResponsibilityClaim should ask:

## R1 — Bearer/domain
Who exactly is claimed responsible, for what action/decision/outcome/domain?

## R2 — Route
Causal, role, agential, moral, accountability, liability, blame, remediation, forward-looking?

## R3 — Attribution
Was the relevant action/decision authored/settled/authorized by this bearer?

## R4 — Control
What practical/causal/preventive/override control actually existed?

## R5 — Epistemic position
What did the bearer know, predict, reasonably foresee, or have a duty/opportunity to know?

## R6 — Competence
Did the bearer possess the capacities required by the responsibility framework?

## R7 — Norm/duty
What standard, obligation, law or role applied?

## R8 — Coercion/constraint
Were authorship/autonomy/options materially compromised?

## R9 — Causal route
How did conduct contribute to the outcome, including intervention/deviation?

## R10 — Delegation topology
Who set goals/policy, recommended, decided, authorized, executed, monitored and could revoke?

## R11 — Forum/remedy
Who can call the bearer to account and what consequence/remedy exists?

## R12 — Evidence/provenance
What traces independently support the standing claim?

### G8-099
No single test determines every responsibility route.

---

# 43. Hard-case audit

## HC-G1 — Lightning causes fire
Causal contribution yes; agential/moral/blame responsibility absent. **PASS.**

## HC-G2 — Child accidentally breaks object
Causal contribution and action may exist; moral competence/blame depends on age/capacity/framework. **PASS:** agency/action ≠ full moral responsibility.

## HC-G3 — Malicious attempt fails
Intentional blameworthy action/attempt; no harmful outcome. **PASS:** blame/action responsibility ≠ outcome occurrence.

## HC-G4 — Careful actor causes unforeseeable harm
Causal contribution clear; culpability may be absent; repair/liability routes may still vary. **PASS.**

## HC-G5 — Negligent actor gets lucky
No harm occurs, but negligent conduct may remain blameworthy/role-defective. **PASS:** outcome luck ≠ conduct quality.

## HC-G6 — Foreseen but unintended side effect
Prediction/risk awareness yes, intention no; responsibility depends on duty/control/risk standard. **PASS.**

## HC-G7 — Coerced action
Authorship may remain while autonomy/blame is mitigated; framework-sensitive. **PASS.**

## HC-G8 — Physically forced movement
Bearer-level action authorship can fail; forcing actor has stronger authorship/responsibility route. **PASS.**

## HC-G9 — Omission with no duty/opportunity
No responsible omission merely from absence. **PASS.**

## HC-G10 — Lifeguard knowingly fails to rescue when able
Role duty + opportunity + knowledge + omission standing create strong responsibility candidate. **PASS.**

## HC-G11 — AI recommends unsafe action; human independently rejects
Recommendation responsibility may exist if advice negligent; no outcome responsibility for rejected action. **PASS.**

## HC-G12 — AI recommends; human rubber-stamps without meaningful information/veto
Displayed approval does not automatically establish meaningful human responsibility; architecture must expose epistemic/control deficits. **PASS.**

## HC-G13 — Delegated AI locally chooses harmful action under safe-looking broad policy
AI may have local agential/operational responsibility; human/institution responsibility depends on delegation, foreseeability, control and governance—not automatic total transfer or total retention. **PASS.**

## HC-G14 — Deterministic approval bot under institutionally valid rule
Operational/institutional Decision/Role responsibility possible; moral blame/personhood not entailed. **PASS.**

## HC-G15 — Bug introduced by developer, missed by reviewer, deployed by operator
Multiple causal/role/accountability routes coexist. **PASS:** responsibility not zero-sum.

## HC-G16 — Strict compensation regime after blameless accident
Liability/remediation standing can exist without moral culpability. **PASS.**

## HC-G17 — Organization blames `the algorithm`
If algorithm lacks the claimed blame competence while institution retains governance/accountability, attribution is responsibility laundering candidate. **PASS.**

## HC-G18 — Harm from genuinely unforeseeable learning-system behavior
Causal roles may be traceable while culpability is absent or disputed; forward governance/remediation responsibility can still remain. **PASS:** typed responsibility gap.

## HC-G19 — Beneficial outcome from accidental contribution
Causal contribution yes; full credit may be unwarranted. **PASS.**

## HC-G20 — Skilled action fails due bad luck
Action/decision quality may merit credit despite poor outcome. **PASS.**

---

# 44. Provisional ResponsibilityProfile v0

```text
ResponsibilityProfile = <
  Bearer/Role,
  Responsibility Object {
    Action?, Omission?, Decision?, Outcome?, Risk?, Domain?, Duty?
  },
  Standing Route {
    Causal?, Agential?, Action?, Outcome?, Role?, Forward?,
    Answerability?, Accountability?, Moral?, Credit?, Blame?,
    Liability?, Remediation?
  },
  Causal Contribution Route?,
  Authorship/Decision/Authorization Route?,
  Control Profile?,
  Authority Profile?,
  Epistemic Profile?,
  Foreseeability/Risk Awareness?,
  Competence?,
  Intention/SideEffect/Risk Relation?,
  Applicable Norm/Role/Duty?,
  Negligence/Recklessness?,
  Coercion/Compulsion/Excuse?,
  Delegation Topology?,
  Forum/Audience?,
  Remedy/Sanction/Correction Route?,
  Temporal/Retrospective/Forward Scope,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### G8-100
Responsibility profiles can be sparse: absence of moral blame does not erase causal/role/accountability fields.

---

# 45. Provisional AccountabilityProfile v0

```text
AccountabilityProfile = <
  Accountable Bearer,
  Domain/Event/Decision,
  Forum/Audience,
  Applicable Standard,
  Evidence/Trace Access,
  Explanation/Justification Requirement,
  Review Procedure,
  Challenge/Appeal Route?,
  Corrective/Remediation Power,
  Sanction/Consequence Route?,
  Authority/Role Basis,
  Temporal Horizon,
  Evidence/Provenance,
  Scope
>
```

### G8-101
Accountability is a relation/system of answerability and consequence, not an internal psychological property.

---

# 46. Revised AgencyStanding candidate v0.7

MF8-G does **not** add moral responsibility to the minimal AgencyStanding core.

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

Responsibility is attached as downstream/relational profiles:

```text
AgentialResponsibilityProfile
RoleResponsibilityProfile
AccountabilityProfile
MoralResponsibilityProfile
Liability/Remediation Profiles
```

### G8-102
**MoralResponsibilityStanding is NOT a universal constituent of minimal AgencyStanding.**

### G8-103
Agency can exist in bearers that are not appropriate moral blame targets.

### G8-104
Responsibility standings nevertheless depend on the earlier agency/action/decision/autonomy distinctions whenever they claim agential rather than merely causal/role responsibility.

---

# 47. Final MF8-G non-collapse stack

```text
Cause ≠ Responsibility
CausalContribution ≠ ActionAuthorship
CausalContribution ≠ Blame
CausalContribution ≠ Liability
```

```text
ActionResponsibility ≠ OutcomeResponsibility
AgentialResponsibility ≠ MoralResponsibility
RoleResponsibility ≠ Blame
ForwardResponsibility ≠ RetrospectiveBlame
```

```text
Answerability ≠ Responsibility
Accountability ≠ Responsibility
Accountability ≠ Punishment
BeingResponsible ≠ BeingHeldResponsible
```

```text
MoralResponsibility ≠ LegalLiability
Blame ≠ Liability
Liability ≠ Culpability
RemediationDuty ≠ Blameworthiness
```

```text
Knowledge ≠ Foreseeability
NoActualKnowledge ≠ NoResponsibility universally
Authority ≠ Responsibility
Control ≠ Responsibility
Agency ≠ ResponsibilityCompetence
```

```text
Intention ≠ Responsibility
Foreseen ≠ Intended
Unintended ≠ NotResponsible
Negligence ≠ Intent
Negligence ≠ BadOutcome
```

```text
Coercion ≠ NoResponsibility automatically
Compulsion ≠ Coercion
Justification ≠ Excuse
```

```text
Delegation ≠ TransferOfAllResponsibility
Delegation ≠ RetentionOfAllResponsibility
Recommendation ≠ Decision
NoDecisionStanding ≠ NoRecommendationResponsibility
```

```text
HumanInTheLoop ≠ MeaningfulHumanResponsibility
Traceability ≠ Accountability
ExplanationOutput ≠ AnswerabilitySatisfaction
```

```text
OperationalResponsibility ≠ MoralPersonhood
InstitutionalAccountability ≠ CollectiveAgency by identity
ResponsibilityGap ≠ one untyped gap
```

---

# 48. FoundationReopen audit

MF8-G attacks FRC-A1 through causation/control/responsibility relations.

No MF7 revision is required:

- causal contribution remains distinct from MF7 causal/dynamic structure and is enriched by responsibility route rather than redefining dynamics;
- responsibility-relevant control consumes MF7 ControlStanding plus MF8 source/authority/epistemic structure;
- omissions use MF8-B omission standing and MF7 opportunity/state/time rather than redefining state transitions;
- consequence responsibility layers normative attribution on causal history;
- accountability/liability are institutional/normative standings outside State/Dynamics/Control constitution.

MF3 also survives:

- explanations/traces/records are representations/evidence, not responsibility itself;
- analyst attribution remains distinct from target responsibility standing.

### G8-105
**FRC-A1 is NOT triggered.**

### G8-106
No MF0–MF7 FoundationReopenCondition is currently demonstrated.

---

# 49. Evidence anchors

Primary/authoritative anchors used in MF8-G:

1. **John Martin Fischer & Mark Ravizza (1998), `Responsibility and Control: A Theory of Moral Responsibility`, Cambridge University Press, DOI `10.1017/CBO9780511814594`.** Guidance control, reasons-responsiveness, mechanism ownership/history, action/consequence/omission responsibility; a major rival model showing moral responsibility need not require regulative control/alternative possibilities.
2. **P. F. Strawson (1962), `Freedom and Resentment`, Proceedings of the British Academy 48.** Reactive-attitudes/interpersonal route to moral responsibility; used to separate blame/holding responsible from causal attribution.
3. **H. L. A. Hart & Tony Honoré (1959/1985), `Causation in the Law`.** Foundational legal-philosophical treatment of causal attribution, intervening agency and legal responsibility; used to keep causal contribution distinct from liability/normative attribution.
4. **Michael S. Moore (1999), `Causation and Responsibility`, in Responsibility, Cambridge University Press, DOI `10.1017/CBO9780511524103.002`.** Legal responsibility routes in which causation is relevant to liability while remaining conceptually distinct from the whole liability judgment.
5. **Helen Nissenbaum (1996), `Accountability in a Computerized Society`, Science and Engineering Ethics 2.** Classic analysis of how computerization/delegation can obscure responsibility/accountability; used to distinguish traceability, answerability and accountable institutional structure.
6. **Andreas Matthias (2004), `The Responsibility Gap: Ascribing Responsibility for the Actions of Learning Automata`, Ethics and Information Technology 6(3), DOI `10.1007/s10676-004-3422-1`.** Canonical AI responsibility-gap argument centered on unpredictability/limited control of learning automata; treated as a live challenge, not a settled conclusion.
7. **Filippo Santoni de Sio & Giulio Mecacci (2021), `Four Responsibility Gaps with Artificial Intelligence: Why they Matter and How to Address them`, Philosophy & Technology 34, DOI `10.1007/s13347-021-00450-x`.** Distinguishes culpability, moral-accountability, public-accountability and active/forward-responsibility gaps; supports replacing one monolithic `responsibility gap` with typed gap routes.
8. **Daniel W. Tigard (2021), `There Is No Techno-Responsibility Gap`, Philosophy & Technology 34, DOI `10.1007/s13347-020-00414-7`.** Rival position rejecting a technology-specific responsibility gap; retained to prevent MF8-G from assuming Matthias's pessimistic conclusion.

MF8-G deliberately preserves disagreement among moral responsibility, legal responsibility and AI responsibility-gap theories. The objective is a typed ontology capable of representing the rival models and their evidence, not choosing one moral/legal doctrine as a universal foundation.

---

# 50. MF8-G verdict

The deepest reconstruction is:

```text
CAUSAL CONTRIBUTION
 = part of how an outcome happened

AGENTIAL RESPONSIBILITY
 = conduct/decision attributable to an agent in a responsibility-relevant way

ROLE / FORWARD RESPONSIBILITY
 = assigned stewardship/duty over a domain

ANSWERABILITY
 = duty to explain/justify/provide evidence

ACCOUNTABILITY
 = institutional/social relation of answerability, review and consequence/remedy

MORAL RESPONSIBILITY
 = appropriateness of moral holding-responsible under a declared framework

BLAME / CREDIT
 = fitting negative/positive appraisal

LIABILITY
 = legal/institutional exposure to recognized consequence/remedy

REMEDIATION DUTY
 = obligation to repair/mitigate/compensate/correct
```

The decisive consequences are:

> **Causation does not allocate responsibility by itself. The actor nearest the harmful effect can differ from the author, principal, decision-maker, authorizer, accountable institution and liable party.**

> **Responsibility is not zero-sum. Distributed systems can contain multiple simultaneous responsibility standings; fragmentation must not automatically dilute all responsibility to zero.**

> **A non-conscious artificial agent can have causal, agential, operational and role responsibility standings without thereby becoming a moral person or fitting target of blame.**

> **Human oversight does not magically restore responsibility. Meaningful responsibility requires actual authority, information, alternatives, control, competence and time to intervene. A decorative approval step can instead launder responsibility.**

> **`Responsibility gap` must be typed. A culpability gap, accountability gap, liability gap and remediation gap are different failures and may coexist or diverge.**

Responsibility therefore enters MF8 not as a constituent required to make something an agent, but as a layered attribution/governance structure built on top of action, decision, autonomy, epistemic and institutional standings.

---

# 51. Next frontier

Proceed directly to:

```text
MF8-H — Collective Agency, Joint Action & Institutional Agency
```

Primary questions:

1. What makes a plurality a collective bearer rather than merely a collection?
2. JointActionStanding ≠ CollectiveAgencyStanding—what additional integration is required?
3. Can collective agency exist without every member sharing the same goal, belief or intention?
4. What is collective decision standing relative to aggregation, voting, delegation and authority?
5. When do institutional goals/norms belong to the organization rather than merely to members?
6. How should distributed memory, policy, authority and action source compose into a group-level agent?
7. Can collective agency survive member turnover?
8. What distinguishes swarm coordination from collective agency?
9. What distinguishes a corporation, committee, market, crowd, team and multi-agent system?
10. How do individual and collective agency/responsibility coexist without double counting or erasing either level?

MF0–MF7 remain frozen unless a named concrete FoundationReopenCondition is demonstrated.
