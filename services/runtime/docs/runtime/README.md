# Runtime Docs

Completed runtime baseline records, H-stage closure documents, and bridge specifications.

## H-Stage Closure Documents

| Document | Stage | Status | Date |
|----------|-------|--------|------|
| [h1-real-model-under-control.md](h1-real-model-under-control.md) | H-1: One Real Model Under Control | **CLOSED** | 2026-04-26 |
| [h2-to-h5-closure-summary.md](h2-to-h5-closure-summary.md) | H-2 through H-5 Summary | **CLOSED** | 2026-04-26 |

## What Each H-Stage Proved

- **H-1**: A real external model (DeepSeek) can run inside the Ordivon governance framework, producing real analysis through the full governance/audit/receipt chain.
- **H-2**: SQLAlchemy ORM is the single source of truth; DuckDB is analytics-only. Hard invariant for P4+.
- **H-2A**: Shared architecture vocabulary (LANGUAGE.md) is documented and enforced.
- **H-3**: Review → Lesson → KnowledgeFeedback loop is closed end-to-end.
- **H-4**: DecisionIntake payloads are validated with discipline rules before reaching governance.
- **H-5**: Governance hard gate enforces 12 rules: reject > escalate > execute priority.

## Bridge Specifications

- [Hermes Runtime Bridge Runbook](../runbooks/hermes-runtime-bridge.md) — operational runbook for the standalone bridge
- [Hermes Model Layer Integration](../architecture/hermes-model-layer-integration.md) — pre-H-1 design doc (needs rewrite)

## Related Docs

- [Architecture Baseline](../architecture/architecture-baseline.md) — canonical architecture
- [State Truth Boundary](../architecture/state-truth-boundary.md) — H-2 boundary spec
- [H-6 Plan](../roadmap/h6-plan-only-receipt-plan.md) — current phase
