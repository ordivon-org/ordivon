#!/usr/bin/env python3
"""Exact-Git, exhaustive Ordivon source/semantic declaration inventory.

Read-only derived projection. Does not add owners, authorize actions, certify
consumers, qualify installed state, or prove any concrete implementation.
A peer's proposed source-regions are compared as an explicit independent
proposal SourceCut, never silently installed into the subject SourceCut.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
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
        "coverageDomain": "TRACKED_PATHS_IN_ONE_EXACT_GIT_TREE",
        "coverageQualification": {
            "sourcePathEnumeration": "COMPLETE_AT_SOURCECUT",
            "designedResponsibilities": "UNKNOWN",
            "actualConsumerClosure": "UNKNOWN",
            "installedRealizations": "UNKNOWN",
            "runtimeStateAndArtifacts": "UNKNOWN",
            "externalEnvironment": "UNKNOWN",
        },
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
        "coverageDomain": inventory["coverageDomain"],
        "coverageQualification": dict(inventory["coverageQualification"]),
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
        "coverageDomain": inventory["coverageDomain"],
        "coverageQualification": dict(inventory["coverageQualification"]),
        "sourceCut": inventory["sourceCut"], "sourceTree": inventory["sourceTree"],
        "proposalCut": inventory["proposalCut"],
        "sourcePathDigest": inventory["sourcePathDigest"],
        "lookupCount": len(findings),
        "truthBoundary": "one exact Git source cut; paths and cell membership only",
        "proofReuseAdmissible": False,
        "lookups": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cut", required=True)
    parser.add_argument("--proposal-cut")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--only-problems", action="store_true")
    parser.add_argument("--live-cells", action="store_true",
                        help="derive fresh exact-Git recursive source cells; never load saved snapshots")
    parser.add_argument("--use-proposal-cells", action="store_true",
                        help="show proposal-source regions without treating them as current authority")
    parser.add_argument("--cell-max-files", type=int, default=24)
    parser.add_argument("--cell-max-depth", type=int, default=6)
    parser.add_argument("--lookup-path", action="append", default=[],
                        help="small exact-Git source/path query; repeat for multiple files")
    args = parser.parse_args()
    if args.lookup_path and (args.live_cells or args.only_problems or args.summary
                            or args.use_proposal_cells):
        parser.error("--lookup-path is a distinct small-result mode")
    result = classification(args.repo, args.source_cut, args.proposal_cut)
    if args.lookup_path:
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
