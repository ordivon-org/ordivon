#!/usr/bin/env python3
"""Artifact Registry Checker — validates artifact classification and registration.

Every file in tests/, scripts/, domains/, src/ must be:
  1. Registered in artifact-registry.jsonl
  2. Have a valid artifact_class
  3. Have a valid artifact_criticality
  4. Have a valid artifact_layer

This closes the governance gap: new files in governed directories are
detected, and existing files must carry proper classification metadata.

Usage:
    python scripts/check_artifact_registry.py
    python scripts/check_artifact_registry.py --json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "governance" / "artifact-registry.jsonl"

GOVERNED_DIRS = ["tests", "scripts", "domains", "src"]

VALID_CLASSES = {
    "checker_core", "checker_meta", "checker_fixture",
    "script_checker", "script_control", "script_tool",
    "script_verification", "script_migration", "script_shell",
    "domain_pure", "domain_state", "domain_engine",
    "source_control", "source_schema", "source_check",
    "source_registry", "source_cli", "source_lib",
    "test_unit", "test_fixture", "test_integration",
    "test_contract", "test_other",
}

VALID_CRITICALITIES = {
    "governance_critical", "governance_supporting",
    "test_evidence", "test_supporting",
    "application",
}

VALID_LAYERS = {
    "L1_TRUTH", "L2_EVIDENCE", "L3_CANON",
    "L4_PRODUCT", "L_CHECKER",
}

EXCLUDE_PATTERNS = [
    "__pycache__", ".egg-info", ".bundled_manifest", ".usage.json",
    ".pyc", ".pyo", ".so",
]


def load_registry() -> tuple[list[dict], set[str]]:
    """Load artifact registry entries and registered paths."""
    entries = []
    paths = set()
    if not REGISTRY.exists():
        return entries, paths
    with open(REGISTRY) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                entries.append(e)
                paths.add(e.get("path", ""))
            except json.JSONDecodeError:
                continue
    return entries, paths


def find_unregistered(registered_paths: set[str]) -> list[str]:
    """Find files in governed dirs not in registry."""
    unregistered = []
    for directory in GOVERNED_DIRS:
        d = ROOT / directory
        if not d.exists():
            continue
        for fpath in d.rglob("*"):
            if not fpath.is_file():
                continue
            if any(p in str(fpath) for p in EXCLUDE_PATTERNS):
                continue
            rel = str(fpath.relative_to(ROOT))
            if rel not in registered_paths:
                unregistered.append(rel)
    return sorted(unregistered)


def validate_classification(entries: list[dict]) -> list[str]:
    """Validate classification fields on all entries."""
    errors = []
    for e in entries:
        aid = e.get("artifact_id", "?")
        aclass = e.get("artifact_class", "")
        acrit = e.get("artifact_criticality", "")
        alayer = e.get("artifact_layer", "")

        if not aclass:
            errors.append(f"{aid}: missing artifact_class")
        elif aclass not in VALID_CLASSES:
            errors.append(f"{aid}: invalid artifact_class '{aclass}'")

        if not acrit:
            errors.append(f"{aid}: missing artifact_criticality")
        elif acrit not in VALID_CRITICALITIES:
            errors.append(f"{aid}: invalid artifact_criticality '{acrit}'")

        if not alayer:
            errors.append(f"{aid}: missing artifact_layer")
        elif alayer not in VALID_LAYERS:
            errors.append(f"{aid}: invalid artifact_layer '{alayer}'")
    return errors


def main():
    entries, registered_paths = load_registry()
    unregistered = find_unregistered(registered_paths)
    class_errors = validate_classification(entries)

    # Stats
    stats_class = {}
    stats_crit = {}
    stats_layer = {}
    for e in entries:
        c = e.get("artifact_class", "?")
        r = e.get("artifact_criticality", "?")
        l = e.get("artifact_layer", "?")
        stats_class[c] = stats_class.get(c, 0) + 1
        stats_crit[r] = stats_crit.get(r, 0) + 1
        stats_layer[l] = stats_layer.get(l, 0) + 1

    all_errors = []
    all_errors.extend(unregistered)
    all_errors.extend(class_errors)

    print("Artifact Registry Check")
    print(f"  Registered:    {len(entries)}")
    print(f"  Ungoverned:    {len(unregistered)}")
    print(f"  Class errors:  {len(class_errors)}")
    print()
    print(f"  By class:       {dict(sorted(stats_class.items()))}")
    print(f"  By criticality: {dict(sorted(stats_crit.items()))}")
    print(f"  By layer:       {dict(sorted(stats_layer.items()))}")
    print()

    if all_errors:
        print(f"❌ {len(all_errors)} issue(s):")
        for err in all_errors[:30]:
            print(f"  {err}")
        if len(all_errors) > 30:
            print(f"  ... and {len(all_errors) - 30} more")
        return 1
    else:
        print("✅ All artifacts registered and properly classified.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
