from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import uuid

import rfc8785
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence import Any
from .semantics import AgentServiceR8, DelegationEnvelope
from .slice1 import ServiceEvent, ServiceEventStore
from .task_runtime import Any


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _route_profiles_from_revision_spec(
    revision_id: str,
    spec: dict[str, Any],
) -> list[dict[str, Any]]:
    """Validate immutable deployment route profiles embedded in an AgentRevision."""
    raw = spec.get("routes", [])
    if not isinstance(raw, list):
        raise ValueError("AgentRevision routes must be an array")

    profiles: list[dict[str, Any]] = []
    by_coordinate: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("AgentRevision route must be an object")

        transport = item.get("transport")
        protocol_version = item.get("protocolVersion")
        url = item.get("url")
        priority = item.get("priority", 0)
        security_requirements = item.get("securityRequirements", {})

        if not isinstance(transport, str) or not transport.strip():
            raise ValueError("route transport must be non-empty")
        normalized_transport = transport.strip()
        if not isinstance(protocol_version, str) or not protocol_version.strip():
            raise ValueError("route protocolVersion must be non-empty")
        normalized_protocol_version = protocol_version.strip()

        if (
            normalized_transport == "a2a-jsonrpc"
            and re.fullmatch(r"[0-9]+\.[0-9]+", normalized_protocol_version) is None
        ):
            raise ValueError("A2A protocolVersion must use Major.Minor without patch")
        if normalized_transport == "mcp":
            if (
                re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                    normalized_protocol_version,
                )
                is None
            ):
                raise ValueError("MCP protocolVersion must use YYYY-MM-DD")
            try:
                import datetime as _datetime

                _datetime.date.fromisoformat(normalized_protocol_version)
            except ValueError as error:
                raise ValueError("MCP protocolVersion must be a valid date version") from error

        if not isinstance(url, str) or not url.strip():
            raise ValueError("route url must be non-empty")
        normalized_url = url.strip()
        if not isinstance(priority, int) or priority < 0:
            raise ValueError("route priority must be a non-negative integer")
        if not isinstance(security_requirements, dict):
            raise ValueError("route securityRequirements must be an object")

        normalized_security: dict[str, list[str]] = {}
        for scheme, scopes in security_requirements.items():
            if (
                not isinstance(scheme, str)
                or not scheme.strip()
                or not isinstance(scopes, list)
            ):
                raise ValueError("invalid route security requirement")
            normalized_scopes: list[str] = []
            for scope in scopes:
                if not isinstance(scope, str) or not scope.strip():
                    raise ValueError(
                        "route security requirement scopes must be non-empty strings"
                    )
                normalized_scope = scope.strip()
                if normalized_scope not in normalized_scopes:
                    normalized_scopes.append(normalized_scope)
            normalized_security[scheme.strip()] = normalized_scopes

        material = {
            "revisionId": revision_id,
            "transport": normalized_transport,
            "protocolVersion": normalized_protocol_version,
            "url": normalized_url,
            "priority": priority,
            "securityRequirements": normalized_security,
        }
        profile = {
            "profileId": "iface_"
            + hashlib.sha256(rfc8785.dumps(material)).hexdigest(),
            "transport": normalized_transport,
            "protocolVersion": normalized_protocol_version,
            "url": normalized_url,
            "priority": priority,
            "securityRequirements": normalized_security,
        }
        coordinate = (
            normalized_transport,
            normalized_protocol_version,
            normalized_url,
        )
        previous = by_coordinate.get(coordinate)
        if previous is not None:
            if previous != profile:
                raise ValueError(
                    "route coordinate is duplicated with conflicting profile data"
                )
            continue
        by_coordinate[coordinate] = profile
        profiles.append(profile)

    return profiles


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


def _require_policy_provider(provider: Any | None) -> Any | None:
    if provider is not None and not callable(getattr(provider, "evaluate", None)):
        raise TypeError("policy provider must expose callable evaluate()")
    return provider


