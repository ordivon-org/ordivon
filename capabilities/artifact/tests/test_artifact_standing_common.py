"""Public contract: both verification entrypoints expose the same bounded coverage semantics."""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from artifact_verification import stage
from artifact_verification.claim_coverage import assess_required_statuses


def test_shared_coverage_never_promotes_missing_unknown_failed_or_contradictory() -> None:
    required = {"decoded", "readback"}
    observed = {"decoded": "PASS"}
    missing = assess_required_statuses(required, observed)
    assert missing["verificationStatus"] == "UNKNOWN"
    assert missing["missing"] == ["readback"]
    assert missing["complete"] is False

    not_evaluated = assess_required_statuses(required, {"decoded": "PASS", "readback": "NOT_EVALUATED"})
    assert not_evaluated["verificationStatus"] == "UNKNOWN"
    assert not_evaluated["notEvaluated"] == ["readback"]

    failed = assess_required_statuses(required, {"decoded": "FAIL", "readback": "PASS"})
    assert failed["verificationStatus"] == "FAIL"
    assert failed["complete"] is False

    contradicted = assess_required_statuses(
        required, {"decoded": "PASS", "readback": "PASS"},
        issues=("native pointer does not match",),
    )
    assert contradicted["verificationStatus"] == "UNKNOWN"
    assert contradicted["complete"] is False

    disputed_failure = assess_required_statuses(
        required, {"decoded": "FAIL", "readback": "PASS"},
        issues=("reported FAIL has no independent matching native witness",),
    )
    assert disputed_failure["verificationStatus"] == "UNKNOWN"
    assert disputed_failure["failed"] == ["decoded"]
    assert disputed_failure["complete"] is False

    all_passed = assess_required_statuses(
        required, {"decoded": "PASS", "readback": "PASS"}
    )
    assert all_passed["verificationStatus"] == "PASS"
    assert all_passed["complete"] is True
    assert assess_required_statuses(set(), {})["complete"] is False


def test_v1_legacy_stage_preserves_pass_but_exposes_missing_gate_coverage() -> None:
    with tempfile.TemporaryDirectory() as root:
        directory = Path(root)
        profile = directory / "profile.json"
        profile.write_text("{}")
        subject = directory / "document.docx"
        subject.write_bytes(b"fixture")
        hooks = SimpleNamespace(
            validate_profile=lambda _: {
                "status": "PASS",
                "profile": {
                    "id": "test-v1",
                    "artifactClass": "document",
                    "gates": {"structural": True, "target": True},
                },
            },
            primary_suffix=lambda _: ".docx",
            verify_openxml_artifact=lambda _: {
                "status": "PASS",
                "validatorOutput": {"validator": {"packageVersion": "test"}},
                "failures": [],
            },
        )
        with mock.patch.object(
            stage, "write_gate_receipt",
            side_effect=lambda *args, **kwargs: {"status": args[4]["status"]},
        ):
            result = stage.execute_verify_stage(
                profile, subject, directory / "evidence", hooks=hooks
            )
        assert result["status"] == "PASS"
        assert result["profileVerificationComplete"] is False
        assert result["standingCoverage"]["verificationStatus"] == "UNKNOWN"
        assert result["standingCoverage"]["missing"] == ["target"]
        assert result["standingCoverage"]["complete"] is False



def test_v1_native_failed_required_gate_is_fail_not_unknown() -> None:
    # Use the actual v1 public stage + native local VSA receipt writer, not a
    # mocked status projection. A valid FAILED receipt falsifies a required gate;
    # it is not itself an evidence-integrity error.
    with tempfile.TemporaryDirectory() as root:
        directory = Path(root)
        profile = directory / "profile.json"
        profile.write_text("{}")
        subject = directory / "document.docx"
        subject.write_bytes(b"fixture")
        hooks = SimpleNamespace(
            validate_profile=lambda _: {
                "status": "PASS",
                "profile": {
                    "id": "test-v1-failure",
                    "artifactClass": "document",
                    "gates": {"profileSchema": True, "structural": True},
                },
            },
            primary_suffix=lambda _: ".docx",
            verify_openxml_artifact=lambda _: {
                "status": "FAIL",
                "validatorOutput": {"validator": {"packageVersion": "test"}},
                "failures": ["structure invalid"],
            },
        )
        result = stage.execute_verify_stage(
            profile, subject, directory / "evidence", hooks=hooks
        )
        assert result["status"] == "FAIL"
        native = result["receipts"]["structural"]
        assert native["status"] == "FAIL"
        assert native["vsaValidation"]["status"] == "PASS"
        assert result["standingCoverage"]["failed"] == ["structural"]
        assert result["standingCoverage"]["verificationStatus"] == "FAIL"
        assert result["profileVerificationComplete"] is False



def test_v1_invalid_failed_gate_receipt_is_unknown_not_falsification() -> None:
    from artifact_verification.evidence import write_gate_receipt

    with tempfile.TemporaryDirectory() as root:
        directory = Path(root)
        profile = directory / "profile.json"
        profile.write_text("{}")
        subject = directory / "document.docx"
        subject.write_bytes(b"fixture")
        hooks = SimpleNamespace(
            validate_profile=lambda _: {
                "status": "PASS",
                "profile": {
                    "id": "test-v1-untrusted-failure",
                    "artifactClass": "document",
                    "gates": {"profileSchema": True, "structural": True},
                },
            },
            primary_suffix=lambda _: ".docx",
            verify_openxml_artifact=lambda _: {
                "status": "FAIL",
                "validatorOutput": {"validator": {"packageVersion": "test"}},
                "failures": ["structure invalid"],
            },
        )

        def corrupt_validation(*args, **kwargs):
            receipt = write_gate_receipt(*args, **kwargs)
            if receipt["gate"] == "structural":
                receipt["vsaValidation"] = {"status": "FAIL"}
            return receipt

        with mock.patch.object(stage, "write_gate_receipt", side_effect=corrupt_validation):
            result = stage.execute_verify_stage(
                profile, subject, directory / "evidence", hooks=hooks
            )
        assert result["status"] == "FAIL"
        assert result["standingCoverage"]["failed"] == ["structural"]
        assert result["standingCoverage"]["verificationStatus"] == "UNKNOWN"
        assert result["standingCoverage"]["evidenceIssues"] == [
            "failed gate lacks validated receipt: structural"
        ]
        assert result["profileVerificationComplete"] is False


def test_existing_formal_checker_refines_shared_standing_projection() -> None:
    path = Path(__file__).resolve().parents[1] / (
        "artifact_verification/formal/verify_claim_coverage.py"
    )
    spec = importlib.util.spec_from_file_location("artifact_shared_formal", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.check_shared_standing()
    assert result["abstractCasesChecked"] == 50
    assert result["counterexamples"] == 0
