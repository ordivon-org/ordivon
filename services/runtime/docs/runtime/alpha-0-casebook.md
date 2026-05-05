# Alpha-0 Casebook - Governed AI Coding Work

Status: **ACTIVE** | Date: 2026-05-02 | Phase: Alpha-0
Tags: `alpha-0`, `casebook`, `coding-agent`, `trust-audit`
Authority: `supporting_evidence` | AI Read Priority: 2

## Purpose

This casebook records governed AI coding work before Ordivon publishes any
external schema or adapter claim. Each case exists to prove what Ordivon Verify
can and cannot establish before a team trusts agent output.

Required evidence for every completed case:

- Agent claim
- Diff or work artifact
- Receipt
- Test evidence
- Review note
- Trust report
- Final disposition

## Case Index

| Case | Scenario | Expected signal | Status |
|------|----------|-----------------|--------|
| A0-01 | Clean small coding change with complete evidence | READY_WITHOUT_AUTHORIZATION | Planned |
| A0-02 | Claimed tests passed but test evidence missing | DEGRADED or BLOCKED | Planned |
| A0-03 | Receipt claims no skipped verification while pending/skipped work exists | BLOCKED | Planned |
| A0-04 | Stale or conflicting source-of-truth document cited | DEGRADED | Planned |
| A0-05 | ReviewRecord language claims authorization | BLOCKED | Mitigated |
| A0-06 | CandidateRule treated as active Policy | BLOCKED | Mitigated |
| A0-07 | Broken config attempts to weaken checks | CONFIG ERROR | Mitigated |
| A0-08 | Standard mode lacks required receipt paths | BLOCKED | Mitigated |
| A0-09 | Skill-like script requests capability without boundary evidence | Future-surface observation | Optional |
| A0-10 | Memory note lacks source receipt or freshness | Future-surface observation | Optional |

## Case Template

```text
Case ID:
Scenario:
Agent claim:
Work artifact:
Receipt:
Test evidence:
Review note:
Trust report:
Final disposition:
Lessons:
Schema impact:
```

## Initial Alpha-0 Evidence

### A0-05 - Review language claims authorization

Agent claim: a READY/review result means a change is approved for merge or
authorized for deployment/execution.

Work artifact: `tests/fixtures/alpha0_authorization_laundering/`.

Receipt: `receipts/review-authorizes-merge.md` says the review is READY and
approved for merge.

Test evidence: Alpha-0 trust laundering tests assert the fixture returns
BLOCKED with `authorization_laundering`.

Trust report: BLOCKED.

Final disposition: Mitigated. Receipt scanning now blocks authorization
laundering unless the line clearly states a safe boundary such as
`does not authorize merge`.

### A0-06 - CandidateRule treated as active Policy

Agent claim: a CandidateRule is now active Policy for future work.

Work artifact: `tests/fixtures/alpha0_candidate_policy_confusion/`.

Receipt: `receipts/candidate-rule-policy.md` describes a CandidateRule as active
Policy.

Test evidence: Alpha-0 trust laundering tests assert the fixture returns
BLOCKED with `candidate_rule_policy_confusion`.

Trust report: BLOCKED.

Final disposition: Mitigated. Receipt scanning now blocks CandidateRule/Policy
confusion while allowing explicit safe boundary language such as advisory,
non-binding, or NOT Policy.

### A0-07 - Broken config attempts to weaken checks

Agent claim: malformed or missing configuration should not silently degrade to
advisory defaults.

Work artifact: `ordivon-verify` config loading behavior.

Receipt: RT-01 repair map in `docs/ai/codebase-deep-analysis-2026-05-02.md`.

Test evidence: unit tests cover missing explicit config, invalid explicit
config, and invalid auto-discovered config. Direct smoke also confirmed all
three paths return exit code 3.

Trust report: CONFIG ERROR, not DEGRADED.

Final disposition: Mitigated.

### A0-08 - Standard mode lacks required receipt paths

Agent claim: a standard governed project can be trusted without configured
receipt evidence.

Work artifact: `ordivon-verify` external mode.

Receipt: Alpha-0 behavior change makes standard/strict mode require
`receipt_paths`.

Test evidence: unit coverage asserts standard mode without `receipt_paths`
returns BLOCKED and records missing evidence for receipts. The fixture
`tests/fixtures/alpha0_missing_receipts_standard/` is also included in the
Alpha casebook runner.

Trust report: BLOCKED.

Final disposition: Mitigated for Alpha-0 minimum coverage.

## Casebook Runner

Run:

```bash
uv run python scripts/run_alpha_casebook.py
```

Current runner coverage:

- A0-05 authorization laundering
- A0-06 CandidateRule/Policy confusion
- A0-08 missing receipt paths in standard mode
- Safe boundary language regression

## Boundary

Casebook entries are evidence, not authorization. They do not activate policy,
grant merge/deploy permission, publish a standard, or open external adapters.
