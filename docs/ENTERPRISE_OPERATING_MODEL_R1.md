# Enterprise Operating Model R1

Date: 2026-09-14
Status: **REAL-WORK DOGFOOD CANDIDATE**

## 0. Decision

Ordivon will not build a private ERP, QMS, PMO, workflow engine, GRC suite, audit system, universal Task ontology, or management methodology.

The enterprise operating model is a **composition of mature external management practice and natural system owners** around a bounded piece of work.

The customer-facing commercial unit may eventually be called a `Work`, `Work Order`, engagement, project, service request, case, contract deliverable, or another provider/domain-native term. R1 does not create a universal persisted `Work` object merely to make those systems look uniform.

The common operating question is:

```text
What commitment exists?
What must be delivered?
What authorities and constraints apply?
Who naturally owns each business / work / execution / evidence fact?
How will acceptance be established?
What happens when the result or process is nonconforming?
What should the organization learn or improve?
```

## 1. External management basis

R1 composes external standards/guidance according to the work rather than adopting every management standard everywhere.

### Integrated management system

Use the ISO management-system Harmonized Approach and the 2026 ISO *Integrated management systems — A practical guide* as the integration pattern. The practical organizational motion is:

```text
Prepare -> Connect -> Integrate
```

R1 uses that pattern as follows:

- **Prepare** — context, interested parties, commitment, intended output, obligations, scope, owner, risks/opportunities, exact subject identity.
- **Connect** — bind the task-specific Standard-Native profile, natural business/work/execution owners, acceptance evidence and existing management processes.
- **Integrate** — execute, verify, handle deviations/nonconformities, deliver/accept, retain records, learn and improve.

This is not an Ordivon lifecycle and does not imply ISO certification.

### Quality-management currentness cut

As of **2026-09-19**, ISO 9001:2026 has been published and is the current edition. ISO published Edition 6 on **2026-09-16**; the prior ISO 9001:2015 baseline and its Amendment 1:2024 are retained as historical/superseded authority records rather than rewritten.

Current baseline for new QMS design/currentness work:

```text
ISO 9001:2026
```

This currentness change does not itself establish Ordivon certification or customer conformity. Existing certification transitions remain owned by the applicable certification/accreditation route.


### Work / project / quality planning

Use as applicable:

- **ISO 10005:2018** — quality plans for a specific process, product, service, project or contract; this is the best fit for a bounded Ordivon delivery plan.
- **ISO 21502:2020** — project-management guidance when the work is genuinely project-shaped; it explicitly permits predictive, incremental, iterative, adaptive or hybrid delivery approaches.
- **ISO 10006:2017** — quality management in projects when project quality-management concerns materially matter.
- **ISO 31000:2018** — risk-management guidance when uncertainty/consequence merits an explicit risk process.
- **ISO 19011:2026** — management-system audit guidance when an actual audit programme or audit is being performed.
- **ISO 37301:2021** — compliance-management requirements/guidance when a real compliance obligation/scope exists.
- **ISO 10002:2018** — complaints handling when a real customer complaint exists.
- **ISO 10004:2018** — customer-satisfaction monitoring/measurement when real external customers and a useful measurement purpose exist.
- **ISO 9004:2018** — sustained-success/self-assessment guidance when organizational maturity review has enough real operating evidence to be meaningful.

Do not activate an ISO family because its topic sounds useful. Applicability remains task-local and evidence-backed through the Standard-Native Enterprise Environment R2.

## 2. The operating composition

```text
external request / internal opportunity / obligation
                    |
                    v
         commitment and business context
         ERPNext only where it naturally owns
         customer / opportunity / contract / project /
         sales / accounting / quality business facts
                    |
                    v
        bounded delivery / quality plan
        external authorities + scope + acceptance
        risks/opportunities + evidence expectations
                    |
                    v
              work coordination
        Host v2 now for minimal continuity
        Plane/OpenProject only when measured PM scale needs it
                    |
                    v
           choose execution semantics
      +-------------+-------------+----------------+
      |             |             |                |
  repeatable     adaptive      durable          integration /
  business       case          technical        SaaS events
  process        semantics     process
  BPMN           CMMN          Temporal         n8n
  Flowable       Flowable
      |
  explicit repeatable business decision -> DMN / Flowable
      |
  open-ended uncertain domain work -> Agent / domain-native method
      |
  exact local physical action -> Runtime when its boundary matters
                    |
                    v
             domain-native V&V
                    |
           +--------+---------+
           |                  |
        accepted          nonconforming /
           |              evidence gap /
           |              external assertion
           |                  |
           |           correction / CAPA /
           |           replanning / escalation
           |                  |
           +--------+---------+
                    v
        delivery / customer or owner acceptance
                    |
                    v
     business / quality / audit record where natural
                    |
                    v
              learn / improve
```

