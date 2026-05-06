# Ordivon Newcomer Red-Team Audit — 2026-05-06

Status: **CLOSED** | Date: 2026-05-06 | Phase: Newcomer-Redteam
Tags: `red-team`, `newcomer`, `verify`, `read-only`, `trust-report`
Authority: `supporting_evidence` | AI Read Priority: 2

## Purpose

This audit tested Ordivon from two viewpoints:

1. A new user who starts at `README.md` and runs the documented Verify command.
2. A red-team reviewer looking for trust laundering, read-only violations,
   stale onboarding state, and misleading report surfaces.

This receipt is evidence only. It does not authorize merge, release,
deployment, publication, trading, policy activation, checker promotion, or any
external action.

## Newcomer Path Tested

A first-time user is likely to do this:

```bash
cat README.md
uv run python scripts/ordivon_verify.py check .
```

Expected newcomer experience:

- command exits `0`.
- trust signal is `READY_WITHOUT_AUTHORIZATION`.
- report states READY is not authorization.
- no tracked repository state changes.
- public surfaces show meaningful coverage instead of `NOT_APPLICABLE`.

## Findings

### RT-NC-01 — Verify Read-Only Contract Was Violated

Severity: **High**

Before the fix, `uv run python scripts/ordivon_verify.py check .` ran the full
native checker set, including state-updating checkers:

- `entropy_telemetry`
- `lesson_extraction`
- `policy_shadow`

Observed effect:

- `docs/governance/entropy-telemetry.jsonl` changed.
- `docs/governance/shadow-evaluation-log.jsonl` changed.

Why it matters:

The README and package docstrings describe Ordivon Verify as local and
read-only. A newcomer should not dirty the worktree by running the first
documented trust-audit command.

Blue-team fix:

- `src/ordivon_verify/runner.py` now exposes `_get_readonly_gate_ids()`.
- `src/ordivon_verify/cli.py` uses that read-only checker set for `all` and
  `check`.
- State-updating checkers remain available through the internal full baseline
  path, not through the public Verify trust-audit entry.
- Unit tests assert `all/check` skip side-effect checkers.

### RT-NC-02 — Trust Surfaces Were Misleadingly `NOT_APPLICABLE`

Severity: **Medium-High**

Before the fix, native Verify ran many checks successfully but reported:

```text
claims: NOT_APPLICABLE
receipts: NOT_APPLICABLE
tests: NOT_APPLICABLE
diff: NOT_APPLICABLE
debt: NOT_APPLICABLE
docs: NOT_APPLICABLE
gates: NOT_APPLICABLE
review: NOT_APPLICABLE
```

Root cause:

`src/ordivon_verify/report.py` only mapped legacy external check IDs
(`receipts`, `debt`, `gates`, `docs`) to public trust surfaces. Native checker
IDs such as `receipt_integrity`, `verification_debt`, `gate_manifest`, and
`document_registry` were not mapped.

Why it matters:

A newcomer could wrongly conclude Ordivon is not checking its own stated
surfaces, despite the checker ecosystem passing.

Blue-team fix:

- Added native checker ID mappings for receipts, debt, gates, docs, current
  truth, agent-native evidence, OEP, EGB-3, ownership, and external sources.
- Human and JSON Verify reports now show the public surfaces as `PASS` when
  covered.
- Unit tests assert native checker IDs map to trust surfaces.

### RT-NC-03 — Onboarding State Had Stale Newcomer Guidance

Severity: **Medium**

Observed drift:

- `README.md` said registered debt was `0 open`; current metrics report `3`.
- AI onboarding docs presented `scripts/run_baseline.py` full baseline without
  warning that it writes telemetry/shadow ledgers.
- `current-phase-boundaries.md` still referenced the old
  `scripts/run_verification_baseline.py --profile pr-fast` command.

Blue-team fix:

- README now reports `3 open diagnostic items`.
- AI onboarding now distinguishes:
  - `scripts/run_baseline.py --read-only` for no JSONL writes.
  - `scripts/run_baseline.py` for full baseline with telemetry/shadow writes.
  - `scripts/ordivon_verify.py check .` for product trust audit.
- The phase-boundary command now points to canonical
  `scripts/run_baseline.py --pr-fast`.

## Newcomer Workflow After Fix

Recommended first path:

```bash
cat README.md
uv run python scripts/ordivon_verify.py check .
uv run python scripts/run_baseline.py --read-only
uv run python scripts/run_alpha_casebook.py
```

Interpretation:

- `ordivon_verify.py check .` is the product trust-audit entry.
- `run_baseline.py --read-only` is the internal governance baseline that avoids
  state writes.
- `run_alpha_casebook.py` shows red-team trust laundering behavior.
- Full `run_baseline.py` is useful for maintainers but writes diagnostic
  telemetry/shadow ledgers by design.

## Verification At Closure

Observed at closure:

- `uv run python scripts/ordivon_verify.py check .`: READY, no tracked state
  writes, public surfaces PASS.
- `uv run python -m ordivon_verify all --json`: READY, 35 read-only checks.
- `uv run python -m ordivon_verify check . --json`: READY, 35 read-only checks.
- `uv run python scripts/run_baseline.py --read-only`: READY, 26/26 hard gates.
- `uv run python scripts/run_alpha_casebook.py`: 13/13 expected outcomes.
- `uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_external_fixture.py tests/unit/product/test_ordivon_verify_cli.py -q`:
  86 passed.

## Residual Risks

- Historical PV quickstart and dogfood docs still mention `all`; this remains
  acceptable as historical evidence, but current docs should prefer
  `check .` for new users.
- Full baseline intentionally writes telemetry/shadow ledgers. New users must
  not treat it as the read-only product entry.
- JSON report includes both public trust surfaces and checker-specific
  surfaces. This is useful for debugging but can be simplified in a future UX
  pass.

READY remains evidence sufficiency only. It is not action authorization.
