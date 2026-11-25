"""Bind v2 request inputs without importing or executing any family verifier.

The caller owns private snapshot lifetime. Legacy paths retain admission-only
semantics: checks at admission and before/after a native call detect observed
drift, but cannot detect arbitrary ABA or prove a sidecar readset.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_core.bindings import CapabilityBinding
from artifact_core.contracts import FileCommitment
from artifact_core.input_snapshot import stage_verified_input
from artifact_core.json_validation import load_json
from artifact_core.profiles import ProfileRecord


def resolve_request_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


@dataclass(frozen=True)
class BoundInput:
    role: str
    original: Path
    delegated: Path
    sha256: str
    size: int
    legacy_commitment: FileCommitment | None

    def recheck_legacy(self) -> list[str]:
        if self.legacy_commitment is None:
            return []
        try:
            self.legacy_commitment.verify()
        except (OSError, RuntimeError, ValueError) as error:
            return [f"{self.role} admission path drift or unavailable: {error}"]
        return []


@dataclass(frozen=True)
class BoundVerificationInputs:
    profile: dict[str, Any]
    profile_path: Path
    subject: BoundInput
    contract: BoundInput | None

    def recheck_legacy(self) -> list[str]:
        issues = self.subject.recheck_legacy()
        if self.contract is not None:
            issues.extend(self.contract.recheck_legacy())
        return issues


def _bind_file(ref: dict[str, Any], scratch: Path, *, role: str, pinned: bool) -> BoundInput:
    path = resolve_request_path(ref["path"])
    label = "object contract" if role == "contract" else role
    if not path.is_file():
        raise ValueError(f"{label} is not a regular file")
    if pinned:
        try:
            snapshot = stage_verified_input(path, ref["sha256"], scratch, role=role)
        except (OSError, ValueError) as error:
            message = str(error).replace("contract bytes", "object contract bytes")
            raise ValueError(message) from error
        return BoundInput(label, path, snapshot.path, snapshot.sha256, snapshot.size, None)
    commitment = FileCommitment.from_path(path)
    if commitment.path != path:
        raise ValueError(f"{label} path changed during admission")
    if commitment.sha256 != ref["sha256"]:
        raise ValueError(f"{label} bytes differ from request digest")
    return BoundInput(label, path, path, commitment.sha256, commitment.size, commitment)


def bind_request_inputs(
    request: dict[str, Any],
    binding: CapabilityBinding,
    profile_record: ProfileRecord,
    profile_root: Path,
    scratch: Path,
) -> BoundVerificationInputs:
    profile_ref = request["profile"]
    profile_id = profile_ref["id"]
    profile_path = resolve_request_path(profile_ref["path"])
    if profile_root.resolve() not in profile_path.parents:
        raise ValueError("profile path is outside the normalized Artifact profile authority")
    if not profile_path.is_file():
        raise ValueError("profile file is unavailable")
    profile_input = stage_verified_input(
        profile_path, profile_ref["sha256"], scratch, role="profile"
    )
    if profile_input.sha256 != profile_record.canonical_sha256:
        raise ValueError("profile snapshot differs from indexed canonical Profile authority")
    profile = load_json(profile_input.path)
    if (
        not isinstance(profile, dict)
        or profile.get("profileVersion") != 2
        or profile.get("id") != profile_id
    ):
        raise ValueError("profile identity/version differs from request")
    if profile_path != profile_record.canonical_path:
        raise ValueError("profile path does not match the registered canonical profile")
    subject = _bind_file(
        request["subject"], scratch, role="subject", pinned=binding.snapshot_inputs
    )
    contract = None
    if request.get("objectContract"):
        contract = _bind_file(
            request["objectContract"], scratch, role="contract", pinned=binding.snapshot_inputs
        )
    elif binding.object_contract_required:
        raise ValueError(f"profile requires an object contract: {profile_id}")
    return BoundVerificationInputs(profile, profile_path, subject, contract)
