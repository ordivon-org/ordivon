# OEP Template (EGB-2)

Status: **CURRENT** | Date: 2026-05-05 | Phase: EGB-2
Tags: `egb-2`, `oep`, `template`
Authority: `source_of_truth` | AI Read Priority: 2

Copy this template for cross-boundary or high-consequence Ordivon changes.

```markdown
# OEP-XXXX: Title

Status: **draft** | Date: YYYY-MM-DD | Phase: <phase>
Owner: <role-or-person>
Authority: proposal

## Summary

One paragraph describing the proposed change.

## Required Metadata

- oep_id: OEP-XXXX
- title: <title>
- owner: <owner>
- status: draft
- affected_layers: <core|pack|adapter|checker|docs|stage-template|public-wedge>
- authority_impact: evidence only; no action authorization
- public_surface_impact: <none|docs|package|cli|schema|adapter>

## Motivation

Why this change is needed.

## Non-Goals

What this change explicitly does not do.

## Design

What will be added or changed.

## Alternatives

Other approaches considered and why they are not selected now.

## Risks

Failure modes, false comfort risks, boundary risks, and rollback risks.

## Security Review

Security, supply-chain, token, adapter, public-surface, and execution-boundary
impact. Say "no security boundary change" only when true.

## Test Plan

Commands, fixtures, and expected trust signals.

## Rollback Plan

How to remove or disable this proposal safely.

## Graduation Criteria

Evidence required to move from draft to shadow_tested, red_teamed, active, or
stable.

## Authority Boundary

This OEP is evidence for review only. It does not authorize merge, release,
deployment, publication, trading, policy activation, or external action.
```
