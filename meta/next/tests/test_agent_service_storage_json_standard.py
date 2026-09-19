from __future__ import annotations

from tests.agent_service_test_support import open_current

import tempfile
import unittest
from pathlib import Path

from agent_service.slice1 import ProviderObservation
from agent_service.task_runtime import RuntimeJobObservation, RuntimeJobRef


class Carrier:
    def ensure(self, placement_id, agent_instance_id, revision_id):
        return None
    def retire(self, placement_id, agent_instance_id):
        return None
    def observe(self, placement_id):
        return ProviderObservation(placement_id, "UNKNOWN", None)


class Runtime:
    def submit(self, client_request_id, execution):
        return RuntimeJobRef(job_id="job:test")
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


class StorageJsonStandardTests(unittest.TestCase):
    def test_custom_canonical_json_helpers_are_retired(self):
        root = Path("agent_service")
        offenders = []
        for path in root.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "def _canonical_json(" in text:
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_storage_roundtrip_preserves_json_number_type(self):
        with tempfile.TemporaryDirectory() as td:
            service = open_current(
                Path(td) / "service.db",
                carrier_adapter=Carrier(),
                runtime_adapter=Runtime(),
            )
            self.addCleanup(service.close)
            d = service.definitions.create("storage-json")
            r = service.revisions.create(d.id, {"kind": "test"})
            task = service.tasks.create(
                description="preserve json scalar representation",
                required_revision_id=r.id,
                execution={"threshold": 1.0},
                acceptance={"kind": "stdout_contains", "value": "ok"},
            )
            self.assertIsInstance(task.execution["threshold"], float)
            reread = service.tasks.get(task.id)
            self.assertIsInstance(reread.execution["threshold"], float)

    def test_non_json_values_remain_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            service = open_current(
                Path(td) / "service.db",
                carrier_adapter=Carrier(),
                runtime_adapter=Runtime(),
            )
            self.addCleanup(service.close)
            d = service.definitions.create("storage-json")
            r = service.revisions.create(d.id, {"kind": "test"})
            with self.assertRaises(TypeError):
                service.tasks.create(
                    description="reject non-json",
                    required_revision_id=r.id,
                    execution={"bad": {1, 2}},
                    acceptance={"kind": "stdout_contains", "value": "ok"},
                )


if __name__ == "__main__":
    unittest.main()
