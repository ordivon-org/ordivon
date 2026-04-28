# Governance Component Specification

Status: **DOCUMENTED** (Phase 6B)
Date: 2026-04-29
Phase: 6B
Tags: `components`, `governance`, `semantic`, `taxonomy`, `spec`

## 1. Purpose

Define every governance-specific UI component in the Ordivon Design
System. These components are not generic — they directly express Ordivon
governance semantics (evidence, policy, risk, actor, shadow, approval).

Each component specification includes: purpose, governance binding,
required token, accessibility requirement, and restriction.

## 2. Component Taxonomy

### 2.1 Status and Identity Badges (8 components)

#### EvidenceFreshnessBadge

```text
Purpose: Display evidence freshness state.
Token: --ordivon-evidence-{current,stale,regenerated,human-exception,missing}
Variants: CURRENT, STALE, REGENERATED, HUMAN_EXCEPTION, MISSING
A11y: Always paired with text label. Never color-only.
Restriction: Must appear on every evidence reference in the UI.
```

#### RiskLevelBadge

```text
Purpose: Display risk classification.
Token: --ordivon-risk-{low,medium,high}
Variants: LOW, MEDIUM, HIGH
A11y: Text label + icon + color. Keyboard focusable if actionable.
Restriction: High risk must pulse warning on first render.
```

#### PolicyStateBadge

```text
Purpose: Display Policy lifecycle state.
Token: --ordivon-policy-{draft,proposed,approved,active-shadow,active-enforced,deprecated,rolled-back,rejected}
Variants: DRAFT, PROPOSED, APPROVED, ACTIVE_SHADOW, ACTIVE_ENFORCED, DEPRECATED, ROLLED_BACK, REJECTED
Restriction: ACTIVE_ENFORCED must show "NOT AVAILABLE (Phase 5 NO-GO)". ACTIVE_SHADOW must show "ADVISORY ONLY".
```

#### ShadowVerdictBadge

```text
Purpose: Display shadow evaluation verdict.
Token: --ordivon-shadow-{recommend-merge,execute,escalate,hold,reject,no-match}
Variants: WOULD_RECOMMEND_MERGE, WOULD_EXECUTE, WOULD_ESCALATE, WOULD_HOLD, WOULD_REJECT, NO_MATCH
Restriction: Must always include "ADVISORY ONLY" sub-label. Never presented as an active decision.
```

#### ApprovalOutcomeBadge

```text
Purpose: Display approval decision outcome.
Token: --ordivon-approval-{approved-shadow,rejected,needs-evidence,needs-shadow,deferred}
Variants: APPROVED_FOR_SHADOW, REJECTED, NEEDS_MORE_EVIDENCE, NEEDS_MORE_SHADOW, DEFERRED
Restriction: APPROVED_FOR_SHADOW must show "Shadow mode only — not active enforcement."
```

#### ActorIdentityBadge

```text
Purpose: Display the actor who performed a governed action.
Token: --ordivon-actor-{human,dependabot,workflow,ai-agent,unknown}
Variants: HUMAN, DEPENDABOT, WORKFLOW, AI_AGENT, UNKNOWN
Restriction: UNKNOWN actor must trigger visual warning. BOT actors must be distinguishable from humans.
```

#### SeverityBadge

```text
Purpose: Display governance decision severity.
Token: --ordivon-risk-{low,medium,high}
Variants: EXECUTE, ESCALATE, REJECT
Restriction: REJECT must be visually distinct. Always paired with reason text.
```

#### StatusMetricCard

```text
Purpose: Dashboard metric with freshness and sub-label.
Template: Label → Value → Sub-label → Freshness timestamp
Restriction: Must show data freshness. Must label mock data.
```

### 2.2 Advisory and Safety Components (4 components)

#### AdvisoryBoundaryBanner

```text
Purpose: Clearly label surfaces that show advisory/shadow content.
Text: "ADVISORY ONLY — NOT A GOVERNANCE DECISION"
Token: --ordivon-advisory-banner-{bg,border,text}
Required on: Shadow Policy Workbench, Evidence Gate output, Governance Console (preview).
Restriction: Must be persistent — not dismissible by user action.
```

