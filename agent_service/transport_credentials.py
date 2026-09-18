from __future__ import annotations

import json
import sqlite3
import time
import urllib.parse
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .delivery import DeliveryAdapter, PolicyAdapter, TransportBinding
from .evidence import RuntimeArtifactReader
from .goals import BoardAdapter
from .provider_adapters import (
    AgentServiceR13,
    EffectLedgerReader,
    ProviderCaller,
)
from .remote_evidence import RemoteArtifactReader
from .slice1 import CarrierProviderAdapter
from .task_runtime import RuntimeAdapter
from .trust import (
    CredentialReference,
    IdentityProofAdapter,
    IdentityProofRecord,
    RemoteDeliveryObserver,
)


def _now_ns() -> int:
    return time.time_ns()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _effective_port(parsed: urllib.parse.ParseResult) -> int | None:
    if parsed.port is not None:
        return parsed.port
    if parsed.scheme == "https":
        return 443
    if parsed.scheme == "http":
        return 80
    return None


def _resource_covers_endpoint(resource: str, endpoint: str) -> bool:
    try:
        r = urllib.parse.urlparse(resource)
        e = urllib.parse.urlparse(endpoint)
        r_port = _effective_port(r)
        e_port = _effective_port(e)
    except ValueError:
        return False
    if r.scheme not in {"https", "http"} or e.scheme not in {"https", "http"}:
        return False
    if not r.hostname or not e.hostname:
        return False
    if (r.scheme, r.hostname.lower(), r_port) != (e.scheme, e.hostname.lower(), e_port):
        return False
    resource_path = r.path or "/"
    endpoint_path = e.path or "/"
    if resource_path == "/":
        return True
    normalized = resource_path.rstrip("/")
    return endpoint_path == normalized or endpoint_path.startswith(normalized + "/")


@dataclass(frozen=True)
class TransportCredentialBinding:
    id: str
    client_binding_request_id: str
    binding_id: str
    security_scheme: str
    credential_reference_id: str
    identity_proof_id: str
    required_scopes: tuple[str, ...]
    created_at_ns: int


class TransportCredentialBindingStore:
    """Durable reference-only association. It never stores resolved secret/header material."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, record_id: str) -> TransportCredentialBinding:
        row = self._connection.execute(
            "SELECT * FROM transport_credential_bindings WHERE id = ?", (record_id,)
        ).fetchone()
        if row is None:
            raise KeyError(record_id)
        return self._from_row(row)

    def get_by_client_request(
        self, client_binding_request_id: str, required: bool = True
    ) -> TransportCredentialBinding | None:
        row = self._connection.execute(
            "SELECT * FROM transport_credential_bindings WHERE client_binding_request_id = ?",
            (client_binding_request_id,),
        ).fetchone()
        if row is None:
            if required:
                raise KeyError(client_binding_request_id)
            return None
        return self._from_row(row)

    def list_for_binding(self, binding_id: str) -> list[TransportCredentialBinding]:
        rows = self._connection.execute(
            """
            SELECT * FROM transport_credential_bindings
            WHERE binding_id = ? ORDER BY security_scheme, id
            """,
            (binding_id,),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def create_in_transaction(
        self,
        *,
        client_binding_request_id: str,
        binding_id: str,
        security_scheme: str,
        credential_reference_id: str,
        identity_proof_id: str,
        required_scopes: tuple[str, ...],
    ) -> TransportCredentialBinding:
        existing = self.get_by_client_request(client_binding_request_id, required=False)
        candidate = (
            binding_id,
            security_scheme,
            credential_reference_id,
            identity_proof_id,
            required_scopes,
        )
        if existing is not None:
            historical = (
                existing.binding_id,
                existing.security_scheme,
                existing.credential_reference_id,
                existing.identity_proof_id,
                existing.required_scopes,
            )
            if candidate != historical:
                raise ValueError(
                    "transport credential binding replay conflicts with committed references"
                )
            return existing
        value = TransportCredentialBinding(
            id=_id("tcred"),
            client_binding_request_id=client_binding_request_id,
            binding_id=binding_id,
            security_scheme=security_scheme,
            credential_reference_id=credential_reference_id,
            identity_proof_id=identity_proof_id,
            required_scopes=required_scopes,
            created_at_ns=_now_ns(),
        )
        try:
            self._connection.execute(
                """
                INSERT INTO transport_credential_bindings(
                    id, client_binding_request_id, binding_id, security_scheme,
                    credential_reference_id, identity_proof_id, required_scopes_json,
                    created_at_ns
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    value.id,
                    value.client_binding_request_id,
                    value.binding_id,
                    value.security_scheme,
                    value.credential_reference_id,
                    value.identity_proof_id,
                    _canonical_json(list(value.required_scopes)),
                    value.created_at_ns,
                ),
            )
        except sqlite3.IntegrityError:
            row = self._connection.execute(
                """
                SELECT * FROM transport_credential_bindings
                WHERE binding_id = ? AND security_scheme = ?
                """,
                (binding_id, security_scheme),
            ).fetchone()
            if row is None:
                raise
            existing = self._from_row(row)
            historical = (
                existing.binding_id,
                existing.security_scheme,
                existing.credential_reference_id,
                existing.identity_proof_id,
                existing.required_scopes,
            )
            if historical != candidate:
                raise RuntimeError(
                    "transport security scheme is already bound to different credential evidence"
                )
            return existing
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> TransportCredentialBinding:
        return TransportCredentialBinding(
            id=row["id"],
            client_binding_request_id=row["client_binding_request_id"],
            binding_id=row["binding_id"],
            security_scheme=row["security_scheme"],
            credential_reference_id=row["credential_reference_id"],
            identity_proof_id=row["identity_proof_id"],
            required_scopes=tuple(json.loads(row["required_scopes_json"])),
            created_at_ns=row["created_at_ns"],
        )


