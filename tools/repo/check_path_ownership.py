#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import subprocess
from pathlib import Path

import affected_owners

ROOT = Path(__file__).resolve().parents[2]


def tracked_paths() -> tuple[str, ...]:
    output = subprocess.check_output(["git", "-C", str(ROOT), "ls-files"], text=True)
    return tuple(path for path in output.splitlines() if path)


def check(paths: tuple[str, ...]) -> dict[str, int]:
    counts: collections.Counter[str] = collections.Counter()
    failures: list[str] = []
    for path in paths:
        try:
            resolution = affected_owners.resolve_path(path)
        except ValueError as exc:
            failures.append(f"{path}: {exc}")
            continue
        label = resolution.owner.name if resolution.owner else resolution.kind
        counts[label] += 1
    if failures:
        preview = "\n".join(failures[:100])
        suffix = "" if len(failures) <= 100 else f"\n... {len(failures)-100} more"
        raise AssertionError(
            f"unclassified tracked repository paths ({len(failures)}):\n{preview}{suffix}"
        )
    return dict(sorted(counts.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Prove total repository path ownership/classification.")
    parser.add_argument("--path", action="append", default=[])
    args = parser.parse_args()
    paths = tuple(args.path) if args.path else tracked_paths()
    counts = check(paths)
    print(f"path ownership: total (paths={len(paths)}, classes={counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
