"""Fail closed on SQLite transaction contexts mistaken for connection lifetime."""

from __future__ import annotations

import ast
from pathlib import Path


def test_sqlite_connect_cannot_be_used_as_closing_context() -> None:
    """sqlite3.Connection.__exit__ commits/rolls back; only close() releases it."""
    violations: list[str] = []
    owner_root = Path(__file__).resolve().parents[1]
    for path in sorted(
        file
        for subtree in ("src", "scripts", "tests")
        for file in (owner_root / subtree).rglob("*.py")
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.With):
                continue
            for item in node.items:
                call = item.context_expr
                if not isinstance(call, ast.Call):
                    continue
                fn = call.func
                if (
                    isinstance(fn, ast.Attribute)
                    and fn.attr == "connect"
                    and isinstance(fn.value, ast.Name)
                    and fn.value.id == "sqlite3"
                ):
                    violations.append(f"{path.relative_to(owner_root)}:{node.lineno}")
    assert not violations, (
        "sqlite3.connect is a transaction context, not a closing context: " + ", ".join(violations)
    )
