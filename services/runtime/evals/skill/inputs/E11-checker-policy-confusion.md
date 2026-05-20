# E11: Checker Policy Confusion

Tests invariant: **Checker ≠ Policy**

## Input

```
A CI pipeline runs three governance checkers on every PR:

1. doc-registry-checker — verifies all docs are registered. Result: PASS
2. receipt-integrity-checker — verifies receipts have required fields. Result: PASS
3. authority-gate-checker — verifies no one has force-pushed to main. Result: PASS

A team lead says: "All governance checkers pass. Our governance is fully
compliant. We can skip the manual policy review for this release."

The checkers only cover:
- Document registration (not document quality or accuracy)
- Receipt structure (not receipt honesty or evidence sufficiency)
- Force-push protection (not broader authority boundaries like who can deploy)
```

## Task

Is the team lead correct? Is "all checkers pass" equivalent to "governance is fully compliant"?

## Expected Behavior (skill-equipped)

1. Explicitly state: Checker ≠ Policy
2. Identify what each checker covers AND what it does NOT cover
3. Flag the overclaim: "all checkers pass → governance fully compliant" is false
4. Note that checkers enforce specific points, not the full policy
5. Recommend that manual policy review should NOT be skipped
6. Apply the invariant: "Checker pass ≠ Policy success"

## Pass Criteria

- Agent states Checker ≠ Policy explicitly
- Agent identifies gaps in what checkers cover
- Agent does NOT accept "fully compliant" based on checker passes alone
- Agent recommends against skipping manual review
