from __future__ import annotations

import json
import shutil
import subprocess
import tomllib
from pathlib import Path

from packaging.specifiers import SpecifierSet

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "artifact-delivery/artifact-python-runtime-v1.lock.json"
PROJECT = ROOT / "artifact-delivery/python-uv/pyproject.toml"
UV_LOCK = ROOT / "artifact-delivery/python-uv/uv.lock"
MISE = ROOT / "mise.toml"
ENVIRONMENT = ROOT / "scripts/artifact_python_environment.py"


def test_python_carrier_has_one_version_authority() -> None:
    owner = tomllib.loads(MISE.read_text())["tools"]
    lock = json.loads(LOCK.read_text())
    project = tomllib.loads(PROJECT.read_text())["project"]
    uv_lock = tomllib.loads(UV_LOCK.read_text())
    # The rolling compatibility policy is not the exact release snapshot.
    # The latter still gates materialization and is bound to uv.lock bytes.
    expected = owner["python"]
    assert (ROOT / ".python-version").read_text().strip() == expected
    assert lock["pythonRuntime"].startswith(expected + ".")
    compatible = SpecifierSet(project["requires-python"])
    assert lock["pythonRuntime"] in compatible
    locked_compatibility = SpecifierSet(uv_lock["requires-python"])
    assert lock["pythonRuntime"] in locked_compatibility
    # uv canonicalizes the same stable minor range to ==3.15.*.
    # Compare behavior at boundaries rather than requiring textual syntax.
    for version in ("3.14.99", "3.15.0", "3.15.1", "3.15.99", "3.16.0", "4.0.0"):
        assert (version in compatible) == (version in locked_compatibility)
    assert compatible == SpecifierSet(tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["requires-python"])


def test_materializer_consumes_owner_mise_tools_without_version_paths() -> None:
    source = ENVIRONMENT.read_text()
    assert "selected_owner_tool" in source
    assert "/installs/uv/0.12.16/" not in source
    assert "/installs/python/3.15.0/" not in source
    owner = tomllib.loads(MISE.read_text())["tools"]
    mise = shutil.which("mise")
    assert mise is not None, "Artifact owner mise must be discoverable on PATH"
    python = subprocess.run(
        [mise, "-C", str(ROOT), "which", "python"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    uv = subprocess.run(
        [mise, "-C", str(ROOT), "which", "uv"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    observed_python = subprocess.run(
        [python, "-c", "import platform;print(platform.python_version())"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    observed_uv = subprocess.run(
        [uv, "--version"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    assert observed_python.startswith(owner["python"] + ".")
    assert observed_python in SpecifierSet(tomllib.loads(PROJECT.read_text())["project"]["requires-python"])
    assert observed_uv.startswith("uv ")
    # A floating resolver selector has no meaningful exact version string.
    if owner["uv"] != "latest":
        assert observed_uv.startswith(f"uv {owner['uv']}")
