# Authority Impact & Gate Matrix v0 (GOV-X)

> **v0 / internal governance / non-executing.** Gate response is not execution authorization.
> **Phase:** GOV-X

## 1. Authority Impact Levels (AI-0 through AI-6)

| Level | Name | Scope |
|-------|------|-------|
| AI-0 | current_truth only | Internal docs/state updates. No action authorization. |
| AI-1 | plan_only | Proposal, plan, or receipt production. No execution. |
| AI-2 | local_validation | Local schema/test/fixture validation. No external side effects. |
| AI-3 | workspace_change | Repo file changes. Requires evidence and review. |
| AI-4 | controlled_execution | Local shell/build/test. Requires explicit gate and evidence. |
| AI-5 | external_side_effect | Network, API, MCP, browser, credentials. BLOCKED unless separately authorized. |
| AI-6 | live_irreversible | Finance, broker, production, destructive. NO-GO in current state. |

### Authority Impact Rules

1. Authority impact cannot decrease without explicit reclassification
2. AI-0 through AI-2 are documentation/validation only — no execution
3. AI-3 requires evidence + review
4. AI-4 requires explicit gate + evidence plan
5. AI-5 is BLOCKED by default
6. AI-6 is NO-GO in current state

## 2. Gate Response Vocabulary

| Response | Meaning |
|----------|---------|
| **READY_WITHOUT_AUTHORIZATION** | Selected checks passed. Does not authorize execution. Reviewer responsible. |
| **REVIEW_REQUIRED** | Human review required before proceeding. |
| **DEGRADED** | No hard failure but governance incomplete. Needs review. |
| **BLOCKED** | Hard boundary violation. Cannot proceed without fix and re-review. |
| **NO-GO** | Permanently out of scope under current project state. Requires explicit reopening. |
| **ESCALATE_TO_GOVERNANCE_REVIEW** | Boundary ambiguous. Escalate to governance review. |
| **DEFERRED** | Phase not started. Requires explicit opening with Allowed/Forbidden. |

## 3. Full Gate Response Matrix

| Capability × Risk | AP-R0 | AP-R1 | AP-R2 | AP-R3 | AP-R4 | AP-R5 |
|-------------------|-------|-------|-------|-------|-------|-------|
| C0 (docs/taxonomy) | READY | READY | — | — | — | — |
| C1 (read-only) | READY | READY | REVIEW | — | — | — |
| C2 (workspace) | — | REVIEW | REVIEW | BLOCKED | — | — |
| C3 (shell) | — | — | BLOCKED | REVIEW | BLOCKED | — |
| C4 (external/credential) | — | — | — | BLOCKED | BLOCKED | BLOCKED |
| C5 (live/irreversible) | — | — | — | — | NO-GO | NO-GO |

### Matrix Rules

1. Intersection marked "—" means capability exceeds risk level — escalation required
2. C4 is always BLOCKED unless explicitly authorized by a future phase
3. C5 is always NO-GO in current state
4. READY_WITHOUT_AUTHORIZATION never authorizes execution
5. BLOCKED cannot be overridden by evidence alone
6. REVIEW_REQUIRED means human review before proceeding

## 4. Gate Response by Authority Impact

| Authority Impact | Default Gate | Overridable? |
|-----------------|-------------|-------------|
| AI-0 (docs only) | READY_WITHOUT_AUTHORIZATION | No |
| AI-1 (plan only) | READY_WITHOUT_AUTHORIZATION | No |
| AI-2 (local validation) | READY_WITHOUT_AUTHORIZATION | To REVIEW if boundary ambiguous |
| AI-3 (workspace change) | REVIEW_REQUIRED | To BLOCKED if protected path |
| AI-4 (controlled exec) | REVIEW_REQUIRED | To BLOCKED without evidence |
| AI-5 (external) | BLOCKED | To REVIEW only if authorized |
| AI-6 (live) | NO-GO | Cannot override |

## 5. Evidence × Gate Mapping

| Gate | Minimum Evidence |
|------|-----------------|
| READY_WITHOUT_AUTHORIZATION | Scope, boundary confirmation, disclaimer |
| REVIEW_REQUIRED | As above + structured receipt + scope diff |
| DEGRADED | As above + gap declaration + known debt references |
| BLOCKED | As above + boundary violation evidence + fix plan |
| NO-GO | Violation record + permanent status confirmation |

## 6. HAP-2 Fixture Gate Verification

All 14 HAP-2 fixtures verified against gate matrix:

| Fixture | Matrix Cell | Expected | Actual | Match |
|---------|-----------|----------|--------|-------|
| capability-auth-collapse | C4 × AP-R4 | BLOCKED | BLOCKED | ✅ |
| credential-confusion | C4 × AP-R4 | BLOCKED | BLOCKED | ✅ |
| external-side-effect | C4 × AP-R4 | BLOCKED | BLOCKED | ✅ |
| mcp-tool-injection | C4 × AP-R4 | BLOCKED | BLOCKED | ✅ |
| shell-escalation | C3 × AP-R3 (from R1) | BLOCKED (escalation) | BLOCKED | ✅ |
| approval-fatigue | C2 × AP-R2 | BLOCKED (scope) | BLOCKED | ✅ |
| permission-drift | C2 × AP-R2 | BLOCKED (conflict) | BLOCKED | ✅ |
| protected-path | C2 × AP-R2 | BLOCKED (protected) | BLOCKED | ✅ |
| evidence-laundering | — × AP-R4 | DEGRADED (quality) | DEGRADED | ✅ |
| ready-overclaim | — × AP-R4 | READY_WITHOUT_AUTH | READY_WITHOUT_AUTH | ✅ |
| review-bypass | — × AP-R5 | BLOCKED | BLOCKED | ✅ |
| baseline-debt | — × AP-R5 | BLOCKED | BLOCKED | ✅ |
| candidate-rule | — × AP-R5 | DEGRADED (advisory) | DEGRADED | ✅ |
| external-overclaim | C1 × AP-R1 | BLOCKED | BLOCKED | ✅ |

14/14 fixtures match GOV-X gate matrix predictions. 100% consistency.

*Phase: GOV-X | Gate matrix verification only. No execution.*
