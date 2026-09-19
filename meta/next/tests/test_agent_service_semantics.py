from __future__ import annotations

from tests.agent_service_test_support import open_current

import tempfile
import unittest
from pathlib import Path

from agent_service.evidence import RuntimeArtifactPayload
from agent_service.slice1 import ProviderObservation
from agent_service.task_runtime import RuntimeJobObservation, RuntimeJobRef


class ReadyCarrier:
    def ensure(
        self, placement_id: str, agent_instance_id: str, revision_id: str
    ) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(
            placement_id=placement_id, state="READY", evidence_ref="test://ready"
        )


class FakeRuntime:
    def submit(self, client_request_id: str, execution: dict) -> RuntimeJobRef:
        return RuntimeJobRef(job_id=f"job:{client_request_id}")

    def observe(self, job_id: str) -> RuntimeJobObservation:
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


class NoopArtifactReader:
    def read(self, job_id: str, artifact_id: str) -> RuntimeArtifactPayload:
        raise AssertionError("artifact read not expected")


class AgentServiceSemanticsTests(unittest.TestCase):
    def _open(self, db: Path) -> object:
        service = open_current(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopArtifactReader(),
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service: object, name: str):
        definition = service.definitions.create(name)
        revision = service.revisions.create(
            definition.id,
            {
                "harness": "r8-test",
                "name": name,
                "skills": [
                    {
                        "id": "review",
                        "name": "Review",
                        "description": "review",
                        "tags": ["review"],
                        "inputModes": ["text/plain"],
                        "outputModes": ["text/markdown"],
                    }
                ],
            },
        )
        identity = service.identities.create(
            definition.id,
            stable_name=name,
            description=f"{name} semantic agent",
        )
        instance = service.instances.create(f"request:{name}", revision.id)
        service.reconciler.reconcile(instance.id)
        return definition, revision, identity, instance

    def _task(self, service: object, revision_id: str, description: str = "task"):
        return service.tasks.create(
            description=description,
            required_revision_id=revision_id,
            execution={
                "workspaceId": "ws-test",
                "executable": "/usr/bin/true",
                "args": [],
                "cwdRelative": ".",
                "env": {},
            },
            acceptance={"kind": "stdout_equals", "value": "OK"},
        )

    def test_agent_identity_is_stable_per_definition_and_not_instance_identity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            definition = service.definitions.create("researcher")
            first = service.identities.create(
                definition.id,
                stable_name="researcher",
                description="Research agent",
            )
            replay = service.identities.create(
                definition.id,
                stable_name="researcher",
                description="Research agent",
            )
            revision = service.revisions.create(definition.id, {"v": 1})
            instance = service.instances.create("request:researcher", revision.id)

            self.assertEqual(first.id, replay.id)
            self.assertNotEqual(first.id, instance.id)
            self.assertEqual(
                service.identities.get_for_definition(definition.id).id, first.id
            )
            with self.assertRaises(ValueError):
                service.identities.create(
                    definition.id,
                    stable_name="renamed",
                    description="different identity replay",
                )

    def test_agent_skills_are_revision_native_without_second_capability_store(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            definition = service.definitions.create("researcher")
            skill = {
                "id": "literature-review",
                "name": "Literature Review",
                "description": "Review a bounded literature corpus",
                "tags": ["research", "review"],
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["text/markdown"],
            }
            revision = service.revisions.create(
                definition.id,
                {"harness": "r8-test", "name": "researcher", "skills": [skill]},
            )

            self.assertEqual(revision.spec["skills"], [skill])
            self.assertFalse(hasattr(service, "capabilities"))
            table = service._connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='capability_advertisements'"
            ).fetchone()
            self.assertIsNone(table)

    def test_session_is_transport_agnostic_goal_bound_continuity_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, revision, identity, _ = self._agent(service, "researcher")
            goal = service.goals.create("paper review")
            session = service.sessions.open(
                client_session_id="session:paper-review",
                initiator_identity_id=identity.id,
                goal_id=goal.id,
            )
            replay = service.sessions.open(
                client_session_id="session:paper-review",
                initiator_identity_id=identity.id,
                goal_id=goal.id,
            )

            self.assertEqual(session.id, replay.id)
            self.assertEqual(session.state, "OPEN")
            self.assertEqual(session.goal_id, goal.id)
            self.assertEqual(session.initiator_identity_id, identity.id)
            self.assertFalse(hasattr(session, "owner_identity_id"))
            self.assertFalse(hasattr(session, "transport_id"))
            self.assertFalse(hasattr(session, "connection_id"))

    def test_session_items_are_append_only_ordered_and_exact_replay_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, _, identity, _ = self._agent(service, "researcher")
            session = service.sessions.open(
                client_session_id="session:items",
                initiator_identity_id=identity.id,
            )
            first = service.session_items.append(
                session.id,
                client_item_id="item:1",
                role="user",
                content={"text": "review this"},
            )
            replay = service.session_items.append(
                session.id,
                client_item_id="item:1",
                role="user",
                content={"text": "review this"},
            )
            second = service.session_items.append(
                session.id,
                client_item_id="item:2",
                role="agent",
                content={"text": "accepted"},
                producer_identity_id=identity.id,
            )

            self.assertEqual(first.id, replay.id)
            self.assertEqual(
                [x.sequence for x in service.session_items.list_for(session.id)], [1, 2]
            )
            self.assertEqual(second.sequence, 2)
            with self.assertRaises(ValueError):
                service.session_items.append(
                    session.id,
                    client_item_id="item:1",
                    role="user",
                    content={"text": "conflicting replay"},
                )

    def test_closed_session_rejects_new_items_and_delegations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, source_revision, source_identity, source_instance = self._agent(
                service, "source"
            )
            _, target_revision, target_identity, _ = self._agent(service, "target")
            task = self._task(service, source_revision.id)
            session = service.sessions.open(
                client_session_id="session:closed",
                initiator_identity_id=source_identity.id,
            )
            service.sessions.close(session.id)

            with self.assertRaises(RuntimeError):
                service.session_items.append(
                    session.id,
                    client_item_id="item:late",
                    role="user",
                    content={"text": "late"},
                )
            with self.assertRaises(RuntimeError):
                service.delegations.create(
                    client_delegation_id="delegation:late",
                    session_id=session.id,
                    source_identity_id=source_identity.id,
                    source_instance_id=source_instance.id,
                    target_identity_id=target_identity.id,
                    target_revision_id=target_revision.id,
                    task_id=task.id,
                    capability_key="review",
                    payload={"text": "do it"},
                    evidence_contract={"kind": "text"},
                )

    def test_delegation_is_transport_neutral_immutable_intent_not_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            _, source_revision, source_identity, source_instance = self._agent(
                service, "source"
            )
            _, target_revision, target_identity, _ = self._agent(service, "target")
            task = self._task(service, source_revision.id)
            session = service.sessions.open(
                client_session_id="session:delegation",
                initiator_identity_id=source_identity.id,
            )
            delegation = service.delegations.create(
                client_delegation_id="delegation:1",
                session_id=session.id,
                source_identity_id=source_identity.id,
                source_instance_id=source_instance.id,
                target_identity_id=target_identity.id,
                target_revision_id=target_revision.id,
                task_id=task.id,
                capability_key="review",
                payload={"text": "review this"},
                evidence_contract={"kind": "text/markdown"},
            )
            replay = service.delegations.create(
                client_delegation_id="delegation:1",
                session_id=session.id,
                source_identity_id=source_identity.id,
                source_instance_id=source_instance.id,
                target_identity_id=target_identity.id,
                target_revision_id=target_revision.id,
                task_id=task.id,
                capability_key="review",
                payload={"text": "review this"},
                evidence_contract={"kind": "text/markdown"},
            )

            self.assertEqual(delegation.id, replay.id)
            self.assertFalse(hasattr(delegation, "transport"))
            self.assertFalse(hasattr(delegation, "remote_task_id"))
            self.assertNotEqual(delegation.id, task.id)
            with self.assertRaises(ValueError):
                service.delegations.create(
                    client_delegation_id="delegation:1",
                    session_id=session.id,
                    source_identity_id=source_identity.id,
                    source_instance_id=source_instance.id,
                    target_identity_id=target_identity.id,
                    target_revision_id=target_revision.id,
                    task_id=task.id,
                    capability_key="review",
                    payload={"text": "changed"},
                    evidence_contract={"kind": "text/markdown"},
                )

    def test_delegation_requires_source_instance_identity_and_target_capability_consistency(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            source_def, source_revision, source_identity, source_instance = self._agent(
                service, "source"
            )
            _, target_revision, target_identity, _ = self._agent(service, "target")
            _, other_revision, other_identity, _ = self._agent(service, "other")
            task = self._task(service, source_revision.id)
            session = service.sessions.open(
                client_session_id="session:consistency",
                initiator_identity_id=source_identity.id,
            )

            with self.assertRaises(ValueError):
                service.delegations.create(
                    client_delegation_id="delegation:wrong-source",
                    session_id=session.id,
                    source_identity_id=other_identity.id,
                    source_instance_id=source_instance.id,
                    target_identity_id=target_identity.id,
                    target_revision_id=target_revision.id,
                    task_id=task.id,
                    capability_key="review",
                    payload={},
                    evidence_contract={},
                )
            with self.assertRaises(ValueError):
                service.delegations.create(
                    client_delegation_id="delegation:wrong-target-revision",
                    session_id=session.id,
                    source_identity_id=source_identity.id,
                    source_instance_id=source_instance.id,
                    target_identity_id=target_identity.id,
                    target_revision_id=other_revision.id,
                    task_id=task.id,
                    capability_key="review",
                    payload={},
                    evidence_contract={},
                )
            with self.assertRaises(LookupError):
                service.delegations.create(
                    client_delegation_id="delegation:missing-capability",
                    session_id=session.id,
                    source_identity_id=source_identity.id,
                    source_instance_id=source_instance.id,
                    target_identity_id=target_identity.id,
                    target_revision_id=target_revision.id,
                    task_id=task.id,
                    capability_key="not-advertised",
                    payload={},
                    evidence_contract={},
                )

    def test_a2a_agent_card_is_public_projection_not_internal_instance_or_session_dump(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            definition = service.definitions.create("researcher")
            revision = service.revisions.create(
                definition.id,
                {
                    "harness": "r8-test",
                    "name": "researcher",
                    "skills": [
                        {
                            "id": "literature-review",
                            "name": "Literature Review",
                            "description": "Review literature",
                            "tags": ["research"],
                            "inputModes": ["text"],
                            "outputModes": ["text/markdown"],
                        }
                    ],
                },
            )
            identity = service.identities.create(
                definition.id,
                stable_name="researcher",
                description="researcher semantic agent",
            )
            instance = service.instances.create("request:researcher:card", revision.id)
            service.reconciler.reconcile(instance.id)
            session = service.sessions.open(
                client_session_id="session:card",
                initiator_identity_id=identity.id,
            )

            card = service.a2a_cards.project(
                identity_id=identity.id,
                revision_id=revision.id,
                interfaces=[
                    {
                        "url": "https://agents.example.test/researcher",
                        "transport": "JSONRPC",
                    }
                ],
            )

            rendered = repr(card)
            self.assertEqual(card["name"], "researcher")
            self.assertEqual(card["version"], revision.id)
            self.assertNotIn("protocolVersion", card)
            self.assertNotIn("url", card)
            self.assertNotIn("preferredTransport", card)
            self.assertEqual(
                card["supportedInterfaces"],
                [
                    {
                        "url": "https://agents.example.test/researcher",
                        "protocolBinding": "JSONRPC",
                        "protocolVersion": "1.0",
                    }
                ],
            )
            self.assertEqual(card["defaultInputModes"], ["text/plain"])
            self.assertEqual(card["skills"][0]["id"], "literature-review")
            self.assertEqual(card["skills"][0]["inputModes"], ["text/plain"])
            self.assertNotIn(instance.id, rendered)
            self.assertNotIn(session.id, rendered)
            self.assertNotIn("request:", rendered)
            self.assertNotIn("credential", rendered.lower())

    def test_semantic_state_survives_service_reconstruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "service.db"
            first = self._open(db)
            _, revision, identity, _ = self._agent(first, "researcher")
            session = first.sessions.open(
                client_session_id="session:restart",
                initiator_identity_id=identity.id,
            )
            first.session_items.append(
                session.id,
                client_item_id="item:restart",
                role="user",
                content={"text": "persist"},
            )
            first.close()

            second = open_current(
                db,
                carrier_adapter=ReadyCarrier(),
                runtime_adapter=FakeRuntime(),
                artifact_reader=NoopArtifactReader(),
            )
            self.addCleanup(second.close)
            self.assertEqual(
                second.identities.get(identity.id).stable_name, "researcher"
            )
            self.assertEqual(
                second.revisions.get(revision.id).spec["skills"][0]["id"],
                "review",
            )
            self.assertEqual(second.sessions.get(session.id).state, "OPEN")
            self.assertEqual(
                second.session_items.list_for(session.id)[0].content["text"], "persist"
            )


if __name__ == "__main__":
    unittest.main()


class AgentServiceDelegationScopeTests(unittest.TestCase):
    def _open(self, db: Path) -> object:
        service = open_current(
            db,
            carrier_adapter=ReadyCarrier(),
            runtime_adapter=FakeRuntime(),
            artifact_reader=NoopArtifactReader(),
        )
        self.addCleanup(service.close)
        return service

    def _agent(self, service: object, name: str):
        definition = service.definitions.create(name)
        revision = service.revisions.create(
            definition.id,
            {
                "harness": "r8",
                "name": name,
                "skills": [
                    {
                        "id": "review",
                        "name": "Review",
                        "description": "review",
                        "tags": ["review"],
                        "inputModes": ["text/plain"],
                        "outputModes": ["text/markdown"],
                    }
                ],
            },
        )
        identity = service.identities.create(
            definition.id, stable_name=name, description=name
        )
        instance = service.instances.create(f"request:{name}:scope", revision.id)
        service.reconciler.reconcile(instance.id)
        return revision, identity, instance

    def _task(self, service: object, revision_id: str, label: str):
        return service.tasks.create(
            description=label,
            required_revision_id=revision_id,
            execution={
                "workspaceId": "ws-test",
                "executable": "/usr/bin/true",
                "args": [],
                "cwdRelative": ".",
                "env": {},
            },
            acceptance={"kind": "stdout_equals", "value": "OK"},
        )

    def test_session_initiator_is_continuity_metadata_not_delegation_authority(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            source_revision, initiator_identity, _ = self._agent(service, "initiator")
            _, delegate_identity, delegate_instance = self._agent(
                service, "delegate-source"
            )
            target_revision, target_identity, _ = self._agent(service, "target-owner")
            task = self._task(service, source_revision.id, "task")
            session = service.sessions.open(
                client_session_id="session:initiator-metadata",
                initiator_identity_id=initiator_identity.id,
            )

            delegation = service.delegations.create(
                client_delegation_id="delegation:non-initiator-source",
                session_id=session.id,
                source_identity_id=delegate_identity.id,
                source_instance_id=delegate_instance.id,
                target_identity_id=target_identity.id,
                target_revision_id=target_revision.id,
                task_id=task.id,
                capability_key="review",
                payload={},
                evidence_contract={},
            )

            self.assertEqual(delegation.source_identity_id, delegate_identity.id)
            self.assertEqual(session.initiator_identity_id, initiator_identity.id)

    def test_goal_bound_session_rejects_task_from_another_goal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self._open(Path(tmp) / "service.db")
            source_revision, source_identity, source_instance = self._agent(
                service, "source-goal"
            )
            target_revision, target_identity, _ = self._agent(service, "target-goal")
            goal_a = service.goals.create("goal-a")
            goal_b = service.goals.create("goal-b")
            task = self._task(service, source_revision.id, "task-b")
            service.goal_task_links.attach(goal_b.id, task.id)
            session = service.sessions.open(
                client_session_id="session:goal-a",
                initiator_identity_id=source_identity.id,
                goal_id=goal_a.id,
            )

            with self.assertRaises(ValueError):
                service.delegations.create(
                    client_delegation_id="delegation:wrong-goal",
                    session_id=session.id,
                    source_identity_id=source_identity.id,
                    source_instance_id=source_instance.id,
                    target_identity_id=target_identity.id,
                    target_revision_id=target_revision.id,
                    task_id=task.id,
                    capability_key="review",
                    payload={},
                    evidence_contract={},
                )
