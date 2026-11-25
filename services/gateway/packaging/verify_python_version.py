"""Validate the exact source-declared Python carrier without a second version pin."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

_EXACT_PATCH = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def source_python_request(release: Path) -> str:
    version_file = release / ".python-version"
    project_file = release / "pyproject.toml"
    for path in (version_file, project_file):
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"release needs a regular {path.name}")
    lines = version_file.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1 or not _EXACT_PATCH.fullmatch(lines[0]):
        raise ValueError(".python-version must contain one exact CPython patch version")
    requested = lines[0]
    project = tomllib.loads(project_file.read_text(encoding="utf-8"))
    if project["project"].get("requires-python") != f"=={requested}":
        raise ValueError("pyproject requires-python must exactly match .python-version")
    return requested


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("request", "verify"))
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    try:
        requested = source_python_request(args.release)
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(str(exc)) from exc
    if args.operation == "request":
        print(requested)
        return
    actual = ".".join(map(str, sys.version_info[:3]))
    if (
        sys.implementation.name != "cpython"
        or sys.version_info.releaselevel != "final"
        or actual != requested
    ):
        raise SystemExit(f"Gateway release Python mismatch: expected {requested}, got {actual}")
    print(f"qualified CPython {actual}")


if __name__ == "__main__":
    main()
