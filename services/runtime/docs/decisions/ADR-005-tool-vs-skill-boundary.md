# ADR-005: Tool Versus Skill Boundary

## Status

Accepted

## Decision

Treat tools as atomic integrations and skills as reusable higher-level capabilities.

## Tool

A tool performs one bounded interaction with the outside world or a narrow utility action, such as fetching market data, writing a file, sending a notification, or querying a broker API.

## Skill

A skill composes tools, intelligence, and business intent into a reusable capability such as generating a morning brief or drafting a review.

## Consequences

- Tool tests stay narrow and deterministic.
- Skills remain composable.
- Workflows can orchestrate skills without inheriting raw connector complexity.
