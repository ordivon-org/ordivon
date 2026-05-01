# OGAP Object Model v0

> v0 / prototype. Not a public standard. Objects may change before public alpha.

## 1. WorkClaim

What an external system claims it did or proposes to do.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| claim_id | Yes | string | Unique claim identifier |
| actor | Yes | string | Who/what made the claim |
| task_type | Yes | string | Category of task |
| claim | Yes | string | Human-readable claim description |
| changed_objects | Yes | list | Files/resources changed |
| evidence_bundle | Yes | object | Reference to EvidenceBundle |
| coverage_report | Yes | object | Reference to CoverageReport |
| debt_declaration | Yes | object | Known limitations |
| authority_statement | Yes | string | Evidence/authority disclaimer |
| requested_decision | No | string | Desired governance outcome |

Prohibited overclaims:
- "all tests passed" without scope
- "verified" without evidence bundle
- "complete" without coverage declaration

## 2. EvidenceBundle

Tests, logs, diffs, receipts, artifacts, screenshots, reports, command outputs.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| bundle_id | Yes | string | Unique bundle identifier |
| work_claim_id | Yes | string | Linked WorkClaim |
| diffs | No | array | File diffs |
| test_results | No | array | Test execution results |
| command_outputs | No | array | Shell command outputs |
| receipts | No | array | Receipt references |
| artifacts | No | array | Artifact references |
| screenshot_refs | No | array | Screenshot references |
| report_refs | No | array | Report references |
| gaps | No | array | Missing evidence |
| evidence_quality | No | string | self_reported / machine_verified / human_reviewed |

Prohibited overclaims:
- "all evidence provided" when gaps exist
- "verified" when quality is self_reported

## 3. ExecutionReceipt

What actually changed, what commands ran, what passed/failed/skipped.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| receipt_id | Yes | string | Unique receipt identifier |
| work_claim_id | Yes | string | Linked WorkClaim |
| commands_run | Yes | array | Commands executed |
| files_changed | Yes | array | Files modified |
| passed_checks | Yes | array | Checks that passed |
| failed_checks | Yes | array | Checks that failed |
| skipped_checks | No | array | Checks not run |
| verification_commands_run | No | array | Verification commands executed |
| unexpected_side_effects | No | array | Side effects not in plan |

Prohibited overclaims:
- "all checks passed" when failed/skipped exist
- "clean" when unexpected_side_effects exist

## 4. CoverageReport

What universe was covered, excluded, and unknown.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| report_id | Yes | string | Unique report identifier |
| claimed_universe | Yes | string | What the checker claims to cover |
| discovery_method | Yes | string | How objects were discovered |
| included_objects | Yes | array | Objects covered |
| excluded_objects | No | array | Objects excluded with reason |
| unknown_objects | No | array | Objects not discovered |
| pass_scope_statement | Yes | string | What PASS actually means |
| coverage_percentage | No | number | estimated / reported |
| confidence | No | string | low / medium / high / unknown |

Prohibited overclaims:
- "100% coverage" without discovery method
- PASS without scope statement

## 5. CapabilityManifest

What the external adapter can technically do.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| adapter_id | Yes | string | Unique adapter identifier |
| adapter_type | Yes | string | agent / tool / MCP / IDE / CI / framework |
| capabilities | Yes | object | Capability flags |
| side_effect_classes | Yes | array | Classes of side effects possible |
| no_go_actions | Yes | array | Actions explicitly prohibited |
| authority_required_for | Yes | array | Actions requiring authority request |
| receipt_required | Yes | boolean | Whether receipt is required for actions |
| trust_level | Yes | string | untrusted / self_reported / ... / governance_native |

Core invariant: **can_X does not imply may_X.**

## 6. AuthorityRequest

What the external adapter asks permission to do.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| request_id | Yes | string | Unique request identifier |
| adapter_id | Yes | string | Linked adapter |
| requested_action | Yes | string | What action is proposed |
| side_effect_class | Yes | string | From side-effect class taxonomy |
| risk_level | Yes | string | low / medium / high / blocking |
| required_gate | Yes | string | Minimum governance gate |
| human_approval_required | Yes | boolean | Whether human must approve |
| rollback_plan | No | string | How to undo |
| evidence_required | No | string | Minimum evidence standard |
| no_go_check | Yes | boolean | Explicitly checks if action is NO-GO |

Prohibited overclaims:
- "low risk" when side_effect_class is financial/production
- requesting NO-GO action without override justification

## 7. ToolCallLedger

What tools were called, with side-effect classification.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| ledger_id | Yes | string | Unique ledger identifier |
| adapter_id | Yes | string | Linked adapter |
| entries | Yes | array | ToolCallEntry objects |
| summary | Yes | object | Counts per side-effect class |

ToolCallEntry:
| Field | Required | Type | Description |
|---|---|---|---|
| call_id | Yes | string | Unique call identifier |
| tool_name | Yes | string | Name of tool invoked |
| tool_args_summary | Yes | string | Summary of arguments |
| side_effect_class | Yes | string | Side-effect classification |
| timestamp | Yes | string | ISO timestamp |
| exit_code | Yes | number | Tool exit code |
| output_summary | No | string | Summary of output |
| authority_request_ref | No | string | If authorization was obtained |

## 8. DebtDeclaration

Known limitations, skipped checks, blockers, unresolved issues.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| declaration_id | Yes | string | Unique declaration identifier |
| work_claim_id | Yes | string | Linked WorkClaim |
| known_gaps | Yes | array | Known coverage/verification gaps |
| skipped_checks | No | array | Checks not performed with reason |
| blockers | No | array | Blocking issues |
| unresolved_items | No | array | Items requiring follow-up |
| accepted_risks | No | array | Risks accepted with justification |
| external_debt_refs | No | array | References to external debt trackers |

Prohibited overclaims:
- "no debt" when gaps exist
- skipping without reason

## 9. GovernanceDecision

READY / DEGRADED / BLOCKED / HOLD / REJECT / NO-GO.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| decision_id | Yes | string | Unique decision identifier |
| work_claim_id | Yes | string | Linked WorkClaim |
| decision | Yes | string | READY / DEGRADED / BLOCKED / HOLD / REJECT / NO-GO |
| decision_scope | Yes | string | What this decision covers |
| evidence_summary | Yes | string | Summary of evidence reviewed |
| coverage_summary | Yes | string | Summary of coverage |
| hard_failures | No | array | Reasons for BLOCKED/REJECT |
| warnings | No | array | Warnings (DEGRADED) |
| authority_statement | Yes | string | Must state: "evidence, not authorization" |
| next_action | No | string | Recommended next action |
| human_review_required | No | boolean | Whether human must review |

## 10. TrustReport

Human/agent/CI readable summary of evidence, coverage, debt, and decision.

| Field | Required | Type | Description |
|---|---|---|---|
| schema_version | Yes | string | "0.1" |
| report_id | Yes | string | Unique report identifier |
| decision_ref | Yes | string | Linked GovernanceDecision |
| actor | Yes | string | Who/what this report is for |
| summary | Yes | string | Human-readable summary |
| evidence_quality | Yes | string | Rating of evidence |
| coverage_confidence | Yes | string | Confidence in coverage |
| debt_status | Yes | string | Summary of outstanding debt |
| risk_assessment | Yes | string | Overall risk level |
| authority_note | Yes | string | "READY is evidence, not authorization." |

---

*Created: 2026-05-01*
*Phase: OGAP-1*
*Version: v0 (prototype)*
