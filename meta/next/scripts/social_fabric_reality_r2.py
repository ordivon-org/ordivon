#!/usr/bin/env python3
"""Reality-completion projections for Ordivon Social Fabric.

REAL20 projects existing W3C PROV JSON-LD without minting a new provenance ontology.
REAL21 builds a bounded transactive-memory locator from explicit natural-owner facts.
REAL22 preserves owner-native currentness/supersession without laundering Git recency
or Host Task state into semantic currentness.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from social_fabric_r1 import canonical_digest

SCHEMA_VERSION = 1
CUT_KIND = "ordivon.social-fabric-reality-owner-cut"
PROV_KIND = "ordivon.social-fabric-prov-projection"
MEMORY_KIND = "ordivon.social-fabric-transactive-memory-projection"
FRESHNESS_KIND = "ordivon.social-fabric-freshness-projection"

OWNER_STANDINGS = {
    "POINT_IN_TIME_OBSERVED",
    "CURRENT_DECLARED",
    "HISTORICAL_NOT_CURRENT",
    "CURRENTNESS_UNKNOWN",
}
PROV_RELATIONS = (
    "prov:wasDerivedFrom",
    "prov:wasGeneratedBy",
    "prov:used",
    "prov:wasAssociatedWith",
    "prov:generated",
    "prov:wasRevisionOf",
    "prov:specializationOf",
    "prov:alternateOf",
)


class RealityProjectionError(ValueError):
    """Fail-closed Reality projection input error."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RealityProjectionError(f"{label} must be an object")
    return value


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RealityProjectionError(f"{label} must be a non-empty string")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RealityProjectionError(f"{label} must be a list")
    return value


def _ref_targets(value: Any, label: str) -> list[str]:
    rows = value if isinstance(value, list) else [value]
    result: list[str] = []
    for index, raw in enumerate(rows):
        if isinstance(raw, str) and raw:
            result.append(raw)
            continue
        if isinstance(raw, dict):
            result.append(_nonempty(raw.get("@id"), f"{label}[{index}].@id"))
            continue
        raise RealityProjectionError(f"{label}[{index}] must be an @id reference")
    return result


