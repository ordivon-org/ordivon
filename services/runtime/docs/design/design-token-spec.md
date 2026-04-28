# Design Token Specification

Status: **DOCUMENTED** (Phase 6B)
Date: 2026-04-29
Phase: 6B
Tags: `tokens`, `semantic`, `css-variables`, `w3c-dtcg`, `governance`

## 1. Purpose

Define Ordivon's semantic design token taxonomy. Every token maps to a
governance concept. Tokens are the single source of truth for visual
language — Tailwind classes and component styles derive from tokens,
not the other way around.

## 2. Token Architecture

```text
Raw Values (CSS custom properties)
  └─ Semantic Tokens (governance-meaningful names)
       └─ Component Tokens (component-specific bindings)
```

### Rule

- Raw values may change. Semantic tokens should be stable.
- Components bind to semantic tokens, never to raw values.
- If a semantic token's value changes, all bound components update.

## 3. Token Format

Tokens follow the W3C Design Tokens Community Group (DTCG) JSON format
where practical, with CSS custom properties as the runtime implementation.

```json
{
  "ordivon": {
    "evidence": {
      "freshness": {
        "current": {
          "$value": "#10B981",
          "$type": "color",
          "$description": "Current/fresh evidence"
        }
      }
    }
  }
}
```

CSS implementation:
```css
--ordivon-evidence-freshness-current: #10B981;
```

## 4. Token Taxonomy

### 4.1 Base Color Tokens

```text
--ordivon-color-surface-primary: #0A0F1F
--ordivon-color-surface-secondary: #111827
--ordivon-color-surface-elevated: #1F2937
--ordivon-color-surface-overlay: rgba(0, 0, 0, 0.5)
--ordivon-color-border-default: #374151
--ordivon-color-border-muted: #1F2937
--ordivon-color-text-primary: #F9FAFB
--ordivon-color-text-secondary: #9CA3AF
--ordivon-color-text-disabled: #6B7280
--ordivon-color-accent-primary: #3B82F6
--ordivon-color-accent-secondary: #8B5CF6
--ordivon-color-accent-tertiary: #06B6D4
```

### 4.2 Evidence Freshness Tokens

```text
--ordivon-evidence-current: #10B981
--ordivon-evidence-current-bg: rgba(16, 185, 129, 0.15)
--ordivon-evidence-stale: #9CA3AF
--ordivon-evidence-stale-bg: rgba(156, 163, 175, 0.10)
--ordivon-evidence-regenerated: #06B6D4
--ordivon-evidence-regenerated-bg: rgba(6, 182, 212, 0.15)
--ordivon-evidence-human-exception: #8B5CF6
--ordivon-evidence-human-exception-bg: rgba(139, 92, 246, 0.15)
--ordivon-evidence-missing: #6B7280
--ordivon-evidence-missing-bg: rgba(107, 114, 128, 0.08)
```

### 4.3 Policy State Tokens

```text
--ordivon-policy-draft: #6B7280
--ordivon-policy-proposed: #3B82F6
--ordivon-policy-approved: #06B6D4
--ordivon-policy-active-shadow: #6366F1
--ordivon-policy-active-shadow-bg: rgba(99, 102, 241, 0.15)
--ordivon-policy-active-enforced: #EF4444
--ordivon-policy-active-enforced-bg: rgba(239, 68, 68, 0.10)
--ordivon-policy-deprecated: #9CA3AF
--ordivon-policy-rolled-back: #F59E0B
--ordivon-policy-rejected: #EF4444
```

### 4.4 Risk Level Tokens

```text
--ordivon-risk-low: #10B981
--ordivon-risk-low-bg: rgba(16, 185, 129, 0.12)
--ordivon-risk-medium: #F59E0B
--ordivon-risk-medium-bg: rgba(245, 158, 11, 0.12)
--ordivon-risk-high: #EF4444
--ordivon-risk-high-bg: rgba(239, 68, 68, 0.10)
```

### 4.5 Actor Trust Tokens

