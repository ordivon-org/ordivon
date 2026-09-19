from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_service
from agent_service.evidence import RuntimeArtifactPayload
from agent_service.runtime_mcp import RuntimeMcpAdapter, RuntimeMcpArtifactReader
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


class PlainRuntime:
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


class PlainArtifactReader:
    def read(self, job_id, artifact_id):
        return RuntimeArtifactPayload(
            job_id=job_id,
            artifact_id=artifact_id,
            digest="sha256:" + "a" * 64,
            content="",
        )


class StructuralRuntimeStandardTests(unittest.TestCase):
    def test_runtime_contracts_are_not_nominal_public_types(self):
        self.assertFalse(hasattr(agent_service, "RuntimeAdapter"))
        self.assertFalse(hasattr(agent_service, "RuntimeArtifactReader"))
        self.assertEqual(RuntimeMcpAdapter.__bases__, (object,))
        self.assertEqual(RuntimeMcpArtifactReader.__bases__, (object,))

    def test_plain_runtime_is_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            service = open_current(
                Path(td) / "service.db",
                carrier_adapter=Carrier(),
                runtime_adapter=PlainRuntime(),
            )
            service.close()

    def test_incomplete_runtime_fails_before_database_creation(self):
        class MissingObserve:
            def submit(self, client_request_id, execution):
                return RuntimeJobRef(job_id="job:x")

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "service.db"
            with self.assertRaises(TypeError):
                open_current(
                    db,
                    carrier_adapter=Carrier(),
                    runtime_adapter=MissingObserve(),
                )
            self.assertFalse(db.exists())

    def test_plain_artifact_reader_is_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            service = open_current(
                Path(td) / "service.db",
                carrier_adapter=Carrier(),
                runtime_adapter=PlainRuntime(),
                artifact_reader=PlainArtifactReader(),
            )
            service.close()

    def test_incomplete_artifact_reader_fails_before_database_creation(self):
        class MissingRead:
            pass

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "service.db"
            with self.assertRaises(TypeError):
                open_current(
                    db,
                    carrier_adapter=Carrier(),
                    runtime_adapter=PlainRuntime(),
                    artifact_reader=MissingRead(),
                )
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
