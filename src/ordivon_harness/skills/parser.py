from __future__ import annotations

import json
import re
from dataclasses import dataclass

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:[ \t]*(.*))?$")
_BLOCK_SCALAR_RE = re.compile(r"^[>|][+-]?[1-9]?$|^[>|][1-9][+-]?$")


class SkillParseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedSkillFrontmatter:
    name: str
    description: str


def _decode_scalar(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SkillParseError("invalid double-quoted frontmatter scalar") from exc
        if not isinstance(value, str):
            raise SkillParseError("frontmatter scalar must decode to string")
        return value
    if raw.startswith("'"):
        if len(raw) < 2 or not raw.endswith("'"):
            raise SkillParseError("invalid single-quoted frontmatter scalar")
        return raw[1:-1].replace("''", "'")
    return raw


def _read_block(lines: list[str], start: int, indicator: str) -> tuple[str, int]:
    block: list[str] = []
    index = start
    indent: int | None = None
    while index < len(lines):
        line = lines[index]
        if line.strip() == "":
            if indent is not None:
                block.append("")
            index += 1
            continue
        leading = len(line) - len(line.lstrip(" "))
        if leading == 0:
            break
        if indent is None:
            indent = leading
        if leading < indent:
            break
        block.append(line[indent:])
        index += 1
    if indicator.startswith(">"):
        value = " ".join(part.strip() for part in block).strip()
    else:
        value = "\n".join(block).strip()
    return value, index


def parse_skill_frontmatter(text: str) -> ParsedSkillFrontmatter:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillParseError("SKILL.md must begin with YAML frontmatter")

    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise SkillParseError("SKILL.md frontmatter is not terminated") from exc

    frontmatter = lines[1:end]
    selected: dict[str, str] = {}
    index = 0
    while index < len(frontmatter):
        line = frontmatter[index]
        if line.startswith((" ", "\t")) or not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        match = _KEY_RE.match(line)
        if not match:
            index += 1
            continue
        key, raw = match.group(1), (match.group(2) or "")
        if key not in {"name", "description"}:
            index += 1
            continue
        if _BLOCK_SCALAR_RE.match(raw.strip()):
            value, next_index = _read_block(frontmatter, index + 1, raw.strip())
            selected[key] = value
            index = next_index
            continue
        selected[key] = _decode_scalar(raw)
        index += 1

    name = selected.get("name", "").strip()
    description = selected.get("description", "").strip()
    if not name:
        raise SkillParseError("Skill frontmatter requires name")
    if not _NAME_RE.fullmatch(name):
        raise SkillParseError("Skill name contains unsupported characters")
    if not description:
        raise SkillParseError("Skill frontmatter requires description")
    return ParsedSkillFrontmatter(name=name, description=description)
