# Legacy Triage Next Actions — DGP-LGC-5

Status: **CLASSIFIED** | Date: 2026-05-09 | Phase: DGP-LGC-5
Authority: supporting_evidence | Owner: Governance

## Architecture-baseline.md: KEEP_ACTIVE_BRIDGE

Decision: Retain as active architecture bridge document.
34 referring files include navigation (README.md), registry (current-truth-entry-map, document-registry), policy (constitution.md), workflow, and architecture docs. Cannot archive without a successor. Future LGC-5A should plan successor/split before any archive attempt.

## Deferred File Triage: 88 files classified

| Area | Files | Action |
|---|---|---|
| docs/architecture | 30 | keep_legacy_qualified (24), safe_doc_rename_future (3), script_triage (3) |
| docs/runtime | 16 | keep_legacy_qualified (all — operational context) |
| docs/audit | 11 | keep_legacy_qualified (all — historical evidence) |
| docs/product | 9 | keep_legacy_qualified (all) |
| docs/governance | 6 | keep_legacy_qualified (all) |
| docs/plans | 6 | keep_legacy_qualified (3), script_triage (3) |
| docs/runbooks | 4 | keep_legacy_qualified (4) |
| docs/ai + docs/README | 2 | safe_doc_rename_future (R1 — navigation impact) |
| Other | 4 | keep_legacy_qualified |

Verdict: 82 of 88 files should keep legacy-qualified naming. Only 8 files are safe-doc-rename candidates. No broad migration recommended.

## Script/Test/Policy/Alembic: 34 unique files classified

| Area | Files | Action |
|---|---|---|
| tests/ | 20 | test_triage_required — may be active test fixtures or legacy |
| scripts/ | 18 | script_triage_required — may be active, obsolete, or generated |
| policies/ | 1 | policy_review_required — trading_limits.yaml, needs separate Trading phase |
| alembic/ | 1 | migration_do_not_edit — historical migration records |
| source_code | 2 | code_reentry_review — legacy code references |

Verdict: No safe edits possible. All require dedicated sub-phases.

## Follow-up Phase Queue

| Phase | Scope | Priority |
|---|---|---|
| LGC-5A | Architecture baseline successor/bridge plan | MEDIUM |
| LGC-5B | Safe doc rename (8 files: docs/ai/, docs/README.md) | LOW |
| LGC-5C | Script inventory (18 scripts — active/obsolete/generated) | MEDIUM |
| LGC-5D | Test/E2E expectation review (20 test files) | MEDIUM |
| LGC-5E | Policy/alembic boundary (trading_limits.yaml + migration records) | HIGH (requires Trading phase) |
| LGC-5F | Source code legacy ref review (2 files) | LOW |
| LGC-S | Legacy governance stage summit | FINAL |

DO NOT EXECUTE these sub-phases now. They are classified, not authorized.
