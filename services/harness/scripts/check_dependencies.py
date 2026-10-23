#!/usr/bin/env python3
"""Validate the exact Host-free Harness dependency graph and lockfile truth."""

from __future__ import annotations

import re
import sys
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"dependencies: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    raw = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = raw["project"]
    expected_dependencies = ["httpx==0.28.1", "jsonschema>=4.26,<5"]
    if project.get("dependencies") != expected_dependencies:
        fail("base dependencies must contain only HTTPX and jsonschema")
    if project.get("optional-dependencies") != {"mcp": ["mcp==2.2.0"]}:
        fail("Harness may expose only the official MCP v2 standards-adapter extra")
    expected_groups = {
        "dev": ["ruff==0.15.17"],
        "test": [
            "mcp==2.2.0",
            "uvicorn==0.52.1",
            "playwright==1.63.0",
            "rfc8785==0.1.4",
            "pytest==9.1.1",
        ],
    }
    if raw.get("dependency-groups") != expected_groups:
        fail("Harness dependency groups must preserve exact dev/test separation")
    if (raw.get("tool") or {}).get("uv", {}).get("default-groups") != ["dev", "test"]:
        fail("Harness owner environment must default to exact dev + test groups")

    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    if "ordivon-protocol" in lock or "ordivon-computing" in lock:
        fail("uv.lock still contains retired cross-repository Protocol/Computing dependency")
    if "ordivon-host" in lock or "ordivon_host" in lock:
        fail("uv.lock still contains Ordivon Host")

    version_match = re.search(
        r'^version = "([^"]+)"$',
        (ROOT / "pyproject.toml").read_text(),
        re.MULTILINE,
    )
    fallback_match = re.search(
        r'^_FALLBACK_VERSION = "([^"]+)"$',
        (ROOT / "src/ordivon_harness/version.py").read_text(),
        re.MULTILINE,
    )
    if (
        version_match is None
        or fallback_match is None
        or version_match.group(1) != fallback_match.group(1)
    ):
        fail("package version and source-checkout fallback differ")

    print(
        "dependency contract: valid canonical=owner-local-compat host=absent "
        "runtime=httpx+jsonschema adapter=mcp2.2 dev=ruff test=agent-mcp+playwright+pytest"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
