#!/usr/bin/env python3
"""OpenAPI Snapshot Sanity Checker — validates snapshot structure and integrity.

Checks:
  1. Snapshot file exists and is valid JSON.
  2. Top-level keys include: openapi, info, paths, components.
  3. Path count and schema count are above minimum thresholds.
  4. Critical API paths exist with expected HTTP methods.
  5. Baseline tracking: first run records counts; subsequent runs compare against baseline.

This complements the CI git diff --exit-code check by distinguishing
"real API changes" from "generator drift" (e.g., path/schema count drops).

This is a CandidateRule (advisory) — it does NOT block CI by default.
Exit 0 = clean; Exit 1 = violations found.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_PATH = ROOT / "tests/contracts/openapi.snapshot.json"
BASELINE_PATH = ROOT / "data/openapi_snapshot_baseline.json"

# ── Minimum thresholds (catches catastrophic generator drift) ───
MIN_PATHS = 25
MIN_SCHEMAS = 35
# Max reduction ratio before flagging (e.g., 0.25 = 25% drop is suspicious)
MAX_PATH_DROP_RATIO = 0.25
MAX_SCHEMA_DROP_RATIO = 0.25

# ── Critical API paths (must exist with expected methods) ───────
CRITICAL_PATHS: dict[str, list[str]] = {
    "/api/v1/finance-decisions/intake":                         ["post"],
    "/api/v1/finance-decisions/intake/{intake_id}":             ["get"],
    "/api/v1/finance-decisions/intake/{intake_id}/govern":      ["post"],
    "/api/v1/finance-decisions/intake/{intake_id}/plan":        ["post"],
    "/api/v1/finance-decisions/intake/{intake_id}/outcome":     ["post"],
    "/api/v1/reviews/submit":                                    ["post"],
    "/api/v1/reviews/{review_id}":                               ["get"],
    "/api/v1/reviews/{review_id}/complete":                      ["post"],
    "/api/v1/health":                                            ["get"],
    "/api/v1/version":                                           ["get"],
}

REQUIRED_TOP_KEYS = {"openapi", "info", "paths", "components"}


def load_snapshot() -> tuple[dict | None, list[str]]:
    """Load and validate the snapshot JSON."""
    violations: list[str] = []

    if not SNAPSHOT_PATH.exists():
        violations.append(f"{SNAPSHOT_PATH}: file not found — run 'pnpm generate:openapi'")
        return None, violations

    try:
        data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        violations.append(f"{SNAPSHOT_PATH}: invalid JSON — {e}")
        return None, violations

    return data, violations


def check_top_level_keys(data: dict) -> list[str]:
    """Verify required top-level keys exist."""
    violations: list[str] = []
    missing = REQUIRED_TOP_KEYS - set(data.keys())
    if missing:
        violations.append(
            f"Missing top-level keys: {sorted(missing)}"
        )
    return violations


def check_paths(data: dict, baseline: dict | None) -> list[str]:
    """Verify path count and critical paths."""
    violations: list[str] = []
    paths = data.get("paths", {})

    # Minimum threshold
    path_count = len(paths)
    if path_count < MIN_PATHS:
        violations.append(
            f"Path count {path_count} below minimum {MIN_PATHS} — possible generator drift"
        )

    # Baseline comparison
    if baseline and "path_count" in baseline:
        baseline_count = baseline["path_count"]
        if baseline_count > 0:
            drop_ratio = (baseline_count - path_count) / baseline_count
            if drop_ratio > MAX_PATH_DROP_RATIO:
                violations.append(
                    f"Path count dropped from {baseline_count} to {path_count} "
                    f"({drop_ratio:.0%}) — exceeds {MAX_PATH_DROP_RATIO:.0%} threshold"
                )

    # Critical paths
    for path, expected_methods in CRITICAL_PATHS.items():
        if path not in paths:
            violations.append(f"Critical path missing: {path}")
            continue
        actual_methods = set(m.lower() for m in paths[path].keys())
        for method in expected_methods:
            if method.lower() not in actual_methods:
                violations.append(
                    f"Critical path {path}: missing {method.upper()} method"
                )

    return violations


def check_schemas(data: dict, baseline: dict | None) -> list[str]:
    """Verify schema count."""
    violations: list[str] = []
    schemas = data.get("components", {}).get("schemas", {})

    schema_count = len(schemas)
    if schema_count < MIN_SCHEMAS:
        violations.append(
            f"Schema count {schema_count} below minimum {MIN_SCHEMAS} — possible generator drift"
        )

    if baseline and "schema_count" in baseline:
        baseline_count = baseline["schema_count"]
        if baseline_count > 0:
            drop_ratio = (baseline_count - schema_count) / baseline_count
            if drop_ratio > MAX_SCHEMA_DROP_RATIO:
                violations.append(
                    f"Schema count dropped from {baseline_count} to {schema_count} "
                    f"({drop_ratio:.0%}) — exceeds {MAX_SCHEMA_DROP_RATIO:.0%} threshold"
                )

    return violations


def check_info(data: dict) -> list[str]:
    """Verify info section has title and version."""
    violations: list[str] = []
    info = data.get("info", {})
    if not info.get("title"):
        violations.append("info.title is missing or empty")
    if not info.get("version"):
        violations.append("info.version is missing or empty")
    return violations


def load_baseline() -> dict | None:
    """Load the baseline if it exists."""
    if BASELINE_PATH.exists():
        try:
            return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def save_baseline(data: dict) -> None:
    """Save current snapshot metrics as baseline."""
    paths = data.get("paths", {})
    schemas = data.get("components", {}).get("schemas", {})
    baseline = {
        "path_count": len(paths),
        "schema_count": len(schemas),
        "openapi_version": data.get("openapi", ""),
        "info_version": data.get("info", {}).get("version", ""),
        "snapshot_path": str(SNAPSHOT_PATH.relative_to(ROOT)),
    }
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    all_violations: list[str] = []

    print("=== OpenAPI Snapshot Sanity Check ===")
    print()

    # Load snapshot
    data, load_violations = load_snapshot()
    all_violations.extend(load_violations)
    if data is None:
        for v in all_violations:
            print(f"❌ {v}")
        print("\n❌ Cannot proceed — snapshot not loadable")
        return 1

    baseline = load_baseline()
    if baseline:
        print(f"  Baseline: {baseline.get('path_count')} paths, {baseline.get('schema_count')} schemas")
    else:
        print("  No baseline yet — creating one")

    # Check 1: Top-level keys
    v = check_top_level_keys(data)
    if v:
        print("❌ Top-level keys:")
        for item in v:
            print(f"  {item}")
        all_violations.extend(v)
    else:
        print("✅ Top-level keys: openapi, info, paths, components")

    # Check 2: Paths
    v = check_paths(data, baseline)
    if v:
        print("❌ Paths:")
        for item in v:
            print(f"  {item}")
        all_violations.extend(v)
    else:
        paths = data.get("paths", {})
        print(f"✅ Paths: {len(paths)} endpoints (min {MIN_PATHS}), critical paths present")

    # Check 3: Schemas
    v = check_schemas(data, baseline)
    if v:
        print("❌ Schemas:")
        for item in v:
            print(f"  {item}")
        all_violations.extend(v)
    else:
        schemas = data.get("components", {}).get("schemas", {})
        print(f"✅ Schemas: {len(schemas)} definitions (min {MIN_SCHEMAS})")

    # Check 4: Info
    v = check_info(data)
    if v:
        print("❌ Info:")
        for item in v:
            print(f"  {item}")
        all_violations.extend(v)
    else:
        info = data.get("info", {})
        print(f"✅ Info: {info.get('title')} v{info.get('version')}")

    # Save baseline for future runs
    save_baseline(data)

    print()
    if all_violations:
        print(f"❌ {len(all_violations)} violation(s)")
        return 1
    else:
        print("✅ OpenAPI snapshot sanity check passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
