"""Legacy sidecar routes cannot promote observed input drift to PASS."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest import mock

from artifact_core.contracts import FileCommitment
from scripts import artifact_verify as service


def make_request(root: Path) -> tuple[Path, Path, Path, str]:
    profile_id = "design-3d-glb-static-mesh-r1"
    profile = service.PROFILE_REGISTRY.resolve(profile_id).canonical_path
    assert not service.BINDING_REGISTRY.resolve(profile_id, "verify").snapshot_inputs
    subject = root / "asset.glb"
    contract = root / "contract.json"
    subject.write_bytes(b"admitted bytes")
    contract.write_text("{}")
    ref = lambda path: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    request = root / "request.json"
    request.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "kind": "artifact-verification-request",
                "requestId": "test:legacy-input-drift",
                "profile": {"id": profile_id, **ref(profile)},
                "subject": ref(subject),
                "objectContract": ref(contract),
                "evidenceDirectory": str(root / "evidence"),
            }
        )
    )
    return request, subject, contract, profile_id


def test_disappearing_legacy_input_is_bounded_admission_failure(tmp_path):
    request, _, _, _ = make_request(tmp_path)
    with (
        mock.patch.object(FileCommitment, "from_path", side_effect=OSError("vanished after check")),
        mock.patch.object(service, "load_function") as native,
    ):
        result = service.verify_request(request)
    assert result["status"] == "FAIL"
    assert any("vanished after check" in issue for issue in result["failures"])
    native.assert_not_called()
    assert not (tmp_path / "evidence").exists()


def test_legacy_path_observed_drift_after_native_cannot_promote(tmp_path):
    request, subject, contract, profile_id = make_request(tmp_path)
    original = subject.read_bytes()

    def native(*_args):
        subject.write_bytes(b"replacement")
        return {
            "status": "PASS",
            "profileId": profile_id,
            "artifact": {"sha256": hashlib.sha256(original).hexdigest(), "size": len(original)},
            "contract": {"sha256": hashlib.sha256(contract.read_bytes()).hexdigest()},
            "failures": [],
        }

    with mock.patch.object(service, "load_function", return_value=(native, "f" * 64)):
        result = service.verify_request(request)
    assert result["status"] == "FAIL", result
    assert not result["profileVerificationComplete"]
    assert result["verification"]["status"] == "PASS"
    assert result["standingCoverage"]["verificationStatus"] == "UNKNOWN"
    assert any("subject" in issue and "drift" in issue for issue in result["failures"])


def test_legacy_contract_drift_before_call_rejects_without_native_effect(tmp_path):
    request, _, contract, _ = make_request(tmp_path)
    native = mock.Mock(return_value={"status": "PASS"})

    def load(*_args):
        contract.write_bytes(b"replacement")
        return native, "f" * 64

    with mock.patch.object(service, "load_function", side_effect=load):
        result = service.verify_request(request)
    assert result["status"] == "FAIL"
    assert any("object contract" in issue and "drift" in issue for issue in result["failures"])
    native.assert_not_called()


def test_legacy_path_checks_do_not_claim_snapshot_or_aba(tmp_path):
    request, subject, contract, profile_id = make_request(tmp_path)

    def native(*_args):
        return {
            "status": "PASS",
            "profileId": profile_id,
            "artifact": {
                "sha256": hashlib.sha256(subject.read_bytes()).hexdigest(),
                "size": subject.stat().st_size,
            },
            "contract": {"sha256": hashlib.sha256(contract.read_bytes()).hexdigest()},
            "failures": [],
        }

    with mock.patch.object(service, "load_function", return_value=(native, "f" * 64)):
        result = service.verify_request(request)
    assert result["status"] == "PASS"
    assert not result["profileVerificationComplete"]
    assert result["inputIdentity"]["subject"] == "ADMISSION_DIGEST_ONLY"
    assert result["inputIdentity"]["legacyPathRecheck"] == "CONSISTENT_AT_CHECKS"
    assert result["inputIdentity"]["sourcePathContinuity"] == "NOT_CLAIMED"
