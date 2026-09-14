# Composition: Enterprise Work -> Verified Outcome R1

Date: 2026-09-14
Standing: **DOGFOOD CANDIDATE**

## Purpose

This composition routes a bounded consequential piece of work through mature management, execution and verification owners without creating a universal Ordivon work-state machine.

## Activation inputs

Use this composition when a request/opportunity/obligation has enough consequence to benefit from explicit scope, acceptance and evidence management.

Minimum questions:

```text
What is the intended output/outcome?
Who can accept it?
What exact subject/scope is bound?
Which obligations/standards apply?
What evidence will demonstrate acceptance?
What risks/authorizations materially constrain execution?
Which mature system naturally owns each fact?
```

## Composition

```text
commitment/context
  -> ISO 10005-informed bounded quality/delivery plan
  -> Standard-Native task profile
  -> select natural work/execution providers
  -> execute
  -> domain-native V&V
  -> acceptance authority decision
  -> owner-native records
  -> correction/improvement when required
```

## Provider selection

- business/customer/accounting/ERP-native quality fact -> ERPNext when real;
- minimal continuity -> Host v2 while sufficient;
- heavyweight collaborative work management -> Plane/OpenProject only after measured need;
- stable prescriptive process -> BPMN/Flowable;
- durable adaptive case -> CMMN/Flowable;
- stable explicit business decision -> DMN/Flowable;
- policy enforcement -> OPA/Rego;
- durable technical orchestration -> Temporal;
- SaaS/API/event integration -> n8n;
- exact local physical execution -> Runtime when its contract adds value;
- uncertain domain reasoning/implementation -> task-selected agents + domain methods;
- semantic acceptance -> domain-native V&V.

## Evidence rule

Provider success is evidence only for that provider's responsibility.

```text
ERP record exists         != domain deliverable accepted
Flowable process ended    != customer outcome achieved
Temporal Workflow closed  != Activity external effect valid
n8n execution green       != target business state correct
Runtime exit 0            != semantic completion
Agent says done            != acceptance
```

## Nonconformity route

Classify before repair:

- provider/mechanical failure;
- domain nonconformity;
- evidence gap;
- external assertion pending;
- customer complaint;
- management/process systemic issue.

Use the natural owner. Escalate to root-cause/corrective-action treatment only when recurrence/consequence justifies it.

## Exit condition

The composition closes only to the bounded authority appropriate to the Work:

- internal owner acceptance;
- customer acceptance;
- domain validator standing;
- external platform/venue/certification result;
- or another explicitly named authority.

Do not convert one authority's acceptance into a stronger claim than it can make.
