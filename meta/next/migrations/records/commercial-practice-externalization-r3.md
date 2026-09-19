# Commercial Practice Externalization R3

Date: 2026-09-19
Role: migration/currentness record, not an Ordivon commercial framework.

## Scope

R3 externalizes four remaining business-operations red zones:

- customer contracting / contract lifecycle;
- operating financial planning and budget control;
- payroll records/processing;
- customer support/helpdesk.

## Contracting

Do not create an `Ordivon Contract Lifecycle`.

Use:

- the **WorldCC / CCM Institute Contract Management Standard (Fourth Edition)** as a voluntary professional lifecycle reference when structured contract management adds value;
- applicable law and qualified legal counsel for legal interpretation, drafting risk and enforceability;
- customer-approved terms/SOW/order as the actual bilateral commitment;
- ERPNext Quotation / Sales Order / Invoice records where they naturally own commercial transaction facts.

The professional standard can structure pre-award, award and post-award work. It cannot turn an unsigned draft or ERP record into a legally binding agreement.

For the first small technical-service engagements, keep the document set minimal: proposal/quotation + exact scope/deliverables + exclusions/assumptions + price/payment + change/acceptance + IP/confidentiality/liability/termination terms as actually needed. Buy legal review rather than growing a private contract engine.

## FP&A / operating finance

There is deliberately no `Ordivon FP&A Lens`.

For the current small-company stage:

- actual accounting truth -> ERPNext submitted ledger records and bank/provider reconciliation;
- approved spending plan -> ERPNext Budget when a real budget exists;
- plan-vs-actual -> ERPNext Budget Variance;
- project economics -> provider-native project profitability / actual time and non-labour cost evidence;
- cash movement -> ERPNext Cash Flow / bank facts;
- prospective runway/forecast -> a small task-local forecast from current cash, committed receivables/payables, known recurring costs and explicitly stated assumptions.

A historical cash-flow report is not a cash-flow forecast. A Budget is not money in the bank. Do not activate a heavier FP&A product until recurring multi-scenario/department/entity planning or consolidation proves a distinct need.

## Payroll / employment operations

Do not create a payroll engine or employment ontology.

When the first real employee exists:

- employment legality, mandatory terms, tax, social insurance and statutory filings -> applicable government rules plus qualified/local payroll/accounting/legal provider;
- employee/payroll operational records -> Frappe HR only if it reduces real record/processing friction;
- bank/payment effect -> bank/provider-native evidence;
- payroll accounting -> ERP/accounting records after reconciliation.

Frappe HR payroll configuration is provider behavior, not jurisdictional legal authority.

## Support / helpdesk

Do not create `Ordivon Ticket`, `SupportState` or a private SLA engine.

Use:

- direct founder/customer communication while ticket volume is tiny;
- Frappe Helpdesk when shared durable ticket/SLA/customer-portal/knowledge-base state has real coordination value;
- ISO 10002 when an actual complaint requires complaint-handling discipline;
- ISO/IEC 20000-1 only when the business is genuinely operating a service-management system where its requirements are applicable.

A support ticket is not automatically a complaint, and a green SLA is not proof that the customer outcome is satisfactory.

## Activation rule

All four areas remain demand-gated.

```text
real commitment / budget / employee / support load
  -> identify natural legal/professional/provider owner
  -> activate minimum mature surface
  -> reconcile provider state with the real-world effect
  -> automate only after repeated workload appears
```

No new local methodology is admitted without measured repeated substitution failure.
