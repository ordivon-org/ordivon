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



def source_membership_query(
    repo: Path, source_cut: str, prefix: str, *, max_members: int = 10000
) -> dict:
    """Exact Git subtree membership and mode/blob fingerprint, never proof reuse.

    In particular, additions/absence are queries about the *set of paths*.
    Merely recording the old members' content hashes misses negative
    dependencies such as "all providers in this namespace satisfy P".
    This query's closed domain is only one immutable Git source tree.
    """
    import hashlib
    import re

    if not isinstance(source_cut, str) or not re.fullmatch(r"[0-9a-f]{40}", source_cut):
        raise ValueError("sourceCut must be an exact 40-hex Git commit")
    if (
        not isinstance(prefix, str)
        or not prefix.endswith("/")
        or (
            prefix.startswith("/")
            or chr(92) in prefix
            or any(part in {"", ".", ".."} for part in prefix[:-1].split("/"))
        )
    ):
        raise ValueError("query prefix must be a canonical non-root directory")
    if type(max_members) is not int or max_members < 1:
        raise ValueError("max_members must be a positive integer")

    exact = git(repo, "rev-parse", "--verify", source_cut + "^{commit}").strip()
    if exact != source_cut:
        raise ValueError("sourceCut did not resolve to the exact requested commit")
    tree_oid = git(repo, "rev-parse", source_cut + "^{tree}").strip()
    # Reuse Git's existing exhaustive NUL-delimited native tree enumeration.
    tree = current_tree(repo, source_cut)
    parts = prefix[:-1].split("/")
    for index in range(1, len(parts) + 1):
        ancestor = "/".join(parts[:index])
        if ancestor in tree:
            # A Git blob, symlink or gitlink is not a directory. In particular
            # a submodule's member set is NOT inside this parent Git tree.
            raise ValueError(f"query crosses a non-directory source boundary: {ancestor}")
    matches = sorted(
        (path, identity) for path, identity in tree.items() if path.startswith(prefix)
    )
    if len(matches) > max_members:
        raise ValueError("query membership bound exceeded; result is UNKNOWN")

    def digest(value: object) -> str:
        data = json.dumps(
            value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        )
        return "sha256:" + hashlib.sha256(data.encode("ascii")).hexdigest()

    paths = [path for path, _ in matches]
    return {
        "kind": "ordivon.git-source-membership-query",
        "truthRole": "exact-immutable-sourcecut-projection-not-consumer-authority",
        "sourceCut": source_cut,
        "treeOid": tree_oid,
        "queryPrefix": prefix,
        "memberCount": len(matches),
        "memberSetDigest": digest({"queryPrefix": prefix, "paths": paths}),
        "memberValuesDigest": digest({"queryPrefix": prefix, "members": matches}),
        "members": [{"path": path, "gitIdentity": ident} for path, ident in matches],
        "gitSourceQueryComplete": True,
        "proofReuseAdmissible": False,
        "nonClaims": [
            "Complete means only named Git paths under exact immutable SourceCut.",
            "It does not qualify Skills visibility or any installed/runtime consumer.",
            "Source membership/value equality is not semantic or proof equivalence.",
        ],
    }


