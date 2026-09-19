from __future__ import annotations

import unittest

import agent_service
from agent_service.local_effect_readers import (
    BrowserlessTurnEffectCoordinate,
    BrowserlessTurnEffectLedgerReader,
)
from agent_service.transport_credentials import (
    AgentServiceR14,
    BoundCredentialHeaderProvider,
    CredentialHeaderMaterial,
    TransportCredentialBindingCoordinator,
)


class AgentServiceR14PublicApiTests(unittest.TestCase):
    def test_package_exports_r14_bricks(self) -> None:
        self.assertIs(agent_service.AgentServiceR14, AgentServiceR14)
        self.assertFalse(hasattr(agent_service, "TransportCredentialBindingStore"))
        self.assertIs(
            agent_service.TransportCredentialBindingCoordinator,
            TransportCredentialBindingCoordinator,
        )
        self.assertIs(agent_service.CredentialHeaderMaterial, CredentialHeaderMaterial)
        self.assertFalse(hasattr(agent_service, "CredentialMaterialProvider"))
        self.assertIs(
            agent_service.BoundCredentialHeaderProvider,
            BoundCredentialHeaderProvider,
        )
        self.assertIs(
            agent_service.BrowserlessTurnEffectCoordinate,
            BrowserlessTurnEffectCoordinate,
        )
        self.assertIs(
            agent_service.BrowserlessTurnEffectLedgerReader,
            BrowserlessTurnEffectLedgerReader,
        )


if __name__ == "__main__":
    unittest.main()
