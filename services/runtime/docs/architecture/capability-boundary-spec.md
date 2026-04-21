# Capability Boundary Spec

This document freezes the capability boundary for product closure work.

## Purpose

- Keep product-facing truth fixes moving without letting capability drift into a generic middle layer.
- Make abstraction type explicit for every current capability.
- Block new page-driven capabilities while closure is in progress.

## Primary Slicing Rule

Classify capability code by `domain object + domain action` first.

- `domain`: stable object reads or lifecycle transitions
- `workflow`: multi-step business actions or composite outputs
- `view`: product aggregates and artifact listings
- `diagnostic`: technical or governance-facing read adapters

## Hard Boundary

Capability code may:

- expose product-facing methods
- normalize contracts for API and UI consumers
- depend on `domains/`, `orchestrator/`, `governance/`, `intelligence/`, and `execution/`

Capability code must not:

- invent new business truth in the frontend or router layer
- absorb page naming as the primary abstraction
- hide orchestration behind vague `*And*` method names
- accept side-effecting calls without `actor`, `context`, `reason`, and `idempotency_key`

## Composite Contracts

The following contracts are explicitly non-domain composites:

- `AnalyzeResult`: workflow composite
- `DashboardResult`: view aggregate
- `ValidationSummaryResult`: diagnostic summary

## Naming Rules

- prefer object or action names: `recommendations`, `reviews`, `analyze`
- avoid page names as capabilities
- avoid multi-stage `*And*` methods inside capability APIs
- document abstraction type in module docstrings or inventory docs

## Current Capability Classification

| Capability | Type | Notes |
| --- | --- | --- |
| `analyze` | workflow | analyze-and-suggest composite |
| `recommendations` | domain | recommendation object reads and lifecycle updates |
| `reviews` | workflow | review drafting and completion |
| `dashboard` | view | homepage aggregate |
| `reports` | view | report artifact listing |
| `audits` | view | audit record listing |
| `evals` | diagnostic | regression eval read adapter |
| `validation` | diagnostic | validation summary plus bounded issue intake |
