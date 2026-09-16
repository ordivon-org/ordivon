from __future__ import annotations

import hashlib
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

from .model import SkillRecord

MAX_SKILL_RESOURCES = 512
MAX_SKILL_BYTES = 16 * 1024 * 1024
SEP_SKILL_AUTHORITY = "ordivon"
_STANDARD_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
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
    try:
        value = yaml.safe_load(_frontmatter_bytes(body))
    except yaml.YAMLError as exc:
        raise AgentSkillsConformanceError("frontmatter is not valid YAML") from exc
    if not isinstance(value, dict):
        raise AgentSkillsConformanceError("frontmatter must be a YAML mapping")
    if any(not isinstance(key, str) for key in value):
        raise AgentSkillsConformanceError("frontmatter keys must be strings")

    extras = sorted(set(value) - _STANDARD_FRONTMATTER_FIELDS)
    if extras:
        raise AgentSkillsConformanceError(
            "non-standard top-level frontmatter fields: " + ", ".join(extras)
        )

    name = value.get("name")
    if not isinstance(name, str) or not (1 <= len(name) <= 64):
        raise AgentSkillsConformanceError("name must be a 1-64 character string")
    if not _STANDARD_NAME_RE.fullmatch(name):
        raise AgentSkillsConformanceError(
            "name must contain lowercase alphanumerics separated by single hyphens"
        )
    if skill_root.name != name:
        raise AgentSkillsConformanceError("name must match the parent directory name")

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


def skill_uri(source_id: str, skill_name: str, relative_path: str = "SKILL.md") -> str:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise AgentSkillsConformanceError("resource path must be safe and relative")
    encoded_path = "/".join(part for part in relative.parts)
    return f"skill://{SEP_SKILL_AUTHORITY}/{source_id}/{skill_name}/{encoded_path}"


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


def resource_manifest(record: SkillRecord) -> tuple[SkillResourceManifestEntry, ...]:
    root = record.skill_root
    manifest: list[SkillResourceManifestEntry] = []
    total_bytes = 0
    for candidate in sorted(root.rglob("*"), key=lambda path: path.as_posix()):
        try:
            lst = candidate.lstat()
        except OSError as exc:
            raise AgentSkillsConformanceError("cannot stat Skill package resource") from exc
        if stat.S_ISDIR(lst.st_mode):
            continue
        relative = candidate.relative_to(root).as_posix()
        if stat.S_ISLNK(lst.st_mode) or not stat.S_ISREG(lst.st_mode):
            raise AgentSkillsConformanceError(
                f"SEP-2640 static manifest rejects non-regular resource: {relative}"
            )
        if len(manifest) >= MAX_SKILL_RESOURCES:
            raise AgentSkillsConformanceError(
                f"Skill exceeds SEP-2640 {MAX_SKILL_RESOURCES}-resource limit"
            )
        try:
            data = candidate.read_bytes()
        except OSError as exc:
            raise AgentSkillsConformanceError(f"cannot read resource: {relative}") from exc
        total_bytes += len(data)
        if total_bytes > MAX_SKILL_BYTES:
            raise AgentSkillsConformanceError(
                f"Skill exceeds SEP-2640 {MAX_SKILL_BYTES}-byte limit"
            )
        manifest.append(
            SkillResourceManifestEntry(
                uri=skill_uri(record.source_id, record.name, relative),
                digest=_sha256(data),
                size=len(data),
            )
        )
    if not any(item.uri.endswith("/SKILL.md") for item in manifest):
        raise AgentSkillsConformanceError("Skill manifest must include SKILL.md")
    return tuple(manifest)


def skill_entry(record: SkillRecord) -> Sep2640SkillEntry:
    frontmatter = parse_standard_frontmatter(record.skill_root)
    if frontmatter["name"] != record.name:
        raise AgentSkillsConformanceError("catalog name differs from standard frontmatter name")
    return Sep2640SkillEntry(
        uri=skill_uri(record.source_id, record.name),
        frontmatter=frontmatter,
        resources=resource_manifest(record),
    )


def manifest_contains(entry: Sep2640SkillEntry, uri: str) -> bool:
    return any(resource.uri == uri for resource in entry.resources)
