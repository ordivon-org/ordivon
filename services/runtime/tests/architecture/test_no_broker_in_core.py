"""Architecture invariant: no broker/trade/order business references in Core modules.

CORE_DIRS = ["governance", "state", "capabilities", "execution", "shared", "domains"]
FORBIDDEN = business-logic patterns only (not documentation or SQL ordering).

This test walks all .py files in Core directories, reads their text,
and asserts that none import or use broker/trade/order business logic.
Files under __pycache__ and migrations directories are skipped.
"""

import re
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CORE_DIRS = ["governance", "state", "capabilities", "execution", "shared", "domains"]

# Patterns that indicate broker/trade/order *business logic* leaking into Core.
# Avoid false positives: SQL "order_by", documentation "Does NOT connect to broker", etc.
FORBIDDEN = [
    (r"from\s+packs\..*import.*broker", "broker pack import in Core"),
    (r"import\s+broker", "broker module import in Core"),
    (r"place_order\(", "place_order call in Core"),
    (r"execute_trade\(", "execute_trade call in Core"),
    (r"from\s+packs\..*import.*trade", "trade pack import in Core"),
    (r"from\s+packs\..*import.*exchange", "exchange pack import in Core"),
]

SKIP_DIRS = {"__pycache__", "migrations"}

# Files known to contain "broker" in architectural documentation or metadata only
# (not actual broker business logic imports)
ALLOWED_FILES = {
    "governance_engine/policy_source.py",  # ADR-006 tool namespace metadata
    "state/db/schema.py",  # Legacy DuckDB analytics DDL
    "execution/catalog.py",  # action catalog descriptions
    "capabilities/domain/finance_outcome.py",  # docstring: "Does NOT connect to broker"
    "capabilities/domain/finance_decisions.py",  # docstring: "Does NOT connect to broker"
    "execution/adapters/finance.py",  # plan-only receipt adapter
}
_ABS_ALLOWED = {str(ROOT / f) for f in ALLOWED_FILES}


def _collect_violations() -> list[tuple[str, str, str]]:
    """Walk Core directories and collect any forbidden pattern matches."""
    violations: list[tuple[str, str, str]] = []
    for core_dir in CORE_DIRS:
        module_path = ROOT / core_dir
        if not module_path.is_dir():
            continue
        for py_file in module_path.rglob("*.py"):
            # Skip files under excluded directories
            if any(skip_dir in py_file.parts for skip_dir in SKIP_DIRS):
                continue
            # Skip allowed files
            if str(py_file) in _ABS_ALLOWED:
                continue
            rel = str(py_file.relative_to(ROOT))
            text = py_file.read_text(encoding="utf-8")
            for pattern, description in FORBIDDEN:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    violations.append((rel, pattern, description))
                    break  # one violation per file is enough
    return violations


def test_no_broker_in_core() -> None:
    """Assert that no Core .py file imports broker/trade/order business logic."""
    violations = _collect_violations()
    if violations:
        msg = "Core files with forbidden broker/trade/order patterns:\n"
        for file_path, pattern, desc in violations:
            msg += f"  {file_path}  ← {desc} (pattern: '{pattern}')\n"
        msg += f"\nTotal: {len(violations)} violation(s)"
        pytest.fail(msg)
    assert violations == []
