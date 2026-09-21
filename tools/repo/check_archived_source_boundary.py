#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
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
    if not isinstance(locator, str) or not locator.startswith("/"):
        raise ValueError("legacyLocator must be an absolute string")
    classes = value.get("allowedReferenceClasses")
    exact = value.get("allowedExactPaths")
    if not isinstance(classes, list) or not isinstance(exact, list):
        raise ValueError("allowedReferenceClasses and allowedExactPaths must be arrays")
    return value


def tracked_reference_paths(root: Path, locator: str) -> list[str]:
    proc = git(root, "grep", "-l", "-F", locator, "--", ".", check=False)
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr.strip() or "git grep failed")
    return sorted({line.strip() for line in proc.stdout.splitlines() if line.strip()})


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

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.archived-source-reference-check",
        "policyId": policy["id"],
        "legacyLocator": locator,
        "trackedReferenceFileCount": len(refs),
        "allowedReferenceFileCount": len(allowed),
        "forbiddenReferenceFileCount": len(forbidden),
        "status": "PASS" if not forbidden else "FAIL",
        "forbidden": forbidden,
        "allowed": allowed,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"{result['status']} archived-source boundary {policy['id']}: "
            f"{len(refs)} tracked reference files, {len(forbidden)} forbidden"
        )
        for path in forbidden:
            print(f"FORBIDDEN {path}")
    return 0 if not forbidden else 1


if __name__ == "__main__":
    raise SystemExit(main())
