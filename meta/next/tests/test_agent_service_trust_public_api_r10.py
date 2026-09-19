from __future__ import annotations

import unittest

import agent_service
from agent_service.trust import (
    AgentServiceR10,
    AuditEnvelopeProjector,
    CredentialReferenceStore,
    IdentityProofAdapter,
    IdentityProofCoordinator,
    IdentityProofRecordStore,
    RemoteCorrelationReconciler,
    RemoteDeliveryObserver,
)


class AgentServiceTrustPublicApiR10Tests(unittest.TestCase):
    def test_package_exports_r10_trust_and_remote_bricks(self) -> None:
        self.assertIs(agent_service.AgentServiceR10, AgentServiceR10)
        self.assertIs(agent_service.CredentialReferenceStore, CredentialReferenceStore)
        self.assertIs(agent_service.IdentityProofAdapter, IdentityProofAdapter)
        self.assertIs(agent_service.IdentityProofRecordStore, IdentityProofRecordStore)
        self.assertIs(agent_service.IdentityProofCoordinator, IdentityProofCoordinator)
        self.assertIs(agent_service.RemoteDeliveryObserver, RemoteDeliveryObserver)
        self.assertFalse(hasattr(agent_service, "RemoteDeliveryObservationStore"))
        self.assertIs(agent_service.RemoteCorrelationReconciler, RemoteCorrelationReconciler)
        self.assertIs(agent_service.AuditEnvelopeProjector, AuditEnvelopeProjector)


if __name__ == "__main__":
    unittest.main()
