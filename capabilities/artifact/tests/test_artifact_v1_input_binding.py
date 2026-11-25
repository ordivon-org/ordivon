"""Admission and receipt identity regressions for the legacy delivery stage."""
from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from artifact_verification import stage


def test_v1_native_result_cannot_be_rebound_to_replaced_subject_or_profile() -> None:
    from artifact_core.contracts import file_fact

    for drift in ("subject", "profile", "subject_missing", "profile_missing", "none"):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            profile_path = directory / "profile.json"
            profile_path.write_text("{}")
            subject = directory / "document.docx"
            subject.write_bytes(b"observed-by-verifier")

            def verify(path):
                observation = file_fact(path)
                if drift == "subject":
                    path.write_bytes(b"different-unverified-bytes")
                elif drift == "profile":
                    profile_path.write_text('{"replaced": true}')
                elif drift == "subject_missing":
                    path.unlink()
                elif drift == "profile_missing":
                    profile_path.unlink()
                return {
                    "status": "PASS", "artifact": observation,
                    "validatorOutput": {"validator": {"packageVersion": "test"}},
                    "failures": [],
                }

            hooks = SimpleNamespace(
                validate_profile=lambda _: {
                    "status": "PASS",
                    "profile": {
                        "id": "test-drift", "artifactClass": "document",
                        "gates": {"profileSchema": True, "structural": True},
                    },
                },
                primary_suffix=lambda _: ".docx",
                verify_openxml_artifact=verify,
            )
            result = stage.execute_verify_stage(
                profile_path, subject, directory / "evidence", hooks=hooks,
            )
            if drift == "none":
                assert result["status"] == "PASS"
                assert result["profileVerificationComplete"]
                assert result["standingCoverage"]["verificationStatus"] == "PASS"
                assert (directory / "evidence/structural.vsa.json").is_file()
                continue
            assert result["status"] == "FAIL", (drift, result)
            assert not result["profileVerificationComplete"]
            assert result["standingCoverage"]["verificationStatus"] == "UNKNOWN"
            assert not (directory / "evidence/structural.vsa.json").exists()



def test_v1_final_observation_cannot_promote_a_later_replaced_subject() -> None:
    from artifact_verification.evidence import write_gate_receipt

    with tempfile.TemporaryDirectory() as root:
        directory = Path(root)
        profile = directory / "profile.json"
        profile.write_text("{}")
        subject = directory / "document.docx"
        subject.write_bytes(b"original")
        hooks = SimpleNamespace(
            validate_profile=lambda _: {
                "status": "PASS", "profile": {
                    "id": "late-drift", "artifactClass": "document",
                    "gates": {"profileSchema": True, "structural": True},
                },
            },
            primary_suffix=lambda _: ".docx",
            verify_openxml_artifact=lambda _: {"status": "PASS", "failures": []},
        )

        def replace_after_receipt(*args, **kwargs):
            receipt = write_gate_receipt(*args, **kwargs)
            if receipt["gate"] == "structural":
                assert receipt["status"] == "PASS"
                subject.write_bytes(b"replacement")
            return receipt

        with mock.patch.object(stage, "write_gate_receipt", side_effect=replace_after_receipt):
            result = stage.execute_verify_stage(profile, subject, directory / "evidence", hooks=hooks)
        assert result["status"] == "FAIL"
        assert not result["profileVerificationComplete"]
        assert result["standingCoverage"]["verificationStatus"] == "UNKNOWN"
        assert result["inputIdentity"]["sourcePathContinuity"] == "NOT_CLAIMED"


def test_v1_profile_drift_during_validation_stops_native_verification() -> None:
    with tempfile.TemporaryDirectory() as root:
        directory = Path(root)
        profile = directory / "profile.json"
        profile.write_text("{}")
        subject = directory / "document.docx"
        subject.write_bytes(b"original")

        def validate(path):
            path.write_text('{"new": true}')
            return {"status": "PASS", "profile": {
                "id": "drift", "artifactClass": "document", "gates": {"structural": True},
            }}

        hooks = SimpleNamespace(
            validate_profile=validate,
            primary_suffix=lambda _: ".docx",
            verify_openxml_artifact=mock.Mock(),
        )
        result = stage.execute_verify_stage(profile, subject, directory / "evidence", hooks=hooks)
        hooks.verify_openxml_artifact.assert_not_called()
        assert result["status"] == "FAIL"
        assert not result["profileVerificationComplete"]
        assert result["standingCoverage"]["verificationStatus"] == "UNKNOWN"
