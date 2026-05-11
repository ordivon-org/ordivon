#!/usr/bin/env python3
"""Generate path map delta between two git commits (GOS-PM-2).

Shows what changed in the governance path map: added nodes, removed nodes,
route changes, authority changes, new exclusions, new blocked files.

Usage:
    python scripts/generate-path-map-delta.py --base HEAD~1 --head HEAD
    python scripts/generate-path-map-delta.py --base HEAD~1 --head HEAD --json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH_MAP = ROOT / "docs/governance/generated/path-map.json"


def load_path_map(ref: str) -> dict | None:
    """Load path map at a given git ref."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:docs/governance/generated/path-map.json"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def compute_delta(base: str, head: str) -> dict:
    base_map = load_path_map(base)
    head_map = load_path_map(head)

    if not base_map:
        # Regenerate at base ref and retry
        subprocess.run(
            ["git", "stash"], capture_output=True, cwd=str(ROOT), timeout=10
        )
        subprocess.run(
            ["git", "checkout", base], capture_output=True, cwd=str(ROOT), timeout=10
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/update-path-map.py")],
            capture_output=True, cwd=str(ROOT), timeout=30
        )
        if PATH_MAP.exists():
            base_map = json.loads(PATH_MAP.read_text())
        subprocess.run(
            ["git", "checkout", "-"], capture_output=True, cwd=str(ROOT), timeout=10
        )
        subprocess.run(
            ["git", "stash", "pop"], capture_output=True, cwd=str(ROOT), timeout=10
        )

    if not head_map:
        head_map = json.loads(PATH_MAP.read_text()) if PATH_MAP.exists() else {"nodes": []}

    if not base_map:
        return {"error": f"Could not load base path map at {base}", "base": base, "head": head}

    base_nodes = {n["path"]: n for n in base_map.get("nodes", [])}
    head_nodes = {n["path"]: n for n in head_map.get("nodes", [])}

    base_paths = set(base_nodes.keys())
    head_paths = set(head_nodes.keys())

    added = head_paths - base_paths
    removed = base_paths - head_paths
    common = base_paths & head_paths

    changed = []
    for p in common:
        bn = base_nodes[p]
        hn = head_nodes[p]
        diffs = {}
        for key in ["route", "authority", "owner", "classification_status", "kind", "doc_type"]:
            bv = bn.get(key, "")
            hv = hn.get(key, "")
            if bv != hv:
                diffs[key] = {"before": bv, "after": hv}
        if diffs:
            changed.append({"path": p, "changes": diffs})

    # Authority changes that require review (PME-7)
    authority_upgrades = [
        c for c in changed
        if "authority" in c["changes"]
        and c["changes"]["authority"]["before"] in ("supporting_evidence", "proposal", "")
        and c["changes"]["authority"]["after"] in ("current_status", "source_of_truth")
    ]

    return {
        "base": base,
        "head": head,
        "stats": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "authority_upgrades_requiring_review": len(authority_upgrades),
        },
        "added_nodes": [{"path": p, "kind": head_nodes[p].get("kind", "?"), "route": head_nodes[p].get("route", "?")} for p in sorted(added)],
        "removed_nodes": [{"path": p, "kind": base_nodes[p].get("kind", "?")} for p in sorted(removed)],
        "changed_nodes": changed,
        "authority_upgrades": authority_upgrades,
    }


def main() -> int:
    as_json = "--json" in sys.argv
    args = {}
    for a in sys.argv[1:]:
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)
            args[k] = v

    base = args.get("base", "HEAD~1")
    head = args.get("head", "HEAD")

    delta = compute_delta(base, head)

    if "error" in delta:
        print(f"✗ {delta['error']}")
        return 1

    if as_json:
        print(json.dumps(delta, indent=2))
        return 0

    print(f"Path Map Delta: {base} → {head}")
    print(f"  Added:    {delta['stats']['added']}")
    print(f"  Removed:  {delta['stats']['removed']}")
    print(f"  Changed:  {delta['stats']['changed']}")
    print(f"  Authority upgrades: {delta['stats']['authority_upgrades_requiring_review']}")

    if delta["added_nodes"]:
        print("\n  Added nodes:")
        for n in delta["added_nodes"][:10]:
            print(f"    + {n['path']} ({n['kind']}, route={n['route']})")

    if delta["removed_nodes"]:
        print("\n  Removed nodes:")
        for n in delta["removed_nodes"][:10]:
            print(f"    - {n['path']} ({n['kind']})")

    if delta["changed_nodes"]:
        print("\n  Changed nodes:")
        for n in delta["changed_nodes"][:10]:
            for k, v in n["changes"].items():
                print(f"    ~ {n['path']}: {k} {v['before']} → {v['after']}")

    if delta["authority_upgrades"]:
        print("\n  ⚠ Authority upgrades (requires review):")
        for n in delta["authority_upgrades"]:
            print(f"    {n['path']}: {n['changes']['authority']['before']} → {n['changes']['authority']['after']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
