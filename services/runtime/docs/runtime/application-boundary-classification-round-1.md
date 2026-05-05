# Application Boundary Classification Round 1

Status: **CLOSED** | Date: 2026-05-05 | Phase: GWOS-2026-P1
Tags: `application-boundary`, `packs`, `adapters`, `registry`, `architecture`
Authority: `supporting_evidence` | AI Read Priority: 2

## Purpose

This report classifies application-layer directories after the completeness
red-team audit. It complements the source-of-truth architecture boundary:

```text
docs/architecture/ordivon-governance-application-boundary.md
```

The key distinction:

```text
self-governed_now = Ordivon Verify's own governance infrastructure
governed_target   = application work Ordivon can verify through gates/cases
deferred          = non-source, generated, data, or future-surface material
```

## Classification

| Path | Classification | Rationale | Next governance action |
|---|---|---|---|
| `docs/` | self-governed_now | document registry + document governance checkers cover it. | keep registry completeness hard. |
| `tests/` | self-governed_now | artifact registry covers tests as evidence assets. | register new tests immediately. |
| `scripts/` | self-governed_now | artifact registry covers governance scripts and compatibility symlinks. | keep canonical/deprecated labels clear. |
| `domains/` | self-governed_now | artifact registry covers domain models. | register new domain semantics. |
| `src/ordivon_verify/` | self-governed_now | artifact registry covers Verify source. | keep public wedge boundary checks. |
| `checkers/` | self-governed_now | checker registry + maturity ledger cover checker packages. | no promotion without red-team evidence. |
| `apps/` | governed_target | app code is governed through lint/type/test/security gates, not per-file registry. | consider owner manifest coverage, not artifact registry expansion. |
| `packs/` | governed_target | pack behavior is domain governance target. | add pack review templates in Phase 6. |
| `adapters/` | governed_target | adapters are integration targets; verify-only boundaries must be clear. | add read-only adapter evidence fixtures later. |
| `execution/` | governed_target | execution engine must remain separated from Verify trust signals. | future authority-boundary audit. |
| `knowledge/` | governed_target | content/memory hygiene surface. | Phase 4 memory/content checks. |
| `skills/` | governed_target | skill-like capability surface. | Phase 4 skill safety review. |
| `capabilities/` | governed_target | capability declarations can confuse can/may boundaries. | future capability manifest review. |
| `governance_engine/` | governed_target | runtime governance logic, governed by tests/gates. | consider owner manifest coverage. |
| `build/` | deferred_with_rationale | generated build output. | keep excluded from source registry. |
| `data/` | deferred_with_rationale | local data, not governance source. | only register if promoted to governed evidence. |
| `wiki/` | deferred_with_rationale | generated or working knowledge surface. | include in content hygiene, not document registry by default. |

## Decision

The application layer is not a registry bug by default. It becomes a bug when a
file claims to be governance authority, checker evidence, maturity evidence, or
public wedge source while staying outside the relevant registry.

## Boundary

This classification does not approve application behavior, adapter execution,
broker access, public release, or external deployment. It only records the
current governance boundary.
