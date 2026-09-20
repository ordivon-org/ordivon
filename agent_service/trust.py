from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .delivery import (
    _delivery_receipt_get_by_binding,
)
from .slice1 import ServiceEvent, ServiceEventStore


def _now_ns() -> int:
    return time.time_ns()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


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
    """Immutable cross-owner credential binding.

    Provider handles and authorization metadata remain externally authoritative.
    This store keeps replay identity plus a fail-closed expected contract; secret
    material is never fetched or stored here.
    """

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
            raise ValueError(
                "credential reference identity/provider/reference/issuer/resource must be non-empty"
            )
        scopes = _normalize_strings(requested_scopes, "requested_scopes")
        candidate = (
            provider.strip(),
            reference.strip(),
            issuer.strip(),
            resource.strip(),
            scopes,
        )
        existing = self.get_by_client_reference(
            client_reference_id.strip(), required=False
        )
        if existing is not None:
            historical = (
                existing.provider,
                existing.reference,
                existing.issuer,
                existing.resource,
                existing.requested_scopes,
            )
            if historical != candidate:
                raise ValueError(
                    "credential reference replay conflicts with committed locator"
                )
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
                    json.dumps(
                        list(value.requested_scopes),
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ),
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


def _identity_proof_record_from_event(
    event: ServiceEvent,
) -> IdentityProofRecord:
    if (
        event.aggregate_type != "IdentityProof"
        or event.event_type != "IdentityProofRecorded"
    ):
        raise ValueError("event is not an identity proof receipt")
    payload = event.payload
    if payload.get("clientProofRequestId") != event.aggregate_id:
        raise RuntimeError("identity proof request identity mismatch")
    authenticated = payload.get("authenticated")
    if not isinstance(authenticated, bool):
        raise RuntimeError("identity proof authenticated must be boolean")
    return IdentityProofRecord(
        id=event.id,
        client_proof_request_id=event.aggregate_id,
        identity_id=payload["identityId"],
        credential_reference_id=payload["credentialReferenceId"],
        purpose=payload["purpose"],
        authenticated=authenticated,
        principal_id=payload.get("principalId"),
        issuer=payload["issuer"],
        auth_method=payload["authMethod"],
        observed_at_ms=int(payload["observedAtMs"]),
        expires_at_ms=(
            None if payload.get("expiresAtMs") is None else int(payload["expiresAtMs"])
        ),
        evidence_ref=payload["evidenceRef"],
        created_at_ns=event.created_at_ns,
    )


def _identity_proof_record_get(
    events: ServiceEventStore,
    proof_id: str,
) -> IdentityProofRecord:
    return _identity_proof_record_from_event(events.get(proof_id))


def _identity_proof_record_get_by_client_request(
    events: ServiceEventStore,
    client_proof_request_id: str,
    required: bool = True,
) -> IdentityProofRecord | None:
    receipts = [
        event
        for event in events.list_for("IdentityProof", client_proof_request_id)
        if event.event_type == "IdentityProofRecorded"
    ]
    if not receipts:
        if required:
            raise KeyError(client_proof_request_id)
        return None
    if len(receipts) != 1:
        raise RuntimeError("identity proof stream contains multiple records")
    return _identity_proof_record_from_event(receipts[0])


def _identity_proof_record_create(
    events: ServiceEventStore,
    *,
    client_proof_request_id: str,
    identity_id: str,
    credential_reference_id: str,
    purpose: str,
    observation: IdentityProofObservation,
    observed_at_ms: int,
) -> IdentityProofRecord:
    event = events.append_once(
        "IdentityProof",
        client_proof_request_id,
        "IdentityProofRecorded",
        {
            "clientProofRequestId": client_proof_request_id,
            "identityId": identity_id,
            "credentialReferenceId": credential_reference_id,
            "purpose": purpose,
            "authenticated": bool(observation.authenticated),
            "principalId": observation.principal_id,
            "issuer": observation.issuer,
            "authMethod": observation.auth_method,
            "observedAtMs": int(observed_at_ms),
            "expiresAtMs": observation.expires_at_ms,
            "evidenceRef": observation.evidence_ref,
        },
    )
    return _identity_proof_record_from_event(event)


