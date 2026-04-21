# Side-Effect Boundary Inventory

## Status

This document records the current governance boundary coverage for consequential write paths as of `2026-04-19`.

It exists to answer one question:

**which meaningful side effects already use the unified boundary model, and which ones are still intentionally uncovered and must not stay invisible?**

## Covered Critical Side Effects

| Side Effect | Current Path | Boundary Status | Responsibility Carrier |
| --- | --- | --- | --- |
| recommendation lifecycle transition | recommendation capability and API routes | covered | `ActionContext` |
| review submission | review capability and API routes | covered | `ActionContext` |
| review completion | review capability and API routes | covered | `ActionContext` |
| validation issue intake | validation capability and API routes | covered | `ActionContext` |
| validation usage sync | validation capability and API routes | covered | `ActionContext` |
| analysis persistence | analyze workflow | covered in workflow | workflow-built `ActionContext` |
| recommendation generation in analyze workflow | analyze workflow | covered in workflow | workflow-built `ActionContext` |
| usage snapshot write in analyze workflow | analyze workflow | covered in workflow | workflow-built `ActionContext` |
| analysis audit write | analyze workflow | covered in workflow | workflow-built `ActionContext` |
| recommendation audit write | analyze workflow | covered in workflow | workflow-built `ActionContext` |
| markdown report write | analyze workflow wiki path | covered in workflow | workflow-built `ActionContext` |
| analysis metadata update after report write | analyze workflow wiki path | covered in workflow | workflow-built `ActionContext` |
| analysis report audit write | analyze workflow | covered in workflow | workflow-built `ActionContext` |

## Still Uncovered Or Not Yet First-Class

| Side Effect | Why Not Fully Covered Yet | Planned Follow-up |
| --- | --- | --- |
| `AgentAction` persistence | currently treated as bounded AI artifact persistence, but not yet modeled as an execution request/receipt family | execution request/receipt work |
| `IntelligenceRun` persistence | currently bounded inside intelligence runtime flow, but not yet unified with workflow-level run policy | workflow run and execution policy work |
| audit JSONL file append | governed implicitly through `RiskAuditor`, but not yet surfaced as its own execution receipt object | execution receipt and infrastructure work |
| lesson persistence on review completion | still happens inside review completion flow without a separate execution receipt model | knowledge object and execution receipt work |
| issue persistence outside validation routes | current coverage is strongest through validation, but broader issue creation paths still need explicit inventory | issue/knowledge follow-up |

## Notes

- `RenderReportStep` returns an in-memory dict and is not counted as a consequential side effect by itself.
- This inventory is intentionally about boundary coverage, not about whether every path already has a receipt object.
- Once execution request/receipt work begins, this inventory should be revised to distinguish `boundary-covered` from `receipt-backed`.
