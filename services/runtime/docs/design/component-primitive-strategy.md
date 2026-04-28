# Component Primitive Strategy

Status: **DOCUMENTED** (Phase 6B)
Date: 2026-04-29
Phase: 6B
Tags: `primitives`, `radix`, `base-ui`, `react-aria`, `accessibility`, `ownership`

## 1. Purpose

Define which accessible interaction primitives Ordivon uses, which it
explicitly does not build, and how ownership works when external
component code enters the Ordivon repository.

## 2. The Rule

> **Ordivon never hand-rolls complex interactive components.**
> **Ordivon never depends on a third-party component library at runtime.**

These two rules are in tension. The resolution: copy-in ownership.

## 3. Primitive Selection

### 3.1 Complex components we delegate to primitives

| Component | Complexity | Why Not Hand-Roll |
|-----------|-----------|-------------------|
| Dialog / Modal | Focus trap, escape handling, ARIA roles, portal | ~200 lines of a11y logic |
| Popover | Positioning, focus management, dismiss layers | Floating UI complexity |
| Combobox / Autocomplete | Typeahead, listbox, selection, filtering | Async + a11y + keyboard |
| Menu / Dropdown | Nested menus, keyboard navigation, role hierarchy | WAI-ARIA menu pattern |
| Tabs | Focus management, ARIA tablist/tab/tabpanel | Roving tabindex |
| Select | Listbox, option navigation, form integration | Native select styling limits |
| Tooltip | Delay, positioning, hover/focus coordination | Timing edge cases |
| Toast / Notification | Stacking, auto-dismiss, accessibility announcement | Live region complexity |

### 3.2 Simple components we own directly

| Component | Why Safe to Own |
|-----------|----------------|
| Button | Trivial interaction. Governance semantics added at Layer 4. |
| Badge | Static display. No interaction. |
| Card | Static container. |
| Input / Textarea | Native elements with styling. |
| Table | HTML table with token bindings. |
| Spinner / Skeleton | Visual only. |

### 3.3 Candidate Libraries

#### Radix UI (Primary)

```text
Strengths:
  - Mature, widely adopted primitives
  - shadcn/ui compatibility (same primitives)
  - Excellent keyboard + screen reader support
  - Each primitive is a separate package (tree-shakeable)
  - Active maintenance, clear documentation

Weaknesses:
  - React-only
  - Styling requires custom approach (which Ordivon wants)

Decision: PRIMARY candidate.
```

#### Base UI (Secondary)

```text
Strengths:
  - From Radix/Floating UI/MUI team
  - Browser-native approach (Web Components direction)
  - Modern API design
  - Framework-agnostic potential

Weaknesses:
  - Newer, less battle-tested than Radix
  - Smaller ecosystem of examples

Decision: SECONDARY candidate. Monitor for maturity.
```

#### React Aria (Tertiary)

```text
Strengths:
  - Most comprehensive accessibility coverage
  - Adobe backing, long-term stability
  - Hooks-based (maximum flexibility)
  - Internationalization built-in

Weaknesses:
  - Hooks-based API adds complexity for simple use cases
  - More code to write per component
  - Steeper learning curve

Decision: TERTIARY. Consider if Radix/Base UI don't meet a specific need.
```

#### Headless UI

```text
Strengths:
  - Tailwind-native
  - Simple API

Weaknesses:
  - Smaller component set (no Combobox, no Toast)
  - Tightly coupled to Tailwind ecosystem

Decision: ACCEPTABLE but not primary. Smaller scope than Radix.
```

### 3.4 Explicitly NOT Used

| Library | Reason |
|---------|--------|
| Full design systems (Carbon, Fluent, Polaris, MUI, Chakra, Mantine) | Visual identity, runtime dependency, semantic mismatch |
| shadcn/ui as library dependency | Use ownership model, not npm dependency |
| Hand-rolled complex components | Accessibility risk |

## 4. Component Ownership Model

### 4.1 How components enter Ordivon

```text
1. Select primitive from Radix UI (Dialog, for example).
2. Copy shadcn/ui's wrapper code as a starting template.
3. Rename to Ordivon namespace (e.g., OrdivonDialog).
4. Bind to Ordivon semantic tokens.
5. Add governance-specific props if needed.
6. Commit to Ordivon repository as owned code.
7. Version alongside Ordivon, not alongside Radix.
```

### 4.2 What this means

- Radix provides accessibility. Ordivon provides governance semantics.
- Radix can upgrade; Ordivon chooses when to adopt upgrades.
- No runtime npm dependency on a component library's visual layer.
- All component code is Ordivon-governed and Design Pack-reviewable.

### 4.3 shadcn/ui's role

shadcn/ui is used as a **code template source**, not a **dependency**.
Its CLI is not used. Its npm package is not depended on. The component
structure and wrapper patterns are adapted, then owned by Ordivon.

## 5. Accessibility Baseline

### 5.1 Standard

WCAG 2.2 Level AA is the minimum.

### 5.2 What primitives provide

- Focus management (Radix handles focus trapping, restoring, roving tabindex)
- Keyboard navigation (Radix handles Enter, Escape, Arrow keys, Tab)
- ARIA roles and attributes (Radix sets correct roles, states, properties)
- Screen reader announcements (Radix uses live regions for dynamic content)

### 5.3 What Ordivon must add

- Color contrast verification on governance-specific colors
- Text labels on all governance badges (never color-only)
- High-risk action confirmation flows
- Preview/production labeling for screen readers
- Evidence freshness announcements for assistive technology

## 6. Non-Goals

- This strategy does not evaluate every UI library in existence.
- This strategy does not mandate React — it assumes React for Phase 6.
- This strategy does not define component APIs or props.
- Primitive selection may be revisited if React ecosystem shifts.
