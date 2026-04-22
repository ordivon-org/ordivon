# Finance Pack Extraction Plan

## Purpose

This document freezes the first extraction boundary for `packs/finance` without performing a directory migration.

The goal is to prevent finance-specific defaults from continuing to leak into `core` behavior while keeping the current repo stable.

## Keep In Core

These remain core primitives and should not be reassigned to `packs/finance`:

- `DecisionLanguage`
- `ActionRequest / ActionReceipt`
- `TraceLink`
- `Outcome` primitive semantics
- `FeedbackPacket` primitive semantics
- `AgentRuntime` interface
- `MemoryPolicy`
- `WorkflowRun / TaskRun` primitives
- governance approval primitives
- execution adapter registry / progress primitives

## Move To Finance Pack Later

These are finance-specific and should move behind `packs/finance` later:

- `MarketContext`
- `PortfolioContext`
- symbol/timeframe-aware analysis context defaults
- trading limits policy
- market/news/broker tools
- finance-specific recommendation rendering and wording
- market / portfolio / trading domain packages

## Finance-specific But Can Stay Temporarily

These remain tolerated in-place until later extraction:

- `domains/strategy/*` pieces tightly coupled to recommendation/outcome behavior
- `domains/research.models.AnalysisRequest` symbol/timeframe fields
- `capabilities/workflow/analyze.py` current finance-shaped request handling
- `orchestrator/context/context_builder.py` while it still builds finance-shaped defaults

## Candidate Inventory Anchors

The first extraction candidates are tracked in:

- [packs/finance/inventory](../../packs/finance/inventory.md)

## Wrong Placement To Avoid

- Do not convert finance nouns into new core primitives
- Do not hide finance semantics inside `orchestrator/` and call them generic runtime context
- Do not move Hermes/runtime ownership into finance-pack planning

## Not Doing

- No directory migration
- No import rewrites
- No behavior changes
- No finance naming cleanup across the repo

## Confirmation

This module does **not**:

- re-inject finance semantics into core
- re-promote Hermes into system identity
- promote hints into truth or policy
