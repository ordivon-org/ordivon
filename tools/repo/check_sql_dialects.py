#!/usr/bin/env python3
"""Read-only, version-exact acceptance for Ordivon's tracked SQL dialect files."""
from __future__ import annotations

import argparse
import ast
import importlib.metadata
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "sqlite": "3.54.1",
    "osquery": "5.23.1",
    "postgresql": "18.6",
    "pglast": "8.6",
}
SQLITE_MIGRATION = "services/runtime/crates/ordivon-runtime-core/migrations/runtime/"
SQLITE_STORAGE = "services/runtime/crates/ordivon-runtime-core/src/runtime/"
OSQUERY_PREFIX = "platform/workstation/inventory/queries/"
POSTGRESQL_FILE = "meta/next/scripts/experimental_episode_r5c_source_r1.sql"

# Exact full-host inventories can traverse thousands of installed Python/npm
# packages on an ephemeral CI runner. Keep them executable and bounded, not
# replaced by a table-exists check or a mocked SQL parse.
OSQUERY_TIMEOUT_SECONDS = {
    "npm_packages.sql": 120,
    "python_packages.sql": 120,
}
OSQUERY_DEFAULT_TIMEOUT_SECONDS = 30


# Source-frozen migration debt, not permanent approval of these backends.
# The canonical SQL owner already lives here; reuse it rather than create a
# second database registry. Counts catch new direct SQLite use in old paths.
# PostgreSQL is preferred for new durable multi-worker stores. A retirement
# that changes these values must update its exact consumer proof here.
# This bounded AST/Rust lexical boundary is necessary but NOT proof that all indirect SQLite
# use has been discovered.
SQLITE_LEGACY_SOURCE_CALLS: dict[str, int] = {
    # Current TypeScript/JavaScript Node SQLite stores were previously invisible
    # to the source bound Python/Rust-only gate. These are actual imports,
    # unlike type-only dependencies or tests.
    'apps/web/src/store.ts': 1,
    'domains/game/experiments/casefile/src/store.ts': 1,
    'domains/game/experiments/game-e2e-r5/host-outbox-shadow.ts': 1,
    'domains/game/experiments/station-zero-v3/src/persistence.ts': 1,
    'domains/game/products/station-zero-v2/src/storage.ts': 1,
    'platform/security/labs/agent-admission-rs/src/grant-store.ts': 1,
    'platform/security/labs/agent-admission-rs/src/principal-store.ts': 1,
    # Other concrete owners previously invisible to the Runtime/Harness-only gate:
    # Gateway pull-worker durability (conditional deployed consumer).
    'services/gateway/src/ordivon_gateway/external_worker.py': 1,
    # Capital accounting and Media research have distinct consumer contracts:
    # do not promote the research executor or test-only ledger to live PG by analogy.
    'domains/capital/src/ordivon_capital/accounting/sqlite_ledger.py': 1,
    # One-shot, read-only historical source copy into qualified PostgreSQL.
    # This is debt scheduled for retirement after installed producer quiescence,
    # NOT a new SQLite accounting authority or permitted write path.
    'domains/capital/src/ordivon_capital/accounting/postgres_ledger.py': 1,
    # Media has migrated durable TrialLedger to PostgreSQL; remaining SQLite is one-shot read-only import.
    'capabilities/media/scripts/migrate-r6-trials.py': 1,
    # Retired Host v1 historical read/projection tools, not current Host v2 state.
    'platform/workstation/scripts/host_historical_projection.py': 2,
    'platform/workstation/scripts/host_retirement_snapshot.py': 3,
    # Experimental stand-alone local sources, not admitted production PG state.
    'meta/next/experiments/browser-security-r4/cf07_metadata_snapshot.py': 1,
    'meta/next/experiments/chaoxing-autosign-mvp/chaoxing_mvp/ledger.py': 1,
    'services/harness/scripts/agent_automation_browserless.py': 1,
    'services/harness/scripts/agent_automation_ledger_reconcile.py': 1,
    'services/harness/scripts/agent_automation_release.py': 3,
    'services/harness/scripts/browser_security_witness_source.py': 1,
    'services/harness/scripts/campaign_materialization.py': 1,
    'services/harness/scripts/cft_human_session.py': 2,
    'services/harness/scripts/harness_p0_scale_acceptance.py': 1,
    'services/harness/scripts/materialization_reconciliation_archive.py': 1,
    'services/harness/scripts/playwright_browserless_turn_once.py': 1,
    'services/harness/scripts/sqlite_conversation_binding.py': 3,
    'services/harness/scripts/sqlite_conversation_materializer.py': 1,
    'services/harness/scripts/sqlite_wake_turn_map.py': 3,
    'services/harness/src/ordivon_harness/sqlite_store.py': 2,
    'services/harness/src/ordivon_harness/store_ops.py': 3,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/doctor.rs': 1,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/error.rs': 1,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/inspection.rs': 1,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/inspection/operator.rs': 1,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/registry.rs': 7,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/registry/lifecycle.rs': 1,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/registry/query.rs': 9,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/registry_storage.rs': 9,
    'services/runtime/crates/ordivon-runtime-core/src/runtime/repair.rs': 1,
    'services/runtime/scripts/backup.py': 2,
    'services/runtime/scripts/mcp_e2e.py': 1,
    'services/runtime/scripts/restore.py': 1,
}


