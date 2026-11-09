"""Reject retroactive edits to registered Authority provenance across a Git change.

Registration is a historical witness, not a live checkout-navigation pointer.
This is a change-level invariant; ordinary source/schema validators cannot
establish it from a single tree. New records and unrelated edits are allowed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RECORDS = "catalogs/authorities/records/"
REVISION = re.compile(r"[0-9a-f]{7,64}\Z")
GIT = shutil.which("git")


def git(*args: str) -> str:
    if GIT is None:
        raise RuntimeError("Git is required for historic registration checking")
    return subprocess.check_output(
        [GIT, "--no-replace-objects", *args], cwd=ROOT, text=True
    )


def registered_at(revision: str) -> dict[str, dict]:
    if not REVISION.fullmatch(revision):
        raise ValueError("Git source revision must be an explicit hexadecimal commit")
    records = {}
    paths = git("ls-tree", "-r", "--name-only", revision, "--", RECORDS)
    for path in paths.splitlines():
        if not path.endswith(".json"):
            continue
        record = json.loads(git("show", f"{revision}:{path}"))
        identifier = record["id"]
        if identifier in records:
            raise ValueError(f"duplicate Authority identity: {identifier}")
        records[identifier] = {
            "path": path,
            "registeredDate": record["provenance"]["registeredDate"],
            "registrationBasis": record["provenance"]["registrationBasis"],
        }
    return records


def changed_history(before: dict[str, dict], after: dict[str, dict]) -> list[str]:
    violations = []
    for identifier in sorted(before.keys() & after.keys()):
        old, new = before[identifier], after[identifier]
        for field in ("registeredDate", "registrationBasis"):
            if old[field] != new[field]:
                violations.append(f"{identifier}: historic provenance.{field} changed")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    before = registered_at(args.base)
    after = registered_at(args.head)
    violations = changed_history(before, after)
    if violations:
        raise SystemExit(
            "Authority historical registration must not be rewritten as current "
            "navigation. Preserve the recorded witness; represent a correction "
            "as a separately evidenced replacement, not an in-place migration:\n"
            + "\n".join(violations)
        )
    print(
        f"Authority registration history preserved: {len(before.keys() & after.keys())} existing records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
