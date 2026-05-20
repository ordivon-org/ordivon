#!/usr/bin/env python3
"""Generate Ordivon path map from repo reality (GOS-PM-1).

Reads git ls-files, document-registry.jsonl, path-map-rules.json,
governed-exclusions.json, and protected-paths-config.json.
Classifies every tracked file into one of five states:
  governed · generated · excluded · debt_parked · blocked

Output: path-map.json, _path-map.md, path-map.dot (generated views).
These are DERIVED — not source of truth. Manual edits → DRIFT DETECTED.

Usage:
    python scripts/update-path-map.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/governance/generated"
SCHEMA_DIR = ROOT / "docs/governance/schemas"
REGISTRY_PATH = ROOT / "docs/governance/document-registry.jsonl"
RULES_PATH = SCHEMA_DIR / "path-map-rules.json"
EXCLUSIONS_PATH = SCHEMA_DIR / "governed-exclusions.json"
PROTECTED_PATH = SCHEMA_DIR / "protected-paths-config.json"


def git_ls_files() -> list[str]:
    """Get all tracked files."""
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=str(ROOT), timeout=15)
    return [l for l in result.stdout.strip().split("\n") if l]


def observed_files(registry: dict[str, dict]) -> list[str]:
    """Get tracked files plus existing registry files not yet tracked."""
    tracked = set(git_ls_files())
    registry_existing = {
        path for path in registry if path not in tracked and (ROOT / path).exists() and (ROOT / path).is_file()
    }
    return sorted(tracked | registry_existing)


def load_registry() -> dict[str, dict]:
    entries = {}
    with open(REGISTRY_PATH) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                entries[e["path"]] = e
    return entries


def load_rules() -> dict:
    with open(RULES_PATH) as f:
        return json.load(f)


def load_exclusions() -> dict[str, str]:
    with open(EXCLUSIONS_PATH) as f:
        return json.load(f).get("entries", {})


def load_debt_patterns() -> list[dict]:
    """Load open path-pattern debts that intentionally park coverage gaps."""
    patterns: list[dict] = []
    for path in (
        ROOT / "docs/governance/dependency-audit-debts.jsonl",
        ROOT / "docs/governance/verification-debt-ledger.jsonl",
    ):
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    debt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                debt_path = debt.get("path") or debt.get("scope", "")
                if debt.get("status") == "OPEN" and debt_path and ("*" in debt_path or "**" in debt_path):
                    patterns.append(debt)
    return patterns


def load_protected_prefixes() -> list[str]:
    with open(PROTECTED_PATH) as f:
        return json.load(f).get("scan_exclude_prefixes", [])


def match_path(filepath: str, patterns: list[str]) -> bool:
    """Simple glob-style matching: ** matches any depth, * matches within segment."""
    import fnmatch

    return any(fnmatch.fnmatch(filepath, p) for p in patterns)


def is_protected_path(filepath: str, governed_dirs: list[str]) -> bool:
    """A path is protected if it's in a governed directory structure."""
    for d in governed_dirs:
        if filepath.startswith(d.rstrip("/") + "/") or filepath == d.rstrip("/"):
            return True
    return False


