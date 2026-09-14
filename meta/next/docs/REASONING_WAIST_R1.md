# Reasoning Waist R1

Date: 2026-09-14
Status: **LOCAL COMPOSED SMOKE PASS / THIN PROVIDER**

## Decision

Do not add another Ordivon-native planning/configuration/knowledge platform. Use a small mature-provider waist between domain-native problem representation and execution orchestration.

```text
domain-native problem / requirement / case
        ↓
RDFLib + SHACL        graph transport/query + structural validation
        ↓
OR-Tools / Z3         configuration, optimization, logical consistency
        ↓
Unified Planning      goal/action model → plan through selected planner
        ↓
plan/configuration artifact
        ↓
n8n / Temporal / Runtime / domain provider
```

This is a **composition**, not a new semantic authority.

## Current local provider set

- OR-Tools `9.15.6755` — CP-SAT/configuration/optimization;
- Z3 `5.1.0.0` — satisfiability and logical consistency;
- Unified Planning `1.3.0` — planner-neutral planning API;
- UP Pyperplan `1.1.0` — lightweight classical-planning smoke engine only;
- RDFLib `7.6.0` — RDF/SPARQL graph handling;
- pySHACL `0.40.1` — SHACL validation.

Local isolated environment:

```text
/root/.local/share/ordivon/reasoning-waist/.venv
```

The environment uses Python 3.12 and occupied approximately 392 MiB at acceptance.

## What R1 proves

`/scripts/check_reasoning_waist_r1.py` runs a composed tiny case that:

1. represents a problem case in RDF;
2. validates required graph shape with SHACL and proves an invalid sibling is rejected;
3. solves a small capability configuration under requires/cost constraints using OR-Tools;
4. cross-checks logical consistency and a known contradiction with Z3;
5. generates a four-step plan through Unified Planning + Pyperplan;
6. emits a bounded acceptance receipt.

This demonstrates mechanical composition only.

## What remains external or domain-native

R1 does **not** own:

- requirements meaning;
- domain ontologies;
- business rules;
- research/game/engineering semantics;
- evidence truth;
- physical execution;
- workflow durability;
- authorization;
- Human/external assertions.

## DMN / BPMN / CMMN

The Standard-Native Enterprise Environment R2 already defines when these representations should be activated. They are not part of the always-on core reasoning waist.

The workstation already has the mature Flowable `8.0.0` provider materialized. Current physical inspection confirms the accepted image is still present (`localhost/ordivon-flowable-rest:8.0.0`, manifest `sha256:b67720807e7b091ef46b5e96f191541e1aa67ba0eb284504b5c6e2771d6a5ae2`), and the existing provider record documents successful ProcessEngine, DmnEngine and CmmnEngine boot. It remains intentionally non-running until a real workload requires it.

Standing:

```text
DMN semantic support    OMG DMN / Flowable provider available
DMN local execution     MATERIALIZED / BOOT-SMOKE-PASS / workload-triggered
BPMN local execution    MATERIALIZED / BOOT-SMOKE-PASS / workload-triggered
CMMN local execution    MATERIALIZED / BOOT-SMOKE-PASS / workload-triggered
second workflow suite   NOT NEEDED
```

## Next admissible work

Use this waist on **one real cross-domain consumer**. Good candidates are:

- Game mechanism configuration: catalog + evidence constraints → legal candidate graph;
- Engineering provider selection: requirements + compatibility/cost constraints → provider configuration;
- Research method selection: study question + evidence/method applicability → bounded plan.

Do not build a universal router or ontology before at least two materially different real consumers expose the same missing mapping.
