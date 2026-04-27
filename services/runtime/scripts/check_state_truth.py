#!/usr/bin/env python3
"""State Truth Boundary Checker — enforces SQLAlchemy ORM as single truth source.

Checks:
  1. No DuckDB direct writes in Core (domains/governance/capabilities/execution).
  2. All ORM Base subclasses are registered in state/db/bootstrap.py.
  3. FinanceManualOutcomeORM is registered (Finance Pack requirement).
  4. No manual ALTER TABLE / raw DDL in Core (outside migrations).

This is a CandidateRule (advisory) — it does NOT block CI by default.
Exit 0 = clean; Exit 1 = violations found.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── Directories scanned for DuckDB / DDL contamination ──────────
CORE_DIRS = ["domains", "governance", "capabilities", "execution"]

# ── Whitelisted files ───────────────────────────────────────────
DUCKDB_WHITELIST = {
    "state/db/schema.py",          # Legacy analytics DDL, clearly marked NOT DOMAIN TRUTH
    "shared/config/settings.py",   # Configuration path declaration only
}

DDL_WHITELIST = {
    "state/db/migrations/runner.py",  # Idempotent migration runner
    "state/db/schema.py",             # Legacy DuckDB analytics DDL (NOT domain truth)
}

ORM_WHITELIST_DIRS = {"tests", "alembic", "__pycache__", ".venv", "build"}


def find_py_files(directories: list[str]) -> list[Path]:
    """Collect all .py files under given directories, skipping cache dirs."""
    files: list[Path] = []
    for d in directories:
        dp = ROOT / d
        if not dp.is_dir():
            continue
        for f in dp.rglob("*.py"):
            if any(skip in f.parts for skip in ORM_WHITELIST_DIRS):
                continue
            files.append(f)
    return files


# ═══════════════════════════════════════════════════════════════════
# Check 1: DuckDB contamination in Core
# ═══════════════════════════════════════════════════════════════════

DUCKDB_PATTERNS = [
    (r"import\s+duckdb\b", "import duckdb"),
    (r"from\s+duckdb\b", "from duckdb import"),
    (r"duckdb\.connect\(", "duckdb.connect()"),
    (r"duckdb://", "duckdb:// connection string"),
]


def check_duckdb_contamination() -> list[str]:
    violations: list[str] = []
    for py_file in find_py_files(CORE_DIRS):
        rel = str(py_file.relative_to(ROOT))
        if rel in DUCKDB_WHITELIST:
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for pattern, desc in DUCKDB_PATTERNS:
            if re.search(pattern, text):
                violations.append(f"{rel}: {desc}")
                break  # one violation per file
    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 2: All ORM Base subclasses registered in bootstrap
# ═══════════════════════════════════════════════════════════════════

def find_orm_classes() -> dict[str, Path]:
    """Find all class XxxORM(Base) definitions. Returns {class_name: file_path}."""
    orm_classes: dict[str, Path] = {}
    search_roots = [
        ROOT / "domains", ROOT / "governance", ROOT / "infra",
        ROOT / "state", ROOT / "packs",
    ]
    for root in search_roots:
        if not root.is_dir():
            continue
        for py_file in root.rglob("*.py"):
            if any(skip in py_file.parts for skip in ORM_WHITELIST_DIRS):
                continue
            try:
                text = py_file.read_text(encoding="utf-8")
            except Exception:
                continue
            # Match: class SomethingORM(Base):
            for m in re.finditer(r"class\s+(\w*ORM)\s*\(\s*Base\s*\)", text):
                orm_classes[m.group(1)] = py_file
    return orm_classes


def check_orm_registration() -> list[str]:
    violations: list[str] = []
    bootstrap_path = ROOT / "state/db/bootstrap.py"
    if not bootstrap_path.exists():
        return ["state/db/bootstrap.py: not found — cannot verify ORM registration"]

    bootstrap_text = bootstrap_path.read_text(encoding="utf-8")
    orm_classes = find_orm_classes()

    for class_name, file_path in sorted(orm_classes.items()):
        rel = str(file_path.relative_to(ROOT))
        if class_name not in bootstrap_text:
            violations.append(
                f"{class_name} ({rel}): not imported in state/db/bootstrap.py"
            )

    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 3: FinanceManualOutcomeORM specifically registered
# ═══════════════════════════════════════════════════════════════════

def check_finance_outcome_orm() -> list[str]:
    violations: list[str] = []
    bootstrap_path = ROOT / "state/db/bootstrap.py"
    if not bootstrap_path.exists():
        return ["state/db/bootstrap.py: not found"]
    bootstrap_text = bootstrap_path.read_text(encoding="utf-8")
    if "FinanceManualOutcomeORM" not in bootstrap_text:
        violations.append(
            "FinanceManualOutcomeORM: not registered in state/db/bootstrap.py "
            "(Finance Pack domain truth gate)"
        )
    return violations


# ═══════════════════════════════════════════════════════════════════
# Check 4: Manual ALTER TABLE / raw DDL in Core
# ═══════════════════════════════════════════════════════════════════

DDL_PATTERNS = [
    (r"ALTER\s+TABLE\s+\w+", "ALTER TABLE (raw DDL)"),
    (r"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?\w+\s*\(", "CREATE TABLE (raw DDL)"),
    (r"DROP\s+TABLE\s+(IF\s+EXISTS\s+)?\w+", "DROP TABLE (raw DDL)"),
    (r"\.execute\s*\(\s*text\s*\(\s*[\"'](ALTER|CREATE|DROP|INSERT|UPDATE|DELETE)\b",
     "text(DDL) via .execute()"),
]


def check_raw_ddl() -> list[str]:
    violations: list[str] = []
    for py_file in find_py_files(CORE_DIRS + ["state"]):
        rel = str(py_file.relative_to(ROOT))
        if rel in DDL_WHITELIST:
            continue
        # Skip alembic migrations and test files
        if "alembic" in rel or "migrations" in rel:
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for pattern, desc in DDL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"{rel}: {desc}")
                break
    return violations


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main() -> int:
    all_violations: list[str] = []

    print("=== State Truth Boundary Check ===")
    print()

    # Check 1
    duckdb_violations = check_duckdb_contamination()
    if duckdb_violations:
        print("❌ DuckDB contamination in Core:")
        for v in duckdb_violations:
            print(f"  {v}")
        all_violations.extend(duckdb_violations)
    else:
        print("✅ No DuckDB contamination in Core")

    # Check 2
    orm_violations = check_orm_registration()
    if orm_violations:
        print("❌ ORM registration gaps:")
        for v in orm_violations:
            print(f"  {v}")
        all_violations.extend(orm_violations)
    else:
        print("✅ All ORM classes registered in bootstrap")

    # Check 3
    finance_violations = check_finance_outcome_orm()
    if finance_violations:
        print("❌ FinanceManualOutcomeORM:")
        for v in finance_violations:
            print(f"  {v}")
        all_violations.extend(finance_violations)
    else:
        print("✅ FinanceManualOutcomeORM registered")

    # Check 4
    ddl_violations = check_raw_ddl()
    if ddl_violations:
        print("❌ Raw DDL in Core:")
        for v in ddl_violations:
            print(f"  {v}")
        all_violations.extend(ddl_violations)
    else:
        print("✅ No raw DDL in Core")

    # Summary
    print()
    if all_violations:
        print(f"❌ {len(all_violations)} violation(s) — State Truth boundary breached")
        return 1
    else:
        print("✅ State Truth boundary clean")
        return 0


if __name__ == "__main__":
    sys.exit(main())
