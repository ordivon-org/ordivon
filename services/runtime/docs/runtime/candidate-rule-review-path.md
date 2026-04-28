# CandidateRule Human Review Path

Status: **DOCUMENTED**
Date: 2026-04-28
Wave: G
Tags: `candidate-rule`, `review`, `human-in-the-loop`, `governance`

## Purpose

Define the controlled human review path for CandidateRule drafts.
After Wave B (Lesson → CandidateRule draft), drafts need explicit human
review before they can be considered as candidates for Policy.

## Scope

- Status transitions: draft → under_review → accepted_candidate / rejected
- Reviewer metadata stored in source_refs
- No Policy creation, no execution side effects

## Non-Goals

- No automatic Policy promotion
- No Policy table or Policy entity
- No modification to packs/finance or packs/coding
- No broker/order/trade/shell/MCP/IDE calls

## State Transition Table

```
from               → to                  method
────────────────────────────────────────────────────
draft              → under_review        submit_for_review()
draft              → rejected            reject_candidate()
under_review       → accepted_candidate  accept_candidate()
under_review       → rejected            reject_candidate()

Terminal states (no transitions):
  accepted_candidate — cannot be re-reviewed
  rejected           — must create new draft
```

## Forbidden Transitions

- draft → accepted_candidate (must pass through under_review)
- accepted_candidate → anything (terminal)
- rejected → accepted_candidate (must create new draft)
- any state → Policy (separate human-only process)

## Human Review Requirements

Each review operation records:
- `reviewer_id` — who performed the review
- `reviewed_at` — ISO timestamp
- `review_rationale` — reason for accept/reject (stored in source_refs)

## Why accepted_candidate Is Not Policy

`accepted_candidate` means "this rule draft has been reviewed and accepted
as a valid candidate." It does NOT mean the rule is active.

Policy promotion requires a separate, explicit human step that:
1. Maps the CandidateRule to a specific Pack policy implementation
2. Adds it to the relevant CI gate or blocking check
3. Is versioned and documented as a Policy change

This separation prevents automated governance escalation.

## Side-Effect Guarantees

- No Policy created
- No ExecutionRequest/Receipt created
- No broker/order/trade calls
- No shell/MCP/IDE calls
- No modification to pack policies

## Test Evidence

`tests/unit/capabilities/test_candidate_rule_review.py` — 14 tests
- All 6 valid transitions tested
- All forbidden transitions rejected
- source_refs and lesson_ids preserved
- No Policy/execution/broker side effects

## Limitations

- Reviewer metadata stored in source_refs (JSON text field) — not in dedicated columns
- No separate reviewed_at timestamp column
- No approval subsystem integration (future: HumanApprovalGate)
- No UI/API endpoint for review operations (service-layer only)

## Next Recommended Wave

Wave H — CandidateRule → Policy controlled promotion path.
Requires a Policy model/table and explicit human approval.
