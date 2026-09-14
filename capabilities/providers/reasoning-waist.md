# Provider: Reasoning Waist R1

Status: **LOCAL CORE SMOKE PASS / THIN COMPOSITION PROVIDER**
Observed: 2026-09-14

## Role

A small standards-friendly reasoning bundle used **before** execution orchestration:

```text
problem/model
  -> validate semantic shape
  -> solve configuration/constraints
  -> generate bounded plan
  -> hand plan/configuration to n8n / Temporal / Runtime / domain provider
```

It is not a universal Ordivon ontology, planner, workflow engine, decision truth source or domain model.

## Local binding

```text
Python 3.12 environment:
/root/.local/share/ordivon/reasoning-waist/.venv
```

Current locally accepted providers:

| Function | Mature provider | Accepted version |
| --- | --- | --- |
| combinatorial configuration / optimization | Google OR-Tools CP-SAT | 9.15.6755 |
| logical consistency / satisfiability | Z3 | 5.1.0.0 |
| planner-neutral planning API | Unified Planning | 1.3.0 |
| lightweight classical planning test engine | UP Pyperplan | 1.1.0 |
| RDF graph / SPARQL | RDFLib | 7.6.0 |
| SHACL graph validation | pySHACL | 0.40.1 |

Environment footprint at acceptance: approximately **392 MiB**.

## Authority boundaries

- OR-Tools solves the encoded optimization/configuration problem; it does not prove the real-world model is correct.
- Z3 proves satisfiability/unsatisfiability only for the encoded formulae.
- Unified Planning provides a common planning interface; actual planning semantics remain those of the problem model and selected engine.
- Pyperplan is accepted only as a lightweight classical-planning smoke engine, not as the default production planner for complex problems.
- RDFLib stores/queries graph statements; it does not make those statements true.
- pySHACL validates RDF graph shape constraints; conformance is not domain correctness.

## DMN / CMMN / BPMN boundary

The Standard-Native environment already recognizes OMG BPMN/CMMN/DMN as task-shape-specific representations. They are **not embedded inside the Reasoning Waist**.

A mature local provider already exists: Flowable `8.0.0` is materialized as `localhost/ordivon-flowable-rest:8.0.0`; current physical inspection confirms image ID `49480a54...`, manifest digest `sha256:b6772080...`, size about 342 MB, and the existing provider acceptance recorded successful Process/Dmn/Cmmn engine boot. It remains `PRODUCTION-HOLD-UNTIL-WORKLOAD`.

Therefore no second DMN/CMMN/BPMN engine is installed. Activate Flowable only when an actual prescriptive process, adaptive case or repeatable decision-table workload justifies it.

## Execution handoff

This provider stops before physical execution:

```text
Reasoning Waist
  -> configuration / plan / validated model
  -> n8n for integration automation
  -> Temporal when durable workflow semantics are actually required
  -> Runtime for exact local physical execution/evidence
  -> domain-native provider for domain action
```

No execution provider inherits semantic truth from the reasoning layer.
