# RPR Finding Triage

> **GENERATED VIEW — DO NOT EDIT**
> Generated: 2026-05-10T21:11:31Z
> Source: `docs/governance/generated/registry-path-reconciliation.json`
> This report classifies findings. It does NOT fix them.

---

## Enforcement Semantics

Finding severity and gate enforcement are separate dimensions:

| Finding Severity | Gate Enforcement | Meaning |
|---|---|---|
| BLOCKING | ENFORCED | CI gate blocks on this finding |
| BLOCKING | NOT_ENFORCED | Finding severity is BLOCKING but gate is advisory — STATE SEMANTICS GAP |
| DEGRADED | NOT_ENFORCED | Non-blocking observation, informational |
| DEGRADED | SHADOW | Non-blocking, shadow-mode collection |

**Critical rule**: BLOCKING while NOT_ENFORCED creates a state semantics gap.
This must be resolved — either enforce or reclassify.

---

## Summary

- Total findings: 122
- By severity: {'blocking': 3, 'degraded': 119}
- By code: {'RPR-1': 1, 'RPR-3': 119, 'RPR-4': 2}
- By disposition: {'A1': 1, 'A2': 119, 'A3': 2, 'A4': 0}

---

## A1 — Fix registry claims — stale owner, wrong doc_type, incorrect

- Count: 1

| Code | Severity | Enforced | Path | Message |
|---|---|---|---|---|
| RPR-1 | blocking | no | `docs/product/gos-pm3-authority-taxonomy-plan.md` | Registry claims 'docs/product/gos-pm3-authority-taxonomy-pla |

## A2 — Refine path-map rules — missing route, narrow coverage, rule

- Count: 119

| Code | Severity | Enforced | Path | Message |
|---|---|---|---|---|
| RPR-3 | degraded | no | `docs/governance/verification-signal-classification.md` | doc_type 'runbook' may not fit route 'governance-core' (expe |
| RPR-3 | degraded | no | `docs/product/ordivon-verify-package-file-manifest.json` | doc_type 'schema' may not fit route 'product-docs' (expects: |
| RPR-3 | degraded | no | `docs/runbooks/newcomer-execution-flow.md` | doc_type 'runbook' may not fit route 'ai-boundaries' (expect |
| RPR-3 | degraded | no | `docs/runtime/README.md` | doc_type 'receipt' may not fit route 'ai-boundaries' (expect |
| RPR-3 | degraded | no | `docs/runtime/adp-2r-redteam-remediation.md` | doc_type 'receipt' may not fit route 'ai-boundaries' (expect |
| ... | ... | ... | _and 114 more_ | |

## A3 — Redesign authority/mechanism model — source_of_truth too coa

- Count: 2

| Code | Severity | Enforced | Path | Message |
|---|---|---|---|---|
| RPR-4 | blocking | YES | `src/ordivon_verify/checker_registry.py` | Authority 'source_of_truth' (risk 5) too high for route 'sou |
| RPR-4 | blocking | YES | `src/ordivon_verify/schemas/pgi-evidence-record.schema.json` | Authority 'source_of_truth' (risk 5) too high for route 'sou |

---

## RPR-4 Disposition (Authority Model Gap)

The 2 BLOCKING RPR-4 findings reveal that `source_of_truth` is used for both
document truth AND implementation/schema authority. These are different
authority domains.

**Disposition**: A3 — Authority Taxonomy Redesign

Not A1 (fixing the claim) because the files ARE authoritative for their domains.
Not A2 (fixing the route) because the route risk model is correct.

The authority model needs to distinguish:
- Document truth: `doc_source_of_truth` / `current_status` / `supporting_evidence`
- Implementation source: `implementation_source`
- Schema definition: `schema_source`
- Generated view: `generated_view` / `derived_view`

**Status**: OPEN — pending authority model redesign (PM-3 or later).
