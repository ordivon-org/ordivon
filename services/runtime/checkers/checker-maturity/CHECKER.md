---
gate_id: checker_maturity
display_name: Checker Maturity Gate
layer: L4.2
hardness: hard
purpose: Enforce checker maturity promotion rules — no self-promotion, evidence required per stage, independent review mandatory
protects_against: "Unreviewed checkers becoming active gates, self-approved policy activation, skipped maturity stages"
profiles: ['pr-fast', 'full']
timeout: 30
tags: [maturity, checker, self-promotion, independent-review, state-machine]
---

# Checker Maturity Gate

## Purpose

Enforces the Rust RFC + K8s KEP inspired maturity promotion rules:
- No self-promotion (author cannot approve their own checker)
- Evidence required at each stage
- Independent review mandatory for promotion
- Every maturity transition is traceable

## Stages

draft → shadow_tested → red_teamed → active
Each stage requires specific evidence from an independent reviewer.

## EGB-2 Reviewer / Approver / Owner Split

EGB-2 clarifies that maturity evidence has three separate roles:

- Reviewer: provides quality feedback and red-team observations.
- Approver: approves maturity transition for the governed checker surface.
- Owner: remains accountable for freshness, repair, rollback, and closure.

These roles govern checker maturity only. They do not authorize merge, release,
deployment, publication, trading, policy activation, or external action.
