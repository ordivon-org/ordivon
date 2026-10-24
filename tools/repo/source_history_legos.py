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
from tempfile import TemporaryDirectory

if __package__:
    from .affected_owners import load_owners
else:
    from affected_owners import load_owners

HEADER = "__ORDIVON_HISTORY_RECORD__"


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
        errors="surrogateescape",
        stderr=subprocess.PIPE,
    )


def owners(repo: Path, canonical_revision: str) -> list[tuple[str, str]]:
    # Natural-owner attribution is part of the exact protected-source cut,
    # not a mutable worktree checkout (which may be on another Git branch).
    exact_manifest = git(repo, "show", canonical_revision + ":tools/repo/owners.toml")
    # Reuse the canonical Owner type checker on source-cut bytes; malformed
    # historical roots must not silently misattribute consumer paths.
    with TemporaryDirectory(prefix="ordivon-source-owners-") as temp:
        manifest = Path(temp) / "owners.toml"
        manifest.write_text(exact_manifest, encoding="utf-8", errors="surrogateescape")
        native = [(owner.root, owner.name) for owner in load_owners(manifest)]
    # Repo mechanics is a separate existing owner, never effect authority.
    return native + [("tools/repo/", "tools/repo")]


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
            result[name.decode("utf-8", errors="surrogateescape")] = (
                mode + ":" + kind + ":" + oid
            )
    return result



