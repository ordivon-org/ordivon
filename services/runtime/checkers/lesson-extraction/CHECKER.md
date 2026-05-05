---
gate_id: lesson_extraction
display_name: Lesson → CandidateRule Extraction
layer: L8A
hardness: escalation
purpose: Scan lesson-ledger.jsonl for rule_candidate lessons and extract CandidateRule drafts — closes the learning loop
protects_against: "Uncaptured lessons, stagnant checker findings, learning loop disconnection, orphaned rule candidates"
profiles: ['full']
side_effects: true
timeout: 60
tags: [learning, candidate-rule, lesson, extraction, pipeline]
---

# Lesson → CandidateRule Extraction

## Purpose

Scans the lesson ledger for `rule_candidate` type lessons and extracts
CandidateRule drafts. This closes the Ordivon governance loop from
"detected a problem" to "proposed a rule to prevent it."

## Pipeline

```
Checker finds violations → Lesson recorded in lesson-ledger.jsonl
    ↓
lesson_type == "rule_candidate"
    ↓
CandidateRule draft extracted (idempotent: same lesson never duplicates)
    ↓
Draft entered into CandidateRule review state machine
    ↓
Human reviews draft → under_review → accepted_candidate or rejected
    ↓
accepted_candidate → CandidateRulePolicyBridge → PolicyRecord(draft)
    ↓
PolicyRecord → shadow evaluation → evidence gate → human activation review
```

## Current State

First run: extracts 2 rule_candidate lessons from the DG-Checkerization phase.
Produces CandidateRule drafts for human review.
