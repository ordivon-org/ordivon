#!/usr/bin/env python3
"""Exact-Git, exhaustive Ordivon source/semantic declaration inventory.

Read-only derived projection. Does not add owners, authorize actions, certify
consumers, qualify installed state, or prove any concrete implementation.
A peer's proposed source-regions are compared as an explicit independent
proposal SourceCut, never silently installed into the subject SourceCut.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import os
import re
import stat
import subprocess
import tomllib
from pathlib import Path


def git(repo: Path, *args: str) -> bytes:
    p = subprocess.run(["git", "--no-replace-objects", "-C", str(repo), *args],
                       capture_output=True)
    if p.returncode:
        raise ValueError(f"git {args[0]} failed: {p.stderr[:400]!r}")
    return p.stdout


def exact_commit(repo: Path, oid: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", oid):
        raise ValueError("source cut must be an exact 40-hex commit")
    got = git(repo, "rev-parse", "--verify", f"{oid}^{{commit}}").decode().strip()
    if got != oid:
        raise ValueError("source cut does not refer to requested commit")
    return oid


def tree(repo: Path, commit: str) -> list[dict]:
    raw = git(repo, "ls-tree", "-r", "-z", commit)
    entries = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        header, name = item.split(b"\t", 1)
        mode, kind, sha = header.decode("ascii").split(" ")
        path = name.decode("utf-8", "surrogateescape")
        entries.append({"path": path, "sourceIdentity": f"{mode}:{kind}:{sha}"})
    paths = [x["path"] for x in entries]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate Git path")
    return sorted(entries, key=lambda x: x["path"])


def read_json(repo: Path, commit: str, path: str) -> dict:
    return json.loads(git(repo, "show", f"{commit}:{path}"))


def read_policy(repo: Path, commit: str) -> dict:
    data = tomllib.loads(git(repo, "show", f"{commit}:tools/repo/owners.toml").decode())
    if data.get("truth_role") != "repository-mechanics-only-not-domain-authority":
        raise ValueError("incorrect repository source-only role")
    return data


def is_match(path: str, rule: str) -> bool:
    return path.startswith(rule) if rule.endswith("/") else path == rule


def source_matches(path: str, policy: dict) -> list[tuple[str, str]]:
    hit = [("ROOT", o["name"]) for o in policy.get("owners", [])
           if path.startswith(o["root"])]
    # Owner roots are strictly unique physical partitions. A source region
    # may overlap an owner rule, but never grants additional verification rights.
    if len(hit) > 1:
        raise ValueError(f"overlapping registered owner roots for {path}")
    if hit:
        return hit
    return [("REGION", region["name"])
            for region in policy.get("source_regions", [])
            if any(is_match(path, rule) for rule in region["paths"])
            and not any(is_match(path, rule) for rule in region.get("exclude", []))]


def source_partition(path: str, policy: dict) -> dict:
    found = source_matches(path, policy)
    return {"standing": "CLASSIFIED" if len(found) == 1 else
            "UNASSIGNED" if not found else "AMBIGUOUS",
            "classification": f"{found[0][0]}:{found[0][1]}" if len(found) == 1 else None,
            "matches": [f"{kind}:{name}" for kind, name in found]}


def entrypoint_kind(path: str) -> str | None:
    name = path.rsplit("/", 1)[-1]
    if name in {"Cargo.toml", "pyproject.toml", "package.json", "Dockerfile",
                "SKILL.md", "plugin.json", "mise.toml"}:
        return name
    if name.endswith((".service", ".timer", ".target")):
        return "systemd-unit"
    if path.startswith(".github/workflows/") and name.endswith((".yml", ".yaml")):
        return "ci-workflow"
    return None


def declared_values(node: dict, aliases: tuple[str, ...]) -> list[str]:
    return [k for k in aliases if k in node and node[k] not in (None, "", [], {})]


FIELDS = {
    "CONTRACT": ("behavioralContract", "contract", "contracts", "replacementContract"),
    "CONSUMER": ("consumerEvidence", "consumerBindings", "actualConsumers", "consumers", "consumerRefs"),
    "FORMAL": ("formalObligations", "proofObligations", "formalEvidence", "formalQualification"),
    "EVIDENCE": ("evidence", "currentEvidence", "implementationEvidence", "verificationEvidence"),
}


def plans(repo: Path, source: str, source_paths: set[str]) -> dict:
    selected = sorted(p for p in source_paths if p.endswith(".json")
                      and "lego-plan" in p.rsplit("/", 1)[-1].lower())
    rows = []
    edge_rows = []
    opaque = []
    for path in selected:
        obj = read_json(repo, source, path)
        nodes = obj.get("nodes")
        if not isinstance(nodes, list):
            opaque.append({"plan": path, "standing": "NON_NODE_PLAN_SHAPE", "kind": obj.get("kind")})
            continue
        local_ids = set()
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError(f"{path}: a node is not a JSON object")
            local = node.get("id")
            if not isinstance(local, str) or not local:
                raise ValueError(f"{path}: node ID is missing or empty")
            if local in local_ids:
                raise ValueError(f"{path}: duplicate local node ID {local}")
            local_ids.add(local)
            shape = ("RESPONSIBILITY_NODE" if all(k in node for k in ("kind", "responsibility"))
                     else "OTHER_NODE_SHAPE")
            present = {k: declared_values(node, v) for k, v in FIELDS.items()}
            gaps = (["SCHEMA_MAPPING_NEEDED"] if shape == "OTHER_NODE_SHAPE" else
                    [f"{k}_DECLARATION_NOT_FOUND" for k, v in present.items() if not v])
            rows.append({"nodeRef": path + "#" + local, "localId": local,
                         "plan": path, "shape": shape, "declarations": present,
                         "problems": gaps, "formalQualification": "UNKNOWN",
                         "consumerQualification": "UNKNOWN",
                         "implementationRefinement": "UNKNOWN"})
        edges = obj.get("edges")
        if isinstance(edges, list):
            for i, edge in enumerate(edges):
                if not isinstance(edge, dict):
                    raise ValueError(f"{path}: malformed edge {i}")
                u, v = edge.get("from"), edge.get("to")
                edge_rows.append({
                    "plan": path, "edgeIndex": i, "from": u, "to": v,
                    "standing": "LOCAL_ENDPOINTS_IDENTIFIED" if u in local_ids and v in local_ids
                    else "EXTERNAL_OR_UNRESOLVED_ENDPOINT",
                    "edgeType": edge.get("type"),
                })
    seen = collections.defaultdict(list)
    for node in rows:
        seen[node["localId"]].append(node["nodeRef"])
    collisions = {k: sorted(v) for k, v in sorted(seen.items()) if len(v) > 1}
    return {"files": selected, "nodes": rows, "edges": edge_rows,
            "opaquePlans": opaque, "sameLocalIdAcrossPlans": collisions}


def classification(repo: Path, source: str, proposed: str | None = None) -> dict:
    exact_commit(repo, source)
    if proposed is not None:
        exact_commit(repo, proposed)
    actual = read_policy(repo, source)
    alternative = read_policy(repo, proposed) if proposed else None
    entries = tree(repo, source)
    pathset = {r["path"] for r in entries}
    placement = read_json(repo, source, "docs/architecture/structure-r2-transition-r1.json")
    paths_out = []
    problem_counts = collections.Counter()
    zones = collections.Counter()
    proposed_zones = collections.Counter()
    for item in entries:
        path = item["path"]
        now = source_partition(path, actual)
        then = source_partition(path, alternative) if alternative else None
        possible = [
            (len(rule), x, rule)
            for x in placement.get("mappings", [])
            for rule in x.get("sourcePaths", [])
            if is_match(path, rule)
        ]
        # Structure R2 deliberately has broad and narrow nested source rules.
        # Longest-prefix precedence is a projection policy, not evidence that
        # a physical move or consumer cutover has occurred.
        best = max((width for width, _, _ in possible), default=0)
        selected = [(x, prefix) for width, x, prefix in possible if width == best]
        targets = []
        for x, source_prefix in selected:
            dests = x.get("targetPaths", [])
            if len(dests) == 1:
                dest = dests[0] + path[len(source_prefix):] if source_prefix.endswith("/") else dests[0]
                targets.append({"map": x.get("id"), "mode": x.get("mode"), "targetPath": dest})
        problems = []
        if now["standing"] != "CLASSIFIED":
            problems.append("CURRENT_SOURCE_UNASSIGNED_OR_AMBIGUOUS")
        if then is not None and then["standing"] != "CLASSIFIED":
            problems.append("PROPOSED_SOURCE_UNASSIGNED_OR_AMBIGUOUS")
        if len({(x.get("id"), prefix) for x, prefix in selected}) > 1:
            problems.append("EQUALLY_SPECIFIC_STRUCTURE_MAPPINGS")
        if len(selected) == 1 and len(selected[0][0].get("targetPaths", [])) != 1:
            problems.append("STRUCTURE_SPLIT_REQUIRES_CONSUMER_WITNESS")
        if any(x["mode"] == "move" and x["targetPath"] != path for x in targets):
            problems.append("PHYSICAL_MOVE_NOT_REALIZED_OR_CONSUMER_NOT_CUT_OVER")
        carrier = entrypoint_kind(path)
        if carrier is not None:
            problems.append("SOURCE_CARRIER_NOT_SEMANTIC_LEGO_PROOF")
        for problem in problems:
            problem_counts[problem] += 1
        zones[now["classification"] or now["standing"]] += 1
        if then is not None:
            proposed_zones[then["classification"] or then["standing"]] += 1
        paths_out.append({**item, "currentSource": now,
                          "proposedSource": then, "targetCandidates": targets,
                          "carrierType": carrier, "problems": problems,
                          "semanticCompleteness": "UNKNOWN"})
    if len(paths_out) != len(pathset):
        raise AssertionError("source inventory must cover exact tracked tree")
    graph = plans(repo, source, pathset)
    node_issue_count = collections.Counter(p for node in graph["nodes"] for p in node["problems"])
    edges = collections.Counter(e["standing"] for e in graph["edges"])
    carriers = collections.Counter(row["carrierType"] for row in paths_out if row["carrierType"])
    roots_without_plan = sorted(
        o["name"] for o in actual.get("owners", [])
        if not any(plan.startswith(o["root"]) for plan in graph["files"])
    )
    # A missing local plan is a mapping frontier, not proof that the domain
    # contains zero reusable LEGO or has no external contracts.
    digest = hashlib.sha256(json.dumps(paths_out, ensure_ascii=True, sort_keys=True,
                                       separators=(",", ":")).encode()).hexdigest()
    return {
        "schemaVersion": 1,
        "kind": "ordivon.source-exhaustive-coverage-projection",
        "sourceCut": source,
        "sourceTree": git(repo, "rev-parse", f"{source}^{{tree}}").decode().strip(),
        "proposalCut": proposed,
        "truthBoundary": "source-only structural classification; no installed proof, external effect, actual consumer coverage, or permission",
        "proofReuseAdmissible": False,
        "sourcePathDigest": "sha256:" + digest,
        "summary": {
            "trackedPaths": len(paths_out), "accountedForPaths": len(pathset),
            "registeredSourceRoots": len(actual.get("owners", [])),
            "currentSourceZones": dict(sorted(zones.items())),
            "proposalZones": dict(sorted(proposed_zones.items())),
            "sourceProblemCounts": dict(sorted(problem_counts.items())),
            "carriers": dict(sorted(carriers.items())),
            "plans": len(graph["files"]), "nodes": len(graph["nodes"]),
            "nodeProblems": dict(sorted(node_issue_count.items())),
            "edges": len(graph["edges"]), "edgeStanding": dict(sorted(edges.items())),
            "crossPlanLocalIdCollisions": len(graph["sameLocalIdAcrossPlans"]),
            "nonNodePlanShapes": len(graph["opaquePlans"]),
            "registeredRootsWithoutLocalLegoPlan": roots_without_plan,
        },
        "sourcePaths": paths_out, "semanticPlans": graph,
    }



def active_source_cells(
    inventory: dict, *, repo: Path, max_files: int = 24, max_depth: int = 6,
    use_proposal: bool = False, include_member_index: bool = False,
) -> dict:
    """Compute small, deterministic *physical* source cells on demand.

    The input is one exact-Git classification projection. Cells do not
    establish semantic LEGO identity, verification authority or a move plan.
    Never substitute the proposed policy for the source's actual policy.
    """
    if max_files < 1 or max_depth < 1 or max_depth > 12:
        raise ValueError("cell limits must be positive and depth <= 12")
    if use_proposal and not inventory.get("proposalCut"):
        raise ValueError("requested proposal cells need exact proposal SourceCut")
    group_key = "proposedSource" if use_proposal else "currentSource"
    source_paths = inventory["sourcePaths"]
    policy_source = inventory["proposalCut"] if use_proposal else inventory["sourceCut"]
    # These are physical Git directory cells nested under the mechanical
    # source zones. Zones remain independent of a proposed directory move.
    zones: dict[str, list[dict]] = collections.defaultdict(list)
    for item in source_paths:
        role = item[group_key]
        zone = role["classification"] if role["standing"] == "CLASSIFIED" else role["standing"]
        zones[zone].append(item)

    cells: list[dict] = []
    member_index: dict[str, str] = {}
    node_problems_by_plan: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for lego in inventory["semanticPlans"]["nodes"]:
        node_problems_by_plan[lego["plan"]].update(lego["problems"])

    def walk(zone: str, directory: str, items: list[dict], level: int) -> None:
        direct = []
        children: dict[str, list[dict]] = collections.defaultdict(list)
        for item in items:
            path = item["path"]
            if not path.startswith(directory):
                raise ValueError("source cell prefix does not contain its member")
            suffix = path[len(directory):]
            if "/" not in suffix:
                direct.append(item)
            else:
                child = suffix.split("/", 1)[0]
                children[directory + child + "/"].append(item)
        if len(items) <= max_files or not children or level >= max_depth:
            emit(zone, directory, items, level, dense=len(items) > max_files)
            return
        if direct:
            emit(zone, directory, direct, level, dense=len(direct) > max_files)
        for child, subset in sorted(children.items()):
            walk(zone, child, subset, level + 1)

    def emit(zone: str, prefix: str, members: list[dict], level: int, *, dense: bool) -> None:
        ext = collections.Counter()
        carriers = collections.Counter()
        source_problems = collections.Counter()
        semantic_problems = collections.Counter()
        for m in members:
            source_problems.update(m["problems"])
            semantic_problems.update(node_problems_by_plan[m["path"]])
            name = m["path"].rsplit("/", 1)[-1]
            ext[name.rsplit(".", 1)[-1].lower() if "." in name else "(no-extension)"] += 1
            if m["carrierType"]:
                carriers[m["carrierType"]] += 1
        issues = []
        observations = []
        if zone in ("UNASSIGNED", "AMBIGUOUS"):
            issues.append("UNCLASSIFIED_SOURCE_REGION")
        if dense:
            issues.append("DENSE_CELL_REQUIRES_SUBCLASSIFICATION_REVIEW")
        if len(ext) > 1:
            observations.append("MIXED_FORMAT_CELL_NOT_IN_ITSELF_AN_ERROR")
        if semantic_problems:
            issues.append("PLAN_DECLARATION_GAPS_REQUIRE_SEMANTIC_MAPPING")
        member_id = hashlib.sha256(json.dumps(
            [(m["path"], m["sourceIdentity"]) for m in sorted(
                members, key=lambda r: r["path"])],
            ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        ).encode()).hexdigest()
        if include_member_index:
            for member in members:
                path = member["path"]
                if path in member_index:
                    raise ValueError(f"source path assigned to multiple cells: {path}")
                member_index[path] = "sha256:" + member_id
        cells.append({
            "memberGitObjectDigest": "sha256:" + member_id,
            "sourceZone": zone,
            "physicalPrefix": prefix or "(repo-root)/",
            "depth": level,
            "pathCount": len(members),
            "firstSourcePath": min(m["path"] for m in members),
            "lastSourcePath": max(m["path"] for m in members),
            "sourceCarriers": dict(sorted(carriers.items())),
            "sourceProblemCounts": dict(sorted(source_problems.items())),
            "planDeclarationProblemCounts": dict(sorted(semantic_problems.items())),
            "extensionKinds": dict(sorted(ext.items())),
            "problems": issues,
            "observations": observations,
            "semanticStanding": "UNQUALIFIED_SOURCE_CELL",
            "consumerStanding": "UNKNOWN",
            "installedStanding": "UNKNOWN",
            "formalStanding": "UNKNOWN",
        })

    # Select the most specific physical prefix that *belongs to* its source
    # region. This avoids inventing a new root: configured source-zone policy
    # is used only as a navigational grouping, not authority.
    def anchor(zone: str, path: str, policy: dict) -> str:
        if zone.startswith("ROOT:"):
            name = zone[len("ROOT:"):]
            found = [x["root"] for x in policy.get("owners", [])
                     if x["name"] == name and path.startswith(x["root"])]
            if len(found) != 1:
                raise ValueError("owner source region and path do not match")
            return found[0]
        if zone.startswith("REGION:"):
            name = zone[len("REGION:"):]
            found = [rule for row in policy.get("source_regions", [])
                     if row["name"] == name
                     and not any(is_match(path, excluded)
                                 for excluded in row.get("exclude", []))
                     for rule in row["paths"] if is_match(path, rule)]
            if len(found) != 1:
                raise ValueError("physical region source path does not match")
            return found[0] if found[0].endswith("/") else ""
        # Unclassified paths remain visible and grouped by their real top-level
        # prefix, rather than being implicitly assigned to a fabricated owner.
        return path.split("/", 1)[0] + "/" if "/" in path else ""

    # Only this exact Git carrier policy is admissible. Caller supplies its
    # already-validated policy; no filesystem or historical snapshot lookup.
    exact_commit(repo, inventory["sourceCut"])
    policy = read_policy(repo, policy_source)
    for zone, members in sorted(zones.items()):
        buckets: dict[str, list[dict]] = collections.defaultdict(list)
        for item in members:
            buckets[anchor(zone, item["path"], policy)].append(item)
        for physical_prefix, subset in sorted(buckets.items()):
            walk(zone, physical_prefix, subset, 0)

    if sum(c["pathCount"] for c in cells) != len(source_paths):
        raise ValueError("source cell cardinality is not complete")
    if include_member_index and set(member_index) != {p["path"] for p in source_paths}:
        raise ValueError("source cell index must enumerate every Git path exactly once")
    cells.sort(key=lambda c: (c["sourceZone"], c["physicalPrefix"], c["firstSourcePath"]))
    tallies = collections.Counter(p for c in cells for p in c["problems"])
    observed = collections.Counter(p for c in cells for p in c["observations"])
    result = {
        "kind": "ordivon.source-cell-live-frontier",
        "sourceCut": inventory["sourceCut"],
        "sourceTree": inventory["sourceTree"],
        "proposalCut": inventory["proposalCut"] if use_proposal else None,
        "projection": "PROPOSED_SOURCE_ONLY" if use_proposal else "CURRENT_SOURCE_ONLY",
        "sourcePathDigest": inventory["sourcePathDigest"],
        "truthBoundary": "physical Git classification, no LEGO or formal/installed evidence",
        "proofReuseAdmissible": False,
        "summary": {
            "trackedPaths": len(source_paths),
            "countedPaths": sum(c["pathCount"] for c in cells),
            "cells": len(cells),
            "sourceZones": len(zones),
            "problemCells": sum(bool(c["problems"]) for c in cells),
            "problemCounts": dict(sorted(tallies.items())),
            "observationCounts": dict(sorted(observed.items())),
            "maxCellFiles": max_files,
            "maxCellDepth": max_depth,
        },
        "cells": cells,
    }
    if include_member_index:
        result["memberCellDigests"] = dict(sorted(member_index.items()))
    return result



def derived_problem_legos(
    inventory: dict, *, repo: Path, max_files: int = 24,
    max_depth: int = 6, use_proposal: bool = False,
) -> dict:
    """Derive a complete Phase1 source-to-problem map, NOT an authority registry.

    No source code is executed and declared plan edges are never promoted to
    verified calls. All answers come from one immutable Git-cut projection.
    """
    frontier = active_source_cells(
        inventory, repo=repo, max_files=max_files, max_depth=max_depth,
        use_proposal=use_proposal, include_member_index=True,
    )
    members = frontier["memberCellDigests"]
    cells = frontier["cells"]
    graph = inventory["semanticPlans"]
    cell_by_key: dict[tuple[str, str], dict] = {}
    for cell in cells:
        key = (cell["sourceZone"], cell["physicalPrefix"])
        if key in cell_by_key:
            raise ValueError("duplicate physical recursive source cell")
        cell_by_key[key] = cell

    def cell_ref(cell: dict) -> str:
        return "source-cell:" + cell["memberGitObjectDigest"]

    hierarchy = []
    all_cells = []
    for cell in cells:
        parent_candidates = [
            other for other in cells if other["sourceZone"] == cell["sourceZone"]
            and other is not cell
            and cell["physicalPrefix"].startswith(other["physicalPrefix"])
            and len(other["physicalPrefix"]) < len(cell["physicalPrefix"])
        ]
        parent = max(parent_candidates, key=lambda x: len(x["physicalPrefix"]),
                     default=None)
        if parent is not None:
            hierarchy.append({
                "relation": "PHYSICAL_PREFIX_CONTAINS_NOT_SEMANTIC_CALL",
                "parent": cell_ref(parent), "child": cell_ref(cell),
                "callStanding": "NOT_ESTABLISHED",
            })
        all_cells.append({
            "sourceCellRef": cell_ref(cell),
            "sourceZone": cell["sourceZone"],
            "physicalPrefix": cell["physicalPrefix"],
            "pathCount": cell["pathCount"],
            "memberGitObjectDigest": cell["memberGitObjectDigest"],
            "parentSourceCellRef": cell_ref(parent) if parent is not None else None,
            "problems": cell["problems"],
            "sourceProblemCounts": cell["sourceProblemCounts"],
            "planDeclarationProblemCounts": cell["planDeclarationProblemCounts"],
            "semanticStanding": cell["semanticStanding"],
            "consumerStanding": cell["consumerStanding"],
            "formalStanding": cell["formalStanding"],
            "installedStanding": cell["installedStanding"],
        })

    issues: list[dict] = []
    for cell in cells:
        if cell["problems"]:
            # Reuse the existing canonical problem record. Its legacy ID is
            # versioned by membership; this separate location-scoped question
            # remains addressable across evidence changes without admitting
            # proof reuse, semantic identity, or a physically moved source.
            source_question = "problem:source-scope:" + hashlib.sha256(
                json.dumps([cell["sourceZone"], cell["physicalPrefix"]],
                           separators=(",", ":"), ensure_ascii=True).encode()
            ).hexdigest()
            issues.append({
                "problemRef": "problem:cell:" + cell["memberGitObjectDigest"],
                "sourceScopeQuestionRef": source_question,
                "sourceScopeIdentityStanding": "PHYSICAL_LOCATION_QUESTION_NOT_SEMANTIC_LEGO",
                "kind": "RECURSIVE_SOURCE_CELL_ISSUE",
                "sourceCellRef": cell_ref(cell),
                "physicalPrefix": cell["physicalPrefix"],
                "sourceZone": cell["sourceZone"],
                "pathCount": cell["pathCount"],
                "issueTags": cell["problems"],
                "sourceIssueTags": cell["sourceProblemCounts"],
                "planIssueTags": cell["planDeclarationProblemCounts"],
                "consumerStanding": "UNKNOWN",
                "callSemanticsStanding": "NOT_YET_QUALIFIED",
                "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
            })
    for node in graph["nodes"]:
        if node["problems"]:
            if node["plan"] not in members:
                raise ValueError("declared Plan has no exact source cell")
            issues.append({
                "problemRef": "problem:declared-node:" + node["nodeRef"],
                "kind": "PLAN_NODE_DECLARATION_ISSUE",
                "nodeRef": node["nodeRef"],
                "sourceCellRef": "source-cell:" + members[node["plan"]],
                "plan": node["plan"],
                "issueTags": node["problems"],
                "declaredFields": node["declarations"],
                "formalQualification": node["formalQualification"],
                "consumerQualification": node["consumerQualification"],
                "implementationRefinement": node["implementationRefinement"],
                "callSemanticsStanding": "NOT_YET_QUALIFIED",
                "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
            })
    for item in graph["opaquePlans"]:
        if item["plan"] not in members:
            raise ValueError("non-node Plan has no exact source cell")
        issues.append({
            "problemRef": "problem:non-node-plan:" + item["plan"],
            "kind": "NON_NODE_PLAN_MAPPING_REVIEW",
            "plan": item["plan"],
            "sourceCellRef": "source-cell:" + members[item["plan"]],
            "issueTags": [item["standing"]],
            "callSemanticsStanding": "NOT_YET_QUALIFIED",
            "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
        })
    for name in inventory["summary"]["registeredRootsWithoutLocalLegoPlan"]:
        issues.append({
            "problemRef": "problem:root-without-local-plan:" + name,
            "kind": "LOCAL_PLAN_MAPPING_REVIEW",
            "sourceZone": "ROOT:" + name,
            "issueTags": ["NO_LOCAL_PLAN_DOES_NOT_PROVE_MISSING_CONTRACT"],
            "consumerStanding": "UNKNOWN",
            "callSemanticsStanding": "NOT_YET_QUALIFIED",
            "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
        })

    # A missing declaration is a question about a specific Plan-scoped node,
    # not a proof that a real consumer/contract/formal artifact is absent.
    field_questions = []
    for node in graph["nodes"]:
        for gap in node["problems"]:
            field_questions.append({
                "problemRef": "problem:declared-field:" + node["nodeRef"] + ":" + gap,
                "parentProblemRef": "problem:declared-node:" + node["nodeRef"],
                "nodeRef": node["nodeRef"],
                "missingDeclarationTag": gap,
                "relation": "DECLARED_FIELD_NOT_FOUND_NOT_RUNTIME_ABSENCE",
                "actualConsumerStanding": "UNKNOWN",
                "actualContractStanding": "UNKNOWN",
                "actualFormalStanding": "UNKNOWN",
                "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
            })

    # The source's existing Structure R2 plan is a declaration carrier only.
    # Reuse the same most-specific-prefix rule as classification() instead of
    # creating competing mapping authority or implying physical migration.
    structure_path = "docs/architecture/structure-r2-transition-r1.json"
    structure = read_json(repo, inventory["sourceCut"], structure_path)
    maps = structure.get("mappings", [])
    if len({m.get("id") for m in maps}) != len(maps):
        raise ValueError("structure mapping IDs must be scoped uniquely")
    mapping_witnesses: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for path in inventory["sourcePaths"]:
        matches = [(len(rule), item, rule) for item in maps
                   for rule in item.get("sourcePaths", []) if is_match(path["path"], rule)]
        longest = max((x[0] for x in matches), default=0)
        selected = [(item, rule) for length, item, rule in matches if length == longest]
        for m, rule in selected:
            if (m.get("mode") == "move"
                    and "PHYSICAL_MOVE_NOT_REALIZED_OR_CONSUMER_NOT_CUT_OVER" in path["problems"]):
                tag = "DECLARED_MOVE_CONSUMER_QUALIFICATION_REQUIRED"
            elif (len(m.get("targetPaths", [])) != 1
                  and "STRUCTURE_SPLIT_REQUIRES_CONSUMER_WITNESS" in path["problems"]):
                tag = "DECLARED_SPLIT_CONSUMER_QUALIFICATION_REQUIRED"
            else:
                continue
            mapping_witnesses[(tag, m["id"])].append(path)

    mapping_by_id = {m["id"]: m for m in maps}
    mapping_reviews = []
    for (tag, map_id), rows in sorted(mapping_witnesses.items()):
        rows.sort(key=lambda x: x["path"])
        fingerprints = [[p["path"], p["sourceIdentity"]] for p in rows]
        identity = hashlib.sha256(json.dumps(
            fingerprints, ensure_ascii=True, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        declaration = mapping_by_id[map_id]
        mapping_reviews.append({
            "reviewRef": "problem:structure-mapping:" + tag + ":" + map_id,
            "declarationRef": structure_path + "#" + map_id,
            "problemTag": tag,
            "sourcePaths": declaration.get("sourcePaths", []),
            "targetPaths": declaration.get("targetPaths", []),
            "declaredMode": declaration.get("mode"),
            "matchedPathCount": len(rows),
            "sourceMembersDigest": "sha256:" + identity,
            "sourceCellRefs": sorted({
                "source-cell:" + members[row["path"]] for row in rows
            }),
            "relation": "STRUCTURE_DECLARATION_TO_SOURCE_NOT_REALIZED_MOVE",
            "consumerStanding": "UNKNOWN",
            "installedStanding": "UNKNOWN",
            "callSemanticsStanding": "NOT_YET_QUALIFIED",
            "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
        })
    identity_scope_reviews = [
        {
            "reviewRef": "problem:plan-local-id-scope:" + local,
            "localId": local,
            "scopedNodeRefs": scoped,
            "relation": "SHARED_LOCAL_NAME_NOT_SHARED_SEMANTIC_IDENTITY",
            "collisionStanding": "REVIEW_REQUIRED_NOT_PROVEN_CONFLICT",
            "consumerStanding": "UNKNOWN",
            "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
        }
        for local, scoped in sorted(graph["sameLocalIdAcrossPlans"].items())
    ]
    if len({x["problemRef"] for x in field_questions}) != len(field_questions):
        raise ValueError("duplicate declaration-field identity")
    if len({x["reviewRef"] for x in mapping_reviews}) != len(mapping_reviews):
        raise ValueError("duplicate structure review identity")

    declared_edges = []
    for e in graph["edges"]:
        qualified = e["standing"] == "LOCAL_ENDPOINTS_IDENTIFIED"
        declared_edges.append({
            "fromNodeRef": f'{e["plan"]}#{e["from"]}' if qualified else None,
            "toNodeRef": f'{e["plan"]}#{e["to"]}' if qualified else None,
            "sourcePlan": e["plan"], "edgeIndex": e["edgeIndex"],
            "declaredEdgeType": e["edgeType"],
            "declarationStanding": e["standing"],
            "runtimeCallStanding": "NOT_ESTABLISHED",
            "effectStanding": "UNKNOWN",
        })
    issues.sort(key=lambda item: (item["kind"], item["problemRef"]))
    counters = collections.Counter(item["kind"] for item in issues)
    counts = collections.Counter(tag for item in issues for tag in item["issueTags"])
    return {
        "kind": "ordivon.phase1.exact-git-derived-problem-legos",
        "schemaVersion": 1,
        "sourceCut": inventory["sourceCut"],
        "sourceTree": inventory["sourceTree"],
        "sourcePathDigest": inventory["sourcePathDigest"],
        "proposalCut": frontier["proposalCut"],
        "projection": frontier["projection"],
        "truthBoundary": (
            "physical source and declared Plan structure only; real calls, "
            "external repos, consumers, installation, effect and formal proof UNKNOWN"
        ),
        "proofReuseAdmissible": False,
        "summary": {
            "trackedPaths": frontier["summary"]["trackedPaths"],
            "countedPaths": frontier["summary"]["countedPaths"],
            "recursiveSourceCells": len(all_cells),
            "issueRecords": len(issues),
            "issueKinds": dict(sorted(counters.items())),
            "issueTagCounts": dict(sorted(counts.items())),
            "hierarchyRelations": len(hierarchy),
            "declaredPlanEdges": len(declared_edges),
            "crossPlanLocalIdReuse": len(graph["sameLocalIdAcrossPlans"]),
            "crossPlanReuseIsError": False,
            "missingInstalledAndDynamicCallClosure": True,
            "declarationFieldQuestions": len(field_questions),
            "mappingDeclarationReviews": len(mapping_reviews),
            "crossPlanIdentityScopeReviews": len(identity_scope_reviews),
        },
        "declarationFieldQuestions": field_questions,
        "mappingDeclarationReviews": mapping_reviews,
        "crossPlanIdentityScopeReviews": identity_scope_reviews,
        "sourceCells": all_cells,
        "sourcePathCellIndex": {
            path: "source-cell:" + digest for path, digest in members.items()
        },
        "sourceContainment": sorted(
            hierarchy, key=lambda item: (item["parent"], item["child"])),
        "problemLegos": issues,
        "declaredPlanEdgesNotActualCalls": declared_edges,
        "sameLocalIdAcrossPlansObservation": graph["sameLocalIdAcrossPlans"],
    }




def join_observed_authorities(problem_frontier: dict, evidence: dict) -> dict:
    """Join caller-supplied *observations* without promoting them to truth.

    No discovery, registry, credentials, network calls or transitive closure.
    Natural authorities remain the only actual fact providers. A reference
    to their Job is a reported witness, NOT proof that the report is genuine.
    """
    import re

    if evidence.get("kind") != "ordivon.external-authority-observations-r1":
        raise ValueError("external evidence must use its explicit observation envelope")
    if evidence.get("subjectSourceCut") != problem_frontier["sourceCut"]:
        raise ValueError("observation/source SourceCut mismatch")
    incoming = evidence.get("observations")
    if not isinstance(incoming, list) or len(incoming) > 512:
        raise ValueError("external observations must be a bounded list")

    issues = {r["problemRef"] for r in problem_frontier["problemLegos"]}
    location_questions = {
        r["sourceScopeQuestionRef"]: r["problemRef"]
        for r in problem_frontier["problemLegos"]
        if r["kind"] == "RECURSIVE_SOURCE_CELL_ISSUE"
    }
    if len(location_questions) != sum(
            r["kind"] == "RECURSIVE_SOURCE_CELL_ISSUE"
            for r in problem_frontier["problemLegos"]):
        raise ValueError("ambiguous source-scope question identity")
    reused = problem_frontier["sameLocalIdAcrossPlansObservation"]
    short_questions = [
        {"problemRef": "problem:unscoped-plan-id:" + short_id,
         "localId": short_id,
         "scopedCandidates": paths,
         "standing": "AMBIGUOUS_ONLY_IF_UNSCOPED_LOOKUP_IS_ACTUALLY_CONSUMED",
         "bareIdIsAnActualCollision": False,
         "realConsumerStanding": "UNKNOWN"}
        for short_id, paths in sorted(reused.items())
    ]
    known = issues | set(location_questions) | {
        q["problemRef"] for q in short_questions
    }
    joined = []
    links = []
    keys = set()
    allowed = {"authorityRef", "subjectRef", "observationKind",
               "observationRevision", "witnessRef", "observedAt",
               "candidateProblemRef", "observedFacts"}
    types = {"INDEPENDENT_GIT_SOURCE", "NON_GIT_DATA_INVENTORY",
             "STATIC_DYNAMIC_CONSUMER_CANDIDATE",
             "INSTALLED_SERVICE_CONFIGURATION", "ENVIRONMENT_EFFECT_OBSERVED",
             "UNSCOPED_PLAN_LOOKUP_CANDIDATE"}
    for item in incoming:
        if not isinstance(item, dict) or set(item) != allowed:
            raise ValueError("observation requires exact scoped evidence fields")
        a, s, kind, revision = (item[k] for k in (
            "authorityRef", "subjectRef", "observationKind", "observationRevision"))
        if (not all(isinstance(v, str) and 1 <= len(v) <= 192
                    for v in (a, s, kind, revision)) or
                not re.fullmatch(r"[a-z][a-z0-9-]{1,24}:[A-Za-z0-9._:-]+", a) or
                not re.fullmatch(r"[A-Za-z0-9._:@#/-]+", s) or
                kind not in types):
            raise ValueError("invalid namespaced authority/subject/kind/revision")
        if (not isinstance(item["witnessRef"], str) or
                not re.fullmatch(r"(job-[A-Za-z0-9-]{8,96}|sha256:[0-9a-f]{64})",
                                 item["witnessRef"])):
            raise ValueError("observation lacks bounded witness reference")
        if not isinstance(item["observedAt"], str) or not re.fullmatch(
                r"20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z",
                item["observedAt"]):
            raise ValueError("observation timestamp is not UTC ISO seconds")
        facts = item["observedFacts"]
        if (not isinstance(facts, dict) or len(facts) > 32 or
                any(not isinstance(k, str) or len(k) > 80 or
                    not (v is None or type(v) in (str, int, float, bool)) or
                    isinstance(v, str) and len(v) > 320
                    for k, v in facts.items())):
            raise ValueError("observation fact payload must be bounded scalar metadata")
        candidate = item["candidateProblemRef"]
        if candidate is not None and (not isinstance(candidate, str)
                                      or candidate not in known):
            raise ValueError("unscoped or unrecognized Problem LEGO reference")
        if candidate is not None and candidate.startswith("problem:unscoped-plan-id:"):
            if kind != "UNSCOPED_PLAN_LOOKUP_CANDIDATE":
                raise ValueError("bare-ID question requires actual scoped syntax witness")
        key = (a, s, kind)
        if key in keys:
            raise ValueError("duplicate authority/subject/kind observation")
        keys.add(key)
        # Revision and witness are deliberately excluded from stable *subject*
        # identity. Observation digest captures both. Neither implies currentness.
        ref = "observed-subject:sha256:" + hashlib.sha256(
            json.dumps(key, separators=(",", ":")).encode()).hexdigest()
        payload_digest = "sha256:" + hashlib.sha256(
            json.dumps(item, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":")).encode()).hexdigest()
        joined.append({
            "subjectRef": ref,
            "authorityRef": a,
            "authorityLocalRef": s,
            "observationKind": kind,
            "observationRevision": revision,
            "reportedWitnessRef": item["witnessRef"],
            "observedAt": item["observedAt"],
            "observedFacts": facts,
            "evidenceDigest": payload_digest,
            "evidenceStanding": "CALLER_REPORTED_NOT_AUTHORITY_REVERIFIED",
            "semanticConsumerStanding": "UNKNOWN",
            "installedSourceEquivalence": "UNKNOWN",
            "effectCausality": "UNKNOWN",
        })
        if candidate is not None:
            links.append({
                "fromSubjectRef": ref,
                "toProblemRef": location_questions.get(candidate, candidate),
                "sourceScopeQuestionRef": candidate if candidate in location_questions else None,
                "relation": "EXPLICIT_CANDIDATE_ASSOCIATION_NOT_AN_INVOKED_EDGE",
                "consumerStanding": "UNKNOWN",
                "proofStanding": "NOT_ESTABLISHED",
            })
    output = dict(problem_frontier)
    output["observationJoin"] = {
        "kind": "ordivon.phase1.caller-supplied-cross-authority-evidence-join",
        "sourceCut": problem_frontier["sourceCut"],
        "observedSubjects": sorted(joined, key=lambda r: r["subjectRef"]),
        "candidateAssociations": sorted(links, key=lambda r: (
            r["toProblemRef"], r["fromSubjectRef"])),
        "unscopedShortIdQuestions": short_questions,
        "summary": {
            "reportedObservationSubjects": len(joined),
            "explicitCandidateAssociations": len(links),
            "unassociatedExternalSubjects": len(joined) - len(links),
            "unscopedIdAmbiguityQuestionsNotCollisions": len(short_questions),
        },
        "naturalAuthoritiesWereReadByJoin": False,
        "installedCurrentnessEstablished": False,
        "dynamicConsumerClosureEstablished": False,
        "callSemanticsEstablished": False,
        "proofReuseAdmissible": False,
        "deletionAuthorized": False,
    }
    return output


def lookup_source_paths(inventory: dict, *, repo: Path,
                        paths: list[str], max_files: int = 24,
                        max_depth: int = 6) -> dict:
    """Bounded exact-file navigation, reusing current native live cell rules.

    Every status is physical/source-only. No alias grants execution authority,
    installed qualification, a consumer claim or semantic LEGO identity.
    """
    if not paths or len(paths) > 32:
        raise ValueError("lookup accepts 1..32 exact paths per query")
    cells = active_source_cells(
        inventory, repo=repo, max_files=max_files, max_depth=max_depth,
        include_member_index=True,
    )
    members = cells.pop("memberCellDigests")
    by_digest = {c["memberGitObjectDigest"]: c for c in cells["cells"]}
    indexed = {item["path"]: item for item in inventory["sourcePaths"]}
    if len(indexed) != len(members) or set(indexed) != set(members):
        raise ValueError("exact Git source tree and cell membership diverge")
    findings = []
    for path in paths:
        if not path or path.startswith("/") or "\\" in path or \
                "." in path.split("/") or ".." in path.split("/") or \
                "//" in path or path.endswith("/"):
            findings.append({"query": path, "standing": "INVALID_SOURCE_LOCATOR",
                             "sourceIdentity": None})
            continue
        source = indexed.get(path)
        if source is None:
            findings.append({"query": path, "standing": "NOT_IN_SOURCE_CUT",
                             "sourceIdentity": None})
            continue
        cell = by_digest[members[path]]
        zone = cell["sourceZone"]
        findings.append({
            "query": path, "standing": "EXACT_GIT_SOURCE",
            "sourceIdentity": source["sourceIdentity"],
            "physicalPath": path,
            "currentSource": source["currentSource"],
            "proposedSource": source["proposedSource"],
            "sourceCell": {
                "sourceZone": zone,
                "physicalPrefix": cell["physicalPrefix"],
                "memberGitObjectDigest": cell["memberGitObjectDigest"],
                "memberCount": cell["pathCount"],
                "problems": cell["problems"],
            },
            # Render-friendly alias. The stable address remains the Git OID/path.
            "agentNavigationLabel": f"{zone} :: {cell['physicalPrefix']}",
            "carrierType": source["carrierType"],
            "sourceProblems": source["problems"],
            "semanticStanding": "UNKNOWN",
            "consumerStanding": "UNKNOWN",
            "installedStanding": "UNKNOWN",
            "formalStanding": "UNKNOWN",
        })
    return {
        "schemaVersion": 1, "kind": "ordivon.source-cut-exact-path-navigation",
        "sourceCut": inventory["sourceCut"], "sourceTree": inventory["sourceTree"],
        "proposalCut": inventory["proposalCut"],
        "sourcePathDigest": inventory["sourcePathDigest"],
        "lookupCount": len(findings),
        "truthBoundary": "one exact Git source cut; paths and cell membership only",
        "proofReuseAdmissible": False,
        "lookups": findings,
    }



def _python_module_path(
    path: str, package_init_paths: set[str] | None = None,
) -> tuple[str, str] | None:
    """Syntactic module candidate only; not active sys.path or installed code."""
    if not path.endswith(".py"):
        return None
    if "/src/" in path:
        root, relative = path.split("/src/", 1)
        root += "/src/"
    elif "/scripts/" in path:
        root, relative = path.split("/scripts/", 1)
        root += "/scripts/"
    elif path.startswith("tools/repo/"):
        root, relative = "tools/repo/", path[len("tools/repo/"):]
    elif package_init_paths:
        # Python packages with real tracked __init__.py are usable source
        # naming candidates even without a src/ packaging layout. Discover
        # only contiguous package segments; implicit namespace packages and
        # import-time sys.path changes remain unqualified.
        current = path.rsplit("/", 1)[0] if "/" in path else ""
        pkg_dirs = []
        while current and current + "/__init__.py" in package_init_paths:
            pkg_dirs.insert(0, current.rsplit("/", 1)[-1])
            current = current.rsplit("/", 1)[0] if "/" in current else ""
        if not pkg_dirs:
            return None
        root = current + "/" if current else ""
        if path.endswith("/__init__.py"):
            relative = "/".join(pkg_dirs) + "/__init__.py"
        else:
            relative = "/".join(pkg_dirs) + "/" + path.rsplit("/", 1)[-1]
    else:
        return None
    parts = relative[:-3].split("/")
    if parts[-1] == "__init__":
        parts.pop()
    if not parts or not all(p.isidentifier() for p in parts):
        return None
    return ".".join(parts), root


def static_python_import_frontier(repo: Path, source: str,
                                  focus_prefix: str | None = None) -> dict:
    """Exact-Git AST import hints. Never proves actual import/call/consumer closure."""
    exact_commit(repo, source)
    if focus_prefix is not None and (
            not focus_prefix or focus_prefix.startswith("/")
            or chr(92) in focus_prefix
            or any(part in ("", ".", "..") for part in
                   focus_prefix.rstrip("/").split("/"))):
        raise ValueError("focus prefix is not canonical Git-relative")
    py = [row for row in tree(repo, source) if row["path"].endswith(".py")]
    by_module: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    by_path = {}
    package_inits = {row["path"] for row in py
                     if row["path"].endswith("/__init__.py")
                     and row["sourceIdentity"].startswith(
                         ("100644:blob:", "100755:blob:"))}
    for row in py:
        candidate = _python_module_path(row["path"], package_inits)
        if candidate:
            by_path[row["path"]] = candidate
            by_module[candidate[0]].append((row["path"], candidate[1]))
    # Single Git batch ensures we never follow symlinks, inspect mutable
    # checkout contents or import the inspected module.
    valid = [x for x in py if x["sourceIdentity"].startswith(
        ("100644:blob:", "100755:blob:"))]
    oids = sorted({row["sourceIdentity"].split(":")[-1] for row in valid})
    proc = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(repo), "cat-file", "--batch"],
        input="".join(oid + "\n" for oid in oids).encode("ascii"),
        capture_output=True, check=True)
    by_oid = {}
    offset = 0
    for oid in oids:
        nl = proc.stdout.find(b"\n", offset)
        if nl < 0:
            raise ValueError("truncated Git batch header")
        h = proc.stdout[offset:nl].decode("ascii").split()
        if len(h) != 3 or h[0] != oid or h[1] != "blob":
            raise ValueError("unexpected source object in Git batch")
        size = int(h[2])
        end = nl + 1 + size
        if end >= len(proc.stdout) or proc.stdout[end:end + 1] != b"\n":
            raise ValueError("truncated Git blob or missing terminator")
        if size <= 196608:
            by_oid[oid] = proc.stdout[nl + 1:end]
        offset = end + 1
    if offset != len(proc.stdout):
        raise ValueError("trailing Git batch bytes")
    edge_set = set()
    unresolved = []
    dynamic = []
    skipped = []
    for row in py:
        path = row["path"]
        oid = row["sourceIdentity"].split(":")[-1]
        if oid not in by_oid:
            skipped.append({"path": path, "reason": "NONREGULAR_OR_TOO_LARGE_GIT_BLOB"})
            continue
        try:
            root = ast.parse(by_oid[oid].decode("utf-8-sig"), filename=path)
        except (SyntaxError, UnicodeError, ValueError):
            skipped.append({"path": path, "reason": "AST_SYNTAX_OR_ENCODING_UNQUALIFIED"})
            continue
        caller = by_path.get(path)
        for node in ast.walk(root):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else None)
                if name in {"__import__", "import_module", "eval", "exec"}:
                    dynamic.append({"consumerPath": path, "line": node.lineno,
                                    "standing": "DYNAMIC_OR_EVALUATION_CALL_SYNTAX_ONLY"})
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
                syntax = "ABSOLUTE_IMPORT"
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                syntax = "RELATIVE_FROM_IMPORT" if node.level else "FROM_IMPORT"
                if node.level:
                    if not caller:
                        unresolved.append({"consumerPath": path, "line": node.lineno,
                                           "expression": base,
                                           "standing": "RELATIVE_PACKAGE_SCOPE_UNKNOWN"})
                        continue
                    pkg = caller[0].split(".")
                    if not path.endswith("/__init__.py"):
                        pkg = pkg[:-1]
                    if node.level > len(pkg):
                        unresolved.append({"consumerPath": path, "line": node.lineno,
                                           "expression": base,
                                           "standing": "RELATIVE_IMPORT_OUTSIDE_CANDIDATE_ROOT"})
                        continue
                    base = ".".join([*pkg[:len(pkg) - node.level + 1],
                                     *([base] if base else [])])
                targets = [base] if base else []
                targets.extend(base + "." + alias.name if base else alias.name
                               for alias in node.names if alias.name != "*")
            else:
                continue
            resolved = False
            for target in sorted(set(targets)):
                providers = by_module.get(target, [])
                if not providers:
                    continue
                if caller:
                    local = [v for v in providers if v[1] == caller[1]]
                    if local:
                        providers = local
                if len(providers) != 1:
                    unresolved.append({"consumerPath": path, "line": node.lineno,
                                       "expression": target,
                                       "standing": "AMBIGUOUS_MODULE_CANDIDATES"})
                    continue
                provider, module_root = providers[0]
                if provider == path:
                    continue
                edge_set.add((path, provider, node.lineno, syntax, target, module_root))
                resolved = True
            if not resolved:
                unresolved.append({"consumerPath": path, "line": node.lineno,
                                   "expression": ",".join(targets) or "(empty)",
                                   "standing": "UNRESOLVED_OR_EXTERNAL_IMPORT_SYNTAX"})
    all_edges = sorted(edge_set)
    counts = (len(all_edges), len(unresolved), len(dynamic))
    if focus_prefix is not None:
        all_edges = [e for e in all_edges if
                     e[0].startswith(focus_prefix) or e[1].startswith(focus_prefix)]
        unresolved = [e for e in unresolved if e["consumerPath"].startswith(focus_prefix)]
        dynamic = [e for e in dynamic if e["consumerPath"].startswith(focus_prefix)]
        skipped = [e for e in skipped if e["path"].startswith(focus_prefix)]
    return {
        "kind": "ordivon.phase1.exact-git-python-static-consumer-hints",
        "sourceCut": source,
        "sourceTree": git(repo, "rev-parse", f"{source}^{{tree}}").decode().strip(),
        "focusPrefix": focus_prefix,
        "truthBoundary": "STATIC_PYTHON_AST_ONLY; no import resolution, executed calls, installed behavior or proof",
        "proofReuseAdmissible": False,
        "summary": {
            "gitPythonPaths": len(py),
            "sourceModuleLayoutIndexed": len(by_path),
            "sourceModuleLayoutUnknown": len(py) - len(by_path),
            "moduleNameCandidates": len(by_module),
            "ambiguousModuleNames": sum(len(v) > 1 for v in by_module.values()),
            "allStaticCandidateEdges": counts[0],
            "allUnresolvedImportStatements": counts[1],
            "allDynamicSyntaxSites": counts[2],
            "selectedEdges": len(all_edges),
            "selectedUnresolved": len(unresolved),
            "selectedDynamicSyntaxSites": len(dynamic),
            "skippedSelectedPaths": len(skipped),
            "zeroStaticEdgesProvesNoConsumers": False,
        },
        "unindexedModuleLayoutSamples": [
            x["path"] for x in py if x["path"] not in by_path
        ][:20],
        "staticCandidateEdges": [
            {"consumerPath": e[0], "providerPath": e[1], "line": e[2],
             "syntax": e[3], "moduleExpression": e[4], "candidateSearchRoot": e[5],
             "agentQueryHandle": "python-module:" + e[4],
             "consumerSourceRole": ("TEST_SOURCE_IMPORT_SYNTAX"
                                    if "/tests/" in e[0] or
                                    e[0].rsplit("/", 1)[-1].startswith("test_")
                                    else "SOURCE_IMPORT_SYNTAX"),
             "sourceStanding": "STATIC_AST_MODULE_MATCH_ONLY",
             "runtimeConsumerStanding": "UNKNOWN"}
            for e in all_edges
        ],
        "unresolvedImportStatements": unresolved,
        "dynamicSyntaxSites": dynamic,
        "skippedPaths": skipped,
    }



def exact_git_reference_hints(
    repo: Path, source: str, paths: list[str], *, per_path_limit: int = 48,
) -> dict:
    """Bounded textual cross-format references from immutable Git source only.

    All hits are lexical observations, NOT fully resolved consumers. Unknown
    or omitted references cannot justify move/retirement/proof acceptance.
    """
    exact_commit(repo, source)
    if not paths or len(paths) > 8 or not 1 <= per_path_limit <= 256:
        raise ValueError("reference query requires 1..8 paths, limit 1..256")
    source_files = tree(repo, source)
    by_path = {item["path"]: item for item in source_files}
    basename_count = collections.Counter(item["path"].rsplit("/", 1)[-1]
                                         for item in source_files)
    results = []
    for target in paths:
        if (not target or target.startswith("/") or "\\" in target
                or any(piece in ("", ".", "..") for piece in target.split("/"))):
            raise ValueError("reference path must be canonical relative Git path")
        source_item = by_path.get(target)
        if source_item is None:
            results.append({
                "queryPath": target, "standing": "NOT_IN_EXACT_GIT_SOURCE",
                "textualHits": [], "totalTextualHits": 0,
                "runtimeConsumerStanding": "UNKNOWN",
                "zeroTextualHitsProvesNoConsumers": False})
            continue
        if not source_item["sourceIdentity"].startswith(("100644:blob:", "100755:blob:")):
            results.append({
                "queryPath": target, "standing": "NONREGULAR_SOURCE_CARRIER",
                "sourceIdentity": source_item["sourceIdentity"],
                "textualHits": [], "totalTextualHits": 0,
                "runtimeConsumerStanding": "UNKNOWN",
                "zeroTextualHitsProvesNoConsumers": False})
            continue
        base = target.rsplit("/", 1)[-1]
        suffix = "/".join(target.split("/")[-2:])
        patterns = [target]
        if suffix != target:
            patterns.append(suffix)
        basename_unique = basename_count[base] == 1
        if basename_unique and len(base) >= 9:
            patterns.append(base)
        args = [
            "git", "--no-replace-objects", "-C", str(repo),
            "grep", "--null", "-n", "-I", "-F",
        ]
        for pattern in dict.fromkeys(patterns):
            args.extend(("-e", pattern))
        args.extend((source, "--"))
        proc = subprocess.run(args, capture_output=True)
        if proc.returncode not in (0, 1):
            raise ValueError("source Git grep failed; cannot project incomplete references")
        if len(proc.stdout) > 8 * 1024 * 1024:
            raise ValueError("reference scan exceeds bounded Git output budget")
        matches = []
        for line in proc.stdout.split(b"\n"):
            if not line:
                continue
            columns = line.split(b"\0", 2)
            if len(columns) != 3:
                raise ValueError("unexpected Git null-delimited lexical witness")
            locus = columns[0].decode("utf-8", "surrogateescape")
            if not locus.startswith(source + ":"):
                raise ValueError("Git grep witness from a different SourceCut")
            consumer_path = locus[len(source) + 1:]
            if consumer_path not in by_path:
                raise ValueError("reference witness outside exact Git source tree")
            try:
                line_no = int(columns[1].decode("ascii"))
            except ValueError as exc:
                raise ValueError("invalid source line reference") from exc
            if line_no <= 0:
                raise ValueError("nonpositive source witness line")
            content = columns[2].decode("utf-8", "replace")
            matched = next((p for p in patterns if p in content), None)
            if matched is None:
                raise ValueError("Git grep result does not contain query token")
            if consumer_path == target:
                continue
            carrier_role = (
                "PYTHON_SOURCE_LITERAL_REFERENCE" if consumer_path.endswith(".py")
                else "SHELL_SOURCE_LITERAL_REFERENCE" if consumer_path.endswith(".sh")
                else "JSON_DECLARATION_LITERAL_REFERENCE" if consumer_path.endswith(".json")
                else "DOCUMENT_LITERAL_REFERENCE" if consumer_path.endswith(".md")
                else "OTHER_TEXT_CARRIER_LITERAL_REFERENCE")
            matches.append({
                "candidateConsumerPath": consumer_path,
                "candidateConsumerCarrierRole": carrier_role,
                "consumerGitIdentity": by_path[consumer_path]["sourceIdentity"],
                "sourceLine": line_no,
                "literalPattern": matched,
                "patternStanding": (
                    "EXACT_RELATIVE_PATH_LITERAL" if matched == target
                    else "TWO_COMPONENT_PATH_LITERAL" if matched == suffix
                    else "UNIQUE_BASENAME_LITERAL"),
                "observedLineExcerpt": content[:210],
                "semanticConsumerStanding": "UNKNOWN",
                "installedConsumerStanding": "UNKNOWN",
            })
        matches.sort(key=lambda r: (r["candidateConsumerPath"], r["sourceLine"]))
        results.append({
            "queryPath": target,
            "standing": "EXACT_GIT_FILE_LEXICAL_REFERENCE_SCAN",
            "sourceIdentity": source_item["sourceIdentity"],
            "basenameUniqueInSource": basename_unique,
            "patternsUsed": list(dict.fromkeys(patterns)),
            "totalTextualHits": len(matches),
            "truncated": len(matches) > per_path_limit,
            "textualHits": matches[:per_path_limit],
            "runtimeConsumerStanding": "UNKNOWN",
            "zeroTextualHitsProvesNoConsumers": False,
        })
    return {
        "kind": "ordivon.phase1.cross-format-lexical-reference-candidates",
        "sourceCut": source,
        "sourceTree": git(repo, "rev-parse", f"{source}^{{tree}}").decode().strip(),
        "truthBoundary": "EXACT_GIT_TEXT_REFERENCE_ONLY; import/use/installed/semantic resolution UNKNOWN",
        "proofReuseAdmissible": False,
        "pathCount": len(results),
        "queries": results,
    }



def independent_scope_frontier(
    repo: Path, source: str, *, external_git: list[str],
    non_git_data: list[str], max_entries: int = 512,
    git_checkout_observations: bool = False,
) -> dict:
    """Read-only scopes beside one exact Git subject. No membership inference.

    Git scopes require independently pinned commits. Non-Git directories are
    locators ONLY; a directory name or stat never becomes a content digest.
    Installed binary and runtime consumer effects are not observed here.
    """
    exact_commit(repo, source)
    if not external_git and not non_git_data:
        raise ValueError("external scopes require an explicitly named source")
    if len(external_git) + len(non_git_data) > 16 or not 1 <= max_entries <= 512:
        raise ValueError("external scope count/entry limit exceeds bounded survey")
    label_pattern = re.compile(r"[a-z][a-z0-9._-]{0,47}\Z")
    labels: set[str] = set()
    scopes = []

    def qualified_label(label: str) -> str:
        if not label_pattern.fullmatch(label) or label in labels:
            raise ValueError("scope label must be unique canonical ASCII identifier")
        labels.add(label)
        return label

    def absolute_locator(raw: str) -> Path:
        path = Path(raw)
        if not path.is_absolute() or ".." in path.parts or not path.is_dir():
            raise ValueError("external root must be a present canonical absolute directory")
        if path.is_symlink() or path.resolve() != path:
            raise ValueError("external directory locator cannot be a symlink/alias")
        return path

    for raw in external_git:
        label, sep, remainder = raw.partition("=")
        if not sep:
            raise ValueError("Git scope requires label=absolute_path@exact_git_cut")
        qualified_label(label)
        root_name, cut_sep, cut = remainder.rpartition("@")
        if not cut_sep:
            raise ValueError("Git scope requires explicit independent Git commit")
        root = absolute_locator(root_name)
        top = git(root, "rev-parse", "--show-toplevel").decode().strip()
        if Path(top).resolve() != root:
            raise ValueError("external Git scope must be a repository root")
        exact_commit(root, cut)
        paths = tree(root, cut)
        top_levels = collections.Counter(
            x["path"].split("/", 1)[0] for x in paths)
        scope = {
            "scopeRef": "git-scope:" + label + "@" + cut,
            "label": label,
            "labelStanding": "CALLER_SCOPED_ALIAS_NOT_GLOBAL_IDENTITY",
            "scopeKind": "INDEPENDENT_GIT_SOURCE_CUT",
            "observedLocalLocator": str(root),
            "sourceCut": cut,
            "sourceTree": git(root, "rev-parse", f"{cut}^{{tree}}").decode().strip(),
            "trackedPaths": len(paths),
            "topLevelPaths": dict(sorted(top_levels.items())),
            "sourceIdentityStanding": "EXACT_GIT_TREE_ONLY",
            "worktreeCurrentnessStanding": "NOT_OBSERVED",
            "ordivonAffiliationStanding": "UNKNOWN",
            "crossScopeConsumerStanding": "UNKNOWN",
            "installedStanding": "UNKNOWN",
        }
        if git_checkout_observations:
            # Index, worktree metadata and pinned commit tree are separate
            # objects. Observe them explicitly, without conflating content
            # equality, invocation or safe deletion.
            checkout_sha = git(root, "rev-parse", "--verify", "HEAD").decode().strip()
            index_paths = [x for x in git(root, "ls-files", "-z").split(bytes([0])) if x]
            records = git(root, "worktree", "list", "--porcelain").decode(
                "utf-8", "surrogateescape").split("\n\n")
            worktrees = []
            for block in records:
                lines = block.splitlines()
                paths_here = [line[len("worktree "):] for line in lines
                              if line.startswith("worktree ")]
                if not paths_here:
                    continue
                if len(paths_here) != 1:
                    raise ValueError("ambiguous worktree metadata locator")
                location = paths_here[0]
                prunable = any(line.startswith("prunable ") or line == "prunable"
                               for line in lines)
                worktrees.append({
                    "locator": location,
                    "prunable": prunable,
                    "pathPresent": os.path.exists(location),
                })
            prunable = [w for w in worktrees if w["prunable"]]
            scope["checkoutObservation"] = {
                "checkedOutHead": checkout_sha,
                "checkedOutHeadMatchesSourceCut": checkout_sha == cut,
                "indexTrackedPaths": len(index_paths),
                "pinnedCommitTreePaths": len(paths),
                "indexToCommitCountStanding": (
                    "COUNTS_EQUAL_CONTENT_NOT_PROVEN" if len(index_paths) == len(paths)
                    else "COUNT_MISMATCH_NO_SEMANTIC_CONCLUSION"),
                "linkedWorktreeMetadataRecords": len(worktrees),
                "prunableWorktreeRecords": len(prunable),
                "prunableLocationMissingCount": sum(
                    not w["pathPresent"] for w in prunable),
                "prunableWorktreeObservations": prunable[:64],
                "prunableObservationsTruncated": len(prunable) > 64,
                "indexIdentityStanding": "INDEX_PATH_COUNT_ONLY",
                "safeCleanupStanding": "NOT_ESTABLISHED",
                "runtimeConsumerStanding": "UNKNOWN",
            }
        scopes.append(scope)
    for raw in non_git_data:
        label, sep, path = raw.partition("=")
        if not sep:
            raise ValueError("non-Git source requires label=absolute_directory")
        qualified_label(label)
        root = absolute_locator(path)
        # Avoid promoting a Git repository to an unbound dataset carrier.
        git_probe = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(root),
             "rev-parse", "--show-toplevel"],
            capture_output=True,
        )
        if git_probe.returncode == 0:
            raise ValueError("non-Git dataset path belongs to a Git worktree")
        kinds = collections.Counter()
        entry_count = 0
        with os.scandir(root) as entries:
            for entry in entries:
                entry_count += 1
                if entry_count > max_entries:
                    raise ValueError("non-Git directory entry survey exceeded limit")
                mode = entry.stat(follow_symlinks=False).st_mode
                kinds["directory" if stat.S_ISDIR(mode) else
                      "file" if stat.S_ISREG(mode) else
                      "symlink" if stat.S_ISLNK(mode) else "other"] += 1
        scopes.append({
            "scopeRef": "non-git-locator:" + label,
            "label": label,
            "labelStanding": "CALLER_SCOPED_ALIAS_NOT_GLOBAL_IDENTITY",
            "scopeKind": "NON_GIT_DATA_DIRECTORY_OBSERVATION",
            "observedLocalLocator": str(root),
            "directChildEntries": entry_count,
            "directChildKinds": dict(sorted(kinds.items())),
            "sourceIdentityStanding": "UNBOUND_NON_GIT_BYTES",
            "contentDigestStanding": "NOT_COMPUTED",
            "recursiveContentsStanding": "NOT_OBSERVED",
            "ordivonAffiliationStanding": "UNKNOWN",
            "crossScopeConsumerStanding": "UNKNOWN",
            "installedStanding": "UNKNOWN",
        })
    scopes.sort(key=lambda r: r["scopeRef"])
    scope_problems = [
        {
            "problemRef": "problem:cross-plane-scope:" + row["scopeRef"],
            "scopeRef": row["scopeRef"],
            "kind": ("INDEPENDENT_GIT_CONSUMER_SCOPE_REVIEW"
                     if row["scopeKind"] == "INDEPENDENT_GIT_SOURCE_CUT"
                     else "NON_GIT_DATA_IDENTITY_REVIEW"),
            "issueTags": (["AFFILIATION_AND_DYNAMIC_CONSUMERS_UNQUALIFIED"]
                          if row["scopeKind"] == "INDEPENDENT_GIT_SOURCE_CUT"
                          else ["DATASET_CONTENT_DIGEST_AND_CONSUMERS_UNKNOWN"]),
            "consumerStanding": "UNKNOWN",
            "installedStanding": "UNKNOWN",
            "runtimeCallStanding": "NOT_ESTABLISHED",
            "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
        }
        for row in scopes
    ]
    if git_checkout_observations:
        for scope in scopes:
            state = scope.get("checkoutObservation")
            if state is None:
                continue
            issue_kinds = []
            if not state["checkedOutHeadMatchesSourceCut"]:
                issue_kinds.append("CHECKOUT_HEAD_DIFFERS_FROM_PINNED_CUT")
            if state["indexTrackedPaths"] != state["pinnedCommitTreePaths"]:
                issue_kinds.append("INDEX_AND_COMMIT_TREE_COUNTS_DIFFER")
            if state["prunableWorktreeRecords"]:
                issue_kinds.append("PRUNABLE_WORKTREE_METADATA_REQUIRES_CONSUMER_REVIEW")
            for kind in issue_kinds:
                scope_problems.append({
                    "problemRef": "problem:cross-plane-checkout:" + scope["scopeRef"] + ":" + kind,
                    "scopeRef": scope["scopeRef"],
                    "kind": kind,
                    "issueTags": ["NO_EMPTY_REPO_OR_CLEANUP_CONCLUSION_ALLOWED"],
                    "consumerStanding": "UNKNOWN",
                    "installedStanding": "UNKNOWN",
                    "runtimeCallStanding": "NOT_ESTABLISHED",
                    "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
                })

    return {
        "kind": "ordivon.phase1.cross-plane-source-scope-observations",
        "sourceCut": source,
        "sourceTree": git(repo, "rev-parse", f"{source}^{{tree}}").decode().strip(),
        "truthBoundary": (
            "exact Git tree objects for explicitly pinned Git roots, "
            "top-level directory metadata only for non-Git; no consumers, "
            "deployment, external affiliation, executable effects or proofs"
        ),
        "proofReuseAdmissible": False,
        "summary": {
            "externalGitRoots": len(external_git),
            "nonGitDirectoryLocators": len(non_git_data),
            "externalGitTrackedPaths": sum(r.get("trackedPaths", 0) for r in scopes),
            "crossPlaneProblemRecords": len(scope_problems),
            "crossScopeCallsVerified": 0,
            "installedSourcesBoundToGit": 0,
            "missingDynamicConsumerClosure": True,
            "gitCheckoutObservationRequested": git_checkout_observations,
            "checkoutCountMismatchScopes": sum(
                x.get("checkoutObservation", {}).get("indexToCommitCountStanding") ==
                "COUNT_MISMATCH_NO_SEMANTIC_CONCLUSION" for x in scopes),
            "prunableWorktreeMetadataRecords": sum(
                x.get("checkoutObservation", {}).get("prunableWorktreeRecords", 0)
                for x in scopes),
        },
        "relatedNativeQueries": [
            "--problem-legos (main Git source and Plan only)",
            "--static-python-consumers (static AST/dynamic syntax observations only)",
            "--reference-path (bounded cross-format lexical witnesses only)",
        ],
        "observedScopes": scopes,
        "pendingScopeProblems": scope_problems,
        "crossScopeRelationships": [
            {"subjectCut": source, "otherScopeRef": row["scopeRef"],
             "relationshipStanding": "UNQUALIFIED_NOT_A_RUNTIME_CALL"}
            for row in scopes
        ],
    }



def cross_scope_exact_locator_hints(
    main_repo: Path, scope_frontier: dict, *, max_witnesses: int = 12,
) -> dict:
    """Lexical Git file → explicitly named other-root locator, never a call.

    Only exact ABSOLUTE source-locator byte mentions qualify as hints. Unlike
    runtime import resolution or instrumented execution, Git grep cannot tell
    whether code reads a path, executes it, or merely documents it.
    """
    if not 1 <= max_witnesses <= 64:
        raise ValueError("cross-scope witness limit must be 1..64")
    if scope_frontier.get("kind") != "ordivon.phase1.cross-plane-source-scope-observations":
        raise ValueError("cross-scope hints require native exact-cut scope census")
    scopes = scope_frontier["observedScopes"]
    if len(scopes) > 9:
        raise ValueError("cross-scope lexical survey permits up to nine declared scopes")
    targets = [
        (x["scopeRef"], x["observedLocalLocator"].encode("utf-8"))
        for x in scopes
    ]
    subject = scope_frontier["sourceCut"]
    exact_commit(main_repo, subject)
    all_sources = [("git-scope:subject@" + subject, main_repo, subject)]
    for scope in scopes:
        if scope["scopeKind"] == "INDEPENDENT_GIT_SOURCE_CUT":
            root = Path(scope["observedLocalLocator"])
            exact_commit(root, scope["sourceCut"])
            all_sources.append((scope["scopeRef"], root, scope["sourceCut"]))
    hits = []
    scanned = []
    for reader_ref, root, cut in all_sources:
        # Binding each hint to its real blob makes the result source-qualified;
        # no uncommitted worktree data can be included accidentally.
        blobs = {x["path"]: x["sourceIdentity"] for x in tree(root, cut)}
        scanned.append({"readerScopeRef": reader_ref, "sourceCut": cut,
                        "sourceTree": git(root, "rev-parse", f"{cut}^{{tree}}").decode().strip(),
                        "trackedPaths": len(blobs)})
        for target_ref, token in targets:
            if target_ref == reader_ref:
                continue
            cmd = ["git", "--no-replace-objects", "-C", str(root),
                   "grep", "-l", "-z", "-I", "-F", "-e",
                   token.decode("utf-8"), cut, "--"]
            proc = subprocess.run(cmd, capture_output=True)
            if proc.returncode not in (0, 1):
                raise ValueError("Git grep lexical survey failed closed")
            prefix = (cut + ":").encode("ascii")
            paths = []
            for item in proc.stdout.split(b"\0"):
                if not item:
                    continue
                if not item.startswith(prefix):
                    raise ValueError("Git grep witness lacks exact source-cut prefix")
                name = item[len(prefix):].decode("utf-8", "surrogateescape")
                if name not in blobs:
                    raise ValueError("Git grep matched file absent from immutable source tree")
                paths.append(name)
            if len(paths) != len(set(paths)):
                raise ValueError("Git grep returned duplicate lexical witnesses")
            if not paths:
                continue
            paths.sort()
            hits.append({
                "readerScopeRef": reader_ref,
                "mentionedScopeRef": target_ref,
                "referenceKind": "EXACT_ABSOLUTE_LOCATOR_BYTES_IN_GIT_SOURCE",
                "matchingGitSourceFiles": len(paths),
                "witnessesTruncated": len(paths) > max_witnesses,
                "witnesses": [
                    {"readerPath": name, "readerSourceIdentity": blobs[name],
                     "readerSourceCut": cut,
                     "referenceStanding": "LEXICAL_ONLY_NOT_EXECUTED"}
                    for name in paths[:max_witnesses]
                ],
                "consumerStanding": "UNKNOWN",
                "runtimeCallStanding": "NOT_ESTABLISHED",
                "deploymentStanding": "UNKNOWN",
                "formalQualification": "UNKNOWN",
                "remediationStanding": "DEFER_UNTIL_JOINT_CALL_SEMANTICS",
            })
    hits.sort(key=lambda x: (x["readerScopeRef"], x["mentionedScopeRef"]))
    return {
        "kind": "ordivon.phase1.exact-cross-scope-lexical-locator-hints",
        "subjectSourceCut": subject,
        "truthBoundary": (
            "Git blob exact absolute path token only; dynamic/string-composed/"
            "indirect consumers, Windows path aliases, semantic calls, "
            "installed effects and proofs NOT RESOLVED"
        ),
        "summary": {
            "gitRootsScanned": len(all_sources),
            "otherScopeLocatorsSearched": len(targets),
            "pairsWithLiteralReferences": len(hits),
            "gitFilePairMentions": sum(x["matchingGitSourceFiles"] for x in hits),
            "zeroLexicalHitsProveNoConsumers": False,
            "runtimeCallEdgesVerified": 0,
            "installedSourceEquivalenceVerified": 0,
        },
        "scannedGitSources": scanned,
        "literalReferencePairsNotCalls": hits,
        "proofReuseAdmissible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cut", required=True)
    parser.add_argument("--proposal-cut")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--only-problems", action="store_true")
    parser.add_argument("--authority-observations", type=Path,
                        help="optional bounded caller-supplied evidence join; requires --problem-legos")
    parser.add_argument("--problem-legos", action="store_true",
                        help="derived full source+Plan problem LEGO map; never a registry")
    parser.add_argument("--scope-census", action="store_true",
                        help="observe explicit independent Git and non-Git source scopes")
    parser.add_argument("--scope-git-worktrees", action="store_true",
                        help="read-only Git checkout/index/prunable-worktree observations for explicit Git scopes")
    parser.add_argument("--scope-locator-hints", action="store_true",
                        help="Git blob lexical references between pinned roots; NOT runtime calls")
    parser.add_argument("--scope-witness-limit", type=int, default=12)
    parser.add_argument("--external-git-cut", action="append", default=[],
                        help="label=absolute_git_root@exact_40hex_commit; no installed inference")
    parser.add_argument("--non-git-root", action="append", default=[],
                        help="label=absolute_non_git_directory; observes immediate entries only")
    parser.add_argument("--reference-path", action="append", default=[],
                        help="cross-format Git textual reference witness for exact file path")
    parser.add_argument("--reference-limit", type=int, default=48,
                        help="maximum witness lines per source path, 1..256")
    parser.add_argument("--static-python-consumers", action="store_true",
                        help="exact Git AST import candidate references; not live consumers")
    parser.add_argument("--imports-prefix",
                        help="show AST import hints touching this canonical source prefix")
    parser.add_argument("--live-cells", action="store_true",
                        help="derive fresh exact-Git recursive source cells; never load saved snapshots")
    parser.add_argument("--use-proposal-cells", action="store_true",
                        help="show proposal-source regions without treating them as current authority")
    parser.add_argument("--cell-max-files", type=int, default=24)
    parser.add_argument("--cell-max-depth", type=int, default=6)
    parser.add_argument("--lookup-path", action="append", default=[],
                        help="small exact-Git source/path query; repeat for multiple files")
    args = parser.parse_args()
    if args.scope_census:
        if (args.problem_legos or args.reference_path or args.lookup_path
                or args.static_python_consumers or args.live_cells or args.proposal_cut
                or args.use_proposal_cells or args.only_problems or args.imports_prefix
                or args.reference_limit != 48
                or args.authority_observations is not None):
            parser.error("scope census is separate from source/call/problem projections")
        result = independent_scope_frontier(
            args.repo, args.source_cut, external_git=args.external_git_cut,
            non_git_data=args.non_git_root,
            git_checkout_observations=args.scope_git_worktrees)
        if args.scope_locator_hints:
            result["lexicalSourceHints"] = cross_scope_exact_locator_hints(
                args.repo, result, max_witnesses=args.scope_witness_limit)
            if args.summary:
                result["lexicalSourceHints"].pop("literalReferencePairsNotCalls")
                result["lexicalSourceHints"].pop("scannedGitSources")
        elif args.scope_witness_limit != 12:
            parser.error("--scope-witness-limit requires --scope-locator-hints")
        if args.summary:
            result.pop("observedScopes")
            result.pop("crossScopeRelationships")
            result.pop("pendingScopeProblems")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if (args.external_git_cut or args.non_git_root or
            args.scope_git_worktrees or args.scope_locator_hints):
        parser.error("external scope, Git checkout and lexical hints require --scope-census")
    if args.scope_witness_limit != 12:
        parser.error("scope-witness-limit requires scope-census and locator hints")

    if args.authority_observations is not None and not args.problem_legos:
        parser.error("--authority-observations requires --problem-legos")
    if args.reference_path:
        if (args.lookup_path or args.static_python_consumers or args.live_cells
                or args.proposal_cut or args.use_proposal_cells or args.only_problems
                or args.imports_prefix or args.summary or args.problem_legos):
            parser.error("reference witness mode is mutually exclusive with projection modes")
        result = exact_git_reference_hints(
            args.repo, args.source_cut, args.reference_path,
            per_path_limit=args.reference_limit)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args.reference_limit != 48:
        parser.error("reference-limit requires reference-path")
    if args.problem_legos and (
        args.lookup_path or args.static_python_consumers or args.imports_prefix
        or args.only_problems or args.live_cells
    ):
        parser.error("problem-legos is a distinct derived source/Plan projection mode")
    if args.imports_prefix and not args.static_python_consumers:
        parser.error("imports-prefix requires static-python-consumers")
    if args.lookup_path and args.static_python_consumers:
        parser.error("exact source-cell path lookup and static consumer scan are separate modes")
    if args.lookup_path and (args.live_cells or args.only_problems or args.summary
                            or args.use_proposal_cells):
        parser.error("--lookup-path is a distinct small-result mode")
    if args.static_python_consumers:
        if args.proposal_cut or args.live_cells or args.only_problems:
            parser.error("static import hints cannot claim proposed classifications or moves")
        result = static_python_import_frontier(
            args.repo, args.source_cut, focus_prefix=args.imports_prefix)
        if args.summary:
            result = {k: v for k, v in result.items() if k not in (
                "staticCandidateEdges", "unresolvedImportStatements",
                "dynamicSyntaxSites", "skippedPaths",
                "unindexedModuleLayoutSamples")}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    result = classification(args.repo, args.source_cut, args.proposal_cut)
    if args.problem_legos:
        result = derived_problem_legos(
            result, repo=args.repo, max_files=args.cell_max_files,
            max_depth=args.cell_max_depth, use_proposal=args.use_proposal_cells,
        )
        if args.authority_observations is not None:
            # Explicit local evidence input, bounded and non-authoritative:
            # this join never probes/impersonates the named natural authority.
            if args.authority_observations.stat().st_size > 262144:
                raise ValueError("authority observation file exceeds 256KiB")
            evidence = json.loads(args.authority_observations.read_text(encoding="utf-8"))
            result = join_observed_authorities(result, evidence)
        if args.summary:
            if "observationJoin" in result:
                result["observationJoin"] = {
                    k: v for k, v in result["observationJoin"].items()
                    if k not in ("observedSubjects", "candidateAssociations",
                                 "unscopedShortIdQuestions")
                }
            result = {k: v for k, v in result.items()
                      if k not in ("sourceCells", "sourcePathCellIndex",
                                   "sourceContainment", "problemLegos",
                                   "declaredPlanEdgesNotActualCalls",
                                   "sameLocalIdAcrossPlansObservation",
                                   "declarationFieldQuestions",
                                   "mappingDeclarationReviews",
                                   "crossPlanIdentityScopeReviews")}
    elif args.lookup_path:
        result = lookup_source_paths(
            result, repo=args.repo, paths=args.lookup_path,
            max_files=args.cell_max_files, max_depth=args.cell_max_depth,
        )
    elif args.live_cells:
        result = active_source_cells(
            result, repo=args.repo, max_files=args.cell_max_files, max_depth=args.cell_max_depth,
            use_proposal=args.use_proposal_cells,
        )
        if args.only_problems:
            result["cells"] = [c for c in result["cells"] if c["problems"]]
            result["displaySelection"] = "ONLY_EXPLICIT_SOURCE_PROBLEMS"
        if args.summary:
            result.pop("cells")
    elif args.summary:
        result = {k: v for k, v in result.items() if k not in ("sourcePaths", "semanticPlans")}
    elif args.only_problems:
        result["sourcePaths"] = [r for r in result["sourcePaths"] if r["problems"]]
        result["semanticPlans"]["nodes"] = [
            n for n in result["semanticPlans"]["nodes"] if n["problems"]]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
