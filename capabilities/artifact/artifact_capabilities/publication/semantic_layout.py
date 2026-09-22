from __future__ import annotations

from collections import Counter
from typing import Any


def build_semantic_layout_graph(inventory: dict[str, Any]) -> dict[str, Any]:
    """Project caption-like inventory rows into a lightweight document graph."""

    if inventory.get("kind") != "publication-carrier-inventory":
        raise ValueError("invalid publication carrier inventory")

    nodes: list[dict[str, Any]] = []
    for page in inventory.get("pages", []):
        nodes.append(
            {
                "id": f"page:{page['page']}",
                "type": "PAGE",
                "page": page["page"],
            }
        )
    for figure in inventory.get("figures", []):
        nodes.append(
            {
                "id": f"figure:{figure['id']}",
                "type": "FIGURE_CAPTION",
                "page": figure["page"],
                "line": figure["line"],
                "text": figure["captionLine"],
            }
        )
    for table in inventory.get("tables", []):
        nodes.append(
            {
                "id": f"table:{table['id']}",
                "type": "TABLE_CAPTION",
                "page": table["page"],
                "line": table["line"],
                "text": table["captionLine"],
            }
        )

    return {
        "schemaVersion": 1,
        "kind": "publication-semantic-layout-graph",
        "truthRole": "text-layer-layout-projection-not-manuscript-semantic-truth",
        "pdfSha256": inventory["pdfSha256"],
        "nodes": nodes,
    }


def evaluate_semantic_layout_graph(graph: dict[str, Any]) -> dict[str, Any]:
    if graph.get("kind") != "publication-semantic-layout-graph":
        raise ValueError("invalid semantic layout graph")

    findings: list[dict[str, Any]] = []
    ids = [node["id"] for node in graph.get("nodes", []) if node["type"] != "PAGE"]
    counts = Counter(ids)
    for node_id, count in sorted(counts.items()):
        if count > 1:
            findings.append(
                {
                    "id": f"duplicate-node:{node_id}",
                    "severity": "MAJOR",
                    "predicate": "CAPTION_IDENTITY_UNIQUE",
                    "evidence": {"count": count},
                }
            )

    standing = "FAIL" if findings else "PASS"
    return {
        "schemaVersion": 1,
        "kind": "publication-semantic-layout-evaluation",
        "pdfSha256": graph["pdfSha256"],
        "findings": findings,
        "standing": standing,
        "nonClaims": [
            "text-layer caption identity does not prove visual caption attachment",
            "semantic-layout PASS does not establish figure or table readability",
        ],
    }
