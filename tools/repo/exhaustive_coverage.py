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



def derive_problem_legos(
    inventory: dict, *, repo: Path, max_files: int = 24, max_depth: int = 6,
    use_proposal: bool = False,
) -> dict:
    """Turn each observed source-cell problem into a *pending* problem LEGO.

    This is a derived, read-only work frontier, not a registry or invocation
    graph. A path/blob is an exact source atom, never evidence of a semantic
    LEGO, no-consumer status, correctness proof, or installed code.
    """
    # Fail closed for programmatic callers that pass a stale, synthetic, or
    # tampered inventory. The CLI already derives this from exact Git, but
    # the reusable function must not accept caller-supplied fake blob IDs.
    expected = tree(repo, exact_commit(repo, inventory["sourceCut"]))
    actual = sorted(
        ({k: item[k] for k in ("path", "sourceIdentity")}
         for item in inventory["sourcePaths"]), key=lambda x: x["path"]
    )
    if expected != actual:
        raise ValueError("problem LEGO source atoms differ from exact Git tree")
    cells = active_source_cells(
        inventory, repo=repo, max_files=max_files, max_depth=max_depth,
        use_proposal=use_proposal, include_member_index=True,
    )
    by_cell: dict[str, list[dict]] = collections.defaultdict(list)
    for item in inventory["sourcePaths"]:
        by_cell[cells["memberCellDigests"][item["path"]]].append(item)
    nodes_by_path: dict[str, list[dict]] = collections.defaultdict(list)
    for node in inventory["semanticPlans"]["nodes"]:
        nodes_by_path[node["plan"]].append(node)
    result = []
    unique_ids = set()
    for cell in cells["cells"]:
        if not cell["problems"]:
            continue
        cid = cell["memberGitObjectDigest"]
        members = sorted(by_cell[cid], key=lambda item: item["path"])
        if len(members) != cell["pathCount"]:
            raise ValueError("source cell lost exact Git member identity")
        for issue in sorted(cell["problems"]):
            oid = hashlib.sha256(json.dumps(
                [issue, cell["sourceZone"], cell["physicalPrefix"]],
                ensure_ascii=True, separators=(",", ":"),
            ).encode()).hexdigest()
            problem_ref = "source-problem:sha256:" + oid
            if problem_ref in unique_ids:
                raise ValueError("duplicate problem LEGO identity")
            unique_ids.add(problem_ref)
            named_nodes = sorted(
                (node for item in members
                 for node in nodes_by_path.get(item["path"], ())
                 if node["problems"]),
                key=lambda n: n["nodeRef"],
            ) if issue == "PLAN_DECLARATION_GAPS_REQUIRE_SEMANTIC_MAPPING" else []
            if issue == "PLAN_DECLARATION_GAPS_REQUIRE_SEMANTIC_MAPPING" and not named_nodes:
                raise ValueError("plan problem has no exact plan-path declaration")
            source_atoms = [{
                "sourcePath": item["path"],
                "sourceIdentity": item["sourceIdentity"],
                "carrierType": item["carrierType"],
                "proposedClassification": (
                    item["proposedSource"]["classification"]
                    if use_proposal and item.get("proposedSource")
                    and item["proposedSource"]["standing"] == "CLASSIFIED"
                    else None
                ),
            } for item in members]
            if issue == "DENSE_CELL_REQUIRES_SUBCLASSIFICATION_REVIEW":
                relative = [
                    x["sourcePath"][len(cell["physicalPrefix"]):]
                    if cell["physicalPrefix"] != "(repo-root)/"
                    else x["sourcePath"]
                    for x in source_atoms
                ]
                all_flat = all("/" not in x for x in relative)
                if all_flat:
                    why = "FLAT_DIRECTORY_ATOMIC_SOURCE_FILES"
                elif cell["depth"] >= max_depth:
                    why = "RECURSIVE_DEPTH_CAP_REACHED"
                else:
                    why = "MIXED_DIRECT_AND_NESTED_PATHS_REQUIRE_RECHECK"
            else:
                why = None
            # Every absent node declaration is a *separate, source-scoped
            # question*, not an asserted absence of a real consumer/proof.
            atom_identities = {a["sourcePath"]: a["sourceIdentity"]
                               for a in source_atoms}
            plan_obligations = []
            for node in named_nodes:
                path = node["plan"]
                for missing in sorted(node["problems"]):
                    subref = "source-problem-obligation:sha256:" + hashlib.sha256(
                        json.dumps([node["nodeRef"], missing],
                                   ensure_ascii=True, separators=(",", ":")).encode()
                    ).hexdigest()
                    plan_obligations.append({
                        "obligationRef": subref,
                        "planNodeRef": node["nodeRef"],
                        "missingDeclaration": missing,
                        "planSourceIdentity": atom_identities[path],
                        "standing": "DECLARATION_GAP_NOT_BEHAVIORAL_ABSENCE",
                        "consumerAndInvocationStanding": "UNKNOWN",
                    })
            if len({r["obligationRef"] for r in plan_obligations}) != len(plan_obligations):
                raise ValueError("duplicate plan gap obligation")
            result.append({
                "problemRef": problem_ref,
                "kind": "ordivon.phase1.pending-source-problem-lego",
                "issue": issue,
                "sourceCellDigest": cid,
                "sourceZone": cell["sourceZone"],
                "physicalPrefix": cell["physicalPrefix"],
                "sourcePathCount": len(source_atoms),
                "sourceAtoms": source_atoms,
                "densityCause": why,
                "planNodeRefs": [n["nodeRef"] for n in named_nodes],
                "planNodeDeclaredProblems": {
                    n["nodeRef"]: n["problems"] for n in named_nodes
                },
                "planProblemObligations": plan_obligations,
                "standing": "PROBLEM_DISCOVERED_NOT_YET_RESOLVED",
                "consumerStanding": "UNKNOWN",
                "invocationStanding": "NOT_MAPPED",
                "formalStanding": "UNKNOWN",
                "installedStanding": "UNKNOWN",
                "replaceOrDeleteStanding": "NOT_QUALIFIED",
            })
    # A bare local ID may be reused in distinct plans without colliding in
    # the real scoped identity. This is a pending *lookup ambiguity*, not
    # evidence that either declared LEGO is incorrectly implemented.
    nodes_by_ref = {node["nodeRef"]: node for node in inventory["semanticPlans"]["nodes"]}
    source_by_path = {r["path"]: r["sourceIdentity"] for r in inventory["sourcePaths"]}
    collisions = []
    for local_id, refs in sorted(
        inventory["semanticPlans"]["sameLocalIdAcrossPlans"].items()
    ):
        if len(refs) < 2 or len(set(refs)) != len(refs):
            raise ValueError("cross-plan local ID collision is not scoped")
        members = []
        for ref in sorted(refs):
            node = nodes_by_ref.get(ref)
            if node is None or node["localId"] != local_id:
                raise ValueError("cross-plan ID has no exact plan node")
            path = node["plan"]
            if path not in source_by_path:
                raise ValueError("cross-plan ID plan has no current Git source")
            members.append({
                "scopedNodeRef": ref,
                "planSourceIdentity": source_by_path[path],
            })
        ref = "source-problem:sha256:" + hashlib.sha256(json.dumps(
            ["CROSS_PLAN_SHORT_ID_AMBIGUITY", local_id],
            ensure_ascii=True, separators=(",", ":"),
        ).encode()).hexdigest()
        if ref in unique_ids:
            raise ValueError("cross-plan ID and source cell problem collide")
        unique_ids.add(ref)
        collisions.append({
            "problemRef": ref,
            "issue": "CROSS_PLAN_SHORT_ID_AMBIGUITY",
            "localId": local_id,
            "scopedPlanNodes": members,
            "bareIdConsumerStanding": "UNKNOWN",
            "semanticOverlapStanding": "UNKNOWN",
            "scopeDisambiguationStanding": "EXACT_PLAN_PATH_AVAILABLE",
            "invocationStanding": "NOT_MAPPED",
            "deleteOrRenameStanding": "NOT_QUALIFIED",
        })
    issue_counts = collections.Counter(p["issue"] for p in result)
    if dict(sorted(issue_counts.items())) != cells["summary"]["problemCounts"]:
        raise ValueError("problem LEGO projection lost or fabricated an issue")
    if len({p["problemRef"] for p in result}) != len(result):
        raise ValueError("problem LEGO identity collision")
    return {
        "kind": "ordivon.phase1.pending-problem-lego-frontier",
        "sourceCut": cells["sourceCut"],
        "sourceTree": cells["sourceTree"],
        "proposalCut": cells["proposalCut"],
        "truthBoundary": "exact Git source and plan declaration only; NO semantic, invoked, installed or mathematical proof",
        "proofReuseAdmissible": False,
        "decisionsDeferred": [
            "CONSUMER_AND_INVOCATION_GRAPH",
            "FORMAL_BEHAVIORAL_REFINEMENT",
            "REUSE_REPLACE_DELETE",
        ],
        "summary": {
            "trackedSourcePaths": cells["summary"]["trackedPaths"],
            "recursiveSourceCells": cells["summary"]["cells"],
            "problemBearingCells": cells["summary"]["problemCells"],
            "problemLegos": len(result),
            "problemCounts": dict(sorted(issue_counts.items())),
            "denseSourceAtomIncidences": sum(p["sourcePathCount"] for p in result
                                               if p["issue"] == "DENSE_CELL_REQUIRES_SUBCLASSIFICATION_REVIEW"),
            "unclassifiedSourceAtomIncidences": sum(p["sourcePathCount"] for p in result
                                               if p["issue"] == "UNCLASSIFIED_SOURCE_REGION"),
            "planGapNodes": sum(len(p["planNodeRefs"]) for p in result),
            "planGapAtomicObligations": sum(len(p["planProblemObligations"]) for p in result),
            "crossPlanShortIdProblems": len(collisions),
            "allPendingProblemInstances": len(result) + len(collisions),
        },
        "problemLegos": result,
        "shortIdAmbiguityProblems": collisions,
    }