def _evaluate_policy_receipt(
    *,
    delegations: Any,
    events: ServiceEventStore,
    adapter: Any | None,
    client_policy_request_id: str,
    delegation_id: str,
) -> ServiceEvent:
    """Evaluate or replay one route-admission policy receipt without local policy authority."""
    request_id = client_policy_request_id.strip()
    if not request_id:
        raise ValueError("client_policy_request_id must be non-empty")

    historical = events.list_for("PolicyEvaluation", request_id)
    if historical:
        if len(historical) != 1 or historical[0].event_type != "PolicyEvaluated":
            raise RuntimeError("policy evaluation receipt stream is malformed")
        event = historical[0]
        if event.payload.get("delegationId") != delegation_id:
            raise ValueError("policy request identity already bound to different delegation")
        return event

    if adapter is None:
        raise RuntimeError("no policy provider configured")
    envelope = delegations.get(delegation_id)
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
    observation = adapter.evaluate(request)
    if not isinstance(observation, PolicyObservation):
        raise TypeError("policy provider must return PolicyObservation")
    if not observation.policy_revision.strip():
        raise ValueError("PolicyObservation.policy_revision must be non-empty")
    scopes = tuple(dict.fromkeys(observation.granted_permissions))
    return events.append(
        "PolicyEvaluation",
        request_id,
        "PolicyEvaluated",
        {
            "delegationId": envelope.id,
            "allowed": bool(observation.allowed),
            "reason": observation.reason,
            "policyRevision": observation.policy_revision,
            "grantedPermissions": list(scopes),
        },
    )


@dataclass(frozen=True)
class TransportBinding:
    id: str
    delegation_id: str
    policy_receipt_id: str
    policy_revision: str
    granted_permissions: tuple[str, ...]
    interface_id: str
    transport: str
    protocol_version: str | None
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
        policy_receipt_id: str,
        policy_revision: str,
        granted_permissions: tuple[str, ...],
        interface: dict[str, Any],
    ) -> TransportBinding:
        if not isinstance(interface["protocolVersion"], str) or not interface["protocolVersion"]:
            raise RuntimeError(
                "legacy interface advertisement lacks protocol_version; explicit re-advertisement is required"
            )
        material = f"{delegation_id}\0{policy_receipt_id}\0{interface['profileId']}\0{interface['protocolVersion']}".encode("utf-8")
        binding_id = "bind_" + hashlib.sha256(material).hexdigest()
        try:
            existing = self.get(binding_id)
        except KeyError:
            existing = None
        if existing is not None:
            candidate = (
                delegation_id,
                policy_receipt_id,
                policy_revision,
                granted_permissions,
                interface["profileId"],
                interface["transport"],
                interface["protocolVersion"],
                interface["url"],
                interface["securityRequirements"],
            )
            historical = (
                existing.delegation_id,
                existing.policy_receipt_id,
                existing.policy_revision,
                existing.granted_permissions,
                existing.interface_id,
                existing.transport,
                existing.protocol_version,
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
            policy_receipt_id=policy_receipt_id,
            policy_revision=policy_revision,
            granted_permissions=tuple(dict.fromkeys(granted_permissions)),
            interface_id=interface["profileId"],
            transport=interface["transport"],
            protocol_version=interface["protocolVersion"],
            endpoint=interface["url"],
            delivery_request_id=delivery_request_id,
            security_requirements=interface["securityRequirements"],
            created_at_ns=_now_ns(),
        )
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO transport_bindings(
                        id, delegation_id, policy_receipt_id, policy_revision, granted_permissions_json,
                        interface_id, transport, protocol_version, endpoint, delivery_request_id,
                        security_requirements_json, created_at_ns
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        value.id,
                        value.delegation_id,
                        value.policy_receipt_id,
                        value.policy_revision,
                        json.dumps(list(value.granted_permissions), sort_keys=True, separators=(",", ":"), ensure_ascii=False),
                        value.interface_id,
                        value.transport,
                        value.protocol_version,
                        value.endpoint,
                        value.delivery_request_id,
                        json.dumps(value.security_requirements, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
                        value.created_at_ns,
                    ),
                )
        except sqlite3.IntegrityError:
            existing = self.get(binding_id)
            candidate = (
                value.delegation_id,
                value.policy_receipt_id,
                value.policy_revision,
                value.granted_permissions,
                value.interface_id,
                value.transport,
                value.protocol_version,
                value.endpoint,
                value.delivery_request_id,
                value.security_requirements,
            )
            historical = (
                existing.delegation_id,
                existing.policy_receipt_id,
                existing.policy_revision,
                existing.granted_permissions,
                existing.interface_id,
                existing.transport,
                existing.protocol_version,
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
            policy_receipt_id=row["policy_receipt_id"],
            policy_revision=row["policy_revision"],
            granted_permissions=tuple(json.loads(row["granted_permissions_json"])),
            interface_id=row["interface_id"],
            transport=row["transport"],
            protocol_version=row["protocol_version"],
            endpoint=row["endpoint"],
            delivery_request_id=row["delivery_request_id"],
            security_requirements=json.loads(row["security_requirements_json"]),
            created_at_ns=row["created_at_ns"],
        )


