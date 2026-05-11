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
TAXONOMY_PATH = ROOT / "docs/governance/schemas/authority-taxonomy.json"
ROUTE_TAXONOMY_PATH = ROOT / "docs/governance/schemas/route-taxonomy.json"
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


def load_taxonomy() -> dict:
    return json.loads(TAXONOMY_PATH.read_text())


def load_route_taxonomy() -> dict:
    return json.loads(ROUTE_TAXONOMY_PATH.read_text())


def reconcile() -> tuple[list[dict], dict]:
    registry = load_registry()
    pm_nodes = {n["path"]: n for n in load_path_map()}

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
            "registry_claim": {
                "doc_type": registry[path].get("doc_type", "?"),
                "status": registry[path].get("status", "?"),
            },
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

    taxonomy = load_taxonomy()

    # RPR-3/4/5/8: Check documents that are in both registry and path map
    for path in sorted(in_both):
        reg = registry[path]
        node = pm_nodes[path]

        # Only reconcile governed nodes — skip excluded/generated/debt-parked
        if node.get("classification_status") != "governed":
            continue

        reg_doc_type = reg.get("doc_type", "")
        reg_doc_type = reg.get("doc_type", "")
        reg_owner = reg.get("owner", "")
        reg_owner = reg.get("owner", "")
        node_route = node.get("route", "")

        # RPR-3: Doc-type/route compatibility (PM-4: route taxonomy)
        route_tax = load_route_taxonomy()
        route_def = route_tax.get("routes", {}).get(node_route, {})
        allowed_types = route_def.get("allowed_doc_types", [])
        forbidden_types = route_def.get("forbidden_doc_types", [])

        # Only check if route exists in taxonomy and is not unrouted
        if node_route in route_tax.get("routes", {}) and node_route != "unrouted":
            if reg_doc_type and allowed_types and reg_doc_type not in allowed_types:
                findings.append({
                    "code": "RPR-3A",
                    "severity": "degraded",
                    "path": path,
                    "registry_claim": {"doc_type": reg_doc_type},
                    "path_observation": {"route": node_route, "allowed_doc_types": allowed_types},
                    "disposition": route_def.get("mismatch_disposition", "A2"),
                    "message": f"doc_type '{reg_doc_type}' not in route '{node_route}' allowed_doc_types",
                })
            elif reg_doc_type and forbidden_types and reg_doc_type in forbidden_types:
                findings.append({
                    "code": "RPR-3F",
                    "severity": "blocking" if route_def.get("must_not_be_source_of_truth") else "degraded",
                    "path": path,
                    "registry_claim": {"doc_type": reg_doc_type},
                    "path_observation": {"route": node_route, "forbidden_doc_types": forbidden_types},
                    "disposition": "A1_OR_A2",
                    "message": f"doc_type '{reg_doc_type}' is forbidden for route '{node_route}'",
                })

        # RPR-4: Authority domain/role vs route compatibility (GOS-PM-3)
        auth_domain = reg.get("authority_domain", "")
        auth_role = reg.get("authority_role", "")
        compatibility = taxonomy.get("compatibility_rules", {})

        # Check domain-role-route compatibility
        incompatible = False
        if node.get("kind") == "generated_view" and auth_role in compatibility.get("generated_view_cannot_be", []):
            incompatible = True
        elif auth_domain == "implementation" and node_route not in compatibility.get(
            "implementation_source_only_for", []
        ):
            incompatible = True
        elif auth_domain == "schema" and node_route not in compatibility.get("schema_source_only_for", []):
            incompatible = True
        elif auth_role == "doc_source_of_truth" and node_route not in compatibility.get(
            "doc_source_of_truth_only_for", []
        ):
            incompatible = True
        elif auth_role == "active_policy" and node_route not in compatibility.get("active_policy_only_for", []):
            incompatible = True

        if incompatible:
            findings.append({
                "code": "RPR-4",
                "severity": "blocking",
                "path": path,
                "registry_claim": {"authority_domain": auth_domain, "authority_role": auth_role},
                "path_observation": {"route": node_route, "kind": node.get("kind")},
                "disposition": "A3",
                "message": f"Authority domain={auth_domain} role={auth_role} incompatible with route={node_route}",
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

    print("Registry–Path Reconciliation")
    print(f"  Registry: {stats['registry_entries']} entries · Path Map: {stats['path_map_nodes']} nodes")
    print(
        f"  In both: {stats['in_both']} · Only registry: {stats['only_registry']} · Only path map: {stats['only_path_map']}"
    )
    print(f"  Findings: {len(blocking)} BLOCKING, {len(degraded)} DEGRADED")

    if blocking:
        print("\n❌ BLOCKING:")
        for f in blocking:
            print(f"  [{f['code']}] {f['path']}: {f['message']}")

    if degraded:
        print("\n⚠ DEGRADED:")
        for f in degraded[:10]:
            print(f"  [{f['code']}] {f['path']}: {f['message']}")

    print(f"\nOutput: {json_out}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