def sqlite_direct_calls(path: str, source: str) -> int:
    """Bounded static evidence: Python direct/aliased connect and Rust rusqlite."""
    if path.endswith(".py"):
        tree = ast.parse(source, filename=path)
        module_names = {"sqlite3"}  # fail closed even for externally injected symbol
        imported_connects: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                module_names.update(
                    entry.asname or entry.name
                    for entry in node.names
                    if entry.name == "sqlite3"
                )
            elif isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
                imported_connects.update(
                    entry.asname or entry.name
                    for entry in node.names
                    if entry.name == "connect"
                )
        return sum(
            isinstance(node, ast.Call)
            and (
                (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "connect"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in module_names
                )
                or (
                    isinstance(node.func, ast.Name)
                    and node.func.id in imported_connects
                )
            )
            for node in ast.walk(tree)
        )
    if path.endswith(".rs"):
        return len(re.findall(r"\brusqlite::", source))
    if path.endswith((".ts", ".tsx", ".js", ".mjs")):
        # This is a deliberately bounded import census, not full JavaScript
        # execution or AST analysis. Type-only imports are NOT active DB users.
        sqlite_modules = r"(?:node:sqlite|bun:sqlite|better-sqlite3|sqlite3|@libsql/client)"
        import_from = re.compile(
            r"^\s*import\s+(?!type\b)[^\n;]*?\bfrom\s*['\"]"
            + sqlite_modules + r"['\"]"
        )
        side_effect_import = re.compile(
            r"^\s*import\s*['\"]" + sqlite_modules + r"['\"]"
        )
        dynamic_import = re.compile(
            r"\b(?:require|import)\s*\(\s*['\"]"
            + sqlite_modules + r"['\"]\s*\)"
        )
        return sum(
            bool(import_from.search(line))
            or bool(side_effect_import.search(line))
            or len(dynamic_import.findall(line))
            for line in source.splitlines()
            if not line.lstrip().startswith(("//", "*", "/*"))
        )
    return 0



def unsafe_sqlite_file_uri_interpolations(path: str, source: str) -> list[int]:
    """Reject interpolating unescaped OS file paths into SQLite file: URIs.

    This is a syntactic fail-closed boundary for the known dangerous idiom,
    not proof of every possible dynamically constructed URI or filesystem race.
    """
    tree = ast.parse(source, filename=path)
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        if not node.values or not isinstance(node.values[0], ast.Constant):
            continue
        first = node.values[0].value
        if (
            isinstance(first, str)
            and first.startswith("file:")
            and any(isinstance(part, ast.FormattedValue) for part in node.values)
        ):
            lines.append(node.lineno)
    return sorted(set(lines))


def tracked_unsafe_sqlite_file_uris(root: Path, legacy_sources: dict[str, int]) -> list[str]:
    """Reuse the actual tracked and source-checked SQLite owner inventory."""
    issues = []
    for rel in sorted(legacy_sources):
        if not rel.endswith(".py"):
            continue
        source = root / rel
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"unsafe SQLite URI source missing or redirected: {rel}")
        for line in unsafe_sqlite_file_uri_interpolations(
            rel, source.read_text(encoding="utf-8")
        ):
            issues.append(
                f"unescaped SQLite file URI path: {rel}:{line}; "
                "use Path.absolute().as_uri() and add a physical-filename test"
            )
    return issues

def sqlite_debt_issues(
    observed: dict[str, int],
    expected: dict[str, int] = SQLITE_LEGACY_SOURCE_CALLS,
) -> list[str]:
    """Explicit new source/retirement/drift review, never a blanket PG cutover claim."""
    issues = []
    for path in sorted(observed.keys() | expected.keys()):
        actual = observed.get(path, 0)
        approved = expected.get(path, 0)
        if actual != approved:
            issues.append(
                f"unqualified SQLite owner backend drift: {path}: "
                f"observed={actual}, source-frozen={approved}; "
                "record owner/consumer and PostgreSQL replacement before accepting"
            )
    return issues


