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
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) in sys.path:
    sys.path.remove(str(SRC))
sys.path.insert(0, str(SRC))

from ordivon_verify.cli import main as verify_main  # noqa: E402


@dataclass(frozen=True)
class GovernedWorkCase:
    case_id: str
    surface: str
    regression_reason: str
    expected_status: str
    expected_exit: int
    fixture: str | None = None
    generator: str | None = None
    expected_failure_id: str | None = None
    expected_missing_check: str | None = None
    expected_non_json_error: str | None = None


CASES = [
    GovernedWorkCase(
        case_id="A0-RT-01",
        surface="config",
        regression_reason="Malformed config must fail closed instead of weakening checks.",
        generator="malformed_config",
        expected_status="CONFIG_ERROR",
        expected_exit=3,
        expected_non_json_error="Config parse error",
    ),
    GovernedWorkCase(
        case_id="A0-RT-02",
        surface="receipts",
        regression_reason="Standard mode cannot proceed without receipt evidence.",
        fixture="tests/fixtures/alpha0_missing_receipts_standard",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_missing_check="receipts",
    ),
    GovernedWorkCase(
        case_id="A0-RT-03",
        surface="review",
        regression_reason="Review/READY wording must not become merge or deploy authorization.",
        fixture="tests/fixtures/alpha0_authorization_laundering",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="authorization_laundering",
    ),
    GovernedWorkCase(
        case_id="A0-RT-04",
        surface="claims",
        regression_reason="CandidateRule must remain advisory and cannot be laundered into Policy.",
        fixture="tests/fixtures/alpha0_candidate_policy_confusion",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="candidate_rule_policy_confusion",
    ),
    GovernedWorkCase(
        case_id="A0-RT-05",
        surface="tests",
        regression_reason="Local test success claims need reproducible command evidence.",
        generator="missing_test_command",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="missing_test_evidence",
    ),
    GovernedWorkCase(
        case_id="A0-RT-06",
        surface="docs",
        regression_reason="Stale current-truth citations must not be accepted as authority.",
        generator="stale_document_registry",
        expected_status="BLOCKED",
        expected_exit=1,
    ),
    GovernedWorkCase(
        case_id="A0-RT-07",
        surface="diff",
        regression_reason="A sealed claim with omitted diff evidence is trust laundering.",
        generator="diff_evidence_missing",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="receipt_contradiction",
    ),
    GovernedWorkCase(
        case_id="A0-RT-08",
        surface="review",
        regression_reason="A sealed claim with pending review is incomplete evidence.",
        generator="review_incomplete",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="receipt_contradiction",
    ),
    GovernedWorkCase(
        case_id="A0-RT-09",
        surface="claims",
        regression_reason="DEGRADED cannot be normalized as a pass.",
        generator="degraded_as_pass",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="degraded_as_pass",
    ),
    GovernedWorkCase(
        case_id="A0-RT-10",
        surface="debt",
        regression_reason="Open governance debt must block standard-mode trust.",
        generator="hidden_open_debt",
        expected_status="BLOCKED",
        expected_exit=1,
    ),
    GovernedWorkCase(
        case_id="A0-RT-11",
        surface="receipts",
        regression_reason="External benchmark language cannot claim compliance or SLSA levels.",
        generator="external_benchmark_overclaim",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="external_benchmark_overclaim",
    ),
    GovernedWorkCase(
        case_id="A0-RT-12",
        surface="claims",
        regression_reason="Clean working tree claims must distinguish tracked vs untracked residue.",
        generator="false_clean_tree",
        expected_status="BLOCKED",
        expected_exit=1,
        expected_failure_id="clean_tree_overclaim",
    ),
    GovernedWorkCase(
        case_id="A0-SAFE-BOUNDARY",
        surface="debt",
        regression_reason="Safe boundary language remains DEGRADED when optional evidence is missing.",
        fixture="tests/fixtures/alpha0_safe_boundaries",
        expected_status="DEGRADED",
        expected_exit=2,
        expected_missing_check="debt",
    ),
]


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_clean_receipt(root: Path) -> None:
    receipt_dir = root / "receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / "clean.md").write_text(
        "# Receipt\n\n"
        "Status: COMPLETE\n\n"
        "## Verification Results\n\n"
        "| Check | Command | Result |\n"
        "|-------|---------|--------|\n"
        "| Unit tests | `pytest tests/unit -q` | passed |\n\n"
        "Skipped Verification: None\n"
        "READY does not authorize execution.\n",
        encoding="utf-8",
    )


def _write_base_config(root: Path, **extra: str) -> None:
    config = {
        "schema_version": "0.1",
        "project_name": "alpha-casebook-generated",
        "mode": "standard",
        "receipt_paths": ["receipts"],
    }
    config.update(extra)
    _write_json(root / "ordivon.verify.json", config)


