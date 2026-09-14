from __future__ import annotations
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TemporalDeployTests(unittest.TestCase):
    def test_canonical_worker_targets_production_cluster(self):
        text = (ROOT / "systemd/ordivon-agent-temporal-worker.service").read_text()
        self.assertIn("Production Temporal worker", text)
        self.assertIn("temporal-agent-automation/.venv/bin/python", text)
        self.assertIn("agent-automation-browserless.json", text)
        self.assertIn("--address 127.0.0.1:17233", text)
        self.assertIn("Requires=temporal.service", text)
        self.assertNotIn("--address 127.0.0.1:7233", text)
        self.assertNotIn("Xvfb", text)
        self.assertNotIn("chromium", text.lower())

    def test_transitional_worker_and_dev_server_units_are_removed(self):
        self.assertFalse((ROOT / "systemd/ordivon-agent-temporal-worker-green.service").exists())
        self.assertFalse((ROOT / "systemd/ordivon-temporal-agent-dev.service").exists())

    def test_deployer_owns_one_production_worker(self):
        text = (ROOT / "scripts/temporal_agent_automation_deploy.py").read_text()
        tree = ast.parse(text)
        constants = {}
        for node in tree.body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant)
            ):
                constants[node.targets[0].id] = node.value.value
        self.assertEqual(constants.get("PRODUCTION_ADDRESS"), "127.0.0.1:17233")
        self.assertEqual(constants.get("WORKER"), "ordivon-agent-temporal-worker.service")
        self.assertEqual(constants.get("PRODUCTION_SERVER"), "temporal.service")
        self.assertNotIn("BLUE_", text)
        self.assertNotIn("GREEN_", text)
        self.assertNotIn("127.0.0.1:7233", text)


if __name__ == "__main__":
    unittest.main()
