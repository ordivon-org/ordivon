"""Pure declared Owner LEGO graph contract; no source or installed authority."""
from __future__ import annotations

import re
from graphlib import CycleError, TopologicalSorter
from typing import Any


class ArchitectureDocsError(ValueError):
    pass

LEGO_RELATION_KINDS = frozenset({
    "ADAPTATION",
    "AUTHORITY",
    "COMPATIBILITY",
    "COMPOSITION",
    "CONTROL",
    "DATA",
    "DELETION",
    "DEPENDENCY",
    "EFFECT",
    "EVIDENCE",
    "FALSIFICATION",
    "IDENTITY",
    "OBSERVATION",
    "POLICY",
    "REALIZATION",
    "SPECIALIZATION",
    "STATE",
    "STORAGE",
    "TRANSACTION",
    "VERIFICATION",
})

def _validated_owner_lego_edges(
    edges: Any, vertices: set[str],
) -> list[tuple[str, str, str]]:
    """One total typed relation check; scheduling semantics remain separate."""
    if not isinstance(edges, list):
        raise ArchitectureDocsError("owner LEGO edges must be a list")
    observed: set[tuple[str, str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise ArchitectureDocsError("LEGO edge must be an object")
        kind = edge.get("type")
        if not isinstance(kind, str) or not kind.strip() or kind != kind.strip():
            raise ArchitectureDocsError("LEGO edge requires a type")
        if kind not in LEGO_RELATION_KINDS:
            raise ArchitectureDocsError("unknown LEGO edge type")
        source, target = edge.get("from"), edge.get("to")
        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or source not in vertices
            or target not in vertices
        ):
            raise ArchitectureDocsError("unknown LEGO edge endpoint")
        triple = (source, kind, target)
        if triple in observed:
            raise ArchitectureDocsError(f"duplicate LEGO edge: {triple}")
        observed.add(triple)
    return sorted(observed)

def _canonical_owner_lego_id(identity: str) -> bool:
    """One unambiguous machine key, distinct from localized LEGO labels."""
    return re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]*", identity) is not None

def _require_exact_schema_one(value: dict[str, Any], label: str) -> None:
    """Schema version is an exact integer, not a Python numeric equality.

    `True == 1` and `1.0 == 1` must not grant admission to old R1
    contracts or historical issue evidence.
    """
    observed = value.get("schemaVersion")
    if type(observed) is not int or observed != 1:
        raise ArchitectureDocsError(f"{label} schemaVersion must be exact integer 1")

_SOURCE_ONLY_AUTHORITY_CLAIMS = frozenset({
    "deletionAuthorized",
    "effectAuthorized",
    "promotionAuthorized",
    "deploymentAuthorized",
    "domainAccepted",
    "proofReuseAdmissible",
})

def _reject_source_only_authority_claim(row: dict[str, Any], identity: str) -> None:
    for claim in _SOURCE_ONLY_AUTHORITY_CLAIMS:
        if claim in row and row[claim] is not False:
            raise ArchitectureDocsError(
                f"source-only LEGO {identity} cannot establish {claim} authority"
            )