#### PreviewDataBanner

```text
Purpose: Label surfaces with preview/mock data.
Text: "PREVIEW — NOT PRODUCTION"
Token: --ordivon-preview-banner-{bg,border,text}
Required on: All surfaces with maturity=preview or maturity=future.
Restriction: Must be persistent. Must not be removable by user config.
```

#### DisabledActionWithReason

```text
Purpose: Show a disabled action with the governance reason.
Example: [Activate Policy] ← disabled. "active_enforced is DEFERRED (Phase 5 NO-GO)."
Token: --ordivon-disabled-action-{bg,text}
Restriction: Reason text must cite the governance decision that disabled it.
```

#### HumanExceptionReceiptPanel

```text
Purpose: Display a human override receipt.
Fields: Who, What, Why, When, Evidence considered, Risk accepted.
Restriction: Must appear whenever a governance decision is overridden by human.
```

### 2.3 Policy Workbench Components (5 components)

#### CandidateRuleCard

```text
Purpose: Display a CandidateRule for review.
Fields: Rule text, status badge, source refs, created date, reviewer.
Actions: Submit for Review, Reject.
Restriction: Submit action requires confirmation.
```

#### PolicyReviewCard

```text
Purpose: Display a PolicyRecord for approval review.
Fields: Policy text, state badge, evidence gate result, shadow summary, approval outcome, rollback contract summary, owner, reviewers.
Actions: Approve for Shadow, Reject, Request More Evidence.
Restriction: No "Activate" button. active_enforced is NOT AVAILABLE.
```

#### ShadowPolicyResultPanel

```text
Purpose: Display shadow evaluation results.
Fields: Case table (case ID, description, verdict badge, confidence), summary stats.
Restriction: Must display AdvisoryBoundaryBanner. Must label "ADVISORY ONLY."
```

#### RollbackContractPanel

```text
Purpose: Display a PolicyRollbackContract.
Fields: trigger, authorized_by, method, blast_radius, target_recovery_time, post_rollback_reviewer.
Restriction: Missing any field → show as invalid with warning.
```

#### HighRiskActionButton

```text
Purpose: Button for actions requiring explicit confirmation.
Carries: action_id, risk_level, required_evidence, required_role, disabled_reason, receipt_required.
Restriction: Must show confirmation dialog before executing. Must be disabled with reason when conditions unmet.
```

### 2.4 Evidence Display Components (3 components)

#### EvidenceReferenceList

```text
Purpose: Display a list of PolicyEvidenceRefs.
Each row: EvidenceFreshnessBadge + ref_type + ref_id + source.
Restriction: Stale evidence → reduced opacity, strikethrough. Missing evidence → "No evidence provided."
```

#### EvidenceLineageGraph

```text
Purpose: Visualize the chain: Lesson → Review → CandidateRule → PolicyRecord.
Restriction: Must be navigable (click-through to source objects).
```

#### TraceReferencePanel

```text
Purpose: Display a governance trace: Intake → Decision → Receipt → Outcome.
Restriction: Must show actor + timestamp at each step.
```

### 2.5 Console Layout Components (3 components)

#### ConsoleShell

```text
Purpose: Standard full-page app frame for all Ordivon consoles.
Composition: TopStatusBar + LeftNavigation + PrimaryWorkbench + EvidenceDrawer (optional).
```

#### SplitReviewLayout

```text
Purpose: Layout for review surfaces.
Composition: Left: governed object detail. Right: review form with action rail.
```

#### EvidenceDrawer

```text
Purpose: Collapsible bottom panel showing evidence references.
Restriction: Must show EvidenceFreshnessBadge on every reference.
```

## 3. Component Dependency Rules

```text
Governance Components MAY use Base Components.
Governance Components MUST use Semantic Tokens.
Governance Components MUST NOT contain hardcoded colors.
Base Components MAY use Primitive Components.
Application Surfaces compose Console Templates + Governance Components.
```

## 4. Non-Goals

- This spec does not define React props or TypeScript interfaces.
- This spec does not define Tailwind class names.
- This spec does not mandate a specific component library (Radix vs Base UI).
- Implementation details belong to Phase 6C.
