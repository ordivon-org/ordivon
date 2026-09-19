from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .schema_migrations import apply_schema_migrations

from .delivery import (
    DelegationRoutePlanner,
    TransportBindingStore,
    _require_delivery_providers,
    _require_policy_provider,
)
from .effect_authority import EffectAuthorizedDeliveryCoordinator
from .evidence import (
    AssignmentExecutionActivator,
    TaskCompletionReconciler,
    _require_artifact_reader,
)
from .failover import (
    ExecutionClaimTransferCoordinator,
    ExecutionQuiescenceCoordinator,
    ExecutionQuiescenceRequestStore,
    FailoverCoordinator,
    ReplaySafetyCoordinator,
    TransferAwareDeliveryCoordinator,
)
from .goals import (
    GoalAssignmentPlanner,
    GoalBoardProjector,
    GoalGraphMutationGuard,
    GoalReconciler,
    GoalStore,
    GoalTaskGraph,
    GoalTaskLinkStore,
    TaskDependencyStore,
    TaskReadinessProjector,
)
from .provider_adapters import (
    A2AQuiescenceAdapter,
    EffectLedgerReplaySafetyAdapter,
    MCPTaskQuiescenceAdapter,
    ProviderCaller,
)
from .remote_evidence import (
    ClaimAwareAssignmentPlanner,
    RemoteArtifactEvidenceResolver,
    RemoteTaskCompletionReconciler,
    TaskExecutionClaimStore,
)
from .semantics import (
    A2AAgentCardProjector,
    AgentIdentityStore,
    DelegationEnvelopeStore,
    SessionItemStore,
    SessionStore,
)
from .slice1 import (
    AgentDefinitionStore,
    AgentInstanceStore,
    AgentRevisionStore,
    DesiredPlacementStore,
    PlacementReconciler,
    ServiceEventStore,
    _require_carrier_provider,
)
from .task_runtime import (
    AssignmentStore,
    TaskStore,
    _require_runtime_provider,
)
from .transport_credentials import (
    BoundCredentialHeaderProvider,
    TransportCredentialBindingCoordinator,
)
from .trust import (
    AuditEnvelopeProjector,
    CredentialReferenceStore,
    IdentityProofCoordinator,
    RemoteCorrelationReconciler,
)