class IdentityProofCoordinator:
    """Durable authentication evidence; never mutates AgentIdentity or grants authorization."""

    def __init__(
        self,
        identities: Any,
        credentials: CredentialReferenceStore,
        events: ServiceEventStore,
        adapter: Any | None,
    ) -> None:
        self._identities = identities
        self._credentials = credentials
        self._events = events
        self.set_adapter(adapter)

    def set_adapter(self, adapter: Any | None) -> None:
        if adapter is not None and not callable(getattr(adapter, "verify", None)):
            raise TypeError("identity proof provider must expose callable verify()")
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
        if (
            not isinstance(client_proof_request_id, str)
            or not client_proof_request_id.strip()
        ):
            raise ValueError("client_proof_request_id must be non-empty")
        if not isinstance(purpose, str) or not purpose.strip():
            raise ValueError("identity proof purpose must be non-empty")
        existing = _identity_proof_record_get_by_client_request(
            self._events, client_proof_request_id.strip(), required=False
        )
        if existing is not None:
            candidate = (identity_id, credential_reference_id, purpose.strip())
            historical = (
                existing.identity_id,
                existing.credential_reference_id,
                existing.purpose,
            )
            if candidate != historical:
                raise ValueError(
                    "identity proof request replay conflicts with committed proof"
                )
            return existing
        self._identities.get(identity_id)
        credential = self._credentials.get(credential_reference_id)
        if self._adapter is None:
            raise RuntimeError("no identity proof provider configured")
        request = IdentityProofRequest(
            identity_id=identity_id,
            credential_reference_id=credential_reference_id,
            purpose=purpose.strip(),
            resource=credential.resource,
        )
        observation = self._adapter.verify(request, credential)
        if not isinstance(observation, IdentityProofObservation):
            raise TypeError(
                "identity proof provider must return IdentityProofObservation"
            )
        if not isinstance(observation.issuer, str) or not observation.issuer.strip():
            raise ValueError("identity proof issuer must be non-empty")
        if observation.issuer != credential.issuer:
            raise ValueError(
                "identity proof issuer does not match credential reference issuer"
            )
        if (
            not isinstance(observation.auth_method, str)
            or not observation.auth_method.strip()
        ):
            raise ValueError("identity proof auth_method must be non-empty")
        if (
            not isinstance(observation.evidence_ref, str)
            or not observation.evidence_ref.strip()
        ):
            raise ValueError("identity proof evidence_ref must be non-empty")
        if observation.authenticated and (
            not isinstance(observation.principal_id, str)
            or not observation.principal_id.strip()
        ):
            raise ValueError("authenticated identity proof requires a principal_id")
        when_ms = _now_ms() if observed_at_ms is None else int(observed_at_ms)
        return _identity_proof_record_create(
            self._events,
            client_proof_request_id=client_proof_request_id.strip(),
            identity_id=identity_id,
            credential_reference_id=credential_reference_id,
            purpose=purpose.strip(),
            observation=observation,
            observed_at_ms=when_ms,
        )

    def get(self, proof_id: str) -> IdentityProofRecord:
        return _identity_proof_record_get(self._events, proof_id)

    def is_current(self, proof_id: str, *, at_ms: int | None = None) -> bool:
        proof = _identity_proof_record_get(self._events, proof_id)
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


def _remote_delivery_observation_from_event(
    event: ServiceEvent,
) -> RemoteDeliverySnapshot:
    if (
        event.aggregate_type != "RemoteDeliveryObservation"
        or event.event_type != "RemoteDeliveryObserved"
    ):
        raise ValueError("event is not a remote delivery observation")
    payload = event.payload
    if payload.get("bindingId") != event.aggregate_id:
        raise RuntimeError("remote delivery observation Binding identity mismatch")
    raw_success = payload.get("successful")
    if raw_success is not None and not isinstance(raw_success, bool):
        raise RuntimeError(
            "remote delivery observation successful must be boolean or null"
        )
    artifact_refs = payload.get("artifactRefs", [])
    if not isinstance(artifact_refs, list) or not all(
        isinstance(x, str) for x in artifact_refs
    ):
        raise RuntimeError(
            "remote delivery observation artifactRefs must be a string array"
        )
    return RemoteDeliverySnapshot(
        id=event.id,
        binding_id=event.aggregate_id,
        sequence=event.sequence,
        provider_status=payload["providerStatus"],
        terminal=bool(payload["terminal"]),
        successful=raw_success,
        remote_task_id=payload.get("remoteTaskId"),
        remote_context_id=payload.get("remoteContextId"),
        artifact_refs=tuple(artifact_refs),
        evidence_ref=payload["evidenceRef"],
        observed_at_ms=int(payload["observedAtMs"]),
        created_at_ns=event.created_at_ns,
    )


def _remote_delivery_observation_list_for_binding(
    events: ServiceEventStore,
    binding_id: str,
) -> list[RemoteDeliverySnapshot]:
    return [
        _remote_delivery_observation_from_event(event)
        for event in events.list_for("RemoteDeliveryObservation", binding_id)
        if event.event_type == "RemoteDeliveryObserved"
    ]


