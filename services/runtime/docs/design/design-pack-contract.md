# Design Pack Contract

Status: **PROPOSED** (Phase 6A)
Date: 2026-04-29
Phase: 6A
Tags: `design`, `pack`, `governance`, `contract`, `ui`, `application-object`

## 1. Purpose

This document defines the Design Pack — a governed Pack in the Ordivon
architecture that treats design artifacts as governable objects with the
same intake → governance → review → lesson lifecycle as Finance and Coding
decisions.

Design is not decoration. Design is a high-consequence action: it shapes
what users see, what they trust, and what they can do. A misleading UI
can cause the same harm as a misleading financial recommendation.

## 2. Design Pack Governance Objects

### 2.1 DesignIntent

What is being proposed and why.

```text
DesignIntent
  intent_id: str
  title: str
  description: str
  problem_statement: str
  target_users: list[str]
  design_context: dict        # brand, platform, device, accessibility
  proposed_by: str
  created_at: datetime
```

### 2.2 DesignBrief

The structured brief that scopes a design task before any artifacts are produced.

```text
DesignBrief
  brief_id: str
  intent_id: str
  scope: DesignScope           # surface / component / system / workflow
  constraints: list[str]       # technical, brand, accessibility, timeline
  non_goals: list[str]
  reference_artifacts: list[str]
  reviewer_ids: list[str]
```

### 2.3 DesignGovernanceDecision

The governance classification of a design proposal. Follows the severity
protocol (reject / escalate / execute).

```text
DesignGovernanceDecision
  decision_id: str
  brief_id: str
  decision: str                # execute / escalate / reject
  reasons: list[str]
  risk_level: RiskLevel        # low / medium / high
  reviewer_id: str
  created_at: datetime
```

### 2.4 DesignPlanReceipt

Evidence that a design plan was reviewed and accepted. Immutable append-only.

```text
DesignPlanReceipt
  receipt_id: str
  brief_id: str
  plan_summary: str
  estimated_effort: str
  side_effects: dict           # all must be false for design phase
  created_at: datetime
```

### 2.5 DesignArtifact

A concrete design output: wireframe, mockup, prototype, token set, spec.

```text
DesignArtifact
  artifact_id: str
  brief_id: str
  artifact_type: DesignArtifactType  # wireframe / mockup / prototype / tokens / spec
  format: str                   # figma / code / markdown / image
  location: str                 # URL or file path
  status: str                   # draft / review / accepted / superseded
  version: int
  created_by: str
  created_at: datetime
```

### 2.6 DesignTokenSet

The visual design variables that define a surface's appearance.

```text
DesignTokenSet
  token_set_id: str
  name: str
  tokens: dict[str, DesignToken]
  surface_ids: list[str]
  version: int
```

### 2.7 ComponentSpec

A reusable UI component definition.

```text
ComponentSpec
  component_id: str
  name: str
  description: str
  variants: list[str]
  states: list[str]            # default / hover / active / disabled / loading / error / empty
  props: dict[str, str]        # prop_name → type
  accessibility: AccessibilityChecklist
  token_bindings: dict[str, str]  # prop → token reference
```

### 2.8 SurfaceSpec

A complete screen or page specification.

```text
SurfaceSpec
  surface_id: str
  name: str
  route: str
  layout: str                  # grid / split / full-width / modal
  component_specs: list[str]   # component_id references
  data_bindings: dict[str, str]
  governance_surface: bool     # does this surface show governance decisions?
  high_risk_actions: list[str] # actions that require confirmation
  preview_state: str           # real / mock / preview / future
```

### 2.9 InteractionSpec

How users interact with a surface or component.

```text
InteractionSpec
  interaction_id: str
  target_id: str               # component_id or surface_id
  trigger: str                 # click / hover / keyboard / voice / gesture
  action: str                  # navigate / submit / cancel / confirm / dismiss
  confirmation_required: bool
  undoable: bool
  keyboard_shortcut: str | None
```

### 2.10 AccessibilityChecklist

Required accessibility properties for any governed UI.

```text
AccessibilityChecklist
  checklist_id: str
  target_id: str
  contrast_ratio: str          # meets WCAG AA / AAA
  keyboard_navigable: bool
  screen_reader_label: str
  focus_order: int
  aria_roles: list[str]
  motion_safe: bool
  touch_target_size: str
  color_not_only: bool
```

