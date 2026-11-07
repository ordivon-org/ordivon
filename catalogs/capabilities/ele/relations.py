"""Derive *cited-source* edges from committed ELE studies, never adoption claims.

Only explicit Markdown links / exact code-span Git paths and structured JSON
references produce edges. Every edge records its source location. A link is not
proof that a tool is installed, a consumer has switched or a LEGO is admitted.
"""

from __future__ import annotations

import json
import posixpath
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

MARKDOWN_LINK = re.compile(r"\[[^\]\n]+\]\(([^)\s]+)(?:\s+[^)]*)?\)")
CODE_PATH = re.compile(
    r"[\x60]((?:\.agents|catalogs|capabilities|domains|platform|profiles|services|packages|studies|tools|docs)/[^\x60\s]+)[\x60]"
)
ROOT_PREFIXES = (
    ".agents/",
    "catalogs/",
    "capabilities/",
    "domains/",
    "platform/",
    "profiles/",
    "services/",
    "packages/",
    "studies/",
    "tools/",
    "docs/",
)


@dataclass(frozen=True)
class Reference:
    study_id: str
    sha256: str
    ordinal: int
    section_ordinal: int
    relation: str
    locator: str
    target: str
    target_study_id: str | None


def tracked_files(root: Path) -> set[str]:
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached"], cwd=root)
    return {value.decode("utf-8") for value in raw.split(b"\0") if value}


def _target(
    raw: str,
    source: str,
    tracked: set[str],
) -> tuple[str, str] | None:
    value = unquote(raw.strip().strip("<>")).split("#", 1)[0]
    if value.startswith(("https://", "http://")):
        parsed = urlsplit(value)
        if parsed.hostname and parsed.scheme in ("https", "http"):
            return ("external_source", value)
        return None
    if not value or value.startswith(("/", "//")):
        return None
    if value.startswith(ROOT_PREFIXES):
        path = posixpath.normpath(value)
    else:
        path = posixpath.normpath(posixpath.join(posixpath.dirname(source), value))
    if path in tracked:
        return ("git_source", path)
    return None


def references_for(
    study: object, sources: dict[str, str], tracked: set[str]
) -> tuple[Reference, ...]:
    """Scan only explicit source locators; all semantic promotion is Owner-owned."""
    refs: list[Reference] = []
    source = study.source_path
    parts = study.sections

    def record(raw: str, locator: str, section: int, context: str) -> None:
        destination = _target(raw, source, tracked)
        if destination is None:
            return
        reference_kind, target = destination
        if context == "consumerSources" and reference_kind == "git_source":
            reference_kind = "consumer_source_reference"
        if context == "repository" and reference_kind == "external_source":
            reference_kind = "upstream_repository_reference"
        refs.append(
            Reference(
                study.study_id,
                study.sha256,
                len(refs),
                section,
                reference_kind,
                locator,
                target,
                sources.get(target),
            )
        )

    if source.endswith(".json"):
        doc = json.loads(study.content)
        if not isinstance(doc, dict):
            return ()
        sections = {part.heading: part.ordinal for part in parts}

        def descend(value: object, path: str, section: int, key: str) -> None:
            if isinstance(value, dict):
                for child_key, item in value.items():
                    child_section = (
                        sections.get(child_key, section) if path == "$" else section
                    )
                    descend(item, f"{path}.{child_key}", child_section, child_key)
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    child_section = section
                    if key == "observations" and path == "$.observations":
                        child_section = next(
                            (
                                part.ordinal
                                for part in parts
                                if part.heading.startswith(f"observations[{index}]")
                            ),
                            section,
                        )
                    descend(item, f"{path}[{index}]", child_section, key)
            elif isinstance(value, str):
                record(value, path, section, key)

        descend(doc, "$", 0, "")
    else:
        for part in parts:
            for matched in MARKDOWN_LINK.finditer(part.body):
                line = part.start_line + part.body.count("\n", 0, matched.start())
                record(matched.group(1), f"line:{line}", part.ordinal, "link")
            for matched in CODE_PATH.finditer(part.body):
                line = part.start_line + part.body.count("\n", 0, matched.start())
                record(matched.group(1), f"line:{line}", part.ordinal, "code")

    return tuple(refs)


def all_references(
    studies: list[object], root: Path
) -> dict[str, tuple[Reference, ...]]:
    sources = {study.source_path: study.study_id for study in studies}
    tracked = tracked_files(root)
    return {
        study.study_id: references_for(study, sources, tracked) for study in studies
    }
