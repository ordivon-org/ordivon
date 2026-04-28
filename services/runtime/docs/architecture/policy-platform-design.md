# Policy Platform Design — Activation Boundary

Status: **PROPOSED** (Phase 5.1)
Date: 2026-04-29
Phase: 5.1
Tags: `policy`, `design`, `activation`, `candidate-rule`, `lifecycle`, `governance`

## 1. Purpose

This document defines the Policy Platform's activation boundary — the full
lifecycle from raw evidence to active, enforced Policy — without implementing
a single line of code. It is a design doc, not an implementation spec.

The Policy Platform is the missing piece of the Ordivon governance loop.
Phases 1–4 built the intake → governance → evidence pipeline. Phases 3–4
built the learning pipeline (Lesson → CandidateRule → PolicyProposal).
What remains is the activation pipeline: turning a PolicyProposal into an
active Policy that modifies runtime behavior.

## 2. Why Policy Platform Is the Next Step

The Stage Summit (Phase 4C) identified Policy Platform Design as the
recommended primary next move. The rationale:

1. **Closes the governance loop**: Ordivon currently classifies and records.
   It does not learn. A Policy Platform turns classification data into
   self-improving constraints.

2. **Highest leverage**: Every other component (Repo Governance Wedge,
   Dependabot, CodeQL, agent adapters) becomes more valuable when Policies
   can be activated, versioned, and rolled back.

3. **Phase 4 validated external tooling**: The tools work. The next frontier
   is not more tools — it's making the governance system itself learnable.

4. **Low risk, high learning**: This phase produces a design document.
   No code changes until the design is reviewed and approved.

## 3. Current State

### 3.1 What Exists

| Component | Location | Status |
|-----------|----------|--------|
| CandidateRule model | `domains/candidate_rules/` | Active — draft, under_review, accepted_candidate, rejected |
| CandidateRuleReviewService | `domains/candidate_rules/review_service.py` | Active — manages state transitions |
| PolicyProposal dataclass | `domains/candidate_rules/policy_proposal.py` | Active — draft only, in-memory |
| PolicyProposalService | `domains/candidate_rules/policy_proposal.py` | Active — creates proposals from accepted_candidate |
| Lesson → CandidateRule draft path | `docs/runtime/candidate-rule-review-path.md` | Documented — Wave B (wb_001 migration) |
| CandidateRule → Policy upgrade protocol | Memory / conventions | Documented — ≥2 weeks, ≥3 real interceptions |

### 3.2 What Does NOT Exist

| Component | Status |
|-----------|--------|
| Policy entity (ORM or dataclass) | Does not exist |
| Policy state machine | Does not exist |
| Policy activation mechanism | Does not exist |
| Policy versioning | Does not exist |
| Policy rollback | Does not exist |
| Policy owner / reviewer metadata | Not designed |
| Policy → Pack policy bridge | Not designed |
| Policy → CI gate bridge | Not designed |
| Policy dashboard / UI | Not designed |

### 3.3 Current Proof Points

- CandidateRuleReviewService has 14 passing tests
- PolicyProposalService has 15 passing tests
- CandidateRule draft has `lesson_ids` and `source_refs` fields (evidence lineage)
- CandidateRule has no `promote`, `accept`, or `approve` methods (Policy isolation verified by runtime evidence checker)

## 4. Policy Lifecycle

### 4.1 Full Lifecycle Diagram

```
Evidence (CI artifact, eval result, PR pattern, human review)
  │
  ├─ Review (human examines evidence, identifies pattern)
  │
  ├─ Lesson (encoded as a KnowledgeLesson record with source_refs)
  │
  ├─ CandidateRule(draft)       ← auto-drafted from Lesson
  │     │
  │     ├─ submit_for_review() → under_review
  │     │
  │     ├─ accept_candidate()  → accepted_candidate
  │     │
  │     ├─ reject_candidate()  → rejected (terminal)
  │     │
  │     └─ propose_from_accepted() → PolicyProposal(draft)
  │                                        │
  │                                        ├─ Human Approval Gate ─────┐
  │                                        │                            │
  │                                        ├─ approved → Policy(active) │
  │                                        │                            │
  │                                        ├─ rejected (terminal)       │
  │                                        │                            │
  │                                        └─ deferred (revisit later)  │
  │                                                                     │
  └─── At no point does this chain skip the Human Approval Gate ────────┘
```

