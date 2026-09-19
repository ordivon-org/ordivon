# Standard-Native Enterprise Environment R2

Date: 2026-09-14
Status: **CROSS-DOMAIN DOGFOOD ACCEPTED CANDIDATE**

## 0. Decision

R1 established the external-first direction. R2 turns that direction into a thin, reusable operating contract proven by three unlike real workloads: Research, Engineering/Runtime, and Game Pre-G0.

Ordivon still does **not** own a universal research lifecycle, software lifecycle, game lifecycle, requirements language, process ontology, quality model, compliance model, or verdict vocabulary.

The shared environment owns only the interoperability needed to answer these questions for a real piece of work:

```text
1. What exact subject / entity of interest is being evaluated or changed?
2. Which external authorities are relevant, and why?
3. Which authorities are applicable, excluded, deferred, advisory, provider-specific, or scope-specific?
4. What stable requirement/reference identities are used for traceability?
5. What evidence was actually produced, under what source/provider/version condition?
6. Is that evidence current for the claim being made?
7. What claims are explicitly NOT established?
8. Which domain or external authority owns the final bounded verdict?
```

Everything else remains domain-native or provider-native.

## 1. Cross-domain dogfood that justifies R2

R2 is promoted only because the same thin pattern survived three materially different workloads.

### Research — Paper 1 publication object

The Research profile binds a frozen manuscript object to ACM SIGSOFT empirical standards, EMSE/Springer submission and data-policy requirements, RO-Crate and FAIR guidance. It contains both applicable and explicitly excluded authorities. Its report retains domain-native statuses such as `EXTERNAL_ASSERTION_REQUIRED` for facts that automation cannot establish.

### Engineering — Ordivon Runtime

The Runtime profile binds a software product/service to ISO/IEC/IEEE 12207:2026, ISO/IEC 25010:2023, NIST SSDF 1.1 and SLSA 1.2 guidance. It preserves source quality, release-candidate quality and installed-deployment currentness as separate facts. Its report deliberately uses `NOT_CLAIMED` rather than laundering Runtime-native receipts into a SLSA level claim.

### Game — Pre-G0 product discovery / human-value falsification

The Game profile binds the current Pre-G0 work to ISO 9241-210, ISO 9241-11, Xbox Accessibility Guidelines, WCAG 2.2 for the web carrier, Games User Research practice and the Godot provider. It preserves real-human evidence gaps as `OPEN`, accessibility as partial/open where appropriate, provider version drift as `PINNED_NOT_LATEST`, and future store/rating obligations as deferred rather than falsely applicable.

The dated 2026-09-14 acceptance receipt under `evidence/acceptance/` preserves the exact source revisions, file digests, authority bindings, stable requirement IDs and domain verdict vocabularies captured during R2 dogfood. Its one-shot producer has been retired from the current command surface; Git history preserves that producer. Current repository integrity is checked by `scripts/check_standard_native_enterprise_r2.py` and the authority-catalog gates rather than regenerating a historical receipt from today's sources.

## 2. What is genuinely common

The dogfood supports exactly seven shared planes.

### 2.1 Subject identity

Every consequential claim must bind an exact subject condition appropriate to the domain: manuscript digest, repository revision, build/provider condition, experiment revision, target carrier, or another domain-native identity.

`latest thing in the project` is not a sufficient evidence identity.

### 2.2 Authority binding

The external source remains authoritative. Ordivon records only enough metadata to use it:

- authority identifier;
- official source/reference;
- version/edition/status where relevant;
- currentness check date;
- task-local role;
- applicability/exclusion/deferment rationale.

A provider document, professional guideline, venue rule, law, contract and formal standard may all appear in one profile. Their authority types must not be flattened into one false hierarchy.

#### Authority Catalog R1 — discovery before applicability

`authorities/` is the accepted lightweight discovery substrate for external authorities already registered by Ordivon work. It follows progressive disclosure rather than loading every authority into every task:

```text
Level 0 generated discovery index
    -> select candidate
Level 1 authority identity/currentness record
    -> inspect official source as needed
Level 2 task-local Standard-Native profile
    -> BOUND / EXCLUDED / DEFERRED + role/rationale/evidence
Level 3 external source/full text
    -> authoritative source or lawfully accessed licensed material
```

The Catalog is deliberately **not** an applicability engine. `authority find` can suggest a candidate because its metadata matches the problem; only the current Work/profile may bind or exclude it. Currentness observations are append-only and separate from stable/versioned authority identity. The generated index is a derived projection and may be deleted/rebuilt without loss of authority truth.

### 2.3 Stable trace identity

Requirements or acceptance criteria that materially affect verification need stable local trace identifiers. The identifier belongs to the task-local mapping, not to an invented universal Ordivon requirement ontology.

