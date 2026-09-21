from __future__ import annotations

import ast
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_extracted_owner_does_not_import_harness_namespace() -> None:
    violations: list[str] = []
    for base in (ROOT / "src", ROOT / "scripts"):
        for path in base.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module == "ordivon_harness" or node.module.startswith("ordivon_harness."):
                        violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "ordivon_harness" or alias.name.startswith("ordivon_harness."):
                            violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert violations == []


def test_runtime_requirements_match_package_metadata() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    requirements = [
        line.strip()
        for line in (ROOT / "config" / "skills-mcp-requirements.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert project["dependencies"] == requirements


def test_example_project_binding_is_monorepo_owned() -> None:
    config = json.loads(
        (ROOT / "config" / "skills-mcp.example.json").read_text(encoding="utf-8")
    )
    workspace = config["workspaces"]["ordivon-next"]
    assert workspace == {
        "path": "/root/projects/ordivon/meta/next",
        "trusted": True,
    }