class TransportCredentialBindingCoordinator:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        bindings: Any,
        delegations: Any,
        policy_decisions: Any,
        credential_references: Any,
        identity_proofs: Any,
        records: TransportCredentialBindingStore,
    ) -> None:
        self._connection = connection
        self._bindings = bindings
        self._delegations = delegations
        self._policy_decisions = policy_decisions
        self._credential_references = credential_references
        self._identity_proofs = identity_proofs
        self._records = records

    def bind(
        self,
        *,
        client_binding_request_id: str,
        binding_id: str,
        security_scheme: str,
        identity_proof_id: str,
    ) -> TransportCredentialBinding:
        if not isinstance(client_binding_request_id, str) or not client_binding_request_id.strip():
            raise ValueError("client_binding_request_id must be non-empty")
        if not isinstance(security_scheme, str) or not security_scheme.strip():
            raise ValueError("security_scheme must be non-empty")
        request_id = client_binding_request_id.strip()
        scheme = security_scheme.strip()
        existing = self._records.get_by_client_request(request_id, required=False)
        if existing is not None:
            candidate = (binding_id, scheme, identity_proof_id)
            historical = (
                existing.binding_id,
                existing.security_scheme,
                existing.identity_proof_id,
            )
            if candidate != historical:
                raise ValueError(
                    "transport credential binding replay conflicts with committed binding"
                )
            return existing

        binding = self._bindings.get(binding_id)
        if scheme not in binding.security_requirements:
            raise ValueError("security_scheme is not declared by immutable TransportBinding")
        envelope = self._delegations.get(binding.delegation_id)
        decision = self._policy_decisions.get(binding.policy_decision_id)
        if not decision.allowed or decision.delegation_id != envelope.id:
            raise PermissionError("binding is not backed by an allowed PolicyDecision")

        proof = self._identity_proofs.get(identity_proof_id)
        if not proof.authenticated or not self._identity_proofs.is_current(proof.id):
            raise PermissionError("identity proof is not currently authenticated")
        if proof.identity_id != envelope.source_identity_id:
            raise PermissionError("identity proof does not belong to Delegation source identity")

        credential = self._credential_references.get(proof.credential_reference_id)
        required_scopes = tuple(binding.security_requirements[scheme])
        missing_credential = [
            scope for scope in required_scopes if scope not in credential.requested_scopes
        ]
        if missing_credential:
            raise PermissionError(
                f"credential reference lacks required scopes: {missing_credential}"
            )
        missing_policy = [
            scope for scope in required_scopes if scope not in decision.granted_permissions
        ]
        if missing_policy:
            raise PermissionError(
                f"PolicyDecision does not grant required scopes: {missing_policy}"
            )
        if not _resource_covers_endpoint(credential.resource, binding.endpoint):
            raise ValueError(
                "credential resource does not cover immutable TransportBinding endpoint"
            )

        with self._connection:
            return self._records.create_in_transaction(
                client_binding_request_id=request_id,
                binding_id=binding.id,
                security_scheme=scheme,
                credential_reference_id=credential.id,
                identity_proof_id=proof.id,
                required_scopes=required_scopes,
            )


