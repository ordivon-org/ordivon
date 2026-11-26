"""Operational absence is not native falsification."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from artifact_verification import stage
from artifact_verifiers.openxml import validator


@pytest.mark.parametrize("status", ["NOT_RUN", "NOT_EVALUATED", "UNKNOWN"])
def test_explicit_unknown_does_not_publish_binary_vsa(tmp_path, status):
    profile = tmp_path / "profile.json"
    profile.write_text("{}")
    subject = tmp_path / "a.docx"
    subject.write_bytes(b"fixture")
    evidence = tmp_path / "e"
    evidence.mkdir()
    (evidence / "structural.vsa.json").write_text("{}")
    hooks = SimpleNamespace(
        validate_profile=lambda _: {
            "status": "PASS",
            "profile": {
                "id": "fixture",
                "artifactClass": "document",
                "gates": {"structural": True},
            },
        },
        primary_suffix=lambda _: ".docx",
        verify_openxml_artifact=lambda _: {"status": status},
    )
    result = stage.execute_verify_stage(profile, subject, evidence, hooks=hooks)
    receipt = result["receipts"]["structural"]
    assert result["status"] == "FAIL"
    assert result["standingCoverage"]["verificationStatus"] == "UNKNOWN"
    assert receipt["verificationResult"] == "NOT_EVALUATED"
    assert "vsa" not in receipt
    assert not (evidence / "structural.vsa.json").exists()


@pytest.mark.parametrize(
    "stdout,code", [("", 126), ("[]", 0), ('{"status":"PASS"}', 0), ('{"status":"FAIL"}', 1)]
)
def test_openxml_unqualified_report_is_not_run(tmp_path, stdout, code):
    subject = tmp_path / "a.docx"
    subject.write_bytes(b"fixture")
    executable = tmp_path / "validator"
    executable.touch()
    with (
        patch.object(validator, "openxml_validator_executable", return_value=executable),
        patch.object(
            validator.subprocess,
            "run",
            return_value=SimpleNamespace(stdout=stdout, stderr="", returncode=code),
        ),
    ):
        result = validator.verify_openxml_artifact(subject)
    assert result["status"] == "NOT_RUN"


@pytest.mark.parametrize(
    "status,code,count,expected",
    [
        ("PASS", 0, 0, "PASS"),
        ("FAIL", 1, 1, "FAIL"),
        ("PASS", 0, 1, "NOT_RUN"),
        ("FAIL", 126, 1, "NOT_RUN"),
        ("PASS", 1, 0, "NOT_RUN"),
    ],
)
def test_openxml_native_report_contract(tmp_path, status, code, count, expected):
    import json

    from artifact_core.contracts import file_fact

    subject = tmp_path / "a.docx"
    subject.write_bytes(b"fixture")
    executable = tmp_path / "validator"
    executable.touch()
    payload = {
        "status": status,
        "artifact": {"sha256": file_fact(subject)["digest"]["sha256"]},
        "validator": {"implementation": "DocumentFormat.OpenXml", "api": "OpenXmlValidator"},
        "validationErrorCount": count,
        "validationErrors": [{"id": "TEST"}] * count,
    }
    with (
        patch.object(validator, "openxml_validator_executable", return_value=executable),
        patch.object(
            validator.subprocess,
            "run",
            side_effect=lambda *args, **kwargs: SimpleNamespace(
                stdout=json.dumps(payload), stderr="", returncode=code
            ),
        ),
    ):
        assert validator.verify_openxml_artifact(subject)["status"] == expected
        payload["artifact"]["sha256"] = "0" * 64
        assert validator.verify_openxml_artifact(subject)["status"] == "NOT_RUN"


def test_qpdf_unavailable_does_not_falsify(tmp_path):
    from artifact_verifiers.pdf import structural

    subject = tmp_path / "a.pdf"
    subject.write_bytes(b"fixture")
    with patch.object(structural, "qpdf_executable", return_value=None):
        assert structural.verify_pdf(subject)["status"] == "NOT_RUN"
    with (
        patch.object(structural, "qpdf_executable", return_value=Path("/bin/sh")),
        patch.object(
            structural.subprocess,
            "run",
            return_value=SimpleNamespace(returncode=126, stdout="", stderr=""),
        ),
    ):
        assert structural.verify_pdf(subject)["status"] == "NOT_RUN"
