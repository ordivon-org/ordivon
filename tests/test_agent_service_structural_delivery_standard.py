from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_service
from agent_service.delivery import DeliveryObservation, PolicyObservation
from agent_service.evidence import RuntimeArtifactPayload
from agent_service.slice1 import ProviderObservation
from agent_service.task_runtime import RuntimeJobObservation, RuntimeJobRef
from tests.agent_service_test_support import open_current


class Carrier:
    def ensure(self, placement_id, agent_instance_id, revision_id):
        return None

    def retire(self, placement_id, agent_instance_id):
        return None

    def observe(self, placement_id):
        return ProviderObservation(placement_id, "UNKNOWN", None)


class Runtime:
    def submit(self, client_request_id, execution):
        return RuntimeJobRef(job_id="job:plain")

    def observe(self, job_id):
        return RuntimeJobObservation(
            job_id=job_id,
            status="working",
            execution_terminal=False,
            delivery_disposition="committed",
            semantic_completion_evaluated=False,
            stdout_tail="",
            stderr_tail="",
            artifacts=(),
        )


class ArtifactReader:
    def read(self, job_id, artifact_id):
        return RuntimeArtifactPayload(
            job_id=job_id,
            artifact_id=artifact_id,
            digest="sha256:" + "a" * 64,
            content="",
        )


class PlainPolicy:
    def evaluate(self, request):
        return PolicyObservation(
            allowed=True,
            reason=None,
            policy_revision="policy:test",
            granted_permissions=(),
        )


class PlainDelivery:
    def send(self, *, delivery_request_id, binding, envelope):
        return DeliveryObservation(
            admission="committed",
            status="accepted",
            provider_request_id="provider:test",
        )


class StructuralDeliveryStandardTests(unittest.TestCase):
    def test_policy_and_delivery_contracts_are_not_public_nominal_types(self):
        self.assertFalse(hasattr(agent_service, "PolicyAdapter"))
        self.assertFalse(hasattr(agent_service, "DeliveryAdapter"))

    def test_plain_policy_and_delivery_providers_are_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            service = open_current(
                Path(td) / "service.db",
                carrier_adapter=Carrier(),
                runtime_adapter=Runtime(),
                artifact_reader=ArtifactReader(),
                policy_adapter=PlainPolicy(),
                delivery_adapters={"mcp": PlainDelivery()},
            )
            service.close()

    def test_incomplete_policy_fails_before_database_creation(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "service.db"
            with self.assertRaises(TypeError):
                open_current(
                    db,
                    carrier_adapter=Carrier(),
                    runtime_adapter=Runtime(),
                    artifact_reader=ArtifactReader(),
                    policy_adapter=object(),
                )
            self.assertFalse(db.exists())

    def test_incomplete_delivery_provider_fails_before_database_creation(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "service.db"
            with self.assertRaises(TypeError):
                open_current(
                    db,
                    carrier_adapter=Carrier(),
                    runtime_adapter=Runtime(),
                    artifact_reader=ArtifactReader(),
                    delivery_adapters={"mcp": object()},
                )
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