### 4.2 Lifecycle Stages

| Stage | Actor | Reversible? | Evidence Required |
|-------|-------|-------------|-------------------|
| Evidence | System | N/A | Raw data (CI artifact, eval result, PR pattern) |
| Review | Human | N/A | Evidence + context |
| Lesson | System | No (immutable) | Review conclusion |
| CandidateRule(draft) | System | Yes (can be rejected) | Lesson + source_refs |
| CandidateRule(under_review) | Human | Yes (can return to draft or be rejected) | Draft + reviewer |
| CandidateRule(accepted_candidate) | Human | No (terminal) | Review + rationale |
| PolicyProposal(draft) | Human | Yes (can be rejected) | accepted_candidate + rationale |
| PolicyProposal(under_review) | Human | Yes | Draft + reviewer |
| Policy(active) | Human + System | Yes (can be deprecated, rolled_back) | Approved proposal + owner sign-off + risk assessment + rollback plan |
| Policy(deprecated) | Human | Yes (can be reactivated) | Deprecation rationale |
| Policy(rolled_back) | Human | Yes (can be reactivated) | Rollback reason + incident reference |

### 4.3 Minimum Time Gates

Per the existing candidate-rule→policy protocol:

| Stage → Stage | Minimum Time | Minimum Evidence |
|---------------|-------------|------------------|
| CandidateRule(draft) → accepted_candidate | None | Human review |
| accepted_candidate → PolicyProposal | None | Human decision |
| PolicyProposal → Policy(active) | None (design discussion) | Owner sign-off + risk assessment + rollback plan |

**Design question**: Should PolicyProposal → Policy(active) have a mandatory
observation period? The Stage Summit did not resolve this. See §9.

## 5. Activation Boundaries

A PolicyProposal may only become Policy(active) when ALL of the following
conditions are met. No single condition is sufficient. No condition may
be waived without a recorded human exception (doctrine §3.8).

### 5.1 Required Evidence

| Evidence | Description | Source |
|----------|-------------|--------|
| Source CandidateRule | The accepted_candidate this Policy derives from | `candidate_rule_id` |
| Lesson lineage | The original Lesson(s) that produced the CandidateRule | `lesson_ids` in CandidateRule |
| Interception count | How many times this pattern was observed in practice | CandidateRule metadata |
| Observation period | How long the CandidateRule ran in advisory mode | CandidateRule created_at → accepted_at |

### 5.2 Required Reviewer

| Role | Minimum | Description |
|------|---------|-------------|
| Technical reviewer | 1 | Reviews the Policy's technical correctness |
| Domain owner | 1 | Confirms the Policy is appropriate for the domain |
| Governance reviewer | 1 | Confirms the Policy doesn't bypass existing governance |

**Note**: These MAY be the same person for small teams, but each role must
be explicitly recorded. A single "approved by X" is insufficient.

### 5.3 Owner

Every active Policy must have a named owner. The owner is responsible for:
- Responding to Policy escalation events
- Reviewing the Policy at least every 6 months
- Approving Policy modifications
- Authorizing Policy deprecation or rollback

An unowned Policy is a governance liability. Policies without owners
should be automatically deprecated after 6 months of inactivity.

### 5.4 Risk Classification

Every Policy must be classified by risk level BEFORE activation:

| Risk Level | Meaning | Activation Requirement |
|-----------|---------|----------------------|
| Low | Advisory only, no blocking | Owner sign-off |
| Medium | Blocking, with documented bypass | Owner + technical reviewer sign-off |
| High | Blocking, no bypass | Owner + technical reviewer + governance reviewer sign-off |

