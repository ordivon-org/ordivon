# Finance Pack v1 Definition

## Status

This document defines the first domain-pack identity mounted on the current PFIOS baseline:

**Finance Pack v1**

It does not require an immediate repository move into `packs/finance/`.

It freezes the semantic boundary first.

## Purpose

PFIOS now has enough real system structure that the next architectural mistake would be treating current finance-domain objects as if they were universal system primitives.

This document prevents that mistake.

It defines:

- what Finance Pack v1 is
- which objects and workflows belong to it
- what it depends on from `core`
- what should remain adapters
- what should not be pulled into `core`

## One-Sentence Definition

Finance Pack v1 is:

**the first concrete domain implementation mounted on the PFIOS core, covering finance-oriented analysis, recommendation, review, outcome, validation, and finance-derived learning flows.**

## What Finance Pack v1 Is Responsible For

Finance Pack v1 owns finance-domain meaning.

That includes:

- market-facing analysis semantics
- recommendation semantics
- review semantics tied to recommendation lifecycle
- recommendation outcome interpretation
- finance-specific validation meaning
- finance-specific lesson extraction and recurring issue semantics
- finance-facing product surfaces

Compressed:

**Core owns order. Finance Pack v1 owns current domain meaning.**

## Scope

### 1. Domain objects

These current nouns should be treated as Finance Pack v1 objects:

- `Recommendation`
- `Review`
- `OutcomeSnapshot` as currently interpreted in recommendation lifecycle
- `Issue` as currently used by validation/journal workflow
- `Portfolio`
- `Market` and symbol-oriented inputs
- finance research/reporting objects and summaries

Important nuance:

Some of these may later split into:

- reusable `core` primitives
- plus finance-specific shapes

But **their current repository semantics are finance-domain semantics**.

### 2. Workflows

These current workflow meanings belong to Finance Pack v1:

- analyze-and-suggest flow
- recommendation generation flow
- review submit / complete flow
- outcome backfill flow tied to recommendation review
- validation issue reporting as currently used in finance/product stability

Important nuance:

The workflow engine is not finance-pack.

The workflow content is.

### 3. Policies and judgments

These are currently Finance Pack v1 concerns:

- recommendation status meaning
- review verdict interpretation
- finance-oriented governance hints
- finance-specific risk interpretation rules
- finance-specific lesson extraction mappings
- finance recurring-issue normalization rules

Important nuance:

The policy **framework** belongs to `core`.

The policy **content** belongs to the pack.

### 4. Action families

These current action families should be treated as Finance Pack v1 action families:

- `recommendation_generate`
- `recommendation_status_update`
- `review_submit`
- `review_complete`
- `validation_issue_report`

Important nuance:

`ActionRequest`, `ActionReceipt`, and `FailureModel` remain `core`.

The action family meaning is Finance Pack v1.

### 5. Knowledge derivation

These current learning flows belong to Finance Pack v1:

- lesson extraction from review/outcome
- knowledge hint summaries shown on recommendation/review surfaces
- recurring issue aggregation over finance lesson narratives
- finance-specific mapping from review completion into governance/intelligence hints

Important nuance:

`Lesson`, `KnowledgeEntry`, `FeedbackPacket`, and retrieval primitives are `core`.

The current extractors and mappings are Finance Pack v1.

### 6. Product surfaces

These current surfaces are Finance Pack v1 surfaces:

- recommendation dashboard cards
- pending review queue and review detail panel
- finance analyze workspace
- recommendation / review trace surfaces as currently shaped
- finance validation summary surface

Important nuance:

`TrustTier`, `MissingState`, `TraceSurface`, `OutcomeSurface`, and `HintSurface` semantics are `core`.

The current cards and workflows are Finance Pack v1.

## Current Repository Mapping

These current areas should be read as the first finance pack implementation.

### Strongest Finance Pack v1 zones

