# Ordivon Capital R3 — Personal Resource Office Architecture Spec

Date: 2026-09-29
Standing: **DRAFT_R3_DESIGN_NOT_AUTHORITY**
Base revision: `71ef659fdb40dcfa32ad688c0e308d388a828188`

This document is a design specification. It does not widen provider, credential, financial-write, procurement, account, legal, tax, or owner authority.

## 1. Re-anchored purpose

Ordivon Capital is the Ordivon umbrella for governing scarce resources and capital across their lifecycle. The current seven Python source-owner packages (`markets`, `trading`, `portfolio`, `risk`, `research`, `governance`, `accounting`) are the instantiated financial subset, not the complete conceptual scope of Capital.

R3 therefore distinguishes:

```text
Capital umbrella semantics
    !=
current Capital Python source-owner packages
    !=
natural reality owners of the underlying resources
```

Capital owns cross-resource governance semantics where no more natural owner exists: objectives, mandates, constraints, allocation requests, risk-budget binding, cross-resource counterfactuals, authority/evidence bindings, effect ordering, reconciliation expectations, performance attribution boundaries and institutional learning.

Capital does **not** become the physical owner of every resource. Workstation/Runtime owns compute reality, providers own account/order/cloud/service reality, Host owns semantic continuity, and domain-native authorities retain their own truth.

## 2. R3 architectural equation

```text
Ordivon Capital R3
= Personal Resource Office institutional topology
+ Resource / liability / commitment / goal semantics
+ existing 12 functional Capital LEGO waist
+ Constitution / delegation / risk-budget bindings
+ cross-resource allocation and opportunity-cost semantics
+ authority / evidence / effect / reconciliation seams
+ performance / attribution / assurance semantics
```

The Personal Family Office is the primary organizational reference pattern, not a claim that Ordivon is a legally constituted family office in any jurisdiction.

## 3. Non-goals

R3 does not:

1. create empty `human/`, `compute/`, `treasury/` or similar Python packages solely to mirror a conceptual taxonomy;
2. collapse Workstation, Runtime, Host, Social, Research, Company, Network or provider owners into Capital;
3. require every resource to be monetized or marked to market;
4. infer owner preferences, risk appetite or legal/tax conclusions from model output;
5. turn an Agent role, model, tool and authority into one identity;
6. introduce a new custom optimizer when a qualified mature solver can own the mechanics;
7. widen live or production effect authority;
8. treat local ledgers, workflow completion or model output as external reality.

## 4. Six orthogonal maps

Every Capital decision is projected across six independent maps. They MUST NOT be collapsed into one taxonomy.

### 4.1 Resource map — what is scarce

First-class `CapitalResource` categories are semantic classes, not necessarily accounting assets:

- `OWNED_ASSET` — transferable or controllable owned property;
- `FINANCIAL_CLAIM` — cash, security, receivable, credit or other financial claim;
- `CAPACITY` — bounded productive capability such as compute or task capacity;
- `RIGHT` — contractual or provider-backed right to use or receive something;
- `OPTION` — preserved future choice or contingent right;
- `KNOWLEDGE` — reusable evidence-backed methods, research or intellectual capital;
- `INFRASTRUCTURE` — productive systems and durable operating capability;
- `TIME` — bounded schedulable time capacity;
- `ATTENTION` — bounded non-storable decision/work capacity;
- `SERVICE_ENTITLEMENT` — API, SaaS, cloud or external-service allowance;
- `RELATIONSHIP_ACCESS` — non-owned access/collaboration capability; never modeled as ownership of a person.

A first-class resource requires identity, natural owner, authority reference, evidence, lifecycle and allocation semantics. It does **not** require a monetary market value.

### 4.2 Functional LEGO map — what operation is performed

The existing R2 waist remains canonical:

`Observe -> Normalize -> Validate -> Measure -> Model -> Counterfactual -> Decide -> Authorize -> Reserve -> Effect -> Reconcile -> Account`

R3 does not add Office names as new functional LEGO roles.

### 4.3 Institutional role map — who is responsible

The Personal Resource Office is organized as durable institutional roles that may be staffed by one or more temporary/persistent Agents:

- Governing Body / Principal;
- Capital Allocation Committee;
- Chief Capital Office;
- Research Office;
- Portfolio & Resource Allocation Office;
- Risk Office;
- Treasury & Liquidity Office;
- Effect / Execution Office;
- Controller / Accounting Office;
- Performance & Attribution Office;
- Model & Data Governance Office;
- Compliance / External Professional Liaison;
- Independent Assurance / Internal Audit.

`Office != Agent != Model != Tool != Authority`.

### 4.4 Authority map — who may decide or assert

Authority classes remain separated:

