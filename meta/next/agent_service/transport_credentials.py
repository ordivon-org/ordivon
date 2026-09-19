from __future__ import annotations

import hashlib
import sqlite3
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

import rfc8785

from .delivery import TransportBinding
from .slice1 import ServiceEvent, ServiceEventStore


def _now_ms() -> int:
    return int(time.time() * 1000)



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


def _transport_credential_scheme_coordinate(
    binding_id: str,
    security_scheme: str,
) -> str:
    return hashlib.sha256(
        rfc8785.dumps([binding_id, security_scheme])
    ).hexdigest()


def _transport_credential_binding_from_event(
    event: ServiceEvent,
) -> TransportCredentialBinding:
    if (
        event.aggregate_type != "TransportCredentialSchemeBinding"
        or event.event_type != "TransportCredentialBindingRecorded"
    ):
        raise ValueError("event is not a transport credential binding receipt")
    payload = event.payload
    required_scopes = payload.get("requiredScopes", [])
    if not isinstance(required_scopes, list) or not all(
        isinstance(scope, str) for scope in required_scopes
    ):
        raise RuntimeError(
            "transport credential binding requiredScopes must be a string array"
        )
    return TransportCredentialBinding(
        id=event.id,
        client_binding_request_id=payload["clientBindingRequestId"],
        binding_id=payload["bindingId"],
        security_scheme=payload["securityScheme"],
        credential_reference_id=payload["credentialReferenceId"],
        identity_proof_id=payload["identityProofId"],
        required_scopes=tuple(required_scopes),
        created_at_ns=event.created_at_ns,
    )


def _transport_credential_binding_get(
    events: ServiceEventStore,
    record_id: str,
) -> TransportCredentialBinding:
    return _transport_credential_binding_from_event(events.get(record_id))


def _transport_credential_binding_get_for_scheme(
    events: ServiceEventStore,
    binding_id: str,
    security_scheme: str,
    *,
    required: bool = True,
) -> TransportCredentialBinding | None:
    coordinate = _transport_credential_scheme_coordinate(binding_id, security_scheme)
    receipts = [
        event
        for event in events.list_for("TransportCredentialSchemeBinding", coordinate)
        if event.event_type == "TransportCredentialBindingRecorded"
    ]
    if not receipts:
        if required:
            raise KeyError((binding_id, security_scheme))
        return None
    if len(receipts) != 1:
        raise RuntimeError(
            "transport credential scheme binding contains multiple receipts"
        )
    record = _transport_credential_binding_from_event(receipts[0])
    if (record.binding_id, record.security_scheme) != (binding_id, security_scheme):
        raise RuntimeError("transport credential scheme coordinate mismatch")
    return record


def _transport_credential_binding_get_by_client_request(
    events: ServiceEventStore,
    client_binding_request_id: str,
    required: bool = True,
) -> TransportCredentialBinding | None:
    aliases = [
        event
        for event in events.list_for(
            "TransportCredentialBindingRequest", client_binding_request_id
        )
        if event.event_type == "TransportCredentialBindingRequestCommitted"
    ]
    if not aliases:
        if required:
            raise KeyError(client_binding_request_id)
        return None
    if len(aliases) != 1:
        raise RuntimeError(
            "transport credential request contains multiple receipts"
        )
    record_id = aliases[0].payload.get("transportCredentialBindingId")
    if not isinstance(record_id, str) or not record_id:
        raise RuntimeError(
            "transport credential request receipt lacks binding record id"
        )
    return _transport_credential_binding_get(events, record_id)


def _transport_credential_binding_list_for_binding(
    events: ServiceEventStore,
    binding_id: str,
) -> list[TransportCredentialBinding]:
    records: list[TransportCredentialBinding] = []
    seen: set[str] = set()
    for event in events.list_for("TransportCredentialBindingIndex", binding_id):
        if event.event_type != "TransportCredentialBindingIndexed":
            continue
        record_id = event.payload.get("transportCredentialBindingId")
        if not isinstance(record_id, str) or not record_id:
            raise RuntimeError("transport credential binding index lacks record id")
        if record_id in seen:
            continue
        record = _transport_credential_binding_get(events, record_id)
        if record.binding_id != binding_id:
            raise RuntimeError("transport credential binding index identity mismatch")
        seen.add(record_id)
        records.append(record)
    return sorted(records, key=lambda item: (item.security_scheme, item.id))


