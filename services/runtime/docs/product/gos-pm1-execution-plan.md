# GOS-PM-1: Auto-Maintained Path Map — Execution Plan

> **This is an execution plan, not a receipt.** No implementation artifacts
> have been created. Schemas, scripts, checkers, tests, and CI jobs are
> specified but not yet built.

**Authority**: `proposal`
**Status**: `ready_for_execution`
**Phase**: `GOS-Hardening → PM-1`
**Owner**: `ordivon-core-maintainer`
**Freshness**: 2026-05-11
**Parent**: `docs/product/gos-n1a-path-map-design.md` (design), `docs/product/ordivon-gos-hardening-roadmap.md` (roadmap)
**AI Read Priority**: 1

---

## Primary Goal

Every git-tracked file must fall into one of five states:

```
1. Governed Node       ← registry entry + doc_type + owner + authority
2. Generated View      ← marked generated, source_refs declared
3. Explicit Exclusion  ← owner + reason + review_date + removal_condition
4. A4 Debt-Parked      ← known gap, formal debt, review trigger
5. BLOCKED             ← protected path, no route, must remediate
```

NOT allowed: file exists but no route. Silent unclassified existence.

---

## New Artifacts Required

```
docs/governance/schemas/path-map-rules.json
docs/governance/schemas/path-map-node.schema.json
docs/governance/schemas/path-map-edge.schema.json

docs/governance/generated/path-map.json
docs/governance/generated/_path-map.md
docs/governance/generated/path-map.dot

scripts/update-path-map.py
scripts/verify-path-map.py
scripts/explain-path-node.py

checkers/path-map/CHECKER.md
checkers/path-map/run.py

tests/unit/governance/test_path_map.py
tests/fixtures/path_map/{valid, invalid_*}
```

---

## Source Model

Path map is compiled from these sources. Path map itself is NOT a source.

```
S1. git ls-files
S2. document-registry.jsonl
S3. document-types.json
S4. governed-exclusions.json
S5. protected-paths-config.json
S6. checkers/*/CHECKER.md + run.py
S7. .github/workflows/*.yml
S8. lesson-ledger.jsonl
S9. dependency-audit-debts.jsonl
S10. candidate-rule-drafts.jsonl
```

---

## Classification Algorithm

Deterministic. AI may propose routes but may not classify authoritatively.

```
For each git-tracked file:

1. Explicit exclusion → validate owner/reason/review_date → ExplicitExclusion
2. Generated file → validate marker + source_refs → GeneratedView
3. In registry → validate doc_type + owner + authority → GovernedNode
4. Checker → validate CHECKER.md + run.py → CheckerNode
5. CI workflow → classify → CIGateNode
6. Ledger → classify → KnowledgeAsset
7. Match path-map rule → RoutedCandidate (BLOCKED if protected, no registry)
8. No match + protected → BLOCKED
9. No match + non-protected → A4 debt or exclusion required
```

Priority: registry > exclusion > generated > checker > CI > rule > fallback.

---

## Acceptance Criteria

ALL 12 must be met before claiming `VERIFIED_AS_GENERATED_VIEW`:

```
1.  path-map-rules.json exists and validates.
2.  update-path-map.py generates json/md/dot.
3.  verify-path-map.py detects manual drift.
4.  checkers/path-map exists with CHECKER.md + run.py.
5.  CI includes verify-path-map job.
6.  Protected docs path cannot contain unclassified file.
7.  Explicit exclusions require owner/reason/review_date/removal_condition.
8.  Generated views cannot be source_of_truth.
9.  At least 5 negative fixtures pass.
10. ordivon-verify all returns READY.
11. Receipt includes raw command output.
12. Full closure is NOT CLAIMED.
```

---

## Allowed Final Status

```
Auto Path Map:           VERIFIED_AS_GENERATED_VIEW or DEGRADED
Governance Coverage:     READY_WITH_EXPLICIT_EXCLUSIONS or PARTIAL_WITH_DEBT
Full Closure:            NOT CLAIMED
External Governance:     NOT CLAIMED
AI Classification:       NOT AUTHORIZED (propose only)
```

---

```text
READY means selected checks passed; it does not authorize execution.
```
