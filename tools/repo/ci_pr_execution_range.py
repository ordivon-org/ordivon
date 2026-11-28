"""Bind pull-request selection to the immutable tested merge cut.

This qualifies the native range, not a proof or artifact reuse decision.
For unequal path inventories the caller must conservatively verify all.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from affected_owners import _source_git_env, changed_paths


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), *args],
        env=_source_git_env(), stderr=subprocess.PIPE, text=True, timeout=30,
    ).strip()


def _commit(repo: Path, value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value) or not value.strip("0"):
        raise ValueError("PR execution requires exact nonzero Git identities")
    if _git(repo, "rev-parse", "--verify", "--end-of-options", value + "^{commit}") != value:
        raise ValueError("PR execution coordinate is not a native commit")
    return value


def resolve(repo: Path, event_base: str, event_head: str, execution_cut: str) -> tuple[str, str] | None:
    """Return actual first-parent range, or None for all-obligation fallback."""
    repo = repo.resolve()
    if Path(_git(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise ValueError("PR execution requires repository root")
    if _git(repo, "rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("PR execution requires complete Git ancestry")
    base, head, cut = (_commit(repo, x) for x in (event_base, event_head, execution_cut))
    if _git(repo, "rev-parse", "HEAD") != cut or cut == head:
        raise ValueError("PR execution checkout mismatch")
    headers = _git(repo, "cat-file", "-p", cut).split("\n\n", 1)[0]
    parents = [line[7:] for line in headers.splitlines() if line.startswith("parent ")]
    if len(parents) != 2 or parents[1] != head:
        raise ValueError("PR execution requires ordered native merge parents")
    parent = _commit(repo, parents[0])
    # Unique original merge base is required before using the event delta.
    if len(_git(repo, "merge-base", "--all", base, head).splitlines()) != 1:
        raise ValueError("PR event merge base is ambiguous")
    if _git(repo, "merge-base", base, parent) != base:
        raise ValueError("PR execution base diverges from original event base")
    event_paths = set(changed_paths(base, head, source_repo_root=repo))
    execution_paths = set(changed_paths(parent, cut, source_repo_root=repo))
    if event_paths != execution_paths:
        return None
    return parent, cut


def main() -> int:
    try:
        base, head, cut = sys.argv[1:]
        if os.environ.get("GITHUB_SHA", cut) != cut:
            raise ValueError("provider execution SHA mismatch")
        result = resolve(Path.cwd(), base, head, cut)
        if result is None:
            print("PR event/execution path inventories differ; verifying all obligations", file=sys.stderr)
            print("ALL")
        else:
            print(*result)
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("ERROR: unqualified PR execution range: " + str(exc), file=sys.stderr)
        return 43


if __name__ == "__main__":
    raise SystemExit(main())
