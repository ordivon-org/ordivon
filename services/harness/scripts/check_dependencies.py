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

    audit = sorted(
        line.strip()
        for line in (ROOT / "requirements-audit.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    lock_data = tomllib.loads(lock)
    packages = [p for p in lock_data.get("package", []) if isinstance(p, dict)]
    by_name: dict[str, dict] = {}
    for package in packages:
        name = str(package.get("name") or "").lower()
        if not name:
            fail("uv.lock contains a package without a name")
        if name in by_name:
            fail(f"uv.lock contains ambiguous duplicate package name: {name}")
        by_name[name] = package

    root = by_name.get("ordivon-harness")
    if root is None:
        fail("uv.lock omits the Harness root package")

    pending = [
        str(item.get("name") or "").lower()
        for item in root.get("dependencies", [])
        if isinstance(item, dict)
    ]
    runtime_names: set[str] = set()
    while pending:
        name = pending.pop()
        if not name or name in runtime_names:
            continue
        package = by_name.get(name)
        if package is None:
            fail(f"runtime dependency is absent from uv.lock: {name}")
        runtime_names.add(name)
        pending.extend(
            str(item.get("name") or "").lower()
            for item in package.get("dependencies", [])
            if isinstance(item, dict)
        )

    locked_pypi = sorted(
        f"{package['name']}=={package['version']}"
        for name, package in by_name.items()
        if name in runtime_names
        and isinstance(package.get("source"), dict)
        and package["source"].get("registry") == "https://pypi.org/simple"
    )
    if audit != locked_pypi:
        fail("requirements-audit.txt must exactly match registry-sourced uv.lock runtime packages")

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
