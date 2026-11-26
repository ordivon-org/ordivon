"""Structural cognition sections using the existing CommonMark parser."""
from __future__ import annotations

from dataclasses import dataclass

from markdown_it import MarkdownIt

COGNITION_SECTIONS = ("FRAME", "BIND", "EXPRESS", "RENDER", "AUDIT", "DECIDE", "LEARNING")


@dataclass(frozen=True, slots=True)
class CognitionSection:
    title: str
    body: str


def cognition_sections(text: str) -> tuple[CognitionSection, ...]:
    """Read top-level H2 sections; quoted, nested and fenced text is not a stage."""
    tokens = MarkdownIt("commonmark").parse(text)
    lines = text.splitlines()
    headings = [
        (token.tag, tokens[index + 1].content, token.map)
        for index, token in enumerate(tokens)
        if token.type == "heading_open" and token.level == 0
        and token.tag in ("h1", "h2") and token.map is not None
    ]
    sections = []
    for index, (tag, title, span) in enumerate(headings):
        if tag != "h2":
            continue
        assert span is not None
        end = len(lines)
        if index + 1 < len(headings):
            next_span = headings[index + 1][2]
            assert next_span is not None
            end = next_span[0]
        sections.append(CognitionSection(title, "\n".join(lines[span[1]:end]).strip()))
    return tuple(sections)


def extract_learning(text: str) -> str | None:
    selected = [section.body for section in cognition_sections(text) if section.title == "LEARNING"]
    return selected[0] or None if len(selected) == 1 else None
