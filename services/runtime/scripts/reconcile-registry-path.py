#!/usr/bin/env python3
"""Registry–Path Reconciliation — compare governance claims with observations (GOS-PM-2).

Registry declares what an object IS (doc_type, owner, authority).
Path Map observes where an object ROUTES (kind, route, classification).
Inconsistency = governance drift, dispatched via A1-A4.
Reconciled ≠ Synchronized.

Usage:
    python scripts/reconcile-registry-path.py
    python scripts/reconcile-registry-path.py --json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs/governance/document-registry.jsonl"
PATH_MAP_PATH = ROOT / "docs/governance/generated/path-map.json"
RULES_PATH = ROOT / "docs/governance/schemas/path-map-rules.json"
EXCLUSIONS_PATH = ROOT / "docs/governance/schemas/governed-exclusions.json"
OUTPUT_DIR = ROOT / "docs/governance/generated"

# Authority risk tiers
AUTHORITY_RISK = {
    "source_of_truth": 5,
    "current_status": 4,
    "supporting_evidence": 2,
    "historical_record": 2,
    "proposal": 1,
    "example": 1,
    "archive": 0,
}

# Route risk levels
ROUTE_RISK = {
    "governance-core": 5,
    "config-and-schemas": 5,
    "knowledge-assets": 4,
    "ai-boundaries": 3,
    "product-docs": 2,
    "source-code": 1,
    "unrouted": 0,
}


def load_registry() -> dict[str, dict]:
    entries = {}
    with open(REGISTRY_PATH) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                entries[e["path"]] = e
    return entries


def load_path_map() -> list[dict]:
    return json.loads(PATH_MAP_PATH.read_text()).get("nodes", [])


def load_rules() -> dict:
    return json.loads(RULES_PATH.read_text())


def load_exclusions() -> list[str]:
    return list(json.loads(EXCLUSIONS_PATH.read_text()).get("entries", {}).keys())


def reconcile() -> tuple[list[dict], dict]:
    registry = load_registry()
    pm_nodes = {n["path"]: n for n in load_path_map()}
    rules = load_rules()
    exclusions = load_exclusions()

    findings = []
    stats = {
        "registry_entries": len(registry),
        "path_map_nodes": len(pm_nodes),
        "in_both": 0,
        "only_registry": 0,
        "only_path_map": 0,
        "findings_total": 0,
    }

    reg_paths = set(registry.keys())
    pm_paths = set(pm_nodes.keys())
    in_both = reg_paths & pm_paths
    stats["in_both"] = len(in_both)
    stats["only_registry"] = len(reg_paths - pm_paths)
    stats["only_path_map"] = len(pm_paths - reg_paths)

    # RPR-1: Registry entry has claim but file doesn't exist in git
    for path in sorted(reg_paths - pm_paths):
        findings.append({
            "code": "RPR-1",
            "severity": "blocking",
            "path": path,
            "registry_claim": {"doc_type": registry[path].get("doc_type", "?"), "status": registry[path].get("status", "?")},
            "path_observation": None,
            "disposition": "A1",
            "message": f"Registry claims '{path}' exists but path map has no such node",
        })

    # RPR-2: File exists in governed area but no registry entry
    governed_prefixes = ["docs/governance/", "docs/ai/", "docs/architecture/", "docs/product/"]
    for path in sorted(pm_paths - reg_paths):
        node = pm_nodes[path]
        if node.get("classification_status") == "governed" and node.get("kind") in ("document",):
            is_governed = any(path.startswith(p) for p in governed_prefixes)
            if is_governed:
                findings.append({
                    "code": "RPR-2",
                    "severity": "blocking",
                    "path": path,
                    "registry_claim": None,
                    "path_observation": {"kind": node.get("kind"), "route": node.get("route")},
                    "disposition": "A1",
                    "message": f"Governed path '{path}' has no registry entry",
                })

    # RPR-3/4/5/8: Check documents that are in both registry and path map
    for path in sorted(in_both):
        reg = registry[path]
        node = pm_nodes[path]

        # Only reconcile governed nodes — skip excluded/generated/debt-parked
        if node.get("classification_status") != "governed":
            continue

        reg_doc_type = reg.get("doc_type", "")
        reg_authority = reg.get("doc_authority", reg.get("authority", ""))
        reg_owner = reg.get("owner", "")
        node_route = node.get("route", "")
        node_kind = node.get("kind", "")

        # RPR-3: Doc type vs route mismatch
        route_doc_type_map = {
            "governance-core": ["governance_pack", "methodology", "template", "checker", "tooling", "proposal", "receipt", "ledger", "root_context", "architecture", "design_spec", "schema"],
            "ai-boundaries": ["ai_onboarding", "phase_boundary", "runtime", "boundary", "context", "supporting_evidence", "architecture", "design_spec", "current-system-map", "knowledge-map", "reading-graph", "template", "tooling"],
            "product-docs": ["product", "architecture", "design_spec", "stage_summit", "proposal", "runbook", "receipt"],
            "knowledge-assets": ["ledger", "lesson"],
            "generated-views": ["generated_view"],
            "config-and-schemas": ["schema"],
            "governance-core": ["governance_pack", "methodology", "template", "checker", "tooling", "proposal", "receipt", "ledger", "root_context", "architecture", "design_spec", "schema", "supporting_evidence", "inventory", "triage", "boundary", "red_team", "tracker"],
        }

        expected_types = route_doc_type_map.get(node_route, [])
        if expected_types and reg_doc_type not in expected_types and node_route != "unrouted":
            findings.append({
                "code": "RPR-3",
                "severity": "degraded",
                "path": path,
                "registry_claim": {"doc_type": reg_doc_type},
                "path_observation": {"route": node_route},
                "disposition": "A2",
                "message": f"doc_type '{reg_doc_type}' may not fit route '{node_route}' (expects: {expected_types})",
            })

        # RPR-4: Authority vs route risk mismatch
        reg_risk = AUTHORITY_RISK.get(reg_authority, 0)
        route_risk = ROUTE_RISK.get(node_route, 0)
        if reg_risk >= 4 and route_risk <= 1:
            findings.append({
                "code": "RPR-4",
                "severity": "blocking",
                "path": path,
                "registry_claim": {"authority": reg_authority, "risk_tier": reg_risk},
                "path_observation": {"route": node_route, "risk_tier": route_risk},
                "disposition": "A3",
                "message": f"Authority '{reg_authority}' (risk {reg_risk}) too high for route '{node_route}' (risk {route_risk})",
            })

        # RPR-5: Owner claim unsupported
        if reg_owner and reg_owner in ("", "unknown", "phase-X"):
            findings.append({
                "code": "RPR-5",
                "severity": "degraded",
                "path": path,
                "disposition": "A1",
                "message": f"Owner claim '{reg_owner}' appears unsupported",
            })

        # RPR-8: Path rule gap — unrouted governed document
        if node_route == "unrouted" and node.get("classification_status") == "governed":
            findings.append({
                "code": "RPR-8",
                "severity": "degraded",
                "path": path,
                "disposition": "A2",
                "message": f"No path-map rule covers '{path}' with doc_type '{reg_doc_type}'",
            })

    stats["findings_total"] = len(findings)
    return findings, stats


def main() -> int:
    as_json = "--json" in sys.argv
    findings, stats = reconcile()

    # Generate output
    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/reconcile-registry-path.py",
        "stats": stats,
        "findings": findings,
    }

    json_out = OUTPUT_DIR / "registry-path-reconciliation.json"
    json_out.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")

    if as_json:
        print(json.dumps(output, indent=2))
        return 0

    blocking = [f for f in findings if f["severity"] == "blocking"]
    degraded = [f for f in findings if f["severity"] == "degraded"]

    print(f"Registry–Path Reconciliation")
    print(f"  Registry: {stats['registry_entries']} entries · Path Map: {stats['path_map_nodes']} nodes")
    print(f"  In both: {stats['in_both']} · Only registry: {stats['only_registry']} · Only path map: {stats['only_path_map']}")
    print(f"  Findings: {len(blocking)} BLOCKING, {len(degraded)} DEGRADED")

    if blocking:
        print(f"\n❌ BLOCKING:")
        for f in blocking:
            print(f"  [{f['code']}] {f['path']}: {f['message']}")

    if degraded:
        print(f"\n⚠ DEGRADED:")
        for f in degraded[:10]:
            print(f"  [{f['code']}] {f['path']}: {f['message']}")

    print(f"\nOutput: {json_out}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
