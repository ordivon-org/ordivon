---
name: enterprise-work
description: Thin router for consequential multi-step/customer/business/cross-domain work. Bind the exact work and acceptance authority, discover current external authorities, route each responsibility to its natural mature owner, and verify the real outcome. Do not use this Skill as an Ordivon management methodology or universal workflow.
compatibility: Requires access to the relevant work/source files and whichever external/domain providers the selected work actually needs. Currentness-sensitive authority claims require official-source checks.
metadata:
  source-authority: external-routing-adapter
  standards-environment: standard-native-enterprise-environment-r2
---

# Enterprise work — thin external router

This Skill owns **routing only**.

It does not define an Ordivon work lifecycle, business methodology, project method, sales method, pricing method, risk method, quality system, legal process, HR process, procurement process, or acceptance ontology.

## 1. Activate only when consequence justifies it

Use this router when one or more of these are material:

- a customer/counterparty commitment;
- multiple domains/providers must coordinate;
- explicit acceptance/quality evidence matters;
- legal, contractual, standards or platform obligations constrain the work;
- production/security/privacy/financial/external effects exist;
- durable handoff, auditability, rollback or repeated operation matters.

For a small reversible local edit, use the narrow domain Skill/provider directly.

## 2. Bind only the task-local facts

Before consequential action, identify the minimum facts needed to route correctly:

- exact subject/input identity;
- intended deliverable/outcome;
- scope, exclusions and assumptions;
- acceptance authority and acceptance criteria;
- authorization/permitted effects;
- material external obligations/currentness;
- material risks only when consequence warrants explicit treatment.

These are task facts, not fields in a universal Ordivon Work schema.

## 3. Resolve external authorities before inventing method

When a mature authority/practice may apply:

1. query the Authority Catalog with `scripts/authority_catalog.py find`;
2. inspect the exact record with `show`;
3. check the official source when freshness/scope matters;
4. bind/exclude/defer it in the current task only;
5. keep currentness separate from compliance, verification and acceptance.

The Catalog is discovery metadata, not an applicability engine.

Do not copy licensed standards into local instructions.

## 4. Route each responsibility to its natural owner

| Need | Natural owner / mature candidate |
| --- | --- |
| bounded quality/delivery planning | ISO 10005 when a quality plan adds value |
| project-shaped management | ISO 21502; use only the practices needed by the real project |
| material risk | ISO 31000 concepts in the natural project/domain record |
| management-system audit | ISO 19011 when an actual audit objective exists |
| company strategy choices | Roger Martin Strategy Choice Cascade as a choice structure + company-specific market evidence |
| early startup/customer discovery | YC / Lean Startup / Strategyzer as advisory practice + real customer evidence |
| early B2B sales | YC early-stage sales guidance + founder-led buyer evidence |
| lead/deal CRM | current CRM provider; evaluate Frappe CRM for new pipeline work |
| quotation/order/invoice/accounting/project/ERP-quality facts | ERPNext/Frappe where native |
| SaaS pricing/packaging | Stripe SaaS guidance when the product is actually SaaS-like + real market evidence |
| service pricing | quotations, negotiation, paid pilots and measured delivery economics |
| satisfaction monitoring | ISO 10004 when useful + customer behavior/feedback |
| complaint handling | ISO 10002 when a real complaint exists |
| recruitment | ISO 30405 + applicable employment law/professional providers |
| supplier/RFQ/PO/purchase-invoice facts | ERPNext Buying or another natural purchasing provider |
| sustainable procurement | ISO 20400 when sustainability is material |
| material outsourcing | ISO 37500 |
| customer contract lifecycle | WorldCC Contract Management Standard when structured contract management adds value + applicable law/legal counsel + actual signed/accepted customer terms |
| operating budget / variance | ERPNext Budget and Budget Variance against real ledger/project facts; keep prospective forecasts task-local until recurrence justifies a dedicated FP&A provider |
| payroll records/processing | applicable law + qualified/local payroll/accounting provider; Frappe HR only when real employees make provider-native payroll records useful |
| customer support / helpdesk | direct founder communication while tiny; Frappe Helpdesk when durable ticket/SLA/portal/KB state has real value; ISO/IEC 20000-1 only for an applicable service-management system |
| heavyweight collaborative work management | Plane/OpenProject only after measured need |
| stable prescriptive business process | BPMN/Flowable when executable process semantics add value |
| adaptive managed case | CMMN/Flowable when real case semantics add value |
| stable repeatable decision table | DMN/Flowable |
| machine-enforceable admission/policy | OPA/Rego |
| durable technical orchestration | Temporal |
| recurring SaaS/API/event integration | n8n |
| scientific/data DAG | domain workflow such as Snakemake |
| exact local mechanical execution evidence | Ordivon Runtime when its contract materially helps |
| open-ended reasoning/implementation | task-selected Agent + domain method |
| semantic outcome acceptance | real customer/domain/external acceptance authority |

