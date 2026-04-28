# Policy Platform — Phase 5 Closure Review

Status: **CLOSED** (Phase 5.8)
Date: 2026-04-29
Phase: 5.1 → 5.8
Tags: `closure`, `policy`, `shadow`, `governance`, `readiness`, `no-go`

## 1. Executive Summary

Phase 5 has built the Policy Platform from a design document into a working,
tested, pure-domain prototype. The full non-enforcing path — from CandidateRule
to APPROVED_FOR_SHADOW — has been exercised with real Phase 4-derived evidence.

**124 tests pass.** **7 hard gates pass.** **0 active policies exist.**

The Policy Platform can now:
- Model Policy lifecycles as immutable value objects
- Validate state transitions through a guarded state machine
- Bridge CandidateRule evidence into Policy drafts
- Gate evidence freshness and readiness through 7 automated checks
- Shadow-evaluate policies against red-team cases
- Produce human-auditable review checklists
- Approve policies for shadow mode with rollback contracts

The Policy Platform cannot yet:
- Connect to RiskEngine or Pack policies
- Persist Policy state to a database
- Enforce active_shadow or active_enforced at runtime
- Present a human review UI

**Decision: active_enforced is NOT ready. active_shadow is design-ready but runtime-deferred.**

## 2. Phase 5 Timeline

| Phase | Description | Files | Tests | Outcome |
|-------|-------------|-------|-------|---------|
| 5.1 | Policy Platform Design | `docs/architecture/policy-platform-design.md` | — | Design reviewed |
| 5.2 | Policy Entity + State Machine | `domains/policies/models.py`, `state_machine.py` | 37 | 8 states, 6 guards |
| 5.2-P | PolicyRecord Invariants | `models.py` (hardened) | 50 | 5 hard invariants, `with_state` → `_with_state_unchecked` |
| 5.3 | CandidateRule → Policy Bridge | `candidate_rules/policy_proposal.py` | 69 | Dual-track resolved; PolicyProposal retired |
| 5.4 | Evidence Gate + Review Checklist | `domains/policies/evidence_gate.py` | 73 | 7 gates, 9 checklist items |
| 5.5 | Shadow Evaluator + Red Team | `domains/policies/shadow.py` | 90 | 6 verdicts, 11 red-team cases |
| 5.6 | Approval Gate + Rollback Contract | `domains/policies/approval.py` | 112 | 8 gates, 5 outcomes, active_enforced DEFERRED |
| 5.7 | First Shadow Policy Dogfood | `tests/unit/policies/test_dogfood.py` | 124 | Full path → APPROVED_FOR_SHADOW |
| 5.8 | Closure Review | This document | 124 | Go/No-Go gate written |

**Total: 8 sub-phases. 9 source files. 124 tests. 0 regressions.**

## 3. Current Policy Platform Architecture

```
CandidateRule(accepted_candidate)
  │
  └─ CandidateRulePolicyBridge.create_policy_draft()
       │
       └─ PolicyRecord(state=draft, evidence_refs=...)
            │
            ├─ PolicyStateMachine (guarded transitions)
            │
            ├─ PolicyEvidenceGate
            │     └─ ReadinessLevel: NOT_READY / READY_FOR_REVIEW /
            │        READY_FOR_SHADOW / READY_FOR_ACTIVATION
            │
            ├─ PolicyReviewChecklist (9 structured questions)
            │
            ├─ PolicyShadowEvaluator
            │     └─ ShadowVerdict: WOULD_EXECUTE / WOULD_ESCALATE /
            │        WOULD_REJECT / WOULD_HOLD /
            │        WOULD_RECOMMEND_MERGE / NO_MATCH
            │
            └─ PolicyApprovalGate
                  └─ ApprovalOutcome: APPROVED_FOR_SHADOW / REJECTED /
                     NEEDS_MORE_EVIDENCE / NEEDS_MORE_SHADOW / DEFERRED
```

### Component Inventory

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| PolicyRecord | `domains/policies/models.py` | 215 | Mature |
| PolicyStateMachine | `domains/policies/state_machine.py` | 248 | Mature |
| CandidateRulePolicyBridge | `domains/candidate_rules/policy_proposal.py` | 175 | Stable |
| PolicyEvidenceGate | `domains/policies/evidence_gate.py` | 228 | Stable |
| PolicyReviewChecklist | `domains/policies/evidence_gate.py` | 82 | Stable |
| PolicyShadowEvaluator | `domains/policies/shadow.py` | 309 | Stable |
| PolicyApprovalGate | `domains/policies/approval.py` | 249 | Stable |
| PolicyRollbackContract | `domains/policies/approval.py` | 75 | Stable |

