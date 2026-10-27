#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from functools import lru_cache
import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

MANIFEST_PATH = Path(__file__).with_name("owners.toml")


@dataclass(frozen=True)
class Owner:
    name: str
    root: str
    task: str
    queue_task: str


def load_owners(path: Path = MANIFEST_PATH) -> tuple[Owner, ...]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("owner manifest schema_version must be 1")
    if data.get("truth_role") != "repository-mechanics-only-not-domain-authority":
        raise ValueError("owner manifest truth_role must remain repository-mechanics-only")
    rows = data.get("owners")
    if not isinstance(rows, list) or not rows:
        raise ValueError("owner manifest must contain at least one [[owners]] row")

    owners: list[Owner] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"owner row {index} must be a table")
        name = row.get("name")
        root = row.get("root")
        task = row.get("verify_task")
        queue_task = row.get("queue_verify_task", task)
        if not all(isinstance(value, str) and value.strip() for value in (name, root, task, queue_task)):
            raise ValueError(
                f"owner row {index} requires non-empty name/root/verify_task and optional queue_verify_task"
            )
        if root.startswith("/") or not root.endswith("/"):
            raise ValueError(f"owner {name}: root must be repository-relative and end with '/': {root}")
        normalized = _normalize(root).rstrip("/") + "/"
        if normalized != root:
            raise ValueError(f"owner {name}: root is not canonical: {root}")
        owners.append(Owner(name=name, root=root, task=task, queue_task=queue_task))

    names = [owner.name for owner in owners]
    roots = [owner.root for owner in owners]
    tasks = [owner.task for owner in owners]
    queue_tasks = [owner.queue_task for owner in owners]
    for label, values in (
        ("name", names),
        ("root", roots),
        ("verify_task", tasks),
        ("queue_verify_task", queue_tasks),
    ):
        if len(values) != len(set(values)):
            raise ValueError(f"owner manifest contains duplicate {label}")

    for i, left in enumerate(owners):
        for right in owners[i + 1 :]:
            if left.root.startswith(right.root) or right.root.startswith(left.root):
                raise ValueError(
                    f"owner roots must not overlap: {left.name}={left.root} {right.name}={right.root}"
                )
    return tuple(owners)



CROSS_CUTTING_PATHS = frozenset(
    {
        "mise.toml",
        ".github/workflows/ci.yml",
        "tools/repo/owners.toml",
        "tools/repo/affected_owners.py",
        "tools/repo/test_affected_owners.py",
        "tools/repo/convergence_plan.py",
        "tools/repo/test_convergence_plan.py",
        "tools/repo/check_github_governance.py",
        "tools/repo/dependency_contracts.toml",
        "tools/repo/check_owner_boundaries.py",
        "tools/repo/test_owner_boundaries.py",
    }
)


def _normalize(path: str) -> str:
    value = path.strip()
    if value.startswith("/") or ".." in value.split("/") or chr(92) in value:
        raise ValueError(f"noncanonical repository path: {path}")
    return PurePosixPath(value).as_posix()


@lru_cache(maxsize=1)
def _default_owners() -> tuple[Owner, ...]:
    return load_owners()


def __getattr__(name: str):
    # Preserve the existing public tuple while exact-cut classification stays
    # independent of mutable working-tree configuration, including on import.
    if name == "OWNERS":
        return _default_owners()
    raise AttributeError(name)


# Verification admission is strict for executable owners. Read-only owner
# discovery stays permissive so unknown paths remain inspectable.
EXECUTABLE_OWNER_ROOTS = (
    "apps/",
    "services/",
    "platform/",
    "capabilities/",
    "domains/",
    "packages/",
    "extensions/",
)


def require_registered_execution_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] | None = None
) -> None:
    owners = _default_owners() if owners is None else owners
    unregistered = sorted({
        path for raw in paths
        if (path := _normalize(raw)).startswith(EXECUTABLE_OWNER_ROOTS)
        and not any(path.startswith(owner.root) for owner in owners)
    })
    if unregistered:
        raise ValueError(f"unregistered owner path: {', '.join(unregistered)}")


def owners_for_paths(
    paths: Iterable[str], *, owners: tuple[Owner, ...] | None = None
) -> tuple[Owner, ...]:
    owners = _default_owners() if owners is None else owners
    normalized = tuple(_normalize(path) for path in paths if path.strip())
    if any(path in CROSS_CUTTING_PATHS for path in normalized):
        return owners
    selected: list[Owner] = []
    for owner in owners:
        if any(path.startswith(owner.root) for path in normalized):
            selected.append(owner)
    return tuple(selected)


