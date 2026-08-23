from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ordivon_studio.agent_surface import (
    dependency_proposal,
    dependency_status,
    execute_surface_action,
    surface_projection,
)


class AgentSurfaceTests(unittest.TestCase):
    def _root(self, directory: str) -> Path:
        root = Path(directory)
        (root / "node_modules/.bin").mkdir(parents=True)
        (root / "node_modules/.modules.yaml").write_text("ok\n", encoding="utf-8")
        (root / "node_modules/.bin/tsc").write_text("ok\n", encoding="utf-8")
        (root / ".venv/bin").mkdir(parents=True)
        (root / ".venv/bin/python").write_text("python\n", encoding="utf-8")
        for name, content in (
            ("pyproject.toml", "[project]\nname='x'\n"),
            ("uv.lock", "version = 1\n"),
            (".python-version", "3.12.13\n"),
        ):
            (root / name).write_text(content, encoding="utf-8")
        inputs = {
            name: "sha256:" + hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ("pyproject.toml", "uv.lock", ".python-version")
        }
        (root / ".venv/.ordivon-materialization.json").write_text(
            json.dumps({
                "schemaVersion": 1,
                "kind": "ordivon.studio-python-materialization-receipt",
                "inputs": inputs,
                "extras": ["resolve"],
                "python": "Python 3.12.13",
                "uv": "uv test",
            }),
            encoding="utf-8",
        )
        return root

    def test_surface_is_small_domain_owned_and_transport_neutral(self) -> None:
        value = surface_projection()
        self.assertEqual(value["domainId"], "domain:ordivon-studio")
        self.assertFalse(value["mcpRequired"])
        self.assertTrue(value["harnessMayAdmitSubsetOnly"])
        self.assertEqual(
            [item["name"] for item in value["tools"]],
            ["studio_dependencies_status", "studio_dependencies_propose", "studio_production_context", "studio_learning_context", "studio_equipment_propose"],
        )

    def test_dependency_observation_never_acquires_and_detects_exact_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            with mock.patch("ordivon_studio.agent_surface.subprocess.run", return_value=mock.Mock(returncode=0)):
                state = dependency_status(root)
                self.assertTrue(state["js"]["ready"])
                self.assertTrue(state["js"]["resolverChecked"])
                self.assertTrue(state["python"]["ready"])
                self.assertTrue(state["resolve"]["ready"])
                (root / "uv.lock").write_text("changed\n", encoding="utf-8")
                stale = dependency_status(root)
            self.assertEqual(stale["python"]["reason"], "PYTHON_RECEIPT_STALE")
            self.assertFalse(stale["python"]["ready"])

    def test_js_status_delegates_currentness_to_fail_closed_workstation_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            with mock.patch("ordivon_studio.agent_surface.subprocess.run", return_value=mock.Mock(returncode=2)) as probe:
                state = dependency_status(root)
            self.assertFalse(state["js"]["ready"])
            self.assertEqual(state["js"]["reason"], "JS_DEPENDENCIES_STALE_OR_UNAVAILABLE")
            self.assertTrue(state["js"]["resolverChecked"])
            self.assertEqual(probe.call_args.args[0][:3], ["/root/tools/bin/pnpm", "exec", "node"])

    def test_missing_dependencies_compile_explicit_acquisition_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("pyproject.toml", "uv.lock", ".python-version"):
                (root / name).write_text("x\n", encoding="utf-8")
            js = dependency_proposal("js", root)
            python = dependency_proposal("python", root)
            resolve = dependency_proposal("resolve", root)
            self.assertTrue(js["effectRequired"])
            self.assertEqual(js["plan"]["executable"], "/root/tools/bin/pnpm")
            self.assertEqual(js["plan"]["args"], ["install", "--frozen-lockfile"])
            self.assertEqual(python["plan"]["executable"], "/usr/bin/python3")
            self.assertEqual(resolve["plan"]["args"], ["scripts/materialize-python.py", "--extra", "resolve"])

    def test_learning_and_production_context_are_owner_native_read_only_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "research/expression").mkdir(parents=True)
            (root / "research/expression/context.json").write_text(json.dumps({
                "creativeSystem": {
                    "learningPromotion": ["artifact-local"],
                    "twoSpeedLearning": {"boundary": "human typed"},
                    "culturalObservatory": {"creativeAlphaResearch": {
                        "authority": "r6",
                        "researchInstitutions": ["pristine-holdout"],
                        "oosDimensions": ["observer-class"],
                        "boundary": "typed",
                    }},
                }
            }), encoding="utf-8")
            prod = root / "productions/p1"
            prod.mkdir(parents=True)
            (prod / "production.json").write_text(json.dumps({
                "id": "p1", "title": "P1", "status": "review", "intent": "test", "audiences": ["agent"],
                "sourceBindings": [], "outputs": [], "sources": {"claims": "claims.json", "cognition": "cognition.md"}
            }), encoding="utf-8")
            (prod / "claims.json").write_text(json.dumps({"productionId": "p1", "claims": []}), encoding="utf-8")
            (prod / "cognition.md").write_text("# P1\n\n## LEARNING\n\nRetain exact evidence.\n", encoding="utf-8")
            production = execute_surface_action("studio_production_context", {"productionId": "p1"}, root=root)
            learning = execute_surface_action("studio_learning_context", {"currentProductionId": "p1"}, root=root)
        self.assertEqual(production["production"]["id"], "p1")
        self.assertEqual(learning["currentProductionId"], "p1")
        self.assertIn("Retain exact evidence", learning["retainedLearning"][0]["learning"] )

    def test_equipment_surface_reuses_truthful_proposal_not_a_second_registry(self) -> None:
        fake = {"ready": False, "blockers": ["AUTH_REQUIRED"]}
        with mock.patch("ordivon_studio.agent_surface.load_equipment_world", return_value={"equipment": []}), mock.patch(
            "ordivon_studio.agent_surface.propose_operation", return_value=fake
        ) as propose:
            result = execute_surface_action(
                "studio_equipment_propose",
                {"capability": "design.node.read", "equipmentId": "figma", "parameters": {}},
                root=Path("."),
            )
        self.assertEqual(result, fake)
        self.assertEqual(propose.call_args.kwargs["equipment_id"], "figma")
        self.assertTrue(propose.call_args.kwargs["local"])


if __name__ == "__main__":
    unittest.main()