def tracked_owner_sqlite_calls(root: Path) -> dict[str, int]:
    """All tracked Python/Rust/TS/JS source: verify index and regular bytes."""
    tracked = subprocess.check_output(
        # All tracked Python/Rust source: owner-specific paths can otherwise
        # introduce new durable SQLite unnoticed outside Runtime/Harness.
        ["git", "-C", str(root), "ls-files", "--stage", "-z",
         "--", "*.py", "*.rs", "*.ts", "*.tsx", "*.js", "*.mjs"]
    )
    result: dict[str, int] = {}
    base = root.resolve()
    for record in tracked.split(b"\0"):
        if not record:
            continue
        metadata, sep, name = record.partition(b"\t")
        if not sep:
            raise ValueError("invalid staged SQLite source record")
        mode, _, stage = metadata.split()
        path = name.decode("utf-8", errors="surrogateescape")
        if not path.endswith((".py", ".rs", ".ts", ".tsx", ".js", ".mjs")) or "/tests/" in path or "/test/" in path or "/__tests__/" in path or "/test_" in path:
            continue
        if path.endswith(("/tests.rs", "/integration_tests.rs", "/summary_query_tests.rs",
                          ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx",
                          ".test.js", ".spec.js", ".test.mjs", ".spec.mjs")):
            continue
        if mode not in (b"100644", b"100755") or stage != b"0":
            raise ValueError(f"SQLite core source not regular stage-0: {path}")
        source = root
        for part in Path(path).parts:
            source = source / part
            if source.is_symlink():
                raise ValueError(f"SQLite core source symlink: {path}")
        if not source.is_file() or not source.resolve().is_relative_to(base):
            raise ValueError(f"SQLite core source unavailable/outside checkout: {path}")
        count = sqlite_direct_calls(path, source.read_text(encoding="utf-8"))
        if count:
            result[path] = count
    return result


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
    # Git path, index file type and resolved checkout source must agree.
    # A local replacement must not mask a symlink committed in the index.
    tracked = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "--stage", "-z", "--", "*.sql"],
    )
    repository = root.resolve()
    accepted: list[str] = []
    for record in tracked.split(b"\0"):
        if not record:
            continue
        metadata, separator, name = record.partition(b"\t")
        mode, _, stage = metadata.split()
        path = name.decode("utf-8", errors="surrogateescape")
        if not separator or mode not in (b"100644", b"100755") or stage != b"0":
            raise ValueError(f"tracked SQL symlink or nonregular index type: {path}")
        source = root
        for component in Path(path).parts:
            source = source / component
            if source.is_symlink():
                raise ValueError(f"tracked SQL symlink or external source: {path}")
        if not source.is_file() or not source.resolve().is_relative_to(repository):
            raise ValueError(f"tracked SQL missing or external source: {path}")
        accepted.append(path)
    return accepted


def run_bounded(
    argv: list[str],
    *,
    cwd: Path,
    stdin: str | None = None,
    timeout: int = 20,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def host_postgres_only_sources(root: Path) -> list[str]:
    """Fail closed when Host authority introduces a second embedded SQL engine.

    Runtime's node-local Registry and Harness's durable Run store are separate
    consumers with different crash/replay contracts; this is not their cutover.
    """
    issues: list[str] = []
    has_postgres_client = False
    forbidden = ("sqlite3", "pysqlite3", "aiosqlite")
    for base in ("services/host/src", "services/host/migrations"):
        directory = root / base
        if not directory.is_dir() or directory.is_symlink():
            issues.append(f"Host PostgreSQL source directory unavailable: {base}")
            continue
        for source in sorted(directory.rglob("*.py")):
            rel = source.relative_to(root).as_posix()
            if source.is_symlink() or not source.is_file():
                issues.append(f"Host PostgreSQL source redirected: {rel}")
                continue
            try:
                tree = ast.parse(source.read_text(encoding="utf-8"), filename=rel)
            except (SyntaxError, UnicodeError, OSError) as exc:
                issues.append(f"Host PostgreSQL source unreadable: {rel}: {type(exc).__name__}")
                continue
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "psycopg"
                        and node.func.attr == "connect"):
                    has_postgres_client = True
                imports: list[str] = []
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imports = [node.module or ""] + [
                        f"{node.module}.{alias.name}" for alias in node.names
                    ]
                if any(
                    name == item or name.startswith(item + ".")
                    for name in imports
                    for item in forbidden
                ) or any("sqlalchemy.dialects.sqlite" in name for name in imports):
                    issues.append(f"Host PostgreSQL authority forbids embedded SQL import: {rel}")
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if "sqlite:" in node.value.lower():
                        issues.append(f"Host PostgreSQL authority forbids SQLite DSN: {rel}")
                if isinstance(node, ast.Call) and node.args:
                    target = node.func
                    dynamic = (
                        isinstance(target, ast.Name) and target.id in {"__import__", "import_module"}
                    ) or (
                        isinstance(target, ast.Attribute)
                        and target.attr == "import_module"
                    )
                    literal = node.args[0]
                    if (dynamic and isinstance(literal, ast.Constant)
                            and isinstance(literal.value, str)
                            and any(literal.value == name or literal.value.startswith(name + ".")
                                    for name in forbidden)):
                        issues.append(f"Host PostgreSQL authority forbids dynamic SQL import: {rel}")
    if not has_postgres_client:
        issues.append("Host PostgreSQL authority has no active psycopg.connect consumer")
    return sorted(set(issues))