def changed_paths(base: str, head: str) -> tuple[str, ...]:
    # Preserve both sides of a cross-owner move, rather than allowing Git's
    # similarity detection to hide the source owner from verification.
    proc = subprocess.run(
        [
            "git", "diff", "--name-only", "--no-renames", "-z",
            "--diff-filter=ACDMRTUXB", f"{base}...{head}",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    return tuple(os.fsdecode(path) for path in proc.stdout.split(b"\0") if path)



def project_source_classification(repo: Path, source_revision: str) -> dict:
    """Rebuild source navigation; never selects verification or qualifies a LEGO."""
    from collections import Counter
    from tempfile import TemporaryDirectory

    try:
        from tools.repo import source_history_legos as source
    except ModuleNotFoundError:
        import source_history_legos as source

    source._require_exact_git_oid(repo, source_revision)
    exact = source.git(repo, "--no-replace-objects", "rev-parse", "--verify",
                       source_revision + "^{commit}").strip()
    if exact != source_revision:
        raise ValueError("sourceRevision must identify the exact requested commit")
    tree = source.current_tree(repo, source_revision)
    manifest_path = "tools/repo/owners.toml"
    manifest_identity = tree.get(manifest_path, "")
    if not manifest_identity.startswith(("100644:blob:", "100755:blob:")):
        raise ValueError("owner manifest must be a regular source-cut file")
    text = source.git(repo, "--no-replace-objects", "show",
                      source_revision + ":" + manifest_path)
    data = tomllib.loads(text)
    with TemporaryDirectory(prefix="ordivon-source-classification-") as temp:
        path = Path(temp) / "owners.toml"
        path.write_text(text, encoding="utf-8", errors="surrogateescape")
        native_owners = load_owners(path)
    regions = data.get("source_regions", [])
    if not isinstance(regions, list):
        raise ValueError("source regions must be an array")
    names = set()
    for region in regions:
        if not isinstance(region, dict) or set(region) - {"name", "description", "paths", "exclude"}:
            raise ValueError("source region fields are navigation-only")
        name = region.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("source region names must be nonempty and unique")
        names.add(name)
        if not isinstance(region.get("paths"), list) or not region["paths"]:
            raise ValueError("source region requires literal paths")
        if not isinstance(region.get("exclude", []), list):
            raise ValueError("source region exclusions must be literal paths")
        for rule in region["paths"] + region.get("exclude", []):
            if not isinstance(rule, str) or not rule:
                raise ValueError("source region requires nonempty literal paths")
            normalized = _normalize(rule).rstrip("/") + ("/" if rule.endswith("/") else "")
            if normalized != rule or rule in {".", "./", "/"}:
                raise ValueError("source region rule must be canonical and non-root")

    def matches(path: str, rule: str) -> bool:
        return path.startswith(rule) if rule.endswith("/") else path == rule

    entries = []
    for path, identity in sorted(tree.items()):
        # Git path bytes are identity. Do not strip/normalize filenames here.
        owner = next((o.name for o in native_owners if path.startswith(o.root)), None)
        matched = []
        if owner is None:
            matched = [
                region["name"] for region in regions
                if any(matches(path, rule) for rule in region["paths"])
                and not any(matches(path, rule) for rule in region.get("exclude", []))
            ]
        standing = ("REGISTERED_OWNER_SOURCE" if owner is not None else
                    "DECLARED_SOURCE_REGION" if len(matched) == 1 else
                    "AMBIGUOUS" if matched else "UNASSIGNED")
        entries.append({
            "path": path, "sourceIdentity": identity, "verificationOwner": owner,
            "sourceRegion": matched[0] if len(matched) == 1 else None,
            "classificationStanding": standing,
            "matchedRules": ["owners:" + owner] if owner is not None else
                            ["source_regions:" + name for name in matched],
        })
    counts = Counter(row["classificationStanding"] for row in entries)
    return {
        "kind": "ordivon.repository-source-classification",
        "truthRole": "SOURCE_NAVIGATION_NOT_OWNER_OR_LEGO_QUALIFICATION",
        "sourceRevision": source_revision,
        "sourceTree": source.git(repo, "--no-replace-objects", "rev-parse",
                                 source_revision + "^{tree}").strip(),
        "ownerManifestIdentity": manifest_identity,
        "proofReuseAdmissible": False,
        "summary": {
            "trackedPaths": len(entries),
            "registeredOwnerPaths": counts["REGISTERED_OWNER_SOURCE"],
            "declaredRegionPaths": counts["DECLARED_SOURCE_REGION"],
            "unassigned": counts["UNASSIGNED"], "ambiguous": counts["AMBIGUOUS"],
        },
        "entries": entries,
    }


def project_source_classification_delta(
    repo: Path, before_revision: str, after_revision: str,
) -> dict:
    """Exact Git-source navigation delta, including unedited reclassified paths.

    In particular, owner/source-region policy changes can affect unchanged
    file identities. The result is neither consumer impact nor proof reuse.
    """
    before = project_source_classification(repo, before_revision)
    after = project_source_classification(repo, after_revision)
    older = {item["path"]: item for item in before["entries"]}
    newer = {item["path"]: item for item in after["entries"]}
    changes = []
    for path in sorted(older.keys() | newer.keys()):
        previous, current = older.get(path), newer.get(path)
        if previous == current:
            continue
        source_changed = (
            previous is None or current is None
            or previous["sourceIdentity"] != current["sourceIdentity"]
        )
        classification_changed = (
            previous is None or current is None
            or any(previous[name] != current[name] for name in (
                "verificationOwner", "sourceRegion", "classificationStanding",
                "matchedRules",
            ))
        )
        changes.append({
            "path": path, "before": previous, "after": current,
            "sourceChanged": source_changed,
            "classificationChanged": classification_changed,
        })
    return {
        "kind": "ordivon.repository-source-classification-delta",
        "truthRole": "SOURCE_NAVIGATION_NOT_CONSUMER_IMPACT_OR_PROOF_REUSE",
        "beforeRevision": before_revision,
        "afterRevision": after_revision,
        "beforeTree": before["sourceTree"],
        "afterTree": after["sourceTree"],
        "beforeOwnerManifestIdentity": before["ownerManifestIdentity"],
        "afterOwnerManifestIdentity": after["ownerManifestIdentity"],
        "proofReuseAdmissible": False,
        "summary": {
            "previousPaths": before["summary"]["trackedPaths"],
            "currentPaths": after["summary"]["trackedPaths"],
            "changedEntries": len(changes),
            "classificationOnlyChanges": sum(
                item["classificationChanged"] and not item["sourceChanged"]
                for item in changes
            ),
            "unchangedEntries": len(older.keys() & newer.keys()) - sum(
                item["before"] is not None and item["after"] is not None
                for item in changes
            ),
            "unassigned": after["summary"]["unassigned"],
            "ambiguous": after["summary"]["ambiguous"],
        },
        "changes": changes,
    }

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select monorepo owners affected by an exact Git range."
    )
    parser.add_argument("--classify-source-revision", help="exact-cut source navigation; does not select verification")
    parser.add_argument("--classify-source-delta-base", help="compare exact Git source identity and source-region membership; no consumer/proof-reuse inference")
    parser.add_argument("--source-path", action="append", default=[], help="restrict exact-cut source navigation output to canonical paths")
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument(
        "--format",
        choices=("json", "names", "tasks", "queue-tasks"),
        default="json",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.classify_source_revision:
        if args.all or args.base or args.head or args.changed_file or args.format != "json":
            raise SystemExit("source classification cannot be combined with verification selection")
        if args.classify_source_delta_base:
            if args.source_path:
                raise SystemExit("source delta must include all reclassified paths")
            result = project_source_classification_delta(
                Path.cwd(), args.classify_source_delta_base, args.classify_source_revision
            )
        else:
            result = project_source_classification(Path.cwd(), args.classify_source_revision)
            if args.source_path:
                # Git paths are opaque source identities. Do not silently
                # normalize "./foo", "foo//bar" or whitespace into the
                # identity of a different tracked file.
                for path in args.source_path:
                    if not path or _normalize(path) != path:
                        raise SystemExit(f"source path must be exact/canonical: {path!r}")
                paths = sorted(set(args.source_path))
                index = {entry["path"]: entry for entry in result["entries"]}
                result["entries"] = [index[path] for path in paths if path in index]
                result["requestedPaths"] = paths
                result["missingPaths"] = [path for path in paths if path not in index]
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.classify_source_delta_base or args.source_path:
        raise SystemExit("source query requires --classify-source-revision")
    if args.all:
        selected = _default_owners()
        paths: tuple[str, ...] = ()
    else:
        if args.changed_file:
            paths = tuple(args.changed_file)
        else:
            if not args.base or not args.head:
                raise SystemExit("--base and --head are required unless --all or --changed-file is used")
            paths = changed_paths(args.base, args.head)
        require_registered_execution_paths(paths)
        selected = owners_for_paths(paths)

    if args.format == "names":
        for owner in selected:
            print(owner.name)
    elif args.format == "tasks":
        for owner in selected:
            print(owner.task)
    elif args.format == "queue-tasks":
        for owner in selected:
            print(owner.queue_task)
    else:
        print(
            json.dumps(
                {
                    "changedPaths": list(paths),
                    "owners": [
                        {
                            "name": owner.name,
                            "root": owner.root,
                            "task": owner.task,
                            "queueTask": owner.queue_task,
                        }
                        for owner in selected
                    ],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
