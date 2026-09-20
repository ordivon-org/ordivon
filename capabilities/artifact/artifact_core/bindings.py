from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import sha256_file


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
    standing: str
    standing_path: Path
    standing_sha256: str


class CapabilityBindingRegistry:
    """Data-driven profile/operation -> capability/provider binding registry."""

    def __init__(self, artifact_root: Path) -> None:
        self.artifact_root = artifact_root.resolve()
        self.repo_root = self.artifact_root.parent
        self.registry_path = self.artifact_root / "capability-bindings-v1.json"
        value = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if value.get("schemaVersion") != 1 or value.get("kind") != "artifact-capability-binding-registry":
            raise RuntimeError("invalid Artifact capability binding registry identity")
        entries = value.get("bindings", [])
        self._entries: dict[tuple[str, str], dict[str, Any]] = {}
        for item in entries:
            key = (str(item["profileId"]), str(item["operation"]))
            if key in self._entries:
                raise RuntimeError(f"duplicate Artifact capability binding: {key}")
            self._entries[key] = item

    def list(self, *, operation: str | None = None) -> list[CapabilityBinding]:
        rows = []
        for profile_id, op in sorted(self._entries):
            if operation is None or operation == op:
                rows.append(self.resolve(profile_id, op))
        return rows

    def resolve(self, profile_id: str, operation: str) -> CapabilityBinding:
        item = self._entries.get((profile_id, operation))
        if item is None:
            raise KeyError(f"no Artifact capability binding for {profile_id}:{operation}")
        standing_path = (self.repo_root / str(item["standingRef"])).resolve()
        if not standing_path.is_file():
            raise RuntimeError(f"capability standing record is absent: {standing_path}")
        standing_value = json.loads(standing_path.read_text(encoding="utf-8"))
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
            standing=standing,
            standing_path=standing_path,
            standing_sha256=sha256_file(standing_path),
        )
