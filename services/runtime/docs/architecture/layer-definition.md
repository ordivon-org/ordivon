# Layer Definition

This file defines layer responsibilities. For the canonical current-state and target-state baseline, see [architecture-baseline](./architecture-baseline.md).

## Experience Layer

Concrete home: `apps/`

Allowed: routes, pages, chat entrypoints, dashboard flows, response adapters, auth entrypoints, worker bootstrap.

Forbidden: core business rules, prompt bodies, risk policy truth, hidden workflow sprawl inside handlers.

## Capability Layer

Concrete home: `capabilities/` plus domain-facing modules in `domains/`

Allowed: user-visible product capabilities such as market brief, asset analysis, portfolio review, trade journal, postmortem, strategy search, and thesis workflows.

Forbidden: direct ownership of raw connector code, model provider glue, or infrastructure details.

## Orchestration Layer

Concrete home: `orchestrator/`

Allowed: workflows, routing, scheduling, runtime control, retry, fallback, dispatch, result normalization, context assembly.

Forbidden: owning risk rules, direct low-level storage details, prompt text bodies.

## Governance Layer

Concrete home: `governance/`

Allowed: risk engine, policy engine, permissions, audit policy, output levels, HITL gates, automation boundaries, safety guards.

Forbidden: being bypassed by capability handlers, prompts, or convenience scripts.

## Intelligence Layer

Concrete home: `intelligence/`

Allowed: model adapters, prompt templates, task definitions, embeddings, evaluators, output schemas, model selection policy.

Forbidden: owning canonical state or acting as the hidden execution layer.

## Execution Layer

Concrete home: `execution/`, `skills/`, `tools/`

Allowed: skills, tools, connectors, report generators, wiki writers, notification emitters, parser utilities, backtest helpers.

Forbidden: mixing raw execution with governance truth or user-experience flow ownership.

## Knowledge and State Layer

Concrete home: `knowledge_state/`, `knowledge/`, `state/`

Allowed in `knowledge/`: wiki, memory, indexes, retrieval, ingestion, theses, postmortems, journals.

Allowed in `state/`: schemas, repositories, migrations, snapshots, state services, source-of-truth records.

Forbidden: treating knowledge as live system truth or treating state storage as a dumping ground for narrative memory.

## Infrastructure Layer

Concrete home: `infra/`

Allowed: local runtime configuration, deployment, monitoring, secrets templates, containers, storage wiring, queues, operational scripts.

Forbidden: business logic growth by convenience.

## Shared Utilities

Concrete home: `shared/`

Allowed: narrow generic primitives such as config, logging, time, generic errors, and value objects with no domain ownership.

Forbidden: domain leakage.