## 4. What Has Been Proven

### 4.1 Policy Modeling
- 8 PolicyState values with guarded transitions
- Immutable PolicyRecord pattern (versioned, predecessor-tracked)
- Direct construction of invalid states rejected at model level (5.2-P)
- State machine prevents draft→active, approved→enforced shortcuts

### 4.2 Evidence Integrity
- 7 automated evidence gates catch: no evidence, stale evidence, unknown ref_types,
  weak solo evidence, missing scope/risk, single-event promotion
- Evidence freshness is a first-class gate (current/regenerated required)
- CodeQL findings and Dependabot behavior alone cannot reach activation readiness

### 4.3 Shadow Evaluation
- 11 red-team cases from Phase 4 Dependabot experience
- WOULD_RECOMMEND_MERGE for clean dependency PRs
- WOULD_HOLD for CI failures and stale evidence
- WOULD_ESCALATE for weak evidence and spoofed human titles
- Evaluator is read-only — never mutates PolicyRecord

### 4.4 Approval Governance
- 8 approval gates enforce: owner required, rollback required,
  shadow verdict quality, risk-based reviewer requirements
- active_enforced is explicitly DEFERRED — only APPROVED_FOR_SHADOW is permitted
- RollbackContract enforces all required fields (trigger, authorized_by, method,
  blast_radius, recovery time, post-rollback review)

### 4.5 End-to-End Dogfood
- Full path exercised: draft → gate → shadow → approval → APPROVED_FOR_SHADOW
- Policy state remains DRAFT throughout
- No active/enforced policy created at any point
- 124 tests pass with zero regressions

## 5. What Remains Explicitly Forbidden

Per the Activation Boundary design (§5) and Agent Operating Doctrine (§3.6):

| Action | Status | Rationale |
|--------|--------|-----------|
| Lesson → Policy(active) | Forbidden | Must pass through CandidateRule observation |
| CodeQL finding → Policy(active) | Forbidden | Scanner output is evidence, not policy |
| Dependabot behavior → Policy(active) | Forbidden | Bot patterns require human judgment |
| AI agent → active Policy | Forbidden | No machine creates human constraints |
| Single-incident Policy | Forbidden | Minimum ≥3 real interceptions |
| Policy without rollback plan | Forbidden | Unremovable policy is governance sclerosis |
| Policy bypassing RiskEngine | Forbidden | All intakes must pass through governance |
| Policy auto-merging Dependabot PRs | Forbidden | Requires 3+ months clean history + human approval |
| CandidateRule → Policy(active) without ApprovalGate | Forbidden | Human Approval Gate is mandatory |

## 6. Activation Readiness Decision

### active_shadow

**Design status**: Ready. The Policy Platform can model shadow policies,
evaluate them against cases, and produce APPROVED_FOR_SHADOW decisions.

**Runtime status**: Deferred. No runtime connection exists between Policy
Platform decisions and actual governance behavior. Shadow mode requires:
- A policy registry that loads active shadow policies
- An integration point in the governance adapter that checks shadow policies
- A feedback mechanism that records shadow decisions for later review

**Gate**: active_shadow MAY be connected to runtime when:
1. A read-only policy registry exists
2. Shadow decisions are recorded but never block
3. A human review dashboard exists for shadow decisions

### active_enforced

**Design status**: Not ready. The Policy Platform explicitly defers
active_enforced requests in the ApprovalGate. The design documents it
as a future state but provides no path to it.

**Runtime status**: Deferred. active_enforced requires:
- Proven shadow mode operation (≥3 months of real shadow data)
- A rollback mechanism that works without code deployment
- Owner accountability (named owner, 6-month review cycle)
- Policy conflict resolution between multiple active policies
- Eval corpus expansion for enforced policy validation

**Gate**: active_enforced MUST NOT be activated until:
1. Shadow mode has operated for ≥3 months with real data
2. At least one CandidateRule has been observed for ≥2 weeks (existing protocol)
3. Rollback has been tested in a non-production environment
4. The Stage Summit has reviewed and approved activation criteria

## 7. Red-Team Coverage Summary

