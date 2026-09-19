from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_service
import agent_service.goals as goals
from tests.agent_service_test_support import open_current


class GoalTaskGraphFacadeRetiredTests(unittest.TestCase):
    def test_goal_task_graph_brand_is_absent(self) -> None:
        self.assertFalse(hasattr(goals, "GoalTaskGraph"))
        self.assertFalse(hasattr(agent_service, "GoalTaskGraph"))

    def test_current_service_exposes_real_graph_components_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            service = open_current(Path(td) / "service.db")
            self.addCleanup(service.close)
            self.assertFalse(hasattr(service, "task_graph"))
            self.assertTrue(hasattr(service, "goal_task_links"))
            self.assertTrue(hasattr(service, "task_dependencies"))
            self.assertTrue(hasattr(service, "task_readiness"))
            self.assertTrue(hasattr(service, "goal_graph_guard"))


if __name__ == "__main__":
    unittest.main()


class StandardLibraryDagTests(unittest.TestCase):
    def test_task_dependency_store_does_not_implement_custom_reachability(self) -> None:
        self.assertFalse(hasattr(goals.TaskDependencyStore, "_reachable"))

    def test_three_hop_cycle_is_rejected(self) -> None:
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