```text
--ordivon-actor-human: #9CA3AF
--ordivon-actor-dependabot: #3B82F6
--ordivon-actor-workflow: #6B7280
--ordivon-actor-ai-agent: #8B5CF6
--ordivon-actor-unknown: #EF4444
```

### 4.6 Shadow Verdict Tokens

```text
--ordivon-shadow-recommend-merge: #10B981
--ordivon-shadow-execute: #10B981
--ordivon-shadow-escalate: #F59E0B
--ordivon-shadow-hold: #F59E0B
--ordivon-shadow-reject: #EF4444
--ordivon-shadow-no-match: #6B7280
```

### 4.7 Approval Outcome Tokens

```text
--ordivon-approval-approved-shadow: #6366F1
--ordivon-approval-approved-shadow-bg: rgba(99, 102, 241, 0.12)
--ordivon-approval-rejected: #EF4444
--ordivon-approval-needs-evidence: #F59E0B
--ordivon-approval-needs-shadow: #F59E0B
--ordivon-approval-deferred: #6B7280
```

### 4.8 Preview / Production Tokens

```text
--ordivon-preview-banner-bg: rgba(245, 158, 11, 0.10)
--ordivon-preview-banner-border: #F59E0B
--ordivon-preview-banner-text: #F59E0B
--ordivon-production-badge: #10B981
--ordivon-advisory-banner-bg: rgba(99, 102, 241, 0.10)
--ordivon-advisory-banner-border: #6366F1
--ordivon-advisory-banner-text: #6366F1
--ordivon-disabled-action-bg: #374151
--ordivon-disabled-action-text: #6B7280
```

### 4.9 Typography Tokens

```text
--ordivon-font-family: 'Inter', system-ui, -apple-system, sans-serif
--ordivon-font-mono: 'JetBrains Mono', 'Fira Code', monospace
--ordivon-font-size-xs: 0.6875rem
--ordivon-font-size-sm: 0.8125rem
--ordivon-font-size-base: 0.875rem
--ordivon-font-size-lg: 1rem
--ordivon-font-size-xl: 1.25rem
--ordivon-font-size-2xl: 1.5rem
--ordivon-font-weight-medium: 500
--ordivon-font-weight-semibold: 600
```

### 4.10 Spacing Tokens

```text
--ordivon-space-1: 0.25rem
--ordivon-space-2: 0.5rem
--ordivon-space-3: 0.75rem
--ordivon-space-4: 1rem
--ordivon-space-5: 1.25rem
--ordivon-space-6: 1.5rem
--ordivon-space-8: 2rem
--ordivon-space-10: 2.5rem
--ordivon-space-12: 3rem
```

### 4.11 Radius and Elevation Tokens

```text
--ordivon-radius-sm: 0.25rem
--ordivon-radius-md: 0.5rem
--ordivon-radius-lg: 0.75rem
--ordivon-shadow-sm: 0 1px 2px rgba(0,0,0,0.3)
--ordivon-shadow-md: 0 4px 6px rgba(0,0,0,0.4)
--ordivon-shadow-lg: 0 10px 15px rgba(0,0,0,0.5)
```

## 5. Light / Dark Mode Strategy

Semantic tokens have the same meaning in both modes. Only raw color values
change. The semantic token name is the contract.

```text
Light mode example:
  --ordivon-evidence-current: #059669

Dark mode example:
  --ordivon-evidence-current: #10B981
```

Both mean "current evidence." The color changes; the meaning does not.

## 6. Token Governance Rules

1. Tokens are defined in this document first, then in CSS.
2. New semantic tokens require Design Pack review.
3. Raw values may be tuned; token names are stable.
4. Components bind to semantic tokens only.
5. No hardcoded color values in component code.
6. Token JSON (DTCG format) is the canonical representation.

## 7. Non-Goals

- Tokens do not define component behavior (that's the component spec).
- Tokens do not define layout (that's the console template spec).
- Tokens do not replace Tailwind — they are the semantic layer above it.