@dataclass(frozen=True)
class CredentialHeaderMaterial:
    headers: dict[str, str]
    issuer: str
    resource: str
    granted_scopes: tuple[str, ...]
    expires_at_ms: int | None
    evidence_ref: str


class CredentialMaterialProvider(ABC):
    """External secret authority. Returned header material is intentionally ephemeral."""

    @abstractmethod
    def resolve_headers(
        self,
        *,
        credential_reference: CredentialReference,
        binding: TransportBinding,
        security_scheme: str,
        identity_proof: IdentityProofRecord,
    ) -> CredentialHeaderMaterial:
        raise NotImplementedError


class BoundCredentialHeaderProvider:
    """Resolve transient provider headers from durable reference/proof bindings."""

    def __init__(
        self,
        *,
        records: TransportCredentialBindingStore,
        credential_references: Any,
        identity_proofs: Any,
        material_provider: CredentialMaterialProvider | None,
    ) -> None:
        self._records = records
        self._credential_references = credential_references
        self._identity_proofs = identity_proofs
        self._material_provider = material_provider

    def __repr__(self) -> str:
        return "BoundCredentialHeaderProvider(material=<external/redacted>)"

    def __call__(self, binding: TransportBinding) -> dict[str, str]:
        requirements = binding.security_requirements
        if not requirements:
            return {}
        if self._material_provider is None:
            raise RuntimeError("no CredentialMaterialProvider configured")

        by_scheme = {
            record.security_scheme: record
            for record in self._records.list_for_binding(binding.id)
        }
        missing = [scheme for scheme in requirements if scheme not in by_scheme]
        if missing:
            raise PermissionError(
                f"TransportBinding lacks credential references for security schemes: {missing}"
            )

        merged: dict[str, str] = {}
        for scheme, required_scopes in requirements.items():
            record = by_scheme[scheme]
            if tuple(required_scopes) != record.required_scopes:
                raise RuntimeError(
                    "durable credential binding scopes drifted from immutable TransportBinding"
                )
            proof = self._identity_proofs.get(record.identity_proof_id)
            if proof.credential_reference_id != record.credential_reference_id:
                raise RuntimeError(
                    "identity proof credential reference drifted from transport credential binding"
                )
            if not proof.authenticated or not self._identity_proofs.is_current(proof.id):
                raise PermissionError("bound identity proof is no longer current")
            credential = self._credential_references.get(record.credential_reference_id)
            if not _resource_covers_endpoint(credential.resource, binding.endpoint):
                raise ValueError("bound credential resource no longer covers Binding endpoint")
            material = self._material_provider.resolve_headers(
                credential_reference=credential,
                binding=binding,
                security_scheme=scheme,
                identity_proof=proof,
            )
            if not isinstance(material, CredentialHeaderMaterial):
                raise TypeError(
                    "CredentialMaterialProvider must return CredentialHeaderMaterial"
                )
            if material.issuer != credential.issuer:
                raise ValueError("resolved credential issuer drifted from CredentialReference")
            if material.resource != credential.resource:
                raise ValueError("resolved credential resource drifted from CredentialReference")
            if (
                material.expires_at_ms is not None
                and _now_ms() >= int(material.expires_at_ms)
            ):
                raise PermissionError("resolved credential material is expired")
            missing_scopes = [
                scope for scope in required_scopes if scope not in material.granted_scopes
            ]
            if missing_scopes:
                raise PermissionError(
                    f"resolved credential material lacks required scopes: {missing_scopes}"
                )
            if not isinstance(material.evidence_ref, str) or not material.evidence_ref.strip():
                raise ValueError("resolved credential evidence_ref must be non-empty")
            if not isinstance(material.headers, dict):
                raise ValueError("resolved credential headers must be an object")
            for name, value in material.headers.items():
                if (
                    not isinstance(name, str)
                    or not name.strip()
                    or not isinstance(value, str)
                ):
                    raise ValueError("resolved credential headers must contain strings")
                if "\r" in name or "\n" in name or "\r" in value or "\n" in value:
                    raise ValueError("resolved credential headers must not contain CR/LF")
                lowered = name.lower()
                if any(existing.lower() == lowered for existing in merged):
                    raise ValueError(
                        f"multiple security schemes resolved the same header: {name}"
                    )
                merged[name] = value
        return merged


