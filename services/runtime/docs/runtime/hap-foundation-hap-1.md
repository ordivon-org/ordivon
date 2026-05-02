# HAP Foundation — Runtime Evidence (HAP-1)

> **Status:** OPEN
> **Date:** 2026-05-02
> **Authority:** supporting_evidence
> **Related:** docs/architecture/harness-adapter-protocol-hap-1.md

## Phase Identity

| Field | Value |
|-------|-------|
| Phase | HAP-1 |
| Task type | Protocol foundation / harness adapter boundary design / local-only schema scaffold |
| Risk level | R0 |
| Authority impact | current_truth only |
| Preceding phase | OGAP-Z (CLOSED) |

HAP is adjacent to OGAP, not a replacement. OGAP (Ordivon Governance Adapter
Protocol) is CLOSED — OGAP-1, OGAP-2, OGAP-3, OGAP-Z are all CLOSED. HAP
describes the harness surface; OGAP governs the external adapter protocol.

## HAP Object Model v0

HAP-1 defines 10 objects for describing harness adapter surfaces.

### 1. HarnessAdapterManifest

Declares adapter identity, supported harness family, declared boundaries,
local schema version, and non-execution status.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| schema_version | Yes | string | "0.1" |
| adapter_id | Yes | string | Unique adapter identifier |
| harness_family | Yes | string | e.g., "hermes", "codex", "claude-code", "gemini-cli" |
| adapter_type | Yes | string | "agent", "mcp_server", "ide", "ci", "worker", "custom" |
| declared_boundaries | Yes | object | HarnessBoundaryDeclaration ref |
| capabilities | Yes | object | HarnessCapability ref |
| risk_profile | Yes | object | HarnessRiskProfile ref |
| non_execution_statement | Yes | string | "This manifest describes capability only. It does not execute." |
| authority_statement | Yes | string | Capability declaration ≠ authorization disclaimer |

### 2. HarnessCapability

Declares technical capabilities only. Capability is not authorization.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| can_read_files | Yes | boolean | Can read workspace files |
| can_write_files | Yes | boolean | Can write/modify workspace files |
| can_apply_patch | Yes | boolean | Can apply targeted file patches |
| can_run_shell | Yes | boolean | Can execute shell commands |
| can_use_browser | Yes | boolean | Can interact with browser |
| can_use_mcp | Yes | boolean | Can connect to MCP servers |
| can_read_credentials | Yes | boolean | Technical ability to read credential-like material |
| can_call_external_api | Yes | boolean | Can make outbound API calls |
| supports_streaming_events | No | boolean | Can emit streaming events |
| supports_resume | No | boolean | Can resume from interrupted state |
| supports_structured_output | No | boolean | Can produce structured output |
| supports_cost_reporting | No | boolean | Can report token/cost usage |
| supports_worktree_isolation | No | boolean | Can operate in isolated worktree |
| max_context_tokens | No | integer | Maximum context window size |
| default_timeout_seconds | No | integer | Default task timeout |
| authority_statement | Yes | string | "can_X does not imply may_X. Capabilities listed do not authorize action." |

### 3. HarnessRiskProfile

Classifies harness risk surfaces.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| risk_level | Yes | string | "read_only", "workspace_write", "shell", "external_side_effect" |
| risk_reason | Yes | string | Why this risk level |
| mitigations | Yes | array | Risk mitigation measures |
| boundary_enforcement | Yes | string | How boundaries are enforced locally |

### 4. HarnessTaskRequest

Describes a requested task shape. Task request is not approval.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| schema_version | Yes | string | "0.1" |
| request_id | Yes | string | Unique request identifier |
| adapter_id | Yes | string | Linked adapter |
| task_type | Yes | string | Category of task |
| description | Yes | string | What is being asked |
| requested_capabilities | Yes | array | Capabilities the task needs |
| boundary_declaration | Yes | object | HarnessBoundaryDeclaration ref |
| authority_statement | Yes | string | "This task request describes intent only. It does not authorize execution." |

