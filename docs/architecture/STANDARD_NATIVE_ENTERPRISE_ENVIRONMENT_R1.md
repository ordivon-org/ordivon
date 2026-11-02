# Standard-Native Enterprise Environment R1

Date: 2026-09-14
Status: **HISTORICAL BASELINE / SUPERSEDED FOR CURRENT OPERATION BY R2**

This file is retained at its original path because authority and acceptance records cite it as historical provenance. Current cross-domain operating guidance is `docs/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md`; do not inherit dated local-provider availability from R1 without revalidation.

## Decision

Ordivon does not define a private management system, universal workflow ontology, quality model, risk model, research lifecycle, engineering lifecycle, or requirements language when a mature external authority already exists.

The environment starts from real work, identifies the applicable external authorities, composes their requirements and methods, delegates execution to mature providers, and retains evidence of applicability, tailoring, execution, verification and outcome.

```text
real problem / obligation / opportunity
        -> identify context and entity of interest
        -> discover applicable external authorities
        -> record applicability / exclusions / tailoring
        -> compose process, case, decision and domain methods
        -> execute through mature providers
        -> collect provider-native evidence
        -> verify against the applicable requirements
        -> deliver / learn / improve
```

This is an environment for using external standards, not an Ordivon standard.

## 1. Management-system basis

Use ISO management-system standards through their Harmonized Structure and the ISO Integrated Management Systems guidance rather than constructing parallel Ordivon management systems.

The current integration model is deliberately small:

- **Prepare**: establish organizational context, scope, leadership intent and relevant obligations.
- **Connect**: map applicable management-system requirements to existing governance, processes, records and evidence.
- **Integrate**: close real gaps, verify operation and improve the shared system.

Common management concerns such as governance, risks/opportunities, compliance, operations, performance evaluation, audit, corrective action and continual improvement are shared concerns. A new domain should connect to them rather than create a duplicate subsystem.

External starting points:

- ISO management-system Harmonized Structure / harmonized approach;
- ISO Integrated Management Systems — A practical guide, 3rd edition, 2026;
- task-applicable MSS such as ISO 9001, ISO/IEC 27001, ISO 37301, ISO 30401, ISO/IEC 42001, ISO/IEC 20000-1, ISO 22301 and others only when their scope is actually relevant.

No claim of certification or conformance follows from registration alone.

## 2. Authority and requirement representation

### Source of truth

The authority remains external: law/regulation, contract, ISO/IEC/IEEE/NIST/OMG or other standards body, platform/vendor rules, professional guidance, scientific reporting standard, venue requirement, customer requirement, or another legitimate source.

Ordivon stores only the minimum interoperable metadata needed to use that authority:

- authority and source identity;
- identifier and edition/version/status;
- jurisdiction/scope where relevant;
- stable clause/section/reference identity where lawful and useful;
- applicability and rationale;
- tailoring/exclusion decision and rationale;
- relationship to work items, evidence and verification results;
- provenance/freshness.

Do not copy proprietary/copyrighted standards text into Ordivon merely to make it searchable. Keep references and licensed excerpts within their license terms. Public machine-readable standards and regulations may be retained according to their own terms.

### Interchange

Use OMG ReqIF 1.2 when requirements need cross-tool interchange. ReqIF is an exchange representation, not the semantic authority and not a universal Ordivon ontology.

### Local authoring / traceability workbench

StrictDoc 0.29.0 is accepted as the initial text/Git-native requirements and traceability workbench. It is replaceable and optional. A local smoke on 2026-09-14 proved:

- pinned installation with `uv tool`;
- HTML and JSON export;
- `reqif-sdoc` export;
- stable demo UID `DEMO-EXT-001` present in HTML, JSON and generated ReqIF.

StrictDoc does not become the authority registry itself. It is a work surface for requirements, references and traceability when useful.

## 3. Process / case / decision semantics

Use the OMG standards according to work shape:

- **BPMN** for sufficiently prescriptive business processes;
- **CMMN** for adaptive case work whose activity order depends on evolving information and judgment;
- **DMN** for explicit business decisions and decision tables.

Do not force all work into one notation. Agentic investigation may remain an adaptive case or task-local execution plan rather than being pre-modeled as BPMN.

### Flowable

Flowable 8.0.0 is accepted as the initial candidate execution provider for the BPMN/CMMN/DMN trio because the same open-source engine family implements all three standards.

Local evidence captured on 2026-09-14:

- official `flowable-rest:8.0.0` image materialized through the existing Network v2 / Surfpath acquisition path after direct Docker Hub access timed out;
- imported local image manifest digest `sha256:b67720807e7b091ef46b5e96f191541e1aa67ba0eb284504b5c6e2771d6a5ae2`;
- image configuration ID `49480a54bd98df6e3ba16cd737b539cc41831504c7582f75e341ea357707ea2b`;
- image size observed as 341,894,286 bytes;
- Flowable REST booted successfully;
- boot logs independently created `ProcessEngine default`, `DmnEngine default` and `CmmnEngine default`;
- Tomcat reported the `/flowable-rest` application started on port 8080;
- an in-container unauthenticated HTTP probe reached the service and received HTTP 401, confirming the REST security boundary is live.

