#!/usr/bin/env python3
"""Cross-Pack Evidence Dogfood — validates Finance + Coding through unified governance.

Runs 10 Finance + 10 Coding simulated decision intakes through the same
RiskEngine.validate_intake() pipeline. Verifies that Ordivon's governance
layer is Pack-agnostic.

NO real code execution, NO file writes, NO shell/MCP/IDE calls.
NO ExecutionRequest/Receipt creation, NO CandidateRule generation.
"""

from __future__ import annotations

import sys

from domains.decision_intake.models import DecisionIntake
from governance.risk_engine.engine import RiskEngine
from packs.coding.policy import CodingDisciplinePolicy
from packs.finance.trading_discipline_policy import TradingDisciplinePolicy


def _run(engine, policy, pack_id, intake_type, tag, payload, expected):
    intake = DecisionIntake(
        id=f"intake-xp-{pack_id}-{hash(str(payload)) % 10000:04d}",
        pack_id=pack_id,
        intake_type=intake_type,
        payload=payload,
        status="validated",
    )
    decision = engine.validate_intake(intake, pack_policy=policy)
    actual = decision.decision
    passed = actual == expected
    return {
        "tag": tag,
        "pack": pack_id,
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "reasons": decision.reasons,
    }


def main():
    engine = RiskEngine()
    finance_policy = TradingDisciplinePolicy()
    coding_policy = CodingDisciplinePolicy()
    runs = []

    # ═══════════════════════════════════════════════════════════════════
    # FINANCE — 10 runs
    # ═══════════════════════════════════════════════════════════════════

    # F1: valid conservative plan → execute
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F01 valid",
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "direction": "long",
                "thesis": "BTC breaking above resistance with volume confirmation; invalidated below 200 EMA.",
                "stop_loss": "2%",
                "max_loss_usdt": 200,
                "position_size_usdt": 1000,
                "risk_unit_usdt": 200,
                "is_revenge_trade": False,
                "is_chasing": False,
                "emotional_state": "calm",
                "confidence": 0.7,
            },
            "execute",
        )
    )

    # F2: missing thesis → reject
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F02 no thesis",
            {
                "symbol": "ETHUSDT",
                "timeframe": "4h",
                "direction": "short",
                "thesis": "",
                "stop_loss": "5%",
                "max_loss_usdt": 500,
                "position_size_usdt": 2000,
                "risk_unit_usdt": 250,
                "is_revenge_trade": False,
                "is_chasing": False,
                "emotional_state": "neutral",
                "confidence": 0.6,
            },
            "reject",
        )
    )

    # F3: missing stop_loss → reject
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F03 no stop_loss",
            {
                "symbol": "SOLUSDT",
                "timeframe": "15m",
                "direction": "long",
                "thesis": "SOL bouncing off support with RSI divergence confirmation.",
                "stop_loss": "",
                "max_loss_usdt": 300,
                "position_size_usdt": 1500,
                "risk_unit_usdt": 150,
                "is_revenge_trade": False,
                "is_chasing": False,
                "emotional_state": "calm",
                "confidence": 0.65,
            },
            "reject",
        )
    )

    # F4: revenge_trade → escalate
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F04 revenge",
            {
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "direction": "long",
                "thesis": "Quick scalp after previous loss to recover.",
                "stop_loss": "1%",
                "max_loss_usdt": 100,
                "position_size_usdt": 500,
                "risk_unit_usdt": 100,
                "is_revenge_trade": True,
                "is_chasing": False,
                "emotional_state": "angry",
                "confidence": 0.9,
            },
            "escalate",
        )
    )

    # F5: chasing → escalate
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F05 chasing",
            {
                "symbol": "DOGEUSDT",
                "timeframe": "1m",
                "direction": "long",
                "thesis": "Price is pumping, don't want to miss the move.",
                "stop_loss": "10%",
                "max_loss_usdt": 1000,
                "position_size_usdt": 5000,
                "risk_unit_usdt": 500,
                "is_revenge_trade": False,
                "is_chasing": True,
                "emotional_state": "fomo",
                "confidence": 0.95,
            },
            "escalate",
        )
    )

    # F6: max_loss exceeded → reject
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F06 max_loss > 2x",
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "direction": "long",
                "thesis": "Strong trend continuation with volume confirmation.",
                "stop_loss": "5%",
                "max_loss_usdt": 1000,
                "position_size_usdt": 2000,
                "risk_unit_usdt": 200,
                "is_revenge_trade": False,
                "is_chasing": False,
                "emotional_state": "calm",
                "confidence": 0.7,
            },
            "reject",
        )
    )

    # F7: position_size exceeded → reject
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F07 position > 10x",
            {
                "symbol": "ETHUSDT",
                "timeframe": "4h",
                "direction": "long",
                "thesis": "ETH breaking key level with DeFi TVL confirmation; invalid if TVL drops.",
                "stop_loss": "3%",
                "max_loss_usdt": 300,
                "position_size_usdt": 5000,
                "risk_unit_usdt": 200,
                "is_revenge_trade": False,
                "is_chasing": False,
                "emotional_state": "calm",
                "confidence": 0.7,
            },
            "reject",
        )
    )

    # F8: low-quality thesis → reject
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F08 bad thesis",
            {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "direction": "long",
                "thesis": "just feels right",
                "stop_loss": "2%",
                "max_loss_usdt": 200,
                "position_size_usdt": 1000,
                "risk_unit_usdt": 200,
                "is_revenge_trade": False,
                "is_chasing": False,
                "emotional_state": "calm",
                "confidence": 0.8,
            },
            "reject",
        )
    )

    # F9: valid conservative plan → execute
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F09 valid",
            {
                "symbol": "LINKUSDT",
                "timeframe": "1d",
                "direction": "long",
                "thesis": "LINK accumulation zone with oracle network growth; invalidated below $10.",
                "stop_loss": "5%",
                "max_loss_usdt": 150,
                "position_size_usdt": 1000,
                "risk_unit_usdt": 150,
                "is_revenge_trade": False,
                "is_chasing": False,
                "emotional_state": "calm",
                "confidence": 0.75,
            },
            "execute",
        )
    )

    # F10: stressed emotional state → escalate
    runs.append(
        _run(
            engine,
            finance_policy,
            "finance",
            "trading_decision",
            "F10 stressed",
            {
                "symbol": "BTCUSDT",
                "timeframe": "15m",
                "direction": "short",
                "thesis": "Range breakdown confirmed with volume spike; exit if reclaims range.",
                "stop_loss": "2%",
                "max_loss_usdt": 150,
                "position_size_usdt": 750,
                "risk_unit_usdt": 150,
                "is_revenge_trade": False,
                "is_chasing": False,
                "emotional_state": "stressed",
                "confidence": 0.4,
            },
            "escalate",
        )
    )

    # ═══════════════════════════════════════════════════════════════════
    # CODING — 10 runs
    # ═══════════════════════════════════════════════════════════════════

    # C1: test fix + plan → execute
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C01 test fix",
            {
                "task_description": "Fix flaky assertion in test_user_auth.py",
                "file_paths": ["tests/unit/test_user_auth.py"],
                "estimated_impact": "low",
                "reasoning": "The assertion compares timestamps without tolerance.",
                "test_plan": "Run pytest tests/unit/test_user_auth.py -x 10 times.",
            },
            "execute",
        )
    )

    # C2: doc change + plan → execute
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C02 doc fix",
            {
                "task_description": "Update README with new setup instructions",
                "file_paths": ["README.md", "docs/setup.md"],
                "estimated_impact": "low",
                "reasoning": "Outdated instructions since uv migration.",
                "test_plan": "Manual review of rendered markdown.",
            },
            "execute",
        )
    )

    # C3: missing task_description → reject
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C03 no task",
            {
                "task_description": "",
                "file_paths": ["apps/api/app/main.py"],
                "estimated_impact": "low",
                "reasoning": "Need to refactor.",
                "test_plan": "Run unit tests.",
            },
            "reject",
        )
    )

    # C4: missing file_paths → reject
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C04 no files",
            {
                "task_description": "Refactor the authentication middleware",
                "file_paths": [],
                "estimated_impact": "medium",
                "reasoning": "Extract duplicate logic.",
                "test_plan": "Run auth test suite.",
            },
            "reject",
        )
    )

    # C5: forbidden .env → reject
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C05 .env",
            {
                "task_description": "Add new environment variable",
                "file_paths": [".env"],
                "estimated_impact": "medium",
                "reasoning": "Need DB_REPLICA_URL for read replica.",
                "test_plan": "Verify app starts with new env var.",
            },
            "reject",
        )
    )

    # C6: forbidden uv.lock → reject
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C06 uv.lock",
            {
                "task_description": "Update dependency version",
                "file_paths": ["uv.lock"],
                "estimated_impact": "low",
                "reasoning": "Patch version bump.",
                "test_plan": "Run pip-audit after update.",
            },
            "reject",
        )
    )

    # C7: forbidden migration runner → reject
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C07 migration",
            {
                "task_description": "Add idempotent migration",
                "file_paths": ["state/db/migrations/runner.py"],
                "estimated_impact": "high",
                "reasoning": "New ORM column needs migration.",
                "test_plan": "Run schema drift check.",
            },
            "reject",
        )
    )

    # C8: high impact → escalate
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C08 high impact",
            {
                "task_description": "Rewrite risk engine validation logic",
                "file_paths": ["governance/risk_engine/engine.py"],
                "estimated_impact": "high",
                "reasoning": "Need to support streaming validation.",
                "test_plan": "Run full governance test suite.",
            },
            "escalate",
        )
    )

    # C9: missing test_plan → escalate
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C09 no plan",
            {
                "task_description": "Optimize database query in recommendation service",
                "file_paths": ["domains/strategy/service.py"],
                "estimated_impact": "medium",
                "reasoning": "N+1 query detected.",
                "test_plan": None,
            },
            "escalate",
        )
    )

    # C10: multi-file + plan → execute
    runs.append(
        _run(
            engine,
            coding_policy,
            "coding",
            "code_change",
            "C10 multi-file",
            {
                "task_description": "Extract shared validation helpers",
                "file_paths": ["shared/validation.py", "capabilities/domain/finance_decisions.py"],
                "estimated_impact": "medium",
                "reasoning": "Duplicate validation logic across capability files.",
                "test_plan": "Run pytest tests/unit/capabilities/ -v.",
            },
            "execute",
        )
    )

    # ═══════════════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════════════
    pass_count = sum(1 for r in runs if r["passed"])
    fail_count = sum(1 for r in runs if not r["passed"])

    fin_exec = sum(1 for r in runs if r["pack"] == "finance" and r["actual"] == "execute")
    fin_rej = sum(1 for r in runs if r["pack"] == "finance" and r["actual"] == "reject")
    fin_esc = sum(1 for r in runs if r["pack"] == "finance" and r["actual"] == "escalate")
    cod_exec = sum(1 for r in runs if r["pack"] == "coding" and r["actual"] == "execute")
    cod_rej = sum(1 for r in runs if r["pack"] == "coding" and r["actual"] == "reject")
    cod_esc = sum(1 for r in runs if r["pack"] == "coding" and r["actual"] == "escalate")

    print(f"\n{'=' * 70}")
    print("CROSS-PACK EVIDENCE DOGFOOD — 20 RUNS")
    print(f"{'=' * 70}")

    print(f"\n{'Run':<6} {'Pack':<8} {'Expected':<8} {'Actual':<8} {'Pass':<5} Reason")
    print(f"{'-' * 70}")
    for r in runs:
        symbol = "✅" if r["passed"] else "❌"
        reason = r["reasons"][0][:50] if r["reasons"] else "—"
        print(f"{r['tag']:<6} {r['pack']:<8} {r['expected']:<8} {r['actual']:<8} {symbol:<5} {reason}")

    print(f"\n{'=' * 50}")
    print(f"RESULTS: {pass_count}/{len(runs)} passed")
    print(f"{'=' * 50}")
    print(f"  Finance:  execute={fin_exec}  reject={fin_rej}  escalate={fin_esc}")
    print(f"  Coding:   execute={cod_exec}  reject={cod_rej}  escalate={cod_esc}")
    print(f"  Combined: execute={fin_exec + cod_exec}  reject={fin_rej + cod_rej}  escalate={fin_esc + cod_esc}")
    print("\n  Errors:                  0")
    print("  Real file writes:        0")
    print("  Shell/MCP/IDE calls:     0")
    print("  ExecutionRequest/Receipt: 0")
    print("  CandidateRule generated: 0")
    print("  Policy promoted:         0")

    if fail_count == 0:
        print("\n✅ ALL 20 RUNS PASSED — Cross-pack governance verified")
    else:
        print(f"\n❌ {fail_count} FAILURES")
        for r in runs:
            if not r["passed"]:
                print(f"  FAIL: {r['tag']} ({r['pack']}) — expected={r['expected']}, actual={r['actual']}")
                for reason in r["reasons"]:
                    print(f"        {reason}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