def history(repo: Path, left: str, right: str) -> dict:
    left_oid = git(repo, "rev-parse", "--verify", left + "^{commit}").strip()
    right_oid = git(repo, "rev-parse", "--verify", right + "^{commit}").strip()
    bases = git(repo, "merge-base", "--all", left_oid, right_oid).splitlines()
    if len(bases) != 1:
        raise ValueError(
            f"ambiguous merge bases: expected one best common ancestor, got {len(bases)}"
        )
    base = bases[0]

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

    # Git pathnames are NUL-delimited byte strings, not lines. Leading NUL
    # records and an explicit NUL after each header produce a structural
    # boundary that a valid Git filename cannot counterfeit (filenames cannot
    # contain NUL); paths may contain newlines or look exactly like HEADER.
    raw_paths = subprocess.check_output(
        [
            "git",
            "-C",
            str(repo),
            "log",
            "-z",
            "--left-right",
            "--cherry-mark",
            "--no-merges",
            "--no-renames",
            "--format=%x00" + HEADER + "%m %H%x00",
            "--name-only",
            spec,
        ],
        stderr=subprocess.PIPE,
    )
    if raw_paths and (
        not raw_paths.startswith(b"\x00") or not raw_paths.endswith(b"\x00")
    ):
        raise ValueError("malformed NUL-delimited Git history")
    fields = raw_paths.split(b"\x00") if raw_paths else []
    pos = 0
    while pos < len(fields) - 1:
        if fields[pos] != b"" or pos + 2 >= len(fields):
            raise ValueError("malformed Git commit record boundary")
        header = fields[pos + 1].decode("ascii")
        if not header.startswith(HEADER) or fields[pos + 2] != b"":
            raise ValueError("missing Git commit record delimiter")
        marker, oid = header[len(HEADER) :].split()
        if oid not in all_commits or all_commits[oid]["kind"] != "patch":
            raise ValueError("invalid patch marker reference")
        record = all_commits[oid]
        if marker == "=":
            record["patchRelation"] = "PATCH_ID_EQUIVALENT"
        elif (
            marker == "<"
            and record["side"] == "local"
            or marker == ">"
            and record["side"] == "remote"
        ):
            record["patchRelation"] = "PATCH_DISTINCT_UNQUALIFIED"
        else:
            raise ValueError("unexpected cherry mark")
        pos += 3
        first_path = True
        while pos < len(fields) and fields[pos] != b"":
            path = fields[pos]
            # Git inserts one LF between the header and the first name.
            # Remove *only* that separator; a genuine leading LF survives.
            if first_path:
                if not path.startswith(b"\n"):
                    raise ValueError("missing Git path separator")
                path = path[1:]
                first_path = False
            if not path:
                raise ValueError("empty Git path")
            record["changedPaths"].append(
                path.decode("utf-8", errors="surrogateescape")
            )
            pos += 1

    # A merge is not a single patch, but it still changes the checked-out
    # source tree. Project its exact first-parent path transition so downstream
    # owner/consumer qualification never silently drops merge-only effects.
    # Do not treat this diff as patch-ID or behavioral equivalence evidence.
    for record in all_commits.values():
        if record["kind"] != "merge-provenance":
            continue
        raw_merge_paths = subprocess.check_output(
            [
                "git",
                "-C",
                str(repo),
                "diff-tree",
                "-r",
                "--name-only",
                "--no-renames",
                "-z",
                record["parents"][0],
                record["commit"],
            ],
            stderr=subprocess.PIPE,
        )
        record["changedPaths"] = sorted(
            {
                path.decode("utf-8", errors="surrogateescape")
                for path in raw_merge_paths.split(b"\x00")
                if path
            }
        )
        # A first-parent delta can merely import behavior from another parent.
        # Only paths whose resulting mode/blob differs from *every* parent
        # are possible merge-specific additions; owner CDC still decides.
        distinct_from_all = set(record["changedPaths"])
        for parent in record["parents"][1:]:
            against_parent = subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(repo),
                    "diff-tree",
                    "-r",
                    "--name-only",
                    "--no-renames",
                    "-z",
                    parent,
                    record["commit"],
                ],
                stderr=subprocess.PIPE,
            )
            distinct_from_all.intersection_update(
                path.decode("utf-8", errors="surrogateescape")
                for path in against_parent.split(b"\x00")
                if path
            )
        record["resultDistinctFromAllParentsPaths"] = sorted(distinct_from_all)

    missing = [
        r["commit"]
        for r in all_commits.values()
        if r["patchRelation"] == "UNCLASSIFIED"
    ]
    if missing:
        raise ValueError("missing exact patch classification: " + ",".join(missing[:5]))

    mappings = owners(repo, right_oid)
    left_tree, right_tree = current_tree(repo, left_oid), current_tree(repo, right_oid)

    # Identity is the *exact* Git Blob plus file mode, not a guessed rename.
    # Preserve duplicates as ambiguous: identical content could belong to
    # unrelated consumers, and relocating source does not relocate its callers.
    def unique_blob_paths(tree: dict[str, str]) -> dict[str, str]:
        paths: dict[str, list[str]] = collections.defaultdict(list)
        for path, identity in tree.items():
            if ":blob:" in identity:
                paths[identity].append(path)
        return {
            identity: entries[0] for identity, entries in paths.items()
            if len(entries) == 1
        }

    unique_left = unique_blob_paths(left_tree)
    unique_right = unique_blob_paths(right_tree)
    counts: collections.Counter[str] = collections.Counter()
    owner_counts: collections.Counter[str] = collections.Counter()
    for record in all_commits.values():
        counts[record["side"] + ":" + record["patchRelation"]] += 1
        paths = record["changedPaths"]
        # An unmatched historical path is a missing owner binding, not
        # authority assigned to the repository root. Keep that distinction
        # while projecting its exact presence at both immutable Git tips.
        path_owners = {
            path: next(
                (owner for root, owner in mappings if path.startswith(root)),
                "ROOT_UNOWNED",
            )
            for path in paths
        }
        record["owners"] = sorted(set(path_owners.values()))
        unmapped_presence: collections.Counter[str] = collections.Counter()
        for path, owner in path_owners.items():
            if owner != "ROOT_UNOWNED":
                continue
            in_local, in_remote = path in left_tree, path in right_tree
            if in_local and in_remote:
                label = "BOTH_PRESENT"
            elif in_local:
                label = "LOCAL_ONLY"
            elif in_remote:
                label = "REMOTE_ONLY"
            else:
                label = "BOTH_ABSENT"
            unmapped_presence[label] += 1
        record["unmappedPathTipPresence"] = dict(unmapped_presence)
        for owner in record["owners"]:
            owner_counts[record["side"] + ":" + owner] += 1
        opposite = right_tree if record["side"] == "local" else left_tree
        own = left_tree if record["side"] == "local" else right_tree
        unique_own = unique_left if record["side"] == "local" else unique_right
        unique_opposite = unique_right if record["side"] == "local" else unique_left
        states = collections.Counter()
        exact_cross_paths = []
        for path in paths:
            own_blob, opposite_blob = own.get(path), opposite.get(path)
            if own_blob is None and opposite_blob is None:
                states["BOTH_TIPS_ABSENT"] += 1
            elif own_blob is not None and own_blob == opposite_blob:
                states["SAME_BLOB_AND_MODE"] += 1
            elif (
                opposite_blob is None
                and own_blob is not None
                and unique_own.get(own_blob) == path
                and (other_path := unique_opposite.get(own_blob)) is not None
                and other_path != path
            ):
                # Proves byte/mode identity across *unique final-tree paths*.
                # Does not prove historical move intent or consumer equivalence.
                states["CROSS_PATH_EXACT_BLOB_AND_MODE"] += 1
                exact_cross_paths.append(
                    {"sourcePath": path, "oppositePath": other_path}
                )
            elif opposite_blob is None:
                states["OPPOSITE_TIP_ABSENT"] += 1
            else:
                states["DIFFERENT_OR_OWN_TIP_ABSENT"] += 1
        record["pathRelations"] = dict(states)
        record["exactCrossPathMatches"] = exact_cross_paths
        record["consumerQualification"] = "UNKNOWN_REQUIRES_OWNER_CDC"

    actual = collections.Counter(r["side"] for r in all_commits.values())
    expected_left, expected_right = [
        int(n) for n in git(repo, "rev-list", "--left-right", "--count", spec).split()
    ]
    if actual["local"] != expected_left or actual["remote"] != expected_right:
        raise ValueError("DAG coverage mismatch")
    return {
        "kind": "ordivon.source-history-lego-projection",
        "truthRole": "derived-readonly-no-retirement-authority",
        "sourceCut": {"local": left_oid, "remote": right_oid, "commonAncestor": base},
        "counts": {"local": expected_left, "remote": expected_right},
        "ownerMappingSourceCut": right_oid,
        # Presence is defined by the source-bound Owner manifest, not by
        # whether a responsibility happens to have commits in this DAG.
        "ownerUniverse": sorted({name for _, name in mappings} | {"ROOT_UNOWNED"}),
        "patchClasses": dict(counts),
        "ownerMembership": dict(owner_counts),
        "warning": "Patch IDs, equal blobs and unique cross-path byte/mode matches do not prove consumer behavior, rename intent or safe retirement.",
        "commits": list(all_commits.values()),
    }


