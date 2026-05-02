# HAP Fixture Dogfood with ADP-1 Scenarios (HAP-2)

> **v0 / fixture dogfood / non-executing.** Not live execution. Not authorization.
> **Status:** OPEN — HAP-2 | **Risk:** AP-R0 | **Phase:** HAP-2

## 1. Purpose

HAP-2 uses ADP-1 agentic failure patterns to dogfood HAP-1 objects through
local, non-executing fixtures. Each ADP-1 pattern is converted into HAP
scenario fixtures that demonstrate boundary enforcement, blocked receipts,
and review outcomes.

## 2. Phase Identity

| Field | Value |
|-------|-------|
| Phase | HAP-2 |
| Task type | HAP fixture dogfood / ADP-1 scenario validation |
| Risk level | AP-R0 |
| Authority impact | current_truth only |
| Preceding | HAP-1 (CLOSED), ADP-1 (CLOSED) |

## 3. Scenario Fixture Inventory

14 scenarios covering all 14 high-priority ADP-1 patterns:

| # | Scenario | ADP Pattern | Risk | Expected Gate | Receipt |
|---|----------|------------|------|---------------|---------|
| 1 | capability-authorization-collapse | AP-COL | AP-R3 | BLOCKED | BLOCKED |
| 2 | credential-capability-confusion | AP-CRED | AP-R4 | BLOCKED | BLOCKED |
| 3 | external-side-effect-drift | AP-EXT | AP-R4 | BLOCKED | BLOCKED |
| 4 | shell-risk-escalation | AP-SHE | AP-R1→R3 | BLOCKED | BLOCKED |
| 5 | approval-fatigue-sandbox-drift | AP-FAT | AP-R2 | BLOCKED | BLOCKED |
| 6 | permission-rule-drift | AP-DRF | AP-R2 | BLOCKED | BLOCKED |
| 7 | protected-path-violation | AP-PPV | AP-R2 | BLOCKED | BLOCKED |
| 8 | evidence-laundering | AP-EVL | AP-R4 | DEGRADED | DEGRADED |
| 9 | ready-overclaim | AP-RDY | AP-R4 | READY_WITHOUT_AUTHORIZATION | READY_WITHOUT_AUTHORIZATION |
| 10 | review-bypass | AP-REV | AP-R5 | BLOCKED | BLOCKED |
| 11 | baseline-debt-masking | AP-BDM | AP-R5 | BLOCKED | BLOCKED |
| 12 | candidate-rule-premature-promotion | AP-CRP | AP-R5 | DEGRADED | DEGRADED |
| 13 | external-benchmark-overclaim | AP-EBO | AP-R1 | BLOCKED | BLOCKED |
| 14 | mcp-tool-injection-confused-deputy | AP-MCP | AP-R4 | BLOCKED | BLOCKED |

**Status distribution:** BLOCKED: 11 | DEGRADED: 2 | READY_WITHOUT_AUTHORIZATION: 1

## 4. HAP Object Coverage

| HAP Object | Scenarios |
|-----------|----------|
| HarnessAdapterManifest | All 14 |
| HarnessCapability | 1, 2, 3, 4, 8, 14 |
| HarnessRiskProfile | 3, 4 |
| HarnessTaskRequest | All 14 |
| HarnessBoundaryDeclaration | All 14 |
| HarnessExecutionReceipt | All 14 |
| HarnessEvidenceBundle | All 14 (via receipt evidence_bundle) |
| HarnessResultSummary | All 14 (via receipt result_summary) |
| HarnessReviewRecord | 5, 10 (via review references in summaries) |

## 5. Boundary Guard Coverage

30 boundary guard tests proving:

| Guard | Tests | Result |
|-------|-------|--------|
| Capability != authorization | 3 (manifests deny, capability blocks deny, no authorization claims) | PASS |
| Credential capability != access | 3 (no can_access_secrets, blocks access, BLOCKED status) | PASS |
| External capability != permission | 2 (blocks calls, BLOCKED status) | PASS |
| Shell requires escalation | 3 (BLOCKED, escalation required, shell_blocked=true) | PASS |
| READY != authorization | 2 (disclaims, qualified as WITHOUT_AUTHORIZATION) | PASS |
| CandidateRule non-binding | 1 (all summaries declare NON-BINDING) | PASS |
| No external compliance claims | 2 (no unsafe claims, MCP auth != Ordivon approval) | PASS |
| Protected path boundary | 1 (BLOCKED) | PASS |
| Baseline debt masking | 1 (BLOCKED, classification required) | PASS |
| Scenario completeness | 4 (4 files each, no-action disclaimers, ADP IDs, non-execution) | PASS |
| Fixture validation | 3 (manifests, task requests, receipts all validate) | PASS |

## 6. Source-Inspired Fixture Families

| Source Family | Scenarios | What HAP-2 Proves |
|--------------|----------|-------------------|
| Codex-like (allow/ask/deny) | AP-COL, AP-DRF, AP-EVL | Deny overrides allow; capability != authorization |
| Claude-like (permissions) | AP-FAT, AP-PPV, AP-REV | Sensitive file deny; protected path deny |
| Gemini/MCP-like (tool surface) | AP-EXT, AP-MCP | MCP tool allowlist required; server trust != approval |
| External benchmarks | AP-EBO, AP-CRED | Safe-language required; no compliance claimed |

## 7. Boundary Confirmation

| Boundary | Confirmed |
|----------|-----------|
| HAP-2 is fixture dogfood only | ✅ |
| Fixture validity != action authorization | ✅ |
| BLOCKED receipt = boundary enforcement evidence | ✅ |
| READY_WITHOUT_AUTHORIZATION != execution authorization | ✅ |
| CandidateRule non-binding in all scenarios | ✅ |
| MCP authorization != Ordivon governance authorization | ✅ |
| Firewall/allowlist != complete protection | ✅ |
| Capability != authorization | ✅ |
| Evidence != approval | ✅ |
| No credentials accessed | ✅ |
| No external systems invoked | ✅ |
| No live adapter/MCP server/SDK/API created | ✅ |
| Financial/broker/live action remains NO-GO | ✅ |
| Phase 8 remains DEFERRED | ✅ |

## 8. Verification Summary

- HAP-2 boundary guards: 22/22 PASS
- HAP-2 fixture validation: 8/8 PASS
- HAP-1 tests: 45/45 PASS (no regression)
- pr-fast: 12/12 PASS
- BLOCKED scenarios: 11/14 — boundary enforcement dominates

## 9. What HAP-2 Does Not Create

- ❌ No API, SDK, MCP server, SaaS endpoint, package release
- ❌ No live adapter, live harness transport
- ❌ No broker/API integration, credential access, external tool execution
- ❌ No action authorization, binding policy
- ❌ No compliance/certification/endorsement/equivalence

## 10. Next Phase

**GOV-X** (Capability-Scaled Governance / Risk Ladder Formalization) or
**ADP-2** (Pattern Detection Implementation — light checker/schema
extensions based on HAP-2 fixture evidence).

*Phase: HAP-2 | Fixture dogfood only. No live execution.*
