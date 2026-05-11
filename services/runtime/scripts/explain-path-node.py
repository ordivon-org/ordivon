#!/usr/bin/env python3
"""Explain a single node in the generated Ordivon path map (GOS-PM-1).

Obsidian local graph / Backstage entity page pattern:
given a file path, show its governance context — route, owner, authority,
checkers, CI gates, debts, lessons, related nodes.

Usage:
    python scripts/explain-path-node.py docs/governance/methodology-core.md
    python scripts/explain-path-node.py --json docs/governance/methodology-core.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH_MAP = ROOT / "docs/governance/generated/path-map.json"
REGISTRY = ROOT / "docs/governance/document-registry.jsonl"


def load_path_map() -> dict:
    if not PATH_MAP.exists():
        print(f"ERROR: {PATH_MAP} not found. Run: python scripts/update-path-map.py")
        sys.exit(1)
    return json.loads(PATH_MAP.read_text())


def load_registry() -> dict:
    entries = {}
    if REGISTRY.exists():
        with open(REGISTRY) as f:
            for line in f:
                if line.strip():
                    e = json.loads(line)
                    entries[e["path"]] = e
    return entries


def explain(target: str) -> dict:
    pm = load_path_map()
    registry = load_registry()
    nodes = {n["path"]: n for n in pm["nodes"]}
    edges = pm.get("edges", [])

    node = nodes.get(target)
    if not node:
        return {"error": f"Path not found in path map: {target}", "suggestions": [p for p in nodes if target.split("/")[-1] in p][:5]}

    # Incoming edges
    incoming = [e for e in edges if e.get("to") == target]
    outgoing = [e for e in edges if e.get("from") == target]

    # Registry metadata
    reg = registry.get(target, {})

    return {
        "path": target,
        "kind": node.get("kind", "?"),
        "route": node.get("route", "unrouted"),
        "classification": node.get("classification_status", "?"),
        "doc_type": reg.get("doc_type", node.get("doc_type", "-")),
        "owner": reg.get("owner", node.get("owner", "-")),
        "authority": reg.get("authority", node.get("authority", "-")),
        "lifecycle": reg.get("status", node.get("lifecycle", "-")),
        "source_refs": node.get("source_refs", []),
        "incoming_edges": [{"from": e["from"], "type": e["type"]} for e in incoming],
        "outgoing_edges": [{"to": e["to"], "type": e["type"]} for e in outgoing],
    }


def main() -> int:
    as_json = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args:
        print("Usage: python scripts/explain-path-node.py <file-path>")
        print("       python scripts/explain-path-node.py --json <file-path>")
        return 1

    result = explain(args[0])

    if "error" in result:
        print(f"✗ {result['error']}")
        if result.get("suggestions"):
            print("  Similar paths:")
            for s in result["suggestions"]:
                print(f"    {s}")
        return 1

    if as_json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Path:         {result['path']}")
    print(f"Kind:         {result['kind']}")
    print(f"Route:        {result['route']}")
    print(f"Status:       {result['classification']}")
    print(f"Doc type:     {result['doc_type']}")
    print(f"Owner:        {result['owner']}")
    print(f"Authority:    {result['authority']}")
    print(f"Lifecycle:    {result['lifecycle']}")
    print(f"Sources:      {', '.join(result['source_refs'])}")

    if result["incoming_edges"]:
        print("\nReferenced by:")
        for e in result["incoming_edges"]:
            print(f"  ← {e['from']} ({e['type']})")

    if result["outgoing_edges"]:
        print("\nReferences:")
        for e in result["outgoing_edges"]:
            print(f"  → {e['to']} ({e['type']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
