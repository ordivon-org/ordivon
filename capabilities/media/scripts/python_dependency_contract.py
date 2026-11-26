"""One lock-derived runtime dependency check for acquisition and readiness."""
from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ("pyproject.toml", "uv.lock", ".python-version")
EXPECTED_PYTHON = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
RUNTIME_PACKAGES = ("jsonschema", "markdown-it-py", "psycopg", "psycopg-binary")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def locked_runtime_versions() -> dict[str, str]:
    packages = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))["package"]
    versions = {}
    for name in RUNTIME_PACKAGES:
        candidates = {entry["version"] for entry in packages if entry["name"] == name}
        if len(candidates) != 1:
            raise ValueError(f"expected one locked version for {name}: {candidates}")
        versions[name] = candidates.pop()
    return versions


def environment_probe() -> str:
    # Explicit checks remain active when the child interpreter enables optimization.
    return (
        "import importlib.metadata as m, platform; "
        f"expected={locked_runtime_versions()!r}; "
        f"actual_python=platform.python_version(); expected_python={EXPECTED_PYTHON!r}; "
        "actual={name:m.version(name) for name in expected}; "
        "raise SystemExit(0 if actual_python==expected_python and actual==expected else 2)"
    )
