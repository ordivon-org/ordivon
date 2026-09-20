# Agent Service retirement R23

Date: 2026-09-20
Status: RETIRED

## Decision

The historical Ordivon Agent Service is retired rather than modernized. Its responsibilities now resolve directly to natural owners: Host for semantic task continuity, Harness for bounded Agent Run continuity, Runtime for physical execution truth, Distribution/provider APIs for external effects, provider/OAuth systems for identity and credentials, and MCP/A2A/mature workflow or orchestration systems for interoperability and coordination.

## Liveness census before deletion

- systemd unit ordivon-agent-service-canary-mcp.service: not installed and inactive;
- TCP 8894: not listening;
- reverse systemd dependencies: none;
- cross-repository named consumers of the canary/service modules: zero;
- only numeric 8894 matches outside the repository were unrelated data/lockfile values.

## Removed forward surfaces

- agent_service Python package;
- read-only Agent Service MCP canary;
- canary systemd deployment recipe;
- Agent-Service-only typing/import-linter configuration and runtime dependencies;
- Agent-Service-specific test/support files.

Historical knowledge graphs, evidence and migration records remain provenance only. They are not supported runtime surfaces.

## Non-regression

policies/external-ownership-boundary.json now carries an empty Agent Service type ceiling and explicit retirement record. Reintroduction of the old subsystem is not an accepted compatibility path.
