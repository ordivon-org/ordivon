from __future__ import annotations

import unittest

from scripts.check_agent_service_graph_identity_r1 import validate


class AgentServiceGraphIdentityR1Tests(unittest.TestCase):
    def test_frozen_graph_history_has_no_hard_node_identity_collision(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["nodeCount"], 92)
        self.assertEqual(result["nodes"]["N40"], "CapabilityAdvertisementStore")
        self.assertEqual(result["nodes"]["N42"], "DelegationEnvelopeStore")
        self.assertEqual(result["nodes"]["N44"], "AgentInterfaceAdvertisementStore")
        self.assertEqual(result["nodes"]["N48"], "TransportBindingStore")
        self.assertEqual(result["nodes"]["N86"], "AgentServiceR14")
        self.assertEqual(result["nodes"]["N90"], "AgentServiceR15")
        self.assertEqual(result["nodes"]["N91"], "AgentServiceReadOnlyMcpFacade")
        self.assertEqual(result["nodes"]["N92"], "AgentServiceCanaryDeployment")


if __name__ == "__main__":
    unittest.main()