def _remote_delivery_observation_latest_for_binding(
    events: ServiceEventStore,
    binding_id: str,
    required: bool = True,
) -> RemoteDeliverySnapshot | None:
    history = _remote_delivery_observation_list_for_binding(events, binding_id)
    if not history:
        if required:
            raise KeyError(binding_id)
        return None
    return history[-1]


def _remote_delivery_observation_record(
    events: ServiceEventStore,
    *,
    binding_id: str,
    observation: RemoteProviderObservation,
    observed_at_ms: int | None = None,
) -> RemoteDeliverySnapshot:
    latest = _remote_delivery_observation_latest_for_binding(
        events, binding_id, required=False
    )
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

    event = events.append(
        "RemoteDeliveryObservation",
        binding_id,
        "RemoteDeliveryObserved",
        {
            "bindingId": binding_id,
            "providerStatus": observation.provider_status,
            "terminal": bool(observation.terminal),
            "successful": observation.successful,
            "remoteTaskId": observation.remote_task_id,
            "remoteContextId": observation.remote_context_id,
            "artifactRefs": list(observation.artifact_refs),
            "evidenceRef": observation.evidence_ref,
            "observedAtMs": _now_ms()
            if observed_at_ms is None
            else int(observed_at_ms),
        },
    )
    return _remote_delivery_observation_from_event(event)


class RemoteCorrelationReconciler:
    def __init__(
        self,
        delegations: Any,
        bindings: Any,
        delivery_events: ServiceEventStore,
        observers: dict[str, Any],
    ) -> None:
        self._delegations = delegations
        self._bindings = bindings
        self._delivery_events = delivery_events
        for transport, observer in observers.items():
            if not isinstance(transport, str) or not transport.strip():
                raise TypeError(
                    "remote observer transport key must be a non-empty string"
                )
            if not callable(getattr(observer, "observe", None)):
                raise TypeError(
                    f"remote observer for {transport!r} must expose callable observe()"
                )
        self._observers = dict(observers)

    def reconcile(self, binding_id: str) -> RemoteDeliverySnapshot:
        binding = self._bindings.get(binding_id)
        receipt = _delivery_receipt_get_by_binding(self._delivery_events, binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        observer = self._observers.get(binding.transport)
        if observer is None:
            raise LookupError(
                f"no remote delivery observer registered for {binding.transport}"
            )
        observation = observer.observe(
            binding=binding, receipt=receipt, envelope=envelope
        )
        if not isinstance(observation, RemoteProviderObservation):
            raise TypeError(
                "remote delivery observer must return RemoteProviderObservation"
            )
        if (
            not isinstance(observation.provider_status, str)
            or not observation.provider_status.strip()
        ):
            raise ValueError("remote provider status must be non-empty")
        if (
            not isinstance(observation.evidence_ref, str)
            or not observation.evidence_ref.strip()
        ):
            raise ValueError("remote observation evidence_ref must be non-empty")
        if (
            receipt.remote_task_id is not None
            and observation.remote_task_id != receipt.remote_task_id
        ):
            raise ValueError("remote task correlation changed from delivery receipt")
        if (
            receipt.remote_context_id is not None
            and observation.remote_context_id != receipt.remote_context_id
        ):
            raise ValueError("remote context correlation changed from delivery receipt")
        latest = _remote_delivery_observation_latest_for_binding(
            self._delivery_events, binding.id, required=False
        )
        if latest is not None:
            if (
                latest.remote_task_id is not None
                and observation.remote_task_id != latest.remote_task_id
            ):
                raise ValueError(
                    "remote task correlation changed from established observation"
                )
            if (
                latest.remote_context_id is not None
                and observation.remote_context_id != latest.remote_context_id
            ):
                raise ValueError(
                    "remote context correlation changed from established observation"
                )
        return _remote_delivery_observation_record(
            self._delivery_events, binding_id=binding.id, observation=observation
        )


class AuditEnvelopeProjector:
    """Pure audit projection over authoritative stores. No audit state table is created."""

    def __init__(
        self,
        proofs: ServiceEventStore,
        bindings: Any,
        delivery_events: ServiceEventStore,
        delegations: Any,
    ) -> None:
        self._proofs = proofs
        self._bindings = bindings
        self._delivery_events = delivery_events
        self._delegations = delegations

    def project_identity_proof(self, proof_id: str) -> dict[str, Any]:
        proof = _identity_proof_record_get(self._proofs, proof_id)
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
        receipt = _delivery_receipt_get_by_binding(self._delivery_events, binding_id)
        envelope = self._delegations.get(binding.delegation_id)
        latest = _remote_delivery_observation_latest_for_binding(
            self._delivery_events, binding_id, required=False
        )
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
