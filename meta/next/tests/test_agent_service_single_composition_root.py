from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import agent_service
from agent_service.slice1 import ProviderObservation
from agent_service.task_runtime import RuntimeJobObservation, RuntimeJobRef


class Carrier:
    def ensure(self, placement_id, agent_instance_id, revision_id):
        return None
    def retire(self, placement_id, agent_instance_id):
        return None
    def observe(self, placement_id):
        return ProviderObservation(placement_id, "READY", "test://ready")


class Runtime:
    def submit(self, client_request_id, execution):
        return RuntimeJobRef(job_id=f"job:{client_request_id}")
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
        raise AssertionError("not used")


class SingleCompositionRootTests(unittest.TestCase):
    def test_package_exposes_one_current_agent_service_root(self) -> None:
        self.assertTrue(hasattr(agent_service, "open_agent_service"))

    def test_current_root_constructs_final_graph_without_version_wrapper_chain(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            service = agent_service.open_agent_service(
                Path(td) / "service.db",
                carrier_adapter=Carrier(),
                runtime_adapter=Runtime(),
                artifact_reader=ArtifactReader(),
                delivery_adapters={},
            )
            self.addCleanup(service.close)

            for name in (
                "definitions", "revisions", "instances", "placements", "events",
                "reconciler", "tasks", "assignments", "execution_activator", "completion",
                "goals", "task_graph", "goal_planner", "identities", "sessions",
                "delegations", "a2a_cards", "transport_bindings", "routes",
                "credential_references", "identity_proofs", "remote_reconciler",
                "execution_claims", "quiescence", "replay_safety", "claim_transfers",
                "failover", "transport_credentials", "credential_headers", "delivery",
            ):
                self.assertTrue(hasattr(service, name), name)

            for name in (
                "_placement", "_r5", "_r6", "_r7", "_r8", "_r9", "_r10",
                "_r11", "_r12", "_r13", "_r14", "_r15",
            ):
                self.assertFalse(hasattr(service, name), name)

    def test_current_root_can_admit_and_reconcile_instance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            service = agent_service.open_agent_service(
                Path(td) / "service.db",
                carrier_adapter=Carrier(),
                runtime_adapter=Runtime(),
                artifact_reader=ArtifactReader(),
                delivery_adapters={},
            )
            self.addCleanup(service.close)
            definition = service.definitions.create("root")
            revision = service.revisions.create(definition.id, {"kind": "test"})
            instance = service.instances.create("request:root", revision.id)
            service.reconciler.reconcile(instance.id)
            self.assertEqual(service.instances.get(instance.id).state, "READY")


if __name__ == "__main__":
    unittest.main()
