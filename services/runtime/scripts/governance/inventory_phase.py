#!/usr/bin/env python3
"""Governance Inventory — discover all artifacts for a phase or component.

Usage:
    python3 scripts/governance/inventory_phase.py --phase AOS
    python3 scripts/governance/inventory_phase.py --phase AOS --json
    python3 scripts/governance/inventory_phase.py --phase-family AOS
    python3 scripts/governance/inventory_phase.py --phase PM

Output:
    Machine-readable inventory JSON showing all files, registry status,
    phase-boundary status, and governance surface coverage.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "docs/governance/document-registry.jsonl"
PHASE_BOUNDARIES_PATH = ROOT / "docs/ai/current-phase-boundaries.md"
WIKI_PATH = ROOT / "docs/governance/wiki-index.md"

# Governance surface patterns — files to discover per phase prefix
SURFACE_PATTERNS = {
    "receipts": ["receipts/governance/{prefix}*.md"],
    "schemas": ["{prefix}/schemas/*.json"],
    "scripts": ["scripts/{prefix}*.py"],
    "fixtures": ["{prefix}/fixtures/**/*.json", "{prefix}/fixtures/**/*.md"],
    "evidence": ["docs/governance/evidence/{prefix}*/**/*", "{prefix}/evidence/**/*"],
    "debts": ["{prefix}/debts/*.jsonl", "docs/governance/dependency-audit-debts.jsonl"],
    "tests": ["tests/**/test_{prefix}*.py", "tests/**/*{prefix}*.py"],
    "generated": ["{prefix}/generated/*.json", "docs/governance/generated/{prefix}*.json"],
    "bootstrap": ["{prefix}/bootstrap/*.md", "{prefix}/bootstrap/*.json"],
    "audits": [
        "docs/governance/audits/{prefix}/**/*.md",
        "docs/governance/audits/{prefix}/**/*.jsonl",
        "docs/governance/audits/aos/**/*.md",
        "docs/governance/audits/aos/**/*.jsonl",
    ],
    "registry_entries": [],
}

ARTIFACT_KIND_MAP = {
    ".md": "markdown",
    ".json": "json",
    ".jsonl": "jsonl",
    ".py": "python",
    ".schema.json": "schema",
    ".txt": "text",
}


def load_registry() -> dict[str, dict]:
    """Load document registry into path→entry map. Uses governance core library."""
    try:
        from ordivon_governance_core.registry import load_registry as _load

        return _load()
    except ImportError:
        # Fallback for environments without core
        registry = {}
        if REGISTRY_PATH.exists():
            with open(REGISTRY_PATH) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        registry[entry.get("path", "")] = entry
                    except json.JSONDecodeError:
                        continue
        return registry


def load_phase_boundary_phases() -> set[str]:
    """Extract phase names from current-phase-boundaries.md."""
    phases = set()
    if PHASE_BOUNDARIES_PATH.exists():
        content = PHASE_BOUNDARIES_PATH.read_text()
        for line in content.split("\n"):
            # Match | **PHASE-NAME** | ...
            if "| **" in line and "** |" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    phase_cell = parts[1].strip()
                    phase_cell = phase_cell.replace("**", "").strip()
                    if phase_cell and not phase_cell.startswith("-"):
                        phases.add(phase_cell)
    return phases


def classify_artifact_kind(path: str) -> str:
    """Classify artifact kind from path and extension."""
    path_lower = path.lower()
    for ext, kind in sorted(ARTIFACT_KIND_MAP.items(), key=lambda x: -len(x[0])):
        if ext == ".schema.json" and path_lower.endswith(".schema.json"):
            return "schema"
    ext = os.path.splitext(path)[1].lower()
    return ARTIFACT_KIND_MAP.get(ext, "unknown")


def classify_surface(path: str) -> str:
    """Classify which governance surface a path belongs to."""
    if "receipts/" in path:
        return "receipt"
    if "schemas/" in path or path.endswith(".schema.json"):
        return "schema"
    if "scripts/" in path and path.endswith(".py"):
        return "script"
    if "fixtures/" in path:
        return "fixture"
    if "evidence/" in path:
        return "evidence"
    if "debts/" in path or path.endswith("debts.jsonl"):
        return "debt"
    if "tests/" in path:
        return "test"
    if "generated/" in path:
        return "generated"
    if "bootstrap/" in path:
        return "bootstrap"
    if "audits/" in path:
        return "audit"
    if "registry" in path and path.endswith(".jsonl"):
        return "registry_entry"
    return "other"


def discover_files(phase_prefix: str) -> list[dict]:
    """Discover all files matching a phase prefix across surfaces."""
    prefix_lower = phase_prefix.lower()
    found = {}  # path -> info dict

    for surface, patterns in SURFACE_PATTERNS.items():
        for pattern in patterns:
            # Substitute prefix (both original and lowercase)
            for pfx in [phase_prefix, prefix_lower]:
                pat = pattern.format(prefix=pfx)
                # Handle ** glob
                if "**" in pat:
                    base_dir = pat.split("/**")[0]
                    full_base = ROOT / base_dir
                    if full_base.exists():
                        for root_dir, dirs, files in os.walk(str(full_base)):
                            for fname in files:
                                fpath = os.path.relpath(os.path.join(root_dir, fname), ROOT)
                                # Filter by phase prefix
                                if prefix_lower not in fpath.lower():
                                    continue
                                if fpath not in found:
                                    found[fpath] = {
                                        "path": fpath,
                                        "surface": classify_surface(fpath),
                                        "kind": classify_artifact_kind(fpath),
                                    }
                else:
                    # Simple glob
                    import glob as globmod

                    for match in globmod.glob(str(ROOT / pat), recursive=False):
                        fpath = os.path.relpath(match, ROOT)
                        if fpath not in found:
                            found[fpath] = {
                                "path": fpath,
                                "surface": classify_surface(fpath),
                                "kind": classify_artifact_kind(fpath),
                            }

    return list(found.values())


def enrich_inventory(files: list[dict], registry: dict, boundary_phases: set, phase_prefix: str) -> dict:
    """Enrich discovered files with registry and phase-boundary metadata."""
    results = []
    missing_registry = []

    phase_prefix.lower()

    for f in files:
        path = f["path"]
        entry = registry.get(path)

        if entry:
            f["registered"] = True
            f["registry_doc_id"] = entry.get("doc_id", "")
            f["registry_phase"] = entry.get("phase", "")
            f["registry_authority"] = entry.get("authority", "")
            f["registry_domain"] = entry.get("authority_domain", "")
            f["registry_role"] = entry.get("authority_role", "")
        else:
            f["registered"] = False
            f["registry_doc_id"] = None
            if path.endswith((".md", ".json", ".jsonl", ".py")) and "generated/" not in path:
                missing_registry.append(path)

        results.append(f)

    # Check phase boundary — does any entry start with or contain the phase prefix?
    found_in_boundary = any(
        bp.upper().startswith(phase_prefix.upper()) or phase_prefix.upper() in bp.upper() for bp in boundary_phases
    )

    return {
        "phase_prefix": phase_prefix,
        "total_files": len(results),
        "registered_count": sum(1 for f in results if f.get("registered")),
        "unregistered_count": sum(1 for f in results if not f.get("registered")),
        "phase_boundary_present": found_in_boundary,
        "files": sorted(results, key=lambda x: (x.get("surface", ""), x["path"])),
        "missing_registry_entries": sorted(missing_registry),
        "missing_phase_boundary_entries": [] if found_in_boundary else [phase_prefix],
    }


def main():
    phase_prefix = None
    phase_family = None
    output_json = "--json" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--phase" and i + 1 < len(sys.argv):
            phase_prefix = sys.argv[i + 1]
        if arg == "--phase-family" and i + 1 < len(sys.argv):
            phase_family = sys.argv[i + 1]

    if not phase_prefix and not phase_family:
        print("Usage: inventory_phase.py --phase <PREFIX> [--json]")
        print("       inventory_phase.py --phase-family <FAMILY> [--json]")
        print("Example: inventory_phase.py --phase AOS")
        print("Example: inventory_phase.py --phase-family AOS")
        return 1

    # Phase-family mode: discover all sub-phases
    if phase_family:
        family_prefix = phase_family.upper()
        family_phases = ["RS", "QA", "FIX", "AUTO", "DOG", "RT", "HARDEN", "PROMOTE"]
        prefixes = [family_prefix]  # base phase
        for sub in family_phases:
            prefixes.append(f"{family_prefix}-{sub}")

        all_files = []
        for pfx in prefixes:
            files = discover_files(pfx)
            all_files.extend(files)

        # Deduplicate
        seen = set()
        unique = []
        for f in all_files:
            if f["path"] not in seen:
                seen.add(f["path"])
                unique.append(f)

        registry = load_registry()
        boundary_phases = load_phase_boundary_phases()
        inventory = enrich_inventory(unique, registry, boundary_phases, phase_family)
        inventory["phase_prefix"] = phase_family
        inventory["phase_family_mode"] = True
        inventory["searched_prefixes"] = prefixes
    else:
        registry = load_registry()
        boundary_phases = load_phase_boundary_phases()
        files = discover_files(phase_prefix)
        inventory = enrich_inventory(files, registry, boundary_phases, phase_prefix)

    if output_json:
        print(json.dumps(inventory, indent=2))
    else:
        print(f"Phase: {phase_prefix}")
        print(f"Files: {inventory['total_files']}")
        print(f"Registered: {inventory['registered_count']}, Unregistered: {inventory['unregistered_count']}")
        print(f"Phase boundary: {'PRESENT' if inventory['phase_boundary_present'] else 'MISSING'}")
        print()

        by_surface = defaultdict(list)
        for f in inventory["files"]:
            by_surface[f.get("surface", "other")].append(f)

        for surface in [
            "receipt",
            "schema",
            "script",
            "fixture",
            "evidence",
            "debt",
            "test",
            "bootstrap",
            "audit",
            "generated",
            "registry_entry",
            "other",
        ]:
            items = by_surface.get(surface, [])
            if items:
                print(f"--- {surface.upper()} ({len(items)}) ---")
                for item in items:
                    reg = "✓" if item.get("registered") else "✗"
                    print(f"  {reg} {item['path']}")
                print()

        if inventory["missing_registry_entries"]:
            print(f"--- MISSING REGISTRY ({len(inventory['missing_registry_entries'])}) ---")
            for path in inventory["missing_registry_entries"]:
                print(f"  ✗ {path}")

        if inventory["missing_phase_boundary_entries"]:
            print("--- MISSING PHASE BOUNDARY ---")
            for p in inventory["missing_phase_boundary_entries"]:
                print(f"  ✗ {p}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
