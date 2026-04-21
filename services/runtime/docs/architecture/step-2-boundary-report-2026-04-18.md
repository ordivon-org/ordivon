# Step 2 Boundary Report - 2026-04-18

## Scope

This report closes Step 2 of the current framework plan:

- formalize Domain / State / Governance ownership
- make default boundaries visible in the repo
- reduce future drift by adding import hygiene checks

## What Was Completed

### Ownership rules are now explicit

Boundary decisions are now documented in:

- [boundary-map.md](./boundary-map.md)
- `domains/research/README.md`
- `domains/strategy/README.md`
- `domains/journal/README.md`
- `state/usage/README.md`
- `governance/audit/README.md`
- `governance/risk_engine/README.md`

### Default placement rules were clarified

The repository now has explicit answers for:

- recommendation outcome ownership
- issue ownership
- usage ownership
- governance audit ownership

### Import hygiene protection was added

[tests/unit/test_boundary_import_hygiene.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/tests/unit/test_boundary_import_hygiene.py:1)
now checks that active code does not reintroduce migrated truth modules through old `pfios/*` imports.

## Final Boundary Decisions

### Domain-owned

- `domains/research`: analysis semantics
- `domains/strategy`: recommendations and recommendation outcomes
- `domains/journal`: reviews, lessons, journal-facing issues

### State-owned

- `state/db`: persistence foundation
- `state/usage`: operational usage snapshots

### Governance-owned

- `governance/risk_engine`: permission-to-proceed logic
- `governance/audit`: traceability and audit persistence

## Why These Decisions

### Outcome remains in `domains/strategy`

Outcome is still closest to recommendation meaning:

- did the thesis work
- did the recommendation fail
- did it expire

That is still business semantics, not just low-level system state.

### Issue remains in `domains/journal`

Issue is currently used as a learning and validation artifact:

- workflow breakdown
- validation problem
- review-derived action item

If a future incident-management or approval workflow appears, governance can add a separate incident model without taking over this journal-facing issue object.

### Usage remains in `state`

Usage snapshots answer "what happened operationally?" rather than "what did we mean?".

That makes them a cleaner fit for `state`.

## Validation

Step 2 was validated by:

- existing repository and import tests
- new import hygiene coverage
- successful targeted regression runs on active capabilities and orchestration imports

## Result

The repository now has a stable default answer for the highest-frequency ownership questions.

Step 2 does not make every layer complete, but it significantly reduces ambiguity for future work and makes architectural regressions easier to catch.
