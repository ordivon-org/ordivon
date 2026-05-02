# HAP-3 TaskPlan + ReviewRecord Strengthening v0

> **v0 / prototype / non-executing.** TaskPlan is not execution permission.
> ReviewRecord is not automatic approval. **Phase:** HAP-3 | **Risk:** AP-R0

## 1. Purpose

HAP-3 strengthens HAP-1/HAP-2 by making HarnessTaskPlan and HarnessReviewRecord
first-class local prototype objects with JSON schemas, fixtures, and boundary
validation.

## 2. Why TaskPlan and ReviewRecord Were Strengthened

HAP-2 showed that HarnessTaskPlan and HarnessReviewRecord were exercised only
through plan_id references and scenario summaries, not standalone schema
objects. This made ADP-2's detector rely exclusively on free-text heuristics.

HAP-3 addresses this by defining structured, detector-readable representations
for both objects.

## 3. Object Distinction

| Object | Timing | Purpose | Authorization? |
|--------|--------|---------|---------------|
| TaskRequest | Pre-action | What is being asked | ❌ Intent only |
| **TaskPlan** | **Pre-action** | **How it will be done, boundaries, risk** | **❌ Plan only** |
| ExecutionReceipt | Post-action | What was done | ❌ Evidence only |
| EvidenceBundle | Post-action | Proof of execution | ❌ Evidence only |
| ResultSummary | Post-action | Status assessment | ❌ Evidence only |
| **ReviewRecord** | **Post-action** | **Epistemic validation** | **❌ Review only** |

## 4. Schema Inventory

| Schema | Path | Required Fields | Validation Rules |
|--------|------|----------------|-----------------|
| HarnessTaskPlan | `hap-task-plan.schema.json` | 11 | C4→BLOCKED, C5→NO_GO, credential_access_planned=false, plan≠execution |
| HarnessReviewRecord | `hap-review-record.schema.json` | 10 | COMMENT_ONLY≠approval, detector≠authorization, CR non-binding |

## 5. Fixture Inventory

**TaskPlan (6):**
- C0 docs-only plan, C2 protected-path, C3 shell-blocked, C4 blocked, C5 NO-GO, unsafe plan-claims-execution

**ReviewRecord (6):**
- Comment-only, detector PASS, evidence insufficient, request changes, CandidateRule non-binding, unsafe comment/detector approval

## 6. Test Results

- HAP-3 schema tests: 27/27 PASS
- Existing HAP tests: 43/43 PASS (fixed 9 pre-existing task request authority statements)
- Total: 70 HAP tests passing
- No can_access_secrets in any fixture

## 7. Boundary Confirmation

| Boundary | Confirmed |
|----------|-----------|
| TaskPlan is not execution permission | ✅ |
| ReviewRecord is not automatic approval | ✅ |
| COMMENT_ONLY is not approval | ✅ |
| Detector PASS is not authorization | ✅ |
| Evidence sufficiency is not approval | ✅ |
| CandidateRule non-binding | ✅ |
| C4 defaults to BLOCKED | ✅ |
| C5 defaults to NO-GO | ✅ |
| No credentials accessed | ✅ |

## 8. Next Phase

**ADP-3** (structure-aware detection with TaskPlan/ReviewRecord parsing,
cross-line context, and CI integration readiness).

*Phase: HAP-3 | Object strengthening only. No execution.*
