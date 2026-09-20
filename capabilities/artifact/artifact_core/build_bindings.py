from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BuildCapabilityBinding:
    artifact_class: str
    source_kind: str
    adapter_id: str
    capability_id: str
    builder_id: str
    build_type: str


class BuildCapabilityBindingRegistry:
    """Data authority for legacy-v1 build selection.

    The registry decides which capability may satisfy an artifact-class/source-kind pair.
    It does not execute the provider and does not judge artifact acceptance.
    """

    def __init__(self, artifact_root: Path) -> None:
        self.artifact_root = artifact_root.resolve()
        self.registry_path = self.artifact_root / "build-capability-bindings-v1.json"
        value = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if value.get("schemaVersion") != 1 or value.get("kind") != "artifact-build-capability-binding-registry":
            raise RuntimeError("invalid Artifact build capability binding registry identity")
        self._entries: dict[tuple[str, str], BuildCapabilityBinding] = {}
        for item in value.get("bindings", []):
            binding = BuildCapabilityBinding(
                artifact_class=str(item["artifactClass"]),
                source_kind=str(item["sourceKind"]),
                adapter_id=str(item["adapterId"]),
                capability_id=str(item["capabilityId"]),
                builder_id=str(item["builderId"]),
                build_type=str(item["buildType"]),
            )
            key = (binding.artifact_class, binding.source_kind)
            if key in self._entries:
                raise RuntimeError(f"duplicate Artifact build capability binding: {key}")
            self._entries[key] = binding

    def resolve(self, artifact_class: str, source_kind: str) -> BuildCapabilityBinding:
        try:
            return self._entries[(artifact_class, source_kind)]
        except KeyError as error:
            raise KeyError(
                f"no Artifact build capability binding for artifactClass={artifact_class!r}, source.kind={source_kind!r}"
            ) from error

    def list(self) -> list[BuildCapabilityBinding]:
        return [self._entries[key] for key in sorted(self._entries)]
