# Coverage Review Routing

> **GENERATED VIEW — DO NOT EDIT**
> Owner ≠ Reviewer. Reviewer ≠ Approver. Routing ≠ Authorization.

Total coverage objects: 2108
Ownerless: 0

## Status → Owner → Reviewer → Approver

| Status | Owner Source | Reviewer | Approver | Review Required |
|---|---|---|---|---|
| governed | document-registry.jsonl (owner field) | registry owner or delegate | authority-gate reviewer | no |
| generated | generator script + source_refs owner | generator owner | governance-core maintainer | no |
| excluded | governed-exclusions.json (owner field) | exclusion owner | governance-core maintainer | yes |
| debt_parked | debt ledger (owner field) | debt owner + governance review | governance-core maintainer if  | yes |
| fixture | owning_test / checker CHECKER.md owner | owning test maintainer | checker owner if fixture affec | no |
| vendored | upstream source attribution | governance reviewer for bounda | governance-core maintainer | yes |
| external | external source reference | governance reviewer for stalen | governance-core maintainer | no |
| legacy | legacy boundary declaration | governance reviewer for routin | governance-core maintainer | yes |
| temporary | creator or expiry declaration | creator review at expiry | governance-core maintainer if  | yes |
| blocked | none — must be resolved immediately | governance-core maintainer | governance-core maintainer | yes |

---
```text
Full Closure: NOT CLAIMED.
```