class DelegationRoutePlanner:
    def __init__(
        self,
        connection: sqlite3.Connection,
        delegations: Any,
        events: ServiceEventStore,
        policy_adapter: Any | None,
        bindings: TransportBindingStore,
    ) -> None:
        policy_adapter = _require_policy_provider(policy_adapter)
        self._connection = connection
        self._delegations = delegations
        self._events = events
        self._policy_adapter = policy_adapter
        self._bindings = bindings

    def plan(
        self,
        delegation_id: str,
        *,
        client_policy_request_id: str,
        preferred_transports: list[str],
    ) -> TransportBinding:
        envelope = self._delegations.get(delegation_id)
        receipt = _evaluate_policy_receipt(
            delegations=self._delegations,
            events=self._events,
            adapter=self._policy_adapter,
            client_policy_request_id=client_policy_request_id,
            delegation_id=envelope.id,
        )
        if receipt.aggregate_type != "PolicyEvaluation" or receipt.event_type != "PolicyEvaluated":
            raise ValueError("policy receipt is not a policy evaluation event")
        if receipt.payload.get("delegationId") != envelope.id:
            raise ValueError("policy receipt belongs to different DelegationEnvelope")
        if not bool(receipt.payload.get("allowed")):
            raise PermissionError(receipt.payload.get("reason") or "delegation denied by policy")
        policy_revision = receipt.payload.get("policyRevision")
        if not isinstance(policy_revision, str) or not policy_revision.strip():
            raise RuntimeError("policy receipt lacks policy revision")
        granted_permissions = tuple(
            item
            for item in receipt.payload.get("grantedPermissions", [])
            if isinstance(item, str)
        )
        revision = self._connection.execute(
            "SELECT spec_json FROM agent_revisions WHERE id = ?",
            (envelope.target_revision_id,),
        ).fetchone()
        if revision is None:
            raise KeyError(envelope.target_revision_id)
        interfaces = _route_profiles_from_revision_spec(
            envelope.target_revision_id,
            json.loads(revision["spec_json"]),
        )
        if not interfaces:
            raise LookupError("target revision declares no route profiles")
        normalized_preferences = [item.strip() for item in preferred_transports if isinstance(item, str) and item.strip()]
        selected: dict[str, Any] | None = None
        for transport in normalized_preferences:
            candidates = [item for item in interfaces if item["transport"] == transport]
            if candidates:
                selected = sorted(candidates, key=lambda item: (item["priority"], item["profileId"]))[0]
                break
        if selected is None and not normalized_preferences:
            selected = sorted(
                interfaces,
                key=lambda item: (item["priority"], item["transport"], item["profileId"]),
            )[0]
        if selected is None:
            raise LookupError("none of the preferred transports are advertised by target revision")
        return self._bindings.create(
            delegation_id=envelope.id,
            policy_receipt_id=receipt.id,
            policy_revision=policy_revision,
            granted_permissions=granted_permissions,
            interface=selected,
        )


