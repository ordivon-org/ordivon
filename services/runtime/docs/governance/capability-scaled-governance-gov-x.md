# Capability-Scaled Governance v0 (GOV-X)

> **v0 / internal governance / non-executing.** Not execution authorization.
> Not binding policy activation. Not compliance.
> **Phase:** GOV-X | **Risk:** AP-R0 | **Authority:** current_truth only

## Identity

GOV-X formalizes Ordivon's internal capability-scaled governance model.
It converts the lessons from OGAP-Z, HAP-1/2, EGB-1, and ADP-1 into a
structured ladder: Capability → Risk → Authority → Gate → Evidence → Review.

GOV-X does not:
- Authorize execution
- Activate binding policy
- Claim compliance with any external framework
- Replace OGAP, HAP, ADP, or EGB

## Safe-Language Clause

> GOV-X references external AI governance and coding-agent documentation as
> benchmark inputs for internal comparison only. These references do not imply
> compliance, certification, endorsement, partnership, equivalence, production
> readiness, or public-standard status.

## 1. Capability Classes (C0-C5)

| Class | Name | Scope | Default Gate |
|-------|------|-------|-------------|
| **C0** | Documentation / taxonomy | Docs, mappings, source ledgers, stage notes. No execution. No external side effect. | READY_WITHOUT_AUTHORIZATION |
| **C1** | Read-only interpretation | File reading, grep/search, summarization. No file modification, no shell write, no external calls. | READY_WITHOUT_AUTHORIZATION |
| **C2** | Workspace write / patch | File edits, patch generation, doc/code modifications. No shell unless gated. No credentials. No external calls. | REVIEW_REQUIRED |
| **C3** | Shell / build / test | Local commands, test runs, builds, migration dry-runs. No credentials. No external side effects unless separately gated. | REVIEW_REQUIRED |
| **C4** | External / credential / MCP | Credential-like materials, external APIs, MCP tools, browser, network egress, external systems. | **BLOCKED by default** |
| **C5** | Live / irreversible | Broker/API trading, live financial action, production deployment, destructive operations. | **NO-GO in current state** |

### C4 Hard Boundary

C4 capabilities are BLOCKED by default. They may only proceed to
REVIEW_REQUIRED under:
1. Explicit phase authorization with Allowed/Forbidden sections
2. Governance review record
3. Credential non-access proof (credential_access_blocked=true)
4. External side-effect block confirmation

C4 never auto-authorizes. No evidence alone can override C4 BLOCKED.

### C5 Hard Boundary

C5 capabilities are NO-GO under current project state. They cannot be
authorized by review, evidence, or gate response. Only a future explicit
phase with Allowed/Forbidden sections can reopen C5.

## 2. Risk Ladder (AP-R0 through AP-R5)

| Level | Name | Capability Equivalent | Allowed Responses |
|-------|------|----------------------|-------------------|
| **AP-R0** | Mapping / documentation | C0 | READY_WITHOUT_AUTHORIZATION |
| **AP-R1** | Read-only agentic | C1 | READY_WITHOUT_AUTHORIZATION, REVIEW_REQUIRED |
| **AP-R2** | Workspace-write | C2 | REVIEW_REQUIRED, BLOCKED (if protected paths) |
| **AP-R3** | Shell / build / test | C3 | REVIEW_REQUIRED, BLOCKED (without evidence plan) |
| **AP-R4** | Credential / external | C4 | BLOCKED (default), REVIEW_REQUIRED (only if authorized) |
| **AP-R5** | Live / irreversible | C5 | NO-GO, BLOCKED |

### Risk Level Rules

1. Risk level cannot decrease without explicit reclassification.
2. External benchmark reference cannot lower risk.
3. Existing baseline debt cannot lower risk.
4. C4 defaults to BLOCKED regardless of risk level.
5. C5 defaults to NO-GO regardless of risk level.
6. Evidence supports review; it cannot grant authorization.
7. CandidateRule cannot become policy without review phase.

## 3. Authority Impact Levels (AI-0 through AI-6)

