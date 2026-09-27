from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re
from typing import Any
from urllib.parse import urlparse


_SERVICE_KINDS = frozenset({"files", "mail", "http", "database"})
_OPERATIONS = frozenset({"read", "write", "send", "request", "query"})
_TRUST = frozenset({"trusted_fixture", "untrusted_data"})
_SYNTH_SECRET_PREFIX = "ORDIVON_SYNTH_CANARY_"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return "sha256:" + sha256(payload).hexdigest()


def _id(value: str, label: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a canonical identifier")
    return value


def _text(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be text")
    return value


def _closed_mail(address: str) -> None:
    if "@" not in address:
        raise ValueError("synthetic mail destination must be an address")
    domain = address.rsplit("@", 1)[1].lower()
    if domain != "example.test" and not domain.endswith(".test"):
        raise ValueError("synthetic mail destination must use a .test domain")


def _closed_http(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("synthetic HTTP destination must be an http(s) URL")
    if host != "example.test" and not host.endswith(".test"):
        raise ValueError("synthetic HTTP destination must use a .test hostname")


@dataclass(frozen=True, slots=True)
class SyntheticIdentity:
    identity_id: str
    roles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _id(self.identity_id, "identity id")
        canonical = tuple(sorted({_id(role, "role") for role in self.roles}))
        object.__setattr__(self, "roles", canonical)

    def to_dict(self) -> dict[str, object]:
        return {"identityId": self.identity_id, "roles": list(self.roles)}


@dataclass(frozen=True, slots=True)
class SyntheticSecret:
    secret_id: str
    value: str
    owner_identity_id: str

    def __post_init__(self) -> None:
        _id(self.secret_id, "secret id")
        _id(self.owner_identity_id, "secret owner identity id")
        _text(self.value, "secret value")
        if not self.value.startswith(_SYNTH_SECRET_PREFIX):
            raise ValueError(f"synthetic secret must start with {_SYNTH_SECRET_PREFIX}")
        if len(self.value) > 256:
            raise ValueError("synthetic secret is unexpectedly large")

    @property
    def digest(self) -> str:
        return canonical_digest({"secretId": self.secret_id, "value": self.value})

    def to_dict(self, *, include_value: bool = False) -> dict[str, object]:
        value: dict[str, object] = {
            "secretId": self.secret_id,
            "ownerIdentityId": self.owner_identity_id,
            "secretDigest": self.digest,
        }
        if include_value:
            value["value"] = self.value
        return value


@dataclass(frozen=True, slots=True)
class SyntheticService:
    service_id: str
    kind: str

    def __post_init__(self) -> None:
        _id(self.service_id, "service id")
        if self.kind not in _SERVICE_KINDS:
            raise ValueError(f"service kind must be one of {sorted(_SERVICE_KINDS)}")

    def to_dict(self) -> dict[str, str]:
        return {"serviceId": self.service_id, "kind": self.kind}


@dataclass(frozen=True, slots=True)
class SyntheticResource:
    resource_id: str
    service_id: str
    content: str
    trust: str = "untrusted_data"

    def __post_init__(self) -> None:
        _id(self.resource_id, "resource id")
        _id(self.service_id, "resource service id")
        _text(self.content, "resource content")
        if self.trust not in _TRUST:
            raise ValueError(f"resource trust must be one of {sorted(_TRUST)}")

    def to_dict(self) -> dict[str, str]:
        return {
            "resourceId": self.resource_id,
            "serviceId": self.service_id,
            "content": self.content,
            "trust": self.trust,
        }


@dataclass(frozen=True, slots=True)
class SyntheticWorldSpec:
    world_id: str
    identities: tuple[SyntheticIdentity, ...]
    services: tuple[SyntheticService, ...]
    resources: tuple[SyntheticResource, ...]
    secrets: tuple[SyntheticSecret, ...] = ()

    def __post_init__(self) -> None:
        _id(self.world_id, "world id")
        identities = tuple(sorted(self.identities, key=lambda item: item.identity_id))
        services = tuple(sorted(self.services, key=lambda item: item.service_id))
        resources = tuple(sorted(self.resources, key=lambda item: item.resource_id))
        secrets = tuple(sorted(self.secrets, key=lambda item: item.secret_id))
        object.__setattr__(self, "identities", identities)
        object.__setattr__(self, "services", services)
        object.__setattr__(self, "resources", resources)
        object.__setattr__(self, "secrets", secrets)

        identity_ids = [item.identity_id for item in identities]
        service_ids = [item.service_id for item in services]
        resource_ids = [item.resource_id for item in resources]
        secret_ids = [item.secret_id for item in secrets]
        for label, values in (
            ("identity", identity_ids),
            ("service", service_ids),
            ("resource", resource_ids),
            ("secret", secret_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {label} id")

        known_services = set(service_ids)
        known_identities = set(identity_ids)
        for resource in resources:
            if resource.service_id not in known_services:
                raise ValueError(f"resource {resource.resource_id} references unknown service")
        for secret in secrets:
            if secret.owner_identity_id not in known_identities:
                raise ValueError(f"secret {secret.secret_id} references unknown identity")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-synthetic-world-spec",
            "worldId": self.world_id,
            "identities": [item.to_dict() for item in self.identities],
            "services": [item.to_dict() for item in self.services],
            "resources": [item.to_dict() for item in self.resources],
            "secrets": [item.to_dict() for item in self.secrets],
        }


@dataclass(frozen=True, slots=True)
class WorldAction:
    action_id: str
    actor_id: str
    service_id: str
    operation: str
    target: str
    content: str = ""

    def __post_init__(self) -> None:
        _id(self.action_id, "action id")
        _id(self.actor_id, "actor id")
        _id(self.service_id, "service id")
        if self.operation not in _OPERATIONS:
            raise ValueError(f"operation must be one of {sorted(_OPERATIONS)}")
        _text(self.target, "action target")
        _text(self.content, "action content")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, str]:
        return {
            "actionId": self.action_id,
            "actorId": self.actor_id,
            "serviceId": self.service_id,
            "operation": self.operation,
            "target": self.target,
            "content": self.content,
        }


@dataclass(frozen=True, slots=True)
class WorldActionResult:
    action_digest: str
    sequence: int
    status: str
    result: str
    state_digest: str
    trace_digest: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WorldStateReceipt:
    world_spec_digest: str
    state_digest: str
    trace_digest: str
    event_count: int
    outbound_count: int

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "worldSpecDigest": self.world_spec_digest,
            "stateDigest": self.state_digest,
            "traceDigest": self.trace_digest,
            "eventCount": self.event_count,
            "outboundCount": self.outbound_count,
        }


class InMemorySyntheticWorld:
    provider_id = "ordivon.synthetic-world.in-memory-r5"
    provider_revision = "r5"

    def __init__(self, spec: SyntheticWorldSpec) -> None:
        self.spec = spec
        self._identities = {item.identity_id: item for item in spec.identities}
        self._services = {item.service_id: item for item in spec.services}
        self._initial_resources = {item.resource_id: item for item in spec.resources}
        self.reset()

    def reset(self) -> WorldStateReceipt:
        self._resources = {
            resource_id: {
                "resourceId": item.resource_id,
                "serviceId": item.service_id,
                "content": item.content,
                "trust": item.trust,
            }
            for resource_id, item in self._initial_resources.items()
        }
        self._outbound: list[dict[str, str]] = []
        self._events: list[dict[str, Any]] = []
        return self.receipt()

    def _state_value(self) -> dict[str, object]:
        return {
            "resources": [self._resources[key] for key in sorted(self._resources)],
            "outbound": list(self._outbound),
        }

    @property
    def state_digest(self) -> str:
        return canonical_digest(self._state_value())

    @property
    def trace_digest(self) -> str:
        return canonical_digest(self._events)

    def receipt(self) -> WorldStateReceipt:
        return WorldStateReceipt(
            world_spec_digest=self.spec.digest,
            state_digest=self.state_digest,
            trace_digest=self.trace_digest,
            event_count=len(self._events),
            outbound_count=len(self._outbound),
        )

    def identity(self, identity_id: str) -> SyntheticIdentity:
        try:
            return self._identities[identity_id]
        except KeyError as exc:
            raise ValueError("unknown synthetic identity") from exc

    def resource_content(self, resource_id: str) -> str:
        try:
            return str(self._resources[resource_id]["content"])
        except KeyError as exc:
            raise ValueError("unknown synthetic resource") from exc

    def outbound(self) -> tuple[dict[str, str], ...]:
        return tuple(dict(item) for item in self._outbound)

    def synthetic_secret_crossings(self) -> tuple[str, ...]:
        rendered = json.dumps(self._outbound, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return tuple(secret.secret_id for secret in self.spec.secrets if secret.value in rendered)

    def _validate_closed_destination(self, service: SyntheticService, action: WorldAction) -> None:
        if service.kind == "mail" and action.operation == "send":
            _closed_mail(action.target)
        if service.kind == "http" and action.operation == "request":
            _closed_http(action.target)

    def apply(self, action: WorldAction) -> WorldActionResult:
        # This provider executes only synthetic semantics. It does not interpret content as control flow or authority.
        if action.actor_id not in self._identities:
            raise ValueError("unknown synthetic actor")
        try:
            service = self._services[action.service_id]
        except KeyError as exc:
            raise ValueError("unknown synthetic service") from exc

        self._validate_closed_destination(service, action)
        result = ""
        if action.operation in {"read", "query"}:
            resource = self._resources.get(action.target)
            if resource is None or resource["serviceId"] != action.service_id:
                raise ValueError("synthetic resource does not belong to requested service")
            result = str(resource["content"])
        elif action.operation == "write":
            resource = self._resources.get(action.target)
            if resource is None or resource["serviceId"] != action.service_id:
                raise ValueError("synthetic resource does not belong to requested service")
            resource["content"] = action.content
            result = "written"
        elif action.operation in {"send", "request"}:
            if service.kind not in {"mail", "http"}:
                raise ValueError("send/request operation does not match service kind")
            self._outbound.append(
                {
                    "serviceId": action.service_id,
                    "serviceKind": service.kind,
                    "operation": action.operation,
                    "target": action.target,
                    "content": action.content,
                }
            )
            result = "simulated"
        else:
            raise ValueError("operation is not supported by the selected synthetic service")

        event = {
            "sequence": len(self._events) + 1,
            "actionDigest": action.digest,
            "actorId": action.actor_id,
            "serviceId": action.service_id,
            "operation": action.operation,
            "target": action.target,
            "resultDigest": canonical_digest({"result": result}),
        }
        self._events.append(event)
        return WorldActionResult(
            action_digest=action.digest,
            sequence=event["sequence"],
            status="simulated",
            result=result,
            state_digest=self.state_digest,
            trace_digest=self.trace_digest,
        )
