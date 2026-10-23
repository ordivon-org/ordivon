from __future__ import annotations

import json
import shutil
import subprocess
import tomllib
from pathlib import Path

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
    expected = owner["python"]
    assert lock["pythonRuntime"] == expected
    assert project["requires-python"] == f"=={expected}"
    assert uv_lock["requires-python"] == f"=={expected}"


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
    assert observed_python == owner["python"]
    assert observed_uv.startswith(f"uv {owner['uv']}")
