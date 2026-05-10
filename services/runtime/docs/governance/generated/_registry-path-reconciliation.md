# Registry–Path Reconciliation Report

> **GENERATED VIEW — DO NOT EDIT**
> Generated: 2026-05-10 20:42 UTC
> Source: `docs/governance/generated/registry-path-reconciliation.json`
> Authority: supporting_evidence
> **Not source of truth. Not raw evidence. Text view only.**

---

## Summary

- Registry entries: 456
- Path Map nodes: 2073
- In both: 456
- Only registry: 0
- Only path map: 1617
- Findings: 2 BLOCKING, 119 DEGRADED

---

## BLOCKING Findings

### RPR-4 [BLOCKING] — `src/ordivon_verify/checker_registry.py`

**Finding**: Authority 'source_of_truth' (risk 5) too high for route 'source-code' (risk 1)
**Disposition Candidate**: A3 — Redesign the governance mechanism — Registry and Path Map are both locally correct, but the system lacks an intermediate model to reconcile them.

**Registry Claim**:
- authority: `source_of_truth`
- risk_tier: `5`

**Path Observation**:
- route: `source-code`
- risk_tier: `1`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-4 [BLOCKING] — `src/ordivon_verify/schemas/pgi-evidence-record.schema.json`

**Finding**: Authority 'source_of_truth' (risk 5) too high for route 'source-code' (risk 1)
**Disposition Candidate**: A3 — Redesign the governance mechanism — Registry and Path Map are both locally correct, but the system lacks an intermediate model to reconcile them.

**Registry Claim**:
- authority: `source_of_truth`
- risk_tier: `5`

**Path Observation**:
- route: `source-code`
- risk_tier: `1`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

---

## DEGRADED Findings

### RPR-3 [DEGRADED] — `docs/governance/verification-signal-classification.md`

**Finding**: doc_type 'runbook' may not fit route 'governance-core' (expects: ['governance_pack', 'methodology', 'template', 'checker', 'tooling', 'proposal', 'receipt', 'ledger', 'root_context', 'architecture', 'design_spec', 'schema', 'supporting_evidence', 'inventory', 'triage', 'boundary', 'red_team', 'tracker'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `runbook`

**Path Observation**:
- route: `governance-core`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/product/ordivon-verify-package-file-manifest.json`

**Finding**: doc_type 'schema' may not fit route 'product-docs' (expects: ['product', 'architecture', 'design_spec', 'stage_summit', 'proposal', 'runbook', 'receipt'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `schema`

**Path Observation**:
- route: `product-docs`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runbooks/newcomer-execution-flow.md`

**Finding**: doc_type 'runbook' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `runbook`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/README.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/adp-2r-redteam-remediation.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/adp-3-closure-seal.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/agent-native-evidence-import-report-round-1.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/agent-native-evidence-round-1.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/candidate-rule-review-path.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/coding-pack-dogfood-evidence.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/coding-trust-adoption-hermes-dogfood-round-2.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/coding-trust-adoption-round-1-receipt.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/coverage-aware-governance-cov-1.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/cpr-1-closure-seal.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/cross-pack-dogfood-evidence.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/ctts-2-template-localization-dogfood-receipt.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/ctts-3-agent-native-evidence-pack-receipt.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/ctts-closure-seal.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/db-backed-runtime-evidence-audit.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

### RPR-3 [DEGRADED] — `docs/runtime/demo-full-flow-receipt.md`

**Finding**: doc_type 'receipt' may not fit route 'ai-boundaries' (expects: ['ai_onboarding', 'phase_boundary', 'runtime', 'boundary', 'context', 'supporting_evidence', 'architecture', 'design_spec', 'current-system-map', 'knowledge-map', 'reading-graph', 'template', 'tooling'])
**Disposition Candidate**: A2 — Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.

**Registry Claim**:
- doc_type: `receipt`

**Path Observation**:
- route: `ai-boundaries`

**Not Claimed**:
- This finding does not prove Registry is wrong.
- This finding does not prove Path Map is wrong.
- This finding requires A1/A2/A3/A4 review before action.

_... and 99 more DEGRADED findings_

---

## Disposition Reference

- **A1**: Fix the Registry claim — owner, doc_type, authority, or lifecycle is incorrect. The declaration does not match the governed reality.
- **A2**: Refine the Path Map observation rule — a new doc_type is not covered, a route is too narrow, or a classification rule needs updating.
- **A3**: Redesign the governance mechanism — Registry and Path Map are both locally correct, but the system lacks an intermediate model to reconcile them.
- **A4**: Record as formal debt — this gap is intentional (legacy, external, not yet governable). Must not be silently ignored.

---

```text
READY means selected checks passed; it does not authorize execution.
```
