# Policy Proposal Path

Status: **DOCUMENTED**
Date: 2026-04-28
Wave: H
Tags: `policy-proposal`, `governance`, `candidate-rule`

## Purpose

Define the path from accepted_candidate CandidateRule to PolicyProposal(draft).
This is the bridge between governance learning (CandidateRule) and runtime
enforcement (Policy), with an explicit human approval gate between them.

## Scope

- accepted_candidate → PolicyProposal(draft)
- Proposal stores candidate_rule_id, source_refs, rationale, created_by
- Duplicate prevention (one proposal per rule)
- No active Policy creation

## Non-Goals

- No active Policy creation or activation
- No modification to pack policy files
- No RiskEngine behavior changes
- No ORM schema changes (PolicyProposal is a plain dataclass)

## CandidateRule vs PolicyProposal vs Policy

| Object | Status | Meaning |
|--------|--------|---------|
| CandidateRule(accepted_candidate) | Learned pattern | "This pattern is valid" |
| PolicyProposal(draft) | Proposed rule | "Let's make this a Policy" |
| Policy(active) | Enforced rule | "This is now blocking" |

Policy activation is a future wave — not implemented here.

## State Transition

```
CandidateRule(accepted_candidate)
  → PolicyProposal(draft)   ✅  propose_from_accepted()

Forbidden:
  draft / under_review / rejected → PolicyProposal
  Duplicate proposal for same rule
```

## Side-Effect Guarantees

- No Pack policy modification
- No RiskEngine import or modification
- No ExecutionRequest/Receipt
- No broker/order/trade/shell/MCP/IDE
- No active Policy states

## Test Evidence

`tests/unit/capabilities/test_policy_proposal.py` — 15 tests
- accepted → draft, all other statuses rejected
- Duplicate prevention
- source_refs preservation
- No RiskEngine/Execution/broker imports

## Limitations

- No ORM persistence (PolicyProposal is in-memory dataclass)
- No API endpoint
- No Policy activation wave
- Service state resets on process restart

## Next Recommended Wave

Wave I — Policy Activation: convert PolicyProposal(draft) to an active
Policy that modifies the runtime policy registry (policy_source.py).
Requires explicit human approval and an ORM schema change.
