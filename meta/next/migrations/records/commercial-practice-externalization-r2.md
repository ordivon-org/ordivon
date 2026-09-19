# Commercial Practice Externalization R2

Date: 2026-09-19
Role: migration/currentness record, not an Ordivon commercial methodology.

## Scope

R2 externalizes the next commercial red zones after customer discovery/business-model work:

- founder-led / early B2B sales;
- pricing and packaging;
- CRM provider ownership;
- customer satisfaction and complaints;
- recruitment;
- procurement and supplier records.

## External/native ownership

| Need | Adopted owner/reference | Boundary |
| --- | --- | --- |
| founder-led early sales | Y Combinator — How to Sell | advisory method; real buyer interaction and closed/lost deals are evidence |
| CRM pipeline | evaluate Frappe CRM for new pipeline work | provider state only; CRM does not prove demand or acceptance |
| ERP transactional selling/accounting | ERPNext/Frappe | Quotation/Sales Order/Sales Invoice/GL remain provider-native business facts |
| SaaS pricing/packaging | Stripe current SaaS pricing/packaging guidance | applies only when the product is SaaS-like; not a universal pricing standard |
| service pricing | real quotations, negotiation, paid pilots and delivery economics | market evidence is primary; no new local pricing Lens |
| customer satisfaction | ISO 10004:2018 | monitoring/measurement guidance, not a Customer Success score |
| complaint handling | ISO 10002:2018 | activate on real complaints |
| recruitment | ISO 30405:2023 + applicable law/professionals | no hiring workflow before a real hire |
| procurement records | ERPNext Buying or another natural purchasing provider | supplier/RFQ/PO/invoice truth remains provider-native |
| sustainable procurement | ISO 20400:2017 | activate only when sustainability is material |
| outsourcing | ISO 37500:2014 | material outsourcing relationships only |

## CRM provider succession

The 2026-09-13 ERPNext v16 acceptance proved a representative Opportunity and transactional/accounting chain. That evidence remains valid for the exact tested version and records.

Current Frappe documentation now says ERPNext's built-in CRM workspace is scheduled for removal in version 17 and recommends evaluating Frappe CRM for a new CRM implementation.

Therefore the migration policy is:

```text
historical ERPNext CRM proof
    != permanent CRM architecture

first real sales pipeline
    -> test current Frappe CRM against the founder-led workflow
    -> activate only if it reduces real coordination/record friction

accepted quotation/order/invoice/accounting semantics
    -> remain ERPNext-native where still supported
```

No synthetic CRM migration is justified before a real pipeline exists.

## Pricing boundary

There is deliberately no `Ordivon Pricing Framework`.

For the near-term technical-service business, pricing evidence should come from:

- offered scope and price;
- buyer response / objection;
- accepted or rejected quotation;
- paid pilot;
- actual delivery time and non-labour cost;
- change requests, rework, support and refund behavior;
- repeat purchase / referral where it occurs.

For a future SaaS product, provider guidance such as Stripe's current value-metric -> pricing-model -> packaging -> measurement structure can be bound when applicable.

A pricing method can inform an experiment. It cannot create willingness to pay.

## Customer-success boundary

Do not create a universal `CustomerSuccessState`.

Use direct facts:

- accepted deliverable;
- satisfaction/feedback evidence where collected;
- complaint and resolution;
- repeat purchase / renewal;
- expansion;
- churn/cancellation;
- referral;
- support/rework burden.

ISO 10004 and ISO 10002 can guide the measurement/complaint processes. The customer's behavior remains the evidence.

## Hiring and procurement boundary

Do not instantiate HR/procurement infrastructure because a future company may need it.

- first real hire -> bind ISO 30405, applicable employment law, payroll/contract provider, and only then select a record system such as Frappe HR if needed;
- first real procurement -> use provider-native supplier/RFQ/PO/invoice records;
- activate ISO 20400 only where sustainability is material;
- activate ISO 37500 when the supplier relationship is materially an outsourcing arrangement.

## Deletion / admission rule

A future Ordivon Sales, GTM, Pricing, Customer-Success, Hiring or Procurement methodology is inadmissible unless repeated measured work shows a residual need not satisfied by the external method/provider plus task-local configuration.
