from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_package_discovery_includes_current_python_surfaces() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    includes = set(pyproject["tool"]["setuptools"]["packages"]["find"]["include"])

    assert "ordivon_governance_core*" in includes
    assert "ordivon_verify*" in includes
    assert "state*" in includes


def test_current_python_surfaces_are_importable() -> None:
    for package in ("ordivon_governance_core", "ordivon_verify", "state"):
        assert importlib.util.find_spec(package) is not None