### 5.5 Rollback Plan

Every Policy must have a rollback plan documented BEFORE activation:

- What triggers a rollback? (false positive rate > X%, incident, owner request)
- Who can authorize a rollback?
- How is the rollback executed? (code change, config flag, feature toggle)
- What is the rollback's blast radius? (which gates, which Packs, which CI jobs)
- How long does rollback take? (seconds, minutes, deploy cycle)

A Policy without a rollback plan cannot be activated.

### 5.6 Eval Requirements

Before activation, the Policy must pass the existing Eval Corpus (24 cases).
If the Policy would change any existing eval case's expected outcome, the
eval case must be updated and the change must be documented in the
activation rationale.

New eval cases SHOULD be added for the specific patterns the Policy is
designed to catch. At minimum, one "should pass" case and one "should
fail" case.

## 6. Policy States

### 6.1 State Machine

```
draft ──→ proposed ──→ approved ──→ active ──→ deprecated
  │          │            │            │            │
  │          │            │            ├──→ rolled_back
  │          │            │            │
  └──→ rejected           └──→ rejected
```

### 6.2 State Definitions

| State | Meaning | Allowed Actions |
|-------|---------|----------------|
| `draft` | Policy is being drafted, not yet proposed for review | Edit, delete, propose |
| `proposed` | Policy is under human review | Approve, reject, return-to-draft |
| `approved` | Policy has passed review but is not yet active | Activate, reject |
| `active` | Policy is enforced at runtime | Deprecate, rollback |
| `deprecated` | Policy was intentionally retired | Reactivate (with new review) |
| `rolled_back` | Policy was emergency-removed due to incident | Reactivate (after incident review) |
| `rejected` | Policy was reviewed and rejected (terminal) | Cannot be resubmitted — create new draft |

### 6.3 State Transitions Requiring Human Action

The following transitions MUST involve a human:

| Transition | Required Human Action |
|-----------|----------------------|
| draft → proposed | Human clicks "submit for review" |
| proposed → approved | Human reviewer approves |
| approved → active | Human owner activates |
| active → deprecated | Human owner deprecates |
| active → rolled_back | Human reviewer rolls back (emergency) |

The following transitions MAY be automated:

| Transition | Automation |
|-----------|-----------|
| (none) | No automated Policy state transitions are currently permitted |

## 7. What Must Never Happen

These are **hard boundaries**. Violating any of them is a governance
incident that must be recorded and rolled back.

### 7.1 Forbidden Shortcuts

| Shortcut | Why Forbidden |
|----------|--------------|
| Lesson → Policy(active) | Skips CandidateRule observation period. No human review of pattern quality. |
| CodeQL finding → Policy(active) | Security scanner output is evidence, not policy. No severity protocol, no domain context. |
| Dependabot behavior → Policy(active) | Bot behavior patterns require human judgment. Auto-policy from bot PRs would encode noise. |
| AI agent creates active Policy | No machine creates a constraint on human behavior without human approval. |
| Single-incident Policy | A pattern seen once is not a pattern. Minimum ≥3 real interceptions before CandidateRule consideration (existing protocol). |
| Policy without rollback plan | Activated constraints must be deactivatable. Unremovable Policy is governance sclerosis. |

### 7.2 Forbidden Bypass Patterns

| Bypass | Why Forbidden |
|--------|--------------|
| Policy that skips RiskEngine | All intakes must pass through RiskEngine. No Policy can create a side channel. |
| Policy that auto-merges Dependabot PRs | Auto-merge requires 3+ months clean history + explicit human approval (doctrine §4.2). |
| Policy that disables another Policy | Policies can only be deprecated or rolled back through human review. No Policy-on-Policy warfare. |
| Policy that hides its own evidence | Every Policy decision must be traceable. A Policy that suppresses its own audit trail is a rootkit. |

