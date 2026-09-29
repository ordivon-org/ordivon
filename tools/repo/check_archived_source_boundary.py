#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/usr/bin/git", "-C", str(root), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def load_policy(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1:
        raise ValueError("unsupported policy schemaVersion")
    if value.get("kind") != "ordivon.archived-source-reference-policy":
        raise ValueError("unexpected policy kind")
    locator = value.get("legacyLocator")
    if not isinstance(locator, str) or not locator.strip():
        raise ValueError("legacyLocator must be a non-empty string")
    if not locator.startswith("/"):
        candidate = Path(locator)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("repository-relative legacyLocator must stay inside the repository")
    archived_tree = value.get("archivedTree")
    if archived_tree is not None:
        if not isinstance(archived_tree, dict):
            raise ValueError("archivedTree must be an object")
        tree_path = archived_tree.get("path")
        tree_object = archived_tree.get("expectedGitTree")
        if (
            not isinstance(tree_path, str)
            or not tree_path
            or tree_path.startswith("/")
            or ".." in Path(tree_path).parts
        ):
            raise ValueError("archivedTree.path must be repository-relative")
        if not isinstance(tree_object, str) or not re.fullmatch(r"[0-9a-f]{40}", tree_object):
            raise ValueError("archivedTree.expectedGitTree must be a 40-hex Git tree object")
    classes = value.get("allowedReferenceClasses")
    exact = value.get("allowedExactPaths")
    if not isinstance(classes, list) or not isinstance(exact, list):
        raise ValueError("allowedReferenceClasses and allowedExactPaths must be arrays")
    return value


def tracked_reference_paths(root: Path, locator: str) -> list[str]:
    proc = git(root, "grep", "-l", "-F", locator, "--", ".", check=False)
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr.strip() or "git grep failed")
    refs = sorted({line.strip() for line in proc.stdout.splitlines() if line.strip()})
    if not locator.startswith("/"):
        archived_prefix = locator.rstrip("/") + "/"
        refs = [path for path in refs if not path.startswith(archived_prefix)]
    return refs


def archived_tree_projection(root: Path, policy: dict) -> dict | None:
    tree = policy.get("archivedTree")
    if tree is None:
        return None
    path = tree["path"]
    expected = tree["expectedGitTree"]
    proc = git(root, "rev-parse", f"HEAD:{path}", check=False)
    observed = proc.stdout.strip() if proc.returncode == 0 else None
    return {
        "path": path,
        "expectedGitTree": expected,
        "observedGitTree": observed,
        "status": "PASS" if observed == expected else "FAIL",
    }


def matches_glob(path: str, pattern: str) -> bool:
    if fnmatch.fnmatchcase(path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatchcase(path, pattern[3:])
    return False


def classify(path: str, policy: dict) -> tuple[str, str] | None:
    for row in policy["allowedExactPaths"]:
        if path == row["path"]:
            return "exact:" + path, row["reason"]
    for row in policy["allowedReferenceClasses"]:
        for pattern in row["globs"]:
            if matches_glob(path, pattern):
                return row["id"], row["reason"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail closed when an archived source locator reappears outside explicit historical reference classes."
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(git(args.repo, "rev-parse", "--show-toplevel").stdout.strip())
    policy_path = args.policy if args.policy.is_absolute() else root / args.policy
    policy = load_policy(policy_path)
    locator = policy["legacyLocator"]

    refs = tracked_reference_paths(root, locator)
    policy_relative = policy_path.resolve().relative_to(root.resolve()).as_posix()
    allowed: list[dict[str, str]] = []
    forbidden: list[str] = []
    for path in refs:
        if path == policy_relative:
            allowed.append({
                "path": path,
                "class": "policy-self",
                "reason": "The retirement policy necessarily names the locator it governs.",
            })
            continue
        classification = classify(path, policy)
        if classification is None:
            forbidden.append(path)
        else:
            klass, reason = classification
            allowed.append({"path": path, "class": klass, "reason": reason})

    tree_projection = archived_tree_projection(root, policy)
    tree_ok = tree_projection is None or tree_projection["status"] == "PASS"
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.archived-source-reference-check",
        "policyId": policy["id"],
        "legacyLocator": locator,
        "trackedReferenceFileCount": len(refs),
        "allowedReferenceFileCount": len(allowed),
        "forbiddenReferenceFileCount": len(forbidden),
        "status": "PASS" if not forbidden and tree_ok else "FAIL",
        "forbidden": forbidden,
        "allowed": allowed,
        "archivedTree": tree_projection,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        tree_detail = ""
        if tree_projection is not None:
            tree_detail = f", archived_tree={tree_projection['status']}"
        print(
            f"{result['status']} archived-source boundary {policy['id']}: "
            f"{len(refs)} tracked reference files, {len(forbidden)} forbidden{tree_detail}"
        )
        for path in forbidden:
            print(f"FORBIDDEN {path}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
