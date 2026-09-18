from __future__ import annotations

import unittest

import agent_service
from agent_service.remote_evidence import (
    AgentServiceR11,
    ClaimAwareAssignmentPlanner,
    ClaimAwareDeliveryCoordinator,
    RemoteArtifactEvidenceResolver,
    RemoteArtifactReader,
    RemoteTaskCompletionReconciler,
    RemoteTaskVerificationStore,
    TaskExecutionClaimStore,
)


class AgentServiceRemoteEvidencePublicApiR11Tests(unittest.TestCase):
    def test_package_exports_r11_execution_and_remote_evidence_bricks(self) -> None:
        self.assertIs(agent_service.AgentServiceR11, AgentServiceR11)
        self.assertIs(agent_service.TaskExecutionClaimStore, TaskExecutionClaimStore)
        self.assertIs(agent_service.ClaimAwareAssignmentPlanner, ClaimAwareAssignmentPlanner)
        self.assertIs(agent_service.ClaimAwareDeliveryCoordinator, ClaimAwareDeliveryCoordinator)
        self.assertIs(agent_service.RemoteArtifactReader, RemoteArtifactReader)
        self.assertIs(agent_service.RemoteArtifactEvidenceResolver, RemoteArtifactEvidenceResolver)
        self.assertIs(agent_service.RemoteTaskVerificationStore, RemoteTaskVerificationStore)
        self.assertIs(agent_service.RemoteTaskCompletionReconciler, RemoteTaskCompletionReconciler)


if __name__ == "__main__":
    unittest.main()
