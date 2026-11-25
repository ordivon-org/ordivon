#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
from functools import cache
from pathlib import Path


def source_git_env() -> dict[str, str]:
    # The explicit repository is the observation subject. Never consume
    # ambient Git selectors, write optional index updates, or fetch objects.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_")}
    env.update(GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
    return env


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["/usr/bin/git", "--no-replace-objects", "-C", str(root), *args],
        check=check,
        capture_output=True,
        text=True,
        errors="surrogateescape",
        env=source_git_env(),
    )
    if result.stderr:
        raise RuntimeError("Git repository observation incomplete")
    return result


def load_policy(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1:
        raise ValueError("unsupported policy schemaVersion")
    if value.get("kind") != "ordivon.archived-source-reference-policy":
        raise ValueError("unexpected policy kind")
    locator = value.get("legacyLocator")
    if (not isinstance(locator, str) or not locator.startswith("/")
            or "\n" in locator or "\r" in locator or "\x00" in locator):
        raise ValueError("legacyLocator must be an absolute string")
    classes = value.get("allowedReferenceClasses")
    exact = value.get("allowedExactPaths")
    if not isinstance(classes, list) or not isinstance(exact, list):
        raise ValueError("allowedReferenceClasses and allowedExactPaths must be arrays")
    return value


def tracked_reference_paths(root: Path, locator: str) -> list[str]:
    """Union staged and tracked-worktree literal witnesses.

    A staged reference hidden by an unstaged edit or sparse checkout remains
    a source-retirement obligation. Git grep diagnostics (including exit 0/1)
    make the observation incomplete, never clean. This bounded lexical
    contract does not establish absence of dynamic or installed consumers.
    """
    # grep --cached can omit all unresolved stage 1/2/3 entries, even
    # when stage 3 carries the forbidden locator. There is no resolved
    # stage-0 source set to qualify in that case.
    if git(root, "ls-files", "--unmerged", "-z").stdout:
        raise RuntimeError("archived-source observation incomplete: unmerged index")
    paths = set()
    for extra in ([], ["--cached"]):
        proc = subprocess.run(
            ["/usr/bin/git", "--no-replace-objects", "-C", str(root),
             "grep", "-l", "-z", "-F", "--no-textconv", "--no-recurse-submodules",
             "--no-color", *extra, "-e", locator, "--", "."],
            check=False, capture_output=True, env=source_git_env(),
        )
        if proc.returncode not in (0, 1) or proc.stderr:
            raise RuntimeError("Git grep failed: archived-source observation incomplete")
        # Git paths are byte sequences; do not split on LF or decode lossily.
        paths.update(item.decode("utf-8", errors="surrogateescape")
                     for item in proc.stdout.split(b"\0") if item)
    return sorted(paths)


def matches_glob(path: str, pattern: str) -> bool:
    """One '*' matches one path segment; '**' matches zero or more segments."""
    segments = tuple(path.split("/"))
    globs = tuple(pattern.split("/"))

    @cache
    def matches(path_index: int, glob_index: int) -> bool:
        if glob_index == len(globs):
            return path_index == len(segments)
        glob = globs[glob_index]
        if glob == "**":
            return matches(path_index, glob_index + 1) or (
                path_index < len(segments) and matches(path_index + 1, glob_index)
            )
        return (
            path_index < len(segments)
            and fnmatch.fnmatchcase(segments[path_index], glob)
            and matches(path_index + 1, glob_index + 1)
        )

    return matches(0, 0)


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
        description=(
            "Fail closed when an archived source locator reappears "
            "outside explicit historical reference classes."
        )
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
            allowed.append(
                {
                    "path": path,
                    "class": "policy-self",
                    "reason": (
                        "The retirement policy necessarily names "
                        "the locator it governs."
                    ),
                }
            )
            continue
        classification = classify(path, policy)
        if classification is None:
            forbidden.append(path)
        else:
            klass, reason = classification
            allowed.append({"path": path, "class": klass, "reason": reason})

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.archived-source-reference-check",
        "policyId": policy["id"],
        "legacyLocator": locator,
        "trackedReferenceFileCount": len(refs),
        "allowedReferenceFileCount": len(allowed),
        "forbiddenReferenceFileCount": len(forbidden),
        "status": "PASS" if not forbidden else "FAIL",
        "observationScope": "TRACKED_WORKTREE_AND_STAGED_LITERAL_REFERENCES",
        "runtimeConsumerStanding": "UNKNOWN",
        "retirementAdmissible": False,
        "forbidden": forbidden,
        "allowed": allowed,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(
            f"{result['status']} archived-source boundary {policy['id']}: "
            f"{len(refs)} tracked reference files, {len(forbidden)} forbidden"
        )
        for path in forbidden:
            print(f"FORBIDDEN {json.dumps(path, ensure_ascii=True)}")
    return 0 if not forbidden else 1


if __name__ == "__main__":
    raise SystemExit(main())
