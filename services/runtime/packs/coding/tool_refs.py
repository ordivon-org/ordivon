"""Coding Pack tool references — metadata about coding tools.

This module mirrors packs/finance/tool_refs.py in structure.
It is used ONLY by pack-level code (capabilities, policy_source).
Never imported by governance/.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodingToolRef:
    """Metadata about a coding-related tool."""

    tool_id: str
    tool_name: str
    category: str  # "lint", "test", "format", "typecheck", "build"
    description: str


_CODING_TOOLS: tuple[CodingToolRef, ...] = (
    CodingToolRef(
        tool_id="ruff_check",
        tool_name="ruff check",
        category="lint",
        description="Static analysis via ruff",
    ),
    CodingToolRef(
        tool_id="ruff_format",
        tool_name="ruff format --check",
        category="format",
        description="Code style enforcement via ruff",
    ),
    CodingToolRef(
        tool_id="pytest",
        tool_name="pytest",
        category="test",
        description="Python test runner",
    ),
    CodingToolRef(
        tool_id="basedpyright",
        tool_name="basedpyright",
        category="typecheck",
        description="Static type checking",
    ),
    CodingToolRef(
        tool_id="bandit",
        tool_name="bandit",
        category="lint",
        description="Security static analysis",
    ),
    CodingToolRef(
        tool_id="pip_audit",
        tool_name="pip-audit",
        category="lint",
        description="Dependency vulnerability audit",
    ),
)


def get_coding_tool_refs() -> tuple[CodingToolRef, ...]:
    """Return the coding tool reference catalog."""
    return _CODING_TOOLS