When cross-tool exchange is useful, use OMG ReqIF 1.2. StrictDoc remains the accepted optional Git/text workbench; it is not the authority source.

### 2.4 Evidence binding

Evidence must retain enough identity to answer what was actually observed: source revision, artifact digest, provider/version, execution condition, participant/session condition, external assertion, or equivalent domain-native provenance.

Mechanical execution evidence is not automatically domain evidence.

### 2.5 Currentness

Currentness is an independent dimension. R2 explicitly rejects these collapses:

```text
newer upstream version exists != current evidence is invalid
installed version differs from source main != source tests fail
historical evidence superseded != historical evidence was false
standard confirmed/current != every clause applies
```

A validated provider pin may remain accepted while a newer stable upstream release is merely recorded as currentness pressure.

### 2.6 Claim boundary / non-claims

Every consequential verification report needs an explicit boundary. Typical boundaries include:

- not certification;
- not venue acceptance;
- not product selection;
- not live-deployment health;
- not a SLSA level;
- not WCAG/XAG conformance;
- not a Human/player-value claim.

The environment treats a correct non-claim as evidence quality, not as failure.

### 2.7 Domain-owned verdict

R2 deliberately does **not** define one global status enum.

The three dogfoods already prove why:

```text
Research:
PASS / PARTIAL / OPEN / EXTERNAL_ASSERTION_REQUIRED

Runtime:
PASS / NOT_CLAIMED

Game:
PASS / PARTIAL / OPEN /
DEFERRED_TRIGGERED_BY_SCOPE_CHANGE /
PINNED_NOT_LATEST /
DEFERRED_NOT_APPLICABLE_CURRENT_PHASE
```

The shared layer records the vocabulary and its owner. It does not reinterpret it.

## 3. Orthogonal dimensions, not one traffic light

A useful enterprise environment must not compress unlike facts into one `PASS/FAIL` field. At minimum, keep these dimensions conceptually separate even when a domain chooses a compact representation:

| Dimension | Question |
| --- | --- |
| applicability | Does this authority/requirement apply to this exact subject and scope? |
| evidence | What observation or artifact supports the statement? |
| verification | What bounded verdict does the domain validator make? |
| currentness | Is the source/provider/evidence current enough for this claim? |
| claim authority | Who is actually allowed to assert the final fact? |
| consequence | What decision, release, delivery or follow-up is justified? |

This prevents common category errors such as treating `provider latest version differs` as `FAIL`, treating `external assertion required` as `test failure`, or treating `tool exit 0` as semantic completion.

## 4. Integrated management-system connection

The 2026 ISO *Integrated management systems — A practical guide* recommends integrating multiple management-system standards into one coherent system rather than operating duplicate systems. Its practical flow is **Prepare → Connect → Integrate** and its common concerns include governance, risks/opportunities, compliance, operations, and performance evaluation/improvement.

R2 maps that mature organizational pattern without turning it into an Ordivon lifecycle:

### Prepare

- identify organization/work context and the entity of interest;
- identify interested parties, obligations and intended outcome;
- bind the exact work scope and authority/currentness discovery cut;
- decide which shared management concerns are actually active.

### Connect

- map applicable external requirements to existing domain work, owners, records, providers and validators;
- reuse existing governance/risk/compliance/operations/evidence mechanisms;
- record exclusions, deferments and substitution boundaries instead of creating parallel subsystems.

### Integrate

- close demonstrated gaps;
- execute through mature providers;
- verify with domain-native evidence;
- retain corrective actions, review outcomes and reusable compositions;
- refresh authority/provider currentness when a trigger occurs.

No certification or ISO conformance claim follows from using this integration pattern.

## 5. Current external representation spine

Use current formal versions unless a real provider/workload deliberately pins another supported version.

- OMG ReqIF **1.2** — formal requirements interchange.
- OMG BPMN **2.0.2** — formal prescriptive business-process notation.
- OMG CMMN **1.1** — formal adaptive case-management notation.
- OMG DMN **1.5** — current formal decision-model notation at this R2 cut; newer 1.6/1.7 work is not silently treated as formal.
- StrictDoc **0.29.0** — current accepted local optional requirements/traceability workbench.

BPMN/CMMN/DMN are activated only when the shape of the work justifies them. None of the Research/Runtime/Game dogfoods required a Flowable model to prove their standards-native behavior; that abstention is correct.

## 6. Workflow/provider activation rules

### BPMN

Activate only when the organizational process is sufficiently repeatable and prescriptive that an explicit process model improves execution, control, auditability or handoff.

### CMMN

Activate only when a durable adaptive case has meaningful case state, milestones, discretionary work and evolving information that are better represented by case semantics than by the existing task/agent approach.

### DMN

Activate only when a repeatable business decision has explicit inputs/rules/decision tables worth separating from orchestration or policy enforcement.

