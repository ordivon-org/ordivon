from __future__ import annotations

from tests.agent_service_test_support import open_current

import sqlite3
import tempfile
import unittest
from pathlib import Path

from agent_service.slice1 import ProviderObservation


class ReadyCarrier:
    def ensure(
        self, placement_id: str, agent_instance_id: str, revision_id: str
    ) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(
            placement_id=placement_id,
            state="READY",
            evidence_ref="test://ready",
        )


class AgentInstanceAdmissionStandardTests(unittest.TestCase):
    def test_instance_create_is_idempotent_and_birth_facade_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = open_current(
                Path(tmp) / "service.db", carrier_adapter=ReadyCarrier()
            )
            self.addCleanup(service.close)
            definition = service.definitions.create("researcher")
            revision = service.revisions.create(definition.id, {"harness": "test"})

            first = service.instances.create("request:researcher", revision.id)
            replay = service.instances.create("request:researcher", revision.id)

            self.assertEqual(first.id, replay.id)
            self.assertEqual(first.client_request_id, "request:researcher")
            placement = service.placements.get_by_instance(first.id)
            self.assertIsNotNone(placement)
            self.assertEqual(placement.desired_state, "READY")
            self.assertFalse(hasattr(service, "birth"))
            self.assertEqual(
                [
                    event.event_type
                    for event in service.events.list_for("AgentInstance", first.id)
                ],
                ["AGENT_INSTANCE_ADMITTED"],
            )

    def test_same_client_request_cannot_change_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = open_current(
                Path(tmp) / "service.db", carrier_adapter=ReadyCarrier()
            )
            self.addCleanup(service.close)
            definition = service.definitions.create("researcher")
            first_revision = service.revisions.create(definition.id, {"v": 1})
            second_revision = service.revisions.create(definition.id, {"v": 2})
            service.instances.create("request:researcher", first_revision.id)

            with self.assertRaises(ValueError):
                service.instances.create("request:researcher", second_revision.id)


class AgentInstanceLegacySchemaMigrationTests(unittest.TestCase):
    def test_open_renames_legacy_request_column_without_losing_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "service.db"
            db = sqlite3.connect(db_path)
            db.executescript(
                """
                CREATE TABLE agent_definitions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at_ns INTEGER NOT NULL
                );
                CREATE TABLE agent_revisions (
                    id TEXT PRIMARY KEY,
                    definition_id TEXT NOT NULL REFERENCES agent_definitions(id),
                    spec_json TEXT NOT NULL,
                    created_at_ns INTEGER NOT NULL
                );
                CREATE TABLE agent_instances (
                    id TEXT PRIMARY KEY,
                    birth_request_id TEXT NOT NULL UNIQUE,
                    revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
                    state TEXT NOT NULL,
                    created_at_ns INTEGER NOT NULL
                );
                CREATE TABLE desired_placements (
                    id TEXT PRIMARY KEY,
                    agent_instance_id TEXT NOT NULL UNIQUE REFERENCES agent_instances(id),
                    desired_state TEXT NOT NULL,
                    observed_state TEXT NOT NULL,
                    evidence_ref TEXT,
                    created_at_ns INTEGER NOT NULL,
                    updated_at_ns INTEGER NOT NULL
                );
                CREATE TABLE service_events (
                    id TEXT PRIMARY KEY,
                    aggregate_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at_ns INTEGER NOT NULL,
                    UNIQUE(aggregate_type, aggregate_id, sequence)
                );
                INSERT INTO agent_definitions VALUES ('adef_legacy', 'legacy', 1);
                INSERT INTO agent_revisions VALUES ('arev_legacy', 'adef_legacy', '{}', 2);
                INSERT INTO agent_instances VALUES (
                    'ainst_legacy', 'request:legacy', 'arev_legacy', 'PROVISIONING', 3
                );
                """
            )
            db.commit()
            db.close()

            service = open_current(db_path, carrier_adapter=ReadyCarrier())
            self.addCleanup(service.close)

            columns = {
                row["name"]
                for row in service._connection.execute(
                    "PRAGMA table_info(agent_instances)"
                )
            }
            self.assertIn("client_request_id", columns)
            self.assertNotIn("birth_request_id", columns)
            recovered = service.instances.get("ainst_legacy")
            self.assertEqual(recovered.client_request_id, "request:legacy")


if __name__ == "__main__":
    unittest.main()
