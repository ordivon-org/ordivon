# Workstation Execution Fabric Providers

Status: PROVIDER-ONLY / STANDARDS-FIRST

This directory retains concrete Workstation/Operations provider implementations and their
acceptance evidence. It no longer owns a generic workflow language, workflow resolver,
binding plan, static routing catalog, or workflow-derived provider backlog.

The former EF6 WorkflowPlan experiments were retired on 2026-09-19 after the Runtime-side
generic WorkflowPlan contract was removed. They duplicated mature orchestration semantics
without owning machine execution truth.

## Ownership after retirement

- durable long-running process orchestration -> Temporal when required;
- standards-native process/decision interchange -> BPMN/DMN when required;
- compensation -> effect/domain owner using Saga/compensating-transaction semantics;
- physical Runtime Job/Attempt/evidence -> Runtime;
- Windows/WSL machine operations -> concrete Workstation providers and accepted maintenance
  mechanisms;
- provider discovery/current execution affordances -> Runtime/provider-native projections,
  not a second static Workstation catalog.

## Retained providers

The provider implementations under providers/ remain because they embody concrete,
physically tested machine capabilities such as:

- Windows WSL observation;
- cross-node WSL service control;
- Runtime/service observation;
- bounded authority-evidence validation where an accepted maintenance contract still needs it.

Provider presence does not imply generic workflow routing, authorization, or semantic Task
completion.

## Standards-first gate

A new Workstation workflow schema/resolver must not be created. If a real workload requires
durable orchestration, use the mature process owner and bind Workstation provider actions
through narrow adapters. If a provider capability is not currently available, report that
at the natural provider boundary rather than creating a planned provider in a local routing
ontology.
