from __future__ import annotations

import unittest
from pathlib import Path

from agent_service import delivery

ROOT = Path(__file__).resolve().parents[1]


class PolicyReceiptEliminationR8Tests(unittest.TestCase):
    def test_specialized_policy_decision_authority_is_deleted(self) -> None:
        self.assertFalse(hasattr(delivery, "PolicyDecision"))
        self.assertFalse(hasattr(delivery, "PolicyDecisionStore"))

        source = (ROOT / "agent_service" / "delivery.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS policy_decisions", source)
        self.assertNotIn("REFERENCES policy_decisions", source)

    def test_transport_binding_owns_only_policy_receipt_snapshot(self) -> None:
        fields = set(delivery.TransportBinding.__dataclass_fields__)
        self.assertNotIn("policy_decision_id", fields)
        self.assertTrue(
            {"policy_receipt_id", "policy_revision", "granted_permissions"}.issubset(fields)
        )


if __name__ == "__main__":
    unittest.main()
