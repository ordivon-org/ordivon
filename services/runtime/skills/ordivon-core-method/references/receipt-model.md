# Receipt Model (R1–R5)

## Receipt Types

| Type | Name | Use Case |
|------|------|----------|
| R1 | Analysis Receipt | Research, audit, claim evaluation |
| R2 | Engineering Receipt | Code changes, bug fixes, features |
| R3 | External Action | MCP/external system actions |
| R4 | Governance Receipt | State, policy, debt, gate changes |
| R5 | Incident Receipt | Failures, outages, security events |

## Required Fields

All receipts must include:

```
receipt_type (R1–R5)
scope — what was intended
actions_taken — what was done
evidence — traces, test outputs, diffs, command outputs
verification_result — what checks passed/failed
remaining_debt — what is NOT resolved
status — PASS / DEGRADED / BLOCKED
draft: true — every receipt is a draft until reviewed
```

## Hard Rules

- Receipt ≠ Resolution. A receipt records; it does not prove.
- Every receipt must declare remaining debt.
- Self-sealing is forbidden. All receipts carry `draft: true`.
- Status upgrades require external gate (human review, checker, or policy).
- Evidence fields must cite specific traces — not contain claims.
- A receipt with "no remaining debt" and no evidence is a red flag.
