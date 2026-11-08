from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import sha256_file
from .json_validation import load_json_with_digest


@dataclass(frozen=True)
class Entrypoint:
    module: str
    callable: str


@dataclass(frozen=True)
class CapabilityBinding:
    profile_id: str
    operation: str
    capability_id: str
    entrypoint: Entrypoint
    object_contract_required: bool
    require_claim_results: bool
    standing: str
    standing_path: Path
    standing_sha256: str


class CapabilityBindingRegistry:
    """Data-driven profile/operation -> capability/provider binding registry."""

    def __init__(self, artifact_root: Path) -> None:
        self.artifact_root = artifact_root.resolve()
        self.repo_root = self.artifact_root.parent
        self.registry_path = self.artifact_root / "capability-bindings-v1.json"
        value, self._registry_sha256 = load_json_with_digest(self.registry_path)
        if not isinstance(value, dict):
            raise RuntimeError("Artifact capability binding registry is not an object")
        if value.get("schemaVersion") != 1 or value.get("kind") != "artifact-capability-binding-registry":
            raise RuntimeError("invalid Artifact capability binding registry identity")
        entries = value.get("bindings", [])
        self._entries: dict[tuple[str, str], dict[str, Any]] = {}
        for item in entries:
            key = (str(item["profileId"]), str(item["operation"]))
            if key in self._entries:
                raise RuntimeError(f"duplicate Artifact capability binding: {key}")
            self._entries[key] = item

    def _require_current_authority(self) -> None:
        if sha256_file(self.registry_path) != self._registry_sha256:
            raise RuntimeError("Artifact capability binding registry changed after indexing")

    def list(self, *, operation: str | None = None) -> list[CapabilityBinding]:
        self._require_current_authority()
        rows = []
        for profile_id, op in sorted(self._entries):
            if operation is None or operation == op:
                rows.append(self.resolve(profile_id, op))
        return rows

    def resolve(self, profile_id: str, operation: str) -> CapabilityBinding:
        self._require_current_authority()
        item = self._entries.get((profile_id, operation))
        if item is None:
            raise KeyError(f"no Artifact capability binding for {profile_id}:{operation}")
        standing_path = (self.repo_root / str(item["standingRef"])).resolve()
        if not standing_path.is_file():
            raise RuntimeError(f"capability standing record is absent: {standing_path}")
        standing_value, standing_sha = load_json_with_digest(standing_path)
        if not isinstance(standing_value, dict):
            raise RuntimeError(f"capability standing record is not an object: {standing_path}")
        standing = str(standing_value.get("status", ""))
        required = str(item.get("requiredStanding", "LOCAL_LIVE_PROVEN"))
        if standing != required:
            raise RuntimeError(
                f"capability binding standing mismatch for {profile_id}:{operation}: {standing!r} != {required!r}"
            )
        entrypoint = item.get("entrypoint", {})
        return CapabilityBinding(
            profile_id=profile_id,
            operation=operation,
            capability_id=str(item["capabilityId"]),
            entrypoint=Entrypoint(module=str(entrypoint["module"]), callable=str(entrypoint["callable"])),
            object_contract_required=bool(item.get("objectContractRequired", False)),
            require_claim_results=item.get("requireClaimResults") is True,
            standing=standing,
            standing_path=standing_path,
            standing_sha256=standing_sha,
        )
