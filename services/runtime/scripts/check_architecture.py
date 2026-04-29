#!/usr/bin/env python3
"""Architecture boundary checker — prevents domain pollution into Core.

ADR-006 allows: Core → pack_policy (RejectReason, EscalateReason types only).
Everything else (tool_refs, policy overlays, pack-specific fields) is forbidden.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE_MODULES = ["governance", "state", "domains", "capabilities", "execution", "shared"]

# Files allowed to reference broker/tool namespace metadata (ADR-006 interface)
ALLOWED_FILES = {
    "governance/policy_source.py",  # ADR-006: tool namespace refs (metadata only)
    "state/db/schema.py",           # Legacy DuckDB analytics schema (DDL only, not domain logic)
    "domains/finance/read_only_adapter.py",  # Phase 6G: read-only capability contract (declares what is NOT allowed)
}

# Patterns that are FORBIDDEN in Core modules
FORBIDDEN = [
    # Direct pack imports of business logic (not type-only imports)
    ("from packs.finance.tool_refs import", "pack tool_refs leaked into Core"),
    ("from packs.finance.policy import", "pack policy overlays leaked into Core"),
    # Finance-specific business logic fields must not appear in Core
    ("stop_loss", "finance field 'stop_loss' in Core"),
    ("max_loss_usdt", "finance field 'max_loss_usdt' in Core"),
    ("position_size_usdt", "finance field 'position_size_usdt' in Core"),
    ("is_chasing", "finance field 'is_chasing' in Core"),
    ("is_revenge_trade", "finance field 'is_revenge_trade' in Core"),
    # Trade execution references must not exist in Core
    ("place_order", "trade execution 'place_order' in Core"),
    ("execute_trade", "trade execution 'execute_trade' in Core"),
]


def check_file(path: Path) -> list[str]:
    violations = []
    rel = str(path.relative_to(ROOT))
    text = path.read_text(encoding="utf-8")

    for pattern, description in FORBIDDEN:
        if pattern in text:
            violations.append(
                f"{rel}: {description} (pattern: '{pattern}')"
            )
    return violations


def main() -> int:
    violations = []
    for module in CORE_MODULES:
        module_path = ROOT / module
        if not module_path.exists():
            continue
        for py_file in module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            rel = str(py_file.relative_to(ROOT))
            if rel in ALLOWED_FILES:
                continue
            violations.extend(check_file(py_file))

    if violations:
        print("ARCHITECTURE BOUNDARY VIOLATIONS:")
        for v in violations:
            print(f"  ❌ {v}")
        return 1

    print("✅ Architecture boundaries clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
