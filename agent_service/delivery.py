from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence import RuntimeArtifactReader
from .semantics import AgentServiceR8, DelegationEnvelope
from .slice1 import CarrierProviderAdapter
from .task_runtime import RuntimeAdapter


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class AgentInterfaceAdvertisement:
    id: str
    revision_id: str
    transport: str
    url: str
    priority: int
    security_requirements: dict[str, list[str]]
    created_at_ns: int


class AgentInterfaceAdvertisementStore:
    """Revision-scoped route/discovery interface metadata, never credential material."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def advertise(
        self,
        revision_id: str,
        *,
        transport: str,
        url: str,
        priority: int,
        security_requirements: dict[str, list[str]],
    ) -> AgentInterfaceAdvertisement:
        if self._connection.execute(
            "SELECT 1 FROM agent_revisions WHERE id = ?", (revision_id,)
        ).fetchone() is None:
            raise KeyError(revision_id)
        if not isinstance(transport, str) or not transport.strip():
            raise ValueError("interface transport must be non-empty")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("interface url must be non-empty")
        if not isinstance(priority, int) or priority < 0:
            raise ValueError("interface priority must be a non-negative integer")
        if not isinstance(security_requirements, dict):
            raise ValueError("security_requirements must be an object")
        normalized_security: dict[str, list[str]] = {}
        for scheme, scopes in security_requirements.items():
            if not isinstance(scheme, str) or not scheme.strip() or not isinstance(scopes, list):
                raise ValueError("invalid interface security requirement")
            normalized_scopes: list[str] = []
            for scope in scopes:
                if not isinstance(scope, str) or not scope.strip():
                    raise ValueError("security requirement scopes must be non-empty strings")
                if scope.strip() not in normalized_scopes:
                    normalized_scopes.append(scope.strip())
            normalized_security[scheme.strip()] = normalized_scopes
        existing = self.get_by_identity(
            revision_id, transport.strip(), url.strip(), required=False
        )
        candidate = (priority, normalized_security)
        if existing is not None:
            historical = (existing.priority, existing.security_requirements)
            if historical != candidate:
                raise ValueError(
                    "interface advertisement is immutable for revision/transport/url"
                )
            return existing
        identity_material = _canonical_json(
            {
                "revisionId": revision_id,
                "transport": transport.strip(),
                "url": url.strip(),
                "priority": priority,
                "securityRequirements": normalized_security,
            }
        )
        value = AgentInterfaceAdvertisement(
            id="iface_" + hashlib.sha256(identity_material.encode("utf-8")).hexdigest(),
            revision_id=revision_id,
            transport=transport.strip(),
            url=url.strip(),
            priority=priority,
            security_requirements=normalized_security,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO agent_interface_advertisements(id, revision_id, transport, url, priority, security_requirements_json, created_at_ns) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    value.id,
                    value.revision_id,
                    value.transport,
                    value.url,
                    value.priority,
                    _canonical_json(value.security_requirements),
                    value.created_at_ns,
                ),
            )
        return value

    def get(self, interface_id: str) -> AgentInterfaceAdvertisement:
        row = self._connection.execute(
            "SELECT * FROM agent_interface_advertisements WHERE id = ?", (interface_id,)
        ).fetchone()
        if row is None:
            raise KeyError(interface_id)
        return self._from_row(row)

    def get_by_identity(
        self,
        revision_id: str,
        transport: str,
        url: str,
        required: bool = True,
    ) -> AgentInterfaceAdvertisement | None:
        row = self._connection.execute(
            """
            SELECT * FROM agent_interface_advertisements
            WHERE revision_id = ? AND transport = ? AND url = ?
            """,
            (revision_id, transport, url),
        ).fetchone()
        if row is None:
            if required:
                raise LookupError((revision_id, transport, url))
            return None
        return self._from_row(row)

    def list_for_revision(self, revision_id: str) -> list[AgentInterfaceAdvertisement]:
        rows = self._connection.execute(
            "SELECT * FROM agent_interface_advertisements WHERE revision_id = ? ORDER BY priority, transport, id",
            (revision_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AgentInterfaceAdvertisement:
        return AgentInterfaceAdvertisement(
            id=row["id"],
            revision_id=row["revision_id"],
            transport=row["transport"],
            url=row["url"],
            priority=row["priority"],
            security_requirements=json.loads(row["security_requirements_json"]),
            created_at_ns=row["created_at_ns"],
        )


@dataclass(frozen=True)
class PolicyRequest:
    delegation_id: str
    session_id: str
    task_id: str
    source_identity_id: str
    source_instance_id: str
    target_identity_id: str
    target_revision_id: str
    capability_key: str


@dataclass(frozen=True)
class PolicyObservation:
    allowed: bool
    reason: str | None
    policy_revision: str
    granted_permissions: tuple[str, ...] = ()


class PolicyAdapter(ABC):
    @abstractmethod
    def evaluate(self, request: PolicyRequest) -> PolicyObservation:
        raise NotImplementedError


@dataclass(frozen=True)
class PolicyDecision:
    id: str
    client_policy_request_id: str
    delegation_id: str
    allowed: bool
    reason: str | None
    policy_revision: str
    granted_permissions: tuple[str, ...]
    created_at_ns: int


class PolicyDecisionStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, decision_id: str) -> PolicyDecision:
        row = self._connection.execute(
            "SELECT * FROM policy_decisions WHERE id = ?", (decision_id,)
        ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return self._from_row(row)

    def get_by_client_request(
        self, client_policy_request_id: str, required: bool = True
    ) -> PolicyDecision | None:
        row = self._connection.execute(
            "SELECT * FROM policy_decisions WHERE client_policy_request_id = ?",
            (client_policy_request_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_policy_request_id)
            return None
        return self._from_row(row)

    def create(
        self,
        *,
        client_policy_request_id: str,
        delegation_id: str,
        observation: PolicyObservation,
    ) -> PolicyDecision:
        scopes = tuple(dict.fromkeys(observation.granted_permissions))
        value = PolicyDecision(
            id=_id("pdec"),
            client_policy_request_id=client_policy_request_id,
            delegation_id=delegation_id,
            allowed=bool(observation.allowed),
            reason=observation.reason,
            policy_revision=observation.policy_revision,
            granted_permissions=scopes,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO policy_decisions(id, client_policy_request_id, delegation_id, allowed, reason, policy_revision, granted_permissions_json, created_at_ns) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    value.id,
                    value.client_policy_request_id,
                    value.delegation_id,
                    1 if value.allowed else 0,
                    value.reason,
                    value.policy_revision,
                    _canonical_json(list(value.granted_permissions)),
                    value.created_at_ns,
                ),
            )
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> PolicyDecision:
        return PolicyDecision(
            id=row["id"],
            client_policy_request_id=row["client_policy_request_id"],
            delegation_id=row["delegation_id"],
            allowed=bool(row["allowed"]),
            reason=row["reason"],
            policy_revision=row["policy_revision"],
            granted_permissions=tuple(json.loads(row["granted_permissions_json"])),
            created_at_ns=row["created_at_ns"],
        )


class PolicyEvaluationCoordinator:
    def __init__(
        self,
        delegations: Any,
        decisions: PolicyDecisionStore,
        adapter: PolicyAdapter | None,
    ) -> None:
        self._delegations = delegations
        self._decisions = decisions
        self._adapter = adapter

    def evaluate(self, *, client_policy_request_id: str, delegation_id: str) -> PolicyDecision:
        if not client_policy_request_id.strip():
            raise ValueError("client_policy_request_id must be non-empty")
        existing = self._decisions.get_by_client_request(client_policy_request_id, required=False)
        if existing is not None:
            if existing.delegation_id != delegation_id:
                raise ValueError("policy request identity already bound to different delegation")
            return existing
        if self._adapter is None:
            raise RuntimeError("no PolicyAdapter configured")
        envelope = self._delegations.get(delegation_id)
        request = PolicyRequest(
            delegation_id=envelope.id,
            session_id=envelope.session_id,
            task_id=envelope.task_id,
            source_identity_id=envelope.source_identity_id,
            source_instance_id=envelope.source_instance_id,
            target_identity_id=envelope.target_identity_id,
            target_revision_id=envelope.target_revision_id,
            capability_key=envelope.capability_key,
        )
        observation = self._adapter.evaluate(request)
        if not isinstance(observation, PolicyObservation):
            raise TypeError("PolicyAdapter must return PolicyObservation")
        if not observation.policy_revision.strip():
            raise ValueError("PolicyObservation.policy_revision must be non-empty")
        return self._decisions.create(
            client_policy_request_id=client_policy_request_id,
            delegation_id=delegation_id,
            observation=observation,
        )


@dataclass(frozen=True)
class TransportBinding:
    id: str
    delegation_id: str
    policy_decision_id: str
    interface_id: str
    transport: str
    endpoint: str
    delivery_request_id: str
    security_requirements: dict[str, list[str]]
    created_at_ns: int


class TransportBindingStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, binding_id: str) -> TransportBinding:
        row = self._connection.execute(
            "SELECT * FROM transport_bindings WHERE id = ?", (binding_id,)
        ).fetchone()
        if row is None:
            raise KeyError(binding_id)
        return self._from_row(row)

    def list_for_delegation(self, delegation_id: str) -> list[TransportBinding]:
        rows = self._connection.execute(
            """
            SELECT * FROM transport_bindings
            WHERE delegation_id = ?
            ORDER BY created_at_ns, id
            """,
            (delegation_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def create(
        self,
        *,
        delegation_id: str,
        policy_decision_id: str,
        interface: AgentInterfaceAdvertisement,
    ) -> TransportBinding:
        material = f"{delegation_id}\0{policy_decision_id}\0{interface.id}".encode("utf-8")
        binding_id = "bind_" + hashlib.sha256(material).hexdigest()
        try:
            existing = self.get(binding_id)
        except KeyError:
            existing = None
        if existing is not None:
            candidate = (
                delegation_id,
                policy_decision_id,
                interface.id,
                interface.transport,
                interface.url,
                interface.security_requirements,
            )
            historical = (
                existing.delegation_id,
                existing.policy_decision_id,
                existing.interface_id,
                existing.transport,
                existing.endpoint,
                existing.security_requirements,
            )
            if historical != candidate:
                raise RuntimeError("content-addressed TransportBinding identity collision")
            return existing
        delivery_request_id = "delivery:" + hashlib.sha256(binding_id.encode("utf-8")).hexdigest()
        value = TransportBinding(
            id=binding_id,
            delegation_id=delegation_id,
            policy_decision_id=policy_decision_id,
            interface_id=interface.id,
            transport=interface.transport,
            endpoint=interface.url,
            delivery_request_id=delivery_request_id,
            security_requirements=interface.security_requirements,
            created_at_ns=_now_ns(),
        )
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO transport_bindings(
                        id, delegation_id, policy_decision_id, interface_id, transport,
                        endpoint, delivery_request_id, security_requirements_json, created_at_ns
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        value.id,
                        value.delegation_id,
                        value.policy_decision_id,
                        value.interface_id,
                        value.transport,
                        value.endpoint,
                        value.delivery_request_id,
                        _canonical_json(value.security_requirements),
                        value.created_at_ns,
                    ),
                )
        except sqlite3.IntegrityError:
            existing = self.get(binding_id)
            candidate = (
                value.delegation_id,
                value.policy_decision_id,
                value.interface_id,
                value.transport,
                value.endpoint,
                value.delivery_request_id,
                value.security_requirements,
            )
            historical = (
                existing.delegation_id,
                existing.policy_decision_id,
                existing.interface_id,
                existing.transport,
                existing.endpoint,
                existing.delivery_request_id,
                existing.security_requirements,
            )
            if historical != candidate:
                raise
            return existing
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> TransportBinding:
        return TransportBinding(
            id=row["id"],
            delegation_id=row["delegation_id"],
            policy_decision_id=row["policy_decision_id"],
            interface_id=row["interface_id"],
            transport=row["transport"],
            endpoint=row["endpoint"],
            delivery_request_id=row["delivery_request_id"],
            security_requirements=json.loads(row["security_requirements_json"]),
            created_at_ns=row["created_at_ns"],
        )


class DelegationRoutePlanner:
    def __init__(
        self,
        delegations: Any,
        decisions: PolicyDecisionStore,
        interfaces: AgentInterfaceAdvertisementStore,
        bindings: TransportBindingStore,
    ) -> None:
        self._delegations = delegations
        self._decisions = decisions
        self._interfaces = interfaces
        self._bindings = bindings

    def plan(
        self,
        delegation_id: str,
        policy_decision_id: str,
        *,
        preferred_transports: list[str],
    ) -> TransportBinding:
        envelope = self._delegations.get(delegation_id)
        decision = self._decisions.get(policy_decision_id)
        if decision.delegation_id != envelope.id:
            raise ValueError("PolicyDecision belongs to different DelegationEnvelope")
        if not decision.allowed:
            raise PermissionError(decision.reason or "delegation denied by policy")
        interfaces = self._interfaces.list_for_revision(envelope.target_revision_id)
        if not interfaces:
            raise LookupError("target revision advertises no route interfaces")
        normalized_preferences = [item.strip() for item in preferred_transports if isinstance(item, str) and item.strip()]
        selected: AgentInterfaceAdvertisement | None = None
        for transport in normalized_preferences:
            candidates = [item for item in interfaces if item.transport == transport]
            if candidates:
                selected = sorted(candidates, key=lambda item: (item.priority, item.id))[0]
                break
        if selected is None and not normalized_preferences:
            selected = sorted(interfaces, key=lambda item: (item.priority, item.transport, item.id))[0]
        if selected is None:
            raise LookupError("none of the preferred transports are advertised by target revision")
        return self._bindings.create(
            delegation_id=envelope.id,
            policy_decision_id=decision.id,
            interface=selected,
        )


@dataclass(frozen=True)
class DeliveryObservation:
    admission: str
    status: str
    provider_request_id: str | None
    remote_task_id: str | None = None
    remote_context_id: str | None = None


class DeliveryAdapter(ABC):
    @abstractmethod
    def send(
        self,
        *,
        delivery_request_id: str,
        binding: TransportBinding,
        envelope: DelegationEnvelope,
    ) -> DeliveryObservation:
        raise NotImplementedError


@dataclass(frozen=True)
class DeliveryReceipt:
    id: str
    binding_id: str
    delivery_request_id: str
    admission: str
    status: str
    provider_request_id: str | None
    remote_task_id: str | None
    remote_context_id: str | None
    created_at_ns: int


class DeliveryReceiptStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, receipt_id: str) -> DeliveryReceipt:
        row = self._connection.execute(
            "SELECT * FROM delivery_receipts WHERE id = ?", (receipt_id,)
        ).fetchone()
        if row is None:
            raise KeyError(receipt_id)
        return self._from_row(row)

    def get_by_binding(self, binding_id: str, required: bool = True) -> DeliveryReceipt | None:
        row = self._connection.execute(
            "SELECT * FROM delivery_receipts WHERE binding_id = ?", (binding_id,)
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(binding_id)
            return None
        return self._from_row(row)

    def list_for_binding(self, binding_id: str) -> list[DeliveryReceipt]:
        row = self.get_by_binding(binding_id, required=False)
        return [] if row is None else [row]

    def create(self, binding: TransportBinding, observation: DeliveryObservation) -> DeliveryReceipt:
        if observation.admission not in {"committed", "existing"}:
            raise ValueError("DeliveryObservation admission must be committed or existing")
        value = DeliveryReceipt(
            id=_id("drcpt"),
            binding_id=binding.id,
            delivery_request_id=binding.delivery_request_id,
            admission=observation.admission,
            status=observation.status,
            provider_request_id=observation.provider_request_id,
            remote_task_id=observation.remote_task_id,
            remote_context_id=observation.remote_context_id,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO delivery_receipts(id, binding_id, delivery_request_id, admission, status, provider_request_id, remote_task_id, remote_context_id, created_at_ns) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    value.id,
                    value.binding_id,
                    value.delivery_request_id,
                    value.admission,
                    value.status,
                    value.provider_request_id,
                    value.remote_task_id,
                    value.remote_context_id,
                    value.created_at_ns,
                ),
            )
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DeliveryReceipt:
        return DeliveryReceipt(
            id=row["id"],
            binding_id=row["binding_id"],
            delivery_request_id=row["delivery_request_id"],
            admission=row["admission"],
            status=row["status"],
            provider_request_id=row["provider_request_id"],
            remote_task_id=row["remote_task_id"],
            remote_context_id=row["remote_context_id"],
            created_at_ns=row["created_at_ns"],
        )


class DeliveryCoordinator:
    def __init__(
        self,
        delegations: Any,
        bindings: TransportBindingStore,
        receipts: DeliveryReceiptStore,
        adapters: dict[str, DeliveryAdapter],
    ) -> None:
        self._delegations = delegations
        self._bindings = bindings
        self._receipts = receipts
        self._adapters = dict(adapters)

    def deliver(self, binding_id: str) -> DeliveryReceipt:
        existing = self._receipts.get_by_binding(binding_id, required=False)
        if existing is not None:
            return existing
        binding = self._bindings.get(binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        adapter = self._adapters.get(binding.transport)
        if adapter is None:
            raise LookupError(f"no DeliveryAdapter registered for {binding.transport}")
        observation = adapter.send(
            delivery_request_id=binding.delivery_request_id,
            binding=binding,
            envelope=envelope,
        )
        if not isinstance(observation, DeliveryObservation):
            raise TypeError("DeliveryAdapter must return DeliveryObservation")
        return self._receipts.create(binding, observation)


class AgentServiceR9:
    """R9 composition: governed route binding and delivery receipts over R8 semantics."""

    def __init__(
        self,
        r8: AgentServiceR8,
        *,
        policy_adapter: PolicyAdapter | None,
        delivery_adapters: dict[str, DeliveryAdapter],
    ) -> None:
        self._r8 = r8
        self._connection = r8._connection
        for name in (
            "definitions", "revisions", "instances", "placements", "events", "birth", "observer",
            "reconciler", "tasks", "assignments", "planner", "execution_activator", "completion",
            "verifications", "goals", "goal_graph_guard", "goal_task_links", "task_dependencies",
            "task_readiness", "task_graph", "goal_planner", "goal_reconciler", "board_receipts",
            "board_projector", "identities", "capabilities", "sessions", "session_items",
            "delegations", "a2a_cards",
        ):
            setattr(self, name, getattr(r8, name))
        self.interfaces = AgentInterfaceAdvertisementStore(self._connection)
        self.policy_decisions = PolicyDecisionStore(self._connection)
        self.policy = PolicyEvaluationCoordinator(
            self.delegations, self.policy_decisions, policy_adapter
        )
        self.transport_bindings = TransportBindingStore(self._connection)
        self.routes = DelegationRoutePlanner(
            self.delegations,
            self.policy_decisions,
            self.interfaces,
            self.transport_bindings,
        )
        self.delivery_receipts = DeliveryReceiptStore(self._connection)
        self.delivery = DeliveryCoordinator(
            self.delegations,
            self.transport_bindings,
            self.delivery_receipts,
            delivery_adapters,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: CarrierProviderAdapter,
        runtime_adapter: RuntimeAdapter,
        artifact_reader: RuntimeArtifactReader,
        policy_adapter: PolicyAdapter | None = None,
        delivery_adapters: dict[str, DeliveryAdapter] | None = None,
        board_adapter: Any | None = None,
    ) -> "AgentServiceR9":
        r8 = AgentServiceR8.open(
            db_path,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
            artifact_reader=artifact_reader,
            board_adapter=board_adapter,
        )
        cls._initialize_schema(r8._connection)
        return cls(
            r8,
            policy_adapter=policy_adapter,
            delivery_adapters=delivery_adapters or {},
        )

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS agent_interface_advertisements (
                id TEXT PRIMARY KEY,
                revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
                transport TEXT NOT NULL,
                url TEXT NOT NULL,
                priority INTEGER NOT NULL,
                security_requirements_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL,
                UNIQUE(revision_id, transport, url)
            );

            CREATE TABLE IF NOT EXISTS policy_decisions (
                id TEXT PRIMARY KEY,
                client_policy_request_id TEXT NOT NULL UNIQUE,
                delegation_id TEXT NOT NULL REFERENCES delegation_envelopes(id),
                allowed INTEGER NOT NULL CHECK(allowed IN (0, 1)),
                reason TEXT,
                policy_revision TEXT NOT NULL,
                granted_permissions_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transport_bindings (
                id TEXT PRIMARY KEY,
                delegation_id TEXT NOT NULL REFERENCES delegation_envelopes(id),
                policy_decision_id TEXT NOT NULL REFERENCES policy_decisions(id),
                interface_id TEXT NOT NULL REFERENCES agent_interface_advertisements(id),
                transport TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                delivery_request_id TEXT NOT NULL UNIQUE,
                security_requirements_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL,
                UNIQUE(delegation_id, policy_decision_id, interface_id)
            );

            CREATE TABLE IF NOT EXISTS delivery_receipts (
                id TEXT PRIMARY KEY,
                binding_id TEXT NOT NULL UNIQUE REFERENCES transport_bindings(id),
                delivery_request_id TEXT NOT NULL UNIQUE,
                admission TEXT NOT NULL,
                status TEXT NOT NULL,
                provider_request_id TEXT,
                remote_task_id TEXT,
                remote_context_id TEXT,
                created_at_ns INTEGER NOT NULL
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._r8.close()