### 5. HarnessTaskPlan

Describes a proposed plan. Plan is not execution permission.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| plan_id | Yes | string | Unique plan identifier |
| request_id | Yes | string | Linked task request |
| steps | Yes | array | Proposed execution steps |
| estimated_capabilities | Yes | array | Expected capability usage per step |
| rollback_strategy | No | string | How to revert if needed |
| authority_statement | Yes | string | "This plan is a proposal only. It does not authorize execution." |

### 6. HarnessBoundaryDeclaration

Describes allowed and forbidden surfaces.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| allowed_actions | Yes | array | Actions permitted within this boundary |
| forbidden_actions | Yes | array | Actions explicitly not permitted |
| requires_review_for | Yes | array | Actions needing human review |
| credential_access_blocked | Yes | boolean | Whether credential access is blocked |
| external_api_blocked | Yes | boolean | Whether external API calls are blocked |
| shell_blocked | Yes | boolean | Whether shell execution is blocked |

### 7. HarnessExecutionReceipt

Records claimed or simulated execution evidence. Receipt is not approval.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| schema_version | Yes | string | "0.1" |
| receipt_id | Yes | string | Unique receipt identifier |
| request_id | Yes | string | Linked task request |
| plan_id | Yes | string | Linked task plan |
| commands_run | Yes | array | Commands actually executed |
| files_changed | Yes | array | Files modified |
| passed_checks | Yes | array | Checks that passed |
| failed_checks | Yes | array | Checks that failed |
| skipped_checks | No | array | Checks not run |
| evidence_bundle | Yes | object | HarnessEvidenceBundle ref |
| authority_statement | Yes | string | "This receipt records what was executed. It does not authorize future action." |

### 8. HarnessEvidenceBundle

Collects logs, command evidence, file evidence, test evidence, and runtime
evidence references.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| bundle_id | Yes | string | Unique bundle identifier |
| receipt_id | Yes | string | Linked execution receipt |
| log_refs | No | array | Log file references |
| command_outputs | No | array | Shell command output refs |
| file_evidence | No | array | File change evidence refs |
| test_results | No | array | Test execution results |
| gaps | No | array | Missing evidence |
| evidence_quality | No | string | "self_reported" / "machine_verified" / "human_reviewed" |

### 9. HarnessResultSummary

Summarizes execution status.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| result_id | Yes | string | Unique result identifier |
| receipt_id | Yes | string | Linked execution receipt |
| status | Yes | string | "READY", "DEGRADED", "BLOCKED", "FAILED", "REVIEW_REQUIRED" |
| status_reason | Yes | string | Why this status |
| warnings | No | array | Advisory warnings |
| authority_statement | Yes | string | "READY means evidence adequate for review. It does not authorize execution." |

### 10. HarnessReviewRecord

Captures review status, boundary findings, violations, known debt, and
candidate rule suggestions.

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| review_id | Yes | string | Unique review identifier |
| receipt_id | Yes | string | Linked execution receipt |
| reviewer | Yes | string | Who performed review |
| findings | Yes | array | Review findings |
| boundary_violations | Yes | array | Boundary violations found |
| known_debt | No | array | Known debt items identified |
| candidate_rule_suggestions | No | array | Suggested CandidateRules |
| verdict | Yes | string | "approved_as_evidence", "needs_rework", "rejected" |

## Closure Predicate (HAP-1)

HAP-1 can be marked CLOSED only when:

1. HAP v0 docs exist.
2. HAP object model is defined (10 objects).
3. HAP boundaries are explicit.
4. AI onboarding is updated.
5. Registry/wiki are updated if docs are added.
6. HAP does not create live execution surfaces.
7. No forbidden files or systems are modified.
8. All required applicable verification is run and accounted for.
9. Known skipped/flaky verification is documented.
10. New AI Context Check passes.
