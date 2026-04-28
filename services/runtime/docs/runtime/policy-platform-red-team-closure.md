# Policy Platform — Red-Team Closure Review (Phase 5Z)

Status: **CLOSED** (Phase 5Z)
Date: 2026-04-29
Tags: `red-team`, `closure`, `policy`, `security`, `invariants`

## 1. Purpose

Adversarial review of every Policy Platform component.
Each vector is tested: what an attacker, bug, or confused operator
could do to bypass governance and activate policy without authorization.

## 2. Threat Vectors

### Vector 1: Hidden activation path

**Threat**: A code path that activates active_shadow or active_enforced
without passing through the full lifecycle.

**Finding**: No path exists. `PolicyRecord(state=ACTIVE_SHADOW)` is
rejected by `__post_init__` invariants (Phase 5.2-P). The state machine
has no transition that bypasses draft→proposed→approved→active_shadow.
The approval gate explicitly defers active_enforced.

**Verdict**: MITIGATED. No hidden activation path found.

### Vector 2: READY_FOR_ACTIVATION naming ambiguity

**Threat**: An operator misreads READY_FOR_ACTIVATION as "ready to
activate" and transitions a policy to active_enforced.

**Finding**: The naming risk was confirmed in Phase 5.8 closure review
and Phase 4.13 static audit. The enum value was renamed in Phase 5Z
from `READY_FOR_ACTIVATION` to `READY_FOR_HUMAN_ACTIVATION_REVIEW`.
The docstring now explicitly states "NOT auto-activation."

**Verdict**: MITIGATED by Phase 5Z rename. No remaining ambiguity.

### Vector 3: PolicyRecord direct construction invariants

**Threat**: Directly constructing `PolicyRecord(state=ACTIVE_ENFORCED)`
without evidence, owner, or rollback_plan.

**Finding**: `__post_init__` rejects ACTIVE_SHADOW/ACTIVE_ENFORCED without
evidence_refs (ValueError), owner (ValueError), rollback_plan (ValueError).
ROLLED_BACK requires rollback_reason. DEPRECATED requires deprecation_reason.
These invariants are tested in 13 direct-construction tests.

**Verdict**: MITIGATED. Model-level invariants prevent direct construction.

### Vector 4: StateMachine illegal transition guards

**Threat**: Bypassing the state machine by calling `with_state` directly.

**Finding**: `with_state` was renamed to `_with_state_unchecked` in Phase
5.2-P. The underscore prefix signals internal use. The only caller is
`PolicyStateMachine.transition()` which runs all 6 guards before calling it.

**Verdict**: MITIGATED. Unchecked method is clearly marked and tests
verify the state machine is the only caller.

### Vector 5: CandidateRule → PolicyRecord bridge boundaries

**Threat**: A CandidateRule with status=draft or under_review creating a
PolicyRecord in active state.

**Finding**: `CandidateRulePolicyBridge.create_policy_draft()` enforces:
only accepted_candidate → DRAFT. Other statuses raise ProposalNotAllowedError.
Duplicate creation raises DuplicateProposalError. The bridge never creates
active_shadow or active_enforced.

**Verdict**: MITIGATED. Bridge boundaries enforced by exception.

### Vector 6: Stale evidence rejection

**Threat**: A PolicyRecord with all-stale evidence reaching approval.

**Finding**: EvidenceGate reject (Gate 3: freshness check). Any stale
evidence triggers NOT_READY. All-stale evidence triggers NEEDS_MORE_EVIDENCE
in ApprovalGate (Gate 2). Test: `test_all_stale_evidence_needs_more`.

**Verdict**: MITIGATED. Two independent gates catch stale evidence.

### Vector 7: Single-event evidence rejection

**Threat**: A Policy based on a single CodeQL finding or single Dependabot
incident reaching activation readiness.

**Finding**: EvidenceGate Gate 6 (weak solo detection) flags single
ci_artifact/source_ref as insufficient. Gate 7 (learning loop lineage
check) warns if no candidate_rule/lesson/review chain exists.
ShadowEvaluator requires READY_FOR_HUMAN_ACTIVATION_REVIEW for
WOULD_RECOMMEND_MERGE — weak evidence reaches at most READY_FOR_SHADOW.

**Verdict**: MITIGATED. Multiple independent checks.

### Vector 8: CodeQL finding alone rejection

**Threat**: A CodeQL finding becoming active policy.

