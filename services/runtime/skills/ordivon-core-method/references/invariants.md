# Ordivon Core Invariants (with Governance ≠ Work)

These invariants are non-negotiable cognitive firebreaks.

## Foundational Invariants

| # | Invariant | Meaning |
|---|-----------|---------|
| 1 | Evidence ≠ Claim | A statement exists. Where is the evidence? |
| 2 | READY ≠ Authorization | Prepared is not authorized. |
| 3 | Generated ≠ Source | Summaries and dashboards are not origin. |
| 4 | Summary ≠ Truth | Compression loses detail. Summaries are lossy. |
| 5 | Receipt ≠ Resolution | A receipt records action. It does not prove the problem is solved. |
| 6 | Checker ≠ Policy | A checker enforces part of a policy. Pass ≠ full compliance. |
| 7 | Trace ≠ Receipt | Process record is not a closure statement. |
| 8 | Memory ≠ Source | Agent memory is context, not canonical truth. |
| 9 | Ignore ≠ Resolution | Skipping a problem does not resolve it. |
| 10 | AI Proposal ≠ Decision | The agent proposes. A human or gate decides. |

## Anti-Bureaucracy Invariants

| # | Invariant | Meaning |
|---|-----------|---------|
| 11 | Governance ≠ Work | A receipt, registry, checker, or ledger is not the work itself. Governance objects record real action; they do not substitute for it. |
| 12 | Governance Object ≠ Governed Reality | A registry entry is not the thing it registers. A receipt is not the action it describes. The map is not the territory. |

## Promotion Gate

No receipt may advance from DRAFT to VALIDATED without:

1. Real input (actual task, actual user request, actual trigger)
2. Real execution (command output, diff, API call, trace hash)
3. Real output (artifact, file, state change)
4. Real evidence (trace, test result, log)
5. Real verdict (PASS / DEGRADED / BLOCKED with evidence)
6. Consumer or reviewer (someone who used or reviewed the output)

Without these, the receipt status is capped at:
```
DRAFT
PROVISIONAL
NON_PRODUCTION
```

## Application

Every claim, output, receipt, and gate decision must be checked against
these invariants. When an invariant is violated, the finding is a governance
violation, not a style issue.
