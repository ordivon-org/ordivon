"""Evidence-only gateway Provider binding and upstream-attempt observations.

This module does not dispatch Provider calls, select credentials, choose network routes,
retry requests, or determine semantic completion.  It only validates a bounded projection
that an Adapter may later attach to the existing Harness Provider lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Any

from anc_canonical import canonical_digest

from ..protocol import HarnessProtocolError


_INGRESS_PROTOCOLS = {
    "openai-chat",
    "openai-responses",
    "claude-messages",
    "gemini-native",
    "other",
}
_ATTEMPT_STANDINGS = {
    "not_dispatched",
    "failed_before_commit",
    "dispatched_unknown",
    "committed",
    "cancelled",
}
_STREAM_TERMINAL_STANDINGS = {
    "complete",
    "incomplete",
    "not_streaming",
    "unknown",
}


def _text(value: object, label: str, *, max_bytes: int = 512) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise HarnessProtocolError(f"{label} must be a non-empty trimmed string")
    if len(value.encode("utf-8")) > max_bytes:
        raise HarnessProtocolError(f"{label} exceeds {max_bytes} UTF-8 bytes")
    return value


def _optional_text(value: object, label: str, *, max_bytes: int = 512) -> str | None:
    if value is None:
        return None
    return _text(value, label, max_bytes=max_bytes)


def _digest(value: object, label: str) -> str:
    text = _text(value, label, max_bytes=71)
    if (
        not text.startswith("sha256:")
        or len(text) != 71
        or any(character not in "0123456789abcdef" for character in text[7:])
    ):
        raise HarnessProtocolError(f"{label} must be sha256:<64 lowercase hex>")
    return text


def _loopback_http_endpoint(value: object) -> str:
    text = _text(value, "gateway endpoint", max_bytes=512)
    parsed = urlparse(text)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise HarnessProtocolError(
            "gateway endpoint must be an explicit loopback HTTP endpoint"
        )
    if parsed.port is None or parsed.port <= 0 or parsed.port > 65_535:
        raise HarnessProtocolError("gateway endpoint must include a valid TCP port")
    if parsed.username is not None or parsed.password is not None:
        raise HarnessProtocolError("gateway endpoint must not embed credentials")
    if parsed.query or parsed.fragment:
        raise HarnessProtocolError("gateway endpoint must not include query or fragment")
    return text


def _exact(value: dict[str, Any], fields: set[str], label: str) -> None:
    if set(value) != fields:
        raise HarnessProtocolError(
            f"{label} fields differ: {sorted(set(value) ^ fields)}"
        )


@dataclass(frozen=True, slots=True)
class HarnessGatewayProviderBinding:
    """Non-authoritative binding evidence for one local gateway route."""

    gateway_implementation: str
    gateway_source_identity: str
    endpoint: str
    ingress_protocol: str
    capability_profile_digest: str
    requested_provider: str
    requested_model: str
    credential_authority_ref: str
    network_authority_ref: str
    direct_fallback: bool
    route_policy_ref: str | None = None
    credential_name_ref: str | None = None
    network_egress_profile_ref: str | None = None
    allowed_effective_providers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.gateway_implementation, "gateway implementation", max_bytes=200)
        _text(self.gateway_source_identity, "gateway source identity", max_bytes=300)
        _loopback_http_endpoint(self.endpoint)
        if self.ingress_protocol not in _INGRESS_PROTOCOLS:
            raise HarnessProtocolError("gateway ingress protocol is invalid")
        _digest(self.capability_profile_digest, "gateway capability profile digest")
        _text(self.requested_provider, "requested Provider", max_bytes=200)
        _text(self.requested_model, "requested model", max_bytes=300)
        _text(self.credential_authority_ref, "credential authority reference", max_bytes=300)
        _text(self.network_authority_ref, "network authority reference", max_bytes=300)
        if type(self.direct_fallback) is not bool:
            raise HarnessProtocolError("gateway directFallback must be boolean")
        _optional_text(self.route_policy_ref, "route policy reference", max_bytes=300)
        _optional_text(self.credential_name_ref, "credential name reference", max_bytes=300)
        _optional_text(
            self.network_egress_profile_ref,
            "network egress profile reference",
            max_bytes=300,
        )
        providers = tuple(
            _text(provider, "allowed effective Provider", max_bytes=200)
            for provider in self.allowed_effective_providers
        )
        if len(providers) != len(set(providers)):
            raise HarnessProtocolError("allowed effective Providers must be unique")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.harness-gateway-provider-binding",
            "gatewayImplementation": self.gateway_implementation,
            "gatewaySourceIdentity": self.gateway_source_identity,
            "endpoint": self.endpoint,
            "ingressProtocol": self.ingress_protocol,
            "capabilityProfileDigest": self.capability_profile_digest,
            "requestedProvider": self.requested_provider,
            "requestedModel": self.requested_model,
            "credentialAuthorityRef": self.credential_authority_ref,
            "networkAuthorityRef": self.network_authority_ref,
            "directFallback": self.direct_fallback,
            "routePolicyRef": self.route_policy_ref,
            "credentialNameRef": self.credential_name_ref,
            "networkEgressProfileRef": self.network_egress_profile_ref,
            "allowedEffectiveProviders": list(self.allowed_effective_providers),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "HarnessGatewayProviderBinding":
        fields = {
            "schemaVersion",
            "kind",
            "gatewayImplementation",
            "gatewaySourceIdentity",
            "endpoint",
            "ingressProtocol",
            "capabilityProfileDigest",
            "requestedProvider",
            "requestedModel",
            "credentialAuthorityRef",
            "networkAuthorityRef",
            "directFallback",
            "routePolicyRef",
            "credentialNameRef",
            "networkEgressProfileRef",
            "allowedEffectiveProviders",
        }
        _exact(value, fields, "HarnessGatewayProviderBinding")
        if (
            value["schemaVersion"] != 1
            or value["kind"] != "ordivon.harness-gateway-provider-binding"
        ):
            raise HarnessProtocolError(
                "HarnessGatewayProviderBinding version or kind is invalid"
            )
        raw_providers = value["allowedEffectiveProviders"]
        if not isinstance(raw_providers, list):
            raise HarnessProtocolError("allowedEffectiveProviders must be a list")
        return cls(
            gateway_implementation=value["gatewayImplementation"],
            gateway_source_identity=value["gatewaySourceIdentity"],
            endpoint=value["endpoint"],
            ingress_protocol=value["ingressProtocol"],
            capability_profile_digest=value["capabilityProfileDigest"],
            requested_provider=value["requestedProvider"],
            requested_model=value["requestedModel"],
            credential_authority_ref=value["credentialAuthorityRef"],
            network_authority_ref=value["networkAuthorityRef"],
            direct_fallback=value["directFallback"],
            route_policy_ref=value["routePolicyRef"],
            credential_name_ref=value["credentialNameRef"],
            network_egress_profile_ref=value["networkEgressProfileRef"],
            allowed_effective_providers=tuple(raw_providers),
        )


@dataclass(frozen=True, slots=True)
class HarnessGatewayAttemptObservation:
    """One observed internal gateway upstream attempt; never an execution instruction."""

    sequence: int
    provider: str
    model: str
    standing: str
    connection_ref: str | None = None
    retry_or_fallback_reason: str | None = None
    provider_request_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.sequence) is not int or self.sequence < 1:
            raise HarnessProtocolError("gateway attempt sequence must be an integer >= 1")
        _text(self.provider, "gateway attempt Provider", max_bytes=200)
        _text(self.model, "gateway attempt model", max_bytes=300)
        if self.standing not in _ATTEMPT_STANDINGS:
            raise HarnessProtocolError("gateway attempt standing is invalid")
        _optional_text(self.connection_ref, "gateway connection reference", max_bytes=300)
        _optional_text(
            self.retry_or_fallback_reason,
            "gateway retry/fallback reason",
            max_bytes=1_024,
        )
        _optional_text(self.provider_request_id, "Provider request identity", max_bytes=300)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "provider": self.provider,
            "model": self.model,
            "standing": self.standing,
            "connectionRef": self.connection_ref,
            "retryOrFallbackReason": self.retry_or_fallback_reason,
            "providerRequestId": self.provider_request_id,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "HarnessGatewayAttemptObservation":
        fields = {
            "sequence",
            "provider",
            "model",
            "standing",
            "connectionRef",
            "retryOrFallbackReason",
            "providerRequestId",
        }
        _exact(value, fields, "HarnessGatewayAttemptObservation")
        return cls(
            sequence=value["sequence"],
            provider=value["provider"],
            model=value["model"],
            standing=value["standing"],
            connection_ref=value["connectionRef"],
            retry_or_fallback_reason=value["retryOrFallbackReason"],
            provider_request_id=value["providerRequestId"],
        )


@dataclass(frozen=True, slots=True)
class HarnessGatewayProviderCallObservation:
    """Bounded evidence about a gateway-internal Provider call.

    This object deliberately has no dispatch/retry/cancel methods.  Unknown dispatch
    standing fences later attempts rather than licensing recovery.
    """

    binding_digest: str
    provider_call_ref: str
    gateway_request_digest: str
    attempts: tuple[HarnessGatewayAttemptObservation, ...]
    stream_terminal_standing: str
    translator_path: tuple[str, ...] = ()
    effective_provider: str | None = None
    effective_model: str | None = None
    effective_connection_ref: str | None = None
    response_digest: str | None = None
    evidence_refs: tuple[str, ...] = ()
    unknown_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _digest(self.binding_digest, "gateway binding digest")
        _text(self.provider_call_ref, "Provider Call reference", max_bytes=300)
        _digest(self.gateway_request_digest, "gateway request digest")
        if not self.attempts:
            raise HarnessProtocolError("gateway call observation requires at least one attempt")
        expected = list(range(1, len(self.attempts) + 1))
        actual = [attempt.sequence for attempt in self.attempts]
        if actual != expected:
            raise HarnessProtocolError("gateway attempt sequences must be contiguous from 1")
        unknown_indexes = [
            index
            for index, attempt in enumerate(self.attempts)
            if attempt.standing == "dispatched_unknown"
        ]
        if unknown_indexes and unknown_indexes[-1] != len(self.attempts) - 1:
            raise HarnessProtocolError(
                "gateway must not report later attempts after dispatched_unknown"
            )
        if len(unknown_indexes) > 1:
            raise HarnessProtocolError("gateway call has multiple dispatched_unknown attempts")
        committed = [
            attempt for attempt in self.attempts if attempt.standing == "committed"
        ]
        if len(committed) > 1:
            raise HarnessProtocolError("gateway call has multiple committed attempts")
        if committed and committed[0] is not self.attempts[-1]:
            raise HarnessProtocolError("committed gateway attempt must be terminal")
        if committed:
            if self.effective_provider != committed[0].provider:
                raise HarnessProtocolError(
                    "effective Provider differs from committed gateway attempt"
                )
            if self.effective_model != committed[0].model:
                raise HarnessProtocolError(
                    "effective model differs from committed gateway attempt"
                )
        elif self.effective_provider is not None or self.effective_model is not None:
            raise HarnessProtocolError(
                "non-committed gateway observation cannot claim effective Provider/model"
            )
        if self.stream_terminal_standing not in _STREAM_TERMINAL_STANDINGS:
            raise HarnessProtocolError("gateway stream terminal standing is invalid")
        for index, value in enumerate(self.translator_path):
            _text(value, f"translator path item {index}", max_bytes=300)
        _optional_text(
            self.effective_connection_ref,
            "effective gateway connection reference",
            max_bytes=300,
        )
        if self.response_digest is not None:
            _digest(self.response_digest, "gateway response digest")
        request_ids = [
            attempt.provider_request_id
            for attempt in self.attempts
            if attempt.provider_request_id is not None
        ]
        if len(request_ids) != len(set(request_ids)):
            raise HarnessProtocolError("Provider request identities must be unique")
        for index, value in enumerate(self.evidence_refs):
            _text(value, f"gateway evidence reference {index}", max_bytes=500)
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise HarnessProtocolError("gateway evidence references must be unique")
        for index, value in enumerate(self.unknown_fields):
            _text(value, f"gateway unknown field {index}", max_bytes=300)
        if len(self.unknown_fields) != len(set(self.unknown_fields)):
            raise HarnessProtocolError("gateway unknown fields must be unique")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.harness-gateway-provider-call-observation",
            "bindingDigest": self.binding_digest,
            "providerCallRef": self.provider_call_ref,
            "gatewayRequestDigest": self.gateway_request_digest,
            "translatorPath": list(self.translator_path),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "effectiveProvider": self.effective_provider,
            "effectiveModel": self.effective_model,
            "effectiveConnectionRef": self.effective_connection_ref,
            "streamTerminalStanding": self.stream_terminal_standing,
            "responseDigest": self.response_digest,
            "evidenceRefs": list(self.evidence_refs),
            "unknownFields": list(self.unknown_fields),
        }

    @classmethod
    def from_dict(
        cls, value: dict[str, Any]
    ) -> "HarnessGatewayProviderCallObservation":
        fields = {
            "schemaVersion",
            "kind",
            "bindingDigest",
            "providerCallRef",
            "gatewayRequestDigest",
            "translatorPath",
            "attempts",
            "effectiveProvider",
            "effectiveModel",
            "effectiveConnectionRef",
            "streamTerminalStanding",
            "responseDigest",
            "evidenceRefs",
            "unknownFields",
        }
        _exact(value, fields, "HarnessGatewayProviderCallObservation")
        if (
            value["schemaVersion"] != 1
            or value["kind"] != "ordivon.harness-gateway-provider-call-observation"
        ):
            raise HarnessProtocolError(
                "HarnessGatewayProviderCallObservation version or kind is invalid"
            )
        raw_path = value["translatorPath"]
        raw_attempts = value["attempts"]
        raw_evidence = value["evidenceRefs"]
        raw_unknown = value["unknownFields"]
        if not isinstance(raw_path, list):
            raise HarnessProtocolError("translatorPath must be a list")
        if not isinstance(raw_attempts, list):
            raise HarnessProtocolError("attempts must be a list")
        if not isinstance(raw_evidence, list):
            raise HarnessProtocolError("evidenceRefs must be a list")
        if not isinstance(raw_unknown, list):
            raise HarnessProtocolError("unknownFields must be a list")
        return cls(
            binding_digest=value["bindingDigest"],
            provider_call_ref=value["providerCallRef"],
            gateway_request_digest=value["gatewayRequestDigest"],
            translator_path=tuple(raw_path),
            attempts=tuple(
                HarnessGatewayAttemptObservation.from_dict(item)
                for item in raw_attempts
            ),
            effective_provider=value["effectiveProvider"],
            effective_model=value["effectiveModel"],
            effective_connection_ref=value["effectiveConnectionRef"],
            stream_terminal_standing=value["streamTerminalStanding"],
            response_digest=value["responseDigest"],
            evidence_refs=tuple(raw_evidence),
            unknown_fields=tuple(raw_unknown),
        )


__all__ = [
    "HarnessGatewayAttemptObservation",
    "HarnessGatewayProviderBinding",
    "HarnessGatewayProviderCallObservation",
]