@dataclass(frozen=True)
class DeliveryObservation:
    admission: str
    status: str
    provider_request_id: str | None
    remote_task_id: str | None = None
    remote_context_id: str | None = None


def _require_delivery_providers(adapters: dict[str, Any]) -> dict[str, Any]:
    for transport, provider in adapters.items():
        if not isinstance(transport, str) or not transport.strip():
            raise TypeError("delivery provider transport key must be a non-empty string")
        if not callable(getattr(provider, "send", None)):
            raise TypeError(
                f"delivery provider for {transport!r} must expose callable send()"
            )
    return dict(adapters)


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


def _delivery_receipt_from_event(event: ServiceEvent) -> DeliveryReceipt:
    if event.aggregate_type != "Delivery" or event.event_type != "DeliveryCommitted":
        raise ValueError("event is not a delivery receipt")
    payload = event.payload
    if payload.get("bindingId") != event.aggregate_id:
        raise RuntimeError("delivery receipt binding identity mismatch")
    return DeliveryReceipt(
        id=event.id,
        binding_id=event.aggregate_id,
        delivery_request_id=payload["deliveryRequestId"],
        admission=payload["admission"],
        status=payload["status"],
        provider_request_id=payload.get("providerRequestId"),
        remote_task_id=payload.get("remoteTaskId"),
        remote_context_id=payload.get("remoteContextId"),
        created_at_ns=event.created_at_ns,
    )


def _delivery_receipt_get(events: ServiceEventStore, receipt_id: str) -> DeliveryReceipt:
    return _delivery_receipt_from_event(events.get(receipt_id))


def _delivery_receipt_get_by_binding(
    events: ServiceEventStore,
    binding_id: str,
    required: bool = True,
) -> DeliveryReceipt | None:
    history = events.list_for("Delivery", binding_id)
    receipts = [item for item in history if item.event_type == "DeliveryCommitted"]
    if not receipts:
        if required:
            raise KeyError(binding_id)
        return None
    if len(receipts) != 1:
        raise RuntimeError("delivery receipt stream contains multiple committed receipts")
    return _delivery_receipt_from_event(receipts[0])


def _delivery_receipt_list_for_binding(
    events: ServiceEventStore,
    binding_id: str,
) -> list[DeliveryReceipt]:
    receipt = _delivery_receipt_get_by_binding(events, binding_id, required=False)
    return [] if receipt is None else [receipt]


def _delivery_receipt_create(
    events: ServiceEventStore,
    binding: TransportBinding,
    observation: DeliveryObservation,
) -> DeliveryReceipt:
    if observation.admission not in {"committed", "existing"}:
        raise ValueError("DeliveryObservation admission must be committed or existing")
    event = events.append_once(
        "Delivery",
        binding.id,
        "DeliveryCommitted",
        {
            "bindingId": binding.id,
            "deliveryRequestId": binding.delivery_request_id,
            "admission": observation.admission,
            "status": observation.status,
            "providerRequestId": observation.provider_request_id,
            "remoteTaskId": observation.remote_task_id,
            "remoteContextId": observation.remote_context_id,
        },
    )
    return _delivery_receipt_from_event(event)