def join_cross_plane_observations(problem_frontier: dict, observations: dict) -> dict:
    """Read-only relation hints across observed source/data/process planes.

    Inputs are externally observed snapshots, *not* authenticated attestations.
    This projects stable observation/problem identities but neither discovers
    nor authorizes invocations, deletes, deployments or runtime equivalence.
    """
    if observations.get("kind") != "ordivon.phase1.cross-plane-observation-input":
        raise ValueError("not a recognized bounded cross-plane observation input")
    if observations.get("schemaVersion") != 1:
        raise ValueError("unsupported cross-plane schema")
    if observations.get("subjectSourceCut") != problem_frontier["sourceCut"]:
        raise ValueError("cross-plane observation subject SourceCut mismatch")
    entries = observations.get("observations")
    links = observations.get("candidateRelations")
    if not isinstance(entries, list) or not isinstance(links, list):
        raise ValueError("cross-plane input must contain typed observation arrays")
    if len(entries) > 256 or len(links) > 512:
        raise ValueError("cross-plane bounded input limit exceeded")
    allowed = {"GIT_SOURCE_VIEW", "NON_GIT_NAMESPACE", "SERVICE_STATUS", "PROCESS_PID"}
    scopes = {"linux", "windows"}
    nodes: dict[str, dict] = {}
    result_problems = []
    digest = lambda x: hashlib.sha256(json.dumps(
        x, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    for item in entries:
        if not isinstance(item, dict) or set(item) - {
            "plane", "hostScope", "locator", "versionIdentity",
            "observedState", "pid", "gitObjectStoreGroup", "witnessRef",
            "serviceLocator",
        }:
            raise ValueError("cross-plane record has unsupported or sensitive fields")
        plane, host, locator = (item.get(k) for k in
                                ("plane", "hostScope", "locator"))
        if plane not in allowed or host not in scopes or not isinstance(locator, str):
            raise ValueError("cross-plane observation kind/host/locator invalid")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,159}", locator):
            raise ValueError("cross-plane locator must be an explicit scoped token")
        if item.get("witnessRef") is None or not isinstance(item["witnessRef"], str):
            raise ValueError("cross-plane observation needs read-only evidence ref")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,191}", item["witnessRef"]):
            raise ValueError("evidence references cannot contain shell/secret text")
        if plane == "GIT_SOURCE_VIEW":
            if host != "linux" or not re.fullmatch(
                r"[0-9a-f]{40}:[0-9a-f]{40}", str(item.get("versionIdentity", ""))
            ):
                raise ValueError("Git view needs exact commit and tree digests")
        elif item.get("versionIdentity") is not None:
            raise ValueError("non-Git observations cannot claim immutable Git identity")
        if plane == "NON_GIT_NAMESPACE" and item.get("observedState") not in (
            "DIRECTORY_OBSERVED", "MIXED_NESTED_GIT_OBSERVED"
        ):
            raise ValueError("non-Git namespace needs explicit observation class")
        if plane in ("SERVICE_STATUS", "PROCESS_PID"):
            if item.get("observedState") not in (
                "RUNNING", "STOPPED", "ACTIVE", "INACTIVE"
            ):
                raise ValueError("service or process state is not observed")
            if item.get("pid") is not None and (
                type(item["pid"]) is not int or not 0 <= item["pid"] <= 2**31-1
            ):
                raise ValueError("invalid observed pid")
            if plane == "PROCESS_PID" and (
                not item.get("pid") or
                not isinstance(item.get("serviceLocator"), str)
            ):
                raise ValueError("process observation must identify observed service")
        if item.get("gitObjectStoreGroup") is not None and (
            plane != "GIT_SOURCE_VIEW" or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,159}",
                str(item["gitObjectStoreGroup"])
            )
        ):
            raise ValueError("object-store grouping applies only to Git views")
        loc = f"{host}:{plane}:{locator}"
        if loc in nodes:
            raise ValueError("duplicate cross-plane observed identity")
        node_ref = "observation:sha256:" + digest([host, plane, locator])
        issue = {
            "GIT_SOURCE_VIEW": "EXTERNAL_GIT_SOURCE_CONSUMER_RELATION_UNKNOWN",
            "NON_GIT_NAMESPACE": "NON_GIT_CONTENT_IDENTITY_AND_RETENTION_UNKNOWN",
            "SERVICE_STATUS": "SERVICE_SOURCE_EFFECT_RELATION_UNKNOWN",
            "PROCESS_PID": "PROCESS_LOADED_IMPLEMENTATION_UNKNOWN",
        }[plane]
        problem_ref = "source-problem:sha256:" + digest(
            ["CROSS_PLANE", issue, node_ref]
        )
        node = {
            "observationRef": node_ref,
            "hostScope": host,
            "plane": plane,
            "locator": locator,
            "versionIdentity": item.get("versionIdentity"),
            "observedState": item.get("observedState"),
            "pid": item.get("pid"),
            "witnessRef": item["witnessRef"],
            "gitObjectStoreGroup": item.get("gitObjectStoreGroup"),
            "serviceLocator": item.get("serviceLocator"),
            "proofStanding": "OBSERVATION_INPUT_NOT_INDEPENDENTLY_ATTESTED",
            "semanticConsumerStanding": "UNKNOWN",
            "loadedImplementationStanding": "UNKNOWN",
        }
        nodes[loc] = node
        result_problems.append({
            "problemRef": problem_ref, "issue": issue,
            "observationRef": node_ref, "standing": "PENDING_INVESTIGATION",
            "consumerStanding": "UNKNOWN", "invocationStanding": "NOT_MAPPED",
            "formalStanding": "UNKNOWN", "deleteOrReplaceStanding": "NOT_QUALIFIED",
        })
    allowed_relations = {
        "SHARED_GIT_OBJECT_STORE_OBSERVED",
        "SERVICE_PID_ASSOCIATION_OBSERVED",
        "SOURCE_TEXT_EXTERNAL_PATH_REFERENCE_CANDIDATE",
    }
    edges = []
    seen_edges = set()
    for row in links:
        if not isinstance(row, dict) or set(row) != {
            "source", "target", "relationKind", "witnessRef"
        }:
            raise ValueError("cross-plane relation must have exact witness fields")
        a, b = nodes.get(row["source"]), nodes.get(row["target"])
        kind = row["relationKind"]
        if a is None or b is None or kind not in allowed_relations:
            raise ValueError("unknown node or asserted semantic relation")
        if not isinstance(row["witnessRef"], str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,191}", row["witnessRef"]
        ):
            raise ValueError("relation has no safe provenance ref")
        if kind == "SHARED_GIT_OBJECT_STORE_OBSERVED" and not (
            a["plane"] == b["plane"] == "GIT_SOURCE_VIEW" and
            a["gitObjectStoreGroup"] and
            a["gitObjectStoreGroup"] == b["gitObjectStoreGroup"] and a != b
        ):
            raise ValueError("object-store relation not grounded in common group")
        if kind == "SERVICE_PID_ASSOCIATION_OBSERVED" and not (
            a["plane"] == "SERVICE_STATUS" and b["plane"] == "PROCESS_PID" and
            a["hostScope"] == b["hostScope"] and a["pid"] and
            a["pid"] == b["pid"] and b["serviceLocator"] == a["locator"]
        ):
            raise ValueError("service-process association lacks observed identity")
        if kind == "SOURCE_TEXT_EXTERNAL_PATH_REFERENCE_CANDIDATE" and not (
            a["plane"] == "GIT_SOURCE_VIEW" and b["plane"] == "NON_GIT_NAMESPACE"
        ):
            raise ValueError("lexical path hint is not a source-to-data relation")
        edge = (a["observationRef"], b["observationRef"], kind)
        if edge in seen_edges:
            raise ValueError("duplicate candidate relation")
        seen_edges.add(edge)
        edges.append({
            "relationRef": "relation:sha256:" + digest(edge),
            "fromObservationRef": edge[0], "toObservationRef": edge[1],
            "relationKind": kind, "witnessRef": row["witnessRef"],
            "consumerAndCallSemantics": "UNKNOWN",
            "formalProofStanding": "UNKNOWN",
        })
    if set(p["problemRef"] for p in result_problems) & set(
        p["problemRef"] for p in problem_frontier["problemLegos"]
    ):
        raise ValueError("cross-plane and source problem identity collision")
    return {
        "kind": "ordivon.phase1.cross-plane-observed-problem-frontier",
        "sourceCut": problem_frontier["sourceCut"],
        "observationBatchDigest": "sha256:" + digest(observations),
        "truthBoundary": "operator-supplied bounded observations; no verified call/impact/delete authority",
        "proofReuseAdmissible": False,
        "problemSources": {
            "gitRecursive": problem_frontier["summary"]["problemLegos"],
            "shortIdAmbiguity": problem_frontier["summary"]["crossPlanShortIdProblems"],
            "crossPlaneObserved": len(result_problems),
        },
        "observationCount": len(nodes),
        "candidateRelationCount": len(edges),
        "observations": sorted(nodes.values(), key=lambda n:n["observationRef"]),
        "problems": sorted(result_problems, key=lambda p:p["problemRef"]),
        "candidateRelations": sorted(edges, key=lambda e:e["relationRef"]),
        "laterStagesNotExecuted": [
            "COMPLETE_DYNAMIC_CONSUMER_DISCOVERY",
            "INVOCATION_SEMANTICS",
            "IMPACT_GRAPH",
            "DELETE_REUSE_COMPOSE_REPAIR",
        ],
    }