- `domains/strategy/`
- `domains/journal/`
- `domains/market/`
- `domains/portfolio/`
- `domains/research/`
- finance-facing portions of `domains/reporting/`
- finance-facing portions of `domains/risk/`
- finance-facing capabilities in `capabilities/workflow/`
- finance-facing capabilities in `capabilities/domain/`
- finance-facing validation capability paths
- finance-facing dashboard/analyze/review surfaces in `apps/`
- recommendation/review/validation action families in `execution/adapters/`
- finance lesson extraction and recurring issue mappings in `knowledge/`

### Mixed zones that currently contain finance pack logic

- `apps/api/app/api/v1/`
- `apps/web/src/components/features/`
- `capabilities/contracts/`
- `intelligence/feedback.py`
- `governance/feedback.py`
- `orchestrator/workflows/analyze.py`

These are mixed because they combine:

- reusable system mechanism
- current finance-domain meaning

## What Finance Pack v1 Depends On From Core

Finance Pack v1 should depend on the following core primitives rather than redefine them.

### Workflow core

- workflow engine
- step lifecycle
- run tracking
- retry / fallback / compensation semantics

### Governance core

- `DecisionLanguage`
- `ActionContext`
- policy source framework
- audit framework

### Execution core

- `ActionRequest`
- `ActionReceipt`
- failure semantics
- idempotency semantics

### State core

- trace bundle mechanics
- relation semantics
- source-of-truth discipline
- persisted run and action lineage

### Knowledge core

- `Lesson`
- `KnowledgeEntry`
- `FeedbackPacket`
- recurring issue primitive
- retrieval primitive

### Runtime core

- task contract
- runtime abstraction
- context building interfaces

### Experience core

- `TrustTier`
- `MissingState`
- truthful object-surface semantics

## What Finance Pack v1 Must Not Own

Finance Pack v1 must not redefine:

- workflow laws
- governance decision language
- request/receipt discipline
- trace relation semantics
- state truth rules
- runtime abstraction contracts
- trust-tier semantics

If it starts owning those, the pack is leaking into core.

## What Should Stay Adapter, Not Finance Pack

The following should not be treated as finance-domain semantics even if Finance Pack v1 uses them heavily:

- Hermes bridge
- provider integrations
- OpenAI/Anthropic/Hermes runtime implementations
- DuckDB/Postgres backend integration
- report/wiki write transport
- notification or tool connectors

These are implementation integrations.

They belong to adapters.

## Immediate Practical Rules

Use these rules for new code now.

### Rule 1

If a new object only makes sense for recommendations, reviews, market symbols, finance outcome judgment, or portfolio interpretation, put it on the Finance Pack v1 side of the boundary.

### Rule 2

If a new mechanic is needed by future finance, research, ops, and compliance packs alike, design it in `core`.

### Rule 3

If a new implementation is about external runtimes, tools, storage, or connectors, make it an `adapter`.

### Rule 4

Do not move finance nouns into `core` just because finance is the first working pack.

### Rule 5

Do not let Finance Pack v1 own provider or backend implementation details.

## Migration Guidance

The correct migration order is:

1. freeze core primitives
2. classify current code
3. explicitly name current finance stack as `Finance Pack v1`
4. separate adapter seams
5. only then consider physical moves to `packs/finance/`

That means this document is a semantic baseline, not a folder-move script.

## Future Relationship To Other Packs

Finance Pack v1 is the first pack, not the last one.

It should later coexist with packs such as:

- `research pack`
- `ops pack`
- `compliance pack`
- `personal cognition pack`

The purpose of freezing Finance Pack v1 now is to ensure later packs can be added without rewriting core around finance assumptions.

## Non-Goals

This document does not:

- declare finance to be the whole identity of PFIOS
- demote finance as unimportant
- immediately move code into a new `packs/finance/` directory
- claim every current finance boundary is already pure

## Final Summary

Finance Pack v1 is the current repository's first real domain pack.

It owns:

- finance-domain objects
- finance-domain workflows
- finance-domain policy meaning
- finance-domain action families
- finance-domain knowledge extraction
- finance-domain product surfaces

It should consume `core` primitives and `adapter` integrations, not redefine them.

Compressed:

**PFIOS core provides order. Finance Pack v1 provides the current business meaning mounted on that order.**
