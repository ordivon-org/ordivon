# System Overview

## Goal

Financial AI OS is a private finance and trading AI system built to keep user experience, product capability, runtime control, governance, intelligence, execution, knowledge, state, and infrastructure from collapsing into one another.

## Canonical Baseline

The current canonical structure and layer semantics are defined in [architecture-baseline](./architecture-baseline.md).

## Canonical Reference

See [architecture-baseline](./architecture-baseline.md) first, then [architecture-diagram](./architecture-diagram.md) for the main layer diagram, core data flow, and boundary reminders.

## Canonical Responsibility Surfaces

1. Experience Layer
2. Capability Layer
3. Orchestration Layer
4. Governance Layer
5. Intelligence Layer
6. Execution Layer
7. State Layer
8. Knowledge Layer
9. Infrastructure Layer

## Why This Shape

This version is intentionally more engineering-oriented than a concept stack:

- It makes user-visible capabilities explicit.
- It keeps governance independent for finance-specific control.
- It separates model intelligence from action execution.
- It separates state truth from accumulated knowledge.
- It stays light enough for a single-node MVP while remaining migration-friendly.

## Concrete Directory Mapping

- Experience Layer -> `apps/`
- Capability Layer -> `capabilities/` and `domains/`
- Orchestration Layer -> `orchestrator/`
- Governance Layer -> `governance/`
- Intelligence Layer -> `intelligence/`
- Execution Layer -> `execution/`, `skills/`, `tools/`
- State Layer -> `state/`
- Knowledge Layer -> `knowledge/`
- Infrastructure Layer -> `infra/`

## High-Level Runtime

`apps/` receives requests, `capabilities/` frames them as product actions, `orchestrator/` builds the runtime plan, `intelligence/` produces structured reasoning, `governance/` decides what is allowed, `execution/` performs real actions, `state/` records fact, and `knowledge/` accumulates reusable lessons and guidance.

## Migration Note

The current implementation still lives partly in `pfios/`. The older eight-layer repo skeleton remains part of migration history, but current design work should follow the nine-surface baseline defined in [architecture-baseline](./architecture-baseline.md).
