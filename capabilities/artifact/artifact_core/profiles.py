from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import sha256_file


@dataclass(frozen=True)
class ProfileRecord:
    profile_id: str
    family: str
    source_kind: str
    source_path: Path
    canonical_path: Path
    canonical: dict[str, Any]
    source_sha256: str
    canonical_sha256: str


class ProfileRegistry:
    """Resolve current Artifact profiles through one canonical v2-shaped view.

    The registry deliberately does not depend on the generated profile-v2 mapping
    manifest. Current profile files are the authority: production v1 files remain the
    source bytes for existing Office/Web paths, while the v2 projection is the common
    semantic view. Standards-first profiles use their v2 bytes directly.
    """

    def __init__(self, artifact_root: Path) -> None:
        self.artifact_root = artifact_root.resolve()
        self.production_root = self.artifact_root / "examples"
        self.canonical_root = self.artifact_root / "shadow-v2/examples"
        self._canonical = self._index_profiles(self.canonical_root, version=2)
        self._production = self._index_profiles(self.production_root, version=1)

    @staticmethod
    def _load_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def _index_profiles(self, root: Path, *, version: int) -> dict[str, tuple[Path, dict[str, Any]]]:
        result: dict[str, tuple[Path, dict[str, Any]]] = {}
        for path in sorted(root.glob("*.json")):
            try:
                value = self._load_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(value, dict) or value.get("profileVersion") != version:
                continue
            profile_id = value.get("id")
            if not isinstance(profile_id, str) or not profile_id:
                continue
            if profile_id in result:
                raise RuntimeError(f"duplicate Artifact profile id in {root}: {profile_id}")
            result[profile_id] = (path.resolve(), value)
        return result

    def ids(self) -> list[str]:
        return sorted(self._canonical)

    def resolve(self, profile_id: str) -> ProfileRecord:
        canonical_entry = self._canonical.get(profile_id)
        if canonical_entry is None:
            raise KeyError(f"unknown Artifact profile: {profile_id}")
        canonical_path, canonical = canonical_entry
        family = canonical.get("classification", {}).get("family")
        if not isinstance(family, str) or not family:
            raise RuntimeError(f"canonical profile family is absent: {profile_id}")

        production_entry = self._production.get(profile_id)
        if production_entry is not None:
            source_path, _ = production_entry
            source_kind = "production-v1-adapted"
        else:
            source_path = canonical_path
            source_kind = "native-v2-shadow"

        return ProfileRecord(
            profile_id=profile_id,
            family=family,
            source_kind=source_kind,
            source_path=source_path,
            canonical_path=canonical_path,
            canonical=canonical,
            source_sha256=sha256_file(source_path),
            canonical_sha256=sha256_file(canonical_path),
        )
