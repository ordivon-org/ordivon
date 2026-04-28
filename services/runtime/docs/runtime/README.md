# Runtime Docs

Completed runtime baseline records, H-stage closure documents, and bridge specifications.

## H-Stage Closure Documents

| Document | Stage | Status | Date |
|----------|-------|--------|------|
| [policy-platform-closure-review.md](policy-platform-closure-review.md) | Policy Platform Phase 5 Closure | **CLOSED** | 2026-04-29 |
| [h1-real-model-under-control.md](h1-real-model-under-control.md) | H-1: One Real Model Under Control | **CLOSED** | 2026-04-26 |
| [h2-to-h5-closure-summary.md](h2-to-h5-closure-summary.md) | H-2 through H-5 Summary | **CLOSED** | 2026-04-26 |

## What Each H-Stage Proved

- **H-1**: A real external model (DeepSeek) can run inside the Ordivon governance framework, producing real analysis through the full governance/audit/receipt chain.
- **H-2**: SQLAlchemy ORM is the single source of truth; DuckDB is analytics-only. Hard invariant for P4+.
- **H-2A**: Shared architecture vocabulary (LANGUAGE.md) is documented and enforced.
- **H-3**: Review → Lesson → KnowledgeFeedback loop is closed end-to-end.
- **H-4**: DecisionIntake payloads are validated with discipline rules before reaching governance.
- **H-5**: Governance hard gate enforces 12 rules: reject > escalate > execute priority.

## Evidence & Audit

| Document | Purpose | Date |
|----------|---------|------|
| [h9-dogfood-protocol.md](h9-dogfood-protocol.md) | H-9 dogfood protocol | 2026-04-26 |
| [h9-evidence-report.md](h9-evidence-report.md) | H-9 evidence report | 2026-04-26 |
| [coding-pack-dogfood-evidence.md](coding-pack-dogfood-evidence.md) | Coding Pack 10-run evidence | 2026-04-28 |
| [cross-pack-dogfood-evidence.md](cross-pack-dogfood-evidence.md) | Cross-Pack 20-run evidence | 2026-04-28 |
| [runtime-evidence-baseline.md](runtime-evidence-baseline.md) | Runtime evidence checker baseline | 2026-04-28 |
| [db-backed-runtime-evidence-audit.md](db-backed-runtime-evidence-audit.md) | DB-backed audit evidence | 2026-04-28 |
| [eval-corpus-v1-plan.md](eval-corpus-v1-plan.md) | Eval Corpus v1 plan | 2026-04-28 |
| [repo-governance-cli.md](repo-governance-cli.md) | Repo Governance CLI prototype | 2026-04-28 |

## Verification Platform

| Document | Purpose | Date |
|----------|---------|------|
| [verification-ci-gate-plan.md](verification-ci-gate-plan.md) | Verification Platform CI gate plan | 2026-04-28 |

## CandidateRule & Policy

| Document | Purpose | Date |
|----------|---------|------|
| [candidate-rule-review-path.md](candidate-rule-review-path.md) | CandidateRule human review path | 2026-04-28 |
| [policy-proposal-path.md](policy-proposal-path.md) | PolicyProposal draft path | 2026-04-28 |

- [Hermes Runtime Bridge Runbook](../runbooks/hermes-runtime-bridge.md) — operational runbook for the standalone bridge
- [Hermes Model Layer Integration](../architecture/hermes-model-layer-integration.md) — pre-H-1 design doc (needs rewrite)

## Related Docs

- [Architecture Baseline](../architecture/architecture-baseline.md) — canonical architecture
- [State Truth Boundary](../architecture/state-truth-boundary.md) — H-2 boundary spec
- [H-6 Plan](../roadmap/h6-plan-only-receipt-plan.md) — current phase