def classify(
    filepath: str,
    registry: dict,
    rules: dict,
    exclusions: dict,
    debt_patterns: list[dict],
    governed_dirs: list[str],
    tracked_files: set[str],
) -> dict:
    """Classify a single file into a path-map node."""
    node = {
        "path": filepath,
        "source_refs": ["git ls-files"],
        "classification_status": "unclassified",
    }
    if filepath in registry and filepath not in tracked_files:
        node["source_refs"] = ["document-registry.jsonl", "working tree"]

    # 1. Explicit exclusion (exact path OR directory prefix)
    is_excluded = filepath in exclusions
    if not is_excluded:
        for excl_path in exclusions:
            if excl_path.endswith("/") and filepath.startswith(excl_path):
                is_excluded = True
                break
    if is_excluded:
        node["kind"] = "explicit_exclusion"
        node["classification_status"] = "excluded"
        # Find matching exclusion (exact or directory prefix)
        if filepath in exclusions:
            node["reason"] = exclusions[filepath]
        else:
            for excl_path, reason in exclusions.items():
                if excl_path.endswith("/") and filepath.startswith(excl_path):
                    node["reason"] = reason
                    break
            else:
                node["reason"] = "excluded by directory rule"
        return node

    # 2. Generated file
    if "/generated/" in filepath or Path(filepath).name.startswith("_"):
        node["kind"] = "generated_view"
        node["classification_status"] = "generated"
        node["must_not_be_source_of_truth"] = True
        return node

    # 3. Registered document
    if filepath in registry:
        reg = registry[filepath]
        node["kind"] = "document"
        node["classification_status"] = "governed"
        node["doc_type"] = reg.get("doc_type", "unknown")
        node["owner"] = reg.get("owner", "")
        node["authority"] = reg.get("doc_authority", reg.get("authority", ""))
        node["lifecycle"] = reg.get("status", "unknown")
        node["source_refs"].append("document-registry.jsonl")

        # Match route
        routes = rules.get("routes", [])
        for route in routes:
            paths = route.get("match", {}).get("paths", [])
            if match_path(filepath, paths):
                node["route"] = route["id"]
                break
        if "route" not in node:
            node["route"] = "unrouted"
        return node

    # 4. Checker (CHECKER.md, run.py, and support files)
    if filepath.startswith("checkers/"):
        node["kind"] = "checker"
        node["classification_status"] = "governed"
        node["route"] = "governance-core"
        node["source_refs"].append("checker discovery")
        return node

    # 5. CI workflow
    if filepath.startswith(".github/workflows/") and filepath.endswith(".yml"):
        node["kind"] = "ci_gate"
        node["classification_status"] = "governed"
        node["route"] = "governance-core"
        return node

    # 6. Ledger (knowledge asset)
    ledger_patterns = [
        "lesson-ledger.jsonl",
        "dependency-audit-debts.jsonl",
        "candidate-rule-drafts.jsonl",
        "lesson-extraction-log.jsonl",
        "verification-debt-ledger.jsonl",
    ]
    if any(filepath.endswith(p) for p in ledger_patterns):
        node["kind"] = "knowledge_asset"
        node["classification_status"] = "governed"
        node["route"] = "knowledge-assets"
        node["source_refs"].append("ledger discovery")
        return node

    # 7. Source code
    code_prefixes = [
        "src/",
        "governance_engine/",
        "state/",
        "domains/",
        "capabilities/",
        "execution/",
        "shared/",
        "packs/",
        "adapters/",
    ]
    if any(filepath.startswith(p) for p in code_prefixes):
        node["kind"] = "source_code"
        node["classification_status"] = "governed"
        node["route"] = "source-code"
        node["governed_by"] = "architecture-boundaries checker"
        return node

    # 8. Open path-pattern debts. Debt-park before protected-path blocking
    # so acknowledged A4 gaps remain visible without masquerading as closure.
    for debt in debt_patterns:
        if match_path(filepath, [debt.get("path") or debt.get("scope", "")]):
            node["kind"] = "debt_parked"
            node["classification_status"] = "debt_parked"
            node["debt_id"] = debt.get("debt_id", "")
            node["finding"] = "PM-9 DEBT_OR_EXCLUSION_REQUIRED"
            node["source_refs"].append("debt ledger")
            return node

    # 9. Schema file
    if filepath.startswith("docs/governance/schemas/") or filepath.startswith("src/ordivon_verify/schemas/"):
        node["kind"] = "schema"
        node["classification_status"] = "governed"
        node["route"] = "config-and-schemas"
        return node

    # 10. Protected path → BLOCKED
    if is_protected_path(filepath, governed_dirs):
        node["kind"] = "blocked"
        node["classification_status"] = "blocked"
        node["finding"] = "PM-2 UNCLASSIFIED_PROTECTED_PATH"
        node["message"] = "File in governed directory with no route and no exclusion"
        return node

    # 11. Non-protected → debt or exclusion required
    node["kind"] = "unclassified"
    node["classification_status"] = "debt_parked"
    node["finding"] = "PM-9 DEBT_OR_EXCLUSION_REQUIRED"
    return node


def compute_edges(nodes: list[dict], registry: dict) -> list[dict]:
    """Derive edges from checker coverage, CI jobs, and registry relations."""
    edges = []

    # checker → document edges
    for node in nodes:
        if node.get("kind") == "checker":
            checker_name = node["path"].split("/")[1]
            for doc_node in nodes:
                checked_by = doc_node.get("checked_by", [])
                if checker_name in checked_by:
                    edges.append({
                        "from": node["path"],
                        "to": doc_node["path"],
                        "type": "checks",
                    })

    # registry edge: document → registry source
    for node in nodes:
        if "document-registry.jsonl" in node.get("source_refs", []):
            edges.append({
                "from": node["path"],
                "to": "docs/governance/document-registry.jsonl",
                "type": "registered_in",
            })

    return edges


