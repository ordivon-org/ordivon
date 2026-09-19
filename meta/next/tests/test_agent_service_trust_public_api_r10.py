from __future__ import annotations

import unittest

import agent_service
from agent_service.trust import (
    AuditEnvelopeProjector,
    CredentialReferenceStore,
    IdentityProofCoordinator,
    RemoteCorrelationReconciler,
)


class AgentServiceTrustPublicApiR10Tests(unittest.TestCase):
    def test_package_exports_r10_trust_and_remote_bricks(self) -> None:
        self.assertFalse(hasattr(agent_service, "AgentServiceR10"))
        self.assertIs(agent_service.CredentialReferenceStore, CredentialReferenceStore)
        self.assertFalse(hasattr(agent_service, "IdentityProofAdapter"))
        self.assertFalse(hasattr(agent_service, "IdentityProofRecordStore"))
        self.assertIs(agent_service.IdentityProofCoordinator, IdentityProofCoordinator)
        self.assertFalse(hasattr(agent_service, "RemoteDeliveryObserver"))
        self.assertFalse(hasattr(agent_service, "RemoteDeliveryObservationStore"))
        self.assertIs(agent_service.RemoteCorrelationReconciler, RemoteCorrelationReconciler)
        self.assertIs(agent_service.AuditEnvelopeProjector, AuditEnvelopeProjector)


if __name__ == "__main__":
    unittest.main()
