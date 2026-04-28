# Ordivon Design System Architecture

Status: **DOCUMENTED** (Phase 6B)
Date: 2026-04-29
Phase: 6B
Tags: `design-system`, `architecture`, `layered`, `semantic`, `governance-ui`

## 1. First-Principles Purpose

Ordivon's UI is not decorative. It exists to make governance objects —
intent, evidence, decision, receipt, review, policy, actor, risk, state,
rollback — **visible, reviewable, and safe to act on**.

The Design System is not a component library. It is a **governance-aligned
semantic language** for the Experience Layer.

### Core questions the design system must answer

```text
When a human sees a governance object on screen:
  - Is this real or advisory?
  - Is this current or stale?
  - Who made this decision?
  - What evidence supports it?
  - What is the risk if I act?
  - Can I act, or is this disabled?
  - If I act, what evidence will be recorded?
  - If I override, where is the receipt?
```

A Button, Card, or Badge that does not answer these questions is
insufficient for Ordivon.

## 2. External Research Summary

### 2.1 Enterprise Design Systems

| System | Strengths | Ordivon Takes | Ordivon Leaves |
|--------|----------|---------------|----------------|
| **Carbon** (IBM) | Enterprise shell, state cards, token layering, platform feel | System-ness, operations console patterns, product-level layout | IBM brand, heavy enterprise weight |
| **Primer** (GitHub) | Developer-first clarity, issue/PR/review/state expression, lightweight rigor | Developer workbench style, information density, governance-as-code feel | GitHub-specific components |
| **Polaris** (Shopify) | Admin workflows, migration warnings, risk operations | Admin panel patterns, risk confirmation, deprecation awareness | Shopify brand, React deprecation risk |
| **Fluent UI** (Microsoft) | Enterprise forms, accessibility, cross-platform consistency | Complex state controls, chart/dashboard patterns, a11y depth | Microsoft product style |

**Decision**: All four are **references**, not foundations. Ordivon builds its own semantic language.

### 2.2 Accessible Primitive Libraries

| Library | Approach | Ordivon Suitability |
|---------|----------|-------------------|
| **Radix UI** | Unstyled, accessible React primitives | High — mature, well-documented, shadcn-compatible |
| **Base UI** | Unstyled components from Radix/Floating UI/MUI team | High — modern, browser-native |
| **React Aria** (Adobe) | Style-free accessible hooks + components | Medium — very powerful but hooks-based API |
| **Headless UI** (Tailwind) | Unstyled, Tailwind-friendly | Medium — smaller scope, tightly coupled to Tailwind |

**Decision**: Use accessible primitives (Radix or Base UI) for complex
interactions. Never hand-roll Dialog, Popover, Combobox, Menu, Tabs,
Tooltip, or Select.

### 2.3 Styling and Component Ownership

| Approach | Ordivon Role |
|----------|-------------|
| **Tailwind CSS** | Implementation layer. Utility classes execute design tokens. |
| **shadcn/ui** | Ownership model (copy-in), not identity. Components enter Ordivon repo → governed by Design Pack. |
| **Storybook** | Component documentation workbench for hard-to-reach governance states (stale evidence, NO-GO actions, shadow verdicts). |

### 2.4 Standards

| Standard | Ordivon Use |
|----------|------------|
| **WCAG 2.2 AA** | Accessibility baseline. Not optional. |
| **W3C Design Tokens (DTCG)** | Token format for cross-tool interoperability. JSON-based. |
| **Atomic Design** (Brad Frost) | Hierarchy model: atoms → molecules → organisms → templates → pages. |
| **Nielsen's Heuristics** | Cognitive engineering principles for governance UI. |

## 3. Architecture Layers

Ordivon's design system has **6 layers**, each building on the one below.

```text
Layer 6: Application Surface
  └─ Concrete pages/screens (Command Center, Policy Workbench, etc.)

Layer 5: Console Template
  └─ Reusable layout patterns (Console Shell, Split Review, Evidence Drawer)

Layer 4: Governance Component
  └─ Ordivon-specific semantic components (EvidenceFreshnessBadge, PolicyStateBadge, etc.)

Layer 3: Base Component
  └─ Generic UI components owned by Ordivon (Button, Card, Badge, Table, Dialog)

Layer 2: Token
  └─ Semantic design variables (--ordivon-evidence-current, --ordivon-risk-high, etc.)

Layer 1: Primitive
  └─ Accessible interaction primitives from Radix/Base UI (Dialog, Popover, Combobox, etc.)
```