def generate_markdown(nodes: list[dict], stats: dict) -> str:
    """Generate _path-map.md."""
    lines = [
        "# Generated Ordivon Path Map",
        "",
        "> Status: GENERATED_VIEW",
        f"> Generated: {stats['generated_at']}",
        "> Source: git ls-files + document-registry.jsonl + path-map-rules.json",
        "> Do not edit manually.",
        "",
        "## Stats",
        f"- Observed files: {stats['observed_files']}",
        f"- Tracked files: {stats['tracked_files']}",
        f"- Registry working-tree files: {stats['registry_working_tree_files']}",
        f"- Governed: {stats['governed']}",
        f"- Generated views: {stats['generated']}",
        f"- Excluded: {stats['excluded']}",
        f"- Blocked: {stats['blocked']}",
        f"- Debt-parked: {stats['debt_parked']}",
        "",
        "## Governed Nodes",
    ]

    # Group by route
    by_route = {}
    for n in nodes:
        route = n.get("route", "ungrouped")
        by_route.setdefault(route, []).append(n)

    for route in sorted(by_route):
        group = by_route[route]
        if not any(n.get("classification_status") == "governed" for n in group):
            continue
        lines.append(f"### {route}")
        for n in sorted(group, key=lambda x: x["path"]):
            if n.get("classification_status") != "governed":
                continue
            kind = n.get("kind", "?")
            owner = n.get("owner", "-")
            lines.append(f"- `{n['path']}` ({kind}, owner={owner})")

    lines.append("")
    lines.append("## Blocked / Debt-Parked")
    for n in nodes:
        if n.get("classification_status") in ("blocked", "debt_parked"):
            lines.append(f"- `{n['path']}`: {n.get('finding', '?')}")

    return "\n".join(lines)


def generate_dot(nodes: list[dict], edges: list[dict]) -> str:
    """Generate path-map.dot (Graphviz format)."""
    lines = [
        "digraph OrdivonPathMap {",
        '  rankdir="LR";',
        '  node [shape=box,style=filled,fontname="JetBrains Mono"];',
    ]
    for n in nodes:
        if n.get("classification_status") != "governed":
            continue
        label = n["path"].split("/")[-1][:40]
        color = {
            "document": "#a78bfa",
            "checker": "#34d399",
            "ci_gate": "#22d3ee",
            "schema": "#fbbf24",
            "source_code": "#94a3b8",
            "knowledge_asset": "#fb7185",
        }.get(n.get("kind", ""), "#94a3b8")
        node_id = n["path"].replace("/", "_").replace(".", "_")
        lines.append(f'  {node_id} [label="{label}",fillcolor="{color}20",color="{color}"];')
    for e in edges[:100]:
        from_id = e["from"].replace("/", "_").replace(".", "_")
        to_id = e["to"].replace("/", "_").replace(".", "_")
        lines.append(f'  {from_id} -> {to_id} [label="{e["type"]}"];')
    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    print("Reading sources...")
    registry = load_registry()
    tracked_files = set(git_ls_files())
    files = observed_files(registry)
    registry_working_tree_files = len(set(files) - tracked_files)
    rules = load_rules()
    exclusions = load_exclusions()
    debt_patterns = load_debt_patterns()
    governed_dirs = [
        "docs/ai",
        "docs/governance",
        "docs/architecture",
        "docs/product",
        "docs/decisions",
        "checkers",
        ".github/workflows",
    ]

    print(f"Classifying {len(files)} observed files...")
    nodes = []
    for fp in files:
        node = classify(fp, registry, rules, exclusions, debt_patterns, governed_dirs, tracked_files)
        nodes.append(node)

    stats = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "observed_files": len(files),
        "tracked_files": len(tracked_files),
        "registry_working_tree_files": registry_working_tree_files,
        "governed": sum(1 for n in nodes if n["classification_status"] == "governed"),
        "generated": sum(1 for n in nodes if n["classification_status"] == "generated"),
        "excluded": sum(1 for n in nodes if n["classification_status"] == "excluded"),
        "blocked": sum(1 for n in nodes if n["classification_status"] == "blocked"),
        "debt_parked": sum(1 for n in nodes if n["classification_status"] == "debt_parked"),
    }

    edges = compute_edges(nodes, registry)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write path-map.json
    output = {
        "generated_at": stats["generated_at"],
        "generator": "scripts/update-path-map.py",
        "source_refs": [
            "git ls-files",
            "docs/governance/document-registry.jsonl",
            "docs/governance/schemas/path-map-rules.json",
            "docs/governance/schemas/governed-exclusions.json",
        ],
        "stats": stats,
        "nodes": nodes,
        "edges": edges,
    }
    json_path = OUTPUT_DIR / "path-map.json"
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(f"Generated {json_path}")

    # Write _path-map.md
    md_path = OUTPUT_DIR / "_path-map.md"
    md_content = generate_markdown(nodes, stats)
    md_path.write_text(md_content + "\n")
    print(f"Generated {md_path}")

    # Write path-map.dot
    dot_path = OUTPUT_DIR / "path-map.dot"
    dot_content = generate_dot(nodes, edges)
    dot_path.write_text(dot_content + "\n")
    print(f"Generated {dot_path}")

    print(
        f"\nStats: {stats['tracked_files']} files → "
        f"{stats['observed_files']} observed, "
        f"{stats['governed']} governed, {stats['generated']} generated, "
        f"{stats['excluded']} excluded, {stats['blocked']} blocked, "
        f"{stats['debt_parked']} debt-parked"
    )

    return 1 if stats["blocked"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
