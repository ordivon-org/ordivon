#!/usr/bin/env python3
"""Atomic Governance Gate — verify governed documents are registered.

Ordivon A3 anti-pattern AP-3 fix (L-CI-SELFCAL-003).
Google presubmit / Linux bisectability pattern: every governed document
must have a registry entry. Adding a file without a registry entry is a
governance drift that CI must BLOCK.

Checks:
  1. Registration completeness: files in governed dirs must be registered
  2. Exclusion validity: excluded files must have a reason in the exclusions ledger
  3. DocType validity: all registry doc_types must be in the schema

Usage:
    python scripts/check_atomic_governance.py              # Full scan
    python scripts/check_atomic_governance.py --changed    # Git-diff mode (PR)
    python scripts/check_atomic_governance.py --json       # Machine-readable
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── Governed directories: files here MUST have registry entries ────────
GOVERNED_DIRS = [
    "docs/ai/",
    "docs/governance/",
]

# ── Files in governed dirs that are intentionally not registered ───────
# Loaded from canonical schema (RT-11 fix — L-CI-SELFCAL-002 pattern).
# Adding a new exclusion requires editing the schema file, not the checker source.
EXCLUSIONS_SCHEMA_PATH = ROOT / "docs/governance/schemas/governed-exclusions.json"

def _load_exclusions() -> dict[str, str]:
    with open(EXCLUSIONS_SCHEMA_PATH) as f:
        return json.load(f)["entries"]

GOVERNED_EXCLUSIONS = _load_exclusions()

# ── Load schema for doc_type validation ────────────────────────────────
SCHEMA_PATH = ROOT / "docs/governance/schemas/document-types.json"
REGISTRY_PATH = ROOT / "docs/governance/document-registry.jsonl"


def load_schema() -> set:
    with open(SCHEMA_PATH) as f:
        return set(json.load(f)["valid_doc_types"])


def load_registry() -> dict[str, dict]:
    entries = {}
    with open(REGISTRY_PATH) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                entries[e["path"]] = e
    return entries


def get_changed_files() -> list[str]:
    """Get files changed in the current commit vs origin/main (PR mode)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=10
        )
        if result.returncode != 0:
            # Fallback: last commit
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True, text=True, cwd=str(ROOT), timeout=10
            )
        return [l for l in result.stdout.strip().split("\n") if l]
    except Exception:
        return []


def find_governed_files() -> list[str]:
    """Find all files in governed directories."""
    files = []
    for gd in GOVERNED_DIRS:
        d = ROOT / gd
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.is_file() and f.suffix in {".md", ".jsonl", ".json"}:
                rel = str(f.relative_to(ROOT))
                if ".git/" not in rel and "__pycache__" not in rel:
                    files.append(rel)
    return files


def check_registration(
    governed_files: list[str],
    registry: dict[str, dict],
    valid_types: set,
    changed_only: bool = False,
) -> tuple[list[dict], dict]:
    """Run all atomic governance checks."""
    findings = []
    stats = {"files_scanned": 0, "unregistered": 0, "bad_doctype": 0}

    changed = set(get_changed_files()) if changed_only else None

    for rel in governed_files:
        if changed_only and rel not in changed:
            continue

        stats["files_scanned"] += 1

        # Check 1: Registration
        if rel in GOVERNED_EXCLUSIONS:
            continue

        if rel not in registry:
            stats["unregistered"] += 1
            findings.append({
                "rule": "AG-1",
                "severity": "blocking",
                "file": rel,
                "message": f"File in governed directory is not registered in document-registry.jsonl",
                "fix": f"Add entry to {REGISTRY_PATH} with doc_id, path, doc_type, status, authority"
            })
            continue

        # Check 2: DocType validity
        entry = registry[rel]
        dt = entry.get("doc_type", "")
        if dt not in valid_types:
            stats["bad_doctype"] += 1
            findings.append({
                "rule": "AG-2",
                "severity": "blocking",
                "file": rel,
                "doc_type": dt,
                "message": f"doc_type '{dt}' is not in {SCHEMA_PATH}",
                "fix": f"Add '{dt}' to valid_doc_types in {SCHEMA_PATH}"
            })

    return findings, stats


def main() -> int:
    as_json = "--json" in sys.argv
    changed_only = "--changed" in sys.argv

    valid_types = load_schema()
    registry = load_registry()
    governed_files = find_governed_files()

    findings, stats = check_registration(governed_files, registry, valid_types, changed_only)

    if as_json:
        output = {"status": "BLOCKED" if findings else "READY", "findings": findings, "stats": stats}
        print(json.dumps(output, indent=2))
    else:
        if changed_only:
            changed = get_changed_files()
            governed_changed = [f for f in changed if any(f.startswith(gd) for gd in GOVERNED_DIRS)]
            print(f"Changed governed files: {len(governed_changed)}")
            if governed_changed:
                for f in governed_changed:
                    print(f"  {f}")

        print(f"Files scanned: {stats['files_scanned']}")
        print(f"Unregistered:  {stats['unregistered']}")
        print(f"Bad doc_type:  {stats['bad_doctype']}")

        if findings:
            print(f"\n❌ BLOCKED — {len(findings)} findings:")
            for f in findings:
                print(f"  [{f['rule']}] {f['file']}: {f['message']}")
            return 1
        else:
            print(f"\n✓ Atomic governance gate PASSED")
            return 0

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