- `OWNER_PRINCIPAL` / Governing Body — values, objectives, mandate, explicit appetite and delegation;
- Capital Governance — policy/admission within delegated scope;
- Agent Office — analysis, proposal, review or bounded delegated action;
- Runtime — physical execution evidence only;
- natural Resource Owner / Provider — external or domain reality;
- External Professional Authority — jurisdiction-specific legal/tax/regulated advice where required;
- Independent Assurance — assurance verdict, not operating authority.

No lower layer may mint a higher layer's authority.

### 4.5 Truth map — which reality is authoritative

- `PREFERENCE_TRUTH` — explicit Principal Constitution and mandate;
- `DECISION_TRUTH` — frozen evidence, assumptions, state and decision record;
- `OPERATIONAL_TRUTH` — Runtime/Host/local accounting mechanical state;
- `RESOURCE_REALITY` — natural owner/provider current state;
- `EXTERNAL_EFFECT_REALITY` — provider/custodian/vendor/broker authoritative effect state.

Local accounting and operational success never replace resource/provider reality.

### 4.6 Lifecycle map — where the resource is in time

`Discover -> Understand -> Plan -> Allocate -> Authorize -> Effect -> Operate -> Monitor -> Reconcile -> Measure -> Learn -> Retire/Reallocate`

## 5. Resource, obligation and objective objects

R3 MUST distinguish at least five object families:

### 5.1 ResourceRecord

Minimum semantic fields:

```text
resourceId
resourceClass
naturalOwner
authorityRef
state
quantityOrCapacity
availability
liquidity
criticality
substitutability
reversibility
valuationMode
valuation
valuationConfidence
dependencies
encumbrances
observationTime
validUntil
evidenceDigest
```

`valuationMode` is one of:

- `PRICEABLE`;
- `ESTIMABLE`;
- `ORDINAL_ONLY`;
- `NON_MONETIZABLE`;
- `NOT_REQUIRED`.

### 5.2 LiabilityRecord

Represents explicit future obligations or economic liabilities. A liability is not a negative ResourceRecord.

### 5.3 CommitmentRecord

Represents already-made commitments that constrain future capacity or liquidity: subscriptions, contracts, reserved compute, capital calls or other bounded commitments.

### 5.4 ConstraintRecord

Represents hard or soft boundaries: liquidity floors, prohibited instruments, deadlines, legal/provider limits, safety envelopes, availability constraints or dependency constraints.

### 5.5 GoalRecord

Represents desired outcomes with horizon, priority, required resource classes, success evidence and optional deadline. Goals are not automatically reduced to monetary return.

## 6. Capital Constitution

The R3 Constitution is the owner-governed semantic template for:

- purpose and objectives;
- protected resources / non-negotiable floors;
- explicit preferences and prohibitions;
- risk appetite;
- delegation and autonomy levels;
- approval thresholds;
- escalation rules;
- effect-class permissions;
- review/revalidation cadence;
- continuity/succession policy.

The semantic reference is the mature Investment Policy Statement / investment-governance pattern, generalized beyond financial portfolios. Capital retains only Ordivon authority bindings and exact machine-readable constraints.

### 6.1 Risk Capacity != Risk Appetite != Risk Budget

- `RiskCapacity` is evidence-derived ability to absorb loss or disruption given resources, liabilities, commitments, liquidity and dependencies.
- `RiskAppetite` is explicit Principal preference and MUST NOT be silently inferred from behavior, model output or a single requested action.
- `EffectiveRiskBudget` is the intersection of capacity, appetite, hard constraints and strategy/resource-specific limits.

`UNSET` appetite or delegation MUST fail closed for effect classes requiring them. `UNSET` never means unlimited.

## 7. Delegation levels

R3 standardizes capability delegation independently of Agent persona:

- `L0_OBSERVE` — read authoritative state;
- `L1_ANALYZE` — measure/model/counterfactual;
- `L2_RECOMMEND` — propose options with evidence and invalidators;
- `L3_PREPARE` — prepare frozen decision/effect intent, no external effect;
- `L4_EXECUTE_BOUNDED` — execute only inside explicit Constitution + policy + credential/provider scope;
- `L5_CHANGE_CONSTITUTION` — Principal/Governing Body authority only unless a separately explicit constitutional delegation exists.

No ordinary Agent role receives `L5` by role name.

## 8. Three Lines institutional control

R3 adopts the Three Lines governance pattern as a reference topology:

### First line — operating allocation/effect

Chief Capital, Research, Allocation, Treasury, Trading/Procurement/Effect and operating resource offices.

### Second line — risk/control

Risk, policy, compliance, model risk and data governance. Second line may block or escalate first-line proposals under the Constitution but cannot rewrite the Principal's preferences.

### Third line — independent assurance

Independent Audit / Assurance tests whether mandates, evidence, controls, reconciliation, accounting and reporting were followed. It does not originate the operating transaction it audits.

