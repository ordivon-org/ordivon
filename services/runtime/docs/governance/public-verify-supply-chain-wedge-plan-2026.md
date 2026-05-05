# Public Verify Supply-Chain Wedge Plan 2026

Status: **CURRENT** | Date: 2026-05-05 | Phase: GWOS-2026-P5
Tags: `ordivon-verify`, `public-wedge`, `supply-chain`, `package`, `read-only`
Authority: `source_of_truth` | AI Read Priority: 2

## Purpose

This plan defines what must be true before `ordivon-verify` can be considered
ready for a public dry-run wedge. It is package evidence planning only. It is
not a publication decision.

## Position

External entry:

```bash
ordivon-verify check .
```

Meaning:

```text
verify claims, receipts, missing evidence, and trust boundaries
```

Non-meaning:

```text
run agent / replace CI / approve merge / approve release / certify compliance
```

## Evidence Tracks

### Package Boundary

Required checks:

- no private repo paths.
- no finance execution imports and no broker integration imports.
- no token handling.
- no action authorization statement.
- no public-standard or production-readiness overclaim.

### Install Smoke

Three layers:

1. source import.
2. wheel install.
3. external fixture trust audit.

Offline fallback can inspect separated package context, but it must label the
result as fallback evidence, not full install proof.

### Supply-Chain Evidence

Use SLSA/OpenSSF-inspired language only:

- provenance-like build evidence.
- dependency audit evidence.
- source/package separation evidence.
- artifact membership evidence.

Forbidden language:

- SLSA level claim.
- compliance claim.
- certification claim.
- endorsement claim.
- partnership claim.
- equivalence claim.
- release approval claim.

## Public Docs Dry-Run

Public docs must be rejected or revised if they imply:

- production readiness.
- platform launch.
- standard publication.
- security certification.
- automatic merge/deploy/release permission.
- adapter runtime availability.

## Exit Criteria

- package smoke passes without private leakage.
- public wording stays bounded and honest.
- Alpha casebook has enough evidence to explain the wedge.
- no schema is presented as public standard.
- no publication action is authorized by this plan or any receipt.

## Boundary

This plan is a supply-chain and product-boundary plan. It does not publish
anything, upload packages, create releases, certify security, or authorize
external action.
