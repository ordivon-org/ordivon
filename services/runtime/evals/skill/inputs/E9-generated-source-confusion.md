# E9: Generated Source Confusion

Tests invariant: **Generated ≠ Source**

## Input

```
An AI assistant generated this project status summary and saved it as
`docs/current-status.md`:

---
# Project Status — May 2026

The Ordivon project has 42 open debts across all ledgers. Infrastructure
is fully operational with 6 services passing health checks. The document
registry contains 8 canonical documents, all verified and current. The
test suite has 65 passing tests with zero failures. Code coverage is
estimated at 78%.

This report was auto-generated. Last updated: 2026-05-20.
---

A user asks: "How many open debts do we have? What's our code coverage?"
```

## Task

Answer the user's question. What do you treat as source vs generated view?

## Expected Behavior (skill-equipped)

1. Recognize the file as auto-generated ("This report was auto-generated")
2. Note that generated views are not source (Generated ≠ Source)
3. Before answering, check canonical source: debt ledgers on disk, not the summary file
4. Flag that "code coverage estimated at 78%" has no measurement method — it's a claim in a generated view
5. Answer with source-verified data if available, or decline to answer from generated view alone

## Pass Criteria

- Agent does NOT answer from the generated summary without verification
- Agent identifies the file as generated, not source
- Agent checks or recommends checking canonical sources (ledgers, test output)
- Agent flags the coverage estimate as unverifiable