### Layer Details

**Layer 1 — Primitive**: Radix UI or Base UI provides unstyled, accessible
interaction behavior. Ordivon never implements Dialog, Popover, Combobox,
Menu, Tabs, or Tooltip from scratch.

**Layer 2 — Token**: CSS variables organized by Ordivon semantic domains
(evidence, risk, policy, actor, freshness, trust). Token values are the
single source of truth for visual language.

**Layer 3 — Base Component**: Generic components (Button, Card, Badge,
Table, Input) built on primitives + tokens. These are Ordivon-owned via
shadcn-style copy-in. They have no governance semantics.

**Layer 4 — Governance Component**: Components that express Ordivon
governance concepts directly. They carry semantic meaning beyond visual
presentation. Examples: EvidenceFreshnessBadge, PolicyStateBadge,
ShadowVerdictBadge, ApprovalOutcomeBadge, HighRiskActionButton.

**Layer 5 — Console Template**: Reusable layout patterns that compose
base + governance components into workbench surfaces. Examples: Console
Shell, Split Review Layout, Evidence Drawer.

**Layer 6 — Application Surface**: Concrete screens defined in the
Ordivon Application Object and Console Inventory. These instantiate
console templates with specific data bindings.

## 4. Key Architecture Decisions

### Decision 1: No wholesale adoption of any external design system

Carbon, Fluent, Polaris, and Primer are references. Ordivon's visual
identity, semantic tokens, and governance components are Ordivon-owned.

### Decision 2: Accessible primitives for complex interactions

Radix UI (primary candidate) or Base UI provides Dialog, Popover,
Combobox, Menu, Tabs, Tooltip, Select. Ordivon never hand-rolls these.

### Decision 3: Ordivon-owned semantic tokens

Tokens express governance semantics, not just visual properties.
`--ordivon-evidence-current` is a semantic token.
`--color-green-500` is a visual value, not a token.

### Decision 4: shadcn-style copy-in component ownership

Components enter the Ordivon repository as owned code. They are
renamed, restyled, and governed by the Design Pack. No runtime
dependency on external component libraries.

### Decision 5: Tailwind is implementation, not semantics

Tailwind executes Ordivon tokens. Token definitions live in CSS
variables and JSON (W3C DTCG format). Tailwind classes are the
implementation detail, not the design contract.

### Decision 6: High-risk actions are special governance surfaces

HighRiskActionButton is not a Button variant. It is a governance
component that carries action_id, risk_level, required_evidence,
required_role, disabled_reason, and receipt_required.

### Decision 7: Storybook before large UI expansion

Hard-to-reach governance states (stale evidence, NO-GO actions,
shadow verdicts) must be documented in a component workbench
before production implementation.

### Decision 8: Labels are mandatory, not decorative

Shadow/advisory/preview/production labels are enforced by governance
components, not by developer discipline. PreviewBanner and
AdvisoryBoundaryBanner are not optional.

## 5. Red-Team Risks

| Risk | Mitigation |
|------|-----------|
| Adopting external system as Ordivon identity | Decision 1: references only |
| Hand-rolling inaccessible complex components | Decision 2: Radix/Base UI primitives |
| Semantic drift in token usage | Decision 3: single token source |
| External component upgrade breaks Ordivon | Decision 4: copy-in ownership |
| Tailwind classes become semantic truth | Decision 5: tokens are source |
| High-risk actions expressed as normal buttons | Decision 6: governance component |
| Governance states untestable before production | Decision 7: Storybook workbench |
| Missing labels on preview/advisory surfaces | Decision 8: mandatory label components |

## 6. Phase 6C Readiness Gate

Before any UI implementation:

- [ ] Architecture layers stable (this document)
- [ ] Token taxonomy complete (design-token-spec.md)
- [ ] Governance component taxonomy complete (governance-component-spec.md)
- [ ] Primitive strategy selected and documented (component-primitive-strategy.md)
- [ ] Console unification plan updated (console-unification-plan.md)
- [ ] External research conclusions documented
- [ ] All 8 architecture decisions explicitly recorded
- [ ] No production claim ambiguity
- [ ] active_enforced labeled NO-GO on all Policy surfaces
- [ ] Shadow policy labeled advisory-only on all Policy surfaces
