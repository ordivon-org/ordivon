# Design System Baseline

Status: **DOCUMENTED** (Phase 6B)
Date: 2026-04-29
Phase: 6B
Tags: `design-system`, `tokens`, `layout`, `governance-ui`, `semantic`

## 1. Purpose

Define the visual and interaction language for Ordivon's Experience Layer.
This is not a CSS framework — it is a governance-aligned design system
that makes governance objects visible, reviewable, traceable, and safe
to act on.

## 2. Design System Principles

Ordivon UI is not decorative. Every visual element must serve governance.

### Core Principles

1. **Evidence before action.**
   No action button is enabled without visible evidence of readiness.
   Buttons that merge, activate, or execute must show their evidence source.

2. **Advisory is not truth.**
   Shadow verdicts, evidence gate results, and approval decisions are
   classifications. They are not objective facts. The UI must never
   present them as incontrovertible.

3. **Preview is not production.**
   Every surface in preview or future maturity must display a persistent
   "PREVIEW — NOT PRODUCTION" banner. Mock data must be labeled
   "SAMPLE DATA."

4. **Actor identity must be visible.**
   Every governed object must show its actor: human, dependabot[bot],
   github-actions[bot], or ai_agent.

5. **Freshness must be visible.**
   Every evidence reference must display its freshness state: current,
   stale, regenerated, or human_exception.

6. **High-risk actions disabled by default.**
   Actions that can cause financial loss, governance bypass, or policy
   activation must be disabled until explicit human enablement.

7. **Human exception requires receipt.**
   Any human override of a governance decision must produce a visible
   receipt recording who, why, and when.

8. **Shadow policy must be labeled advisory-only.**
   Every Policy Platform surface must display "Shadow Policy — Advisory
   Only" and "active_enforced: NOT AVAILABLE."

## 3. Design Tokens

### 3.1 Color Tokens

```text
--color-surface-primary: #0A0F1F
--color-surface-secondary: #111827
--color-surface-elevated: #1F2937
--color-surface-overlay: #00000080
--color-border-default: #374151
--color-border-muted: #1F2937
--color-text-primary: #F9FAFB
--color-text-secondary: #9CA3AF
--color-text-disabled: #6B7280
--color-accent-primary: #3B82F6
--color-accent-secondary: #8B5CF6
--color-accent-tertiary: #06B6D4
```

### 3.2 Semantic Color Tokens

```text
--color-semantic-success: #10B981
--color-semantic-warning: #F59E0B
--color-semantic-danger: #EF4444
--color-semantic-info: #3B82F6
--color-semantic-neutral: #6B7280
--color-semantic-advisory: #8B5CF6
--color-semantic-shadow: #6366F1
--color-semantic-stale: #9CA3AF
--color-semantic-current: #10B981
--color-semantic-regenerated: #06B6D4
--color-semantic-preview: #F59E0B
--color-semantic-production: #10B981
--color-semantic-disabled: #374151
```

### 3.3 Typography

```text
--font-family: 'Inter', system-ui, -apple-system, sans-serif
--font-mono: 'JetBrains Mono', 'Fira Code', monospace
--font-size-xs: 11px
--font-size-sm: 13px
--font-size-base: 14px
--font-size-lg: 16px
--font-size-xl: 20px
--font-size-2xl: 24px
--font-size-3xl: 30px
--font-weight-normal: 400
--font-weight-medium: 500
--font-weight-semibold: 600
--font-weight-bold: 700
--line-height-tight: 1.25
--line-height-normal: 1.5
--line-height-relaxed: 1.75
```

### 3.4 Spacing Scale

```text
--space-0: 0
--space-1: 4px
--space-2: 8px
--space-3: 12px
--space-4: 16px
--space-5: 20px
--space-6: 24px
--space-8: 32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

### 3.5 Radius Scale

```text
--radius-none: 0
--radius-sm: 4px
--radius-md: 8px
--radius-lg: 12px
--radius-xl: 16px
--radius-full: 9999px
```

### 3.6 Border and Elevation

```text
--border-width-thin: 1px
--border-width-medium: 2px
--shadow-sm: 0 1px 2px rgba(0,0,0,0.3)
--shadow-md: 0 4px 6px rgba(0,0,0,0.4)
--shadow-lg: 0 10px 15px rgba(0,0,0,0.5)
--shadow-xl: 0 20px 25px rgba(0,0,0,0.6)
```

### 3.7 Icon Usage

```text
Icon library: Lucide (preferred) or Heroicons
Size scale: 14px / 16px / 20px / 24px
Usage: icons accompany badges, status indicators, and action buttons.
       Icons alone must not communicate governance state.
       Always pair icon + text label for accessibility.
```

### 3.8 Chart/Graph Usage

```text
Library: Recharts (React) or equivalent
Charts must include:
  - axis labels
  - legend
  - data source attribution
  - freshness timestamp
  - "SAMPLE DATA" label when applicable
```

## 4. Light / Dark Mode Strategy

| Mode | Use Case | Surfaces |
|------|----------|----------|
| **Dark** | Default. Ops, trace, runtime, infrastructure | Command Center, State, Execution, Runtime, Infrastructure |
| **Light** | Review, analysis, policy workbench | Reviews, Knowledge, Governance, Shadow Policy |

### Shared Rules

- Semantic tokens have identical meaning in both modes
- No semantic drift: "danger" is red in both, "success" is green in both
- Preview/production labels identical across modes
- Evidence freshness colors identical across modes
- Accessibility contrast meets WCAG AA in both modes

## 5. Core Layout Primitives

### 5.1 Console Shell

```text
┌─────────────────────────────────────────────────────┐
│ Top Status Bar (actor, freshness, notifications)     │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ Left Nav │ Primary Workbench Area                   │
│          │                                          │
│          │                                          │
│          ├──────────────────────────────────────────┤
│          │ Evidence Drawer (collapsible)             │
└──────────┴──────────────────────────────────────────┘
```

### 5.2 Layout Components

| Layout | Description | Used On |
|--------|-------------|---------|
| Console Shell | Full-page app frame with nav + status bar | All surfaces |
| Left Navigation | Collapsible nav with layer-grouped items | All surfaces |
| Top Status Bar | Actor badge, freshness indicator, notifications | All surfaces |
| Metric Card Grid | 2-4 column grid of StatusMetricCards | Command Center, Dashboards |
| Primary Workbench | Main content area with action toolbar | Analyze, Reviews, Knowledge |
| Right Inspection Drawer | Slide-out panel for detail inspection | Reviews, State, Governance |
| Evidence Drawer | Bottom panel showing evidence references | Reviews, Shadow Policy |
| Action Rail | Vertical action buttons with confirmation | Reviews, Governance |
| Timeline Rail | Horizontal governance event timeline | State, Execution |
| Split Review Layout | Left: object, Right: review form | Reviews |

## 6. Density Rules

| Density | Spacing | Font | Use Case |
|---------|---------|------|----------|
| Comfortable | space-4, space-6 | base, lg | Review workbench, policy editor |
| Compact | space-2, space-3 | sm, base | Command center, trace view |
| Dense | space-1, space-2 | xs, sm | Data tables, audit logs |

## 7. Phase 6C Readiness

Before any UI implementation begins:

- [ ] Token names stable (this document)
- [ ] P0 component patterns defined (governance-ui-patterns.md)
- [ ] High-risk actions specified
- [ ] Preview labels specified
- [ ] P0 console shell defined (console-unification-plan.md)
- [ ] No production claim ambiguity
- [ ] active_enforced labeled NO-GO on all Policy surfaces
- [ ] Shadow policy labeled advisory-only on all Policy surfaces