| Level | Name | Description |
|-------|------|-------------|
| **AI-0** | current_truth only | Updates internal docs/state. No action authorization. |
| **AI-1** | plan_only | Produces proposal, plan, or receipt. No execution. |
| **AI-2** | local_validation | Local schema/test/fixture validation. No external side effects. |
| **AI-3** | workspace_change | Repo file changes. Requires evidence and review. |
| **AI-4** | controlled_execution | Local shell/build/test. Requires explicit gate and evidence. |
| **AI-5** | external_side_effect | Network, API, MCP, browser, credentials. BLOCKED unless separately authorized. |
| **AI-6** | live_irreversible | Finance, broker, production, destructive. NO-GO in current state. |

## 4. Gate Response Matrix

| Capability | AP-R0 | AP-R1 | AP-R2 | AP-R3 | AP-R4 | AP-R5 |
|-----------|-------|-------|-------|-------|-------|-------|
| C0 (docs) | READY | READY | — | — | — | — |
| C1 (read-only) | READY | READY | REVIEW | — | — | — |
| C2 (workspace) | — | REVIEW | REVIEW | BLOCKED | — | — |
| C3 (shell) | — | — | BLOCKED | REVIEW | BLOCKED | — |
| C4 (external) | — | — | — | BLOCKED | BLOCKED | BLOCKED |
| C5 (live) | — | — | — | — | NO-GO | NO-GO |

Key: READY = READY_WITHOUT_AUTHORIZATION | REVIEW = REVIEW_REQUIRED | BLOCKED = BLOCKED | NO-GO = NO-GO | — = Not applicable (capability exceeds risk level)

### Gate Response Rules

1. READY_WITHOUT_AUTHORIZATION is never execution authorization.
2. BLOCKED cannot be overridden by evidence alone.
3. Evidence supports review; it cannot grant authorization.
4. REVIEW_REQUIRED means human review before proceeding.
5. NO-GO means permanently out of scope under current project state.
6. ESCALATE_TO_GOVERNANCE_REVIEW applies when boundary is ambiguous.
7. DEFERRED means phase not started — requires explicit opening.

## 5. Evidence Requirements by Level

| Level | Minimum Evidence |
|-------|-----------------|
| AP-R0 | Source references, boundary confirmation, New AI Context Check |
| AP-R1 | Read scope, no-write confirmation, no-external-call confirmation |
| AP-R2 | Files changed, allowed/forbidden comparison, protected path check, test/doc plan |
| AP-R3 | Exact commands, exit codes, relevant logs, failure classification, rollback plan |
| AP-R4 | Explicit authorization record (future phases), credential non-access proof, network/MCP/browser non-invocation proof, external side-effect block confirmation |
| AP-R5 | Cannot proceed — record NO-GO and stop |

## 6. Review Requirements by Level

| Level | Review Required |
|-------|----------------|
| AP-R0 | Self-review + receipt |
| AP-R1 | Self-review + boundary check |
| AP-R2 | Structured receipt + scope review |
| AP-R3 | Structured receipt + evidence review + regression check |
| AP-R4 | Governance review required; BLOCKED by default |
| AP-R5 | NO-GO; cannot be approved by ordinary review |

## 7. NO-GO Ladder

Explicit NO-GO triggers:
- Live financial / broker / trading action
- Credential access
- External API side effect
- MCP tool execution with external impact
- Browser action affecting external account/system
- Production deployment
- Destructive file/system operation outside allowed scope
- CandidateRule promoted to Policy without review
- Valid payload interpreted as action authorization
- READY interpreted as execution authorization
- Evidence interpreted as approval
- External framework reference interpreted as compliance/certification/equivalence
- Public standard claim without explicit public-standard phase
- can_access_secrets field name reintroduced — use can_read_credentials

## 8. ADP-1 Pattern Mapping