def _build_service(connection: sqlite3.Connection,
    *,
    carrier_adapter: Any,
    runtime_adapter: Any,
    artifact_reader: Any,
    delivery_adapters: dict[str, Any],
    credential_material_provider: Any | None,
    a2a_caller: ProviderCaller | None,
    mcp_tasks_caller: ProviderCaller | None,
    effect_ledger_reader: Any | None,
    quiescence_providers: dict[str, Any] | None,
    replay_safety_provider: Any | None,
    policy_adapter: Any | None,
    identity_proof_adapter: Any | None,
    remote_delivery_observers: dict[str, Any],
    remote_artifact_readers: dict[str, Any],
    board_adapter: Any | None) -> SimpleNamespace:
    service = SimpleNamespace()
    carrier_adapter = _require_carrier_provider(carrier_adapter)
    runtime_adapter = _require_runtime_provider(runtime_adapter)
    artifact_reader = _require_artifact_reader(artifact_reader)
    policy_adapter = _require_policy_provider(policy_adapter)
    delivery_adapters = _require_delivery_providers(delivery_adapters)

    service._connection = connection
    service._closed = False

    # Admission and placement truth.
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

    # Durable task/runtime evidence truth.
    service.tasks = TaskStore(connection, service.events)
    service.assignments = AssignmentStore(connection)
    service.execution_activator = AssignmentExecutionActivator(
        connection,
        service.tasks,
        service.assignments,
        service.events,
        runtime_adapter,
    )
    service.completion = TaskCompletionReconciler(
        connection,
        service.tasks,
        service.assignments,
        service.events,
        runtime_adapter,
        artifact_reader,
    )

    # Goal/DAG truth.
    service.goals = GoalStore(connection, service.events)
    service.goal_graph_guard = GoalGraphMutationGuard(
        connection, service.goals, service.tasks
    )
    service.goal_task_links = GoalTaskLinkStore(
        connection, service.goals, service.tasks, service.goal_graph_guard
    )
    service.task_dependencies = TaskDependencyStore(
        connection, service.goal_task_links, service.goal_graph_guard
    )
    service.task_readiness = TaskReadinessProjector(
        service.tasks, service.goal_task_links, service.task_dependencies
    )
    service.task_graph = GoalTaskGraph(
        service.goal_task_links,
        service.task_dependencies,
        service.task_readiness,
        service.goal_graph_guard,
    )
    service.goal_reconciler = GoalReconciler(
        connection, service.goals, service.goal_task_links, service.events
    )
    service.board_projector = GoalBoardProjector(
        service.goals, service.events, board_adapter
    )

    # Identity/session/delegation semantics.
    service.identities = AgentIdentityStore(connection)
    service.sessions = SessionStore(connection, service.identities)
    service.session_items = SessionItemStore(
        connection, service.sessions, service.identities
    )
    service.delegations = DelegationEnvelopeStore(
        connection,
        service.sessions,
        service.identities,
        service.task_graph,
    )
    service.a2a_cards = A2AAgentCardProjector(connection, service.identities)

    # Route and trust evidence.
    service.transport_bindings = TransportBindingStore(connection)
    service.routes = DelegationRoutePlanner(
        connection,
        service.delegations,
        service.events,
        policy_adapter,
        service.transport_bindings,
    )
    service.credential_references = CredentialReferenceStore(connection)
    service.identity_proofs = IdentityProofCoordinator(
        service.identities,
        service.credential_references,
        service.events,
        identity_proof_adapter,
    )
    service.remote_reconciler = RemoteCorrelationReconciler(
        service.delegations,
        service.transport_bindings,
        service.events,
        remote_delivery_observers,
    )
    service.audit = AuditEnvelopeProjector(
        service.events,
        service.transport_bindings,
        service.events,
        service.delegations,
    )

    # Exactly-one execution ownership.
    service.execution_claims = TaskExecutionClaimStore(connection)
    service.planner = ClaimAwareAssignmentPlanner(
        connection,
        service.tasks,
        service.assignments,
        service.instances,
        service.events,
        service.execution_claims,
    )
    service.goal_planner = GoalAssignmentPlanner(service.task_readiness, service.planner)

    # Remote evidence.
    service.remote_artifacts = RemoteArtifactEvidenceResolver(
        remote_artifact_readers
    )
    service.remote_completion = RemoteTaskCompletionReconciler(
        connection,
        service.tasks,
        service.events,
        service.execution_claims,
        service.delegations,
        service.transport_bindings,
        service.events,
        service.events,
        service.remote_artifacts,
    )

    # Provider-specific quiescence and replay evidence are lowered into the
    # transport-neutral failover coordinators here, at the composition boundary.
    explicit_quiescence = dict(quiescence_providers or {})
    if explicit_quiescence and (a2a_caller is not None or mcp_tasks_caller is not None):
        raise ValueError(
            "pass quiescence_providers or protocol callers, not both"
        )
    if not explicit_quiescence:
        if a2a_caller is not None:
            explicit_quiescence["a2a-jsonrpc"] = A2AQuiescenceAdapter(a2a_caller)
        if mcp_tasks_caller is not None:
            explicit_quiescence["mcp"] = MCPTaskQuiescenceAdapter(mcp_tasks_caller)

    if replay_safety_provider is not None and effect_ledger_reader is not None:
        raise ValueError(
            "pass replay_safety_provider or effect_ledger_reader, not both"
        )
    replay_provider = replay_safety_provider
    if replay_provider is None and effect_ledger_reader is not None:
        replay_provider = EffectLedgerReplaySafetyAdapter(effect_ledger_reader)

    service.quiescence_requests = ExecutionQuiescenceRequestStore(connection)
    service.quiescence = ExecutionQuiescenceCoordinator(
        connection,
        service.tasks,
        service.events,
        service.execution_claims,
        service.delegations,
        service.transport_bindings,
        service.events,
        service.events,
        service.quiescence_requests,
        explicit_quiescence,
    )
    service.replay_safety = ReplaySafetyCoordinator(
        connection,
        service.tasks,
        service.events,
        service.execution_claims,
        service.delegations,
        service.transport_bindings,
        service.events,
        service.events,
        replay_provider,
    )
    service.claim_transfers = ExecutionClaimTransferCoordinator(
        connection,
        service.tasks,
        service.events,
        service.execution_claims,
        service.delegations,
        service.transport_bindings,
        service.events,
        service.events,
        service.quiescence_requests,
    )
    delivery_delegate = TransferAwareDeliveryCoordinator(
        connection,
        service.tasks,
        service.assignments,
        service.events,
        service.execution_claims,
        service.task_readiness,
        service.delegations,
        service.transport_bindings,
        service.events,
        delivery_adapters,
        quiescence_requests=service.quiescence_requests,
    )
    service.failover = FailoverCoordinator(
        service.quiescence,
        service.replay_safety,
        service.claim_transfers,
        service.events,
    )

    # Reference-only credential material.
    service.transport_credentials = TransportCredentialBindingCoordinator(
        connection,
        bindings=service.transport_bindings,
        delegations=service.delegations,
        credential_references=service.credential_references,
        identity_proofs=service.identity_proofs,
        events=service.events,
    )
    service.credential_headers = BoundCredentialHeaderProvider(
        events=service.events,
        credential_references=service.credential_references,
        identity_proofs=service.identity_proofs,
        material_provider=credential_material_provider,
    )

    # Final external-effect authority wraps the final transfer-aware delivery
    # coordinator; there are no intermediate service wrappers.
    service.delivery = EffectAuthorizedDeliveryCoordinator(
        delegate=delivery_delegate,
        bindings=service.transport_bindings,
        delegations=service.delegations,
        events=service.events,
        policy_adapter=policy_adapter,
    )
    service.close = connection.close
    return service

