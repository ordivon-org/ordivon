---
name: enterprise-work
description: Plan, execute, govern, verify, or deliver a consequential multi-step Work using current external standards and natural enterprise/domain providers. Use for customer or business requests, cross-domain projects, work with explicit acceptance criteria, quality/risk/compliance obligations, significant external effects, or tasks where ERP/work-management/BPMN/CMMN/DMN/Temporal/n8n/Runtime/provider ownership must be selected. Do not activate for trivial low-risk edits that need no explicit management composition.
compatibility: Requires access to the relevant source/work files and, for execution, whichever domain/provider tools the task actually needs. External standards and provider currentness may require web or official-source access.
metadata:
  source-authority: ordivon-next
  operating-model: enterprise-operating-model-r1
  standards-environment: standard-native-enterprise-environment-r2
---

# Enterprise work

Turn a consequential real request into a bounded, externally grounded, verifiable delivery without inventing a universal Ordivon Work ontology or activating every enterprise system.

## Core rule

```text
real request / opportunity / obligation
  -> Prepare
  -> Connect
  -> Integrate
  -> domain-native verification
  -> bounded acceptance
  -> owner-native records / learning
```

`Prepare -> Connect -> Integrate` is the adopted integrated-management pattern. It is not a mandatory sequential workflow engine and may iterate as evidence changes the work.

## 1. Decide whether this Skill is needed

Use this Skill when at least one of these is material:

- customer/counterparty commitment or delivery;
- multiple domains/providers/teams must be coordinated;
- explicit quality/acceptance criteria matter;
- legal, contractual, standards, platform or professional obligations constrain the work;
- significant security/privacy/financial/production/external effects exist;
- failure, rollback, evidence, auditability or repeated operational handoff matters;
- the work is project/case/process-shaped enough that management method selection affects the outcome.

For a trivial reversible local edit, follow `AGENTS.md` and the relevant narrow Skill/provider instead of manufacturing a quality plan.

## 2. PREPARE — bind the real work

Before committing to execution, establish only what the current consequence requires:

1. **Intended outcome / deliverables** — what must exist or change?
2. **Exact subject and inputs** — repository revision, artifact digest, dataset, system, customer request, environment or other domain-native identity.
3. **Acceptance authority** — who/what can legitimately accept the result?
4. **Scope / exclusions / assumptions** — prevent an unbounded natural-language problem from becoming an unlimited commitment.
5. **Authorization / permitted effects** — especially for customer systems, credentials, production, security testing, money, publication or external writes.
6. **Interested parties / constraints** — only those material to this Work.
7. **Risks/opportunities** — explicit when consequence/uncertainty justifies them; otherwise keep lightweight.

For external commercialization, preserve the rule:

```text
Universal front door != universal unlimited contract
```

Do not guarantee third-party outcomes outside Ordivon's control. Prefer controllable deliverables plus explicit acceptance criteria.

## 3. CONNECT — build the Standard-Native working set

Read `../../../docs/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md` when standards/applicability/currentness or cross-domain evidence matters.

For the exact Work:

1. discover the current external authorities from authoritative sources;
2. record why each is bound, excluded, deferred, advisory or provider-specific;
3. bind stable requirement/acceptance identities where traceability materially helps;
4. select domain-native evidence and validators;
5. record currentness separately from verification/compliance;
6. state non-claims and external assertions that automation cannot establish.

Do not copy licensed standards text into project files merely for convenience. Keep lawful references and permitted derived mappings.

## 4. Use a bounded quality/delivery plan

For consequential delivery, use the **ISO 10005 quality-plan concept** as the default management shape rather than inventing a universal workflow schema.

A plan may live in an existing contract, project record, issue, repository document, domain profile or ERP record. It normally needs only the relevant subset of:

- output/deliverables;
- acceptance authority and criteria;
- scope/exclusions/assumptions;
- external obligations / Standard-Native profile;
- responsibilities/natural owners;
- resources/providers/environment;
- execution approach;
- V&V and evidence;
- material risk treatments;
- configuration/change identity;
- records/retention;
- nonconformity/corrective-action path;
- delivery/release/acceptance path.

For project-shaped work, use current project-management guidance (for example ISO 21502) as applicable; iterative/adaptive work is still project-manageable. For material risk, use ISO 31000 concepts. Do not assume the versions in memory are current—check official sources when the claim is consequential.

Detailed local composition/currentness: `../../../docs/ENTERPRISE_OPERATING_MODEL_R1.md`.

## 5. Select natural owners; do not centralize truth