No arrow above implies that all providers are activated for every Work.

## 3. Natural owner matrix

| Fact / responsibility | Natural owner | Activation rule | Must not become |
| --- | --- | --- | --- |
| customer, opportunity, sales, accounting, business project, ERP-native quality record | ERPNext/Frappe | real business event needs that record | universal Task DB |
| minimal durable work/continuity state | Host v2 | current local need; remain bounded | universal semantic/execution owner |
| heavyweight collaborative work items/boards/cycles/modules | Plane, or OpenProject if PMO/time/cost governance dominates | measured coordination complexity exceeds Host v2 | domain truth |
| prescriptive business process | BPMN/Flowable | stable repeatable organizational process benefits from executable model | universal workflow graph |
| adaptive managed case | CMMN/Flowable | real case state/milestones/discretion outperform task-local approach | generic agent scratchpad |
| explicit repeatable business decision | DMN/Flowable | rules/decision tables are stable enough to deserve a model | policy engine or domain truth by default |
| policy/admission enforcement | OPA/Rego | machine-enforceable policy boundary exists | general decision methodology |
| durable technical orchestration | Temporal | crash-proof history, timers, waits, retries, messaging or workers are materially required | business database |
| API/SaaS/event integration | n8n | recurring/event-driven multi-service integration exists | business/work truth |
| exact local execution evidence | Ordivon Runtime | source/executable/input/attempt boundary materially matters | domain semantic completion |
| repository/document source state | Git / owning repository | source-controlled knowledge/code/artifact | enterprise business record |
| requirements/traceability workbench | StrictDoc + ReqIF when useful | explicit traceability/interchange is valuable | standards authority |
| JSON Schema validation | check-jsonschema | JSON Schema contract exists | domain semantic validator |
| domain acceptance | Research/Engineering/Game/Artifact/Security/etc. native V&V | always where domain outcome is claimed | generic management green light |
| management-system audit | audit programme using ISO 19011:2026 guidance | actual audit objective/scope exists | everyday execution gate |

## 4. Quality plan as the bounded delivery contract

For a consequential Ordivon delivery, use an ISO 10005-informed **quality plan** rather than inventing an all-purpose workflow schema. The carrier can be a contract, statement of work, project plan, issue, document, ERP record, or domain profile depending on context.

The plan should answer only what the work needs, typically:

```text
intended output / deliverables
interested parties and acceptance authority
exact scope / exclusions / assumptions
external obligations and Standard-Native profile
responsibilities and natural owners
resources / providers / environment
methods / execution approach
verification and validation
acceptance criteria
risk / opportunity treatments when material
change control / configuration identity
records / evidence / retention
nonconformity / corrective-action route
release / delivery / acceptance route
```

Do not copy ISO text into the plan. Use licensed standards lawfully and retain clause/source references or permitted derived mappings.

## 5. Project management is activated by work shape

A difficult piece of work can be managed as a project without forcing a predictive waterfall.

ISO 21502:2020 explicitly permits predictive, incremental, iterative, adaptive and hybrid delivery approaches. Therefore:

```text
project management != fixed waterfall
agentic work != absence of management
```

For project-shaped work, select only the practices justified by consequence and complexity, such as:

- objectives / outcomes;
- scope and change;
- stakeholders;
- resources;
- schedule/milestones;
- risks/issues;
- quality;
- information/records;
- procurement/suppliers if any;
- transition/closeout/evaluation.

A small one-person internal improvement project may need a tiny subset. A customer engagement, regulated deployment or multi-party programme may need far more.

## 6. Risk is a decision input, not another database

Use ISO 31000 concepts when consequence/uncertainty merits it:

```text
establish context
-> identify risk/opportunity
-> analyse/evaluate
-> treat
-> monitor/review
-> communicate/consult
```