Independence is a contract property, not a prompt persona.

## 9. Maker-checker and role-conflict rules

Sensitive effects SHOULD bind separate Maker, Checker and Effect Owner identities. At minimum:

```text
Proposal/Maker
    -> independent Checker
    -> Policy/Authority Gate
    -> Effect Owner
    -> Provider Reality
    -> independent Reconcile/Account
```

Required conflict rules include:

- model developer cannot be the sole model validator;
- proposal owner cannot approve its own risk exception;
- effect executor cannot establish provider truth from its own send/ack;
- reconciliation must use authoritative observation independent of the original effect claim;
- independent assurance cannot be the operating owner of the audited action.

High-risk effect classes may require multiple independent approvals; R3 does not use majority vote to override a role with explicit veto authority.

## 10. Agent-office semantics

An Office is a durable mandate and authority profile. Agents are workers bound to an Office role for a task/run. A committee is an authority topology, not Agent democracy.

For material ambiguous decisions, R3 SHOULD support:

1. role-specific evidence packets;
2. independent initial judgments;
3. frozen pre-discussion verdicts;
4. explicit conflict representation;
5. aggregation only after independence is preserved;
6. escalation according to Constitution and veto rights.

Consensus is not required. Disagreement is evidence.

## 11. Cross-resource Capital Allocation Committee

The committee operates on `CapitalRequest` objects that compete for scarce resources across domains, for example financial capital, compute, external services, time and attention.

A request MUST include:

- objective / GoalRef;
- requested resource classes and amounts/capacity;
- horizon and deadline;
- alternatives including `DO_NOTHING` / preserve optionality when meaningful;
- expected benefits without requiring monetary reduction;
- costs and commitments;
- reversibility;
- dependencies;
- risk-capacity impact;
- evidence/currentness;
- required effect class and authority.

The committee does not hand-write optimization algorithms. For formally optimizable assignment/scheduling/constraint problems, OR-Tools or another qualified mature solver is the default candidate owner. Ordivon owns semantic lowering, constraints, evidence and interpretation, not solver internals.

## 12. Opportunity-cost semantics

R3 evaluates an opportunity against its feasible alternative set, not only in isolation.

A valid `OpportunitySet` MAY contain heterogeneous options whose value is multi-dimensional. Monetary NPV is one signal, not a universal objective function. The decision record MUST preserve non-monetized criteria where they are decision-relevant.

## 13. Treasury and liquidity

Treasury is a distinct institutional role, not synonymous with investing. Its semantics include:

- liquidity reserves and runway;
- upcoming liabilities and commitments;
- funding and collateral needs;
- currency and payment timing;
- recurring subscriptions and capital calls;
- resource-specific capacity floors.

A high-return opportunity cannot consume resources needed for a protected near-term liability merely because its expected return is higher.

## 14. Asset/resource lifecycle management

For durable assets and infrastructure, ISO 55001:2024 is the external reference pattern for balancing performance, risk and expenditure across the asset lifecycle. Capital does not claim ISO certification.

For technology/cloud resources, FinOps Framework Allocation and workload-placement practices are reference patterns for ownership metadata, allocation, shared-cost treatment, budgeting, utilization and cost-aware placement. Physical cloud/compute reality remains with providers/Workstation/Runtime.

## 15. Risk management

ISO 31000:2018 remains the current generic risk-management reference while the third edition is still under development. R3 uses the generic sequence and principles proportionately rather than inventing a Capital-specific universal risk methodology.

Risk treatments may include:

`ACCEPT / AVOID / REDUCE / DIVERSIFY / HEDGE / INSURE / TRANSFER / CONTINGENCY`.

Risk Office is therefore not merely a blocking service.

## 16. Data, lineage and evidence

BCBS 239 remains the proportionate reference for source identity, accuracy, completeness, timeliness, aggregation, lineage and ad-hoc reporting. No bank-regulatory compliance claim is made.

Every material cross-resource claim SHOULD bind:

```text
claimId
producer / natural owner
claim type
observation time
validity deadline
evidence digest
lineage / source identity
confidence or quality standing
```

Agent memory alone is not current resource truth.

## 17. Performance, attribution and learning

GIPS Asset Owner standards are the reference for disciplined investment performance reporting and independent verification in the financial subset. R3 generalizes the separation of outcome, attribution and assurance to non-financial resources without pretending that GIPS directly governs compute/time/knowledge resources.

R3 preserves:

- outcome != decision quality;
- profit != skill;
- successful project outcome != proof of one causal resource decision;
- hypothetical/backtest/model results != realized external outcome;
- future observations cannot rewrite the frozen decision boundary.

## 18. Generalized effect taxonomy

The existing invariant remains:

`Authorize -> Reserve -> Effect -> Observe -> Reconcile -> Account`