def open_agent_service(db_path: str | Path,
    *,
    carrier_adapter: Any,
    runtime_adapter: Any,
    artifact_reader: Any,
    delivery_adapters: dict[str, Any],
    credential_material_provider: Any | None = None,
    a2a_caller: ProviderCaller | None = None,
    mcp_tasks_caller: ProviderCaller | None = None,
    effect_ledger_reader: Any | None = None,
    quiescence_providers: dict[str, Any] | None = None,
    replay_safety_provider: Any | None = None,
    policy_adapter: Any | None = None,
    identity_proof_adapter: Any | None = None,
    remote_delivery_observers: dict[str, Any] | None = None,
    remote_artifact_readers: dict[str, Any] | None = None,
    board_adapter: Any | None = None) -> SimpleNamespace:
    _require_carrier_provider(carrier_adapter)
    _require_runtime_provider(runtime_adapter)
    _require_artifact_reader(artifact_reader)
    _require_policy_provider(policy_adapter)
    _require_delivery_providers(delivery_adapters)

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        apply_schema_migrations(connection)
        return _build_service(
            connection,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
            artifact_reader=artifact_reader,
            delivery_adapters=delivery_adapters,
            credential_material_provider=credential_material_provider,
            a2a_caller=a2a_caller,
            mcp_tasks_caller=mcp_tasks_caller,
            effect_ledger_reader=effect_ledger_reader,
            quiescence_providers=quiescence_providers,
            replay_safety_provider=replay_safety_provider,
            policy_adapter=policy_adapter,
            identity_proof_adapter=identity_proof_adapter,
            remote_delivery_observers=remote_delivery_observers or {},
            remote_artifact_readers=remote_artifact_readers or {},
            board_adapter=board_adapter,
        )
    except BaseException:
        connection.close()
        raise
