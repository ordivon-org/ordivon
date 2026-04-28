#!/usr/bin/env python3
"""Eval Corpus Runner — validates governance classification against expected decisions.

Loads eval cases from evals/*.json, runs each through RiskEngine.validate_intake(),
compares actual vs expected, and outputs a machine-parseable JSON summary.

Exit 0 = all cases pass. Exit 1 = one or more cases fail.

NO: ExecutionRequest, ExecutionReceipt, file writes, shell/MCP/IDE calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_cases(glob_pattern: str) -> list[dict]:
    """Load all JSON case files matching the glob pattern."""
    cases: list[dict] = []
    for f in sorted(Path(glob_pattern).parent.glob(Path(glob_pattern).name)):
        if f.suffix == ".json":
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                cases.extend(data)
    return cases


def run_finance_case(case: dict) -> dict:
    from domains.decision_intake.models import DecisionIntake
    from governance.risk_engine.engine import RiskEngine
    from packs.finance.trading_discipline_policy import TradingDisciplinePolicy

    engine = RiskEngine()
    policy = TradingDisciplinePolicy()
    inp = case["input"]
    intake = DecisionIntake(
        id=f"eval-{case['case_id']}",
        pack_id=inp["pack_id"],
        intake_type=inp["intake_type"],
        payload=inp["payload"],
        status="validated",
    )
    decision = engine.validate_intake(intake, pack_policy=policy)
    return _check_result(case, decision)


def run_coding_case(case: dict) -> dict:
    from domains.decision_intake.models import DecisionIntake
    from governance.risk_engine.engine import RiskEngine
    from packs.coding.policy import CodingDisciplinePolicy

    engine = RiskEngine()
    policy = CodingDisciplinePolicy()
    inp = case["input"]
    intake = DecisionIntake(
        id=f"eval-{case['case_id']}",
        pack_id=inp["pack_id"],
        intake_type=inp["intake_type"],
        payload=inp["payload"],
        status="validated",
    )
    decision = engine.validate_intake(intake, pack_policy=policy)
    return _check_result(case, decision)


def run_cross_pack_case(case: dict) -> dict:
    from domains.decision_intake.models import DecisionIntake
    from governance.risk_engine.engine import RiskEngine
    from packs.coding.policy import CodingDisciplinePolicy
    from packs.finance.trading_discipline_policy import TradingDisciplinePolicy

    engine = RiskEngine()

    if case.get("check_type") == "static":
        import subprocess

        cmd = case.get("check_command", "")
        if cmd:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(ROOT))
            passed = (result.returncode == 1 and result.stdout.strip() == "") == case["expected"].get(
                "output_empty", True
            )
            return {
                "case_id": case["case_id"],
                "pack": "cross_pack",
                "passed": passed,
                "expected": case["expected"],
                "actual": {"exit_code": result.returncode, "output": result.stdout.strip()[:200]},
            }

    fin_intake = DecisionIntake(
        id=f"eval-{case['case_id']}-fin",
        pack_id=case["input_finance"]["pack_id"],
        intake_type=case["input_finance"]["intake_type"],
        payload=case["input_finance"]["payload"],
        status="validated",
    )
    cod_intake = DecisionIntake(
        id=f"eval-{case['case_id']}-cod",
        pack_id=case["input_coding"]["pack_id"],
        intake_type=case["input_coding"]["intake_type"],
        payload=case["input_coding"]["payload"],
        status="validated",
    )

    fin_dec = engine.validate_intake(fin_intake, pack_policy=TradingDisciplinePolicy())
    cod_dec = engine.validate_intake(cod_intake, pack_policy=CodingDisciplinePolicy())

    passed = (
        fin_dec.decision == case["expected"]["finance_decision"]
        and cod_dec.decision == case["expected"]["coding_decision"]
    )
    return {
        "case_id": case["case_id"],
        "pack": "cross_pack",
        "passed": passed,
        "expected": case["expected"],
        "actual": {
            "finance": fin_dec.decision,
            "coding": cod_dec.decision,
        },
    }


def _check_result(case: dict, decision) -> dict:
    expected_decision = case["expected"]["decision"]
    reason_patterns = case["expected"].get("reason_patterns", [])
    actual = decision.decision
    reasons_text = " ".join(decision.reasons).lower()

    pattern_pass = all(p.lower() in reasons_text for p in reason_patterns) if reason_patterns else True

    return {
        "case_id": case["case_id"],
        "pack": case["pack"],
        "passed": actual == expected_decision and pattern_pass,
        "expected": case["expected"],
        "actual": {"decision": actual, "reasons": decision.reasons},
    }


def main() -> int:
    EVALS_DIR = ROOT / "evals"

    finance_cases = load_cases(str(EVALS_DIR / "finance_cases.json"))
    coding_cases = load_cases(str(EVALS_DIR / "coding_cases.json"))
    cross_pack_cases = load_cases(str(EVALS_DIR / "cross_pack_cases.json"))

    results: list[dict] = []

    for case in finance_cases:
        results.append(run_finance_case(case))
    for case in coding_cases:
        results.append(run_coding_case(case))
    for case in cross_pack_cases:
        results.append(run_cross_pack_case(case))

    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)

    fin_pass = sum(1 for r in results if r["pack"] == "finance" and r["passed"])
    cod_pass = sum(1 for r in results if r["pack"] == "coding" and r["passed"])
    xp_pass = sum(1 for r in results if r["pack"] == "cross_pack" and r["passed"])

    # Human-readable summary
    print(f"\n{'=' * 60}")
    print(f"EVAL CORPUS v1 — {total} cases")
    print(f"{'=' * 60}")
    for r in results:
        symbol = "✅" if r["passed"] else "❌"
        actual_str = r["actual"].get("decision", r["actual"])
        print(f"  {symbol} {r['case_id']} ({r['pack']}): {actual_str}")

    print(f"\n{'=' * 50}")
    print(f"RESULTS: {passed}/{total} passed")
    print(f"  Finance:    {fin_pass}/{len(finance_cases)}")
    print(f"  Coding:     {cod_pass}/{len(coding_cases)}")
    print(f"  Cross-Pack: {xp_pass}/{len(cross_pack_cases)}")

    if failed > 0:
        print(f"\n❌ {failed} FAILURES:")
        for r in results:
            if not r["passed"]:
                print(f"  {r['case_id']}: expected={r['expected']}, actual={r['actual']}")

    # Machine-readable JSON summary
    summary = {
        "eval_corpus_version": "v1",
        "total": total,
        "passed": passed,
        "failed": failed,
        "by_pack": {
            "finance": {"total": len(finance_cases), "passed": fin_pass},
            "coding": {"total": len(coding_cases), "passed": cod_pass},
            "cross_pack": {"total": len(cross_pack_cases), "passed": xp_pass},
        },
        "results": results,
    }
    print("\n--- JSON SUMMARY ---")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
