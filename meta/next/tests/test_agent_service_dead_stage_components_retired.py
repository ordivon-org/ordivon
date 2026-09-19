from __future__ import annotations

import unittest

import agent_service
from agent_service import delivery, task_runtime


class DeadStageComponentsRetiredTests(unittest.TestCase):
    def test_obsolete_stage_components_are_absent(self) -> None:
        for module, name in (
            (task_runtime, "AssignmentPlanner"),
            (task_runtime, "SemanticVerifier"),
            (task_runtime, "AssignmentActivator"),
            (delivery, "DeliveryCoordinator"),
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(module, name))
                self.assertFalse(hasattr(agent_service, name))


if __name__ == "__main__":
    unittest.main()
