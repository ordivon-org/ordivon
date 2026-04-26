# Ordivon Documentation

> Last updated: 2026-04-26

## Purpose

This directory is the single entry point for all project documentation. Every document
here must be accessible within two clicks from this file.

## Directory Map

| Directory | Purpose | Authoritative? |
|-----------|---------|----------------|
| `architecture/` | Canonical architecture baseline, layer definitions, boundary specs, ADRs | Yes |
| `runtime/` | Completed runtime baseline records, H-stage closure docs, bridge specs | Yes |
| `roadmap/` | H-stage plans, P4/P5 briefs, known debt, current execution plans | Yes |
| `audits/` | Audit reports, findings registers, remediation plans, document inventories | Yes |
| `archive/` | Historical documents, completed batch records, superseded reports | No |
| `decisions/` | Architecture Decision Records (ADR-001 through ADR-005) | Yes |
| `product/` | Product specs, MVP briefs, quality matrix, templates | Mixed — see inventory |
| `runbooks/` | Operational procedures for local dev, monitoring, incident response | Yes |
| `tasks/` | Task cards and templates (mostly completed — see archive candidates) | No |
| `schemas/` | Cross-layer contract documentation (placeholder) | Incomplete |
| `workflows/` | Durable workflow descriptions | Yes |

## Authoritative Entry Points

These documents define the current system identity. Start here:

1. **Architecture Baseline** — `docs/architecture/architecture-baseline.md`
   The canonical architecture baseline as of 2026-04-22. All other architecture docs defer to this.

2. **Architecture Language** — `docs/architecture/LANGUAGE.md`
   Shared vocabulary for all Ordivon/PFIOS architecture discussions.

3. **State Truth Boundary** — `docs/architecture/state-truth-boundary.md`
   Hard boundary between SQLAlchemy ORM (domain truth) and DuckDB (analytics). Tagged H-2, P4-prep.

4. **H-1: Real Model Under Control** — `docs/runtime/h1-real-model-under-control.md`
   Closed. Proves an external real model (DeepSeek) runs inside Ordivon governance.

5. **Documentation Inventory** — `docs/audits/docs-inventory.md`
   Complete inventory of all 89 docs/ markdown files with classifications and recommended actions.

## Current System Identity

The project is tracked under the working identity **AegisOS / CAIOS** with the external
brand anchor **Ordivon** reserved for future use. The repository directory name remains
`financial-ai-os` and user rules use `PFIOS`. See `docs/naming.md` and
`docs/architecture/aegisos-working-identity.md` for the full naming convention.

## Current Phase

**H-6: Plan-Only Receipt** — see `docs/roadmap/h6-plan-only-receipt-plan.md`.

Previous phases:
- H-1 through H-5: completed — see `docs/runtime/h2-to-h5-closure-summary.md`
- Phase 4 (Personal Control Loop): in progress — see `docs/tasks/phase-4-personal-control-loop-brief.md`

## Quick Links

- [Architecture Baseline](architecture/architecture-baseline.md)
- [Documentation Inventory](audits/docs-inventory.md)
- [H-1 Closure](runtime/h1-real-model-under-control.md)
- [H-2 to H-5 Summary](runtime/h2-to-h5-closure-summary.md)
- [H-6 Plan](roadmap/h6-plan-only-receipt-plan.md)
- [State Truth Boundary](architecture/state-truth-boundary.md)
- [Naming Convention](architecture/aegisos-working-identity.md)