def source_membership_delta(
    repo: Path, previous_cut: str, current_cut: str, prefix: str, *,
    max_members: int = 10000
) -> dict:
    """Exact Git owner evidence for task-local proof impact, never proof approval.

    A proof may depend on one member's bytes/mode, or on the *complete set* of
    paths in a namespace. Treat these as different dependencies so adding a
    new provider cannot silently reuse a proof about "all providers" while
    unrelated neighboring source changes need not invalidate a file-specific
    proof. Both cuts must be immutable Git commits in the same repository.

    No runtime/configuration/installed/consumer dependency is discovered here.
    """
    import hashlib
    from urllib.parse import quote_from_bytes

    before = source_membership_query(repo, previous_cut, prefix, max_members=max_members)
    after = source_membership_query(repo, current_cut, prefix, max_members=max_members)

    # Git source identity belongs to the shared object store, not the temporary
    # checkout: linked Agent Workspaces have one common Git directory. Independent
    # repositories retain distinct identities even when paths/objects match.
    source_root = str(
        Path(
            git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
        ).resolve(strict=True)
    )
    source_scope_ref = "git:repo:" + hashlib.sha256(
        source_root.encode("utf-8", "surrogateescape")
    ).hexdigest()

    def ref(kind: str, name: str) -> str:
        # Git paths are bytes, and may contain newlines or invalid UTF-8.
        # Quoting the exact surrogateescape bytes gives unambiguous typed IDs.
        encoded = quote_from_bytes(name.encode("utf-8", "surrogateescape"), safe="/")
        return f"{source_scope_ref}:{kind}:{encoded}"

    old = {item["path"]: item["gitIdentity"] for item in before["members"]}
    new = {item["path"]: item["gitIdentity"] for item in after["members"]}
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(
        path for path in old.keys() & new.keys() if old[path] != new[path]
    )
    member_set_changed = bool(added or removed)
    values_changed = bool(member_set_changed or changed)

    # Root refs are query identities: consumers can declare one file,
    # the entire namespace, or both in the existing Composition DAG.
    membership_ref = ref("members", prefix)
    file_refs = [
        ref("path", path) for path in sorted(set(added + removed + changed))
    ]
    changed_refs = sorted(
        file_refs + ([membership_ref] if member_set_changed else [])
    )
    authority_refs = sorted(
        [membership_ref] + [ref("path", path) for path in old.keys() | new.keys()]
    )
    if member_set_changed != (before["memberSetDigest"] != after["memberSetDigest"]):
        raise ValueError("Git membership digest contradicts exact native paths")
    if values_changed != (before["memberValuesDigest"] != after["memberValuesDigest"]):
        raise ValueError("Git value digest contradicts exact native objects")

    return {
        "kind": "ordivon.git-source-membership-delta",
        "truthRole": "exact-git-source-delta-no-proof-acceptance",
        "queryPrefix": prefix,
        "sourceScopeRef": source_scope_ref,
        "sourceCuts": {"previous": previous_cut, "current": current_cut},
        "membershipRef": membership_ref,
        "authorityRefs": authority_refs,
        "addedPaths": added,
        "removedPaths": removed,
        "changedValuePaths": changed,
        "membershipChanged": member_set_changed,
        "changedRefs": changed_refs,
        "memberSetDigests": {
            "previous": before["memberSetDigest"],
            "current": after["memberSetDigest"],
        },
        "memberValuesDigests": {
            "previous": before["memberValuesDigest"],
            "current": after["memberValuesDigest"],
        },
        "gitSourceQueryComplete": True,
        "proofReuseAdmissible": False,
        "nonClaims": [
            "Complete only for Git path membership and blob/mode under one prefix.",
            "A gitlink is an opaque source member; its internals are not observed.",
            "The caller must still qualify proof readsets, relevant configuration, "
            "runtime consumers, dynamic edges and all non-Git assumptions.",
            "changedRefs feeds a selector, never certifies REUSE_CANDIDATE as PASS.",
        ],
    }


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
    parser.add_argument(
        "--impact-prefix",
        help="Compute task-local Git source impact for this exact directory; never proof PASS",
    )
    parser.add_argument("--max-members", type=int, default=10000)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.impact_prefix is not None:
        if args.owner is not None:
            parser.error("--owner is only supported for history, not source-impact queries")
        try:
            previous = git(repo, "rev-parse", "--verify", args.left + "^{commit}").strip()
            current = git(repo, "rev-parse", "--verify", args.right + "^{commit}").strip()
            report = source_membership_delta(
                repo, previous, current, args.impact_prefix, max_members=args.max_members
            )
        except (subprocess.CalledProcessError, ValueError) as exc:
            parser.error(f"Git source impact is unqualified: {exc}")
    else:
        report = history(repo, args.left, args.right)
        if args.owner:
            report = owner_slice(report, args.owner)
    payload = json.dumps(report, ensure_ascii=True, separators=(",", ":")) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
