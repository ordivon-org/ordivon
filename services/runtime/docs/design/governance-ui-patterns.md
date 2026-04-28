# Governance UI Pattern Library

Status: **DOCUMENTED** (Phase 6B)
Date: 2026-04-29
Phase: 6B
Tags: `ui`, `patterns`, `governance`, `components`, `evidence`, `policy`

## 1. Purpose

Define the reusable UI component patterns for Ordivon governance surfaces.
Every component maps to a governance concept. No component is purely decorative.

## 2. Status and Identity Badges

### StatusMetricCard

```text
┌─────────────────────────┐
│ ACTIVE POLICIES         │  ← metric label
│ 3                       │  ← value (large)
│ 2 shadow · 0 enforced   │  ← sub-label
│ Updated 2m ago          │  ← freshness
└─────────────────────────┘
```

### SeverityBadge

```text
[EXECUTE]  → green, low risk
[ESCALATE] → amber, medium risk
[REJECT]   → red, high risk
```

Rules: always paired with reason text. Never color-only.

### EvidenceFreshnessBadge

```text
[CURRENT]      → green
[STALE]        → gray, strikethrough
[REGENERATED]  → cyan, refresh icon
[HUMAN EXCEPT] → purple, person icon
```

### ActorIdentityBadge

```text
[human-maintainer]     → person icon, default
[dependabot[bot]]      → bot icon, blue
[github-actions[bot]]  → workflow icon, gray
[ai_agent]             → sparkle icon, purple
[unknown]              → question icon, red — escalation trigger
```

### PolicyStateBadge

```text
[draft]              → gray
[proposed]           → blue
[approved]           → cyan
[active_shadow]      → purple, "ADVISORY ONLY" sub-label
[active_enforced]    → red, "NOT AVAILABLE" sub-label (Phase 5 NO-GO)
[deprecated]         → gray, strikethrough
[rolled_back]        → red, rollback icon
[rejected]           → red, X icon
```

### ShadowVerdictBadge

```text
[WOULD_RECOMMEND_MERGE] → green, merge icon
[WOULD_EXECUTE]         → green, check icon
[WOULD_ESCALATE]        → amber, flag icon
[WOULD_HOLD]            → amber, pause icon
[WOULD_REJECT]          → red, block icon
[NO_MATCH]              → gray, "—"
```

### ApprovalOutcomeBadge

```text
[APPROVED_FOR_SHADOW]    → purple, "ADVISORY ONLY"
[REJECTED]               → red
[NEEDS_MORE_EVIDENCE]    → amber
[NEEDS_MORE_SHADOW]      → amber
[DEFERRED]               → gray
```

### RiskLevelBadge

```text
[LOW]    → green
[MEDIUM] → amber
[HIGH]   → red
```

## 3. Advisory and Safety Banners

### AdvisoryBoundaryBanner

```text
┌────────────────────────────────────────────────────────┐
│ ⚠ ADVISORY ONLY — NOT A GOVERNANCE DECISION           │
│                                                        │
│ This surface shows shadow evaluation results. These    │
│ are classifications, not enforced policies.            │
│ No active policy is created by viewing this surface.   │
└────────────────────────────────────────────────────────┘
```

Used on: Shadow Policy Workbench, Evidence Gate output, Governance Console (preview).

### PreviewDataBanner

```text
┌────────────────────────────────────────────────────────┐
│ ⚠ PREVIEW — NOT PRODUCTION                            │
│                                                        │
│ Data shown is sample/mock data for design validation.  │
│ No real trades, policies, or user data are displayed.  │
└────────────────────────────────────────────────────────┘
```

Used on: All surfaces with maturity=preview or maturity=future.

### DisabledActionWithReason

```text
[Activate Policy]  ← disabled button
"active_enforced is DEFERRED (Phase 5 NO-GO). See Phase 5Z red-team closure."
```

### HighRiskActionButton

```text
[Confirm Merge]  ← primary button, requires confirmation dialog
"Are you sure? This will merge Dependabot PR #5 (sentry-sdk). Reviewer: @alice."

[CANCEL] [CONFIRM MERGE]
```

## 4. Policy Workbench Components

### CandidateRuleCard

```text
┌────────────────────────────────────────────────────────┐
│ CANDIDATE RULE    [draft]                              │
│                                                        │
│ "Trusted Dependabot dependency-only PRs..."             │
│                                                        │
│ Source: lesson:L001, review:R001                        │
│ Created: 2026-04-29 · by @alice                         │
│                                                        │
│ [Submit for Review]  [Reject]                           │
└────────────────────────────────────────────────────────┘
```

### PolicyReviewCard

```text
┌────────────────────────────────────────────────────────┐
│ POLICY REVIEW    POL-DOGFOOD-001    [draft]             │
│                                                        │
│ "Trusted Dependabot dependency-only PRs..."             │
│                                                        │
│ Evidence Gate: READY_FOR_HUMAN_ACTIVATION_REVIEW       │
│ Shadow: 3× WOULD_RECOMMEND_MERGE, 0 hold, 0 reject     │
│ Approval: APPROVED_FOR_SHADOW                           │
│                                                        │
│ Rollback: fp_rate > 5% · state_transition · seconds     │
│ Owner: alice · Reviewers: alice (tech), bob (domain)    │
│                                                        │
│ [Approve for Shadow]  [Reject]  [Request More Evidence] │
└────────────────────────────────────────────────────────┘
```

