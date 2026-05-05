"""Alpha casebook runner regression tests."""

from __future__ import annotations

from scripts import run_alpha_casebook


def test_casebook_has_alpha_1_governed_work_coverage():
    case_ids = {case.case_id for case in run_alpha_casebook.CASES}
    surfaces = {case.surface for case in run_alpha_casebook.CASES}

    assert len(run_alpha_casebook.CASES) >= 12
    assert {
        "A0-RT-01",
        "A0-RT-05",
        "A0-RT-06",
        "A0-RT-09",
        "A0-RT-11",
        "A0-RT-12",
        "A0-SAFE-BOUNDARY",
    }.issubset(case_ids)
    assert {
        "claims",
        "config",
        "debt",
        "diff",
        "docs",
        "receipts",
        "review",
        "tests",
    }.issubset(surfaces)
    assert all(case.regression_reason for case in run_alpha_casebook.CASES)


def test_generated_missing_test_command_case_blocks(tmp_path):
    case = next(case for case in run_alpha_casebook.CASES if case.case_id == "A0-RT-05")

    result = run_alpha_casebook._run_case(case, tmp_path)

    assert result["ok"] is True
    assert result["surface"] == "tests"
    assert result["status"] == "BLOCKED"


def test_generated_false_clean_tree_case_blocks(tmp_path):
    case = next(case for case in run_alpha_casebook.CASES if case.case_id == "A0-RT-12")

    result = run_alpha_casebook._run_case(case, tmp_path)

    assert result["ok"] is True
    assert result["surface"] == "claims"
    assert result["status"] == "BLOCKED"
