"""Exact-Git Problem LEGO *candidates*, projected from the canonical Phase 1 census.

A source cell or plan node is NEVER asserted to be a behavioral LEGO.
This is a read-only, rebuildable representation for later joint consumer/call
semantic analysis, not a second classifier, plan, registry or permission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from exhaustive_coverage import active_source_cells, classification


CELL_QUESTIONS = {
    "UNCLASSIFIED_SOURCE_REGION": "Which observed source responsibility and navigation area, if any, matches this exact path set?",
    "DENSE_CELL_REQUIRES_SUBCLASSIFICATION_REVIEW": "What smaller observable source responsibilities, if any, justify separating this physical cell?",
    "PLAN_DECLARATION_GAPS_REQUIRE_SEMANTIC_MAPPING": "Which plan declarations have actual source, consumer, contract, or implementation witnesses?",
}


def _ref(kind: str, values: Any) -> str:
    raw = json.dumps(values, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return "problem-lego-candidate:" + kind + ":sha256:" + hashlib.sha256(raw.encode()).hexdigest()


def project_problem_legos(
    inventory: dict, *, repo: Path, max_files: int = 24, max_depth: int = 6,
) -> dict:
    """Project ALL physical cells + ALL declared plan nodes without call semantics.

    A separate problem candidate is emitted for each problematic physical cell
    and each plan-node qualification gap. Multiple labels on one physical cell
    do not create duplicate problems or imply multiple semantic responsibilities.
    """
    frontier = active_source_cells(
        inventory, repo=repo, max_files=max_files, max_depth=max_depth,
        include_member_index=True,
    )
    source_cut = inventory["sourceCut"]
    index = frontier["memberCellDigests"]
    by_members: dict[str, list[str]] = defaultdict(list)
    for path, digest in index.items():
        by_members[digest].append(path)
    for group in by_members.values():
        group.sort()

    cell_rows = []
    physical_problems = []
    cell_refs = {}
    for cell in frontier["cells"]:
        digest = cell["memberGitObjectDigest"]
        if digest in cell_refs:
            raise ValueError("source cells must have distinct exact-Git member identities")
        cell_ref = "source-cell:" + digest
        cell_refs[digest] = cell_ref
        members = by_members[digest]
        if len(members) != cell["pathCount"]:
            raise ValueError("source cell membership is not complete")
        problems = list(cell["problems"])
        problem_ref = (
            _ref("source-cell", [source_cut, cell["sourceZone"], digest, problems])
            if problems else None
        )
        cell_rows.append({
            "sourceUnitRef": cell_ref,
            "agentLocator": cell["sourceZone"] + " :: " + cell["physicalPrefix"],
            "sourceZone": cell["sourceZone"],
            "physicalPrefix": cell["physicalPrefix"],
            "memberGitObjectDigest": digest,
            "memberPaths": members,
            "pathCount": len(members),
            "sourceCarriers": cell["sourceCarriers"],
            "extensionKinds": cell["extensionKinds"],
            "sourceProblemCounts": cell["sourceProblemCounts"],
            "planDeclarationProblemCounts": cell["planDeclarationProblemCounts"],
            "problemCodes": problems,
            "problemLegoCandidateRef": problem_ref,
            "sourceStanding": "EXACT_GIT_PHYSICAL_CELL",
            "semanticLegoStanding": "NOT_ESTABLISHED",
            "consumerStanding": "UNKNOWN",
            "callSemanticsStanding": "NOT_ASSESSED",
            "installedStanding": "UNKNOWN",
            "formalStanding": "UNKNOWN",
        })
        if problems:
            if not set(problems) <= set(CELL_QUESTIONS):
                raise ValueError("unmodeled physical cell issue code")
            physical_problems.append({
                "problemLegoCandidateRef": problem_ref,
                "representation": "PHYSICAL_SOURCE_CELL_PROBLEM_HYPOTHESIS",
                "sourceUnitRef": cell_ref,
                "agentLocator": cell_rows[-1]["agentLocator"],
                "problemCodes": problems,
                "unresolvedQuestions": [CELL_QUESTIONS[p] for p in problems],
                "memberCount": len(members),
                "consumerStanding": "UNKNOWN",
                "callSemanticsStanding": "NOT_ASSESSED",
                "decision": "HOLD_FOR_JOINT_SEMANTIC_CONSUMER_REVIEW",
            })

    # Retain every native file-level structural flag and exact Git mode/blob
    # identity. These flags are *not* 4,000+ additional semantic Problem LEGO:
    # a proposed physical move is NOT evidence that a consumer is broken.
    file_facts = []
    file_problem_counts: Counter[str] = Counter()
    file_problem_paths = 0
    for item in sorted(inventory["sourcePaths"], key=lambda r: r["path"]):
        file_path = item["path"]
        digest = index.get(file_path)
        if digest is None:
            raise ValueError("Git source path lost its physical cell assignment")
        flags = list(item["problems"])
        file_problem_counts.update(flags)
        file_problem_paths += bool(flags)
        file_facts.append({
            "sourcePath": file_path,
            "sourceIdentity": item["sourceIdentity"],
            "sourceUnitRef": cell_refs[digest],
            "currentSource": item["currentSource"],
            "sourceProblemCodes": flags,
            "carrierType": item["carrierType"],
            "consumerStanding": "UNKNOWN",
            "callSemanticsStanding": "NOT_ASSESSED",
        })

    if len(cell_rows) != frontier["summary"]["cells"] or (
        sum(row["pathCount"] for row in cell_rows)
        != inventory["summary"]["trackedPaths"]
        != len(index)
    ):
        raise ValueError("canonical physical source partition does not close")
    if len({path for row in cell_rows for path in row["memberPaths"]}) != len(index):
        raise ValueError("one source path was counted more than once")

    scoped_nodes = {n["nodeRef"]: n for n in inventory["semanticPlans"]["nodes"]}
    if len(scoped_nodes) != len(inventory["semanticPlans"]["nodes"]):
        raise ValueError("plan node references must be scoped to exact plan path")
    plan_nodes = []
    for node in sorted(scoped_nodes.values(), key=lambda n: n["nodeRef"]):
        plan_path = node["plan"]
        digest = index.get(plan_path)
        if digest is None:
            raise ValueError("plan node has no exact Git source-cell carrier")
        declared = node["declarations"]
        issues = list(node["problems"])
        if not all(node[k] == "UNKNOWN" for k in (
            "consumerQualification", "formalQualification", "implementationRefinement"
        )):
            raise ValueError("unexpected qualification promotion by source-only plan")
        plan_nodes.append({
            "problemLegoCandidateRef": _ref("plan-node", [source_cut, node["nodeRef"]]),
            "representation": "PLAN_NODE_UNQUALIFIED_SEMANTIC_CANDIDATE",
            "nodeRef": node["nodeRef"],
            "planSourcePath": plan_path,
            "sourceUnitRef": cell_refs[digest],
            "localId": node["localId"],
            "nodeShape": node["shape"],
            "declaredFieldAliases": declared,
            "declarationProblemCodes": issues,
            "declarationStanding": "GAPS_PRESENT" if issues else "FOUR_ROLES_DECLARED_NOT_VERIFIED",
            "consumerStanding": node["consumerQualification"],
            "formalStanding": node["formalQualification"],
            "implementationStanding": node["implementationRefinement"],
            "callSemanticsStanding": "NOT_ASSESSED",
            "decision": "HOLD_FOR_JOINT_SEMANTIC_CONSUMER_REVIEW",
        })

    # Retain every literal plan edge as a *declaration*; do not infer function
    # calls, operational ownership, execution order or semantic transitivity.
    relation_rows = []
    for edge in sorted(inventory["semanticPlans"]["edges"],
                       key=lambda e: (e["plan"], e["edgeIndex"])):
        def target(name: Any) -> str | None:
            ref = edge["plan"] + "#" + name if isinstance(name, str) else None
            return ref if ref in scoped_nodes else None

        relation_rows.append({
            "planSourcePath": edge["plan"],
            "edgeIndex": edge["edgeIndex"],
            "declaredType": edge["edgeType"],
            "fromRaw": edge["from"],
            "toRaw": edge["to"],
            "fromScopedNodeRef": target(edge["from"]),
            "toScopedNodeRef": target(edge["to"]),
            "endpointStanding": edge["standing"],
            "callSemanticsStanding": "NOT_ASSESSED",
            "executableDependencyProof": False,
        })

    label_counts = Counter(p for x in physical_problems for p in x["problemCodes"])
    node_gap_counts = Counter(p for x in plan_nodes for p in x["declarationProblemCodes"])
    overlapping = sum(len(x["problemCodes"]) > 1 for x in physical_problems)
    if (len(physical_problems) != frontier["summary"]["problemCells"]
            or dict(sorted(label_counts.items())) != frontier["summary"]["problemCounts"]):
        raise ValueError("physical issue union/count mismatch")
    if dict(sorted(node_gap_counts.items())) != inventory["summary"]["nodeProblems"]:
        raise ValueError("plan declaration gap count mismatch")
    summary = {
        "trackedPaths": len(index),
        "sourceUnits": len(cell_rows),
        "sourcePathsWithStructuralFlags": file_problem_paths,
        "sourcePathStructuralFlagCounts": dict(sorted(file_problem_counts.items())),
        "structuralFlagsAreVerifiedRuntimeFailures": False,
        "sourceProblemCandidates": len(physical_problems),
        "sourceProblemLabelOccurrences": sum(label_counts.values()),
        "multiLabelSourceProblemCandidates": overlapping,
        "sourceProblemCodeCounts": dict(sorted(label_counts.items())),
        "unqualifiedPlanNodeCandidates": len(plan_nodes),
        "planNodesWithDeclarationGaps": sum(bool(x["declarationProblemCodes"]) for x in plan_nodes),
        "planNodesWithFourRolesDeclaredButStillUnverified": sum(
            not x["declarationProblemCodes"] for x in plan_nodes),
        "planDeclarationGapCounts": dict(sorted(node_gap_counts.items())),
        "planDeclarationRelationsUnverified": len(relation_rows),
        "totalProblemLegoCandidates": len(physical_problems) + len(plan_nodes),
        "consumerSemanticsResolved": 0,
        "installedEquivalenceProven": 0,
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.phase1.problem-lego-candidates",
        "sourceCut": source_cut,
        "sourceTree": inventory["sourceTree"],
        "sourcePathDigest": inventory["sourcePathDigest"],
        "projection": "REBUILDABLE_SOURCE_AND_PLAN_PROBLEM_REPRESENTATION_ONLY",
        "truthBoundary": (
            "Physical Git cells, syntactic plan declarations and candidate problems only; "
            "a Problem LEGO candidate is not a semantic LEGO, call graph, actual "
            "consumer, installed proof, deletion permission or verification authority"
        ),
        "proofReuseAdmissible": False,
        "callerOrRuntimeAuthorityInferred": False,
        "defaultRemediation": "DEFER_UNTIL_CONSUMER_AND_CALL_SEMANTICS_QUALIFIED",
        "summary": summary,
        "sourceUnits": cell_rows,
        "sourcePathFacts": file_facts,
        "sourceProblemCandidates": physical_problems,
        "planNodeProblemCandidates": plan_nodes,
        "deferredPlanRelationDeclarations": relation_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cut", required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--summary", action="store_true",
                        help="show exact census and issue overlap, omit expanded candidates")
    parser.add_argument("--cell-max-files", type=int, default=24)
    parser.add_argument("--cell-max-depth", type=int, default=6)
    args = parser.parse_args()
    source = classification(args.repo, args.source_cut)
    result = project_problem_legos(
        source, repo=args.repo, max_files=args.cell_max_files,
        max_depth=args.cell_max_depth)
    if args.summary:
        for key in ("sourceUnits", "sourcePathFacts", "sourceProblemCandidates",
                    "planNodeProblemCandidates", "deferredPlanRelationDeclarations"):
            result.pop(key)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