### OPA / Rego

Use for policy/admission enforcement. Do not stretch policy enforcement into domain decision truth.

### Temporal

Use for durable technical orchestration. Do not treat Temporal workflow code as business-process semantic authority.

### n8n

Use for integration edges and automation. Do not make it business truth.

### Runtime

Use for exact mechanical execution evidence. Runtime does not assert semantic completion.

### ERPNext / domain-native systems

Use them for the business facts they naturally own. Do not mirror those records into a universal Ordivon task database merely for centralization.

## 7. Currentness and refresh triggers

Do not continuously churn profiles simply because the outside world changes. Refresh when one of these triggers is material:

- the work subject or scope changes;
- a mandatory law/contract/platform/venue rule changes;
- an authority publishes a new edition affecting the current scope;
- a provider pin reaches end-of-support or a relevant defect/security issue appears;
- a new target platform, jurisdiction, participant class or distribution carrier is admitted;
- evidence ages past the domain's accepted freshness boundary;
- a conflicting authority or contradictory result appears;
- a decision depends on current market/provider state.

Record `currentness_checked` separately from `compliance` or `verification`.

## 8. Historical evidence is append/supersede, not rewrite

The Game dogfood exposed a concrete example: an older access record correctly showed that an initial Factorio-first recommendation had been superseded at that time, while a later portfolio decision selected Factorio Demo again as the current first canary. The correct repair was to bind both historical and current evidence, not rewrite the historical record.

Enterprise rule:

```text
new standing
    -> successor evidence / supersession relation
    != mutate history until it agrees with the present
```

The same rule applies to releases, audits, experiments, decisions, incidents and management reviews.

## 9. Human and external assertions

Some facts cannot be synthesized by tools or agents:

- author declarations at submission;
- participant-reported experience;
- legal/contractual authorization;
- external certification or platform approval;
- customer acceptance where the customer is the authority;
- real market outcomes.

Represent these as unresolved external assertions or explicit external-authority steps. Do not convert their absence into fabricated evidence.

## 10. Minimal machine-actionable bridge

After three-domain proof, `schemas/standard-native-profile-projection-v1.schema.json` is admitted as a **projection schema**.

It is intentionally not a source-of-truth schema. It projects only:

- exact source/profile/report/requirement carrier identities;
- opaque domain subject metadata;
- authority bindings and applicability disposition;
- stable requirement IDs;
- domain-owned verdict vocabulary;
- claim boundary;
- bounded currentness/non-claim signals.

Domain profiles remain free to use different source structures. The projection exists so enterprise tooling can inventory, audit and compare coverage without owning domain semantics.

JSON Schema validation is delegated to the mature `check-jsonschema` provider rather than reimplemented in Ordivon. The R2 semantic checker verifies only cross-domain invariants that JSON Schema cannot decide, such as preservation of domain-owned verdict vocabularies.

## 11. Promotion result

R2 is accepted when the cross-domain dogfood receipt proves all of the following without changing the domain source artifacts:

1. Research, Runtime and Game can all be projected from their existing heterogeneous profiles.
2. Each case retains one or more external authority bindings.
3. Each case retains stable requirement IDs.
4. Each report retains an explicit claim boundary.
5. Domain verdict vocabularies remain distinct and are not normalized away.
6. Authority currentness observations remain visible.
7. The projection validates against the minimal bridge contract.
8. The three source requirement carriers remain exportable to ReqIF through the accepted StrictDoc path.

## 12. What R2 still does not add

R2 does **not** add:

- an Ordivon standard replacing external standards;
- a universal verdict enum;
- a global requirement ontology;
- a global process model;
- a mandatory BPMN/CMMN/DMN workflow;
- a universal GRC system;
- certification claims;
- automatic full-text ingestion of copyrighted standards;
- provider auto-upgrades merely because a newer version exists;
- a rule that every future domain must look like Research, Runtime or Game.

The next domain should reuse this environment and add only its real external authorities and native verification methods.

## External sources checked for R2

- ISO management-system standards / Harmonized Structure: https://www.iso.org/management-system-standards.html
- ISO JTCG Harmonized Approach: https://committee.iso.org/sites/jtcg/home/exploring-mss.html
- ISO *Integrated management systems — A practical guide*, 3rd edition, 2026: https://www.iso.org/publication/PUB100435.html
- OMG specifications catalog: https://www.omg.org/spec
- OMG ReqIF 1.2: https://www.omg.org/spec/ReqIF/1.2
- OMG BPMN 2.0.2: https://www.omg.org/spec/BPMN/2.0.2
- OMG CMMN 1.1: https://www.omg.org/spec/CMMN/1.1
- OMG DMN 1.5: https://www.omg.org/spec/DMN/1.5
- StrictDoc documentation: https://strictdoc.readthedocs.io/