| Pattern | Capability | Risk | Default Gate |
|---------|-----------|------|-------------|
| AP-COL | C4 | AP-R4 | BLOCKED |
| AP-CRED | C4 | AP-R4 | BLOCKED |
| AP-EXT | C4 | AP-R4 | BLOCKED |
| AP-MCP | C4 | AP-R4 | BLOCKED |
| AP-SHE | C3 | AP-R3 | BLOCKED (no escalation) |
| AP-EVL | — | AP-R4 | DEGRADED (self_reported) |
| AP-RDY | — | AP-R4 | READY_WITHOUT_AUTHORIZATION only |
| AP-REV | — | AP-R5 | BLOCKED |
| AP-BDM | — | AP-R5 | BLOCKED |
| AP-CRP | — | AP-R5 | DEGRADED (CandidateRule advisory) |
| AP-EBO | C1 | AP-R1 | BLOCKED (if overclaim) |
| AP-PPV | C2 | AP-R2 | BLOCKED |
| AP-FAT | C2 | AP-R2 | BLOCKED |
| AP-DRF | C2 | AP-R2 | BLOCKED |
| AP-INS | C1 | AP-R1 | DEGRADED |
| AP-CTD | C1 | AP-R1 | DEGRADED |
| AP-SCP | C2 | AP-R2 | DEGRADED |
| AP-TST | C3 | AP-R3 | DEGRADED |

All 18 ADP-1 patterns mapped. All CandidateRule suggestions remain NON-BINDING.

## 9. HAP-2 Fixture Mapping

All 14 HAP-2 fixtures map to GOV-X gate matrix:

| Fixture | Capability | Risk | Gate | Matches Matrix? |
|---------|-----------|------|------|-----------------|
| capability-authorization-collapse | C4 | AP-R4 | BLOCKED | ✅ C4→AP-R4→BLOCKED |
| credential-capability-confusion | C4 | AP-R4 | BLOCKED | ✅ C4→AP-R4→BLOCKED |
| external-side-effect-drift | C4 | AP-R4 | BLOCKED | ✅ C4→AP-R4→BLOCKED |
| mcp-tool-injection | C4 | AP-R4 | BLOCKED | ✅ C4→AP-R4→BLOCKED |
| shell-risk-escalation | C3 | AP-R1→R3 | BLOCKED | ✅ Escalation required |
| approval-fatigue | C2 | AP-R2 | BLOCKED | ✅ C2→AP-R2→BLOCKED |
| permission-rule-drift | C2 | AP-R2 | BLOCKED | ✅ C2→AP-R2→BLOCKED |
| protected-path-violation | C2 | AP-R2 | BLOCKED | ✅ C2→AP-R2→BLOCKED |
| evidence-laundering | — | AP-R4 | DEGRADED | ✅ Evidence quality |
| ready-overclaim | — | AP-R4 | READY_WITHOUT_AUTH | ✅ READY≠authorization |
| review-bypass | — | AP-R5 | BLOCKED | ✅ Review required |
| baseline-debt-masking | — | AP-R5 | BLOCKED | ✅ Classification required |
| candidate-rule-premature | — | AP-R5 | DEGRADED | ✅ CR non-binding |
| external-benchmark-overclaim | C1 | AP-R1 | BLOCKED | ✅ Overclaim blocked |

## 10. EGB-1 Gap Closure

| EGB Gap | GOV-X Addresses |
|---------|----------------|
| Capability-scaled governance | C0-C5 + AP-R0-R5 ladder |
| Systematic risk taxonomy | Capability×Risk×Authority matrix |
| Deployment authorization | Gate response matrix + AI levels |
| Source freshness | EGB-SOURCE-FRESHNESS-001 remains open |

## 11. Boundary Confirmation

| Boundary | Confirmed |
|----------|-----------|
| GOV-X is governance formalization, not execution | ✅ |
| Risk classification is not permission | ✅ |
| Gate response is not automatic execution | ✅ |
| READY_WITHOUT_AUTHORIZATION is not execution authorization | ✅ |
| Evidence supports review; does not approve | ✅ |
| C4 defaults to BLOCKED | ✅ |
| C5 defaults to NO-GO | ✅ |
| CandidateRule non-binding | ✅ |
| External benchmark reference is not compliance | ✅ |
| No credentials accessed | ✅ |
| No external systems invoked | ✅ |
| No live adapter/MCP/SDK/API created | ✅ |
| Financial/broker/live action remains NO-GO | ✅ |
| Phase 8 remains DEFERRED | ✅ |

## 12. Next Phase

**ADP-2** (pattern detection implementation) or **HAP-3** (HarnessTaskPlan
+ HarnessReviewRecord standalone fixture representation).

*Phase: GOV-X | Governance formalization only. No execution.*
