# ADP-3 Closure — Structure-Aware + Registry-Aware + PV-Aware Detector Seal

Status: **CLOSED** | Date: 2026-05-02 | Phase: ADP-3-S
Tags: `adp-3`, `closure`, `seal`, `detector`, `structure`, `registry`, `pv`, `debt`
Authority: `supporting_evidence` | AI Read Priority: 2

## Closure Summary

ADP-3 hardens the ADP detector beyond line/window regex scanning to include
structure-aware (HAP-3), registry-aware (DG), and public-surface-aware (PV)
detection. It inherits ADP2R red-team debt and partially remediates the
highest-value detector-facing portions.

Implementation commit: `ebc6714`
Seal commit: (this commit)

## Rule Inventory

### Structure-Aware (HAP-3 objects)

| Rule | Severity | Description |
|------|----------|-------------|
| ADP3-PLAN-EXEC | blocking | TaskPlan READY without authorization denial or claims execution permission |
| ADP3-PLAN-C4 | blocking | C4 TaskPlan not BLOCKED/REVIEW_REQUIRED |
| ADP3-PLAN-C5 | blocking | C5 TaskPlan not NO_GO |
| ADP3-PLAN-PPATH | degraded | Protected paths without boundary_statement |
| ADP3-REVIEW-DETECTOR | blocking | Detector PASS treated as authorization |
| ADP3-REVIEW-COMMENT | blocking | COMMENT_ONLY treated as approval |
| ADP3-REVIEW-CLOSURE-SCOPE | blocking | APPROVED_FOR_CLOSURE with dangerous scope (execution/deployment/broker) |
| ADP3-CR-BINDING | blocking | CandidateRule status implies binding policy |

### DG Registry-Aware

| Rule | Severity | Description |
|------|----------|-------------|
| ADP3-DG-SUPERSEDED | blocking | Entry marked current while superseded_by is non-null |
| ADP3-DG-AI-STALE | degraded | High-priority AI doc is superseded/archived |
| ADP3-DG-STALENESS | degraded | High-priority AI doc missing last_verified/stale_after_days |
| ADP3-DG-DEGRADED-LIFECYCLE | degraded | DEGRADED entry missing owner/stale_after_days/due_stage |
| ADP3-DG-RECEIPT-AUTH | blocking | Receipt/ledger described as action authorization |

### PV Public-Surface-Aware

| Rule | Severity | Description |
|------|----------|-------------|
| ADP3-PV-RELEASE | blocking | PV doc claims package published/public repo/license/production-ready |
| ADP3-PV-WEDGE | blocking | PV doc collapses wedge into core |
| ADP3-PV-READY | blocking | PV doc uses READY as approval |
| ADP3-PV-PACKAGE-SAFETY | degraded | PV package doc missing private-core boundary disclaimer |
| ADP3-PV-CHANGELOG-CONFUSION | degraded | Changelog conflates internal receipt with public release |

### Red-Team Debt-Aware (ADP2R inherited)

| Rule | Severity | Description |
|------|----------|-------------|
| AP-RT-CONFIG-GUARD | degraded | Config guard cited as safety proof without invariant tests/evidence |

## ADP2R Inherited Debt Disposition

| Debt ID | Status | Evidence |
|---------|--------|----------|
| CONFIG-GUARD-001 | partially mitigated | AP-RT-CONFIG-GUARD rule added; open unless ledger says closed |
| DEGRADED-LIFECYCLE-001 | mitigated | ADP3-DG-DEGRADED-LIFECYCLE rule verified; close via debt ledger |
| PATH-BRITTLENESS | partially mitigated | Broader PV detection by content + path; not fully resolved |
| FRESHNESS-001 | partially mitigated | ADP3-DG-STALENESS rule added; registry schema upgrade required for full mitigation |
| CODE-FENCE-001 | open | Code fence false positives in safe docs not fully resolved |
| RECEIPT-SCOPE-001 | open | Receipt checker has 7 patterns; semantic gaps remain |

## Things Not Created

No API, SDK, MCP server, SaaS endpoint, package release, public standard,
public repo, live adapter, live harness transport, runtime enforcement,
CI enforcement, broker/API integration, credential access, external tool
execution, action authorization, binding policy activation.

## Things Not Claimed

No compliance, certification, endorsement, partnership, equivalence,
production readiness, public release, license activation.

## Known Limitations

- Static detector can miss semantic context.
- Registry-aware checks depend on registry correctness.
- PV checks are conservative and may need safe-context allowlists.
- Detector does not prove safety.
- Detector does not authorize action.
- Detector does not execute tools.
- Detector does not publish, package, release, or change repo visibility.
- Detector does not replace human review.

## Detector Boundaries

- Detector PASS is review evidence only, NOT authorization.
- Absence of findings is NOT proof of safety.
- Public wedge (Ordivon Verify) ≠ full private core.
- No package has been published. No public repo has been created.
- No license has been activated. No release program has been opened.
- can_read_credentials is the accepted field. can_access_secrets must not be reintroduced.
- CandidateRule remains NON-BINDING.

## Next Recommended Phase

DG-1 / DGP-1 — Document Governance Pack hardening.
ADP-3 now depends on DG registry metadata (freshness, supersession, AI read priority).
Hardening the DG substrate before further detector expansion is the correct next move.
