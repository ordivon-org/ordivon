## Module
Audit Event Strictification

## Philosophy
- 真相必须单独存在
- 失败必须结构化

## Layer
Governance / State

## Type
Core

## Owner
Governance audit owner

## Current Value
- Audit writes now produce a structured envelope at write time.
- Audit surfaces can distinguish structured records from legacy unstructured records.

## Remaining Gap
- Existing legacy rows still need migration if we want every audit row to be first-class structured truth.
- Some downstream tests and readers still rely on transitional top-level compatibility keys inside `payload_json`.

## Immediate Action
- Normalize audit writes through a strict envelope builder.
- Treat legacy rows honestly as `legacy_unstructured` instead of inferring product fields from arbitrary payloads.

## Affected Chain
- execution / workflow write -> audit repository -> audit API surface

## Invariant
- Audit top-level product fields are write-time truth, not read-time inference.
- Legacy rows may be surfaced, but must be marked as legacy instead of guessed into modern semantics.

## Wrong Placement To Avoid
- Do not reconstruct audit truth inside the API or React surfaces.
- Do not let arbitrary payload keys redefine governance-grade audit meaning.

## Not Doing
- No DB schema migration in this patch.
- No historical backfill script yet.

## Required Test Pack
- unit: strict envelope write normalization
- unit: legacy row downgrade behavior
- integration: audit product surface remains stable

## Done Criteria
- New audit writes are stored as structured envelopes.
- Legacy rows no longer require guessed decision/summary fields at read time.
- Product audit surface remains stable under CI.
