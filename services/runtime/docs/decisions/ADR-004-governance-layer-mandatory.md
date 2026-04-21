# ADR-004: Governance Layer Is Mandatory

## Status

Accepted

## Decision

Any decision that constrains recommendations, automation, persistence, or approval thresholds must pass through the governance layer.

## Rationale

Risk logic scattered across routes, prompts, and workflows becomes impossible to audit or update consistently.

## Consequences

- Governance cannot be an optional helper.
- Route handlers and workflows call into governance instead of re-implementing risk checks locally.
- Auditable policy changes become feasible.
