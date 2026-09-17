from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence import RuntimeArtifactReader
from .goals import AgentServiceR7
from .slice1 import CarrierProviderAdapter
from .task_runtime import RuntimeAdapter


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _normalized_strings(values: list[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, list):
        raise ValueError(f"{field} must be a list")
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} entries must be non-empty strings")
        if value.strip() not in normalized:
            normalized.append(value.strip())
    return tuple(normalized)


@dataclass(frozen=True)
class AgentIdentity:
    id: str
    definition_id: str
    stable_name: str
    description: str
    created_at_ns: int


class AgentIdentityStore:
    """Stable semantic Agent identity bound to one AgentDefinition, not an Instance."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, definition_id: str, *, stable_name: str, description: str) -> AgentIdentity:
        if not stable_name.strip() or not description.strip():
            raise ValueError("Agent identity name and description must be non-empty")
        if self._connection.execute(
            "SELECT 1 FROM agent_definitions WHERE id = ?", (definition_id,)
        ).fetchone() is None:
            raise KeyError(definition_id)
        existing = self.get_for_definition(definition_id, required=False)
        candidate = (stable_name.strip(), description.strip())
        if existing is not None:
            if (existing.stable_name, existing.description) != candidate:
                raise ValueError("AgentDefinition identity already exists with different semantics")
            return existing
        value = AgentIdentity(
            id=_id("aid"),
            definition_id=definition_id,
            stable_name=candidate[0],
            description=candidate[1],
            created_at_ns=_now_ns(),
        )
        try:
            with self._connection:
                self._connection.execute(
                    "INSERT INTO agent_identities(id, definition_id, stable_name, description, created_at_ns) VALUES (?, ?, ?, ?, ?)",
                    (value.id, value.definition_id, value.stable_name, value.description, value.created_at_ns),
                )
        except sqlite3.IntegrityError:
            existing = self.get_for_definition(definition_id, required=False)
            if existing is None or (existing.stable_name, existing.description) != candidate:
                raise
            return existing
        return value

    def get(self, identity_id: str) -> AgentIdentity:
        row = self._connection.execute(
            "SELECT id, definition_id, stable_name, description, created_at_ns FROM agent_identities WHERE id = ?",
            (identity_id,),
        ).fetchone()
        if row is None:
            raise KeyError(identity_id)
        return self._from_row(row)

    def get_for_definition(self, definition_id: str, required: bool = True) -> AgentIdentity | None:
        row = self._connection.execute(
            "SELECT id, definition_id, stable_name, description, created_at_ns FROM agent_identities WHERE definition_id = ?",
            (definition_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(definition_id)
            return None
        return self._from_row(row)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AgentIdentity:
        return AgentIdentity(
            id=row["id"],
            definition_id=row["definition_id"],
            stable_name=row["stable_name"],
            description=row["description"],
            created_at_ns=row["created_at_ns"],
        )


@dataclass(frozen=True)
class CapabilityAdvertisement:
    id: str
    revision_id: str
    key: str
    description: str
    input_modes: tuple[str, ...]
    output_modes: tuple[str, ...]
    tags: tuple[str, ...]
    created_at_ns: int


class CapabilityAdvertisementStore:
    """Immutable revision-scoped discovery metadata; never authorization state."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def advertise(
        self,
        revision_id: str,
        *,
        key: str,
        description: str,
        input_modes: list[str],
        output_modes: list[str],
        tags: list[str],
    ) -> CapabilityAdvertisement:
        if self._connection.execute(
            "SELECT 1 FROM agent_revisions WHERE id = ?", (revision_id,)
        ).fetchone() is None:
            raise KeyError(revision_id)
        if not isinstance(key, str) or not key.strip() or not isinstance(description, str) or not description.strip():
            raise ValueError("capability key and description must be non-empty")
        inputs = _normalized_strings(input_modes, "input_modes")
        outputs = _normalized_strings(output_modes, "output_modes")
        normalized_tags = _normalized_strings(tags, "tags")
        if not inputs or not outputs:
            raise ValueError("capability requires at least one input and output mode")
        existing = self.get_by_key(revision_id, key.strip(), required=False)
        candidate = (description.strip(), inputs, outputs, normalized_tags)
        if existing is not None:
            historical = (
                existing.description,
                existing.input_modes,
                existing.output_modes,
                existing.tags,
            )
            if historical != candidate:
                raise ValueError("capability advertisement is immutable for one revision/key")
            return existing
        identity_material = _canonical_json(
            {
                "revisionId": revision_id,
                "key": key.strip(),
                "description": candidate[0],
                "inputModes": inputs,
                "outputModes": outputs,
                "tags": normalized_tags,
            }
        )
        value = CapabilityAdvertisement(
            id="cap_" + hashlib.sha256(identity_material.encode("utf-8")).hexdigest(),
            revision_id=revision_id,
            key=key.strip(),
            description=candidate[0],
            input_modes=inputs,
            output_modes=outputs,
            tags=normalized_tags,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO capability_advertisements(id, revision_id, capability_key, description, input_modes_json, output_modes_json, tags_json, created_at_ns) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    value.id,
                    value.revision_id,
                    value.key,
                    value.description,
                    _canonical_json(list(value.input_modes)),
                    _canonical_json(list(value.output_modes)),
                    _canonical_json(list(value.tags)),
                    value.created_at_ns,
                ),
            )
        return value

    def get_by_key(
        self, revision_id: str, key: str, required: bool = True
    ) -> CapabilityAdvertisement | None:
        row = self._connection.execute(
            "SELECT * FROM capability_advertisements WHERE revision_id = ? AND capability_key = ?",
            (revision_id, key),
        ).fetchone()
        if row is None:
            if required:
                raise LookupError(f"capability {key!r} not advertised by revision {revision_id}")
            return None
        return self._from_row(row)

    def list_for_revision(self, revision_id: str) -> list[CapabilityAdvertisement]:
        rows = self._connection.execute(
            "SELECT * FROM capability_advertisements WHERE revision_id = ? ORDER BY capability_key, id",
            (revision_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> CapabilityAdvertisement:
        return CapabilityAdvertisement(
            id=row["id"],
            revision_id=row["revision_id"],
            key=row["capability_key"],
            description=row["description"],
            input_modes=tuple(json.loads(row["input_modes_json"])),
            output_modes=tuple(json.loads(row["output_modes_json"])),
            tags=tuple(json.loads(row["tags_json"])),
            created_at_ns=row["created_at_ns"],
        )


@dataclass(frozen=True)
class SemanticSession:
    id: str
    client_session_id: str
    initiator_identity_id: str
    goal_id: str | None
    state: str
    created_at_ns: int
    closed_at_ns: int | None


class SessionStore:
    """N07: semantic continuity identity independent of transport connections."""

    def __init__(self, connection: sqlite3.Connection, identities: AgentIdentityStore) -> None:
        self._connection = connection
        self._identities = identities

    def open(
        self,
        *,
        client_session_id: str,
        initiator_identity_id: str,
        goal_id: str | None = None,
    ) -> SemanticSession:
        if not client_session_id.strip():
            raise ValueError("client_session_id must be non-empty")
        self._identities.get(initiator_identity_id)
        if goal_id is not None and self._connection.execute(
            "SELECT 1 FROM service_goals WHERE id = ?", (goal_id,)
        ).fetchone() is None:
            raise KeyError(goal_id)
        existing = self.get_by_client_id(client_session_id, required=False)
        if existing is not None:
            if (existing.initiator_identity_id, existing.goal_id) != (initiator_identity_id, goal_id):
                raise ValueError("client_session_id already bound to different semantics")
            return existing
        value = SemanticSession(
            id=_id("sess"),
            client_session_id=client_session_id,
            initiator_identity_id=initiator_identity_id,
            goal_id=goal_id,
            state="OPEN",
            created_at_ns=_now_ns(),
            closed_at_ns=None,
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO semantic_sessions(id, client_session_id, initiator_identity_id, goal_id, state, created_at_ns, closed_at_ns) VALUES (?, ?, ?, ?, 'OPEN', ?, NULL)",
                (value.id, value.client_session_id, value.initiator_identity_id, value.goal_id, value.created_at_ns),
            )
        return value

    def get(self, session_id: str) -> SemanticSession:
        row = self._connection.execute(
            "SELECT * FROM semantic_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise KeyError(session_id)
        return self._from_row(row)

    def get_by_client_id(self, client_session_id: str, required: bool = True) -> SemanticSession | None:
        row = self._connection.execute(
            "SELECT * FROM semantic_sessions WHERE client_session_id = ?", (client_session_id,)
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_session_id)
            return None
        return self._from_row(row)

    def close(self, session_id: str) -> SemanticSession:
        session = self.get(session_id)
        if session.state == "CLOSED":
            return session
        with self._connection:
            self._connection.execute(
                "UPDATE semantic_sessions SET state = 'CLOSED', closed_at_ns = ? WHERE id = ?",
                (_now_ns(), session_id),
            )
        return self.get(session_id)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> SemanticSession:
        return SemanticSession(
            id=row["id"],
            client_session_id=row["client_session_id"],
            initiator_identity_id=row["initiator_identity_id"],
            goal_id=row["goal_id"],
            state=row["state"],
            created_at_ns=row["created_at_ns"],
            closed_at_ns=row["closed_at_ns"],
        )


@dataclass(frozen=True)
class SessionItem:
    id: str
    session_id: str
    client_item_id: str
    sequence: int
    role: str
    content: dict[str, Any]
    producer_identity_id: str | None
    created_at_ns: int


class SessionItemStore:
    def __init__(
        self,
        connection: sqlite3.Connection,
        sessions: SessionStore,
        identities: AgentIdentityStore,
    ) -> None:
        self._connection = connection
        self._sessions = sessions
        self._identities = identities

    def append(
        self,
        session_id: str,
        *,
        client_item_id: str,
        role: str,
        content: dict[str, Any],
        producer_identity_id: str | None = None,
    ) -> SessionItem:
        if role not in {"user", "agent", "system", "tool"}:
            raise ValueError("unsupported session item role")
        if not client_item_id.strip() or not isinstance(content, dict):
            raise ValueError("session item requires client_item_id and object content")
        existing = self.get_by_client_id(session_id, client_item_id, required=False)
        candidate_content = json.loads(_canonical_json(content))
        if existing is not None:
            if (
                existing.role,
                existing.content,
                existing.producer_identity_id,
            ) != (role, candidate_content, producer_identity_id):
                raise ValueError("session item replay conflicts with committed item")
            return existing
        session = self._sessions.get(session_id)
        if session.state != "OPEN":
            raise RuntimeError("cannot append to closed Session")
        if producer_identity_id is not None:
            self._identities.get(producer_identity_id)
        row = self._connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) AS max_sequence FROM session_items WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        value = SessionItem(
            id=_id("sitem"),
            session_id=session_id,
            client_item_id=client_item_id,
            sequence=int(row["max_sequence"]) + 1,
            role=role,
            content=candidate_content,
            producer_identity_id=producer_identity_id,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO session_items(id, session_id, client_item_id, sequence, role, content_json, producer_identity_id, created_at_ns) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    value.id,
                    value.session_id,
                    value.client_item_id,
                    value.sequence,
                    value.role,
                    _canonical_json(value.content),
                    value.producer_identity_id,
                    value.created_at_ns,
                ),
            )
        return value

    def get_by_client_id(
        self, session_id: str, client_item_id: str, required: bool = True
    ) -> SessionItem | None:
        row = self._connection.execute(
            "SELECT * FROM session_items WHERE session_id = ? AND client_item_id = ?",
            (session_id, client_item_id),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError((session_id, client_item_id))
            return None
        return self._from_row(row)

    def list_for(self, session_id: str) -> list[SessionItem]:
        self._sessions.get(session_id)
        rows = self._connection.execute(
            "SELECT * FROM session_items WHERE session_id = ? ORDER BY sequence",
            (session_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> SessionItem:
        return SessionItem(
            id=row["id"],
            session_id=row["session_id"],
            client_item_id=row["client_item_id"],
            sequence=row["sequence"],
            role=row["role"],
            content=json.loads(row["content_json"]),
            producer_identity_id=row["producer_identity_id"],
            created_at_ns=row["created_at_ns"],
        )


@dataclass(frozen=True)
class DelegationEnvelope:
    id: str
    client_delegation_id: str
    session_id: str
    source_identity_id: str
    source_instance_id: str
    target_identity_id: str
    target_revision_id: str
    task_id: str
    capability_key: str
    payload: dict[str, Any]
    evidence_contract: dict[str, Any]
    created_at_ns: int


class DelegationEnvelopeStore:
    """Immutable transport-neutral delegation intent. It grants no authority by itself."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        sessions: SessionStore,
        identities: AgentIdentityStore,
        capabilities: CapabilityAdvertisementStore,
        task_graph: Any,
    ) -> None:
        self._connection = connection
        self._sessions = sessions
        self._identities = identities
        self._capabilities = capabilities
        self._task_graph = task_graph

    def create(
        self,
        *,
        client_delegation_id: str,
        session_id: str,
        source_identity_id: str,
        source_instance_id: str,
        target_identity_id: str,
        target_revision_id: str,
        task_id: str,
        capability_key: str,
        payload: dict[str, Any],
        evidence_contract: dict[str, Any],
    ) -> DelegationEnvelope:
        if not client_delegation_id.strip() or not capability_key.strip():
            raise ValueError("delegation ids/capability must be non-empty")
        if not isinstance(payload, dict) or not isinstance(evidence_contract, dict):
            raise ValueError("delegation payload/evidence_contract must be objects")
        normalized_payload = json.loads(_canonical_json(payload))
        normalized_evidence = json.loads(_canonical_json(evidence_contract))
        existing = self.get_by_client_id(client_delegation_id, required=False)
        candidate = (
            session_id,
            source_identity_id,
            source_instance_id,
            target_identity_id,
            target_revision_id,
            task_id,
            capability_key.strip(),
            normalized_payload,
            normalized_evidence,
        )
        if existing is not None:
            historical = (
                existing.session_id,
                existing.source_identity_id,
                existing.source_instance_id,
                existing.target_identity_id,
                existing.target_revision_id,
                existing.task_id,
                existing.capability_key,
                existing.payload,
                existing.evidence_contract,
            )
            if historical != candidate:
                raise ValueError("delegation replay conflicts with committed envelope")
            return existing

        session = self._sessions.get(session_id)
        if session.state != "OPEN":
            raise RuntimeError("cannot create delegation in closed Session")
        source_identity = self._identities.get(source_identity_id)
        target_identity = self._identities.get(target_identity_id)
        instance = self._connection.execute(
            "SELECT revision_id FROM agent_instances WHERE id = ?", (source_instance_id,)
        ).fetchone()
        if instance is None:
            raise KeyError(source_instance_id)
        source_revision = self._connection.execute(
            "SELECT definition_id FROM agent_revisions WHERE id = ?", (instance["revision_id"],)
        ).fetchone()
        if source_revision is None or source_revision["definition_id"] != source_identity.definition_id:
            raise ValueError("source AgentInstance does not belong to source AgentIdentity")
        target_revision = self._connection.execute(
            "SELECT definition_id FROM agent_revisions WHERE id = ?", (target_revision_id,)
        ).fetchone()
        if target_revision is None:
            raise KeyError(target_revision_id)
        if target_revision["definition_id"] != target_identity.definition_id:
            raise ValueError("target revision does not belong to target AgentIdentity")
        if self._connection.execute(
            "SELECT 1 FROM service_tasks WHERE id = ?", (task_id,)
        ).fetchone() is None:
            raise KeyError(task_id)
        self._capabilities.get_by_key(target_revision_id, capability_key.strip())
        if session.goal_id is not None:
            linked_goal = self._task_graph.goal_for_task(task_id)
            if linked_goal.id != session.goal_id:
                raise ValueError("delegated Task does not belong to Session Goal")

        value = DelegationEnvelope(
            id=_id("deleg"),
            client_delegation_id=client_delegation_id,
            session_id=session_id,
            source_identity_id=source_identity_id,
            source_instance_id=source_instance_id,
            target_identity_id=target_identity_id,
            target_revision_id=target_revision_id,
            task_id=task_id,
            capability_key=capability_key.strip(),
            payload=normalized_payload,
            evidence_contract=normalized_evidence,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO delegation_envelopes(id, client_delegation_id, session_id, source_identity_id, source_instance_id, target_identity_id, target_revision_id, task_id, capability_key, payload_json, evidence_contract_json, created_at_ns) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    value.id,
                    value.client_delegation_id,
                    value.session_id,
                    value.source_identity_id,
                    value.source_instance_id,
                    value.target_identity_id,
                    value.target_revision_id,
                    value.task_id,
                    value.capability_key,
                    _canonical_json(value.payload),
                    _canonical_json(value.evidence_contract),
                    value.created_at_ns,
                ),
            )
        return value

    def get(self, delegation_id: str) -> DelegationEnvelope:
        row = self._connection.execute(
            "SELECT * FROM delegation_envelopes WHERE id = ?",
            (delegation_id,),
        ).fetchone()
        if row is None:
            raise KeyError(delegation_id)
        return self._from_row(row)

    def get_by_client_id(
        self, client_delegation_id: str, required: bool = True
    ) -> DelegationEnvelope | None:
        row = self._connection.execute(
            "SELECT * FROM delegation_envelopes WHERE client_delegation_id = ?",
            (client_delegation_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_delegation_id)
            return None
        return self._from_row(row)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DelegationEnvelope:
        return DelegationEnvelope(
            id=row["id"],
            client_delegation_id=row["client_delegation_id"],
            session_id=row["session_id"],
            source_identity_id=row["source_identity_id"],
            source_instance_id=row["source_instance_id"],
            target_identity_id=row["target_identity_id"],
            target_revision_id=row["target_revision_id"],
            task_id=row["task_id"],
            capability_key=row["capability_key"],
            payload=json.loads(row["payload_json"]),
            evidence_contract=json.loads(row["evidence_contract_json"]),
            created_at_ns=row["created_at_ns"],
        )


class A2AAgentCardProjector:
    """Pure discovery projection. It never exports Instance, Session, credential, or policy state."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        identities: AgentIdentityStore,
        capabilities: CapabilityAdvertisementStore,
    ) -> None:
        self._connection = connection
        self._identities = identities
        self._capabilities = capabilities

    def project(
        self,
        *,
        identity_id: str,
        revision_id: str,
        interfaces: list[dict[str, str]],
    ) -> dict[str, Any]:
        identity = self._identities.get(identity_id)
        revision = self._connection.execute(
            "SELECT definition_id FROM agent_revisions WHERE id = ?", (revision_id,)
        ).fetchone()
        if revision is None:
            raise KeyError(revision_id)
        if revision["definition_id"] != identity.definition_id:
            raise ValueError("Agent Card revision does not belong to identity")
        if not isinstance(interfaces, list) or not interfaces:
            raise ValueError("Agent Card requires at least one supported interface")
        normalized_interfaces: list[dict[str, str]] = []
        for interface in interfaces:
            if not isinstance(interface, dict):
                raise ValueError("interface must be an object")
            url = interface.get("url")
            transport = interface.get("transport")
            if not isinstance(url, str) or not url.strip() or not isinstance(transport, str) or not transport.strip():
                raise ValueError("interface requires non-empty url and transport")
            normalized_interfaces.append({"url": url.strip(), "transport": transport.strip()})
        capabilities = self._capabilities.list_for_revision(revision_id)
        input_modes = sorted({mode for capability in capabilities for mode in capability.input_modes})
        output_modes = sorted({mode for capability in capabilities for mode in capability.output_modes})
        return {
            "protocolVersion": "1.0.0",
            "name": identity.stable_name,
            "description": identity.description,
            "url": normalized_interfaces[0]["url"],
            "preferredTransport": normalized_interfaces[0]["transport"],
            "supportedInterfaces": normalized_interfaces,
            "capabilities": {},
            "defaultInputModes": input_modes,
            "defaultOutputModes": output_modes,
            "skills": [
                {
                    "id": capability.key,
                    "name": capability.key,
                    "description": capability.description,
                    "tags": list(capability.tags),
                    "inputModes": list(capability.input_modes),
                    "outputModes": list(capability.output_modes),
                }
                for capability in capabilities
            ],
        }


class AgentServiceR8:
    """R8 composition: transport-neutral identity/capability/session/delegation semantics."""

    def __init__(self, r7: AgentServiceR7) -> None:
        self._r7 = r7
        self._connection = r7._connection
        for name in (
            "definitions", "revisions", "instances", "placements", "events", "birth", "observer",
            "reconciler", "tasks", "assignments", "planner", "execution_activator", "completion",
            "verifications", "goals", "goal_graph_guard", "goal_task_links", "task_dependencies",
            "task_readiness", "task_graph", "goal_planner", "goal_reconciler", "board_receipts",
            "board_projector",
        ):
            setattr(self, name, getattr(r7, name))
        self.identities = AgentIdentityStore(self._connection)
        self.capabilities = CapabilityAdvertisementStore(self._connection)
        self.sessions = SessionStore(self._connection, self.identities)
        self.session_items = SessionItemStore(self._connection, self.sessions, self.identities)
        self.delegations = DelegationEnvelopeStore(
            self._connection,
            self.sessions,
            self.identities,
            self.capabilities,
            self.task_graph,
        )
        self.a2a_cards = A2AAgentCardProjector(
            self._connection, self.identities, self.capabilities
        )

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: CarrierProviderAdapter,
        runtime_adapter: RuntimeAdapter,
        artifact_reader: RuntimeArtifactReader,
        board_adapter: Any | None = None,
    ) -> "AgentServiceR8":
        r7 = AgentServiceR7.open(
            db_path,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
            artifact_reader=artifact_reader,
            board_adapter=board_adapter,
        )
        cls._initialize_schema(r7._connection)
        return cls(r7)

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS agent_identities (
                id TEXT PRIMARY KEY,
                definition_id TEXT NOT NULL UNIQUE REFERENCES agent_definitions(id),
                stable_name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS capability_advertisements (
                id TEXT PRIMARY KEY,
                revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
                capability_key TEXT NOT NULL,
                description TEXT NOT NULL,
                input_modes_json TEXT NOT NULL,
                output_modes_json TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL,
                UNIQUE(revision_id, capability_key)
            );

            CREATE TABLE IF NOT EXISTS semantic_sessions (
                id TEXT PRIMARY KEY,
                client_session_id TEXT NOT NULL UNIQUE,
                initiator_identity_id TEXT NOT NULL REFERENCES agent_identities(id),
                goal_id TEXT REFERENCES service_goals(id),
                state TEXT NOT NULL CHECK(state IN ('OPEN', 'CLOSED')),
                created_at_ns INTEGER NOT NULL,
                closed_at_ns INTEGER
            );

            CREATE TABLE IF NOT EXISTS session_items (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES semantic_sessions(id),
                client_item_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                role TEXT NOT NULL,
                content_json TEXT NOT NULL,
                producer_identity_id TEXT REFERENCES agent_identities(id),
                created_at_ns INTEGER NOT NULL,
                UNIQUE(session_id, client_item_id),
                UNIQUE(session_id, sequence)
            );

            CREATE TABLE IF NOT EXISTS delegation_envelopes (
                id TEXT PRIMARY KEY,
                client_delegation_id TEXT NOT NULL UNIQUE,
                session_id TEXT NOT NULL REFERENCES semantic_sessions(id),
                source_identity_id TEXT NOT NULL REFERENCES agent_identities(id),
                source_instance_id TEXT NOT NULL REFERENCES agent_instances(id),
                target_identity_id TEXT NOT NULL REFERENCES agent_identities(id),
                target_revision_id TEXT NOT NULL REFERENCES agent_revisions(id),
                task_id TEXT NOT NULL REFERENCES service_tasks(id),
                capability_key TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                evidence_contract_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._r7.close()
