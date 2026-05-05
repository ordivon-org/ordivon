"""Alpha-0 trust-laundering regression tests."""

from __future__ import annotations

import json
from pathlib import Path

from ordivon_verify import main, run_external_receipts, scan_receipt_files


FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
AUTH_FIXTURE = FIXTURES / "alpha0_authorization_laundering"
POLICY_FIXTURE = FIXTURES / "alpha0_candidate_policy_confusion"
SAFE_FIXTURE = FIXTURES / "alpha0_safe_boundaries"


def test_authorization_laundering_receipt_blocks():
    failures, scanned = scan_receipt_files(["receipts"], AUTH_FIXTURE)

    assert scanned == 1
    assert any(f["id"] == "authorization_laundering" for f in failures)


def test_candidate_rule_policy_confusion_blocks():
    failures, scanned = scan_receipt_files(["receipts"], POLICY_FIXTURE)

    assert scanned == 1
    assert any(f["id"] == "candidate_rule_policy_confusion" for f in failures)


def test_safe_boundary_language_passes():
    result = run_external_receipts(["receipts"], SAFE_FIXTURE)

    assert result["status"] == "PASS"


def test_authorization_laundering_fixture_json_report(capsys):
    exit_code = main(["all", "--root", str(AUTH_FIXTURE), "--json"])

    assert exit_code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "BLOCKED"
    assert any(f["id"] == "authorization_laundering" for f in report["hard_failures"])
    assert report["surfaces"]["review"]["status"] == "FAIL"


def test_candidate_rule_policy_fixture_json_report(capsys):
    exit_code = main(["all", "--root", str(POLICY_FIXTURE), "--json"])

    assert exit_code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "BLOCKED"
    assert any(f["id"] == "candidate_rule_policy_confusion" for f in report["hard_failures"])