This is provider-mechanics evidence, not yet acceptance of a production Flowable deployment or a real business workload. Production activation remains demand-driven.

## 4. Existing provider ownership

Do not collapse the existing mature substrates into Flowable or into an Ordivon database.

| Concern | Default owner / role |
| --- | --- |
| Business master/transaction/accounting/quality records | ERPNext / Frappe |
| Prescriptive business-process semantics | Flowable BPMN when needed |
| Adaptive case semantics | Flowable CMMN when needed |
| Business decision semantics | Flowable DMN when needed |
| Policy/admission enforcement | OPA / Rego |
| Durable technical orchestration | Temporal |
| API/SaaS/event integration edges | n8n |
| Agentic repository / engineering work | Codex or the task-selected agent host |
| Agentic browser work | Browser Use / Browserless / Playwright as appropriate |
| Exact local mechanical execution evidence | Ordivon Runtime |
| Business facts | Domain-native systems such as ERPNext, not Runtime |
| Telemetry | OpenTelemetry / Prometheus / Vector / Loki / Grafana / Netdata as applicable |
| Enterprise architecture description | ArchiMate / TOGAF methods when useful |
| Product/system MBSE | task-selected systems-engineering tools/methods, e.g. Capella/Arcadia when justified |

Key non-substitution rules:

- Flowable does not replace Temporal merely because both execute workflows.
- Temporal does not define business BPMN/CMMN/DMN semantics.
- n8n does not become business truth or global workflow truth.
- OPA enforces policy; it does not replace domain business decision models.
- ERPNext owns its natural business records; it does not become Ordivon's universal Task store.
- Runtime proves mechanical execution; it does not assert domain completion.

## 5. Enterprise architecture

Use TOGAF as an enterprise-architecture method/reference body and ArchiMate as an enterprise-architecture modeling language when a real architecture question benefits from them.

Archi is the preferred lightweight open-source ArchiMate modeling tool candidate if/when an actual enterprise architecture model is needed. Do not install or maintain an always-on architecture platform merely to have one.

The Open Group documentation and specifications have their own license terms. Store references and models we create; do not mirror licensed specification text into the Ordivon repository.

## 6. Domain profiles

Research, Engineering, Game, Artifact, Media, Security, Network and future domains are profiles over this shared environment, not independent management systems.

A domain profile should add only what is specific to that work, for example:

```text
shared management / authority / evidence environment
        + entity-of-interest lifecycle
        + domain standards and methods
        + platform / venue / jurisdiction rules
        + domain-native tools and validators
        -> task-specific execution profile
```

Examples:

- Research selects study-type-specific scientific methods, reporting standards, reproducibility and venue requirements.
- Engineering selects ISO/IEC/IEEE 12207/15288 and software/security/platform standards only where applicable.
- Game adds engine, platform/store, accessibility, ratings, privacy, production and playtesting requirements according to the target product.

## 7. Authority precedence is contextual

Do not encode one universal precedence list. In a concrete task, resolve conflicts using the actual legal/contractual/professional context. Typical inputs include mandatory law/regulation, binding contracts, customer requirements, certification scope, authoritative domain standards and voluntary best practice.

Every consequential applicability or tailoring decision must retain its source and rationale.

## 8. What remains intentionally absent

R1 does **not** add:

- an Ordivon universal requirement schema;
- an Ordivon universal process ontology;
- a custom GRC suite;
- a duplicate ERP/QMS;
- a universal lifecycle imposed on Research/Game/Engineering;
- automatic ingestion of copyrighted standards bodies' full texts;
- a claim that every ISO/IEC/IEEE/NIST/OMG framework applies to every task.

Security-specific machine-readable control work should prefer native standards such as NIST OSCAL when that domain requires them rather than stretching the general ReqIF/StrictDoc workbench into a security-control ontology.

## 9. Next acceptance workloads

Promote only through real work:

1. take one existing Research or Engineering case and identify its actual external authorities;
2. represent the bounded requirement/reference set with stable identities and traceability;
3. use DMN only if there is a real repeatable decision worth modeling;
4. use CMMN for one genuinely adaptive case only if its case semantics improve work over the current agent/task approach;
5. use BPMN for one repeatable organizational process only if the process is sufficiently prescriptive;
6. connect resulting business records to ERPNext only where ERPNext is the natural owner;
7. verify outcome using domain-native evidence;
8. delete or downgrade any provider whose real workload does not justify its operational cost.

## External authorities / provider documentation

- ISO management system standards and Harmonized Structure: https://www.iso.org/management-system-standards.html
- ISO Integrated Management Systems practical guide: https://www.iso.org/publication/PUB100435.html
- OMG BPMN/CMMN/DMN overview: https://www.omg.org/intro/TripleCrown.pdf
- OMG ReqIF 1.2: https://www.omg.org/spec/ReqIF/1.2
- Flowable open source: https://www.flowable.com/open-source-code
- StrictDoc documentation: https://strictdoc.readthedocs.io/
- The Open Group TOGAF / ArchiMate: https://www.opengroup.org/togaf
- Archi: https://www.archimatetool.com/