def validate_owner_lego_graph(plan: dict[str, Any]) -> None:
    """Check all Owner slices reference typed vertices, including unregistered ones.

    Registered dependency DAGs and typed edges have separate existing laws.
    This does not assert behavioral currentness or execution authority.
    """
    _require_exact_schema_one(plan, "owner LEGO graph")
    if plan.get("kind") != "ordivon.project-lego-plan":
        raise ArchitectureDocsError("owner LEGO graph has unexpected kind")
    if plan.get("truthRole") != "planning-projection-not-project-truth":
        raise ArchitectureDocsError("owner LEGO graph must remain non-authoritative")

    nodes = plan.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ArchitectureDocsError("owner LEGO graph needs nodes")
    identities: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise ArchitectureDocsError("LEGO node must be an object")
        identity = node.get("id")
        if not isinstance(identity, str) or not identity.strip():
            raise ArchitectureDocsError("LEGO node requires non-empty identity")
        if not _canonical_owner_lego_id(identity):
            raise ArchitectureDocsError("non-canonical LEGO node identity")
        if identity in identities:
            raise ArchitectureDocsError(f"duplicate LEGO node: {identity}")
        _reject_source_only_authority_claim(node, identity)
        if not isinstance(node.get("kind"), str) or not node["kind"].strip():
            raise ArchitectureDocsError(f"LEGO node {identity} requires a type")
        identities.add(identity)

    slices = plan.get("slices", [])
    if not isinstance(slices, list):
        raise ArchitectureDocsError("LEGO slices must be a list")
    slice_ids: set[str] = set()
    for slice_ in slices:
        if not isinstance(slice_, dict):
            raise ArchitectureDocsError("LEGO slice must be an object")
        identity = slice_.get("id")
        if not isinstance(identity, str) or not identity.strip():
            raise ArchitectureDocsError("LEGO slice needs non-empty identity")
        if not _canonical_owner_lego_id(identity):
            raise ArchitectureDocsError("non-canonical LEGO slice identity")
        if identity in slice_ids:
            raise ArchitectureDocsError(f"duplicate LEGO slice: {identity}")
        _reject_source_only_authority_claim(slice_, identity)
        slice_ids.add(identity)
        refs = slice_.get("nodeIds")
        if not isinstance(refs, list) or not refs:
            raise ArchitectureDocsError(f"LEGO slice {identity} needs node references")
        if any(not isinstance(ref, str) or ref not in identities for ref in refs):
            raise ArchitectureDocsError(f"unknown LEGO slice node in {identity}")
        if len(refs) != len(set(refs)):
            raise ArchitectureDocsError(f"duplicate LEGO slice node in {identity}")

    # A blocked slice is a derived claim over the *current* declared
    # prerequisite graph, not a historical reason to keep work blocked.
    # Do not infer completion from released blockers; the slice stays
    # PROPOSED until its own acceptance evidence exists.
    slice_states = {row["id"]: row.get("status") for row in slices}
    # Reuse the stdlib DAG checker; these are planning prerequisites, not
    # executable workflows, and no new scheduler or registry is admitted.
    slice_prerequisites: dict[str, set[str]] = {name: set() for name in slice_states}
    # Finite planning states are types, not descriptive free text. Unknown
    # states must not silently bypass blocker/progress admission.
    lifecycle_states = {
        "PROPOSED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED",
        "COMPLETE", "RETIRED",
    }
    for row in slices:
        state = row.get("status")
        if (
            not isinstance(state, str)
            or (state not in lifecycle_states and not state.startswith("BLOCKED_ON_"))
        ):
            raise ArchitectureDocsError(f"invalid LEGO slice status: {row['id']}")
        if not state.startswith("BLOCKED_ON_"):
            continue
        blockers = row.get("blockers")
        if (
            not isinstance(blockers, list)
            or not blockers
            or any(not isinstance(ref, str) or ref not in slice_states for ref in blockers)
            or len(blockers) != len(set(blockers))
            or state != "BLOCKED_ON_" + "_".join(blockers)
            or any(slice_states[ref] in {"COMPLETE", "RETIRED"} for ref in blockers)
        ):
            raise ArchitectureDocsError(
                f"invalid LEGO blocking prerequisites: {row['id']}"
            )
        slice_prerequisites[row["id"]].update(blockers)
    try:
        TopologicalSorter(slice_prerequisites).prepare()
    except CycleError as error:
        raise ArchitectureDocsError("cyclic LEGO slice blockers") from error

    # Typed relations are structural; OBSERVATION/STATE cycles are allowed.
    _validated_owner_lego_edges(plan.get("edges", []), identities)

def validate_owner_lego_dependencies(
    plan: dict[str, Any], owner: str,
) -> tuple[set[str], tuple[tuple[str, ...], ...]]:
    """Well-founded *declared prerequisites*, not a workflow/execution graph.

    Node.dependencies and typed DEPENDENCY edges are equivalent prerequisite
    syntax in different existing natural-Owner LEGO plans.  DATA, CONTROL,
    EFFECT and OBSERVATION edges are not prerequisite claims.
    """
    _require_exact_schema_one(plan, "owner LEGO prerequisites")
    nodes = plan.get("nodes")
    if not isinstance(nodes, list):
        raise ArchitectureDocsError("owner-local LEGO nodes missing")
    if not nodes:
        raise ArchitectureDocsError(f"{owner}: empty LEGO owner graph")
    graph: dict[str, set[str]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"]:
            raise ArchitectureDocsError("untyped LEGO node identity")
        identity = node["id"]
        if not _canonical_owner_lego_id(identity):
            raise ArchitectureDocsError("non-canonical LEGO node identity")
        if identity in graph:
            raise ArchitectureDocsError("duplicate LEGO node identity")
        depends = node.get("dependencies")
        if not isinstance(depends, list) or any(
            not isinstance(value, str) or not value for value in depends
        ):
            raise ArchitectureDocsError("untyped LEGO dependencies")
        if len(depends) != len(set(depends)):
            raise ArchitectureDocsError("duplicate LEGO dependency")
        graph[identity] = set(depends)
    node_ids = set(graph)
    if any(d not in node_ids for deps in graph.values() for d in deps):
        raise ArchitectureDocsError("unknown LEGO dependency")
    # Reuse the same total typed relation check without altering the
    # existing node/dependency/slice error precedence.
    for source, kind, target in _validated_owner_lego_edges(
        plan.get("edges", []), node_ids,
    ):
        if kind == "DEPENDENCY":
            graph[target].add(source)
    sorter = TopologicalSorter(graph)
    try:
        sorter.prepare()
    except CycleError as error:
        raise ArchitectureDocsError("cyclic LEGO dependencies") from error
    frontiers: list[tuple[str, ...]] = []
    while sorter.is_active():
        ready = tuple(sorted(sorter.get_ready()))
        frontiers.append(ready)
        sorter.done(*ready)
    return node_ids, tuple(frontiers)
