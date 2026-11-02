#!/usr/bin/env python3
"""Fail when a tracked file exceeds the size limit without an allowlist entry.

Large media and build output belong in an artifact store or release asset, not
in Git history. Files that are already accepted are listed with an exact
``max_bytes`` so they cannot silently grow, and stale entries fail so the list
stays honest. The check reads tracked bytes in the working tree only; it does
not rewrite or judge history.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = Path(__file__).with_name("large_files_allowlist.toml")


class AllowlistError(ValueError):
    pass


def tracked_sizes(root: Path) -> dict[str, int]:
    output = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
    sizes: dict[str, int] = {}
    for raw in output.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", errors="surrogateescape")
        try:
            st = os.lstat(root / rel)
        except FileNotFoundError:
            continue
        if os.path.islink(root / rel) or not os.path.isfile(root / rel):
            continue
        sizes[rel] = st.st_size
    return sizes


def load_allowlist(path: Path) -> tuple[int, dict[str, int]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    limit = data.get("limit_bytes")
    if not isinstance(limit, int) or limit <= 0:
        raise AllowlistError("limit_bytes must be a positive integer")
    allowed: dict[str, int] = {}
    for row in data.get("file", []):
        name = row.get("path")
        max_bytes = row.get("max_bytes")
        reason = row.get("reason")
        if not isinstance(name, str) or not name:
            raise AllowlistError("every [[file]] needs a path")
        if not isinstance(max_bytes, int) or max_bytes <= 0:
            raise AllowlistError(f"{name}: max_bytes must be a positive integer")
        if not isinstance(reason, str) or not reason.strip():
            raise AllowlistError(f"{name}: reason is required")
        if name in allowed:
            raise AllowlistError(f"{name}: listed more than once")
        allowed[name] = max_bytes
    return limit, allowed


def check(sizes: dict[str, int], limit: int, allowed: dict[str, int]) -> list[str]:
    errors: list[str] = []
    for name, size in sorted(sizes.items()):
        if size <= limit:
            continue
        if name not in allowed:
            errors.append(
                f"{name}: {size} bytes exceeds {limit}; keep large files out of Git "
                "(artifact store or release asset) or add an allowlist entry with a reason"
            )
        elif size > allowed[name]:
            errors.append(f"{name}: grew to {size} bytes, allowlisted up to {allowed[name]}")
    for name in sorted(allowed):
        if name not in sizes:
            errors.append(f"{name}: allowlist entry is stale (file is not tracked)")
        elif sizes[name] <= limit:
            errors.append(f"{name}: allowlist entry is stale (file is within {limit} bytes)")
    return errors


def main() -> int:
    try:
        limit, allowed = load_allowlist(ALLOWLIST)
    except (AllowlistError, tomllib.TOMLDecodeError, OSError) as exc:
        print(f"large-file check: invalid allowlist: {exc}", file=sys.stderr)
        return 1
    errors = check(tracked_sizes(ROOT), limit, allowed)
    for error in errors:
        print(f"large-file check: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"large-file check passed: limit {limit} bytes, {len(allowed)} allowlisted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
