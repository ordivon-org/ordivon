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
    assert result["claimBindingCasesChecked"] == 16
    assert result["counterexamples"] == 0


def test_v1_witnessed_required_gate_failure_is_a_real_failure() -> None:
    """An executed, required failed gate is a scoped FAIL, not a missing witness."""
    with tempfile.TemporaryDirectory() as root:
        directory = Path(root)
        profile = directory / "profile.json"
        profile.write_text("{}")
        subject = directory / "document.docx"
        subject.write_bytes(b"not-real-docx")
        hooks = SimpleNamespace(
            validate_profile=lambda _: {
                "status": "PASS",
                "profile": {
                    "id": "failed-required-structural",
                    "artifactClass": "document",
                    "gates": {"structural": True},
                },
            },
            primary_suffix=lambda _: ".docx",
            verify_openxml_artifact=lambda _: {
                "status": "FAIL",
                "validatorOutput": {"validator": {"packageVersion": "test"}},
                "failures": ["OpenXML structure rejected"],
            },
        )
        result = stage.execute_verify_stage(
            profile, subject, directory / "evidence", hooks=hooks
        )
        assert result["status"] == "FAIL"
        assert result["receipts"]["structural"]["status"] == "FAIL"
        assert result["standingCoverage"]["failed"] == ["structural"]
        assert result["standingCoverage"]["verificationStatus"] == "FAIL"
        assert result["profileVerificationComplete"] is False


def test_claim_pointer_requires_claim_specific_semantic_coverage() -> None:
    from artifact_verification.claim_coverage import assess_required_evidence

    profile = {
        "requiredEvidence": {
            "decoderMatrix": {"required": True},
            "deliveryReadback": {"required": True},
        }
    }
    generic = {
        "status": "PASS",
        "verification": {"status": "PASS"},
        "claimResults": {
            claim: {
                "status": "PASS", "nativePointers": ["/verification"],
            }
            for claim in profile["requiredEvidence"]
        },
    }
    decision = assess_required_evidence(profile, generic)
    assert decision["complete"] is False
    assert any("claim-specific" in item for item in decision["issues"])

    generic["observations"] = {
        "combined": {
            "status": "PASS",
            "supportsClaims": ["decoderMatrix", "deliveryReadback"],
        }
    }
    for claim in generic["claimResults"].values():
        claim["nativePointers"] = ["/observations/combined"]
    supported = assess_required_evidence(profile, generic)
    assert supported["complete"] is True
    assert supported["status"] == "COMPLETE"


def test_frozen_png_metadata_observation_alias_keeps_its_actual_semantics() -> None:
    """Preserve the existing native /metadata observation and its frozen tool digest."""
    from artifact_verification.claim_coverage import assess_required_evidence

    profile = {
        "id": "still-image-png-srgb-r1",
        "requiredEvidence": {"metadataObservation": {"required": True}},
    }
    native = {
        "kind": "artifact-still-image-verification",
        "status": "PASS",
        "metadata": {"status": "PASS", "observedGroupPropertyCount": 4},
        "claimResults": {
            "metadataObservation": {
                "status": "PASS",
                "nativePointers": ["/metadata"],
            }
        },
    }
    assert assess_required_evidence(profile, native)["complete"] is True

    # A different family cannot inherit this one specific native alias.
    profile["id"] = "unrelated-profile"
    assert assess_required_evidence(profile, native)["complete"] is False
