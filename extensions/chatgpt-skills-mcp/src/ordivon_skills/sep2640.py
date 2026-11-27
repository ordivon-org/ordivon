from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from .catalog import SkillCatalogError, _package_revision, _package_snapshot
from .model import SkillRecord
from .parser import SkillParseError, _load_yaml_mapping

SEP_SKILL_AUTHORITY = "ordivon"
_STANDARD_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


class AgentSkillsConformanceError(ValueError):
    """The source package cannot be advertised as an Agent Skills standard Skill."""


@dataclass(frozen=True, slots=True)
class SkillResourceManifestEntry:
    uri: str
    digest: str
    size: int

    def value(self) -> dict[str, object]:
        return {"uri": self.uri, "digest": self.digest, "size": self.size}


@dataclass(frozen=True, slots=True)
class Sep2640SkillEntry:
    uri: str
    frontmatter: dict[str, object]
    resources: tuple[SkillResourceManifestEntry, ...]

    def value(self) -> dict[str, object]:
        return {
            "uri": self.uri,
            "frontmatter": self.frontmatter,
            "resources": [resource.value() for resource in self.resources],
        }


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _frontmatter_bytes(skill_md: bytes) -> bytes:
    try:
        text = skill_md.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AgentSkillsConformanceError("SKILL.md must be UTF-8") from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AgentSkillsConformanceError("SKILL.md must begin with YAML frontmatter")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]).encode("utf-8")
    raise AgentSkillsConformanceError("SKILL.md frontmatter is not terminated")


def _validate_standard_name(name: object, parent_name: str) -> str:
    if not isinstance(name, str) or not (1 <= len(name) <= 64):
        raise AgentSkillsConformanceError("name must be a 1-64 character string")
    if name != name.lower():
        raise AgentSkillsConformanceError("name must use lowercase Unicode alphanumeric characters")
    if name.startswith("-") or name.endswith("-"):
        raise AgentSkillsConformanceError("name cannot start or end with a hyphen")
    if "--" in name:
        raise AgentSkillsConformanceError("name cannot contain consecutive hyphens")
    if not all(character.isalnum() or character == "-" for character in name):
        raise AgentSkillsConformanceError(
            "name may contain only Unicode alphanumeric characters and hyphens"
        )
    if parent_name != name:
        raise AgentSkillsConformanceError("name must match the parent directory name")
    return name


def _parse_standard_frontmatter_bytes(
    body: bytes,
    *,
    parent_name: str,
) -> dict[str, object]:
    try:
        value = _load_yaml_mapping(_frontmatter_bytes(body).decode("utf-8"))
    except SkillParseError as exc:
        raise AgentSkillsConformanceError(str(exc)) from exc
    if not isinstance(value, dict):
        raise AgentSkillsConformanceError("frontmatter must be a YAML mapping")
    if any(not isinstance(key, str) for key in value):
        raise AgentSkillsConformanceError("frontmatter keys must be strings")

    extras = sorted(set(value) - _STANDARD_FRONTMATTER_FIELDS)
    if extras:
        raise AgentSkillsConformanceError(
            "non-standard top-level frontmatter fields: " + ", ".join(extras)
        )

    _validate_standard_name(value.get("name"), parent_name)

    description = value.get("description")
    if not isinstance(description, str) or not (1 <= len(description) <= 1024):
        raise AgentSkillsConformanceError("description must be a 1-1024 character string")

    if "license" in value and not isinstance(value["license"], str):
        raise AgentSkillsConformanceError("license must be a string")
    if "compatibility" in value:
        compatibility = value["compatibility"]
        if not isinstance(compatibility, str) or not (1 <= len(compatibility) <= 500):
            raise AgentSkillsConformanceError(
                "compatibility must be a 1-500 character string"
            )
    if "metadata" in value:
        metadata = value["metadata"]
        if not isinstance(metadata, dict) or any(
            not isinstance(key, str) or not isinstance(item, str)
            for key, item in (metadata.items() if isinstance(metadata, dict) else ())
        ):
            raise AgentSkillsConformanceError("metadata must be a string-to-string mapping")
    if "allowed-tools" in value and not isinstance(value["allowed-tools"], str):
        raise AgentSkillsConformanceError("allowed-tools must be a space-separated string")

    return dict(value)


def parse_standard_frontmatter(skill_root: Path) -> dict[str, object]:
    """Parse and enforce the portable Agent Skills frontmatter contract.

    Product/Harness dialect fields stay outside this transport projection. This is
    intentionally stricter than Ordivon's raw discovery parser because SEP-2640
    requires every advertised Skill to conform to the Agent Skills specification.
    """

    skill_md = skill_root / "SKILL.md"
    try:
        body = skill_md.read_bytes()
    except OSError as exc:
        raise AgentSkillsConformanceError("cannot read SKILL.md") from exc
    return _parse_standard_frontmatter_bytes(body, parent_name=skill_root.name)


