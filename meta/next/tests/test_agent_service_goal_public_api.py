from __future__ import annotations

import unittest

import agent_service
from agent_service.goals import (
    BoardProjectionReceipt,
    GoalGraphMutationGuard,
    GoalStore,
    GoalTaskLinkStore,
    TaskDependencyStore,
    TaskReadinessProjector,
)
from agent_service.host_board import HostBoardMcpAdapter


class AgentServiceGoalPublicApiTests(unittest.TestCase):
    def test_package_exports_goal_dag_and_board_bricks(self) -> None:
        self.assertFalse(hasattr(agent_service, "AgentServiceR7"))
        self.assertIs(agent_service.GoalStore, GoalStore)
        self.assertIs(agent_service.GoalTaskLinkStore, GoalTaskLinkStore)
        self.assertIs(agent_service.TaskDependencyStore, TaskDependencyStore)
        self.assertIs(agent_service.TaskReadinessProjector, TaskReadinessProjector)
        self.assertIs(agent_service.GoalGraphMutationGuard, GoalGraphMutationGuard)
        self.assertFalse(hasattr(agent_service, "BoardAdapter"))
        self.assertIs(agent_service.BoardProjectionReceipt, BoardProjectionReceipt)
        self.assertIs(agent_service.HostBoardMcpAdapter, HostBoardMcpAdapter)


if __name__ == "__main__":
    unittest.main()
