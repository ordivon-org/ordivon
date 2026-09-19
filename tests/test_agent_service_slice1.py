from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_service.slice1 import ProviderObservation
from tests.agent_service_test_support import open_current


class RecordingHostAdapter:
    def __init__(self) -> None:
        self.ensure_calls: list[str] = []
        self.retire_calls: list[str] = []
        self.observations: dict[str, ProviderObservation] = {}
        self.before_ensure = None

    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        if self.before_ensure is not None:
            self.before_ensure(placement_id)
        self.ensure_calls.append(placement_id)

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        self.retire_calls.append(placement_id)

    def observe(self, placement_id: str) -> ProviderObservation:
        return self.observations.get(
            placement_id,
            ProviderObservation(placement_id=placement_id, state="UNKNOWN", evidence_ref=None),
        )


class AgentServiceSlice1Tests(unittest.TestCase):
    def _open(self, db: Path, host: RecordingHostAdapter | None = None) -> object:
        service = open_current(db, carrier_adapter=host or RecordingHostAdapter())
        self.addCleanup(service.close)
        return service

    def test_revision_is_immutable_and_historical_revision_remains_resolvable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            definition = service.definitions.create("research-agent")

            a1 = service.revisions.create(definition.id, {"harness": "h1", "plugins": ["research"]})
            a2 = service.revisions.create(definition.id, {"harness": "h2", "plugins": ["research", "web"]})

            self.assertNotEqual(a1.id, a2.id)
            self.assertEqual(service.revisions.get(a1.id), a1)
            self.assertEqual(service.revisions.get(a2.id), a2)
            self.assertEqual(a1.spec["harness"], "h1")

    def test_birth_is_idempotent_for_one_birth_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            definition = service.definitions.create("research-agent")
            revision = service.revisions.create(definition.id, {"harness": "h1"})

            first = service.instances.create("request-001", revision.id)
            second = service.instances.create("request-001", revision.id)

            self.assertEqual(first.id, second.id)
            self.assertEqual(len(service.instances.list_all()), 1)
            self.assertEqual(len(service.placements.list_all()), 1)
            self.assertEqual(first.state, "PROVISIONING")

    def test_desired_placement_is_durable_before_host_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = RecordingHostAdapter()
            service = self._open(Path(tmp) / "service.db", host)
            definition = service.definitions.create("research-agent")
            revision = service.revisions.create(definition.id, {"harness": "h1"})
            instance = service.instances.create("request-001", revision.id)
            placement = service.placements.get_by_instance(instance.id)
            self.assertIsNotNone(placement)

            def assert_placement_already_committed(placement_id: str) -> None:
                committed = service.placements.get(placement_id)
                self.assertEqual(committed.desired_state, "READY")

            host.before_ensure = assert_placement_already_committed
            service.reconciler.reconcile(instance.id)

            self.assertEqual(host.ensure_calls, [placement.id])

    def test_ready_requires_positive_provider_observation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = RecordingHostAdapter()
            service = self._open(Path(tmp) / "service.db", host)
            definition = service.definitions.create("research-agent")
            revision = service.revisions.create(definition.id, {"harness": "h1"})
            instance = service.instances.create("request-001", revision.id)
            placement = service.placements.get_by_instance(instance.id)
            assert placement is not None

            service.reconciler.reconcile(instance.id)
            self.assertEqual(service.instances.get(instance.id).state, "PROVISIONING")
            self.assertEqual(service.placements.get(placement.id).observed_state, "UNKNOWN")

            host.observations[placement.id] = ProviderObservation(
                placement_id=placement.id,
                state="READY",
                evidence_ref="host://carrier/agent-1/ready",
            )
            service.reconciler.reconcile(instance.id)

            self.assertEqual(service.instances.get(instance.id).state, "READY")
            self.assertEqual(service.placements.get(placement.id).observed_state, "READY")

    def test_restart_recovers_birth_without_duplicate_agent_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            first_host = RecordingHostAdapter()
            first = self._open(db, first_host)
            definition = first.definitions.create("research-agent")
            revision = first.revisions.create(definition.id, {"harness": "h1"})
            instance = first.instances.create("request-001", revision.id)
            placement = first.placements.get_by_instance(instance.id)
            assert placement is not None
            first.close()

            second_host = RecordingHostAdapter()
            second_host.observations[placement.id] = ProviderObservation(
                placement_id=placement.id,
                state="READY",
                evidence_ref="host://carrier/agent-1/ready",
            )
            second = self._open(db, second_host)
            recovered = second.instances.create("request-001", revision.id)
            second.reconciler.reconcile(recovered.id)

            self.assertEqual(recovered.id, instance.id)
            self.assertEqual(len(second.instances.list_all()), 1)
            self.assertEqual(second.instances.get(instance.id).state, "READY")

    def test_birth_request_cannot_be_replayed_with_different_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            definition = service.definitions.create("research-agent")
            a1 = service.revisions.create(definition.id, {"harness": "h1"})
            a2 = service.revisions.create(definition.id, {"harness": "h2"})
            service.instances.create("request-001", a1.id)

            with self.assertRaises(ValueError):
                service.instances.create("request-001", a2.id)

    def test_ready_state_and_ready_event_commit_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = RecordingHostAdapter()
            service = self._open(Path(tmp) / "service.db", host)
            definition = service.definitions.create("research-agent")
            revision = service.revisions.create(definition.id, {"harness": "h1"})
            instance = service.instances.create("request-001", revision.id)
            placement = service.placements.get_by_instance(instance.id)
            assert placement is not None
            host.observations[placement.id] = ProviderObservation(
                placement_id=placement.id,
                state="READY",
                evidence_ref="host://carrier/agent-1/ready",
            )

            with patch.object(service.events, "append_in_transaction", side_effect=RuntimeError("event write failed")):
                with self.assertRaises(RuntimeError):
                    service.reconciler.reconcile(instance.id)

            self.assertEqual(service.instances.get(instance.id).state, "PROVISIONING")
            self.assertEqual(
                [event.event_type for event in service.events.list_for("AgentInstance", instance.id)],
                ["AGENT_INSTANCE_ADMITTED"],
            )

    def test_lost_provider_evidence_revokes_ready_and_records_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = RecordingHostAdapter()
            service = self._open(Path(tmp) / "service.db", host)
            definition = service.definitions.create("research-agent")
            revision = service.revisions.create(definition.id, {"harness": "h1"})
            instance = service.instances.create("request-001", revision.id)
            placement = service.placements.get_by_instance(instance.id)
            assert placement is not None
            host.observations[placement.id] = ProviderObservation(
                placement_id=placement.id, state="READY", evidence_ref="host://ready"
            )
            service.reconciler.reconcile(instance.id)

            host.observations[placement.id] = ProviderObservation(
                placement_id=placement.id, state="UNKNOWN", evidence_ref=None
            )
            service.reconciler.reconcile(instance.id)

            self.assertEqual(service.instances.get(instance.id).state, "PROVISIONING")
            self.assertEqual(service.placements.get(placement.id).observed_state, "UNKNOWN")
            self.assertEqual(
                [event.event_type for event in service.events.list_for("AgentInstance", instance.id)],
                ["AGENT_INSTANCE_ADMITTED", "AGENT_READY", "AGENT_READINESS_LOST"],
            )

    def test_service_events_preserve_semantic_transition_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = RecordingHostAdapter()
            service = self._open(Path(tmp) / "service.db", host)
            definition = service.definitions.create("research-agent")
            revision = service.revisions.create(definition.id, {"harness": "h1"})
            instance = service.instances.create("request-001", revision.id)
            placement = service.placements.get_by_instance(instance.id)
            assert placement is not None
            host.observations[placement.id] = ProviderObservation(
                placement_id=placement.id,
                state="READY",
                evidence_ref="host://carrier/agent-1/ready",
            )
            service.reconciler.reconcile(instance.id)

            event_types = [event.event_type for event in service.events.list_for("AgentInstance", instance.id)]
            self.assertEqual(event_types, ["AGENT_INSTANCE_ADMITTED", "AGENT_READY"])


if __name__ == "__main__":
    unittest.main()
