from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

import agent_service
from agent_service import effect_authority
from agent_service.schema_migrations import apply_schema_migrations

ROOT = Path(__file__).resolve().parents[1]


class EffectAuthorizationReceiptEliminationR10Tests(unittest.TestCase):
    def test_specialized_effect_authorization_decision_authority_is_deleted(self) -> None:
        self.assertFalse(hasattr(effect_authority, "EffectAuthorizationDecision"))
        self.assertFalse(hasattr(effect_authority, "EffectAuthorizationDecisionStore"))
        self.assertFalse(hasattr(agent_service, "EffectAuthorizationDecision"))
        self.assertFalse(hasattr(agent_service, "EffectAuthorizationDecisionStore"))

        source = (ROOT / "agent_service" / "effect_authority.py").read_text(encoding="utf-8")
        self.assertNotIn("CREATE TABLE IF NOT EXISTS effect_authorization_decisions", source)
        self.assertNotIn("effect_authorization_records", source)

    def test_legacy_effect_authorization_table_fails_closed(self) -> None:
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.execute("CREATE TABLE effect_authorization_decisions(id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "legacy effect_authorization_decisions"):
            apply_schema_migrations(connection)


if __name__ == "__main__":
    unittest.main()
