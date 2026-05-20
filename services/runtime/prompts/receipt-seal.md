# Receipt Seal Prompt

Use this prompt when asking an AI agent to generate a closure receipt.

## Task Summary

[Describe what was done]

## Receipt Generation

Generate an R4 Governance Receipt with:

- **Receipt Type:** R4 (Governance)
- **Scope:** What was the intended scope?
- **Actions Taken:** What was done? List each action with evidence reference.
- **Evidence:** For each action, cite specific evidence (command output, diff, test result, file path).
- **Verification Result:** What passed? What failed? What was not verified?
- **Remaining Debt:** List every unresolved item with debt_id and severity.
- **Status:** PASS / DEGRADED / BLOCKED
- **Draft: true** — this receipt is a draft until reviewed.

## Hard Rules

- Evidence fields must cite specific traces — not contain claims.
- Remaining debt must never be empty or "None" without justification.
- Status cannot be PASS if verification is missing.
- Receipt does NOT authorize, close debt, or declare final resolution.