def compile_prov(document: dict[str, Any], source_ref: str) -> dict[str, Any]:
    """Project explicit PROV nodes/relations while preserving source semantics."""
    source_ref = _nonempty(source_ref, "sourceRef")
    graph = _list(document.get("@graph"), "@graph")
    nodes: list[dict[str, Any]] = []
    seen: set[str] = set()
    raw_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(graph):
        node = _object(raw, f"@graph[{index}]")
        node_id = _nonempty(node.get("@id"), f"@graph[{index}].@id")
        if node_id in seen:
            raise RealityProjectionError(f"duplicate PROV node @id: {node_id}")
        seen.add(node_id)
        raw_by_id[node_id] = node
        raw_type = node.get("@type")
        if isinstance(raw_type, str):
            prov_types = [raw_type]
        elif isinstance(raw_type, list) and all(
            isinstance(item, str) and item for item in raw_type
        ):
            prov_types = sorted(raw_type)
        elif raw_type is None:
            prov_types = []
        else:
            raise RealityProjectionError(f"invalid @type: {node_id}")
        projected = {"id": node_id, "provTypes": prov_types}
        if isinstance(node.get("dct:title"), str):
            projected["title"] = node["dct:title"]
        if isinstance(node.get("dct:identifier"), str):
            projected["identifier"] = node["dct:identifier"]
        nodes.append(projected)

    edges: list[dict[str, Any]] = []
    for source_id in sorted(raw_by_id):
        node = raw_by_id[source_id]
        for relation in PROV_RELATIONS:
            if relation not in node:
                continue
            for target_id in _ref_targets(node[relation], f"{source_id}.{relation}"):
                edges.append(
                    {
                        "source": source_id,
                        "relation": relation,
                        "target": target_id,
                        "targetPresentInDocument": target_id in raw_by_id,
                    }
                )

    result = {
        "schemaVersion": 1,
        "kind": PROV_KIND,
        "truthRole": "thin-projection-of-explicit-w3c-prov-relations",
        "sourceRef": source_ref,
        "sourceDocumentDigest": canonical_digest(document),
        "nodes": sorted(nodes, key=lambda row: row["id"]),
        "edges": sorted(
            edges,
            key=lambda row: (row["source"], row["relation"], row["target"]),
        ),
        "nonClaims": [
            "The projection does not mint a Social Fabric provenance ontology.",
            "An observed sequence or PROV relation is not independently promoted to a causal mechanism claim.",
            "Referenced nodes may be external to this document; absence is preserved rather than rejected as nonexistence.",
            "Natural provenance/evidence owners remain authoritative.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def validate_cut(cut: dict[str, Any]) -> None:
    if cut.get("schemaVersion") != SCHEMA_VERSION or cut.get("kind") != CUT_KIND:
        raise RealityProjectionError("unsupported Reality owner cut kind/schema")
    _nonempty(cut.get("observedAt"), "observedAt")
    _list(cut.get("authorityEntries", []), "authorityEntries")
    _object(cut.get("gatewayCapabilities", {}), "gatewayCapabilities")
    _object(cut.get("hostTasks", {}), "hostTasks")
    _list(cut.get("verificationBindings", []), "verificationBindings")
    _list(cut.get("currentnessFacts", []), "currentnessFacts")
    _list(cut.get("supersessionFacts", []), "supersessionFacts")


def compile_transactive_memory(cut: dict[str, Any]) -> dict[str, Any]:
    """Compile an explicit locator; never infer expertise or semantic ownership."""
    validate_cut(cut)
    entries: list[dict[str, Any]] = []

    for index, raw in enumerate(cut.get("authorityEntries", [])):
        row = _object(raw, f"authorityEntries[{index}]")
        authority_id = _nonempty(row.get("id"), f"authorityEntries[{index}].id")
        issuer = _nonempty(row.get("issuer"), f"authorityEntries[{index}].issuer")
        record_digest = _nonempty(
            row.get("recordDigest"), f"authorityEntries[{index}].recordDigest"
        )
        entries.append(
            {
                "subjectRef": f"authority:{authority_id}",
                "relation": "EXTERNAL_AUTHORITY_ISSUER",
                "principalRef": f"issuer:{issuer}",
                "evidenceRefs": sorted(
                    item
                    for item in [record_digest, row.get("observationDigest")]
                    if isinstance(item, str) and item
                ),
                "locator": {
                    "authorityId": authority_id,
                    "currentnessChecked": row.get("currentnessChecked"),
                },
                "sourceRef": f"authority-index:{authority_id}",
            }
        )

    gateway = cut.get("gatewayCapabilities", {})
    gateway_digest = _nonempty(
        gateway.get("projection_digest"), "gatewayCapabilities.projection_digest"
    )
    for index, raw in enumerate(gateway.get("capabilities", [])):
        row = _object(raw, f"gatewayCapabilities.capabilities[{index}]")
        capability = _nonempty(
            row.get("capability"),
            f"gatewayCapabilities.capabilities[{index}].capability",
        )
        owner_id = _nonempty(
            row.get("owner_id"), f"gatewayCapabilities.capabilities[{index}].owner_id"
        )
        entries.append(
            {
                "subjectRef": f"capability:{capability}",
                "relation": "NATURAL_CAPABILITY_OWNER",
                "principalRef": f"owner:{owner_id}",
                "evidenceRefs": [gateway_digest],
                "locator": {
                    "available": row.get("available"),
                    "configured": row.get("configured"),
                    "truthBoundary": row.get("truth_boundary"),
                },
                "sourceRef": f"gateway-capability:{gateway_digest}#{capability}",
            }
        )

    host = cut.get("hostTasks", {})
    for index, raw in enumerate(host.get("tasks", [])):
        row = _object(raw, f"hostTasks.tasks[{index}]")
        task_id = _nonempty(row.get("task_id"), f"hostTasks.tasks[{index}].task_id")
        checkpoint = _nonempty(
            row.get("checkpoint_digest"), f"hostTasks.tasks[{index}].checkpoint_digest"
        )
        entries.append(
            {
                "subjectRef": task_id,
                "relation": "CONTINUITY_OWNER",
                "principalRef": "owner:host",
                "evidenceRefs": [checkpoint],
                "locator": {
                    "goalRef": row.get("goal_id"),
                    "revision": row.get("revision"),
                    "state": row.get("state"),
                },
                "sourceRef": f"host-task:{task_id}@{row.get('revision')}",
            }
        )

    for index, raw in enumerate(cut.get("verificationBindings", [])):
        row = _object(raw, f"verificationBindings[{index}]")
        evidence_refs = _list(
            row.get("evidenceRefs", []), f"verificationBindings[{index}].evidenceRefs"
        )
        if not all(isinstance(item, str) and item for item in evidence_refs):
            raise RealityProjectionError(
                f"verificationBindings[{index}].evidenceRefs must be non-empty strings"
            )
        entries.append(
            {
                "subjectRef": _nonempty(
                    row.get("subjectRef"), f"verificationBindings[{index}].subjectRef"
                ),
                "relation": "EXPLICIT_VERIFIER",
                "principalRef": _nonempty(
                    row.get("verifierRef"), f"verificationBindings[{index}].verifierRef"
                ),
                "evidenceRefs": sorted(set(evidence_refs)),
                "locator": row.get("locator")
                if isinstance(row.get("locator"), dict)
                else {},
                "sourceRef": _nonempty(
                    row.get("sourceRef"), f"verificationBindings[{index}].sourceRef"
                ),
            }
        )

    unique_keys: set[tuple[str, str, str, str]] = set()
    for row in entries:
        key = (
            row["subjectRef"],
            row["relation"],
            row["principalRef"],
            row["sourceRef"],
        )
        if key in unique_keys:
            raise RealityProjectionError(f"duplicate transactive-memory binding: {key}")
        unique_keys.add(key)

    result = {
        "schemaVersion": 1,
        "kind": MEMORY_KIND,
        "truthRole": "rebuildable-owner-and-evidence-locator",
        "observedAt": cut["observedAt"],
        "sourceCutDigest": canonical_digest(cut),
        "entries": sorted(
            entries,
            key=lambda row: (
                row["subjectRef"],
                row["relation"],
                row["principalRef"],
                row["sourceRef"],
            ),
        ),
        "nonClaims": [
            "The projection does not infer expertise, knowledge, trustworthiness, assignment, or task priority.",
            "External issuer, capability owner, continuity owner, and verifier are distinct relations.",
            "Host Task state is continuity state, not proof that work is active or domain-complete.",
            "A locator is navigation evidence, not EffectAuthority.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def _freshness_standing(rows: list[dict[str, Any]]) -> str:
    current = {
        row["versionRef"] for row in rows if row["standing"] == "CURRENT_DECLARED"
    }
    if len(current) > 1:
        return "CONFLICTED_CURRENT_DECLARATIONS"
    if len(current) == 1:
        return "CURRENT_DECLARED"
    if any(row["standing"] == "HISTORICAL_NOT_CURRENT" for row in rows):
        return "HISTORICAL_NOT_CURRENT"
    if any(row["standing"] == "POINT_IN_TIME_OBSERVED" for row in rows):
        return "POINT_IN_TIME_OBSERVED"
    return "CURRENTNESS_UNKNOWN"


def compile_freshness(cut: dict[str, Any]) -> dict[str, Any]:
    """Preserve currentness per natural owner; no global recency synthesis."""
    validate_cut(cut)
    facts: list[dict[str, Any]] = []

    for index, raw in enumerate(cut.get("currentnessFacts", [])):
        row = _object(raw, f"currentnessFacts[{index}]")
        standing = _nonempty(row.get("standing"), f"currentnessFacts[{index}].standing")
        if standing not in OWNER_STANDINGS:
            raise RealityProjectionError(
                f"unsupported currentness standing: {standing}"
            )
        version_ref = row.get("versionRef")
        if standing in {"CURRENT_DECLARED", "HISTORICAL_NOT_CURRENT"}:
            version_ref = _nonempty(
                version_ref, f"currentnessFacts[{index}].versionRef"
            )
        elif version_ref is not None and not isinstance(version_ref, str):
            raise RealityProjectionError(
                f"currentnessFacts[{index}].versionRef must be string or null"
            )
        facts.append(
            {
                "subjectRef": _nonempty(
                    row.get("subjectRef"), f"currentnessFacts[{index}].subjectRef"
                ),
                "owner": _nonempty(
                    row.get("owner"), f"currentnessFacts[{index}].owner"
                ),
                "standing": standing,
                "versionRef": version_ref,
                "sourceRef": _nonempty(
                    row.get("sourceRef"), f"currentnessFacts[{index}].sourceRef"
                ),
            }
        )

    # Authority Catalog observations are explicitly point-in-time checks, never
    # silently upgraded to durable CURRENT_DECLARED semantics.
    for index, raw in enumerate(cut.get("authorityEntries", [])):
        row = _object(raw, f"authorityEntries[{index}]")
        authority_id = _nonempty(row.get("id"), f"authorityEntries[{index}].id")
        if row.get("currentnessChecked") is None:
            continue
        facts.append(
            {
                "subjectRef": f"authority:{authority_id}",
                "owner": "authority-catalog",
                "standing": "POINT_IN_TIME_OBSERVED",
                "versionRef": row.get("versionLabel"),
                "sourceRef": f"authority-index:{authority_id}#{row.get('observationDigest')}",
            }
        )

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in facts:
        grouped[(row["subjectRef"], row["owner"])].append(row)

    owner_views: list[dict[str, Any]] = []
    for (subject_ref, owner), rows in sorted(grouped.items()):
        current_refs = sorted(
            {row["versionRef"] for row in rows if row["standing"] == "CURRENT_DECLARED"}
        )
        historical_refs = sorted(
            {
                row["versionRef"]
                for row in rows
                if row["standing"] == "HISTORICAL_NOT_CURRENT"
            }
        )
        owner_views.append(
            {
                "subjectRef": subject_ref,
                "owner": owner,
                "standing": _freshness_standing(rows),
                "currentVersionRefs": current_refs,
                "historicalVersionRefs": historical_refs,
                "pointInTimeObservationCount": sum(
                    row["standing"] == "POINT_IN_TIME_OBSERVED" for row in rows
                ),
                "unknownObservationCount": sum(
                    row["standing"] == "CURRENTNESS_UNKNOWN" for row in rows
                ),
                "sourceRefs": sorted({row["sourceRef"] for row in rows}),
            }
        )

    supersession: list[dict[str, Any]] = []
    for index, raw in enumerate(cut.get("supersessionFacts", [])):
        row = _object(raw, f"supersessionFacts[{index}]")
        supersession.append(
            {
                "subjectRef": _nonempty(
                    row.get("subjectRef"), f"supersessionFacts[{index}].subjectRef"
                ),
                "owner": _nonempty(
                    row.get("owner"), f"supersessionFacts[{index}].owner"
                ),
                "relation": _nonempty(
                    row.get("relation"), f"supersessionFacts[{index}].relation"
                ),
                "olderRef": _nonempty(
                    row.get("olderRef"), f"supersessionFacts[{index}].olderRef"
                ),
                "newerRef": _nonempty(
                    row.get("newerRef"), f"supersessionFacts[{index}].newerRef"
                ),
                "sourceRef": _nonempty(
                    row.get("sourceRef"), f"supersessionFacts[{index}].sourceRef"
                ),
            }
        )

    result = {
        "schemaVersion": 1,
        "kind": FRESHNESS_KIND,
        "truthRole": "owner-scoped-currentness-and-explicit-supersession-projection",
        "observedAt": cut["observedAt"],
        "sourceCutDigest": canonical_digest(cut),
        "ownerViews": owner_views,
        "supersession": sorted(
            supersession,
            key=lambda row: (
                row["subjectRef"],
                row["owner"],
                row["olderRef"],
                row["newerRef"],
            ),
        ),
        "nonClaims": [
            "Git tip recency does not mint semantic currentness.",
            "Host Task state does not mint activity/currentness or domain completion.",
            "Point-in-time observation is not durable freshness.",
            "Supersession is projected only when an owner-native source states it explicitly; no transitive semantic replacement is inferred.",
            "Different owners retain separate currentness views; this projection does not elect a global winner.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RealityProjectionError(f"{path}: root must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    prov = sub.add_parser("prov")
    prov.add_argument("--document", type=Path, required=True)
    prov.add_argument("--source-ref")

    memory = sub.add_parser("memory")
    memory.add_argument("--cut", type=Path, required=True)

    freshness = sub.add_parser("freshness")
    freshness.add_argument("--cut", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "prov":
            result = compile_prov(
                _load(args.document),
                args.source_ref or f"file:{args.document.as_posix()}",
            )
        elif args.command == "memory":
            result = compile_transactive_memory(_load(args.cut))
        else:
            result = compile_freshness(_load(args.cut))
    except (OSError, json.JSONDecodeError, RealityProjectionError) as exc:
        raise SystemExit(f"social fabric Reality R2 failed: {exc}") from exc
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
