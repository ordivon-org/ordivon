# Boundary Map

## Purpose

This document defines the default ownership rules for the most active parts of the current repository.

It exists to reduce drift during ongoing migration work.

## Ownership Matrix

### Domains

- `domains/research`
  - owns analysis semantics
  - owns research-facing result objects
- `domains/strategy`
  - owns recommendations
  - owns recommendation outcome meaning
- `domains/journal`
  - owns reviews
  - owns lessons
  - owns journal-facing issues

### State

- `state/db`
  - owns database base/session/bootstrap foundation
- `state/usage`
  - owns operational usage counters and snapshots

### Governance

- `governance/risk_engine`
  - owns allow/block and policy-facing risk decisions
- `governance/audit`
  - owns audit persistence and traceability

## Default Questions

Use these questions to decide placement:

- "What did we conclude?" -> `domains/research` or `domains/strategy`
- "What did we learn?" -> `domains/journal`
- "What is true right now operationally?" -> `state/*`
- "What is the system allowed to do?" -> `governance/*`
- "How do we prove what the system did?" -> `governance/audit`

## Important Boundary Decisions

### Outcome

Outcome stays in `domains/strategy` for now because it measures whether a recommendation thesis worked.

### Issue

Issue stays in `domains/journal` for now because it is used as a review and validation learning artifact, not yet as a governance incident object.

### Usage

Usage belongs to `state/usage` because it is an operational fact, not business meaning.

## Anti-Patterns

- do not put policy enforcement into domain repositories
- do not store operational counters in domain packages
- do not use governance packages as a dumping ground for all cross-cutting logic
- do not reintroduce migrated truth modules back into `pfios/*`
