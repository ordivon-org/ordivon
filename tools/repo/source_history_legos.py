#!/usr/bin/env python3
"""Read-only two-cut Git history LEGO projection. Never grants merge/delete authority.

Keep the Git DAG, exact native stable patch equivalence, owner mapping and
opposite-tip file relation separate. Path/blobs are NOT consumer equivalence.
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
from pathlib import Path

import tomllib

HEADER = "__ORDIVON_HISTORY_RECORD__"


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
        errors="surrogateescape",
        stderr=subprocess.PIPE,
    )


def owners(repo: Path) -> list[tuple[str, str]]:
    with (repo / "tools/repo/owners.toml").open("rb") as stream:
        manifest = tomllib.load(stream)
    return [(item["root"], item["name"]) for item in manifest["owners"]]


def current_tree(repo: Path, revision: str) -> dict[str, str]:
    raw = subprocess.check_output(
        ["git", "-C", str(repo), "ls-tree", "-rz", "--full-tree", revision]
    )
    result = {}
    for entry in raw.split(b"\x00"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        if kind in ("blob", "commit"):
            result[name.decode("utf-8", errors="surrogateescape")] = mode + ":" + kind + ":" + oid
    return result


def history(repo: Path, left: str, right: str) -> dict:
    left_oid = git(repo, "rev-parse", "--verify", left + "^{commit}").strip()
    right_oid = git(repo, "rev-parse", "--verify", right + "^{commit}").strip()
    base = git(repo, "merge-base", left_oid, right_oid).strip()
    if not base:
        raise ValueError("source cuts have no common ancestor")

    spec = left_oid + "..." + right_oid
    # The full DAG includes merge connectors, which have no single patch ID.
    all_commits: dict[str, dict] = {}
    raw = git(repo, "log", "--left-right", "--format=%m %H %P", spec)
    for line in raw.splitlines():
        mark, oid, *parents = line.split()
        if mark not in ("<", ">"):
            raise ValueError("unexpected Git side marker")
        all_commits[oid] = {
            "commit": oid,
            "side": "local" if mark == "<" else "remote",
            "kind": "merge-provenance" if len(parents) > 1 else "patch",
            "parents": parents,
            "patchRelation": "NOT_APPLICABLE" if len(parents) > 1 else "UNCLASSIFIED",
            "changedPaths": [],
        }

    lines = git(
        repo, "log", "--left-right", "--cherry-mark", "--no-merges",
        "--no-renames", "--format=" + HEADER + "%m %H", "--name-only", spec,
    )
    current: dict | None = None
    for line in lines.splitlines():
        if line.startswith(HEADER):
            marker, oid = line[len(HEADER):].split()
            if oid not in all_commits or all_commits[oid]["kind"] != "patch":
                raise ValueError("invalid patch marker reference")
            record = all_commits[oid]
            if marker == "=":
                record["patchRelation"] = "PATCH_ID_EQUIVALENT"
            elif (
                marker == "<" and record["side"] == "local"
                or marker == ">" and record["side"] == "remote"
            ):
                record["patchRelation"] = "PATCH_DISTINCT_UNQUALIFIED"
            else:
                raise ValueError("unexpected cherry mark")
            current = record
        elif line and current is not None:
            current["changedPaths"].append(line)

    missing = [r["commit"] for r in all_commits.values() if r["patchRelation"] == "UNCLASSIFIED"]
    if missing:
        raise ValueError("missing exact patch classification: " + ",".join(missing[:5]))

    mappings = owners(repo)
    left_tree, right_tree = current_tree(repo, left_oid), current_tree(repo, right_oid)
    counts: collections.Counter[str] = collections.Counter()
    owner_counts: collections.Counter[str] = collections.Counter()
    for record in all_commits.values():
        counts[record["side"] + ":" + record["patchRelation"]] += 1
        paths = record["changedPaths"]
        record["owners"] = sorted({
            next((owner for root, owner in mappings if path.startswith(root)), "ROOT_UNOWNED")
            for path in paths
        })
        for owner in record["owners"]:
            owner_counts[record["side"] + ":" + owner] += 1
        opposite = right_tree if record["side"] == "local" else left_tree
        own = left_tree if record["side"] == "local" else right_tree
        states = collections.Counter()
        for path in paths:
            own_blob, opposite_blob = own.get(path), opposite.get(path)
            if own_blob is None and opposite_blob is None:
                states["BOTH_TIPS_ABSENT"] += 1
            elif own_blob is not None and own_blob == opposite_blob:
                states["SAME_BLOB_AND_MODE"] += 1
            elif opposite_blob is None:
                states["OPPOSITE_TIP_ABSENT"] += 1
            else:
                states["DIFFERENT_OR_OWN_TIP_ABSENT"] += 1
        record["pathRelations"] = dict(states)
        record["consumerQualification"] = "UNKNOWN_REQUIRES_OWNER_CDC"

    actual = collections.Counter(r["side"] for r in all_commits.values())
    expected_left, expected_right = [
        int(n) for n in git(repo, "rev-list", "--left-right", "--count", spec).split()
    ]
    if actual != {"local": expected_left, "remote": expected_right}:
        raise ValueError("DAG coverage mismatch")
    return {
        "kind": "ordivon.source-history-lego-projection",
        "truthRole": "derived-readonly-no-retirement-authority",
        "sourceCut": {"local": left_oid, "remote": right_oid, "commonAncestor": base},
        "counts": {"local": expected_left, "remote": expected_right},
        "patchClasses": dict(counts),
        "ownerMembership": dict(owner_counts),
        "warning": "Patch equivalence and tip blob equality do not prove consumer behavior or safe retirement.",
        "commits": list(all_commits.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--left", default="main")
    parser.add_argument("--right", default="origin/main")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = history(args.repo.resolve(), args.left, args.right)
    payload = json.dumps(report, ensure_ascii=True, separators=(",", ":")) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
