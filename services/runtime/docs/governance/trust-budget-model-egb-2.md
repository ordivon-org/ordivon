# Trust Budget Model (EGB-2)

Status: **CURRENT** | Date: 2026-05-05 | Phase: EGB-2
Tags: `egb-2`, `trust-budget`, `delivery-metrics`, `diagnostic`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Trust budget turns governance degradation into a visible diagnostic signal.
It is inspired by reliability budget thinking, but it is not an SLO, compliance
claim, or production-readiness claim.

## Metrics

The first read-only reporter tracks:

- `missing_evidence_count`
- `degraded_count`
- `blocked_count`
- `stale_source_count`
- `registry_drift_count`
- `open_debt_count`
- `checker_shadow_count`
- `rework_placeholder`

These metrics are diagnostic. They do not rank people, authorize action, or
replace review.

## Budget Interpretation

If trust budget is spent, the correct response is not to hide warnings. The
stage should stop expanding scope and repair evidence, tests, ownership,
registry drift, stale sources, or checker coverage before continuing.

## Boundary

Trust budget output is evidence only. It does not authorize merge, release,
deployment, publication, trading, policy activation, or external action.