| Threat | Mitigation | Phase |
|--------|-----------|-------|
| Direct construction of active policy | PolicyRecord.__post_init__ invariants | 5.2-P |
| Bypass StateMachine via with_state | Renamed to _with_state_unchecked | 5.2-P |
| Dual-track PolicyProposal confusion | CandidateRulePolicyBridge unified | 5.3 |
| Weak evidence reaching activation | EvidenceGate 7 automated checks | 5.4 |
| Stale evidence treated as current | EvidenceGate freshness gate | 5.4 |
| CodeQL-only policy activation | Shadow evaluator + evidence gate block | 5.5 |
| React CI failure merged | Shadow WOULD_HOLD verdict | 5.5 |
| Human spoofed "deps:" title | Shadow WOULD_ESCALATE for humans | 5.5 |
| Missing rollback contract | ApprovalGate rejects | 5.6 |
| active_enforced bypass | ApprovalGate DEFERRED | 5.6 |

## 8. Open Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| READY_FOR_ACTIVATION naming ambiguity | Medium | Rename to READY_FOR_HUMAN_ACTIVATION_REVIEW to clarify it means review, not auto-activation |
| No persistent Policy store | Medium | PolicyRecords are in-memory only. Process restart loses all state. Need ORM-backed repository. |
| No UI review workbench | Medium | All review is programmatic. Humans cannot see Policy lifecycle, shadow results, or approval status. |
| No evidence dashboard | Low | Evidence gate results are not visible outside test output. |
| No production policy registry | Medium | No mechanism exists to load active policies into runtime. |
| No Pack/Adapter policy conflict resolver | Low | Design exists (§8.2) but not implemented. Two conflicting policies would produce undefined behavior. |
| No real CandidateRule data pipeline | High | The dogfood used synthetic evidence. No real CandidateRule has been created from operational data. The full learning loop has not been exercised with real evidence. |
| Policy Platform has no connection to Phase 5.4 design §9 open questions | Medium | Observation period, versioning, storage, rollback mechanism questions remain unresolved. |

## 9. Go / No-Go Gate for Future Active Policy

### active_shadow (GO — with conditions)

active_shadow may proceed when:
- [ ] Policy registry exists (read-only, in-memory acceptable for prototype)
- [ ] Governance adapter has a shadow policy check point
- [ ] Shadow decisions are advisory only (recorded, not enforced)
- [ ] Shadow decision data is collected for ≥1 month before review

### active_enforced (NO-GO)

active_enforced MUST NOT proceed. Conditions not met:
- [ ] Shadow mode has not operated with real data
- [ ] No rollback has been tested
- [ ] No owner accountability cycle established
- [ ] No Stage Summit review of enforcement criteria
- [ ] No Policy Platform eval corpus for enforced policies

### Auto-merge (NO-GO)

- [ ] Requires 3+ months clean Dependabot history (not yet met)
- [ ] Requires explicit human approval gate (not designed)

## 10. Recommended Next Phase

**Phase 6: Design Pack / UI Governance Pack**

Phase 5 has proven the Policy Platform domain model. The next bottleneck is
not more domain logic — it's human visibility and interaction.

Phase 6 should focus on:
1. **Policy Review UI**: A human workbench for reviewing Policy drafts, shadow
   results, evidence gate output, and approval decisions.
2. **Design System**: Unify the frontend components (dashboard, analyze,
   reviews, workspace) into a coherent design language.
3. **Evidence Timeline**: Visualize evidence freshness, policy lifecycle,
   and CandidateRule→Policy lineage.
4. **CandidateRule Workbench**: Interface for creating, reviewing, and
   promoting CandidateRules.

Phase 6 does NOT require:
- active_shadow or active_enforced runtime connection
- ORM/DB schema changes
- RiskEngine integration
- New security tools or Dependabot ecosystems

This aligns with the Stage Summit (4C) secondary recommendation: "Run
Option E (Dashboard) as a parallel lightweight track." The Policy Platform
needs a UI before it can become a real governance tool.

## 11. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/architecture/policy-platform-design.md` | Phase 5 design + implementation roadmap |
| `docs/product/ordivon-stage-summit-phase-4.md` | Stage Summit — recommended Policy as next move |
| `docs/runtime/security-external-tooling-closure.md` | Phase 4 source evidence for Policy dogfood |
| `docs/runbooks/ordivon-agent-operating-doctrine.md` | Agent doctrine §3.6 (CandidateRule ≠ Policy) |
| `docs/architecture/ordivon-current-architecture.md` | Layer 9 (CandidateRule), Layer 10 (Policy) |