def check(root: Path) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    facts: list[str] = []
    issues.extend(host_postgres_only_sources(root))
    if not issues:
        facts.append("Host PostgreSQL-only active source authority PASS")
    files = tracked_sql(root)
    legacy_sources = tracked_owner_sqlite_calls(root)
    issues.extend(sqlite_debt_issues(legacy_sources))
    issues.extend(tracked_unsafe_sqlite_file_uris(root, legacy_sources))
    facts.append(
        f"multi-owner SQLite direct API callsites={sum(legacy_sources.values())}, "
        f"source paths={len(legacy_sources)}; "
        "PostgreSQL durable-owner migration standing=NOT_CUT_OVER"
    )
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
                facts.append(f"SQLite {version}: 6 migrations + 4 storage DDL in-memory and integrity_check PASS")
    except (OSError, subprocess.SubprocessError, IndexError) as exc:
        issues.append(f"SQLite native SQL evidence unavailable: {type(exc).__name__}")
    # osquery SELECT providers: query against current host, never mutate.
    try:
        p = run_bounded(["osqueryi", "--version"], cwd=root)
        observed = re.search(r"([0-9]+\.[0-9]+\.[0-9]+)", p.stdout + p.stderr)
        current = observed.group(1) if p.returncode == 0 and observed else "UNAVAILABLE"
        if current != EXPECTED["osquery"]:
            issues.append(f"osqueryi {current} != latest {EXPECTED['osquery']}")
        passed = 0
        for name in grouped["osquery"]:
            query = (root / name).read_text(encoding="utf-8")
            if not re.match(r"^\s*SELECT\b", query, re.I):
                issues.append(f"osqueryi query is not bounded read-only SELECT: {name}")
                continue
            seconds = OSQUERY_TIMEOUT_SECONDS.get(Path(name).name, OSQUERY_DEFAULT_TIMEOUT_SECONDS)
            print(f"osquery native query: {name} (budget={seconds}s)", flush=True)
            try:
                result = run_bounded(
                    ["osqueryi", "--json", query],
                    cwd=root,
                    timeout=seconds,
                )
            except subprocess.TimeoutExpired:
                issues.append(f"osqueryi timed out after {seconds}s: {name}")
                continue
            if result.returncode != 0:
                issues.append(f"osqueryi execution failed: {name}: {result.stderr[-180:]}")
                continue
            try:
                rows = json.loads(result.stdout)
                if not isinstance(rows, list):
                    raise ValueError("not a JSON result list")
            except (json.JSONDecodeError, ValueError):
                issues.append(f"osqueryi non-JSON result: {name}")
                continue
            passed += 1
            print(f"osquery native query passed: {name}; rows={len(rows)}", flush=True)
        if passed == len(grouped["osquery"]):
            facts.append(f"osquery {current}: all {passed} native read-only query executions PASS")
        else:
            facts.append(f"osquery {current}: {passed}/{len(grouped['osquery'])} native query executions PASS")
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
    try:
        issues, facts = check(ROOT)
    except (ValueError, SyntaxError) as exc:
        print(f"SQL dialect acceptance: NONCOMPLIANT ({exc})")
        return 2
    for fact in facts:
        print(fact)
    for issue in issues:
        print("NONCOMPLIANT " + issue)
    print(f"SQL dialect acceptance: {'PASS' if not issues else 'NONCOMPLIANT'} ({len(issues)} issues)")
    return 0 if args.audit or not issues else 1


if __name__ == "__main__":
    sys.exit(main())