def skill_uri(source_id: str, skill_name: str, relative_path: str = "SKILL.md") -> str:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise AgentSkillsConformanceError("resource path must be safe and relative")
    encoded_source = quote(source_id, safe="-._~")
    encoded_name = quote(skill_name, safe="-._~")
    encoded_path = "/".join(quote(part, safe="-._~") for part in relative.parts)
    return f"skill://{SEP_SKILL_AUTHORITY}/{encoded_source}/{encoded_name}/{encoded_path}"


def parse_skill_uri(uri: str) -> tuple[str, str, str]:
    split = urlsplit(uri)
    if split.scheme != "skill" or split.netloc != SEP_SKILL_AUTHORITY:
        raise AgentSkillsConformanceError("URI is not an Ordivon SEP-2640 Skill URI")
    if split.query or split.fragment:
        raise AgentSkillsConformanceError("Skill URI cannot contain query or fragment")
    raw_parts = [unquote(part) for part in split.path.split("/") if part]
    if len(raw_parts) < 3:
        raise AgentSkillsConformanceError("Skill URI path is incomplete")
    source_id, skill_name, *resource_parts = raw_parts
    if any(part in {".", ".."} or "/" in part or "\\" in part for part in raw_parts):
        raise AgentSkillsConformanceError("Skill URI contains unsafe path segments")
    resource_path = "/".join(resource_parts)
    if not resource_path:
        raise AgentSkillsConformanceError("Skill URI must name a resource")
    return source_id, skill_name, resource_path


def _resource_manifest_from_inventory(
    record: SkillRecord,
    inventory: tuple[dict[str, object], ...],
) -> tuple[SkillResourceManifestEntry, ...]:
    manifest = tuple(
        SkillResourceManifestEntry(
            uri=skill_uri(record.source_id, record.name, str(item["path"])),
            digest=str(item["sha256"]),
            size=int(item["size"]),
        )
        for item in inventory
    )
    if not any(item.uri.endswith("/SKILL.md") for item in manifest):
        raise AgentSkillsConformanceError("Skill manifest must include SKILL.md")
    return manifest


def resource_manifest(record: SkillRecord) -> tuple[SkillResourceManifestEntry, ...]:
    try:
        revision, inventory, _ = _package_snapshot(record.skill_root)
    except (SkillCatalogError, OSError) as exc:
        raise AgentSkillsConformanceError("cannot verify admitted Skill package") from exc
    if revision != record.package_revision:
        raise AgentSkillsConformanceError("Skill package differs from admitted scan")
    return _resource_manifest_from_inventory(record, inventory)


def skill_entry(record: SkillRecord) -> Sep2640SkillEntry:
    # A fresh digest of live files cannot replace the source package whose
    # scan/trust verdict admitted this record. Build every advertised field from
    # one bounded package observation, then reject mutation after that snapshot.
    try:
        revision, inventory, package_bytes = _package_snapshot(record.skill_root)
        if revision != record.package_revision:
            raise AgentSkillsConformanceError("Skill package differs from admitted scan")
        try:
            instruction_key = record.main_resource.relative_to(record.skill_root).as_posix()
            instruction = package_bytes[instruction_key]
        except (KeyError, ValueError) as exc:
            raise AgentSkillsConformanceError("SKILL.md differs from admitted scan") from exc
        if _sha256(instruction) != record.instruction_digest:
            raise AgentSkillsConformanceError("SKILL.md differs from admitted scan")
        frontmatter = _parse_standard_frontmatter_bytes(
            instruction,
            parent_name=record.skill_root.name,
        )
        if frontmatter["name"] != record.name:
            raise AgentSkillsConformanceError("catalog name differs from standard frontmatter name")
        resources = _resource_manifest_from_inventory(record, inventory)
        if _package_revision(record.skill_root) != record.package_revision:
            raise AgentSkillsConformanceError("Skill package changed after admitted scan")
    except (SkillCatalogError, OSError) as exc:
        raise AgentSkillsConformanceError("cannot verify admitted Skill package") from exc
    return Sep2640SkillEntry(
        uri=skill_uri(record.source_id, record.name),
        frontmatter=frontmatter,
        resources=resources,
    )


def manifest_contains(entry: Sep2640SkillEntry, uri: str) -> bool:
    return any(resource.uri == uri for resource in entry.resources)
