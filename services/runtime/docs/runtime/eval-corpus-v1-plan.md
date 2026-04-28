# Eval Corpus v1 Plan

Status: **PLAN**
Date: 2026-04-28
Phase: 3.1
Tags: `eval`, `corpus`, `dogfood`, `regression`

## 1. Purpose

Convert Ordivon's existing dogfood scripts into a standardized eval corpus.
Every change to governance policy, RiskEngine, or Pack rules must be validated
against this corpus to detect behavioral regressions.

## 2. Why Dogfood Must Become Eval Corpus

Current dogfood scripts (`scripts/run_cross_pack_dogfood.py`, etc.) are:

- **Ad-hoc**: written per wave, not maintained as assets
- **Inline**: expected decisions are embedded in code, not data
- **Unversioned**: no way to track "this case used to pass, now it fails"
- **Unstructured**: output is human-readable, not machine-parseable

Eval corpus fixes all four: data-driven, version-controlled, machine-parseable,
regression-aware.

## 3. Finance Eval Cases (10)

Extracted from `scripts/run_cross_pack_dogfood.py`:

```
F01  valid conservative plan                    → execute
F02  missing thesis                             → reject
F03  missing stop_loss                          → reject
F04  revenge_trade                              → escalate
F05  chasing                                    → escalate
F06  max_loss > 2× risk_unit                    → reject
F07  position > 10× risk_unit                   → reject
F08  low-quality thesis                         → reject
F09  valid conservative plan                    → execute
F10  stressed emotional state                   → escalate
```

## 4. Coding Eval Cases (10)

```
C01  test fix + plan                            → execute
C02  doc change + plan                          → execute
C03  missing task_description                   → reject
C04  missing file_paths                         → reject
C05  forbidden .env                             → reject
C06  forbidden uv.lock                          → reject
C07  forbidden migration runner                 → reject
C08  high impact                                → escalate
C09  missing test_plan                          → escalate
C10  multi-file + plan                          → execute
```

## 5. Cross-Pack Eval Cases (future)

Cases that verify Core Pack-agnosticism:

```
XP01  Same RiskEngine validates Finance + Coding  → both execute
XP02  Finance policy does not affect Coding        → independence
XP03  Coding policy does not affect Finance        → independence
XP04  Severity protocol works for both             → protocol integrity
```

## 6. Runtime Evidence Eval Cases (future)

Cases that verify the evidence checker and DB audit:

```
RE01  Valid evidence chain passes audit
RE02  Broken receipt reference detected
RE03  Broken outcome_ref detected
RE04  CandidateRule without source_refs detected
RE05  Audit is read-only
```

## 7. Case Schema Proposal

Each eval case is a JSON object:

```json
{
  "case_id": "F01",
  "pack": "finance",
  "description": "Valid conservative plan should execute",
  "input": {
    "pack_id": "finance",
    "intake_type": "trading_decision",
    "payload": {
      "symbol": "BTCUSDT",
      "timeframe": "1h",
      "thesis": "BTC breaking above resistance; invalidated below 200 EMA.",
      "stop_loss": "2%",
      "max_loss_usdt": 200,
      "position_size_usdt": 1000,
      "risk_unit_usdt": 200,
      "emotional_state": "calm",
      "confidence": 0.7
    }
  },
  "expected": {
    "decision": "execute",
    "reason_patterns": ["Passed all governance gates"]
  },
  "forbidden_side_effects": [
    "no ExecutionRequest created",
    "no ExecutionReceipt created",
    "no file writes",
    "no shell/MCP/IDE calls"
  ],
  "source_refs": ["cross-pack-dogfood-wave-f"]
}
```

## 8. Runner Plan

`evals/run_evals.py`:

```
1. Load all case files from evals/finance_cases.json, evals/coding_cases.json
2. For each case:
   a. Build DecisionIntake from input
   b. Run RiskEngine.validate_intake with appropriate pack_policy
   c. Compare actual.decision vs expected.decision
   d. Check reason_patterns against actual.reasons
   e. Record pass/fail
3. Output summary:
   - Total cases, passed, failed
   - Per-pack breakdown
   - Failed case details
4. Exit 0 if all pass, 1 if any fail
```

## 9. Regression Policy

- Eval corpus is version-controlled in `evals/`
- Adding a case requires a PR with rationale
- Modifying a case's expected decision requires explicit review
- CI runs evals on every push to main
- A regression (previously-passing case now fails) blocks merge

## 10. CI Integration Plan

```
GitHub Actions job: eval-corpus
  1. uv sync --extra dev
  2. uv run python evals/run_evals.py
  3. Output: JSON evidence report
  4. Fail job if any case fails
```

## 11. Limitations

- 20 cases is a minimum baseline — real systems need 100+
- Cases only cover classification, not execution chain
- No adversarial cases (deliberately tricky inputs)
- No cross-Pack interaction cases yet
- No runtime evidence eval cases yet
- No performance regression tracking

## 12. Next Steps

1. Create `evals/` directory structure
2. Extract cases from `scripts/run_cross_pack_dogfood.py` into JSON files
3. Write `evals/run_evals.py` runner
4. Integrate into CI
5. Grow corpus from real usage (Phase 3.2+)
