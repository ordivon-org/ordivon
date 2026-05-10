# EGB-3 Operating Governance

Status: **CURRENT** | Date: 2026-05-05 | Phase: EGB-3
Tags: `egb-3`, `oep`, `ownership`, `freeze`, `trust-budget`, `shadow-first`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

EGB-3 turns EGB-2's benchmark-informed backbone into a daily operating model.
It remains shadow-first until promotion evidence exists.

External engineering practices inform the design. They do not create
compliance, certification, endorsement, partnership, equivalence,
public-standard, production-readiness, or action authorization claims.

## Operating Objects

| Object | EGB-3 role |
|---|---|
| OEP | proposal lifecycle for cross-boundary changes. |
| Ownership manifest | path-native reviewer, approver, owner, backup, emeritus, staleness. |
| Freeze protocol | stage state that limits churn after scope closes. |
| Trust budget | diagnostic evidence exposure for a stage. |
| Maturity ledger | promotion evidence for checkers and governance surfaces. |

## OEP Lifecycle

```text
draft -> shadow_tested -> red_teamed -> owner_reviewed -> active_or_closed
```

Rules:

- `draft` can describe intent but cannot claim acceptance.
- `shadow_tested` means fixtures or dry-runs exist; it is not approval.
- `red_teamed` means negative cases exist and have expected signals.
- `owner_reviewed` means named owner review happened.
- `active_or_closed` still does not authorize merge, release, deployment,
  publication, trading, or external action.

## Freeze Warning Gate

EGB-2 recorded freeze state. EGB-3 may warn on state violations:

| State | Allowed work | Warning condition |
|---|---|---|
| `open_scope` | discovery, design, fixtures, scoped implementation | none. |
| `enhancement_freeze` | no new scope; repair, evidence, test, review | new unrelated feature or surface. |
| `verification_freeze` | tests, docs, receipts, registry repair | feature code change without evidence gap. |
| `closure_freeze` | receipt, current-truth, closure verification | scope expansion. |
| `closed` | follow-up stage only | mutation without new OEP/stage. |

Warnings are evidence. They are not hard authorization controls until a future
owner-approved promotion.

## Trust Budget Interpretation

Trust budget counts must be split into:

- current blockers: failures that affect the active stage.
- historical samples: old receipts or fixtures intentionally preserved.
- diagnostic debt: evidence gaps that should feed repair backlog.

Never interpret trust budget as:

- a release score.
- a personal performance score.
- approval to act.
- proof that the project is failed.

## Red-Team Fixtures Required

EGB-3 must add fixtures for:

- reviewer presented as approver.
- owner role missing but approval claimed.
- shadow checker described as hard gate.
- freeze state ignored after closure freeze.
- trust budget spent but expansion continues.

## Boundary

EGB-3 does not promote any EGB-2 checker by default. Promotion requires
red-team evidence, owner review, maturity ledger update, baseline dry run, and
closure receipt.