**Finding**: Shadow case DF-CODEQL: ci_artifact evidence alone →
WOULD_ESCALATE, not WOULD_RECOMMEND_MERGE. Evidence gate: single
ci_artifact → warning, not READY_FOR_HUMAN_ACTIVATION_REVIEW.
Doctrine §7.3: "CodeQL finding is evidence, not policy."

**Verdict**: MITIGATED. Cannot reach activation from CodeQL alone.

### Vector 9: Dependabot behavior alone rejection

**Threat**: A Dependabot PR pattern becoming active policy without
CandidateRule observation.

**Finding**: Shadow evaluator handles Dependabot cases correctly:
clean PR → WOULD_RECOMMEND_MERGE (advisory only), CI failure → WOULD_HOLD.
But this is shadow evaluation — no active policy is created.
Doctrine §3.6: CandidateRule ≠ Policy.

**Verdict**: MITIGATED. Dependabot patterns inform shadow evaluation,
not policy activation.

### Vector 10: Actor spoofing

**Threat**: A human PR with "deps:" title receiving Dependabot bot
treatment in policy evaluation.

**Finding**: Shadow case DF-SPOOF: human actor + no test_plan →
WOULD_ESCALATE. Shadow evaluator routes by actor_type, not title.
This mirrors the Phase 4.11 identity hardening fix in the governance
adapter.

**Verdict**: MITIGATED. Actor identity from metadata, not text.

### Vector 11: Shadow evaluator advisory-only behavior

**Threat**: Shadow evaluator mutating PolicyRecord state or producing
non-advisory results.

**Finding**: All `is_advisory` fields are True. Tests: "shadow evaluator
never mutates policy", "shadow evaluator never changes policy state",
"shadow result is always advisory". Evaluator is read-only.

**Verdict**: MITIGATED. Evaluator is pure function.

### Vector 12: Approval gate not mutating PolicyRecord

**Threat**: Approval gate changing policy state during review.

**Finding**: `PolicyApprovalGate.review()` returns a `PolicyApprovalDecision`
but never calls `_with_state_unchecked` or modifies the input PolicyRecord.
Test: "approval gate never mutates policy" confirms state stays DRAFT.

**Verdict**: MITIGATED. Approval is read-only classification.

### Vector 13: Rollback contract completeness

**Threat**: A rollback contract with missing fields reaching approval.

**Finding**: `PolicyRollbackContract.__post_init__` validates all 6 fields
(trigger, authorized_by, method, blast_radius, target_recovery_time,
post_rollback_reviewer). Any missing field raises ValueError. ApprovalGate
rejects missing rollback contract (Gate 4).

**Verdict**: MITIGATED. No incomplete rollback contracts can pass.

### Vector 14: Policy scope mismatch

**Threat**: A shadow case with mismatched policy scope producing incorrect results.

**Finding**: Shadow evaluator checks case.policy_scope vs policy.scope.
Mismatch → ShadowVerdict.NO_MATCH with confidence=1.0. Test: RT-008.

**Verdict**: MITIGATED. Scope mismatch produces explicit NO_MATCH.

### Vector 15: Future UI overclaim risk

**Threat**: A future UI displaying "Activate Policy" button without
underlying governance enforcement.

**Finding**: This is a design-time risk, not a code vulnerability. The
Design Pack contract (Phase 6A §4.4) requires high-risk actions to stay
disabled by default. The HighRiskActionMap lists "Activate Policy" as
"Disabled (Phase 5 NO-GO)."

**Verdict**: MITIGATED by design contract. Requires implementation enforcement.

## 3. Decisions

### active_shadow runtime-ready?

**Decision**: NO. Design-ready only. No runtime policy registry,
shadow check point, or feedback mechanism exists.

### active_enforced ready?

**Decision**: NO-GO. No shadow data, no rollback tested, no owner
accountability, no Stage Summit approval.

### auto-merge ready?

**Decision**: NO-GO. Clean Dependabot history requirement unmet,
approval gate not designed for merge automation.

### Phase 6 allowed?

**Decision**: YES — but only Design Pack + UI Governance work.
No Policy activation, no RiskEngine integration, no active_enforced.

### READY_FOR_ACTIVATION renamed?

**Decision**: YES. Renamed to `READY_FOR_HUMAN_ACTIVATION_REVIEW` in Phase 5Z.

## 4. Summary

15 threat vectors tested. 15 mitigated. 0 vulnerabilities found.
1 naming risk corrected (Phase 5Z rename).
The Policy Platform is safe for Phase 6 UI work.
active_enforced remains explicitly NO-GO.