class DeliveryCoordinator:
    def __init__(
        self,
        delegations: Any,
        bindings: TransportBindingStore,
        events: ServiceEventStore,
        adapters: dict[str, Any],
    ) -> None:
        adapters = _require_delivery_providers(adapters)
        self._delegations = delegations
        self._bindings = bindings
        self._events = events
        self._adapters = adapters

    def deliver(self, binding_id: str) -> DeliveryReceipt:
        existing = _delivery_receipt_get_by_binding(
            self._events, binding_id, required=False
        )
        if existing is not None:
            return existing
        binding = self._bindings.get(binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        adapter = self._adapters.get(binding.transport)
        if adapter is None:
            raise LookupError(f"no delivery provider registered for {binding.transport}")
        observation = adapter.send(
            delivery_request_id=binding.delivery_request_id,
            binding=binding,
            envelope=envelope,
        )
        if not isinstance(observation, DeliveryObservation):
            raise TypeError("delivery provider must return DeliveryObservation")
        return _delivery_receipt_create(self._events, binding, observation)


class AgentServiceR9:
    """R9 composition: governed route binding and delivery receipts over R8 semantics."""

    def __init__(
        self,
        r8: AgentServiceR8,
        *,
        policy_adapter: Any | None,
        delivery_adapters: dict[str, Any],
    ) -> None:
        self._r8 = r8
        self._connection = r8._connection
        for name in (
            "definitions", "revisions", "instances", "placements", "events",
            "reconciler", "tasks", "assignments", "planner", "execution_activator", "completion",
            "goals", "goal_graph_guard", "goal_task_links", "task_dependencies",
            "task_readiness", "task_graph", "goal_planner", "goal_reconciler",
            "board_projector", "identities", "sessions", "session_items",
            "delegations", "a2a_cards",
        ):
            setattr(self, name, getattr(r8, name))
        self.transport_bindings = TransportBindingStore(self._connection)
        self.routes = DelegationRoutePlanner(
            self._connection,
            self.delegations,
            self.events,
            policy_adapter,
            self.transport_bindings,
        )
        self.delivery = DeliveryCoordinator(
            self.delegations,
            self.transport_bindings,
            self.events,
            delivery_adapters,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: Any,
        runtime_adapter: Any,
        artifact_reader: Any,
        policy_adapter: Any | None = None,
        delivery_adapters: dict[str, Any] | None = None,
        board_adapter: Any | None = None,
    ) -> "AgentServiceR9":
        policy_adapter = _require_policy_provider(policy_adapter)
        delivery_adapters = _require_delivery_providers(delivery_adapters or {})
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
            delivery_adapters=delivery_adapters,
        )

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        legacy_interface_table = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'agent_interface_advertisements'"
        ).fetchone()
        if legacy_interface_table is not None:
            raise RuntimeError(
                "legacy agent_interface_advertisements schema is unsupported; "
                "perform explicit destructive migration before opening this revision"
            )
        legacy_policy_table = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'policy_decisions'"
        ).fetchone()
        if legacy_policy_table is not None:
            raise RuntimeError(
                "legacy policy_decisions schema is unsupported; "
                "perform explicit destructive migration before opening this revision"
            )
        legacy_delivery_receipts = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'delivery_receipts'"
        ).fetchone()
        if legacy_delivery_receipts is not None:
            raise RuntimeError(
                "legacy delivery_receipts schema is unsupported; "
                "perform explicit destructive migration before opening this revision"
            )
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS transport_bindings (
                id TEXT PRIMARY KEY,
                delegation_id TEXT NOT NULL REFERENCES delegation_envelopes(id),
                policy_receipt_id TEXT NOT NULL,
                policy_revision TEXT NOT NULL,
                granted_permissions_json TEXT NOT NULL,
                interface_id TEXT NOT NULL,
                transport TEXT NOT NULL,
                protocol_version TEXT,
                endpoint TEXT NOT NULL,
                delivery_request_id TEXT NOT NULL UNIQUE,
                security_requirements_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL,
                UNIQUE(delegation_id, policy_receipt_id, interface_id)
            );
            """
        )
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(transport_bindings)"
            ).fetchall()
        }
        if "protocol_version" not in columns:
            connection.execute(
                "ALTER TABLE transport_bindings ADD COLUMN protocol_version TEXT"
            )
        connection.commit()

    def close(self) -> None:
        self._r8.close()