## 8. Relationship to Pack Policies

### 8.1 Policy Taxonomy

| Policy Type | Scope | Example | Status |
|------------|-------|---------|--------|
| **Core Policy** | Applies to all intakes, all Packs | Severity protocol (reject > escalate > execute) | Active |
| **Pack Policy** | Applies to intakes for a specific Pack | CodingDisciplinePolicy (forbidden files, test_plan required) | Active |
| **Adapter Policy** | Applies to governance at the adapter level | Bot actor synthetic test_plan injection | Active |
| **Verification Gate Policy** | Applies to CI gate classification | CodeQL workflow-health hard gate | Active |
| **Activated Policy** | A Policy that originated from a CandidateRule and was activated through the Policy Platform | (none yet — this is what the Policy Platform enables) | Not yet |

### 8.2 Policy Conflict Resolution

When two Policies produce conflicting decisions on the same intake:

1. **Hard gates take priority**: A Policy that rejects always overrides a Policy
   that escalates or executes.
2. **More specific takes priority**: A Pack Policy takes priority over a Core
   Policy for intakes within that Pack.
3. **Newer activation takes priority**: If two Policies of the same type conflict,
   the more recently activated Policy takes priority (documented rationale required).
4. **Conflict is an escalation**: If resolution is ambiguous, the intake escalates
   for human review rather than silently choosing one Policy.

### 8.3 Policy Inheritance

Activated Policies do NOT automatically inherit into Pack policies.
A Policy that originated from a Finance domain observation does not
automatically apply to the Coding domain. Cross-domain Policy application
requires explicit human review and approval.

## 9. Open Design Questions

These questions are raised by this design document and should be resolved
before implementation begins.

### 9.1 Observation Period

**Question**: Should PolicyProposal → Policy(active) require a mandatory
observation period (e.g., 2 weeks with the CandidateRule running in
advisory mode)?

**Arguments for**: Prevents premature activation. Aligns with existing
CandidateRule → Policy protocol (≥2 weeks).

**Arguments against**: Adds latency. Some Policies (e.g., known vulnerability
mitigations) may need faster activation.

**Proposed resolution**: Default observation period of 2 weeks for
CandidateRules originating from operational patterns. Exception for
security Policies with documented urgency rationale (requires governance
reviewer sign-off).

### 9.2 Policy Versioning

**Question**: How should Policy versions be tracked?

**Options**:
- A. `version` integer on the Policy entity (1, 2, 3...)
- B. Immutable Policy records — each activation creates a new Policy,
  the old one is deprecated
- C. Git-based versioning — Policy activations are commits to a policy
  registry file

**Proposed resolution**: Option B (immutable Policy records). Aligns with
the ExecutionReceipt pattern (immutable append-only). Each activation
creates a new Policy entity. The previous version is deprecated. The
lineage is traceable through `predecessor_policy_id`.

### 9.3 Policy Storage

**Question**: Should PolicyProposal and Policy be ORM entities or in-memory?

**Current state**: PolicyProposal is an in-memory dataclass. CandidateRule
has a repository pattern with (future) ORM backing.

**Options**:
- A. Both stay in-memory (simple, no schema changes)
- B. PolicyProposal → ORM, Policy → ORM (durable, queryable)
- C. PolicyProposal stays in-memory, Policy → ORM (activation is the persistence boundary)

**Proposed resolution**: Option C. PolicyProposal is transient — it exists
only during the human review window. Policy is durable — once activated,
it must survive process restarts. The activation step is the persistence
boundary.

### 9.4 Policy Rollback Mechanism

**Question**: How is rollback implemented technically?

**Options**:
- A. Feature flag: Policy registry has enable/disable flags
- B. Code deployment: Rollback means reverting the Policy's code change
- C. Database state: Policy entity has `rolled_back` state, runtime
  registry checks state before enforcing

