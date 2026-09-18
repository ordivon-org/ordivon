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


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    name: str
    created_at_ns: int


@dataclass(frozen=True)
class AgentRevision:
    id: str
    definition_id: str
    spec: dict[str, Any]
    created_at_ns: int


@dataclass(frozen=True)
class AgentInstance:
    id: str
    birth_request_id: str
    revision_id: str
    state: str
    created_at_ns: int


@dataclass(frozen=True)
class DesiredPlacement:
    id: str
    agent_instance_id: str
    desired_state: str
    observed_state: str
    evidence_ref: str | None
    created_at_ns: int
    updated_at_ns: int


@dataclass(frozen=True)
class ServiceEvent:
    id: str
    aggregate_type: str
    aggregate_id: str
    sequence: int
    event_type: str
    payload: dict[str, Any]
    created_at_ns: int


@dataclass(frozen=True)
class ProviderObservation:
    placement_id: str
    state: str
    evidence_ref: str | None


class CarrierProviderAdapter(ABC):
    """Provider seam for realizing and observing an Agent carrier.

    The provider may be Workstation-managed Agent Automation, a hosted Agent service,
    Kubernetes, or another placement substrate. It reports provider facts and performs
    provider-local effects; it never owns Agent Service semantic state.
    """

    @abstractmethod
    def ensure(self, placement_id: str, agent_instance_id: str, revision_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def retire(self, placement_id: str, agent_instance_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def observe(self, placement_id: str) -> ProviderObservation:
        raise NotImplementedError


# R3 compatibility name. Host v2 is not the natural owner of placement effects;
# new code should use CarrierProviderAdapter.
HostAdapter = CarrierProviderAdapter


class _SqliteNode:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection


class AgentDefinitionStore(_SqliteNode):
    def create(self, name: str) -> AgentDefinition:
        if not name.strip():
            raise ValueError("agent definition name must not be empty")
        value = AgentDefinition(id=_id("adef"), name=name, created_at_ns=_now_ns())
        with self._connection:
            self._connection.execute(
                "INSERT INTO agent_definitions(id, name, created_at_ns) VALUES (?, ?, ?)",
                (value.id, value.name, value.created_at_ns),
            )
        return value

    def get(self, definition_id: str) -> AgentDefinition:
        row = self._connection.execute(
            "SELECT id, name, created_at_ns FROM agent_definitions WHERE id = ?", (definition_id,)
        ).fetchone()
        if row is None:
            raise KeyError(definition_id)
        return AgentDefinition(id=row["id"], name=row["name"], created_at_ns=row["created_at_ns"])


class AgentRevisionStore(_SqliteNode):
    def create(self, definition_id: str, spec: dict[str, Any]) -> AgentRevision:
        definition_exists = self._connection.execute(
            "SELECT 1 FROM agent_definitions WHERE id = ?", (definition_id,)
        ).fetchone()
        if definition_exists is None:
            raise KeyError(definition_id)
        encoded = _canonical_json(spec)
        digest = hashlib.sha256(f"{definition_id}\0{encoded}".encode("utf-8")).hexdigest()
        revision_id = f"arev_{digest}"
        created_at_ns = _now_ns()
        with self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO agent_revisions(id, definition_id, spec_json, created_at_ns) VALUES (?, ?, ?, ?)",
                (revision_id, definition_id, encoded, created_at_ns),
            )
        return self.get(revision_id)

    def get(self, revision_id: str) -> AgentRevision:
        row = self._connection.execute(
            "SELECT id, definition_id, spec_json, created_at_ns FROM agent_revisions WHERE id = ?",
            (revision_id,),
        ).fetchone()
        if row is None:
            raise KeyError(revision_id)
        return AgentRevision(
            id=row["id"],
            definition_id=row["definition_id"],
            spec=json.loads(row["spec_json"]),
            created_at_ns=row["created_at_ns"],
        )


class AgentInstanceStore(_SqliteNode):
    def get(self, instance_id: str) -> AgentInstance:
        row = self._connection.execute(
            "SELECT id, birth_request_id, revision_id, state, created_at_ns FROM agent_instances WHERE id = ?",
            (instance_id,),
        ).fetchone()
        if row is None:
            raise KeyError(instance_id)
        return self._from_row(row)

    def get_by_birth_request(self, birth_request_id: str) -> AgentInstance | None:
        row = self._connection.execute(
            "SELECT id, birth_request_id, revision_id, state, created_at_ns FROM agent_instances WHERE birth_request_id = ?",
            (birth_request_id,),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_all(self) -> list[AgentInstance]:
        rows = self._connection.execute(
            "SELECT id, birth_request_id, revision_id, state, created_at_ns FROM agent_instances ORDER BY created_at_ns, id"
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def set_state(self, instance_id: str, state: str) -> AgentInstance:
        with self._connection:
            self.set_state_in_transaction(instance_id, state)
        return self.get(instance_id)

    def set_state_in_transaction(self, instance_id: str, state: str) -> None:
        cursor = self._connection.execute(
            "UPDATE agent_instances SET state = ? WHERE id = ?", (state, instance_id)
        )
        if cursor.rowcount != 1:
            raise KeyError(instance_id)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AgentInstance:
        return AgentInstance(
            id=row["id"],
            birth_request_id=row["birth_request_id"],
            revision_id=row["revision_id"],
            state=row["state"],
            created_at_ns=row["created_at_ns"],
        )


class DesiredPlacementStore(_SqliteNode):
    def get(self, placement_id: str) -> DesiredPlacement:
        row = self._connection.execute(
            "SELECT id, agent_instance_id, desired_state, observed_state, evidence_ref, created_at_ns, updated_at_ns FROM desired_placements WHERE id = ?",
            (placement_id,),
        ).fetchone()
        if row is None:
            raise KeyError(placement_id)
        return self._from_row(row)

    def get_by_instance(self, instance_id: str) -> DesiredPlacement | None:
        row = self._connection.execute(
            "SELECT id, agent_instance_id, desired_state, observed_state, evidence_ref, created_at_ns, updated_at_ns FROM desired_placements WHERE agent_instance_id = ?",
            (instance_id,),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_all(self) -> list[DesiredPlacement]:
        rows = self._connection.execute(
            "SELECT id, agent_instance_id, desired_state, observed_state, evidence_ref, created_at_ns, updated_at_ns FROM desired_placements ORDER BY created_at_ns, id"
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def record_observation(self, placement_id: str, observation: ProviderObservation) -> DesiredPlacement:
        if observation.placement_id != placement_id:
            raise ValueError("observation placement identity mismatch")
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE desired_placements SET observed_state = ?, evidence_ref = ?, updated_at_ns = ? WHERE id = ?",
                (observation.state, observation.evidence_ref, _now_ns(), placement_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(placement_id)
        return self.get(placement_id)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DesiredPlacement:
        return DesiredPlacement(
            id=row["id"],
            agent_instance_id=row["agent_instance_id"],
            desired_state=row["desired_state"],
            observed_state=row["observed_state"],
            evidence_ref=row["evidence_ref"],
            created_at_ns=row["created_at_ns"],
            updated_at_ns=row["updated_at_ns"],
        )


class ServiceEventStore(_SqliteNode):
    def append(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> ServiceEvent:
        with self._connection:
            return self.append_in_transaction(aggregate_type, aggregate_id, event_type, payload)

    def append_in_transaction(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> ServiceEvent:
        payload = payload or {}
        row = self._connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) AS max_sequence FROM service_events WHERE aggregate_type = ? AND aggregate_id = ?",
            (aggregate_type, aggregate_id),
        ).fetchone()
        sequence = int(row["max_sequence"]) + 1
        event = ServiceEvent(
            id=_id("evt"),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            sequence=sequence,
            event_type=event_type,
            payload=payload,
            created_at_ns=_now_ns(),
        )
        self._connection.execute(
            "INSERT INTO service_events(id, aggregate_type, aggregate_id, sequence, event_type, payload_json, created_at_ns) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                event.id,
                event.aggregate_type,
                event.aggregate_id,
                event.sequence,
                event.event_type,
                _canonical_json(event.payload),
                event.created_at_ns,
            ),
        )
        return event

    def append_once(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> ServiceEvent:
        """Append exactly one immutable event for an aggregate identity."""
        with self._connection:
            return self.append_once_in_transaction(
                aggregate_type,
                aggregate_id,
                event_type,
                payload,
            )

    def append_once_in_transaction(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> ServiceEvent:
        """Transaction-scoped exactly-once append; caller owns commit/rollback."""
        payload = payload or {}

        def read_existing() -> ServiceEvent | None:
            row = self._connection.execute(
                "SELECT id, aggregate_type, aggregate_id, sequence, event_type, payload_json, created_at_ns "
                "FROM service_events WHERE aggregate_type = ? AND aggregate_id = ? AND sequence = 1",
                (aggregate_type, aggregate_id),
            ).fetchone()
            if row is None:
                return None
            return ServiceEvent(
                id=row["id"],
                aggregate_type=row["aggregate_type"],
                aggregate_id=row["aggregate_id"],
                sequence=row["sequence"],
                event_type=row["event_type"],
                payload=json.loads(row["payload_json"]),
                created_at_ns=row["created_at_ns"],
            )

        existing = read_existing()
        if existing is not None:
            if existing.event_type != event_type or existing.payload != payload:
                raise RuntimeError(
                    "append_once identity is already bound to different event content"
                )
            return existing
        event = ServiceEvent(
            id=_id("evt"),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            sequence=1,
            event_type=event_type,
            payload=payload,
            created_at_ns=_now_ns(),
        )
        try:
            self._connection.execute(
                "INSERT INTO service_events(id, aggregate_type, aggregate_id, sequence, event_type, payload_json, created_at_ns) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event.id,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.sequence,
                    event.event_type,
                    _canonical_json(event.payload),
                    event.created_at_ns,
                ),
            )
        except sqlite3.IntegrityError:
            existing = read_existing()
            if existing is None:
                raise
            if existing.event_type != event_type or existing.payload != payload:
                raise RuntimeError(
                    "append_once identity raced with different event content"
                ) from None
            return existing
        return event

    def get(self, event_id: str) -> ServiceEvent:
        row = self._connection.execute(
            "SELECT id, aggregate_type, aggregate_id, sequence, event_type, payload_json, created_at_ns FROM service_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            raise KeyError(event_id)
        return ServiceEvent(
            id=row["id"],
            aggregate_type=row["aggregate_type"],
            aggregate_id=row["aggregate_id"],
            sequence=row["sequence"],
            event_type=row["event_type"],
            payload=json.loads(row["payload_json"]),
            created_at_ns=row["created_at_ns"],
        )

    def list_for(self, aggregate_type: str, aggregate_id: str) -> list[ServiceEvent]:
        rows = self._connection.execute(
            "SELECT id, aggregate_type, aggregate_id, sequence, event_type, payload_json, created_at_ns FROM service_events WHERE aggregate_type = ? AND aggregate_id = ? ORDER BY sequence",
            (aggregate_type, aggregate_id),
        ).fetchall()
        return [
            ServiceEvent(
                id=row["id"],
                aggregate_type=row["aggregate_type"],
                aggregate_id=row["aggregate_id"],
                sequence=row["sequence"],
                event_type=row["event_type"],
                payload=json.loads(row["payload_json"]),
                created_at_ns=row["created_at_ns"],
            )
            for row in rows
        ]


class BirthCoordinator:
    def __init__(
        self,
        connection: sqlite3.Connection,
        revisions: AgentRevisionStore,
        instances: AgentInstanceStore,
        placements: DesiredPlacementStore,
        events: ServiceEventStore,
    ) -> None:
        self._connection = connection
        self._revisions = revisions
        self._instances = instances
        self._placements = placements
        self._events = events

    def birth(self, birth_request_id: str, revision_id: str) -> AgentInstance:
        if not birth_request_id.strip():
            raise ValueError("birth_request_id must not be empty")
        self._revisions.get(revision_id)
        existing = self._instances.get_by_birth_request(birth_request_id)
        if existing is not None:
            if existing.revision_id != revision_id:
                raise ValueError("birth request already bound to a different revision")
            return existing

        instance = AgentInstance(
            id=_id("ainst"),
            birth_request_id=birth_request_id,
            revision_id=revision_id,
            state="PROVISIONING",
            created_at_ns=_now_ns(),
        )
        placement_id = _id("place")
        placement_now = _now_ns()

        try:
            with self._connection:
                self._connection.execute(
                    "INSERT INTO agent_instances(id, birth_request_id, revision_id, state, created_at_ns) VALUES (?, ?, ?, ?, ?)",
                    (instance.id, instance.birth_request_id, instance.revision_id, instance.state, instance.created_at_ns),
                )
                self._connection.execute(
                    "INSERT INTO desired_placements(id, agent_instance_id, desired_state, observed_state, evidence_ref, created_at_ns, updated_at_ns) VALUES (?, ?, 'READY', 'UNKNOWN', NULL, ?, ?)",
                    (placement_id, instance.id, placement_now, placement_now),
                )
                self._append_event_in_transaction(
                    instance.id,
                    "AGENT_BIRTH_REQUESTED",
                    {"birthRequestId": birth_request_id, "revisionId": revision_id, "placementId": placement_id},
                )
        except sqlite3.IntegrityError:
            existing = self._instances.get_by_birth_request(birth_request_id)
            if existing is None or existing.revision_id != revision_id:
                raise
            return existing
        return instance

    def _append_event_in_transaction(self, instance_id: str, event_type: str, payload: dict[str, Any]) -> None:
        row = self._connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) AS max_sequence FROM service_events WHERE aggregate_type = 'AgentInstance' AND aggregate_id = ?",
            (instance_id,),
        ).fetchone()
        sequence = int(row["max_sequence"]) + 1
        self._connection.execute(
            "INSERT INTO service_events(id, aggregate_type, aggregate_id, sequence, event_type, payload_json, created_at_ns) VALUES (?, 'AgentInstance', ?, ?, ?, ?, ?)",
            (_id("evt"), instance_id, sequence, event_type, _canonical_json(payload), _now_ns()),
        )


class ProviderObserver:
    def __init__(self, carrier_adapter: CarrierProviderAdapter) -> None:
        self._carrier_adapter = carrier_adapter

    def observe(self, placement_id: str) -> ProviderObservation:
        observation = self._carrier_adapter.observe(placement_id)
        if observation.placement_id != placement_id:
            raise ValueError("provider returned observation for different placement")
        return observation


class PlacementReconciler:
    def __init__(
        self,
        connection: sqlite3.Connection,
        revisions: AgentRevisionStore,
        instances: AgentInstanceStore,
        placements: DesiredPlacementStore,
        events: ServiceEventStore,
        carrier_adapter: CarrierProviderAdapter,
        observer: ProviderObserver,
    ) -> None:
        self._connection = connection
        self._revisions = revisions
        self._instances = instances
        self._placements = placements
        self._events = events
        self._carrier_adapter = carrier_adapter
        self._observer = observer

    def reconcile(self, instance_id: str) -> AgentInstance:
        instance = self._instances.get(instance_id)
        revision = self._revisions.get(instance.revision_id)
        placement = self._placements.get_by_instance(instance.id)
        if placement is None:
            raise RuntimeError(f"agent instance {instance.id} has no desired placement")

        if placement.desired_state == "READY":
            self._carrier_adapter.ensure(placement.id, instance.id, revision.id)
        elif placement.desired_state == "RETIRED":
            self._carrier_adapter.retire(placement.id, instance.id)
        else:
            raise ValueError(f"unsupported desired state: {placement.desired_state}")

        observation = self._observer.observe(placement.id)
        self._placements.record_observation(placement.id, observation)

        current = self._instances.get(instance.id)
        if placement.desired_state == "READY" and observation.state == "READY":
            if current.state != "READY":
                with self._connection:
                    self._instances.set_state_in_transaction(instance.id, "READY")
                    self._events.append_in_transaction(
                        "AgentInstance",
                        instance.id,
                        "AGENT_READY",
                        {"placementId": placement.id, "evidenceRef": observation.evidence_ref},
                    )
                current = self._instances.get(instance.id)
            return current

        if current.state == "READY":
            with self._connection:
                self._instances.set_state_in_transaction(instance.id, "PROVISIONING")
                self._events.append_in_transaction(
                    "AgentInstance",
                    instance.id,
                    "AGENT_READINESS_LOST",
                    {"placementId": placement.id, "observedState": observation.state},
                )
            current = self._instances.get(instance.id)
        return current


class AgentServiceSlice1:
    """Thin composition root for the first clean-room Agent Service vertical slice."""

    def __init__(
        self, connection: sqlite3.Connection, carrier_adapter: CarrierProviderAdapter
    ) -> None:
        self._connection = connection
        self.definitions = AgentDefinitionStore(connection)
        self.revisions = AgentRevisionStore(connection)
        self.instances = AgentInstanceStore(connection)
        self.placements = DesiredPlacementStore(connection)
        self.events = ServiceEventStore(connection)
        self.birth = BirthCoordinator(connection, self.revisions, self.instances, self.placements, self.events)
        self.observer = ProviderObserver(carrier_adapter)
        self.reconciler = PlacementReconciler(
            connection,
            self.revisions,
            self.instances,
            self.placements,
            self.events,
            carrier_adapter,
            self.observer,
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        carrier_adapter: CarrierProviderAdapter | None = None,
        *,
        host_adapter: CarrierProviderAdapter | None = None,
    ) -> "AgentServiceSlice1":
        if carrier_adapter is not None and host_adapter is not None:
            raise ValueError("pass carrier_adapter or legacy host_adapter, not both")
        provider = carrier_adapter if carrier_adapter is not None else host_adapter
        if provider is None:
            raise ValueError("carrier_adapter is required")
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        cls._initialize_schema(connection)
        return cls(connection, provider)

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS agent_definitions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_revisions (
                id TEXT PRIMARY KEY,
                definition_id TEXT NOT NULL REFERENCES agent_definitions(id),
                spec_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_instances (
                id TEXT PRIMARY KEY,
                birth_request_id TEXT NOT NULL UNIQUE,
                revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
                state TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS desired_placements (
                id TEXT PRIMARY KEY,
                agent_instance_id TEXT NOT NULL UNIQUE REFERENCES agent_instances(id),
                desired_state TEXT NOT NULL,
                observed_state TEXT NOT NULL,
                evidence_ref TEXT,
                created_at_ns INTEGER NOT NULL,
                updated_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS service_events (
                id TEXT PRIMARY KEY,
                aggregate_type TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL,
                UNIQUE(aggregate_type, aggregate_id, sequence)
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._connection.close()
