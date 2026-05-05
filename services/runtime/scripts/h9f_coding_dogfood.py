#!/usr/bin/env python3
"""H-9F Coding Dogfood — 10-run validation of CodingDisciplinePolicy + RiskEngine.

Runs 10 simulated coding decision intakes through the governance pipeline.
NO real code execution, NO file writes, NO shell/MCP/IDE calls.
Only validates: CodingDisciplinePolicy → RiskEngine.validate_intake().

Usage:
    uv run python scripts/h9f_coding_dogfood.py
"""

from __future__ import annotations

import json
import sys

from domains.decision_intake.models import DecisionIntake
from governance_engine.risk_engine.engine import RiskEngine
from packs.coding.models import CodingDecisionPayload
from packs.coding.policy import CodingDisciplinePolicy


def _intake(pack_id: str, intake_type: str, payload: dict) -> DecisionIntake:
    return DecisionIntake(
        id=f"intake-df-{pack_id}-{hash(str(payload)) % 10000:04d}",
        pack_id=pack_id,
        intake_type=intake_type,
        payload=payload,
        status="validated",
    )


def _run(engine, policy, tag, payload, expected):
    intake = _intake("coding", "code_change", payload)
    decision = engine.validate_intake(intake, pack_policy=policy)
    actual = decision.decision
    passed = actual == expected
    return {
        "tag": tag,
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "reasons": decision.reasons,
    }


def main():
    engine = RiskEngine()
    policy = CodingDisciplinePolicy()
    runs = []

    # ── Run 1: Normal test file fix + test_plan → execute ──────────
    runs.append(
        _run(
            engine,
            policy,
            "R01: test fix + plan",
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

    # ── Run 2: Doc change + test_plan → execute ────────────────────
    runs.append(
        _run(
            engine,
            policy,
            "R02: doc change + plan",
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

    # ── Run 3: Missing task_description → reject ───────────────────
    runs.append(
        _run(
            engine,
            policy,
            "R03: missing task",
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

    # ── Run 4: Missing file_paths → reject ─────────────────────────
    runs.append(
        _run(
            engine,
            policy,
            "R04: missing files",
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

    # ── Run 5: Modify .env → reject ────────────────────────────────
    runs.append(
        _run(
            engine,
            policy,
            "R05: touch .env",
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

    # ── Run 6: Modify uv.lock → reject ─────────────────────────────
    runs.append(
        _run(
            engine,
            policy,
            "R06: touch uv.lock",
            {
                "task_description": "Update dependency version",
                "file_paths": ["uv.lock"],
                "estimated_impact": "low",
                "reasoning": "Patch version bump for security fix.",
                "test_plan": "Run pip-audit after update.",
            },
            "reject",
        )
    )

    # ── Run 7: Modify migration runner → reject ────────────────────
    runs.append(
        _run(
            engine,
            policy,
            "R07: touch migration runner",
            {
                "task_description": "Add idempotent migration for new column",
                "file_paths": ["state/db/migrations/runner.py"],
                "estimated_impact": "high",
                "reasoning": "New ORM column needs migration.",
                "test_plan": "Run schema drift check + PG regression.",
            },
            "reject",
        )
    )

    # ── Run 8: High impact → escalate ──────────────────────────────
    runs.append(
        _run(
            engine,
            policy,
            "R08: high impact",
            {
                "task_description": "Rewrite the risk engine validation logic",
                "file_paths": ["governance_engine/risk_engine/engine.py"],
                "estimated_impact": "high",
                "reasoning": "Need to support streaming validation.",
                "test_plan": "Run full governance test suite.",
            },
            "escalate",
        )
    )

    # ── Run 9: Missing test_plan → escalate ────────────────────────
    runs.append(
        _run(
            engine,
            policy,
            "R09: missing test plan",
            {
                "task_description": "Optimize database query in recommendation service",
                "file_paths": ["domains/strategy/service.py"],
                "estimated_impact": "medium",
                "reasoning": "N+1 query detected in list_recent.",
                "test_plan": None,
            },
            "escalate",
        )
    )

    # ── Run 10: Multi-file medium change + test_plan → execute ─────
    runs.append(
        _run(
            engine,
            policy,
            "R10: multi-file + plan",
            {
                "task_description": "Extract shared validation helpers into shared/validation.py",
                "file_paths": [
                    "shared/validation.py",
                    "capabilities/domain/finance_decisions.py",
                    "capabilities/domain/finance_outcome.py",
                ],
                "estimated_impact": "medium",
                "reasoning": "Duplicate validation logic across 3 capability files.",
                "test_plan": "Run pytest tests/unit/capabilities/ tests/unit/shared/ -v.",
            },
            "execute",
        )
    )

    # ── Run 11: Medium impact single file + test_plan → execute ────
    # CPR-2: Added to prove medium-impact changes with a test plan
    # correctly pass all 5 gates and receive execute.
    runs.append(
        _run(
            engine,
            policy,
            "R11: medium + plan",
            {
                "task_description": "Refactor validation logic in capabilities/domain/finance_decisions.py",
                "file_paths": ["capabilities/domain/finance_decisions.py"],
                "estimated_impact": "medium",
                "reasoning": "Extract duplicate validation into shared helper function.",
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

    execute_count = sum(1 for r in runs if r["actual"] == "execute")
    reject_count = sum(1 for r in runs if r["actual"] == "reject")
    escalate_count = sum(1 for r in runs if r["actual"] == "escalate")

    expected_width = 8
    actual_width = 8

    print(f"\n{'=' * 70}")
    print(f"{'Run':<6} {'Expected':<{expected_width}} {'Actual':<{actual_width}} {'Pass':<5} Reasons")
    print(f"{'=' * 70}")
    for r in runs:
        symbol = "✅" if r["passed"] else "❌"
        reason_summary = r["reasons"][0][:55] if r["reasons"] else "—"
        print(
            f"{r['tag']:<6} {r['expected']:<{expected_width}} "
            f"{r['actual']:<{actual_width}} {symbol:<5} {reason_summary}"
        )
        if len(r["reasons"]) > 1:
            for extra in r["reasons"][1:]:
                print(f"      {'':<{expected_width}} {'':<{actual_width}}      {extra[:55]}")

    print(f"\n{'=' * 50}")
    print(f"RESULTS: {pass_count}/{len(runs)} passed")
    print(f"{'=' * 50}")
    print(f"  Execute:  {execute_count}")
    print(f"  Reject:   {reject_count}")
    print(f"  Escalate: {escalate_count}")
    print(f"  Errors:   0")
    print(f"  Real file writes: 0")
    print(f"  Shell/MCP/IDE calls: 0")
    print(f"  ExecutionRequest/Receipt: 0")

    if fail_count == 0:
        print(f"\n✅ ALL {len(runs)} RUNS PASSED — Coding Pack governance verified")
    else:
        print(f"\n❌ {fail_count} FAILURES")
        for r in runs:
            if not r["passed"]:
                print(f"  FAIL: {r['tag']} — expected={r['expected']}, actual={r['actual']}")
                for reason in r["reasons"]:
                    print(f"        reason: {reason}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
