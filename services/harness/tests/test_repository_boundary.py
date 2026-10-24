from __future__ import annotations

import ast
import json
from pathlib import Path
import tomllib
import unittest

import ordivon_harness
from ordivon_harness.store import HARNESS_STORE_EVENT_KINDS

ROOT = Path(__file__).resolve().parents[1]


class RepositoryBoundaryTests(unittest.TestCase):
    def test_harness_has_no_host_dependency_or_compatibility_package(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        requirements = project["project"]["dependencies"]
        self.assertEqual(len(requirements), 2)
        self.assertIn("httpx==0.28.1", requirements)
        self.assertIn("jsonschema>=4.26,<5", requirements)
        self.assertFalse(any("ordivon-protocol" in requirement for requirement in requirements))
        self.assertEqual(project["project"].get("optional-dependencies"), {"mcp": ["mcp==2.3.0"]})
        self.assertEqual(
            project.get("dependency-groups"),
            {
                "dev": ["ruff==0.17.2"],
                "test": [
                    "mcp==2.3.0",
                    "uvicorn==0.52.1",
                    "playwright==1.63.0",
                    "rfc8785==0.1.4",
                    "pytest==9.1.1",
                ],
            },
        )
        self.assertEqual(
            (project.get("tool") or {}).get("uv", {}).get("default-groups"),
            ["dev", "test"],
        )
        self.assertNotIn("ordivon-host", str(project.get("dependency-groups", {})))
        package = ROOT / "src" / "ordivon_harness"
        self.assertFalse((package / "_host_compat").exists())
        self.assertFalse((package / "host.py").exists())
        self.assertFalse((package / "runner.py").exists())
        self.assertFalse((package / "cutover.py").exists())
        self.assertFalse((package / "skills").exists())
        self.assertFalse(hasattr(ordivon_harness, "HarnessHost"))
        self.assertFalse(hasattr(ordivon_harness, "HarnessRunner"))

    def test_unconsumed_generic_harness_provider_spi_stays_retired(self) -> None:
        """A prospective alternate-engine plan is not an admitted executable Owner."""
        plan = json.loads((ROOT / "planning" / "lego-plan-r1.json").read_text())
        node_ids = {item["id"] for item in plan["nodes"]}
        self.assertTrue({"H01", "H02", "H03", "H04"} <= node_ids)
        self.assertNotIn("H05", node_ids)
        self.assertFalse(any(
            edge["from"] == "H05" or edge["to"] == "H05"
            for edge in plan["edges"]
        ))
        slices = {item["id"]: item for item in plan["slices"]}
        self.assertNotIn("HS1", slices)
        self.assertEqual(set(slices["HS2"]["nodeIds"]), {"H03", "H04"})
        self.assertFalse(any("alternate-harness adapter" in gap for gap in plan["gaps"]))

    def test_portable_workflows_consume_only_locked_runtime_audit_closure(self) -> None:
        """No optional extracted-repo Workflow may reference a retired requirements snapshot."""
        audit_export = (
            "uv export --locked --no-default-groups --no-emit-project "
            "--format requirements-txt"
        )
        audit_action = (
            'uvx pip-audit --disable-pip --require-hashes '
            '-r "$tmp/runtime-requirements.txt" --strict --progress-spinner off'
        )
        for name in ("ci.yml", "release-acceptance.yml"):
            with self.subTest(workflow=name):
                workflow = (ROOT / ".github" / "workflows" / name).read_text()
                self.assertNotIn("requirements-audit.txt", workflow)
                self.assertIn(audit_export, workflow)
                self.assertIn(audit_action, workflow)
                self.assertIn("uv run --locked ruff check src tests scripts", workflow)
                self.assertNotIn("uvx ruff==", workflow)
                self.assertFalse((ROOT / "requirements-audit.txt").exists())

    def test_source_tree_contains_no_ordivon_host_imports(self) -> None:
        source_root = ROOT / "src" / "ordivon_harness"
        violations: list[str] = []
        for path in source_root.rglob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module == "ordivon_host" or node.module.startswith("ordivon_host."):
                        violations.append(f"{path.relative_to(source_root)}:{node.lineno}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "ordivon_host" or alias.name.startswith("ordivon_host."):
                            violations.append(f"{path.relative_to(source_root)}:{node.lineno}")
        self.assertEqual(violations, [])

    def test_harness_store_owns_its_event_vocabulary(self) -> None:
        self.assertIn("harness.run-created", HARNESS_STORE_EVENT_KINDS)
        self.assertIn("harness.provider-call-claimed", HARNESS_STORE_EVENT_KINDS)
        self.assertIn("harness.tool-step-prepared", HARNESS_STORE_EVENT_KINDS)

    def test_retired_host_era_abandonment_surface_does_not_return(self) -> None:
        import ordivon_harness.api as api
        from ordivon_harness.store import HARNESS_STORE_EVENT_KINDS, HarnessRunStatus

        package = ROOT / "src" / "ordivon_harness"
        self.assertFalse((package / "disposition.py").exists())
        self.assertFalse((package / "core.py").exists())
        self.assertFalse(hasattr(api, "NativeRunAbandonment"))
        self.assertFalse(hasattr(HarnessRunStatus, "ABANDONED"))
        self.assertNotIn("harness.run-abandoned", HARNESS_STORE_EVENT_KINDS)


if __name__ == "__main__":
    unittest.main()