def _generate_case_root(case: GovernedWorkCase, tmp: Path) -> Path:
    root = tmp / case.case_id
    root.mkdir(parents=True)

    if case.generator == "malformed_config":
        (root / "ordivon.verify.json").write_text("{ invalid json", encoding="utf-8")
        return root

    _write_base_config(root)
    receipt_dir = root / "receipts"
    receipt_dir.mkdir()

    if case.generator == "missing_test_command":
        (receipt_dir / "missing-test-evidence.md").write_text(
            "# Receipt\n\n"
            "Status: COMPLETE\n\n"
            "Tests passed locally.\n\n"
            "This receipt does not list a command or reproducible evidence.\n",
            encoding="utf-8",
        )
    elif case.generator == "stale_document_registry":
        _write_clean_receipt(root)
        gov = root / "governance"
        gov.mkdir()
        (gov / "document-registry.jsonl").write_text(
            '{"doc_id":"stale-current-truth","path":"docs/current.md","type":"runtime","status":"stale","authority":"current_status"}\n',
            encoding="utf-8",
        )
        _write_base_config(root, document_registry="governance/document-registry.jsonl")
    elif case.generator == "diff_evidence_missing":
        (receipt_dir / "diff-missing.md").write_text(
            "# Receipt\n\nStatus: **SEALED**\n\nDiff evidence omitted and addendum required.\n",
            encoding="utf-8",
        )
    elif case.generator == "review_incomplete":
        (receipt_dir / "review-pending.md").write_text(
            "# Receipt\n\nStatus: **SEALED**\n\nReview pending before trust decision.\n",
            encoding="utf-8",
        )
    elif case.generator == "degraded_as_pass":
        (receipt_dir / "degraded-pass.md").write_text(
            "# Receipt\n\nStatus: COMPLETE\n\nDEGRADED is green and passed for merge readiness.\n",
            encoding="utf-8",
        )
    elif case.generator == "hidden_open_debt":
        _write_clean_receipt(root)
        gov = root / "governance"
        gov.mkdir()
        (gov / "verification-debt-ledger.jsonl").write_text(
            '{"debt_id":"A0-DEBT-001","status":"open","description":"Hidden missing evidence debt."}\n',
            encoding="utf-8",
        )
        _write_base_config(root, debt_ledger="governance/verification-debt-ledger.jsonl")
    elif case.generator == "external_benchmark_overclaim":
        (receipt_dir / "benchmark-overclaim.md").write_text(
            "# Receipt\n\nStatus: COMPLETE\n\nOrdivon is certified, compliant, production-ready, and SLSA level 3.\n",
            encoding="utf-8",
        )
    elif case.generator == "false_clean_tree":
        (receipt_dir / "clean-tree-overclaim.md").write_text(
            "# Receipt\n\nStatus: COMPLETE\n\nThe working tree is clean.\n",
            encoding="utf-8",
        )
    else:
        raise ValueError(f"unknown case generator: {case.generator}")

    return root


def _case_root(case: GovernedWorkCase, tmp: Path) -> Path:
    if case.fixture:
        return ROOT / case.fixture
    if case.generator:
        return _generate_case_root(case, tmp)
    raise ValueError(f"{case.case_id}: either fixture or generator is required")


def _run_case(case: GovernedWorkCase, tmp: Path) -> dict:
    root = _case_root(case, tmp)
    buf = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        exit_code = verify_main(["all", "--root", str(root), "--json"])

    if case.expected_non_json_error:
        stderr = err.getvalue()
        errors = []
        if exit_code != case.expected_exit:
            errors.append(f"exit {exit_code} != expected {case.expected_exit}")
        if case.expected_non_json_error not in stderr:
            errors.append(f"missing stderr marker {case.expected_non_json_error!r}")
        return {
            "case_id": case.case_id,
            "surface": case.surface,
            "regression_reason": case.regression_reason,
            "fixture": case.fixture or f"generated:{case.generator}",
            "ok": not errors,
            "status": case.expected_status if not errors else "ERROR",
            "trust_signal": case.expected_status if not errors else "ERROR",
            "exit_code": exit_code,
            "missing_evidence": [],
            "errors": errors,
        }

    try:
        report = json.loads(buf.getvalue())
    except json.JSONDecodeError as exc:
        return {
            "case_id": case.case_id,
            "surface": case.surface,
            "regression_reason": case.regression_reason,
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
        "surface": case.surface,
        "regression_reason": case.regression_reason,
        "fixture": case.fixture or f"generated:{case.generator}",
        "ok": not errors,
        "status": report.get("status"),
        "trust_signal": report.get("trust_signal"),
        "exit_code": exit_code,
        "missing_evidence": sorted(missing_checks),
        "errors": errors,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="alpha-casebook-") as td:
        tmp = Path(td)
        results = [_run_case(case, tmp) for case in CASES]
    print(json.dumps({"tool": "alpha-casebook-runner", "case_count": len(results), "results": results}, indent=2))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
