#!/usr/bin/env python3
"""Run Alpha casebook trust-regression fixtures.

Local-only. Does not mutate files, call networks, authorize actions, or run
agents. It verifies that known Alpha red-team cases keep producing the expected
trust signal.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) in sys.path:
    sys.path.remove(str(SRC))
sys.path.insert(0, str(SRC))

from ordivon_verify.cli import main as verify_main  # noqa: E402


@dataclass(frozen=True)
class AlphaCase:
    case_id: str
    fixture: str
    expected_status: str
    expected_exit: int
    expected_failure_id: str | None = None
    expected_missing_check: str | None = None


CASES = [
    AlphaCase(
        case_id="A0-05",
        fixture="tests/fixtures/alpha0_authorization_laundering",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="authorization_laundering",
    ),
    AlphaCase(
        case_id="A0-06",
        fixture="tests/fixtures/alpha0_candidate_policy_confusion",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="candidate_rule_policy_confusion",
    ),
    AlphaCase(
        case_id="A0-08",
        fixture="tests/fixtures/alpha0_missing_receipts_standard",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_missing_check="receipts",
    ),
    AlphaCase(
        case_id="A0-SAFE-BOUNDARY",
        fixture="tests/fixtures/alpha0_safe_boundaries",
        expected_status="DEGRADED",
        expected_exit=2,
        expected_missing_check="debt",
    ),
]


def _run_case(case: AlphaCase) -> dict:
    root = ROOT / case.fixture
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = verify_main(["all", "--root", str(root), "--json"])
    try:
        report = json.loads(buf.getvalue())
    except json.JSONDecodeError as exc:
        return {
            "case_id": case.case_id,
            "ok": False,
            "error": f"invalid JSON output: {exc}",
            "exit_code": exit_code,
        }

    errors = []
    if exit_code != case.expected_exit:
        errors.append(f"exit {exit_code} != expected {case.expected_exit}")
    if report.get("status") != case.expected_status:
        errors.append(f"status {report.get('status')} != expected {case.expected_status}")

    failure_ids = {f.get("id") for f in report.get("hard_failures", [])}
    if case.expected_failure_id and case.expected_failure_id not in failure_ids:
        errors.append(f"missing hard failure {case.expected_failure_id}")

    missing_checks = {m.get("check") for m in report.get("missing_evidence", [])}
    if case.expected_missing_check and case.expected_missing_check not in missing_checks:
        errors.append(f"missing evidence gap {case.expected_missing_check}")

    return {
        "case_id": case.case_id,
        "fixture": case.fixture,
        "ok": not errors,
        "status": report.get("status"),
        "trust_signal": report.get("trust_signal"),
        "exit_code": exit_code,
        "errors": errors,
    }


def main() -> int:
    results = [_run_case(case) for case in CASES]
    print(json.dumps({"tool": "alpha-casebook-runner", "results": results}, indent=2))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
