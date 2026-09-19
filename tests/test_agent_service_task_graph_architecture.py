from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_service.goals as goals
from tests.agent_service_test_support import open_current


class TaskGraphArchitectureTests(unittest.TestCase):
    def test_service_exposes_explicit_graph_components(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            service = open_current(Path(td) / "service.db")
            self.addCleanup(service.close)
            self.assertTrue(hasattr(service, "goal_task_links"))
            self.assertTrue(hasattr(service, "task_dependencies"))
            self.assertTrue(hasattr(service, "task_readiness"))
            self.assertTrue(hasattr(service, "goal_graph_guard"))

    def test_dependency_store_uses_standard_graph_cycle_detection_boundary(
        self,
    ) -> None:
        self.assertFalse(hasattr(goals.TaskDependencyStore, "_reachable"))

        with tempfile.TemporaryDirectory() as td:
            service = open_current(Path(td) / "service.db")
            self.addCleanup(service.close)
            definition = service.definitions.create("dag")
            revision = service.revisions.create(definition.id, {"kind": "dag"})
            goal = service.goals.create("dag")
            tasks = [
                service.tasks.create(
                    description=name,
                    required_revision_id=revision.id,
                    execution={"kind": "noop"},
                    acceptance={"kind": "stdout_contains", "value": "ok"},
                )
                for name in ("a", "b", "c")
            ]
            for task in tasks:
                service.goal_task_links.attach(goal.id, task.id)
            a, b, c = tasks
            service.task_dependencies.add(b.id, a.id)
            service.task_dependencies.add(c.id, b.id)
            with self.assertRaisesRegex(ValueError, "cycle"):
                service.task_dependencies.add(a.id, c.id)


if __name__ == "__main__":
    unittest.main()
