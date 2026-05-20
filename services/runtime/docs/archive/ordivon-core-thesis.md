# Ordivon Core Thesis

Status: `current`
Authority: `source_of_truth`
Purpose: Define Ordivon's core position, value boundary, and non-negotiable governance thesis.
Supersedes: `deep-research-architecture-methodology`, `deep-research-governance-truth-model`, `deep-research-productization-plan`, historical positioning notes.
Verification: `scripts/check_document_registry.py`, Rust/Postgres trusted-path tests, certification readiness evidence.

## Thesis

Ordivon is a Trust Compiler for AI-mediated work. It turns claims, plans,
tool actions, AI outputs, evidence, authority, receipts, and unresolved debt
into governed state transitions.

Its value is not that it has many checkers. Its value is that failures can be
objectified, receipted, converted into rules, and reused across projects.

```text
AI expands generation and execution.
Ordivon constrains claims and execution until they earn trust.
```

Ordivon is not a chatbot wrapper, project-management layer, generic compliance
checklist, or documentation archive. It is the governance kernel between
unstable semantic output and high-consequence action.

## Problem

AI systems now produce more text, code, plans, actions, summaries, and
recommendations than humans can reliably audit by memory. The hard failure is
uncontrolled qualification:

- claims are treated as evidence;
- summaries are treated as truth;
- proposals are treated as authorization;
- tool traces are treated as closure;
- AI confidence is treated as review;
- repeated failures disappear into chat history instead of becoming system
  constraints.

Ordivon exists because high-consequence work needs a stricter path:

```text
claim -> object -> evidence -> authority -> gate -> execution -> receipt
```

## Position

Ordivon occupies the governance layer above agent frameworks and below human
or organizational authority.

- LLMs may propose and summarize.
- Policy engines may decide allow or deny.
- Workflow engines may execute.
- Logs may prove that an event happened.
- Ordivon decides whether a claim, action, or closure has governed standing.

The standing of an object depends on evidence, authority, scope, state, and
receipt. Text alone never moves state.

## Non-Negotiable Invariants

- Meaning is not governed commitment.
- Statement is not state transition.
- Claim is not evidence.
- Evidence is not authorization.
- Intent is not execution.
- Trace is not receipt.
- Generated view is not source of truth.
- AI proposal is not human approval.
- Waiver is not closure.
- Suppression is not deletion.

These invariants are product requirements, not slogans. Any Ordivon feature
that violates them is outside the core thesis.

## Compounding Mechanism

```text
failure
-> governance object
-> evidence and receipt
-> checker or policy candidate
-> gate
-> pack template
-> reusable method
```

A failure that only becomes a retrospective is weak memory. A failure that
becomes a gate changes future behavior.

## What This Changes In Implementation

- Core objects must be constructed through validated paths, not public struct
  literals that can fake legitimacy.
- Postgres/Rust is the trusted path for ledger, authority, adapter dispatch,
  comparator receipts, debt, and red-team proof.
- Python reporting can summarize evidence but cannot certify P-stage
  completion.
- Receipts must be emitted from comparator or runner results, not written as
  success claims.
- Dogfood seals must be generated from verified runs and signed evidence, not
  static outcome fixtures.
- Documentation is governed material. A document without authority, purpose,
  scope, and verification path is not a source of truth.

## Boundary

Current source-of-truth status means this document defines Ordivon's thesis and
governance meaning. It does not certify production security, external market
adoption, or support for destructive real-world actions. Those require separate
receipts and certification evidence.
