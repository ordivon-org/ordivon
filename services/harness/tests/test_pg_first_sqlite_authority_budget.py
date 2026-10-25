"""Harness H04 PG-first migration budget, scoped to direct sqlite3 source imports.

This is a source-level CLOSED-WORLD intake gate, not live database migration.
An existing SQLite store is not allowed to disappear unless its own consumers
and durable recovery/replay are migrated. No parallel registry is created.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OWNER_SOURCE = (ROOT / "scripts", ROOT / "src")

# Existing, independently consumed or test/acceptance SQLite code.
# Shrink this set as PG conversions land. Do not expand it for new stores.
KNOWN_LEGACY_SQLITE_SOURCES = frozenset(
    {
        "scripts/agent_automation_browserless.py",
        "scripts/agent_automation_ledger_reconcile.py",
        "scripts/agent_automation_release.py",
        "scripts/browser_security_witness_source.py",
        "scripts/campaign_materialization.py",
        "scripts/cft_human_session.py",
        "scripts/harness_p0_scale_acceptance.py",
        "scripts/materialization_reconciliation_archive.py",
        "scripts/playwright_browserless_turn_once.py",
        "scripts/sqlite_conversation_binding.py",
        "scripts/sqlite_conversation_materializer.py",
        "scripts/sqlite_wake_turn_map.py",
        "src/ordivon_harness/sqlite_store.py",
        "src/ordivon_harness/store_ops.py",
    }
)


def direct_sqlite_imports(
    owner: Path, *, sources: tuple[str, ...] = ("scripts", "src")
) -> frozenset[str]:
    found: set[str] = set()
    for directory in sources:
        for source in (owner / directory).rglob("*.py"):
            if any(p in {".venv", "build", "tests", "__pycache__"} for p in source.parts):
                continue
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
            if any(
                (
                    isinstance(node, ast.Import)
                    and any(name.name == "sqlite3" for name in node.names)
                )
                or (isinstance(node, ast.ImportFrom) and node.module == "sqlite3")
                for node in ast.walk(tree)
            ):
                found.add(source.relative_to(owner).as_posix())
    return frozenset(found)


def require_no_new_sqlite_direct_imports(observed: frozenset[str]) -> None:
    additions = sorted(observed - KNOWN_LEGACY_SQLITE_SOURCES)
    if additions:
        raise ValueError(
            "PostgreSQL-first H04: new direct SQLite source requires PG consumer "
            "migration instead: " + ", ".join(additions)
        )


def test_h04_postgres_first_prevents_new_sqlite_owner_sources() -> None:
    observed = direct_sqlite_imports(ROOT)
    require_no_new_sqlite_direct_imports(observed)
    assert observed == KNOWN_LEGACY_SQLITE_SOURCES, (
        "Legacy SQLite authority inventory was reduced; remove migrated entries "
        "from this gate instead of retaining stale allowances."
    )


def test_unregistered_sqlite_import_is_rejected_not_silently_added(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "scripts" / "new_durable_state.py").write_text(
        "from sqlite3 import connect\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="new direct SQLite source"):
        require_no_new_sqlite_direct_imports(direct_sqlite_imports(tmp_path))


def test_current_legacy_set_can_be_reduced_without_a_migration_sidecar() -> None:
    reduced = KNOWN_LEGACY_SQLITE_SOURCES - {"scripts/sqlite_wake_turn_map.py"}
    require_no_new_sqlite_direct_imports(reduced)
