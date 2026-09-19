from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from agent_service import open_agent_service
from agent_service.evidence import RuntimeArtifactPayload
from agent_service.slice1 import (
    AgentDefinitionStore,
    AgentInstanceStore,
    AgentRevisionStore,
    DesiredPlacementStore,
    PlacementReconciler,
    ProviderObservation,
    ServiceEventStore,
    _initialize_schema as _initialize_placement_schema,
)
from agent_service.task_runtime import (
    AssignmentActivator,
    AssignmentPlanner,
    AssignmentStore,
    RuntimeJobObservation,
    RuntimeJobRef,
    SemanticVerifier,
    TaskStore,
    _initialize_schema as _initialize_task_schema,
)


class ReadyCarrier:
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        return None

    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        return None

    def observe(self, placement_id: str) -> ProviderObservation:
        return ProviderObservation(
            placement_id=placement_id,
            state="READY",
            evidence_ref="test-support://ready",
        )


class IdleRuntime:
    def submit(self, client_request_id: str, execution: dict[str, Any]) -> RuntimeJobRef:
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


def open_current(
    db_path: str | Path,
    *,
    carrier_adapter: Any | None = None,
    runtime_adapter: Any | None = None,
    artifact_reader: Any | None = None,
    delivery_adapters: dict[str, Any] | None = None,
    execution_quiescence_adapters: dict[str, Any] | None = None,
    replay_safety_adapter: Any | None = None,
    **kwargs: Any,
) -> SimpleNamespace:
    if "quiescence_providers" in kwargs and execution_quiescence_adapters is not None:
        raise ValueError("duplicate quiescence provider arguments")
    if "replay_safety_provider" in kwargs and replay_safety_adapter is not None:
        raise ValueError("duplicate replay-safety provider arguments")
    if execution_quiescence_adapters is not None:
        kwargs["quiescence_providers"] = execution_quiescence_adapters
    if replay_safety_adapter is not None:
        kwargs["replay_safety_provider"] = replay_safety_adapter
    return open_agent_service(
        db_path,
        carrier_adapter=carrier_adapter or ReadyCarrier(),
        runtime_adapter=runtime_adapter or IdleRuntime(),
        artifact_reader=artifact_reader or NoopArtifactReader(),
        delivery_adapters=delivery_adapters or {},
        **kwargs,
    )


def open_task_runtime_fixture(
    db_path: str | Path,
    *,
    carrier_adapter: Any,
    runtime_adapter: Any,
) -> SimpleNamespace:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    _initialize_placement_schema(connection)
    _initialize_task_schema(connection)

    service = SimpleNamespace()
    service._connection = connection
    service.close = connection.close
    service.definitions = AgentDefinitionStore(connection)
    service.revisions = AgentRevisionStore(connection)
    service.instances = AgentInstanceStore(connection)
    service.placements = DesiredPlacementStore(connection)
    service.events = ServiceEventStore(connection)
    service.reconciler = PlacementReconciler(
        connection,
        service.revisions,
        service.instances,
        service.placements,
        service.events,
        carrier_adapter,
    )
    service.tasks = TaskStore(connection, service.events)
    service.assignments = AssignmentStore(connection)
    service.planner = AssignmentPlanner(
        connection,
        service.tasks,
        service.assignments,
        service.instances,
        service.events,
    )
    service.verifier = SemanticVerifier()
    service.activator = AssignmentActivator(
        connection,
        service.tasks,
        service.assignments,
        service.events,
        runtime_adapter,
        service.verifier,
    )
    return service
