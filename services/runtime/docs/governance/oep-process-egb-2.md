# Ordivon Enhancement Proposal Process (EGB-2)

Status: **CURRENT** | Date: 2026-05-05 | Phase: EGB-2
Tags: `egb-2`, `oep`, `proposal`, `governance-process`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

An Ordivon Enhancement Proposal (OEP) makes high-consequence or cross-boundary
changes reviewable before implementation. It is inspired by mature proposal
processes in open-source engineering governance, but it is an Ordivon-local
process only.

An OEP is evidence for review. It is not approval, release permission, merge
permission, deployment permission, policy activation, or external action
authorization.

## When An OEP Is Required

Create an OEP before changes that affect more than one of these surfaces:

- Core governance behavior
- Pack behavior
- Adapter or external boundary behavior
- Checker maturity or gate behavior
- Public Verify wedge behavior
- Stage template semantics
- Ownership, approval, freeze, or trust-budget process

Small local fixes can continue to use receipts without an OEP.

## Required Fields

Every OEP must include:

```text
oep_id
title
owner
status
affected_layers
motivation
non_goals
design
alternatives
risks
security_review
test_plan
rollback_plan
graduation_criteria
authority_impact
public_surface_impact
```

## Status Ladder

```text
draft -> shadow_tested -> red_teamed -> active -> stable -> deprecated
```

Status means maturity of the proposal evidence. It does not authorize external
action. Promotion requires evidence, tests, owner review, and a receipt.

## Reviewer / Approver / Owner Split

- Reviewer: may provide quality feedback.
- Approver: may approve maturity transition for the governed surface.
- Owner: accountable for freshness, repair, and closure evidence.

These roles govern Ordivon documents and maturity transitions only. They do not
authorize merge, deployment, trading, publication, or external tool execution.

## OEP Review Rules

- OEPs must state non-goals explicitly.
- OEPs must define rollback before implementation.
- OEPs must include graduation criteria before any maturity promotion.
- OEPs must include security review when they affect public, package, adapter,
  agent, token, or execution boundaries.
- OEPs must include public-surface impact, even when the impact is "none".

## Non-Goals

The OEP process does not:

- Replace receipts.
- Replace tests.
- Replace human judgment.
- Create a public standard.
- Activate policy.
- Approve release, deployment, merge, publication, trading, or external action.
