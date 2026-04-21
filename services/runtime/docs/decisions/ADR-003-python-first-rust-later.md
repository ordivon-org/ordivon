# ADR-003: Python First, Rust Later

## Status

Accepted

## Decision

Use Python for the backend and orchestration path during the MVP stage. Preserve room for Rust only where performance or packaging pressure justifies it later.

## Rationale

The current complexity is architectural, not low-level performance. Introducing multiple primary runtime languages too early would increase coordination and migration cost.

## Consequences

- Python remains the default for domain, orchestration, governance, and intelligence work.
- TypeScript remains the default for web UI.
- Rust can be introduced later behind narrow interfaces rather than as a parallel core stack.