### 2.11 ImplementationHandoff

The bridge between design and engineering.

```text
ImplementationHandoff
  handoff_id: str
  artifact_ids: list[str]
  accepted_by_engineering: bool
  handoff_notes: str
  production_readiness: ProductionReadiness  # not_ready / preview_only / production_ready
  created_at: datetime
```

### 2.12 DesignReview

A human review of a design artifact or surface.

```text
DesignReview
  review_id: str
  artifact_id: str
  reviewer_id: str
  verdict: str                 # accepted / needs_revision / rejected
  feedback: str
  created_at: datetime
```

### 2.13 DesignOutcome

The result of a design decision after implementation.

```text
DesignOutcome
  outcome_id: str
  brief_id: str
  artifact_ids: list[str]
  actual_result: str           # what happened vs what was intended
  user_feedback: str | None
  created_at: datetime
```

### 2.14 DesignLesson

A lesson extracted from design outcomes.

```text
DesignLesson
  lesson_id: str
  outcome_ids: list[str]
  insight: str
  severity: str
  created_at: datetime
```

### 2.15 DesignCandidateRule

A candidate rule extracted from design lessons.

```text
DesignCandidateRule
  candidate_rule_id: str
  lesson_ids: list[str]
  rule_text: str
  scope: DesignScope
  status: CandidateRuleStatus  # draft / under_review / accepted_candidate / rejected
  created_at: datetime
```

## 3. Design Pack Lifecycle

```
Design Intent
  → Design Governance Gate (validate_intake via severity protocol)
  → Design Plan Receipt (immutable, append-only)
  → Design Artifact / Surface Spec (the actual design work)
  → Design Review (human acceptance / revision / rejection)
  → Implementation Handoff (bridge to engineering)
  → Implementation (production code, governed by Repo Governance)
  → Outcome (what actually happened)
  → Lesson (what was learned)
  → CandidateRule (can experience become an active constraint?)
```

## 4. Design Pack Boundaries

Design is a governed Pack. It does not bypass any other Pack or governance layer.

### Hard Boundaries

1. **Design output is proposal, not truth.**
   A mockup is a proposal. A spec is a proposal. Neither is accepted
   implementation until it passes Repo Governance.

2. **Generated UI/code is handoff candidate, not accepted implementation.**
   AI-generated or design-tool-generated code is a starting point.
   Production merge requires full Repo Governance.

3. **Production code changes still require Repo Governance.**
   Design Pack does not replace the Coding Pack or the GitHub adapter.
   Design artifacts inform implementation but do not authorize it.

4. **High-risk actions must stay disabled by default.**
   Any action that can cause financial loss, data loss, governance bypass,
   or user confusion must require explicit enablement. A mockup that shows
   these as active is misleading if it is not labeled as preview.

5. **No fake production claims.**
   A mockup must not show fake "trades executed" or "policies active" without
   clear "PREVIEW — NOT PRODUCTION" labeling. Misrepresentation erodes
   governance trust.

6. **Preview/mock data must be labeled.**
   Any screenshot, mockup, or prototype that uses sample data must clearly
   label it as "SAMPLE DATA — NOT REAL" or "MOCK DATA."

7. **Accessibility and responsive behavior must be explicit.**
   Every SurfaceSpec must include an AccessibilityChecklist. "We'll do it
   later" is not an acceptable answer for governed UI.

## 5. Design Pack Scope

The Design Pack governs:

| Scope | Description |
|-------|-------------|
| `surface` | Individual screens, pages, and views |
| `component` | Reusable UI components |
| `system` | Design systems, token sets, component libraries |
| `workflow` | Multi-step user flows and interaction patterns |

## 6. Relationship to Other Packs

| Pack | Relationship |
|------|-------------|
| Coding Pack | Design artifacts inform coding intents. Coding governance gates the implementation. |
| Finance Pack | Design of finance surfaces must not imply live trading without explicit risk labeling. |
| Policy Platform | Design of policy review surfaces is governed by the Design Pack. Policy activation is governed by the Policy Platform. |
| Repo Governance | All design-to-code handoffs must pass Repo Governance before merge. |

## 7. Non-Goals

- Design Pack does not replace Figma, design tools, or existing workflows.
- Design Pack does not require a design token engine or CSS framework.
- Design Pack does not auto-generate code from mockups.
- Design Pack does not create active Policy from design decisions.
