# VD-005 Post-Mortem: The Known/Unknown Quadrant Analysis

> This document preserves the multi-domain analysis of VD-005 — the governance
> coverage gap discovered during PV-N2H. It is a "case law" document: a record
> of how Ordivon diagnosed a meta-governance failure and what invariants emerged.

## The Quadrant

VD-005 was not a single residual cleanup. It was a discovery failure across four
knowledge quadrants:

| Quadrant | Ordivon Example | Pre-VD-005 State | Issue |
|----------|----------------|-----------------|-------|
| **Known Known** | 31 registered docs, 4 closed debts, 11 gates, receipt checker | Strong governance | Local PASS misread as global health |
| **Known Unknown** | config/.env/package files excluded from DG scope | Known exclusion | Underestimated identity-bearing risk |
| **Unknown Known** | Human knowledge that PFIOS/AegisOS are historical | Implicit, not machine-encoded | New AI couldn't distinguish history from truth |
| **Unknown Unknown** | Unregistered AegisOS docs, identity context pollution | Undetected | DG had no object discovery mechanism |

## The Real Failure

```
Known Known PASS
    ↓  masked
Unknown Unknown coverage gap

Known Unknown out-of-scope
    ↓  misclassified
Identity-bearing surfaces ungoverned

Unknown Known implicit history
    ↓  not encoded
New AI could read AegisOS as current
```

The checker said PASS but only validated objects it knew about. A green light
on a partial view is more dangerous than no light at all — it creates false
confidence.

## Four New Governance Invariants

### 1. PASS is scoped

A PASS result only applies to its declared coverage universe. A checker that
does not declare what it checked and what it didn't check is producing an
unverifiable signal.

### 2. Registry must be reconciled with reality

A registry is not complete until it is checked against discoverable repository
reality. Known registered items ≠ all relevant items.

### 3. Out-of-scope must be explicit and justified

Silent omission is not governance. Every exclusion must carry a reason,
classification, owner, and review date.

### 4. Identity-bearing surfaces are governance-relevant

Files that carry project identity (pyproject.toml, package.json, README.md,
apps/*/package.json) are governance-relevant even though they are not documents.

## The Maturity Model

Governance maturity is measured by the ability to migrate across quadrants:

```
Unknown Unknown  →  Known Unknown  →  Known Known
                    (discovery)       (remediation)

Unknown Known    →  Known Known
                    (explicitation)
```

PV-N2H executed this migration:
- **Discovery:** `check_completeness()` found 142 unregistered/excluded items
- **Reclassification:** Identity-bearing surfaces moved from Known Unknown (excluded config) to Known Known (governed surfaces)
- **Explicitation:** PFIOS/AegisOS/Ordivon identity relationships encoded in README, AGENTS, docs/ai

## Coverage Precedes Confidence

The core lesson: a governance check is only as trustworthy as its object
discovery model. You cannot trust a PASS until you know what universe it
covers.

---

*Created: 2026-05-01, post PV-N2H closure*
*Reference: VD-2026-05-01-005 (CLOSED)*
