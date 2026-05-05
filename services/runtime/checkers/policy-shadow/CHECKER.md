---
gate_id: policy_shadow
display_name: Policy Shadow Runner
layer: L8B
hardness: escalation
purpose: Run CandidateRule drafts through shadow evaluation against red-team corpus — accumulate advisory evidence for activation review
protects_against: "Untested candidate rules entering activation review without shadow evidence, governance rules deployed without red-team validation"
profiles: ['full']
side_effects: true
timeout: 60
tags: [policy, shadow, candidate-rule, red-team, evidence-accumulation]
---

# Policy Shadow Runner

## Purpose

Runs every `draft` CandidateRule through the PolicyShadowEvaluator against
a fixed red-team corpus of governance scenarios. Produces advisory-only
verdicts (WOULD_EXECUTE, WOULD_ESCALATE, WOULD_HOLD, WOULD_REJECT,
WOULD_RECOMMEND_MERGE, NO_MATCH).

**Never blocks CI.** This is an escalation checker — its job is to accumulate
evidence, not to gate.

## Pipeline Position

```
CandidateRule draft (candidate-rule-drafts.jsonl)
    ↓
Policy Shadow Runner (this checker)
    ├── Constructs synthetic PolicyRecord from draft
    ├── Runs against red-team shadow corpus
    ├── Logs results to shadow-evaluation-log.jsonl
    └── Produces readiness-check report
    ↓
When shadow verdicts consistently match expected:
    PolicyEvidenceGate → READY_FOR_HUMAN_ACTIVATION_REVIEW
```

## Shadow Cases

10 red-team scenarios (in fixtures/shadow_cases.json):
- RT-001: Clean dependabot → would_recommend_merge
- RT-002: React + CI fail → would_hold
- RT-003: Stale evidence → would_hold
- RT-004: Human deps: title → would_escalate
- RT-005: CodeQL solo → would_escalate
- RT-008: Scope mismatch → no_match
- RT-009: CI fail non-react → would_hold
- RT-010: Unknown actor → would_escalate
- RT-011: AI agent → would_escalate
- GT-012: Human + test plan → would_execute

## Evidence Accumulation

Each run appends to `docs/governance/shadow-evaluation-log.jsonl`.
When a CandidateRule accumulates consistent positive verdicts across
multiple runs, the PolicyEvidenceGate can advance it from
READY_FOR_REVIEW → READY_FOR_SHADOW → READY_FOR_HUMAN_ACTIVATION_REVIEW.

## Current State

Initial deployment. The pipeline from checker findings → lesson →
candidate rule → shadow evaluation is now complete.
