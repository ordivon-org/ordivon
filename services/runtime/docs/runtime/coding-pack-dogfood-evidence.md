# Coding Pack Dogfood Evidence

Status: **EVIDENCE**
Date: 2026-04-28
Wave: C2-R
Tags: `dogfood`, `coding-pack`, `governance`, `evidence`, `c2`

## 1. Purpose

Validate that the Coding Pack (`packs/coding/`) governance pipeline —
`CodingDisciplinePolicy` → `RiskEngine.validate_intake()` — correctly
classifies coding decision intakes as `execute`, `reject`, or `escalate`
across 10 representative scenarios.

This is a dogfood run, not a test suite. The difference:
- Tests verify individual gate rules.
- Dogfood verifies the pipeline end-to-end with realistic payloads.

## 2. Scope

- 10 simulated coding decision intakes
- Each run: build a `DecisionIntake` → pass through `CodingDisciplinePolicy` → `RiskEngine.validate_intake()` → record verdict + reasons
- Compare expected verdict against actual verdict

## 3. Non-Goals

This dogfood does NOT:
- Execute real code
- Modify files
- Call shell, MCP, or IDE agents
- Create `ExecutionRequest` or `ExecutionReceipt`
- Generate `CandidateRule` drafts
- Promote any rule to Policy

## 4. 10-Run Result Table

```
Run   Tag                        Expected    Actual      Pass   Key Reason
──────────────────────────────────────────────────────────────────────────────────
R01   test fix + plan            execute     execute     ✅     Passed all governance gates
R02   doc change + plan          execute     execute     ✅     Passed all governance gates
R03   missing task               reject      reject      ✅     Missing required field: task_description
R04   missing files              reject      reject      ✅     Missing required field: file_paths
R05   touch .env                 reject      reject      ✅     Forbidden file path: '.env'
R06   touch uv.lock              reject      reject      ✅     Forbidden file path: 'uv.lock'
R07   touch migration runner     reject      reject      ✅     Forbidden file path: 'state/db/migrations/runner.py'
R08   high impact                escalate    escalate    ✅     estimated_impact='high'
R09   missing test plan          escalate    escalate    ✅     Missing test_plan
R10   multi-file + plan          execute     execute     ✅     Passed all governance gates
```

## 5. Decision Distribution

| Verdict  | Count | Scenarios |
|----------|-------|-----------|
| execute  | 3     | R01, R02, R10 |
| reject   | 5     | R03, R04, R05, R06, R07 |
| escalate | 2     | R08, R09 |
| **Total**  | **10**  | |

```
Execute:  30%  — low/medium impact + valid fields + test_plan
Reject:   50%  — missing fields + forbidden paths
Escalate: 20%  — high impact + missing test_plan
```

## 6. Side-Effect Confirmation

```
✅ Errors:                   0
✅ Real file writes:         0
✅ Shell/MCP/IDE calls:      0
✅ ExecutionRequest created: 0
✅ ExecutionReceipt created: 0
✅ CandidateRule generated:  0
✅ Policy promoted:          0
```

## 7. Key Finding

The Ordivon Governance Core (`RiskEngine.validate_intake`) correctly handles
a non-Finance Pack without modification. The `pack_policy` parameter and
`.severity` protocol (ADR-006) are proven to be domain-agnostic:

- Same `RiskEngine` serves both `FinanceDisciplinePolicy` and `CodingDisciplinePolicy`.
- `governance/` imports zero `packs.coding` modules.
- `packs/coding/` imports zero `governance` internals.
- All reason types use the `.severity` + `.message` protocol.

This confirms that Ordivon's governance architecture supports arbitrary
Pack types through the same Intake → Governance → Receipt pipeline.

## 8. Limitations

- No real code execution — the dogfood only tests classification, not execution.
- Forbidden path list is minimal (9 patterns) — real use would expand it.
- No integration with existing CI tools (ruff, pytest, bandit) — tool_refs exist but are unused.
- No CandidateRule generation from coding decisions — Wave B extraction only applies to `rule_candidate` lessons from Reviews.

## 9. Related Artifacts

| Artifact | Path |
|----------|------|
| Dogfood script | `scripts/h9f_coding_dogfood.py` |
| Coding policy | `packs/coding/policy.py` |
| Coding models | `packs/coding/models.py` |
| Coding tool refs | `packs/coding/tool_refs.py` |
| Policy unit tests | `tests/unit/packs/test_coding_policy.py` (20 tests) |
| Architecture boundary tests | `tests/architecture/test_coding_pack_boundary.py` (3 tests) |
| Governance baseline | `docs/architecture/repo-governance-baseline.md` |

## 10. Next Recommended Wave

Based on this evidence, the next logical step is:

**Wave C3 — Coding Pack API surface**: expose `/api/v1/decisions/intake` with
`pack_id="coding"` so that external tools (CLI, IDE, CI) can submit coding
intents through the same governance pipeline currently used by Finance decisions.

This would require:
- A `DecisionIntake` API route that accepts `pack_id` and routes to the
  correct `pack_policy` (no new endpoint needed — only routing logic).
- Integration tests for coding intakes via the API.
- No governance/risk_engine changes (already generic).
