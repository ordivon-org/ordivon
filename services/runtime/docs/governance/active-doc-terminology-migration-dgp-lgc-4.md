# Active Docs Terminology Migration — DGP-LGC-4

Status: **CLOSED** | Date: 2026-05-09 | Phase: DGP-LGC-4
Authority: supporting_evidence | Owner: Governance

## Action: MINIMAL, TARGETED

Reduced PFIOS/AegisOS terms in our own LGC governance documents from 16 to 0. All 111 architecture/audit/runtime/product docs deferred to LGC-5.

## Files Edited (4)

| File | Before | After |
|---|---|---|
| legacy-cleanup-risk-matrix-dgp-lgc-0.md | 2 | 0 |
| data-stateful-classification-dgp-lgc-2.md | 4 | 0 |
| generated-artifact-quarantine-dgp-lgc-1.md | 4 | 0 |
| archive-active-path-historical-docs-dgp-lgc-3.md | 2 | 0 |

## Files Deferred (112)

| Category | Count | Reason |
|---|---|---|
| Architecture docs | 25 | Design context, not naming cleanup |
| Audit reports | 15 | Historical evidence |
| Runtime docs | 12 | Operational context |
| Product/roadmap | 8 | Active product docs |
| Plans/debt | 7 | Active planning docs |
| Runbooks | 4 | Operational |
| README/naming | 2 + naming.md | High-traffic entry points |
| All scripts/tests/policies | 39 | Code, not docs |

All deferred to LGC-5 triage. No code, scripts, tests, policies, or architecture-baseline.md touched.

## Verification

```
184 tests passed
ordivon-verify document-governance --check: 0 BLOCKED, 0 DEGRADED
```