def recursive_external_git_cells(
    problem_frontier: dict, crossplane_input: dict, root_specs: dict, *,
    max_files: int = 24, max_depth: int = 6,
) -> dict:
    """Recursively partition exact *other Git trees* without inventing LEGO semantics.

    External roots must match a contemporaneous bounded cross-plane observation.
    Git mode/blob identity proves exact source bytes, not consumers or installation.
    """
    if not 1 <= max_files <= 10000 or not 1 <= max_depth <= 12:
        raise ValueError("external recursive cell limits invalid")
    if (root_specs.get("kind") != "ordivon.phase1.external-git-root-locations"
        or root_specs.get("subjectSourceCut") != problem_frontier["sourceCut"]
        or crossplane_input.get("subjectSourceCut") != problem_frontier["sourceCut"]):
        raise ValueError("external roots and observations require exact common subject cut")
    input_roots = root_specs.get("roots")
    if not isinstance(input_roots, list) or len(input_roots) > 32:
        raise ValueError("external Git spec needs at most 32 roots")
    observed = {
        row["locator"]: row
        for row in crossplane_input.get("observations", ())
        if row.get("plane") == "GIT_SOURCE_VIEW" and row.get("hostScope") == "linux"
    }
    result = []
    total_paths = 0
    total_cells = 0
    all_problem_refs = set()
    for spec in input_roots:
        if not isinstance(spec, dict) or set(spec) != {"locator", "rootPath"}:
            raise ValueError("external Git locator needs exact source path and label")
        locator, raw_root = spec["locator"], spec["rootPath"]
        if locator not in observed or not isinstance(raw_root, str) or not raw_root.startswith("/"):
            raise ValueError("external Git source root has no observed source view")
        root = Path(raw_root)
        if not root.is_dir():
            raise ValueError("external Git source root not accessible")
        row = observed[locator]
        rev, tree_sha = row["versionIdentity"].split(":")
        exact_commit(root, rev)
        if git(root, "rev-parse", rev + "^{tree}").decode().strip() != tree_sha:
            raise ValueError("external Git tree mismatches observed immutable cut")
        atoms = tree(root, rev)
        if len(atoms) > 100000:
            raise ValueError("external Git tree exceeds bounded enumeration")
        member_refs = set()
        cells = []
        def emit(prefix: str, members: list[dict], depth: int) -> None:
            nonlocal total_cells
            if not members:
                raise ValueError("empty recursive Git cell")
            for a in members:
                if a["path"] in member_refs:
                    raise ValueError("external Git atom appears in multiple cells")
                member_refs.add(a["path"])
            prefix_id = prefix or "(repo-root)/"
            digest = hashlib.sha256(json.dumps(
                [(x["path"], x["sourceIdentity"]) for x in members],
                ensure_ascii=True, sort_keys=True, separators=(",", ":"),
            ).encode()).hexdigest()
            problem_ref = "source-problem:sha256:" + hashlib.sha256(
                json.dumps(["EXTERNAL_GIT_SOURCE_CELL_UNQUALIFIED", locator, prefix_id],
                           separators=(",", ":"), ensure_ascii=True).encode()
            ).hexdigest()
            if problem_ref in all_problem_refs:
                # A flat directory with direct files may produce at most one group.
                raise ValueError("duplicate stable external Git cell problem identity")
            all_problem_refs.add(problem_ref)
            direct_only = all("/" not in x["path"][len(prefix):] for x in members)
            density = (
                "FLAT_DIRECTORY_GIT_ATOMS" if len(members)>max_files and direct_only
                else "MAX_DEPTH_REACHED" if len(members)>max_files and depth>=max_depth
                else "WITHIN_DIRECTORY_CAP"
            )
            cells.append({
                "problemRef": problem_ref,
                "rootLocator": locator,
                "physicalPrefix": prefix_id,
                "depth": depth,
                "sourcePathCount": len(members),
                "firstSourcePath": members[0]["path"],
                "lastSourcePath": members[-1]["path"],
                "memberGitObjectDigest": "sha256:"+digest,
                "sourceAtoms": [{"path":a["path"],"sourceIdentity":a["sourceIdentity"]}
                                for a in members],
                "densityStanding": density,
                "issue": "EXTERNAL_GIT_SOURCE_CELL_UNQUALIFIED",
                "semanticConsumer": "UNKNOWN",
                "invocationStanding": "NOT_MAPPED",
                "proofStanding": "UNKNOWN",
                "installedStanding": "UNKNOWN",
                "deleteOrReplaceStanding": "NOT_QUALIFIED",
            })
            total_cells += 1

        def walk(prefix: str, members: list[dict], depth: int) -> None:
            direct = []
            children = collections.defaultdict(list)
            for a in members:
                if not a["path"].startswith(prefix):
                    raise ValueError("external Git recursive prefix mismatch")
                suffix = a["path"][len(prefix):]
                if "/" not in suffix:
                    direct.append(a)
                else:
                    child = suffix.split("/", 1)[0]
                    children[prefix+child+"/"].append(a)
            if len(members)<=max_files or not children or depth>=max_depth:
                emit(prefix,members,depth)
                return
            if direct:
                emit(prefix,direct,depth)
            for child,group in sorted(children.items()):
                walk(child,group,depth+1)

        walk("",atoms,0) if atoms else None
        if len(member_refs)!=len(atoms) or set(member_refs)!={a["path"] for a in atoms}:
            raise ValueError("external Git recursive cells not complete")
        cells.sort(key=lambda x: (x["physicalPrefix"],x["firstSourcePath"]))
        result.append({
            "rootLocator": locator,
            "sourceCut": rev,
            "sourceTree": tree_sha,
            "observationWitnessRef": row["witnessRef"],
            "trackedPathCount":len(atoms),
            "recursiveCellCount":len(cells),
            "denseCellCount":sum(x["densityStanding"]!="WITHIN_DIRECTORY_CAP" for x in cells),
            "atomCompletenessStanding":"EXACT_IMMUTABLE_GIT_TREE_PATH_COVERAGE",
            "callSemanticStanding":"UNKNOWN",
            "cells":cells,
        })
        total_paths+=len(atoms)
    if len({x["rootLocator"] for x in result}) != len(result):
        raise ValueError("duplicate external Git root locator")
    return {
        "kind":"ordivon.phase1.external-git-recursive-source-problem-frontier",
        "subjectSourceCut":problem_frontier["sourceCut"],
        "rootCount":len(result),
        "sourcePathIncidences":total_paths,
        "sourceCellProblems":total_cells,
        "pathsMayRepeatAcrossWorktrees":True,
        "proofReuseAdmissible":False,
        "truthBoundary":"per-root exact Git tree only; duplicate Worktree versions, consumer and installation UNKNOWN",
        "roots":result,
    }


