# Checker Ecosystem Audit Round 1

Status: **CLOSED** | Date: 2026-05-05 | Phase: GWOS-2026-P1
Tags: `checker`, `maturity`, `audit`, `read-only`, `egb-3`
Authority: `supporting_evidence` | AI Read Priority: 2

## Purpose

This audit records how the checker ecosystem should be read after EGB-2 and
before any EGB-3 promotion work.

The checker ecosystem is operational, but maturity remains deliberately
conservative. Shadow-first checkers expose evidence gaps; they are not hard
gate promotions.

## Current Shape

Observed at closure:

- checker directories: 36.
- hard checkers: 26.
- escalation checkers: 10.
- pr-fast profile: 12 hard gates.
- EGB-2 shadow checkers: external source registry, OEP governance, ownership
  manifest.

## Crosswalk

| Source | Role |
|---|---|
| `src/ordivon_verify/checker_registry.py` | runtime checker list and product-level grouping. |
| `checkers/*/CHECKER.md` | local checker contract, hardness, profiles, maturity metadata. |
| `docs/governance/checker-maturity-ledger.jsonl` | lifecycle state and promotion evidence. |
| `docs/governance/verification-gate-manifest.json` | baseline gate manifest consumed by baseline runner. |
| `scripts/run_baseline.py` | canonical baseline runner. |
| `scripts/run_verification_baseline.py` | deprecated compatibility symlink, registered to avoid registry drift. |

## Red-Team Risks

| Risk | Current defense | Next action |
|---|---|---|
| Shadow checker treated as hard gate | maturity ledger and CHECKER.md mark EGB-2 as escalation/shadow-first. | EGB-3 should add promotion/no-promotion receipt fields. |
| Deprecated runner treated as canonical | artifact registry now marks `run_verification_baseline.py` deprecated. | Keep AGENTS and AI docs pointing to `run_baseline.py`. |
| Read-only baseline writes state | baseline excludes state-writing surfaces in read-only mode. | Add a future side-effect assertion around tracked file diff. |
| Checker claims coverage but misses registry object | artifact/document registry checks are explicit pre-close gates. | Keep registry drift as P0 in closure receipts. |
| Reviewer and approver roles collapse | EGB-2 ownership checker validates split. | Add EGB-3 red-team fixture for owner/reviewer/approver confusion. |

## Promotion Rule

No checker moves from escalation/shadow to hard because it passed once. Promotion
requires:

```text
fixture coverage -> red-team result -> owner review -> maturity ledger update
                -> baseline dry run -> closure receipt
```

## Boundary

This audit does not promote checkers, activate policy, publish a quality score,
or authorize merge/release/deployment.