def owner_slice(projection: dict, owner: str) -> dict:
    """Project one current Owner without inventing retirement authority.

    Owner membership overlaps for commits touching several Owners. Therefore
    a collection of Owner views is a cover, not a disjoint Git partition.
    """
    records = projection["commits"]
    declared = projection["ownerUniverse"]
    if not isinstance(declared, list) or not all(
        isinstance(name, str) for name in declared
    ) or declared != sorted(set(declared)):
        raise ValueError("invalid source-bound Owner universe")
    if owner not in declared:
        raise ValueError(f"unknown Owner in source history: {owner!r}")
    if any(name not in declared for item in records for name in item["owners"]):
        raise ValueError("unbound historical Owner membership")
    global_counts = collections.Counter(item["side"] for item in records)
    if {side: global_counts[side] for side in ("local", "remote")} != projection["counts"]:
        raise ValueError("source-history global DAG coverage mismatch")

    picked = [item for item in records if owner in item["owners"]]
    counts = collections.Counter(item["side"] for item in picked)
    per_side = {side: counts[side] for side in ("local", "remote")}
    for side, count in per_side.items():
        expected = projection["ownerMembership"].get(side + ":" + owner, 0)
        if count != expected:
            raise ValueError("source-history Owner membership mismatch")

    return {
        "kind": "ordivon.source-history-lego-owner-view",
        "truthRole": projection["truthRole"],
        "sourceCut": projection["sourceCut"],
        "ownerMappingSourceCut": projection["ownerMappingSourceCut"],
        "owner": owner,
        "counts": per_side,
        "unfilteredCounts": projection["counts"],
        "warning": projection["warning"]
        + " Owner views overlap; they are not a disjoint partition.",
        "commits": picked,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--left", default="main")
    parser.add_argument("--right", default="origin/main")
    parser.add_argument("--owner", help="Restrict output to one natural Owner")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = history(args.repo.resolve(), args.left, args.right)
    if args.owner:
        report = owner_slice(report, args.owner)
    payload = json.dumps(report, ensure_ascii=True, separators=(",", ":")) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
