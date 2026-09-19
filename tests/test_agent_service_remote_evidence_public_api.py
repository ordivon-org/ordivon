from __future__ import annotations

import unittest

import agent_service
from agent_service.remote_evidence import (
    ClaimAwareAssignmentPlanner,
    ClaimAwareDeliveryCoordinator,
    RemoteArtifactEvidenceResolver,
    RemoteTaskCompletionReconciler,
    TaskExecutionClaimStore,
)


class AgentServiceRemoteEvidencePublicApiTests(unittest.TestCase):
    def test_package_exports_r11_execution_and_remote_evidence_bricks(self) -> None:
        self.assertFalse(hasattr(agent_service, "AgentServiceR11"))
        self.assertIs(agent_service.TaskExecutionClaimStore, TaskExecutionClaimStore)
        self.assertIs(
            agent_service.ClaimAwareAssignmentPlanner, ClaimAwareAssignmentPlanner
        )
        self.assertIs(
            agent_service.ClaimAwareDeliveryCoordinator, ClaimAwareDeliveryCoordinator
        )
        self.assertFalse(hasattr(agent_service, "RemoteArtifactReader"))
        self.assertIs(
            agent_service.RemoteArtifactEvidenceResolver, RemoteArtifactEvidenceResolver
        )
        self.assertFalse(hasattr(agent_service, "RemoteTaskVerificationStore"))
        self.assertIs(
            agent_service.RemoteTaskCompletionReconciler, RemoteTaskCompletionReconciler
        )


if __name__ == "__main__":
    unittest.main()
