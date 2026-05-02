"""HAP-3: HarnessReviewRecord schema and fixture tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "scripts" / "validate_hap_payload.py"
RR_DIR = ROOT / "examples" / "hap" / "review-record"


def _validate(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True, timeout=10, cwd=str(ROOT)
    )


class TestReviewRecordSchema:
    def test_schema_exists(self):
        path = ROOT / "src/ordivon_verify/schemas/hap-review-record.schema.json"
        assert path.exists()

    def test_schema_parses(self):
        path = ROOT / "src/ordivon_verify/schemas/hap-review-record.schema.json"
        json.loads(path.read_text())


class TestReviewRecordFixturesValidate:
    def test_comment_only_validates(self):
        r = _validate(RR_DIR / "comment-only-not-approval.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_detector_pass_validates(self):
        r = _validate(RR_DIR / "detector-pass-not-authorization.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_degraded_evidence_validates(self):
        r = _validate(RR_DIR / "degraded-evidence-insufficient.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_request_changes_validates(self):
        r = _validate(RR_DIR / "request-changes-blocking.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_candidate_rule_validates(self):
        r = _validate(RR_DIR / "candidate-rule-non-binding.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"


class TestReviewRecordBoundaries:
    def test_comment_only_not_approval(self):
        rec = json.loads((RR_DIR / "comment-only-not-approval.json").read_text())
        assert rec["review_status"] == "COMMENT_ONLY"
        assert rec["approval_scope"] == "none"
        assert "not approval" in rec["no_action_authorization_statement"].lower()

    def test_detector_pass_not_authorization(self):
        rec = json.loads((RR_DIR / "detector-pass-not-authorization.json").read_text())
        assert rec["reviewer_type"] == "detector"
        assert rec["approval_scope"] == "none"
        assert "not authorization" in rec["no_action_authorization_statement"].lower()

    def test_evidence_insufficient_not_approval(self):
        rec = json.loads((RR_DIR / "degraded-evidence-insufficient.json").read_text())
        assert rec["evidence_sufficiency"] == "insufficient"
        assert rec["review_status"] == "DEGRADED"

    def test_candidate_rule_non_binding(self):
        rec = json.loads((RR_DIR / "candidate-rule-non-binding.json").read_text())
        assert rec["candidate_rule_status"] == "proposed_non_binding"

    def test_approved_for_closure_not_action_authorization(self):
        rec = json.loads((RR_DIR / "candidate-rule-non-binding.json").read_text())
        assert rec["review_status"] == "APPROVED_FOR_CLOSURE"
        assert rec["approval_scope"] == "closure_only"
        assert "closure" in rec["approval_scope"]

    def test_no_can_access_secrets(self):
        for f in RR_DIR.glob("*.json"):
            content = f.read_text()
            assert "can_access_secrets" not in content

    def test_unsafe_comment_detector_approval(self):
        rec = json.loads((RR_DIR / "unsafe-comment-detector-approval.json").read_text())
        assert rec["reviewer_type"] == "detector"
        stmt = rec["no_action_authorization_statement"].lower()
        assert "approved" in stmt or "authorized" in stmt, (
            "Unsafe fixture should contain approval/authorization claim for testing"
        )