def recursive_non_git_metadata_cells(
    problem_frontier: dict, crossplane_input: dict, root_specs: dict, *,
    max_files: int = 24, max_depth: int = 6,
) -> dict:
    """Bounded non-Git directory metadata partition, NOT a content hash or FS snapshot.

    Stops at *nested Git roots* to avoid treating a separately inventoried Git
    worktree as ordinary non-Git data. Never follows symlinks or reads contents.
    """
    import os
    import stat
    if not 1 <= max_files <= 10000 or not 1 <= max_depth <= 12:
        raise ValueError("non-Git recursive cell limits invalid")
    if (root_specs.get("kind") != "ordivon.phase1.non-git-root-locations"
        or root_specs.get("subjectSourceCut") != problem_frontier["sourceCut"]
        or crossplane_input.get("subjectSourceCut") != problem_frontier["sourceCut"]):
        raise ValueError("non-Git roots and observations need common SourceCut")
    specs = root_specs.get("roots")
    if not isinstance(specs,list) or len(specs) > 32:
        raise ValueError("non-Git enumeration needs no more than 32 specified roots")
    observed = {r["locator"]:r for r in crossplane_input.get("observations",())
                if r.get("plane")=="NON_GIT_NAMESPACE" and r.get("hostScope")=="linux"}
    roots = []
    used = set()
    total_files = 0
    total_cells = 0
    total_nested = 0
    for spec in specs:
        if not isinstance(spec,dict) or set(spec)!={"locator","rootPath"}:
            raise ValueError("non-Git root needs exact locator and path")
        loc,raw = spec["locator"],spec["rootPath"]
        if loc not in observed or loc in used or not isinstance(raw,str) or not raw.startswith("/"):
            raise ValueError("non-Git root lacks unique observed locator")
        used.add(loc)
        root=Path(raw)
        if not root.is_dir() or root.is_symlink():
            raise ValueError("non-Git root inaccessible or symlink")
        atoms=[]
        excluded=[]
        scandir_errors=[]
        def on_error(error):
            scandir_errors.append(type(error).__name__)
        for current,dirs,files in os.walk(root,topdown=True,followlinks=False,onerror=on_error):
            base=Path(current)
            if ".git" in dirs:
                # The parent can itself be an independently versioned Git root.
                if base != root:
                    excluded.append(base.relative_to(root).as_posix())
                    dirs[:]=[]
                    continue
                dirs.remove(".git")
            for entry in sorted(dirs[:]):
                full=base/entry
                if full.is_symlink():
                    dirs.remove(entry)
                    # A symlink itself is a path atom; never follow its target.
                    files.append(entry)
            for name in sorted(files):
                full=base/name
                try:
                    meta=full.lstat()
                except OSError as e:
                    scandir_errors.append(type(e).__name__)
                    continue
                rel=full.relative_to(root).as_posix()
                if rel.startswith("../") or rel.startswith("/"):
                    raise ValueError("non-Git cell path escaped root")
                form=("REGULAR_FILE" if stat.S_ISREG(meta.st_mode)
                      else "SYMLINK_NOT_FOLLOWED" if stat.S_ISLNK(meta.st_mode)
                      else "SPECIAL_ENTRY_UNREAD")
                atoms.append({
                    "path":rel,
                    "mode":stat.S_IMODE(meta.st_mode),
                    "byteSizeObserved":meta.st_size,
                    "mtimeNsObserved":meta.st_mtime_ns,
                    "form":form,
                })
                if len(atoms)>100000:
                    raise ValueError("non-Git root larger than bounded path enumeration")
        if scandir_errors:
            # Do not mark unreadable/racing trees as fully inventoried.
            raise ValueError("non-Git scan incomplete due to filesystem errors")
        atoms.sort(key=lambda x:x["path"])
        if len({x["path"] for x in atoms})!=len(atoms):
            raise ValueError("non-Git path enumerated twice")
        cells=[]
        emitted=set()
        def emit(prefix,members,depth):
            if not members:
                raise ValueError("empty non-Git cell")
            for item in members:
                if item["path"] in emitted:
                    raise ValueError("non-Git file included twice")
                emitted.add(item["path"])
            pref=prefix or "(repo-root)/"
            witness=hashlib.sha256(json.dumps(members,sort_keys=True,ensure_ascii=True,
                                              separators=(",",":")).encode()).hexdigest()
            idref="source-problem:sha256:"+hashlib.sha256(json.dumps(
                ["NON_GIT_CONTENT_IDENTITY_UNOBSERVED",loc,pref],separators=(",",":"),
                ensure_ascii=True).encode()).hexdigest()
            direct=all("/" not in x["path"][len(prefix):] for x in members)
            dense=(len(members)>max_files)
            cells.append({
                "problemRef":idref,
                "rootLocator":loc,
                "physicalPrefix":pref,
                "depth":depth,
                "fileCount":len(members),
                "metadataDigest":"sha256:"+witness,
                "firstRelativePath":members[0]["path"],
                "lastRelativePath":members[-1]["path"],
                "observedAtoms":members,
                "densityStanding":(
                    "FLAT_DIRECTORY_PATHS" if dense and direct
                    else "MAX_DEPTH_REACHED" if dense and depth>=max_depth
                    else "WITHIN_PATH_CAP"),
                "issue":"NON_GIT_CONTENT_IDENTITY_UNOBSERVED",
                "contentHashStanding":"NOT_OBSERVED",
                "consumerStanding":"UNKNOWN",
                "invocationStanding":"NOT_MAPPED",
                "installedStanding":"UNKNOWN",
                "proofStanding":"UNKNOWN",
                "deleteOrReplaceStanding":"NOT_QUALIFIED",
            })
        def walk(prefix,members,depth):
            direct=[]
            children=collections.defaultdict(list)
            for item in members:
                if not item["path"].startswith(prefix):
                    raise ValueError("non-Git cell prefix is invalid")
                suffix=item["path"][len(prefix):]
                if "/" not in suffix:
                    direct.append(item)
                else:
                    children[prefix+suffix.split("/",1)[0]+"/"].append(item)
            if len(members)<=max_files or not children or depth>=max_depth:
                emit(prefix,members,depth)
                return
            if direct:
                emit(prefix,direct,depth)
            for child,subset in sorted(children.items()):
                walk(child,subset,depth+1)
        if atoms:
            walk("",atoms,0)
        if emitted!={x["path"] for x in atoms}:
            raise ValueError("non-Git metadata cell enumeration lost files")
        cells.sort(key=lambda x:(x["physicalPrefix"],x["firstRelativePath"]))
        nested_git = []
        for nested in sorted(set(excluded)):
            # A .git marker alone does NOT entail a valid immutable SourceCut.
            # Never silently count an unborn repository as a Git source view.
            target = root / nested
            cmd = subprocess.run(
                ["git", "--no-replace-objects", "-C", str(target),
                 "rev-parse", "--verify", "HEAD^{commit}"],
                capture_output=True, text=True, timeout=10,
            )
            cut = cmd.stdout.strip()
            valid = cmd.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", cut)
            nested_git.append({
                "nestedRelativeRoot": nested,
                "sourceStanding": ("GIT_COMMIT_PRESENT_SEPARATE_VIEW"
                                    if valid else "GIT_MARKER_WITH_NO_VERIFIED_HEAD"),
                "issue": ("SEPARATE_GIT_SOURCE_VIEW_NOT_PART_OF_NON_GIT"
                          if valid else "NESTED_GIT_ROOT_SOURCECUT_UNQUALIFIED"),
                "exactGitCut": cut if valid else None,
                "consumerStanding": "UNKNOWN",
                "deleteOrReplaceStanding": "NOT_QUALIFIED",
            })
        roots.append({
            "rootLocator":loc,
            "observationWitnessRef":observed[loc]["witnessRef"],
            "enumeratedPathCount":len(atoms),
            "recursiveCellCount":len(cells),
            "nestedGitRootExclusions":sorted(set(excluded)),
            "nestedGitRootQualifications":nested_git,
            "unqualifiedNestedGitHeads":sum(
                x["exactGitCut"] is None for x in nested_git),
            "metadataOnlyStanding":"NON_ATOMIC_FILESYSTEM_STAT_OBSERVATIONS",
            "contentDigestStanding":"NOT_OBSERVED",
            "sourceToConsumerStanding":"UNKNOWN",
            "cells":cells,
        })
        total_files+=len(atoms)
        total_cells+=len(cells)
        total_nested+=len(set(excluded))
    return {
        "kind":"ordivon.phase1.non-git-recursive-metadata-problem-frontier",
        "subjectSourceCut":problem_frontier["sourceCut"],
        "rootCount":len(roots),
        "enumeratedPathIncidences":total_files,
        "recursiveCellProblems":total_cells,
        "nestedGitRootsExcluded":total_nested,
        "nestedGitRootsWithoutSourceCut":sum(
            x["unqualifiedNestedGitHeads"] for x in roots),
        "metadataIsContentHash":False,
        "filesystemSnapshotAtomicity":"UNKNOWN",
        "semanticCallOrImpactProof":"UNKNOWN",
        "proofReuseAdmissible":False,
        "roots":sorted(roots,key=lambda x:x["rootLocator"]),
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cut", required=True)
    parser.add_argument("--proposal-cut")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--only-problems", action="store_true")
    parser.add_argument("--reference-path", action="append", default=[],
                        help="cross-format Git textual reference witness for exact file path")
    parser.add_argument("--reference-limit", type=int, default=48,
                        help="maximum witness lines per source path, 1..256")
    parser.add_argument("--static-python-consumers", action="store_true",
                        help="exact Git AST import candidate references; not live consumers")
    parser.add_argument("--imports-prefix",
                        help="show AST import hints touching this canonical source prefix")
    parser.add_argument("--non-git-roots", type=Path,
                        help="read-only recursive non-Git path metadata; never hashes file contents")
    parser.add_argument("--external-git-roots", type=Path,
                        help="read-only recursive exact Git views explicitly matched to observed source roots")
    parser.add_argument("--cross-plane-observations", type=Path,
                        help="join explicitly supplied observation evidence WITHOUT attesting it")
    parser.add_argument("--problem-legos", action="store_true",
                        help="derive exact-Git pending problems from recursive source cells; NO invocation or fixes")
    parser.add_argument("--live-cells", action="store_true",
                        help="derive fresh exact-Git recursive source cells; never load saved snapshots")
    parser.add_argument("--use-proposal-cells", action="store_true",
                        help="show proposal-source regions without treating them as current authority")
    parser.add_argument("--cell-max-files", type=int, default=24)
    parser.add_argument("--cell-max-depth", type=int, default=6)
    parser.add_argument("--lookup-path", action="append", default=[],
                        help="small exact-Git source/path query; repeat for multiple files")
    args = parser.parse_args()
    if args.non_git_roots and not (args.cross_plane_observations and args.problem_legos):
        parser.error("--non-git-roots requires problem-legos and cross-plane observations")
    if args.non_git_roots and args.use_proposal_cells:
        parser.error("non-Git data cannot be projected into proposed source policy")
    if args.external_git_roots and not (args.cross_plane_observations and args.problem_legos):
        parser.error("--external-git-roots requires both --problem-legos and --cross-plane-observations")
    if args.external_git_roots and args.use_proposal_cells:
        parser.error("external Git views cannot use proposed source ownership")
    if args.cross_plane_observations and not args.problem_legos:
        parser.error("--cross-plane-observations requires --problem-legos")
    if args.cross_plane_observations and args.use_proposal_cells:
        parser.error("cross-plane evidence cannot be attached to proposed source authority")
    if args.cross_plane_observations and (
        args.lookup_path or args.reference_path or args.static_python_consumers or
        args.live_cells
    ):
        parser.error("cross-plane observation join is exclusive to pending problem projection")
    if args.reference_path:
        if (args.lookup_path or args.static_python_consumers or args.live_cells
                or args.proposal_cut or args.use_proposal_cells or args.only_problems or args.problem_legos
                or args.imports_prefix or args.summary):
            parser.error("reference witness mode is mutually exclusive with projection modes")
        result = exact_git_reference_hints(
            args.repo, args.source_cut, args.reference_path,
            per_path_limit=args.reference_limit)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args.reference_limit != 48:
        parser.error("reference-limit requires reference-path")
    if args.imports_prefix and not args.static_python_consumers:
        parser.error("imports-prefix requires static-python-consumers")
    if args.lookup_path and args.static_python_consumers:
        parser.error("exact source-cell path lookup and static consumer scan are separate modes")
    if args.lookup_path and (args.live_cells or args.problem_legos or args.only_problems or args.summary
                            or args.use_proposal_cells):
        parser.error("--lookup-path is a distinct small-result mode")
    if args.static_python_consumers:
        if args.proposal_cut or args.live_cells or args.problem_legos or args.only_problems:
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
    if args.lookup_path:
        result = lookup_source_paths(
            result, repo=args.repo, paths=args.lookup_path,
            max_files=args.cell_max_files, max_depth=args.cell_max_depth,
        )
    elif args.problem_legos:
        result = derive_problem_legos(
            result, repo=args.repo, max_files=args.cell_max_files,
            max_depth=args.cell_max_depth, use_proposal=args.use_proposal_cells,
        )
        if args.only_problems:
            result["displaySelection"] = "ALL_DISCOVERED_PROBLEMS_ONLY"
        if args.cross_plane_observations:
            parsed = json.loads(args.cross_plane_observations.read_text())
            result["crossPlane"] = join_cross_plane_observations(result, parsed)
            if args.external_git_roots:
                results = recursive_external_git_cells(
                    result, parsed, json.loads(args.external_git_roots.read_text()),
                    max_files=args.cell_max_files,max_depth=args.cell_max_depth,
                )
                result["externalGit"] = results
                if args.summary:
                    for row in result["externalGit"]["roots"]:
                        row.pop("cells")
            if args.non_git_roots:
                non_git = recursive_non_git_metadata_cells(
                    result, parsed, json.loads(args.non_git_roots.read_text()),
                    max_files=args.cell_max_files, max_depth=args.cell_max_depth,
                )
                result["nonGit"] = non_git
                if args.summary:
                    for root in non_git["roots"]:
                        root.pop("cells")
            if args.summary:
                for field in ("observations", "problems", "candidateRelations"):
                    result["crossPlane"].pop(field)
        if args.summary:
            result.pop("problemLegos")
            result.pop("shortIdAmbiguityProblems")
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
