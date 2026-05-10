# GOS-PM-3: Authority Taxonomy Redesign — Plan

> **This is a plan, not a receipt.** No implementation artifacts beyond
> the taxonomy schema exist. The plan is derived from PM-2S RPR-4 findings
> and 7 external reference systems.

**Authority**: `proposal`
**Status**: `ready_for_execution`
**Phase**: `GOS-Hardening → PM-3`
**Owner**: `ordivon-core-maintainer`
**Freshness**: 2026-05-11
**Parent**: GOS-PM-2S (RPR-4 → A3 disposition)
**AI Read Priority**: 1

---

## Problem

```
PM-2S found: 2 BLOCKING RPR-4 findings.
Root cause: source_of_truth used for documentation truth, implementation
            source, and schema definition — three different authority domains
            collapsed into one label.

Example:
  checker_registry.py         authority=source_of_truth → route=source-code
  pgi-evidence-record.schema  authority=source_of_truth → route=source-code
  methodology-core.md         authority=current_status   → route=governance-core

All three use "source_of_truth" but mean fundamentally different things.
```

---

## Design Input (7 External Systems)

| System | Principle | Ordivon Application |
|--------|-----------|---------------------|
| Kubernetes | Controller ≠ RBAC, desired state reconciliation ≠ authorization | Authority declaration ≠ execution |
| Terraform | Plan ≠ Apply | RPR finding ≠ fix; disposition candidate ≠ authorized mutation |
| Backstage | Catalog metadata taxonomy must be organization-defined | Authority domain must be schema-constrained, not natural language |
| GitHub | Path ownership ≠ merge enforcement | Owner ≠ approver; gate pass ≠ full closure |
| OPA | Admission before mutation | Authority change must pass admission check before state change |
| SLSA/in-toto | Provenance binds subject + predicate + materials | Authority claim must bind domain + role + scope + source_ref |
| Google SRE | Error budget, not absolute perfection | Mismatch severity is risk-based; not all findings are BLOCKING |

---

## Solution: Domain-Aware Authority Taxonomy

Replace the overloaded flat `authority` field:

```
authority_domain  (documentation / implementation / schema / generated / evidence / policy / runtime / external)
authority_role    (doc_source_of_truth / implementation_source / schema_source / ...)
authority_scope   (specific governed object identifier)
```

Legacy `authority` field retained as migration bridge. New checkers validate domain-role-route compatibility.

---

## 8 Domains × 27 Roles

See `docs/governance/schemas/authority-taxonomy.json`.

Key constraints:
- Generated views cannot claim any source role
- Implementation source only for code routes
- Schema source only for schema/code routes
- Doc source of truth only for governance/doc routes
- Active policy only for governance core route

---

## Required Artifacts

```
docs/governance/schemas/authority-taxonomy.json          (CREATED — plan only)
docs/governance/schemas/authority-taxonomy.schema.json   (pending)
docs/governance/generated/_authority-taxonomy.md         (pending)
docs/governance/generated/authority-migration-plan.json  (pending)
scripts/update-authority-taxonomy.py                     (pending)
scripts/verify-authority-taxonomy.py                     (pending)
checkers/authority-taxonomy/                             (pending)
tests/test_authority_taxonomy.py                         (pending)
```

---

## Target Disposition for 2 RPR-4 Findings

```
checker_registry.py:
  Before: authority=source_of_truth, route=source-code → BLOCKING
  After:  authority_domain=implementation, authority_role=implementation_source
  → RPR-4 MITIGATED

pgi-evidence-record.schema.json:
  Before: authority=source_of_truth, route=source-code → BLOCKING
  After:  authority_domain=schema, authority_role=schema_source
  → RPR-4 MITIGATED
```

Not downgraded. Reclassified into appropriate authority domains.

---

## Status

```
Authority Taxonomy Schema:   PROPOSED
Implementation:              NOT STARTED
RPR-4:                       OPEN (A3)
Full Closure:                NOT CLAIMED
```

---

```text
READY means selected checks passed; it does not authorize execution.
```
