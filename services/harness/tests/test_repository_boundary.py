from __future__ import annotations

import ast
from pathlib import Path
import tomllib
import unittest

from ordivon_harness.store import HARNESS_STORE_EVENT_KINDS

ROOT = Path(__file__).resolve().parents[1]


class RepositoryBoundaryTests(unittest.TestCase):
    def test_harness_business_api_has_no_foreign_host_dependency(self) -> None:
        """Public Agent capability must import without a Host framework."""
        from ordivon_harness.api import DomainToolLoopRunner, HarnessAgentRun

        project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        direct = project["project"]["dependencies"]
        declared_optional = project["project"].get("optional-dependencies", {})
        self.assertFalse(any(
            "ordivon-host" in dependency or "ordivon-protocol" in dependency
            for dependency in direct
        ))
        self.assertFalse(any(
            "ordivon-host" in dependency
            for dependencies in declared_optional.values()
            for dependency in dependencies
        ))
        self.assertTrue(callable(DomainToolLoopRunner.run))
        self.assertTrue(callable(HarnessAgentRun.create))

    def test_release_pipeline_executes_locked_dependency_security_audit(self) -> None:
        """Validate the audit mechanism, not a former CI file's absence."""
        tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
        release = (ROOT / ".github/workflows/release-acceptance.yml").read_text()
        entrypoints = {
            "queue": tasks["queue"]["run"],
            "verify": tasks["verify"]["run"],
            "release": release,
        }
        for owner, commands in entrypoints.items():
            with self.subTest(consumer=owner):
                self.assertIn("uv export --locked", commands)
                self.assertIn("--no-default-groups", commands)
                self.assertIn("pip-audit", commands)
                self.assertIn("--strict", commands)

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

    def test_internal_module_capability_dependencies_form_a_dag(self) -> None:
        """Agent-facing components must not force each other to import cyclically.

        The graph is discovered from the installed Python package tree. New,
        renamed or retired implementation files change the graph automatically;
        no historic file name, old MixIn, or retired directory is pinned.
        """
        source_root = ROOT / "src" / "ordivon_harness"
        modules: dict[str, Path] = {}
        for path in source_root.rglob("*.py"):
            relative = path.relative_to(source_root)
            if path.name == "__init__.py":
                suffix = relative.parent.parts
            else:
                suffix = relative.with_suffix("").parts
            name = ".".join(("ordivon_harness", *suffix))
            modules[name] = path
        imports: dict[str, set[str]] = {name: set() for name in modules}
        for name, path in modules.items():
            package = name.split(".") if path.name == "__init__.py" else name.split(".")[:-1]
            for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
                if isinstance(node, ast.ImportFrom):
                    if node.level:
                        if node.level > len(package):
                            continue
                        root = ".".join(package[: len(package) - node.level + 1])
                        if node.module:
                            root += "." + node.module
                    else:
                        root = node.module or ""
                    candidates = (root, *(root + "." + alias.name for alias in node.names))
                elif isinstance(node, ast.Import):
                    candidates = tuple(alias.name for alias in node.names)
                else:
                    continue
                imports[name].update(
                    dest for dest in candidates if dest in modules and dest != name
                )
        state: dict[str, int] = {}
        stack: list[str] = []

        def visit(name: str) -> None:
            if state.get(name) == 2:
                return
            if state.get(name) == 1:
                raise AssertionError(
                    "first-party capability import cycle: " + " -> ".join(
                        (*stack[stack.index(name) :], name)
                    )
                )
            state[name] = 1
            stack.append(name)
            for dependency in sorted(imports[name]):
                visit(dependency)
            stack.pop()
            state[name] = 2

        for module in sorted(modules):
            visit(module)

    def test_harness_store_owns_its_event_vocabulary(self) -> None:
        self.assertIn("harness.run-created", HARNESS_STORE_EVENT_KINDS)
        self.assertIn("harness.provider-call-claimed", HARNESS_STORE_EVENT_KINDS)
        self.assertIn("harness.tool-step-prepared", HARNESS_STORE_EVENT_KINDS)

    def test_retired_host_era_abandonment_surface_does_not_return(self) -> None:
        import ordivon_harness.api as api
        from ordivon_harness.store import HARNESS_STORE_EVENT_KINDS, HarnessRunStatus

        self.assertFalse(hasattr(api, "NativeRunAbandonment"))
        self.assertFalse(hasattr(HarnessRunStatus, "ABANDONED"))
        self.assertNotIn("harness.run-abandoned", HARNESS_STORE_EVENT_KINDS)


if __name__ == "__main__":
    unittest.main()