Provider state is authoritative only for that provider's responsibility.

## 5. Commercial currentness rules

Do not create Ordivon-native Strategy, Sales, GTM, Pricing, Customer-Success, Contracting, FP&A, Payroll, Support, Hiring or Procurement frameworks.

Current provider boundary:

- ERPNext v16 acceptance proves the tested transactional/accounting slice.
- Frappe currently documents ERPNext's built-in CRM workspace as scheduled for removal in v17; do not accumulate new long-term CRM dependence there.
- Frappe CRM is a candidate for the first real pipeline, not something to deploy merely because it exists.
- ERPNext Buying/Frappe HR remain dormant until real procurement/hiring workloads justify them.

For pre-PMF work, keep the founder/decision owner exposed to the evidence needed for learning: buyer conversations, price objections, problem selection, acceptance interpretation and product trade-offs. Agents and suppliers may execute bounded work; they must not hide the evidence needed to decide whether the business should exist.

## 6. Execute through the selected owner

Use the thinnest mature capability that can produce the required effect.

Before consequential writes, confirm target, authorization, scope, identity/credentials, reversibility and evidence path. Apply least privilege where practical.

Do not infer semantic success from mechanical success:

```text
ERP/CRM record exists       != customer demand or acceptance
BPMN process ended          != real business outcome achieved
Temporal workflow closed    != external Activity effect valid
n8n execution green         != target system state correct
Runtime exit 0              != semantic completion
Agent says done              != acceptance
playbook completed           != market truth
```

## 7. Verify with the real authority

For each material acceptance criterion, use the domain/customer/provider/legal/venue authority that can actually establish the claim.

Preserve partial/open/external-assertion/currentness states instead of manufacturing a global PASS.

Historical evidence is append/supersede, not rewrite.

## 8. Keep local residue thin

Retain only:

- task-local scope/acceptance/configuration;
- provider/domain evidence references;
- company/project-specific decisions;
- measured lessons that affect future provider selection.

Do not turn successful one-off work into a new Ordivon methodology by default.

A new local abstraction is admissible only after repeated measured substitution failure in mature external methods/providers.

## References to load only when needed

- External authority/currentness/evidence boundary: `../../../docs/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md`
- Company-specific strategy facts/open choices: `../../../docs/COMMERCIAL_STRATEGY_CURRENT_FACTS_R1.md`
- Detailed provider/currentness and historical dogfood map: `../../../docs/ENTERPRISE_OPERATING_MODEL_R1.md`
- Current capability/provider coverage: `../../../docs/CAPABILITY_PACKAGES_R1.md`
- Commercial migrations: `../../../migrations/records/commercial-practice-externalization-r1.md`, `commercial-practice-externalization-r2.md`, `commercial-practice-externalization-r3.md`, and `commercial-strategy-debt-externalization-r1.md`

For artifact production/verification, activate `artifact-work` instead of duplicating artifact-family procedure here.
