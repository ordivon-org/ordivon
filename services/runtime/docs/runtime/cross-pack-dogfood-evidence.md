# Cross-Pack Dogfood Evidence

Status: **EVIDENCE**
Date: 2026-04-28
Wave: F
Tags: `dogfood`, `cross-pack`, `governance`, `evidence`

## 1. Purpose

Validate that Ordivon's governance pipeline correctly handles both Finance Pack
and Coding Pack intakes through the same `RiskEngine.validate_intake()` without
modification. This proves Core is Pack-agnostic.

## 2. Scope

- 10 Finance decision intakes through `TradingDisciplinePolicy`
- 10 Coding decision intakes through `CodingDisciplinePolicy`
- All 20 runs through the same `RiskEngine` instance
- No real execution, no file writes, no side effects

## 3. Non-Goals

- No real code modification
- No real financial trading
- No shell/MCP/IDE agent calls
- No ExecutionRequest/ExecutionReceipt creation
- No CandidateRule generation
- No Policy promotion

## 4. Finance 10-Run Results

| Run | Tag | Expected | Actual | Pass |
|-----|-----|----------|--------|------|
| F01 | valid conservative plan | execute | execute | ✅ |
| F02 | missing thesis | reject | reject | ✅ |
| F03 | missing stop_loss | reject | reject | ✅ |
| F04 | revenge_trade | escalate | escalate | ✅ |
| F05 | chasing | escalate | escalate | ✅ |
| F06 | max_loss > 2× risk_unit | reject | reject | ✅ |
| F07 | position > 10× risk_unit | reject | reject | ✅ |
| F08 | low-quality thesis | reject | reject | ✅ |
| F09 | valid conservative plan | execute | execute | ✅ |
| F10 | stressed emotional state | escalate | escalate | ✅ |

## 5. Coding 10-Run Results

| Run | Tag | Expected | Actual | Pass |
|-----|-----|----------|--------|------|
| C01 | test fix + plan | execute | execute | ✅ |
| C02 | doc change + plan | execute | execute | ✅ |
| C03 | missing task_description | reject | reject | ✅ |
| C04 | missing file_paths | reject | reject | ✅ |
| C05 | forbidden .env | reject | reject | ✅ |
| C06 | forbidden uv.lock | reject | reject | ✅ |
| C07 | forbidden migration runner | reject | reject | ✅ |
| C08 | high impact | escalate | escalate | ✅ |
| C09 | missing test_plan | escalate | escalate | ✅ |
| C10 | multi-file + plan | execute | execute | ✅ |

## 6. Combined Decision Distribution

```
           Execute  Reject  Escalate  Total
Finance       2       5        3       10
Coding        3       5        2       10
Combined      5      10        5       20
```

- **Execute 25%** — valid intakes with proper safeguards
- **Reject 50%** — missing fields, forbidden paths, risk ratio violations
- **Escalate 25%** — behavioral flags, high impact, missing test plans

## 7. Side-Effect Confirmation

```
✅ Errors:                  0
✅ Real file writes:        0
✅ Shell/MCP/IDE calls:     0
✅ ExecutionRequest created: 0
✅ ExecutionReceipt created: 0
✅ CandidateRule generated:  0
✅ Policy promoted:          0
```

## 8. Runtime Evidence Audit Relationship

The cross-pack dogfood validates the governance classification layer.
The DB-backed audit (`scripts/audit_runtime_evidence_db.py`) validates
the structural integrity of objects that WOULD be created if these intakes
were executed through the full API chain.

Together they form a two-layer evidence system:
- **Layer 1 (Dogfood):** "Does governance classify correctly?"
- **Layer 2 (DB Audit):** "Are the resulting objects structurally sound?"

## 9. Key Findings

1. **Core is Pack-agnostic.** The same `RiskEngine.validate_intake()` correctly
   handles both Finance and Coding intakes without modification. `governance/`
   imports zero `packs.finance` or `packs.coding` modules.

2. **Severity protocol is proven.** Both `RejectReason`/`EscalateReason` (Finance)
   and `CodingRejectReason`/`CodingEscalateReason` (Coding) use `.severity` +
   `.message`. Core only reads these two attributes.

3. **Gate priority holds.** In F04 and F05, both thesis quality escalation
   and behavioral escalation fire — the system correctly accumulates all
   reasons and applies reject > escalate > execute priority.

## 10. Limitations

- All runs are simulation-only — no real API calls, no DB writes.
- Finance samples use the same symbol/timeframe structure — could be diversified.
- Coding forbidden path list is minimal (9 patterns).
- No CandidateRule generation from these runs (requires Review completion).

## 11. Related Artifacts

| Artifact | Path |
|----------|------|
| Dogfood script | `scripts/run_cross_pack_dogfood.py` |
| Finance policy | `packs/finance/trading_discipline_policy.py` |
| Coding policy | `packs/coding/policy.py` |
| Runtime evidence checker | `scripts/check_runtime_evidence.py` |
| DB-backed audit | `scripts/audit_runtime_evidence_db.py` |
| Coding dogfood evidence | `docs/runtime/coding-pack-dogfood-evidence.md` |
| DB audit evidence | `docs/runtime/db-backed-runtime-evidence-audit.md` |

## 12. Next Recommended Wave

Wave G — CandidateRule Evidence Loop: complete the full Ordivon learning
cycle by running a dogfood → Review → Lesson → CandidateRule(draft) chain
and verifying the DB audit catches the full lifecycle.