Choose providers by responsibility, not by architecture symmetry.

| Need | Preferred owner / candidate |
| --- | --- |
| customer/opportunity/sales/accounting/business project/ERP-native quality fact | ERPNext/Frappe when a real business event exists |
| minimal work continuity | Host v2 while sufficient |
| heavyweight collaborative PM/work items | Plane; consider OpenProject when formal PMO/time/cost governance dominates |
| stable prescriptive business process | BPMN / Flowable |
| durable adaptive case with meaningful case state/milestones/discretion | CMMN / Flowable |
| stable explicit repeatable business decision | DMN / Flowable |
| machine-enforceable policy/admission | OPA/Rego |
| durable crash-resumable technical orchestration, timers, waits, retries | Temporal |
| recurring API/SaaS/event integration | n8n |
| exact source/executable/input-bound local execution evidence | Ordivon Runtime when its boundary adds value |
| open-ended uncertain reasoning/implementation | task-selected Agent + domain method |
| semantic outcome acceptance | domain-native V&V / real acceptance authority |

**Dormant is not deficient.** Do not start Plane, Flowable, Temporal, n8n or another service because the diagram contains it.

## 6. Choose execution semantics from the work

Do not force all work into BPMN or any other notation.

- **Repeatable prescriptive business process** → BPMN when executable process semantics add value.
- **Adaptive managed case** → CMMN when durable case semantics are genuinely useful.
- **Explicit stable business decision/rule table** → DMN when separating decision logic improves control/reuse.
- **Durable technical program** → Temporal when crash recovery, history, timers/waits/retries/messages justify the control plane.
- **Connector automation** → n8n for events/APIs/SaaS glue.
- **Scientific/data DAG** → domain workflow such as Snakemake when that fit is stronger.
- **Open-ended investigation/engineering** → Agent/domain procedure; do not pre-model uncertainty as fake deterministic flow.

Provider state is authoritative only for that provider's responsibility.

## 7. ACT — execute with bounded authority

Use the thinnest mature capability that can produce the required effect.

Before consequential writes/effects, confirm the applicable authorization, target, scope, credentials/identity, reversibility and evidence path. Use least privilege where practical.

Mechanical/provider success is not the overall acceptance verdict.

## 8. VERIFY — evaluate the real outcome

For every material acceptance criterion:

1. identify the validator/evidence source;
2. bind the exact source/provider/environment/participant condition required by the claim;
3. run domain-native verification;
4. preserve partial/open/external-assertion/currentness statuses instead of forcing a global PASS/FAIL;
5. state the claim boundary.

Never infer:

```text
ERP record exists         -> deliverable accepted
BPMN process ended        -> customer outcome achieved
Temporal Workflow closed  -> external Activity effect is valid
n8n execution green       -> target business state is correct
Runtime exit 0            -> semantic completion
Agent says done            -> acceptance
```

## 9. Handle deviations/nonconformity by class

Classify before repair:

- mechanical/provider/environment failure;
- domain requirement nonconformity;
- evidence insufficiency;
- currentness/configuration drift;
- external assertion pending;
- customer complaint;
- recurring/systemic management-process failure.

Route to the natural owner. Use root-cause/corrective-action depth when recurrence, customer harm, regulatory consequence, material rework or systemic failure justifies it. Do not manufacture CAPA ceremony for every transient command failure.

Historical evidence is append/supersede, not rewrite.

## 10. DELIVER / ACCEPT / LEARN

Close only to the authority named in PREPARE:

- internal owner acceptance;
- customer acceptance;
- domain validator standing;
- venue/platform/certification authority;
- contract milestone;
- or another explicit bounded authority.

Then retain only the records that natural owners need. Capture reusable compositions/lessons when repeated value is demonstrated; remove/demote one-off working-set infrastructure.

For a real business event, write business facts through ERPNext/Frappe native lifecycle where it is the natural owner. Do not manufacture ERP transactions for internal architecture acceptance.

## 11. References to load only when needed

- Standards/applicability/currentness/evidence boundary: `../../../docs/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md`
- Enterprise owner routing, management guidance and provider activation: `../../../docs/ENTERPRISE_OPERATING_MODEL_R1.md`
- Compact reusable composition: `../../../compositions/enterprise-work-to-outcome-r1.md`
- Capability availability/standing: `../../../docs/CAPABILITY_PACKAGES_R1.md`
- Policy/authority dimensions: `../../../policies/README.md`

If a task is primarily artifact creation/verification, also activate the `artifact-work` Skill rather than duplicating its family-specific procedures here.
