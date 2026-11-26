"""An unavailable or inconsistent native validation is not a content verdict."""

import json
import subprocess

import pytest

from artifact_verifiers.pdf import conformance


def native_report(path, compliant=False):
    c = int(compliant)
    return {
        "report": {
            "jobs": [
                {
                    "itemDetails": {"name": str(path), "size": path.stat().st_size},
                    "validationResult": [
                        {
                            "jobEndStatus": "normal",
                            "profileName": "PDF/UA-2 + Tagged PDF validation profile",
                            "compliant": compliant,
                            "details": {"failedRules": 1 - c, "failedChecks": 1 - c},
                        }
                    ],
                }
            ],
            "batchSummary": {
                "totalJobs": 1,
                "outOfMemory": 0,
                "veraExceptions": 0,
                "failedEncryptedJobs": 0,
                "failedParsingJobs": 0,
                "validationSummary": {
                    "nonCompliantPdfaCount": 1 - c,
                    "compliantPdfaCount": c,
                    "failedJobCount": 0,
                    "totalJobCount": 1,
                    "successfulJobCount": 1,
                },
            },
        }
    }


@pytest.mark.parametrize(
    "case",
    [
        "malformed",
        "parse_failure",
        "false_string",
        "wrong_subject",
        "wrong_exit",
        "wrong_count",
        "timeout",
        "launch",
    ],
)
def test_unqualified_native_report_is_not_content_failure(tmp_path, monkeypatch, case):
    path = tmp_path / "x.pdf"
    path.write_bytes(b"fixture")
    monkeypatch.setattr(conformance, "verapdf_executable", lambda: path)
    raw = native_report(path)
    report = raw["report"]
    code = 1
    if case == "parse_failure":
        report["jobs"][0].pop("validationResult")
        report["batchSummary"]["failedParsingJobs"] = 1
        code = 7
    elif case == "false_string":
        report["jobs"][0]["validationResult"][0]["compliant"] = "false"
    elif case == "wrong_subject":
        report["jobs"][0]["itemDetails"]["name"] = str(tmp_path / "other.pdf")
    elif case == "wrong_exit":
        code = 2
    elif case == "wrong_count":
        report["batchSummary"]["validationSummary"]["failedJobCount"] = 1

    def invoke(*args, **kwargs):
        if case == "timeout":
            raise subprocess.TimeoutExpired("verapdf", 60)
        if case == "launch":
            raise OSError("fixture launch error")
        return subprocess.CompletedProcess(
            args, code, "bad-json" if case == "malformed" else json.dumps(raw), ""
        )

    monkeypatch.setattr(conformance.subprocess, "run", invoke)
    result = conformance.verify_pdf_conformance(path, "ua2")
    assert result["status"] == "NOT_RUN"
    assert result["compliant"] is None


@pytest.mark.parametrize("compliant", [False, True])
def test_qualified_native_positive_and_negative(tmp_path, monkeypatch, compliant):
    path = tmp_path / "x.pdf"
    path.write_bytes(b"fixture")
    monkeypatch.setattr(conformance, "verapdf_executable", lambda: path)
    monkeypatch.setattr(
        conformance.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(
            a, 0 if compliant else 1, json.dumps(native_report(path, compliant)), ""
        ),
    )
    result = conformance.verify_pdf_conformance(path, "ua2")
    assert result["status"] == ("PASS" if compliant else "FAIL")
    assert result["compliant"] is compliant
    assert result["parseError"] is None


@pytest.mark.integration
def test_actual_native_parse_failure_is_not_conformance_falsification(tmp_path):
    if conformance.verapdf_executable() is None:
        pytest.skip("native veraPDF unavailable")
    path = tmp_path / "not-pdf.pdf"
    path.write_bytes(b"not a PDF")
    result = conformance.verify_pdf_conformance(path, "ua2")
    assert result["status"] == "NOT_RUN", result
    assert result["exitCode"] == 7
    assert result["compliant"] is None
    assert result["parseError"]
