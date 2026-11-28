"""Browser gate claims must be bound to the native subject and actual observations."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from artifact_verification.stage import execute_verify_stage


@pytest.mark.parametrize(
    "case",
    [
        "wrong_digest",
        "failed_transport",
        "duplicate_name",
        "missing_renderer",
        "malformed_accessibility",
        "decisive_accessibility_failure",
        "positive",
    ],
)
def test_unqualified_browser_report_cannot_promote(tmp_path, case):
    artifact = tmp_path / "page.html"
    artifact.write_bytes(b"<h1>Example</h1>")
    profile = tmp_path / "profile.json"
    profile.write_text("{}")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    browsers = {
        k: {"name": n, "status": "PASS"}
        for k, n in [("chromium", "Chromium"), ("firefox", "Firefox"), ("webkit", "WebKit")]
    }
    browsers["chromium"]["accessibility"] = {"status": "PASS", "violationCount": 0}
    result = {
        "status": "PASS",
        "digestBound": True,
        "exitCode": 0,
        "verifierOutput": {
            "schemaVersion": 1,
            "kind": "artifact-web-local-verification-evidence",
            "status": "PASS",
            "subject": {"sha256": digest},
            "browsers": browsers,
            "tooling": {},
        },
    }
    if case == "wrong_digest":
        result["verifierOutput"]["subject"]["sha256"] = "0" * 64
        result["digestBound"] = False
    elif case == "failed_transport":
        result["status"] = "FAIL"
        result["exitCode"] = 1
    elif case == "duplicate_name":
        browsers["other"] = {"name": "Chromium", "status": "PASS"}
    elif case == "missing_renderer":
        browsers["webkit"]["status"] = "NOT_INSTALLED"
    elif case == "malformed_accessibility":
        browsers["chromium"]["accessibility"] = None
    elif case == "decisive_accessibility_failure":
        browsers["chromium"]["accessibility"] = {"status": "FAIL", "violationCount": 1}
    hooks = SimpleNamespace(
        validate_profile=lambda _: {
            "status": "PASS",
            "profile": {
                "id": "test-web",
                "artifactClass": "web",
                "gates": {
                    "profileSchema": True,
                    "structural": True,
                    "conformance": True,
                    "target": True,
                    "accessibility": True,
                },
                "targetRenderer": {"name": "Chromium", "required": True},
                "secondaryRenderers": [
                    {"name": "Firefox", "required": True},
                    {"name": "WebKit", "required": True},
                ],
            },
        },
        primary_suffix=lambda _: ".html",
        verify_html_conformance=lambda _: {"status": "PASS", "validator": {}},
        verify_web_local=lambda _: result,
    )
    value = execute_verify_stage(profile, artifact, tmp_path / "evidence", hooks=hooks)
    if case == "positive":
        assert value["status"] == "PASS"
        assert value["profileVerificationComplete"]
        assert value["standingCoverage"]["verificationStatus"] == "PASS"
        return
    assert value["status"] == "FAIL", value
    assert not value["profileVerificationComplete"]
    if case == "decisive_accessibility_failure":
        assert value["standingCoverage"]["verificationStatus"] == "FAIL"
        assert value["receipts"]["accessibility"]["verificationResult"] == "FAILED"
        assert (tmp_path / "evidence/accessibility.vsa.json").is_file()
        return
    assert value["standingCoverage"]["verificationStatus"] == "UNKNOWN"
    if case in ("wrong_digest", "failed_transport", "duplicate_name"):
        assert value["receipts"]["target"]["status"] != "PASS"
        assert value["receipts"]["accessibility"]["status"] != "PASS"
    unknown = [
        g
        for g in ("target", "accessibility")
        if value["receipts"][g].get("observationStanding") == "UNKNOWN"
    ]
    assert unknown
    for gate in unknown:
        assert value["receipts"][gate]["verificationResult"] == "NOT_EVALUATED"
        assert "vsa" not in value["receipts"][gate]
        assert not (tmp_path / "evidence" / f"{gate}.vsa.json").exists()
        assert (tmp_path / "evidence" / f"{gate}.raw.json").is_file()


def test_unqualified_gate_removes_stale_binary_attestation(tmp_path):
    from artifact_verification.evidence import write_unqualified_gate_receipt

    stale = tmp_path / "target.vsa.json"
    stale.write_text("{}")
    result = write_unqualified_gate_receipt(tmp_path, "target", {"status": "FAIL"})
    assert not stale.exists()
    assert result["observationStanding"] == "UNKNOWN"
