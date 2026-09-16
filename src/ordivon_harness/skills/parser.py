from __future__ import annotations

import unicodedata
from dataclasses import dataclass
_STANDARD_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


class SkillParseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedSkillFrontmatter:
    name: str
    description: str
    diagnostics: tuple[str, ...] = ()


def _split_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillParseError("SKILL.md must begin with YAML frontmatter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise SkillParseError("SKILL.md frontmatter is not terminated") from exc
    return "\n".join(lines[1:end])


def _load_yaml_mapping(frontmatter: str) -> dict:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise SkillParseError("PyYAML is required by the Skills MCP bridge runtime") from exc
    try:
        value = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        raise SkillParseError("SKILL.md frontmatter is not valid YAML") from exc
    if not isinstance(value, dict):
        raise SkillParseError("SKILL.md frontmatter must be a YAML mapping")
    return value


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SkillParseError(f"Skill frontmatter requires non-empty string {field}")
    return value.strip()


def parse_skill_frontmatter(
    text: str,
    *,
    validation_mode: str = "strict",
    expected_directory_name: str | None = None,
) -> ParsedSkillFrontmatter:
    """Parse Agent Skills YAML frontmatter.

    strict follows the published Agent Skills format and the reference validator's
    closed-field behavior. lenient is a client-side migration mode for
    legacy/client-specific Skill files; it never upgrades private fields into
    portable Agent Skills semantics.
    """

    if validation_mode not in {"strict", "lenient"}:
        raise ValueError("validation_mode must be strict or lenient")
    value = _load_yaml_mapping(_split_frontmatter(text))
    name = _require_string(value.get("name"), "name")
    description = _require_string(value.get("description"), "description")
    diagnostics: list[str] = []

    extras = sorted(str(key) for key in value if key not in _STANDARD_FIELDS)
    if extras:
        message = "non-standard Agent Skills frontmatter fields: " + ", ".join(extras)
        if validation_mode == "strict":
            raise SkillParseError(message)
        diagnostics.append(message)

    if len(name) > 128:
        raise SkillParseError("Skill name exceeds raw discovery limit")
    if name in {".", ".."} or any(
        ch in {"/", "\\", "\x00"} or unicodedata.category(ch).startswith("C") for ch in name
    ):
        raise SkillParseError("Skill name contains path-unsafe/control characters")

    normalized_name = unicodedata.normalize("NFKC", name)
    name_problems: list[str] = []
    if not (1 <= len(normalized_name) <= 64):
        name_problems.append("name must be 1-64 characters after NFKC normalization")
    if normalized_name != normalized_name.lower():
        name_problems.append("name must be lowercase")
    if normalized_name.startswith("-") or normalized_name.endswith("-"):
        name_problems.append("name cannot start or end with a hyphen")
    if "--" in normalized_name:
        name_problems.append("name cannot contain consecutive hyphens")
    if not all(ch.isalnum() or ch == "-" for ch in normalized_name):
        name_problems.append("name may contain only Unicode alphanumeric characters and hyphens")
    if (
        expected_directory_name is not None
        and unicodedata.normalize("NFKC", expected_directory_name) != normalized_name
    ):
        name_problems.append("name does not match parent directory")
    if name_problems:
        if validation_mode == "strict":
            raise SkillParseError("; ".join(name_problems))
        diagnostics.extend(name_problems)

    if len(description) > 1024:
        if validation_mode == "strict":
            raise SkillParseError("description exceeds 1024 characters")
        diagnostics.append("description exceeds 1024 characters")

    license_value = value.get("license")
    if license_value is not None and not isinstance(license_value, str):
        if validation_mode == "strict":
            raise SkillParseError("license must be a string")
        diagnostics.append("non-standard license value type ignored")

    compatibility = value.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not compatibility.strip():
            if validation_mode == "strict":
                raise SkillParseError("compatibility must be a non-empty string")
            diagnostics.append("non-standard compatibility value type ignored")
        elif len(compatibility) > 500:
            if validation_mode == "strict":
                raise SkillParseError("compatibility exceeds 500 characters")
            diagnostics.append("compatibility exceeds 500 characters")

    metadata = value.get("metadata")
    if metadata is not None:
        metadata_valid = isinstance(metadata, dict) and all(
            isinstance(key, str) and isinstance(item, str) for key, item in metadata.items()
        )
        if not metadata_valid:
            if validation_mode == "strict":
                raise SkillParseError("metadata must be a string-to-string mapping")
            diagnostics.append("non-standard metadata shape ignored")

    allowed_tools = value.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        if validation_mode == "strict":
            raise SkillParseError("allowed-tools must be a space-separated string")
        diagnostics.append("non-standard allowed-tools value type ignored")

    return ParsedSkillFrontmatter(
        name=name,
        description=description,
        diagnostics=tuple(diagnostics),
    )
