from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any


def _now_ns() -> int:
    return time.time_ns()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


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


def _agent_skills_from_revision_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate and return A2A AgentSkill values embedded in an immutable revision spec."""
    raw = spec.get("skills", [])
    if not isinstance(raw, list):
        raise ValueError("AgentRevision skills must be an array of A2A AgentSkill objects")

    skills: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("AgentRevision skill must be an object")
        normalized = json.loads(json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        for field in ("id", "name", "description"):
            value = normalized.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"A2A AgentSkill requires non-empty {field}")
            normalized[field] = value.strip()
        tags = normalized.get("tags")
        if not isinstance(tags, list):
            raise ValueError("A2A AgentSkill requires tags array")
        normalized["tags"] = list(_normalized_strings(tags, "tags"))
        skill_id = normalized["id"]
        if skill_id in seen_ids:
            raise ValueError(f"duplicate A2A AgentSkill id: {skill_id}")
        seen_ids.add(skill_id)

        for field in ("examples", "inputModes", "outputModes"):
            if field in normalized:
                values = normalized[field]
                if not isinstance(values, list):
                    raise ValueError(f"A2A AgentSkill {field} must be an array")
                normalized[field] = list(_normalized_strings(values, field))
        if "securityRequirements" in normalized and not isinstance(
            normalized["securityRequirements"], list
        ):
            raise ValueError("A2A AgentSkill securityRequirements must be an array")
        skills.append(normalized)
    return skills


def _agent_skill_by_id(spec: dict[str, Any], skill_id: str) -> dict[str, Any]:
    normalized_id = skill_id.strip()
    for skill in _agent_skills_from_revision_spec(spec):
        if skill["id"] == normalized_id:
            return skill
    raise LookupError(f"skill {normalized_id!r} not present in immutable AgentRevision")


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
        candidate_content = json.loads(json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
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
                    json.dumps(value.content, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
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
        goal_task_links: Any,
    ) -> None:
        self._connection = connection
        self._sessions = sessions
        self._identities = identities
        self._goal_task_links = goal_task_links

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
        normalized_payload = json.loads(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        normalized_evidence = json.loads(json.dumps(evidence_contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
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
            "SELECT definition_id, spec_json FROM agent_revisions WHERE id = ?",
            (target_revision_id,),
        ).fetchone()
        if target_revision is None:
            raise KeyError(target_revision_id)
        if target_revision["definition_id"] != target_identity.definition_id:
            raise ValueError("target revision does not belong to target AgentIdentity")
        if self._connection.execute(
            "SELECT 1 FROM service_tasks WHERE id = ?", (task_id,)
        ).fetchone() is None:
            raise KeyError(task_id)
        _agent_skill_by_id(
            json.loads(target_revision["spec_json"]),
            capability_key.strip(),
        )
        if session.goal_id is not None:
            linked_goal = self._goal_task_links.goal_for_task(task_id)
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
                    json.dumps(value.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
                    json.dumps(value.evidence_contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
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
    """Pure A2A 1.0 Agent Card projection; never a second discovery authority."""

    _PROTOCOL_BINDING_ALIASES = {
        "a2a-jsonrpc": "JSONRPC",
        "jsonrpc": "JSONRPC",
        "grpc": "GRPC",
        "http+json": "HTTP+JSON",
        "rest": "HTTP+JSON",
    }
    _MEDIA_TYPE_ALIASES = {
        "text": "text/plain",
        "json": "application/json",
    }

    def __init__(
        self,
        connection: sqlite3.Connection,
        identities: AgentIdentityStore,
    ) -> None:
        self._connection = connection
        self._identities = identities

    @classmethod
    def _protocol_binding(cls, value: str) -> str:
        normalized = value.strip()
        return cls._PROTOCOL_BINDING_ALIASES.get(normalized.lower(), normalized)

    @classmethod
    def _media_type(cls, value: str) -> str:
        normalized = value.strip()
        return cls._MEDIA_TYPE_ALIASES.get(normalized.lower(), normalized)

    def project(
        self,
        *,
        identity_id: str,
        revision_id: str,
        interfaces: list[dict[str, str]],
    ) -> dict[str, Any]:
        identity = self._identities.get(identity_id)
        revision = self._connection.execute(
            "SELECT definition_id, spec_json FROM agent_revisions WHERE id = ?", (revision_id,)
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
            binding = interface.get("protocolBinding", interface.get("transport"))
            protocol_version = interface.get("protocolVersion", "1.0")
            if (
                not isinstance(url, str)
                or not url.strip()
                or not isinstance(binding, str)
                or not binding.strip()
                or not isinstance(protocol_version, str)
                or not protocol_version.strip()
            ):
                raise ValueError(
                    "interface requires non-empty url, protocolBinding, and protocolVersion"
                )
            normalized_interfaces.append(
                {
                    "url": url.strip(),
                    "protocolBinding": self._protocol_binding(binding),
                    "protocolVersion": protocol_version.strip(),
                }
            )

        revision_spec = json.loads(revision["spec_json"])
        skills = _agent_skills_from_revision_spec(revision_spec)
        input_modes = sorted(
            {
                self._media_type(mode)
                for skill in skills
                for mode in skill.get("inputModes", [])
            }
        ) or ["text/plain"]
        output_modes = sorted(
            {
                self._media_type(mode)
                for skill in skills
                for mode in skill.get("outputModes", [])
            }
        ) or ["text/plain"]
        agent_version = revision_spec.get("version")
        if not isinstance(agent_version, str) or not agent_version.strip():
            agent_version = revision_id

        return {
            "name": identity.stable_name,
            "description": identity.description,
            "supportedInterfaces": normalized_interfaces,
            "version": agent_version.strip(),
            "capabilities": {},
            "defaultInputModes": input_modes,
            "defaultOutputModes": output_modes,
            "skills": [
                {
                    **skill,
                    **(
                        {
                            "inputModes": [
                                self._media_type(mode)
                                for mode in skill["inputModes"]
                            ]
                        }
                        if "inputModes" in skill
                        else {}
                    ),
                    **(
                        {
                            "outputModes": [
                                self._media_type(mode)
                                for mode in skill["outputModes"]
                            ]
                        }
                        if "outputModes" in skill
                        else {}
                    ),
                }
                for skill in skills
            ],
        }
