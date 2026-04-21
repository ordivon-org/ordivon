# ADR-001: Repository Structure

## Status

Accepted

## Canonical Note

This ADR establishes the eight-layer decision.

The current authoritative interpretation of that decision lives in [architecture-baseline](../architecture/architecture-baseline.md). If older migration-era wording conflicts with the baseline, the baseline wins unless a newer ADR supersedes it.

## Decision

Adopt an eight-layer architecture:

1. Experience Layer
2. Capability Layer
3. Orchestration Layer
4. Governance Layer
5. Intelligence Layer
6. Execution Layer
7. Knowledge and State Layer
8. Infrastructure Layer

With the current concrete repository mapping:

- `apps/` for Experience
- `capabilities/` and `domains/` for Capability
- `orchestrator/` for Orchestration
- `governance/` for Governance
- `intelligence/` for Intelligence
- `execution/`, `skills/`, and `tools/` for Execution
- `knowledge_state/`, `knowledge/`, and `state/` for Knowledge and State
- `infra/` for Infrastructure

## Rationale

The system's failure mode is not lack of features. It is boundary collapse: routes becoming business engines, capabilities remaining implicit, governance hidden inside prompts, wiki mixed with system truth, and scripts growing into a second runtime.

## Consequences

- New modules have a default home.
- Architectural review gets simpler.
- The architecture is more product-facing and easier to evolve incrementally.
- Existing `pfios/` code can be migrated gradually without forcing a big-bang rewrite.
