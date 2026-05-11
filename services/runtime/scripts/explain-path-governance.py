#!/usr/bin/env python3
"""Explain path governance context — all governance layers for a single file (PM-10).

Usage:
    python scripts/explain-path-governance.py <path>
    python scripts/explain-path-governance.py docs/governance/methodology-core.md
"""

from __future__ import annotations

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/governance/generated"


def explain(filepath: str) -> dict:
    result = {"path": filepath, "layers": {}}

    # Path map
    pm = json.loads((OUTPUT / "path-map.json").read_text())
    pm_node = next((n for n in pm.get("nodes", []) if n["path"] == filepath), None)
    if pm_node:
        result["layers"]["path_map"] = {
            "route": pm_node.get("route"),
            "kind": pm_node.get("kind"),
            "classification": pm_node.get("classification_status"),
        }

    # Registry
    reg_path = ROOT / "docs/governance/document-registry.jsonl"
    if reg_path.exists():
        with open(reg_path) as f:
            for line in f:
                if line.strip():
                    e = json.loads(line)
                    if e["path"] == filepath:
                        result["layers"]["registry"] = {
                            "doc_type": e.get("doc_type"),
                            "owner": e.get("owner"),
                            "authority_domain": e.get("authority_domain"),
                            "authority_role": e.get("authority_role"),
                            "status": e.get("status"),
                        }
                        break

    # Coverage
    cov = json.loads((OUTPUT / "coverage-boundary.json").read_text())
    cov_entry = next((c for c in cov.get("files", []) if c["path"] == filepath), None)
    if cov_entry:
        result["layers"]["coverage"] = {"status": cov_entry.get("coverage_status"), "source": cov_entry.get("source")}

    # RPR findings
    rec = json.loads((OUTPUT / "registry-path-reconciliation.json").read_text())
    rpr = [f for f in rec.get("findings", []) if f.get("path") == filepath]
    if rpr:
        result["layers"]["rpr_findings"] = [{"code": f["code"], "message": f.get("message", "")[:80]} for f in rpr]

    # Not claimed
    result["not_claimed"] = ["approval", "authorization", "full closure"]

    return result


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Usage: explain-path-governance.py <file-path>")
        return 1

    as_json = "--json" in sys.argv
    result = explain(args[0])

    if as_json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Path: {result['path']}")
    for layer, data in result.get("layers", {}).items():
        print(f"  [{layer}]")
        for k, v in data.items():
            if isinstance(v, list):
                for item in v:
                    print(f"    {item}")
            else:
                print(f"    {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