R3 may later extend admitted non-live effect classes beyond trading to examples such as:

- `PURCHASE`;
- `SUBSCRIBE`;
- `TRANSFER`;
- `ALLOCATE_RESOURCE`;
- `RESERVE_CAPACITY`;
- `LEASE`;
- `HIRE_SERVICE`;
- `CANCEL_COMMITMENT`;
- `SELL_ASSET`;
- `REBALANCE`.

This list is taxonomy design only. No new live external effect is admitted by this spec.

## 19. Current R2 -> R3 mapping

| Current R2 owner | R3 standing |
| --- | --- |
| Markets | retained financial Resource Reality observation owner |
| Trading | retained financial private/provider reality + execution/effect owner |
| Portfolio | retained bounded counterfactual seam; future cross-resource allocation semantics remain outside until qualified |
| Risk | retained financial measurement/risk-budget evaluation owner; generalized capacity/risk semantics require new contracts |
| Research | retained model/evidence validation owner |
| Governance | retained financial policy/admission owner; future Constitution/delegation binding is the natural extension |
| Accounting | retained financial local reservation/post/void owner; general Resource Ledger requires separate design and must not falsify physical reality |

The 12 functional LEGO roles remain unchanged.

## 20. External-owner adoption map

R3 follows `DELETE-CUSTOM-BY-DEFAULT`:

- owner objectives, constraints, discretionary authority and IPS semantics -> CFA private wealth / investment-governance patterns;
- investment performance presentation / independent verification -> GIPS Asset Owner / Verifier patterns for the financial subset;
- organizational accountability / independent assurance -> IIA Three Lines Model;
- dual control / segregation of duties -> Basel operational-risk control pattern;
- generic risk process -> ISO 31000;
- durable asset lifecycle management -> ISO 55001:2024;
- risk-data lineage/quality -> BCBS 239;
- cloud/technology allocation -> FinOps Framework;
- formal assignment/scheduling/resource optimization -> OR-Tools or another qualified solver;
- provider/resource truth -> natural provider/owner APIs and records.

Ordivon retains only cross-owner authority/evidence/reconciliation/composition seams and exact qualification evidence.

## 21. Implementation waves

### W0 — Currentness and invariants

- fence current main and current Capital contracts;
- freeze current R2 behavior and 12 functional LEGO waist;
- no authority widening.

### W1 — Semantic schemas, read-only

Introduce draft machine schemas/registries for Resource, Liability, Commitment, Constraint and Goal. No provider writes and no new empty source-owner packages.

### W2 — Constitution / delegation / risk-capacity

Implement explicit Constitution and delegation records. Add evidence-derived risk capacity as distinct from explicit appetite. Preserve current financial `UNSET` fail-closed behavior until migration is accepted.

### W3 — Institutional role topology

Bind Office roles, Three Lines, maker-checker conflicts and veto/escalation semantics into Composition/Host/Agent Birth contracts. Reuse generic orchestration; Capital owns only financial/resource semantics.

### W4 — Cross-resource counterfactual and allocation

Implement read-only `CapitalRequest` / `OpportunitySet` / counterfactual reports. Qualify OR-Tools or another mature optimizer only for problems with explicit objective/constraints; do not convert qualitative values into fake monetary utility.

### W5 — Treasury / liability / commitment

Introduce cross-resource liquidity/capacity floors and future obligations so allocation cannot consume protected resources.

### W6 — Generalized non-live effects

Extend effect taxonomy only in simulated/sandbox lanes with Reserve/Observe/Reconcile/Account fault matrices. Live/provider writes require separate owner-authority graduation.

### W7 — Performance / attribution / assurance

Separate realized outcome, attribution, process quality and independent assurance; add periodic governance audit.

### W8 — Provider-specific graduation

Only after explicit Principal/provider/credential/legal authority events. No R3 architecture acceptance implicitly grants production authority.

## 22. Acceptance invariants

R3 is unacceptable if any of the following occur:

1. a conceptual Resource class creates a fake physical source owner;
2. an Agent infers owner appetite or L5 constitutional authority;
3. a second-line control becomes the sole first-line effect owner for the same action;
4. an audit verdict is treated as provider/resource reality;
5. monetary valuation becomes mandatory for non-monetizable resources;
6. a solver output is treated as preference truth or effect authority;
7. an UNKNOWN external effect is blindly replayed;
8. a ledger or Runtime result substitutes for provider/resource truth;
9. a local custom optimizer is added where a qualified mature owner fits the exact contract;
10. R3 migration silently widens live financial or procurement authority.

## 23. Reference standing

External standards/frameworks are reference owners or candidate mechanic owners only. Applicability and compliance remain separate questions. R3 must record exact version/currentness and cannot turn a reference framework into legal/regulatory applicability by configuration.