def _transport_credential_binding_create_in_transaction(
    events: ServiceEventStore,
    *,
    client_binding_request_id: str,
    binding_id: str,
    security_scheme: str,
    credential_reference_id: str,
    identity_proof_id: str,
    required_scopes: tuple[str, ...],
) -> TransportCredentialBinding:
    candidate = (
        binding_id,
        security_scheme,
        credential_reference_id,
        identity_proof_id,
        required_scopes,
    )
    existing_request = _transport_credential_binding_get_by_client_request(
        events, client_binding_request_id, required=False
    )
    if existing_request is not None:
        historical = (
            existing_request.binding_id,
            existing_request.security_scheme,
            existing_request.credential_reference_id,
            existing_request.identity_proof_id,
            existing_request.required_scopes,
        )
        if candidate != historical:
            raise ValueError(
                "transport credential binding replay conflicts with committed references"
            )
        return existing_request

    existing_scheme = _transport_credential_binding_get_for_scheme(
        events, binding_id, security_scheme, required=False
    )
    if existing_scheme is not None:
        historical = (
            existing_scheme.binding_id,
            existing_scheme.security_scheme,
            existing_scheme.credential_reference_id,
            existing_scheme.identity_proof_id,
            existing_scheme.required_scopes,
        )
        if candidate != historical:
            raise RuntimeError(
                "transport security scheme is already bound to different credential evidence"
            )
        record = existing_scheme
    else:
        coordinate = _transport_credential_scheme_coordinate(
            binding_id, security_scheme
        )
        event = events.append_once_in_transaction(
            "TransportCredentialSchemeBinding",
            coordinate,
            "TransportCredentialBindingRecorded",
            {
                "clientBindingRequestId": client_binding_request_id,
                "bindingId": binding_id,
                "securityScheme": security_scheme,
                "credentialReferenceId": credential_reference_id,
                "identityProofId": identity_proof_id,
                "requiredScopes": list(required_scopes),
            },
        )
        record = _transport_credential_binding_from_event(event)
        events.append_in_transaction(
            "TransportCredentialBindingIndex",
            binding_id,
            "TransportCredentialBindingIndexed",
            {
                "transportCredentialBindingId": record.id,
                "securityScheme": security_scheme,
            },
        )

    events.append_once_in_transaction(
        "TransportCredentialBindingRequest",
        client_binding_request_id,
        "TransportCredentialBindingRequestCommitted",
        {
            "transportCredentialBindingId": record.id,
            "bindingId": binding_id,
            "securityScheme": security_scheme,
        },
    )
    return record


class TransportCredentialBindingCoordinator:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        bindings: Any,
        delegations: Any,
        credential_references: Any,
        identity_proofs: Any,
        events: ServiceEventStore,
    ) -> None:
        self._connection = connection
        self._bindings = bindings
        self._delegations = delegations
        self._credential_references = credential_references
        self._identity_proofs = identity_proofs
        self._events = events

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
        existing = _transport_credential_binding_get_by_client_request(
            self._events, request_id, required=False
        )
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
        if binding.delegation_id != envelope.id:
            raise PermissionError("binding delegation identity mismatch")

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
            scope for scope in required_scopes if scope not in binding.granted_permissions
        ]
        if missing_policy:
            raise PermissionError(
                f"immutable policy receipt snapshot does not grant required scopes: {missing_policy}"
            )
        if not _resource_covers_endpoint(credential.resource, binding.endpoint):
            raise ValueError(
                "credential resource does not cover immutable TransportBinding endpoint"
            )

        with self._connection:
            return _transport_credential_binding_create_in_transaction(
                self._events,
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




class BoundCredentialHeaderProvider:
    """Resolve transient provider headers from durable reference/proof bindings."""

    def __init__(
        self,
        *,
        events: ServiceEventStore,
        credential_references: Any,
        identity_proofs: Any,
        material_provider: Any | None,
    ) -> None:
        self._events = events
        self._credential_references = credential_references
        self._identity_proofs = identity_proofs
        if material_provider is not None and not callable(
            getattr(material_provider, "resolve_headers", None)
        ):
            raise TypeError(
                "credential material provider must expose callable resolve_headers()"
            )
        self._material_provider = material_provider

    def __repr__(self) -> str:
        return "BoundCredentialHeaderProvider(material=<external/redacted>)"

    def __call__(self, binding: TransportBinding) -> dict[str, str]:
        requirements = binding.security_requirements
        if not requirements:
            return {}
        if self._material_provider is None:
            raise RuntimeError("no credential material provider configured")

        by_scheme = {
            record.security_scheme: record
            for record in _transport_credential_binding_list_for_binding(
                self._events, binding.id
            )
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
                    "credential material provider must return CredentialHeaderMaterial"
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