The risk record stays where it naturally belongs: project tool, ERP/QMS record, security threat model, research protocol, engineering issue, contract file, or another mature owner. Do not create a universal Ordivon Risk table merely to centralize it.

Scale controls with consequence. A reversible documentation edit and a customer production write should not carry the same approval/review burden.

## 7. Nonconformity, corrective action and learning

A failed tool run, domain failure, missing external assertion and customer complaint are different things.

Classify the actual condition before acting:

```text
mechanical execution failure
provider / environment drift
domain requirement nonconformity
evidence insufficiency
external assertion pending
customer complaint
management-system process failure
```

Then route to the natural owner.

Corrective action should target cause when recurrence matters. Do not manufacture CAPA ceremony for every one-off typo or failed command. Repeated/systemic defects, customer harm, regulatory consequence, material rework or recurring process failures justify deeper root-cause/corrective-action treatment.

Historical evidence is append/supersede, not rewrite, following Standard-Native Environment R2.

## 8. Audit and management review

Use **ISO 19011:2026** when performing management-system audits. An audit needs an objective, scope, criteria, evidence, findings and competent/appropriately independent judgement; it is not equivalent to running repository tests.

Management review is broader than audit. At an appropriate cadence and maturity, review evidence such as:

- customer/owner outcomes and complaints;
- delivery/acceptance performance;
- recurring nonconformities and corrective actions;
- risks/opportunities;
- provider/standard currentness pressure;
- resource/capability constraints;
- audit results where audits exist;
- effectiveness of improvement actions;
- demand for activating/deactivating heavier providers.

At Ordivon's present early stage, review should stay lightweight and evidence-driven rather than simulate a large-company committee calendar.

## 9. Commercial Work boundary

For external commercialization, the public front door may accept a broad natural-language problem, but the organization should not commit to an unbounded problem statement.

Before commitment, compile the request into a bounded agreement with, as applicable:

```text
customer / counterparty
problem / intended outcome
scope and exclusions
inputs and access/authorization
permitted actions
external authorities / constraints
outputs / deliverables
acceptance authority and acceptance criteria
price / commercial terms / SLA where applicable
change mechanism
privacy / security / rights obligations
failure / cancellation / refund / escalation conditions
```

This can map to native CRM/sales/project/contract records when a real company/customer event exists. It is not yet a justification for a custom Ordivon `WorkContract` database schema.

Strong rule:

```text
Universal front door
!=
Universal unlimited contract
```

Sell controllable deliverables/acceptance conditions rather than guaranteeing third-party outcomes that Ordivon does not control.

## 10. Provider activation economics

A provider is activated only when the work demonstrates a responsibility that it solves better than the current thinner composition.

### Keep dormant now unless triggered

- **Plane** — no current proof that Host v2 is too small for the actual collaboration load.
- **OpenProject** — no recurring PMO/time/cost governance workload yet.
- **Flowable** — image is materialized and engines boot-smoked, but no current BPMN/CMMN/DMN workload has demonstrated execution value.
- **Temporal** — not locally active; no current Work requires durable timers/waits/crash-proof Workflow history strongly enough to justify operating it.
- **customer complaint/satisfaction processes** — no real external customer event in this R1 dogfood.
- **formal audit programme** — no certification/customer/regulatory audit objective is asserted for this R1 dogfood.

Dormant is not deficient.

## 11. R1 dogfood — Standard-Native Enterprise Environment R2

R1 is dogfooded against the real internal improvement project that just created `STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2`.

### Prepare

Problem observed:

> Research, Engineering and Game repeatedly needed external standards, but without a shared standards-native environment each workload had to rediscover how applicability, currentness, traceability, evidence and claim boundaries should be handled.

Intended output:

> A thin cross-domain environment that preserves external/domain authority instead of replacing it.

Interested party/acceptance authority for this internal improvement:

> Ordivon owner/operator, evidenced by accepted source integration and cold verification; there is no external customer acceptance claim.

### Connect

Applicable management guidance for this improvement project:

- ISO Integrated Management Systems practical integration pattern;
- ISO 10005 quality-plan concept for a bounded specific case;
- ISO 21502 project-management guidance because the work has a defined outcome, finite implementation and acceptance;
- ISO 10006 project-quality guidance as advisory support;
- ISO 31000 risk concepts because overgeneralization and false authority claims are material design risks.

Not activated:

- ERPNext business record — no external customer/sale/accounting event and no need to create fake business activity;
- Plane/OpenProject — one owner plus existing Git/Runtime continuity was sufficient;
- Flowable BPMN/CMMN/DMN — no stable organizational process/case/decision model was required;
- Temporal — no durable long-wait/crash-resume Workflow requirement;
- n8n — no recurring cross-service integration edge;
- ISO 19011 audit programme — no independent management-system audit was claimed.

### Integrate / actual execution

The work used:

- Git/`ordivon-next` as source authority;
- Research, Runtime and Game source profiles as domain authorities;
- StrictDoc/ReqIF for explicit requirement interchange;
- JSON Schema 2020-12 + mature `check-jsonschema 0.38.0` for projection validation;
- Ordivon Runtime for bounded mechanical local execution evidence;
- current external source checks for ISO/OMG/provider versions;
- domain-owned report vocabularies without normalization.

Acceptance evidence already proved:

```text
Research projection       PASS
Runtime projection        PASS
Game projection           PASS
JSON Schema validation    PASS via check-jsonschema 0.38.0
ReqIF export              PASS for all three domains
Domain verdicts distinct  TRUE
Universal normalization   FALSE
ordivon-next main cold verify PASS
```

### Actual risks and treatments

| Risk | Observed treatment |
| --- | --- |
| invent a universal Ordivon standards ontology | admitted only a read-only projection after three-domain proof |
| normalize incompatible domain verdicts | preserved each domain vocabulary; cross-domain intersection observed as only `PASS` |
| stale external standard/provider version | explicit currentness checks and refresh triggers |
| custom validator creep | replaced ad-hoc JSON Schema validation with pinned mature `check-jsonschema 0.38.0` |
| rewrite historical evidence to fit current state | append/supersede rule; Game historical access evidence retained while current portfolio evidence was added |
| duplicate side effects during Runtime Registry contention | reconciled exact committed Jobs rather than creating replacement executions |
| overwrite concurrent work on `ordivon-next/main` | detected main advancement and opened a fresh Workspace from the latest revision before this operating-model work |

### R1 dogfood conclusion

The enterprise model adds value primarily as **selection, ownership, quality/risk/acceptance discipline**, not as another runtime.

The R2 internal project required no ERP record, no Plane, no Flowable, no Temporal and no n8n workflow. That is a positive result: the environment can use modern enterprise management without forcing heavyweight platforms onto work that does not need them.

## 12. Next real activation triggers

Use the first real external/customer or company-operating event to test the business side of this model.

Examples:

- first real customer request -> CRM/opportunity + bounded quality/delivery plan + domain execution + customer acceptance;
- first customer complaint -> ISO 10002-informed owner-native complaint handling;
- first repeated prescriptive organizational process -> BPMN/Flowable candidate;
- first durable case with meaningful discretionary state -> CMMN/Flowable candidate;
- first repeatable explicit business rule set -> DMN/Flowable candidate;
- first long-lived crash-resumable technical process -> Temporal candidate;
- first workload where Host v2 materially impedes coordination -> compare Plane/OpenProject using measured requirements;
- first formal internal/customer/certification audit -> ISO 19011:2026 audit route;
- before any consequential QMS claim -> bind the current ISO 9001:2026 edition and the exact customer/certification scope; do not reuse the superseded 2015 baseline by habit.

Do not manufacture those events to complete an architecture checklist.

## External sources / currentness references

- ISO management system standards: https://www.iso.org/management-system-standards.html
- ISO Integrated management systems practical guide, 3rd edition, 2026: https://www.iso.org/publication/PUB100435.html
- ISO 9001 current/successor status: https://www.iso.org/standard/9001
- ISO 10005:2018: https://www.iso.org/standard/70398.html
- ISO 10006:2017: https://www.iso.org/standard/70376.html
- ISO 21502:2020: https://www.iso.org/standard/74947.html
- ISO 31000:2018: https://www.iso.org/standard/65694.html
- ISO 19011:2026: https://www.iso.org/standard/19011
- ISO 37301:2021: https://www.iso.org/standard/75080.html
- ISO 10002:2018: https://www.iso.org/standard/71580.html
- ISO 10004:2018: https://www.iso.org/standard/71582.html
- ISO 9004:2018: https://www.iso.org/standard/70397.html