### ShadowPolicyResultPanel

```text
┌────────────────────────────────────────────────────────┐
│ SHADOW EVALUATION RESULTS    [ADVISORY ONLY]            │
│                                                        │
│ DF-005 (sentry-sdk)    WOULD_RECOMMEND_MERGE   0.85    │
│ DF-006 (uvicorn)       WOULD_RECOMMEND_MERGE   0.85    │
│ DF-008 (@types/node)   WOULD_RECOMMEND_MERGE   0.85    │
│ DF-007 (React)         WOULD_HOLD              0.90    │
│ DF-STALE (stale)       WOULD_HOLD              0.80    │
│                                                        │
│ Confidence: 0.85  ·  FP Risk: low  ·  FN Risk: low     │
│                                                        │
│ ⚠ These are advisory classifications only.             │
│   No active policy is created.                          │
└────────────────────────────────────────────────────────┘
```

### RollbackContractPanel

```text
┌────────────────────────────────────────────────────────┐
│ ROLLBACK CONTRACT                                      │
│                                                        │
│ Trigger:     false_positive_rate > 5%                  │
│ Authorized:  alice                                     │
│ Method:      state_transition                          │
│ Blast Radius: CI gate repo-governance-pr               │
│ Recovery:    seconds                                   │
│ Post-Rollback Review: bob                              │
│                                                        │
│ [✓ Contract Valid]                                      │
└────────────────────────────────────────────────────────┘
```

## 5. Evidence Display Rules

### EvidenceReferenceList

```text
┌────────────────────────────────────────────────────────┐
│ EVIDENCE REFERENCES (3)                                │
│                                                        │
│ [CURRENT] candidate_rule:001     → CandidateRule       │
│ [CURRENT] lesson:001             → Lesson              │
│ [CURRENT] review:001             → Review              │
│ [STALE]   ci_artifact:build-42   → CI Build #42        │
│ [REGEN]   eval_result:case-24    → Eval Case #24       │
└────────────────────────────────────────────────────────┘
```

Rules:
- Current evidence: green badge, full opacity
- Stale evidence: gray badge, reduced opacity, strikethrough text
- Regenerated: cyan badge, refresh icon
- Human exception: purple badge, person icon, shows who/when/why
- Missing evidence: empty state with "No evidence provided" message

### Evidence Lineage Visualization

```text
Lesson:L001 ──→ CandidateRule:CR001 ──→ PolicyRecord:POL-001
     │                    │
     └── Review:R001 ─────┘
```

### TraceReferencePanel

```text
┌────────────────────────────────────────────────────────┐
│ TRACE                                                  │
│                                                        │
│ DecisionIntake → GovernanceDecision → ExecutionReceipt  │
│     ↑                                          │       │
│     └── DecisionIntake:DI-001 ─────────→ Receipt:ER-01 │
│                                                        │
│ Source: CI artifact #build-42 · 2026-04-29 04:30 UTC   │
└────────────────────────────────────────────────────────┘
```

## 6. Policy Platform UI Safety Rules

### Must display on every Policy surface

| Surface | Required Label |
|---------|---------------|
| Shadow Policy Workbench | "ADVISORY ONLY — No active policy is created" |
| Evidence Gate output | "READY_FOR_HUMAN_ACTIVATION_REVIEW — not automatic activation" |
| Approval results | "APPROVED_FOR_SHADOW" with "active_enforced: NOT AVAILABLE" sub-label |
| Policy state | If active_shadow: "ADVISORY ONLY" sub-label |
| Policy state | If active_enforced: "NOT AVAILABLE (Phase 5 NO-GO)" |

### Must never display

- "Activate Policy" button without explicit active_enforced gate
- "Merge Dependabot PR" without human confirmation
- Production claims on preview surfaces
- Real data appearance on mock data surfaces
- active_enforced as available or reachable

### Must enforce

- Evidence before action: action buttons disabled until evidence shown
- Freshness visibility: every evidence ref has freshness badge
- Actor visibility: every object shows its actor
- Shadow labeling: every shadow result says "ADVISORY ONLY"

## 7. Red-Team Risks

| Risk | Mitigation |
|------|-----------|
| UI overclaims production readiness | PreviewBanner on all preview surfaces |
| Mock data mistaken for real | MockDataLabel on all sample data |
| active_enforced shown as available | PolicyStateBadge shows "NOT AVAILABLE" |
| Shadow result mistaken for policy | AdvisoryBoundaryBanner on all Policy surfaces |
| Dangerous buttons enabled early | HighRiskActionButton requires confirmation |
| Color-only status communication | All badges paired with text labels |
| Dark/light semantic divergence | Shared semantic tokens across modes |
| Too many consoles before P0 workbench | Console unification plan (separate doc) |
| Design system becomes aesthetic-only | Every component maps to governance concept |

## 8. Phase 6C Readiness

All component patterns defined above must be stable before implementation:

- [ ] Status badges: 8 patterns defined
- [ ] Safety banners: 3 patterns defined
- [ ] Policy workbench: 5 patterns defined
- [ ] Evidence display: 3 patterns defined
- [ ] Policy safety rules: 4 required labels, 3 forbidden items
- [ ] Red-team: 9 risks, 9 mitigations