class AgentServiceR14:
    """R14: immutable interface protocol versions plus reference-only transport credentials."""

    def __init__(
        self,
        r13: AgentServiceR13,
        *,
        credential_material_provider: CredentialMaterialProvider | None,
    ) -> None:
        self._r13 = r13
        self._connection = r13._r12._connection
        self.transport_credential_records = TransportCredentialBindingStore(self._connection)
        self.transport_credentials = TransportCredentialBindingCoordinator(
            self._connection,
            bindings=r13.transport_bindings,
            delegations=r13.delegations,
            policy_decisions=r13.policy_decisions,
            credential_references=r13.credential_references,
            identity_proofs=r13.identity_proofs,
            records=self.transport_credential_records,
        )
        self.credential_headers = BoundCredentialHeaderProvider(
            records=self.transport_credential_records,
            credential_references=r13.credential_references,
            identity_proofs=r13.identity_proofs,
            material_provider=credential_material_provider,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._r13, name)

    @classmethod
    def open(
        cls,
        db_path: str | Path,
        *,
        carrier_adapter: CarrierProviderAdapter,
        runtime_adapter: RuntimeAdapter,
        artifact_reader: RuntimeArtifactReader,
        delivery_adapters: dict[str, DeliveryAdapter],
        credential_material_provider: CredentialMaterialProvider | None = None,
        a2a_caller: ProviderCaller | None = None,
        mcp_tasks_caller: ProviderCaller | None = None,
        effect_ledger_reader: EffectLedgerReader | None = None,
        policy_adapter: PolicyAdapter | None = None,
        identity_proof_adapter: IdentityProofAdapter | None = None,
        remote_delivery_observers: dict[str, RemoteDeliveryObserver] | None = None,
        remote_artifact_readers: dict[str, RemoteArtifactReader] | None = None,
        board_adapter: BoardAdapter | None = None,
    ) -> "AgentServiceR14":
        r13 = AgentServiceR13.open(
            db_path,
            carrier_adapter=carrier_adapter,
            runtime_adapter=runtime_adapter,
            artifact_reader=artifact_reader,
            delivery_adapters=delivery_adapters,
            a2a_caller=a2a_caller,
            mcp_tasks_caller=mcp_tasks_caller,
            effect_ledger_reader=effect_ledger_reader,
            policy_adapter=policy_adapter,
            identity_proof_adapter=identity_proof_adapter,
            remote_delivery_observers=remote_delivery_observers or {},
            remote_artifact_readers=remote_artifact_readers or {},
            board_adapter=board_adapter,
        )
        cls._initialize_schema(r13._r12._connection)
        return cls(
            r13,
            credential_material_provider=credential_material_provider,
        )

    @staticmethod
    def _initialize_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS transport_credential_bindings (
                id TEXT PRIMARY KEY,
                client_binding_request_id TEXT NOT NULL UNIQUE,
                binding_id TEXT NOT NULL REFERENCES transport_bindings(id),
                security_scheme TEXT NOT NULL,
                credential_reference_id TEXT NOT NULL REFERENCES credential_references(id),
                identity_proof_id TEXT NOT NULL REFERENCES identity_proof_records(id),
                required_scopes_json TEXT NOT NULL,
                created_at_ns INTEGER NOT NULL,
                UNIQUE(binding_id, security_scheme)
            );
            """
        )
        connection.commit()

    def close(self) -> None:
        self._r13.close()
