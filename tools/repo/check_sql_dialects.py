#!/usr/bin/env python3
"""Read-only, version-exact acceptance for Ordivon's tracked SQL dialect files."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "sqlite": "3.54.0",
    "osquery": "5.23.1",
    "postgresql": "18.6",
    "pglast": "8.6",
}
SQLITE_MIGRATION = "services/runtime/crates/ordivon-runtime-core/migrations/runtime/"
SQLITE_STORAGE = "services/runtime/crates/ordivon-runtime-core/src/runtime/"
OSQUERY_PREFIX = "platform/workstation/inventory/queries/"
POSTGRESQL_FILE = "meta/next/scripts/experimental_episode_r5c_source_r1.sql"


def classify(path: str) -> str | None:
    if path.startswith(OSQUERY_PREFIX) and path.endswith(".sql"):
        return "osquery"
    if path.startswith(SQLITE_MIGRATION) and path.endswith(".sql"):
        return "sqlite"
    if path.startswith(SQLITE_STORAGE) and path.endswith("_storage.sql"):
        return "sqlite"
    if path == POSTGRESQL_FILE:
        return "postgresql"
    return None


def tracked_sql(root: Path) -> list[str]:
    return [
        p for p in subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "--", "*.sql"],
            text=True,
        ).splitlines() if (root / p).is_file()
    ]


def run_bounded(argv: list[str], *, cwd: Path, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


def check(root: Path) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    facts: list[str] = []
    files = tracked_sql(root)
    grouped: dict[str, list[str]] = {"sqlite": [], "osquery": [], "postgresql": []}
    for path in files:
        dialect = classify(path)
        if dialect is None:
            issues.append(f"unmapped tracked SQL dialect: {path}")
        else:
            grouped[dialect].append(path)
    facts.append(f"tracked .sql files={len(files)}; mapped={sum(map(len,grouped.values()))}; dialects=" +
                 ", ".join(f"{key}:{len(rows)}" for key, rows in grouped.items()))
    if not all(grouped.values()):
        issues.append("one or more expected SQL dialect groups absent; mapping changed")
    # In-memory SQLite only: NEVER point at the live Registry.
    try:
        sqlite = run_bounded(["sqlite3", "--version"], cwd=root)
        version = sqlite.stdout.split()[0] if sqlite.returncode == 0 and sqlite.stdout else "UNAVAILABLE"
        if version != EXPECTED["sqlite"]:
            issues.append(f"SQLite CLI {version} != latest {EXPECTED['sqlite']}")
        migrations = [p for p in grouped["sqlite"] if p.startswith(SQLITE_MIGRATION)]
        storage = [p for p in grouped["sqlite"] if p.startswith(SQLITE_STORAGE)]
        if len(migrations) != 6 or len(storage) != 4:
            issues.append(f"SQLite migration/storage map changed: {len(migrations)}+{len(storage)}")
        else:
            sql = "PRAGMA foreign_keys=ON;\n" + "\n".join(
                (root / name).read_text(encoding="utf-8") for name in sorted(migrations) + sorted(storage)
            ) + "\nPRAGMA integrity_check;\nSELECT COUNT(*) FROM sqlite_schema WHERE type='table';\n"
            result = run_bounded(["sqlite3", "-batch", "-bail", ":memory:"], cwd=root, stdin=sql)
            if result.returncode != 0 or result.stdout.splitlines()[:1] != ["ok"]:
                issues.append("SQLite latest in-memory DDL/integrity failure: " +
                              (result.stderr or result.stdout)[-250:])
            else:
                facts.append("SQLite 3.54.0: 6 migrations + 4 storage DDL in-memory and integrity_check PASS")
    except (OSError, subprocess.SubprocessError, IndexError) as exc:
        issues.append(f"SQLite native SQL evidence unavailable: {type(exc).__name__}")
    # osquery SELECT providers: query against current host, never mutate.
    try:
        p = run_bounded(["osqueryi", "--version"], cwd=root)
        observed = re.search(r"([0-9]+\.[0-9]+\.[0-9]+)", p.stdout + p.stderr)
        current = observed.group(1) if p.returncode == 0 and observed else "UNAVAILABLE"
        if current != EXPECTED["osquery"]:
            issues.append(f"osqueryi {current} != latest {EXPECTED['osquery']}")
        for name in grouped["osquery"]:
            query = (root / name).read_text(encoding="utf-8")
            if not re.match(r"^\s*SELECT\b", query, re.I):
                issues.append(f"osqueryi query is not bounded read-only SELECT: {name}")
                continue
            result = run_bounded(["osqueryi", "--json", query], cwd=root)
            if result.returncode != 0:
                issues.append(f"osqueryi execution failed: {name}: {result.stderr[-180:]}")
                continue
            try:
                rows = json.loads(result.stdout)
                if not isinstance(rows, list):
                    raise ValueError("not a JSON result list")
            except (json.JSONDecodeError, ValueError):
                issues.append(f"osqueryi non-JSON result: {name}")
        facts.append(f"osquery {current}: {len(grouped['osquery'])} read-only query executions checked")
    except (OSError, subprocess.SubprocessError) as exc:
        issues.append(f"osquery native SQL evidence unavailable: {type(exc).__name__}")
    # Parsing a schema-dependent projection without executing against live DB.
    try:
        p = run_bounded(["psql", "--version"], cwd=root)
        observed = re.search(r"([0-9]+\.[0-9]+)", p.stdout + p.stderr)
        current = observed.group(1) if p.returncode == 0 and observed else "UNAVAILABLE"
        if current != EXPECTED["postgresql"]:
            issues.append(f"psql {current} != latest {EXPECTED['postgresql']}")
        from pglast import parse_sql  # Explicit CLI dependency: uv --with pglast==8.6
        if importlib.metadata.version("pglast") != EXPECTED["pglast"]:
            issues.append("PostgreSQL AST parser version is not pinned to exact 8.6")
        for name in grouped["postgresql"]:
            parsed = parse_sql((root / name).read_text(encoding="utf-8"))
            if len(parsed) != 1:
                issues.append(f"PostgreSQL statement count changed unexpectedly: {name}")
        facts.append(f"PostgreSQL {current}: {len(grouped['postgresql'])} SQL source AST parsed with pglast")
    except (ImportError, OSError, subprocess.SubprocessError, ValueError) as exc:
        issues.append(f"PostgreSQL source parse evidence unavailable: {type(exc).__name__}: {str(exc)[:120]}")
    return issues, facts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    issues, facts = check(ROOT)
    for fact in facts:
        print(fact)
    for issue in issues:
        print("NONCOMPLIANT " + issue)
    print(f"SQL dialect acceptance: {'PASS' if not issues else 'NONCOMPLIANT'} ({len(issues)} issues)")
    return 0 if args.audit or not issues else 1


if __name__ == "__main__":
    sys.exit(main())
