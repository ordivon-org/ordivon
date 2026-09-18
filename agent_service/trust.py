from __future__ import annotations

import json
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .delivery import (
    AgentServiceR9,
    DeliveryAdapter,
    PolicyAdapter,
    TransportBinding,
)
from .evidence import RuntimeArtifactReader
from .semantics import DelegationEnvelope
from .slice1 import CarrierProviderAdapter
from .task_runtime import RuntimeAdapter


def _now_ns() -> int:
    return time.time_ns()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _normalize_strings(values: list[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, list):
        raise ValueError(f"{field} must be a list")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} entries must be non-empty strings")
        normalized = value.strip()
        if normalized not in result:
            result.append(normalized)
    return tuple(result)


@dataclass(frozen=True)
class CredentialReference:
    id: str
    client_reference_id: str
    provider: str
    reference: str
    issuer: str
    resource: str
    requested_scopes: tuple[str, ...]
    created_at_ns: int


class CredentialReferenceStore:
    """Opaque credential locator metadata. Secret material is never fetched or stored here."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def register(
        self,
        *,
        client_reference_id: str,
        provider: str,
        reference: str,
        issuer: str,
        resource: str,
        requested_scopes: list[str],
    ) -> CredentialReference:
        values = (client_reference_id, provider, reference, issuer, resource)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("credential reference identity/provider/reference/issuer/resource must be non-empty")
        scopes = _normalize_strings(requested_scopes, "requested_scopes")
        candidate = (
            provider.strip(),
            reference.strip(),
            issuer.strip(),
            resource.strip(),
            scopes,
        )
        existing = self.get_by_client_reference(client_reference_id.strip(), required=False)
        if existing is not None:
            historical = (
                existing.provider,
                existing.reference,
                existing.issuer,
                existing.resource,
                existing.requested_scopes,
            )
            if historical != candidate:
                raise ValueError("credential reference replay conflicts with committed locator")
            return existing
        value = CredentialReference(
            id=_id("credref"),
            client_reference_id=client_reference_id.strip(),
            provider=candidate[0],
            reference=candidate[1],
            issuer=candidate[2],
            resource=candidate[3],
            requested_scopes=scopes,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO credential_references(
                    id, client_reference_id, provider, reference, issuer, resource,
                    requested_scopes_json, created_at_ns
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    value.id,
                    value.client_reference_id,
                    value.provider,
                    value.reference,
                    value.issuer,
                    value.resource,
                    _canonical_json(list(value.requested_scopes)),
                    value.created_at_ns,
                ),
            )
        return value

    def get(self, reference_id: str) -> CredentialReference:
        row = self._connection.execute(
            "SELECT * FROM credential_references WHERE id = ?", (reference_id,)
        ).fetchone()
        if row is None:
            raise KeyError(reference_id)
        return self._from_row(row)

    def get_by_client_reference(
        self, client_reference_id: str, required: bool = True
    ) -> CredentialReference | None:
        row = self._connection.execute(
            "SELECT * FROM credential_references WHERE client_reference_id = ?",
            (client_reference_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_reference_id)
            return None
        return self._from_row(row)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> CredentialReference:
        return CredentialReference(
            id=row["id"],
            client_reference_id=row["client_reference_id"],
            provider=row["provider"],
            reference=row["reference"],
            issuer=row["issuer"],
            resource=row["resource"],
            requested_scopes=tuple(json.loads(row["requested_scopes_json"])),
            created_at_ns=row["created_at_ns"],
        )


@dataclass(frozen=True)
class IdentityProofRequest:
    identity_id: str
    credential_reference_id: str
    purpose: str
    resource: str


@dataclass(frozen=True)
class IdentityProofObservation:
    authenticated: bool
    principal_id: str | None
    issuer: str
    auth_method: str
    expires_at_ms: int | None
    evidence_ref: str


class IdentityProofAdapter(ABC):
    @abstractmethod
    def verify(
        self,
        request: IdentityProofRequest,
        credential_reference: CredentialReference,
    ) -> IdentityProofObservation:
        raise NotImplementedError


@dataclass(frozen=True)
class IdentityProofRecord:
    id: str
    client_proof_request_id: str
    identity_id: str
    credential_reference_id: str
    purpose: str
    authenticated: bool
    principal_id: str | None
    issuer: str
    auth_method: str
    observed_at_ms: int
    expires_at_ms: int | None
    evidence_ref: str
    created_at_ns: int


class IdentityProofRecordStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, proof_id: str) -> IdentityProofRecord:
        row = self._connection.execute(
            "SELECT * FROM identity_proof_records WHERE id = ?", (proof_id,)
        ).fetchone()
        if row is None:
            raise KeyError(proof_id)
        return self._from_row(row)

    def get_by_client_request(
        self, client_proof_request_id: str, required: bool = True
    ) -> IdentityProofRecord | None:
        row = self._connection.execute(
            "SELECT * FROM identity_proof_records WHERE client_proof_request_id = ?",
            (client_proof_request_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_proof_request_id)
            return None
        return self._from_row(row)

    def create(
        self,
        *,
        client_proof_request_id: str,
        identity_id: str,
        credential_reference_id: str,
        purpose: str,
        observation: IdentityProofObservation,
        observed_at_ms: int,
    ) -> IdentityProofRecord:
        value = IdentityProofRecord(
            id=_id("iproof"),
            client_proof_request_id=client_proof_request_id,
            identity_id=identity_id,
            credential_reference_id=credential_reference_id,
            purpose=purpose,
            authenticated=bool(observation.authenticated),
            principal_id=observation.principal_id,
            issuer=observation.issuer,
            auth_method=observation.auth_method,
            observed_at_ms=observed_at_ms,
            expires_at_ms=observation.expires_at_ms,
            evidence_ref=observation.evidence_ref,
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO identity_proof_records(
                    id, client_proof_request_id, identity_id, credential_reference_id,
                    purpose, authenticated, principal_id, issuer, auth_method,
                    observed_at_ms, expires_at_ms, evidence_ref, created_at_ns
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    value.id,
                    value.client_proof_request_id,
                    value.identity_id,
                    value.credential_reference_id,
                    value.purpose,
                    1 if value.authenticated else 0,
                    value.principal_id,
                    value.issuer,
                    value.auth_method,
                    value.observed_at_ms,
                    value.expires_at_ms,
                    value.evidence_ref,
                    value.created_at_ns,
                ),
            )
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> IdentityProofRecord:
        return IdentityProofRecord(
            id=row["id"],
            client_proof_request_id=row["client_proof_request_id"],
            identity_id=row["identity_id"],
            credential_reference_id=row["credential_reference_id"],
            purpose=row["purpose"],
            authenticated=bool(row["authenticated"]),
            principal_id=row["principal_id"],
            issuer=row["issuer"],
            auth_method=row["auth_method"],
            observed_at_ms=row["observed_at_ms"],
            expires_at_ms=row["expires_at_ms"],
            evidence_ref=row["evidence_ref"],
            created_at_ns=row["created_at_ns"],
        )


class IdentityProofCoordinator:
    """Durable authentication evidence; never mutates AgentIdentity or grants authorization."""

    def __init__(
        self,
        identities: Any,
        credentials: CredentialReferenceStore,
        records: IdentityProofRecordStore,
        adapter: IdentityProofAdapter | None,
    ) -> None:
        self._identities = identities
        self._credentials = credentials
        self._records = records
        self._adapter = adapter

    def set_adapter(self, adapter: IdentityProofAdapter | None) -> None:
        self._adapter = adapter

    def verify(
        self,
        *,
        client_proof_request_id: str,
        identity_id: str,
        credential_reference_id: str,
        purpose: str,
        observed_at_ms: int | None = None,
    ) -> IdentityProofRecord:
        if not isinstance(client_proof_request_id, str) or not client_proof_request_id.strip():
            raise ValueError("client_proof_request_id must be non-empty")
        if not isinstance(purpose, str) or not purpose.strip():
            raise ValueError("identity proof purpose must be non-empty")
        existing = self._records.get_by_client_request(
            client_proof_request_id.strip(), required=False
        )
        if existing is not None:
            candidate = (identity_id, credential_reference_id, purpose.strip())
            historical = (
                existing.identity_id,
                existing.credential_reference_id,
                existing.purpose,
            )
            if candidate != historical:
                raise ValueError("identity proof request replay conflicts with committed proof")
            return existing
        self._identities.get(identity_id)
        credential = self._credentials.get(credential_reference_id)
        if self._adapter is None:
            raise RuntimeError("no IdentityProofAdapter configured")
        request = IdentityProofRequest(
            identity_id=identity_id,
            credential_reference_id=credential_reference_id,
            purpose=purpose.strip(),
            resource=credential.resource,
        )
        observation = self._adapter.verify(request, credential)
        if not isinstance(observation, IdentityProofObservation):
            raise TypeError("IdentityProofAdapter must return IdentityProofObservation")
        if not isinstance(observation.issuer, str) or not observation.issuer.strip():
            raise ValueError("identity proof issuer must be non-empty")
        if observation.issuer != credential.issuer:
            raise ValueError("identity proof issuer does not match credential reference issuer")
        if not isinstance(observation.auth_method, str) or not observation.auth_method.strip():
            raise ValueError("identity proof auth_method must be non-empty")
        if not isinstance(observation.evidence_ref, str) or not observation.evidence_ref.strip():
            raise ValueError("identity proof evidence_ref must be non-empty")
        if observation.authenticated and (
            not isinstance(observation.principal_id, str) or not observation.principal_id.strip()
        ):
            raise ValueError("authenticated identity proof requires a principal_id")
        when_ms = _now_ms() if observed_at_ms is None else int(observed_at_ms)
        return self._records.create(
            client_proof_request_id=client_proof_request_id.strip(),
            identity_id=identity_id,
            credential_reference_id=credential_reference_id,
            purpose=purpose.strip(),
            observation=observation,
            observed_at_ms=when_ms,
        )

    def get(self, proof_id: str) -> IdentityProofRecord:
        return self._records.get(proof_id)

    def is_current(self, proof_id: str, *, at_ms: int | None = None) -> bool:
        proof = self._records.get(proof_id)
        when = _now_ms() if at_ms is None else int(at_ms)
        if not proof.authenticated:
            return False
        return proof.expires_at_ms is None or when < proof.expires_at_ms


@dataclass(frozen=True)
class RemoteProviderObservation:
    provider_status: str
    terminal: bool
    successful: bool | None
    remote_task_id: str | None
    remote_context_id: str | None
    artifact_refs: tuple[str, ...]
    evidence_ref: str


class RemoteDeliveryObserver(ABC):
    @abstractmethod
    def observe(
        self,
        *,
        binding: TransportBinding,
        receipt: Any,
        envelope: DelegationEnvelope,
    ) -> RemoteProviderObservation:
        raise NotImplementedError


@dataclass(frozen=True)
class RemoteDeliverySnapshot:
    id: str
    binding_id: str
    sequence: int
    provider_status: str
    terminal: bool
    successful: bool | None
    remote_task_id: str | None
    remote_context_id: str | None
    artifact_refs: tuple[str, ...]
    evidence_ref: str
    observed_at_ms: int
    created_at_ns: int


class RemoteDeliveryObservationStore:
    """Append-only provider snapshots; remote lifecycle is not local Task semantic truth."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_for_binding(self, binding_id: str) -> list[RemoteDeliverySnapshot]:
        rows = self._connection.execute(
            """
            SELECT * FROM remote_delivery_observations
            WHERE binding_id = ? ORDER BY sequence
            """,
            (binding_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def latest_for_binding(
        self, binding_id: str, required: bool = True
    ) -> RemoteDeliverySnapshot | None:
        row = self._connection.execute(
            """
            SELECT * FROM remote_delivery_observations
            WHERE binding_id = ? ORDER BY sequence DESC LIMIT 1
            """,
            (binding_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(binding_id)
            return None
        return self._from_row(row)

    def record(
        self,
        *,
        binding_id: str,
        observation: RemoteProviderObservation,
        observed_at_ms: int | None = None,
    ) -> RemoteDeliverySnapshot:
        latest = self.latest_for_binding(binding_id, required=False)
        candidate = (
            observation.provider_status,
            bool(observation.terminal),
            observation.successful,
            observation.remote_task_id,
            observation.remote_context_id,
            tuple(observation.artifact_refs),
            observation.evidence_ref,
        )
        if latest is not None:
            historical = (
                latest.provider_status,
                latest.terminal,
                latest.successful,
                latest.remote_task_id,
                latest.remote_context_id,
                latest.artifact_refs,
                latest.evidence_ref,
            )
            if candidate == historical:
                return latest
        sequence = 1 if latest is None else latest.sequence + 1
        value = RemoteDeliverySnapshot(
            id=_id("robs"),
            binding_id=binding_id,
            sequence=sequence,
            provider_status=observation.provider_status,
            terminal=bool(observation.terminal),
            successful=observation.successful,
            remote_task_id=observation.remote_task_id,
            remote_context_id=observation.remote_context_id,
            artifact_refs=tuple(observation.artifact_refs),
            evidence_ref=observation.evidence_ref,
            observed_at_ms=_now_ms() if observed_at_ms is None else int(observed_at_ms),
            created_at_ns=_now_ns(),
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO remote_delivery_observations(
                    id, binding_id, sequence, provider_status, terminal, successful,
                    remote_task_id, remote_context_id, artifact_refs_json, evidence_ref,
                    observed_at_ms, created_at_ns
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    value.id,
                    value.binding_id,
                    value.sequence,
                    value.provider_status,
                    1 if value.terminal else 0,
                    None if value.successful is None else (1 if value.successful else 0),
                    value.remote_task_id,
                    value.remote_context_id,
                    _canonical_json(list(value.artifact_refs)),
                    value.evidence_ref,
                    value.observed_at_ms,
                    value.created_at_ns,
                ),
            )
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> RemoteDeliverySnapshot:
        raw_success = row["successful"]
        return RemoteDeliverySnapshot(
            id=row["id"],
            binding_id=row["binding_id"],
            sequence=row["sequence"],
            provider_status=row["provider_status"],
            terminal=bool(row["terminal"]),
            successful=None if raw_success is None else bool(raw_success),
            remote_task_id=row["remote_task_id"],
            remote_context_id=row["remote_context_id"],
            artifact_refs=tuple(json.loads(row["artifact_refs_json"])),
            evidence_ref=row["evidence_ref"],
            observed_at_ms=row["observed_at_ms"],
            created_at_ns=row["created_at_ns"],
        )


class RemoteCorrelationReconciler:
    def __init__(
        self,
        delegations: Any,
        bindings: Any,
        delivery_receipts: Any,
        observations: RemoteDeliveryObservationStore,
        observers: dict[str, RemoteDeliveryObserver],
    ) -> None:
        self._delegations = delegations
        self._bindings = bindings
        self._delivery_receipts = delivery_receipts
        self._observations = observations
        self._observers = dict(observers)

    def reconcile(self, binding_id: str) -> RemoteDeliverySnapshot:
        binding = self._bindings.get(binding_id)
        receipt = self._delivery_receipts.get_by_binding(binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        observer = self._observers.get(binding.transport)
        if observer is None:
            raise LookupError(f"no RemoteDeliveryObserver registered for {binding.transport}")
        observation = observer.observe(binding=binding, receipt=receipt, envelope=envelope)
        if not isinstance(observation, RemoteProviderObservation):
            raise TypeError("RemoteDeliveryObserver must return RemoteProviderObservation")
        if not isinstance(observation.provider_status, str) or not observation.provider_status.strip():
            raise ValueError("remote provider status must be non-empty")
        if not isinstance(observation.evidence_ref, str) or not observation.evidence_ref.strip():
            raise ValueError("remote observation evidence_ref must be non-empty")
        if receipt.remote_task_id is not None and observation.remote_task_id != receipt.remote_task_id:
            raise ValueError("remote task correlation changed from delivery receipt")
        if receipt.remote_context_id is not None and observation.remote_context_id != receipt.remote_context_id:
            raise ValueError("remote context correlation changed from delivery receipt")
        latest = self._observations.latest_for_binding(binding.id, required=False)
        if latest is not None:
            if latest.remote_task_id is not None and observation.remote_task_id != latest.remote_task_id:
                raise ValueError("remote task correlation changed from established observation")
            if latest.remote_context_id is not None and observation.remote_context_id != latest.remote_context_id:
                raise ValueError("remote context correlation changed from established observation")
        return self._observations.record(binding_id=binding.id, observation=observation)


class AuditEnvelopeProjector:
    """Pure audit projection over authoritative stores. No audit state table is created."""

    def __init__(
        self,
        proofs: IdentityProofRecordStore,
        bindings: Any,
        delivery_receipts: Any,
        observations: RemoteDeliveryObservationStore,
        delegations: Any,
    ) -> None:
        self._proofs = proofs
        self._bindings = bindings
        self._delivery_receipts = delivery_receipts
        self._observations = observations
        self._delegations = delegations

    def project_identity_proof(self, proof_id: str) -> dict[str, Any]:
        proof = self._proofs.get(proof_id)
        return {
            "kind": "ordivon.agent-service.identity-proof-audit-v1",
            "proofId": proof.id,
            "identityId": proof.identity_id,
            "credentialReferenceId": proof.credential_reference_id,
            "purpose": proof.purpose,
            "authenticated": proof.authenticated,
            "principalId": proof.principal_id,
            "issuer": proof.issuer,
            "authMethod": proof.auth_method,
            "observedAtMs": proof.observed_at_ms,
            "expiresAtMs": proof.expires_at_ms,
            "evidenceRef": proof.evidence_ref,
        }

    def project_remote_delivery(self, binding_id: str) -> dict[str, Any]:
        binding = self._bindings.get(binding_id)
        receipt = self._delivery_receipts.get_by_binding(binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        latest = self._observations.latest_for_binding(binding_id, required=False)
        remote_task_id = receipt.remote_task_id
        remote_context_id = receipt.remote_context_id
        if latest is not None:
            if remote_task_id is None:
                remote_task_id = latest.remote_task_id
            if remote_context_id is None:
                remote_context_id = latest.remote_context_id
        return {
            "kind": "ordivon.agent-service.remote-delivery-audit-v1",
            "bindingId": binding.id,
            "delegationId": envelope.id,
            "sessionId": envelope.session_id,
            "taskId": envelope.task_id,
            "transport": binding.transport,
            "endpoint": binding.endpoint,
            "deliveryRequestId": binding.delivery_request_id,
            "providerRequestId": receipt.provider_request_id,
            "remoteTaskId": remote_task_id,
            "remoteContextId": remote_context_id,
            "providerStatus": None if latest is None else latest.provider_status,
            "remoteTerminal": None if latest is None else latest.terminal,
            "remoteSuccessful": None if latest is None else latest.successful,
            "remoteEvidenceRef": None if latest is None else latest.evidence_ref,
        }


class AgentServiceR10:
    """R10: credential-reference/identity-proof boundary plus remote lifecycle observations."""

    def __init__(
        self,
        r9: AgentServiceR9,
        *,
        identity_proof_adapter: IdentityProofAdapter | None,
        remote_delivery_observers: dict[str, RemoteDeliveryObserver],
    ) -> None:
        self._r9 = r9
        self._connection = r9._connection
        for name in (
            "definitions", "revisions", "instances", "placements", "events", "birth", "observer",
            "reconciler", "tasks", "assignments", "planner", "execution_activator", "completion",
            "verifications", "goals", "goal_graph_guard", "goal_task_links", "task_dependencies",
            "task_readiness", "task_graph", "goal_planner", "goal_reconciler", "board_receipts",
            "board_projector", "identities", "capabilities", "sessions", "session_items",
            "delegations", "a2a_cards", "interfaces", "policy_decisions", "policy",
            "transport_bindings", "routes", "delivery_receipts", "delivery",
        ):
            setattr(self, name, getattr(r9, name))
        self.credential_references = CredentialReferenceStore(self._connection)
        self.identity_proof_records = IdentityProofRecordStore(self._connection)
        self.identity_proofs = IdentityProofCoordinator(
            self.identities,
            self.credential_references,
            self.identity_proof_records,
            identity_proof_adapter,
        )
        self.remote_observations = RemoteDeliveryObservationStore(self._connection)
        self.remote_reconciler = RemoteCorrelationReconciler(
            self.delegations,
            self.transport_bindings,
            self.delivery_receipts,
            self.remote_observations,
            remote_delivery_observers,
        )
        self.audit = AuditEnvelopeProjector(
            self.identity_proof_records,
            self.transport_bindings,
            self.delivery_receipts,
            self.remote_observations,
            self.delegations,
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
        identity_proof_adapter: IdentityProofAdapter | None = None,
        remote_delivery_observers: dict[str, RemoteDeliveryObserver] | None = None,
        board_adapter: Any | None = None,
    ) -> "AgentServiceR10":
        r9 = AgentServiceR9.open(
            db_path,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
            artifact_reader=artifact_reader,
            policy_adapter=policy_adapter,
            delivery_adapters=delivery_adapters or {},
            board_adapter=board_adapter,
        )
        cls._initialize_schema(r9._connection)
        return cls(
            r9,
            identity_proof_adapter=identity_proof_adapter,
            remote_delivery_observers=remote_delivery_observers or {},
        )

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS credential_references (
                id TEXT PRIMARY KEY,
                client_reference_id TEXT NOT NULL UNIQUE,
                provider TEXT NOT NULL,
                reference TEXT NOT NULL,
                issuer TEXT NOT NULL,
                resource TEXT NOT NULL,
                requested_scopes_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS identity_proof_records (
                id TEXT PRIMARY KEY,
                client_proof_request_id TEXT NOT NULL UNIQUE,
                identity_id TEXT NOT NULL REFERENCES agent_identities(id),
                credential_reference_id TEXT NOT NULL REFERENCES credential_references(id),
                purpose TEXT NOT NULL,
                authenticated INTEGER NOT NULL CHECK(authenticated IN (0, 1)),
                principal_id TEXT,
                issuer TEXT NOT NULL,
                auth_method TEXT NOT NULL,
                observed_at_ms INTEGER NOT NULL,
                expires_at_ms INTEGER,
                evidence_ref TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS remote_delivery_observations (
                id TEXT PRIMARY KEY,
                binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
                sequence INTEGER NOT NULL,
                provider_status TEXT NOT NULL,
                terminal INTEGER NOT NULL CHECK(terminal IN (0, 1)),
                successful INTEGER CHECK(successful IS NULL OR successful IN (0, 1)),
                remote_task_id TEXT,
                remote_context_id TEXT,
                artifact_refs_json TEXT NOT NULL,
                evidence_ref TEXT NOT NULL,
                observed_at_ms INTEGER NOT NULL,
                created_at_ns INTEGER NOT NULL,
                UNIQUE(binding_id, sequence)
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._r9.close()