**Proposed resolution**: Option C for Phase 5. Policy entities have a
state field. The runtime policy registry only enforces Policies in
`active` state. Rollback is a state transition, not a code deployment.
This enables fast rollback (seconds) without deploy cycles.

### 9.5 Who Can Activate

**Question**: What is the minimum authorization for Policy activation?

**Current practice**: No activation exists. All current Policies
(CodingDisciplinePolicy, TradingDisciplinePolicy) are baked into the
codebase and activated by code merge.

**Proposed resolution**: Owner sign-off is required (see §5.3). For
Phase 5, the owner is the person who created the PolicyProposal.
For future phases, owner may be a role (e.g., "security-owner",
"pack-finance-owner").

## 10. Recommended Implementation Phases

### Phase 5.1: Design (this phase)

- This document
- Review and approval by Stage Summit stakeholders
- Resolution of open design questions (§9)

### Phase 5.2: Policy Entity + State Machine (complete)

- ~~Create `Policy` dataclass or ORM entity with state machine~~ → ✅ Complete
  - `domains/policies/models.py` — PolicyRecord, PolicyScope, PolicyState, PolicyRisk, PolicyEvidenceRef, PolicyRollbackPlan, PolicyOwner
  - `domains/policies/state_machine.py` — PolicyStateMachine with transition guards
  - `tests/unit/policies/test_policy_state_machine.py` — 36 tests covering all transitions, guards, terminal states, and pure model validation
- ~~Implement state transitions as defined in §6~~ → ✅ Complete
- ~~Add rollback mechanism~~ → ✅ Complete
- ~~Tests: all valid transitions, all forbidden transitions, rollback → reactivate path~~ → ✅ Complete

### Phase 5.3: CandidateRule → Policy Bridge (complete)

- ~~Resolve dual-track boundary between `domains/candidate_rules/policy_proposal.py` and `domains/policies/*`~~ → ✅ Complete
  - `PolicyProposal` lightweight dataclass retired
  - `CandidateRulePolicyBridge` creates `PolicyRecord(state=draft)` from accepted_candidate
  - Bridge is a thin adapter — CandidateRule learning path → Policy Platform
  - All guards preserved: only accepted_candidate, duplicate prevention, evidence lineage
  - Draft policy has no owner/rollback_plan — those are required only at activation
  - `tests/unit/capabilities/test_policy_proposal.py` — 19 tests covering full boundary
- ~~Bridge PolicyProposal → Policy activation~~ → Deferred to Phase 5.4 (activation pipeline)
- ~~Tests: missing-evidence rejection, missing-reviewer rejection~~ → Covered in 5.2-P (PolicyRecord invariants)

### Phase 5.4: Policy Registry (next)

### Phase 5.4: Policy Registry

- Runtime policy registry that loads active Policies
- Integration point with RiskEngine (RiskEngine reads active Policies)
- Policy conflict resolution (§8.2)
- Tests: registry loads correct Policies, conflicting Policies escalate

### Phase 5.5: First Shadow Policy Dogfood

- Select one real CandidateRule from operational data
- Run it through the full lifecycle: draft → review → accepted → proposal → activation
- Document the entire process as a runbook
- This is the "dogfood" phase — validate the design with real data

### Phase 5.6: Iteration + Hardening

- Based on Phase 5.5 findings, iterate on the design
- Hardening: error handling, concurrent activation prevention, rollback safety
- Eval Corpus expansion for Policy-specific cases

## 11. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/runtime/candidate-rule-review-path.md` | CandidateRule human review path |
| `docs/runtime/policy-proposal-path.md` | PolicyProposal draft path |
| `docs/architecture/ordivon-current-architecture.md` | Canonical architecture (Layer 9: CandidateRule, Layer 10: Policy) |
| `docs/product/ordivon-stage-summit-phase-4.md` | Stage Summit — recommended Policy Platform as next move |
| `docs/runbooks/ordivon-agent-operating-doctrine.md` | Agent doctrine §3.6 (CandidateRule ≠ Policy), §3.8 (human exception) |
