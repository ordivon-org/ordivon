# ADR-002: Knowledge Versus State

## Status

Accepted

## Decision

Separate long-lived learned material from operational source-of-truth records.

## Knowledge

Knowledge includes wiki pages, memory entries, postmortems, theses, research notes, and retrieval indexes.

## State

State includes positions, orders, risk budget, task status, approvals, report metadata, and user preferences that answer what is true right now.

## Consequences

- Wiki content cannot be treated as a ledger.
- Agent memory cannot override canonical state.
- Retrieval systems remain advisory unless explicitly persisted through state services.
