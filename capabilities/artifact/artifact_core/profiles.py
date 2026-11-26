from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from .contracts import sha256_file
from .json_validation import load_json, load_json_with_digest
from .profile_refinement import assess_v1_v2_refinement


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


type IndexedProfile = tuple[Path, dict[str, Any], str]


class ProfileRegistry:
    """Strict, source-committed canonical Profile registry.

    The v1 examples directory also contains request/source fixtures. Only
    identified Profile candidates enter the v1 authority. The v2 directory
    contains Profiles exclusively and is never silently filtered. A registry
    is an immutable index snapshot: changed indexed bytes fail at resolve.
    """

    def __init__(self, artifact_root: Path) -> None:
        self.artifact_root = artifact_root.resolve()
        self.production_root = self.artifact_root / "examples"
        self.canonical_root = self.artifact_root / "shadow-v2/examples"
        schema_root = Path(__file__).resolve().parents[1] / "artifact-delivery"
        self._schema_v1 = self._validator(schema_root / "profile-v1.schema.json")
        self._schema_v2 = self._validator(schema_root / "profile-v2.shadow.schema.json")
        self._canonical = self._index_profiles(self.canonical_root, version=2)
        self._production = self._index_profiles(self.production_root, version=1)
        unknown = sorted(self._production.keys() - self._canonical.keys())
        if unknown:
            raise RuntimeError(f"production Profiles lack canonical v2 counterparts: {unknown}")

    @staticmethod
    def _validator(schema_path: Path) -> jsonschema.Draft202012Validator:
        schema = load_json(schema_path)
        jsonschema.Draft202012Validator.check_schema(schema)
        return jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )

    def _index_profiles(
        self, root: Path, *, version: int
    ) -> dict[str, IndexedProfile]:
        result: dict[str, IndexedProfile] = {}
        validator = self._schema_v2 if version == 2 else self._schema_v1
        for path in sorted(root.glob("*.json")):
            try:
                value, digest = load_json_with_digest(path)
            except (OSError, ValueError, UnicodeError) as error:
                raise RuntimeError(f"invalid Artifact JSON authority: {path}: {error}") from error
            if version == 1 and isinstance(value, dict) and (
                value.get("profileVersion") is None
                and "artifactClass" not in value
                and "primaryOutput" not in value
                and "id" not in value
            ):
                # The production examples directory also contains requests,
                # source fixtures, etc. They remain outside Profile authority.
                continue
            if not isinstance(value, dict):
                raise RuntimeError(f"Artifact Profile is not an object: {path}")
            if value.get("profileVersion") != version:
                raise RuntimeError(f"Artifact Profile version mismatch: {path}")
            instance = dict(value)
            if version == 1:
                # Reuse the existing v1 validator's established $schema
                # annotation treatment; it is not part of the Profile fields.
                instance.pop("$schema", None)
            failures = sorted(
                validator.iter_errors(instance),
                key=lambda error: tuple(str(part) for part in error.absolute_path),
            )
            if failures:
                raise RuntimeError(
                    f"Artifact Profile Schema violation: {path}: {failures[0].message}"
                )
            profile_id = value["id"]
            expected_stem = f"{profile_id}-v2" if version == 2 else profile_id
            if path.stem != expected_stem:
                raise RuntimeError(
                    f"Artifact Profile filename and identity disagree: {path}"
                )
            if profile_id in result:
                raise RuntimeError(f"duplicate Artifact Profile id in {root}: {profile_id}")
            result[profile_id] = (path.resolve(), value, digest)
        return result

    def ids(self) -> list[str]:
        return sorted(self._canonical)

    def resolve(self, profile_id: str) -> ProfileRecord:
        entry = self._canonical.get(profile_id)
        if entry is None:
            raise KeyError(f"unknown Artifact profile: {profile_id}")
        canonical_path, canonical, canonical_sha = entry
        if sha256_file(canonical_path) != canonical_sha:
            raise RuntimeError(f"canonical Profile changed after registry indexing: {profile_id}")

        family = canonical["classification"]["family"]
        production = self._production.get(profile_id)
        if production is not None:
            source_path, source, source_sha = production
            if sha256_file(source_path) != source_sha:
                raise RuntimeError(
                    f"production Profile changed after registry indexing: {profile_id}"
                )
            refinement = assess_v1_v2_refinement(source, canonical)
            if not refinement["complete"]:
                raise RuntimeError(
                    f"Profile v1/v2 refinement mismatch for {profile_id}: "
                    f"{refinement['mismatches']}"
                )
            source_kind = "production-v1-adapted"
        else:
            source_path, source_sha = canonical_path, canonical_sha
            source_kind = "native-v2-shadow"

        return ProfileRecord(
            profile_id=profile_id,
            family=family,
            source_kind=source_kind,
            source_path=source_path,
            canonical_path=canonical_path,
            canonical=deepcopy(canonical),
            source_sha256=source_sha,
            canonical_sha256=canonical_sha,
        )
