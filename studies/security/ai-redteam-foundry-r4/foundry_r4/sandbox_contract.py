from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re
from typing import Any

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_THREAT_CLASSES = frozenset({"semantic_only", "synthetic_agent", "hostile_code"})
_PROCESS = frozenset({"same_process", "separate_process_tree", "container", "vm"})
_KERNEL = frozenset({"shared", "separate_guest_kernel"})
_FILESYSTEM = frozenset({"host_visible", "restricted_host", "synthetic", "disposable_overlay"})
_NETWORK = frozenset({"none", "loopback_only", "simulated_internet", "allowlist_egress", "full_egress"})
_CREDENTIALS = frozenset({"host_ambient", "provider_scoped", "synthetic_only", "none"})
_DEVICES = frozenset({"host_default", "explicit_allowlist", "none"})
_EFFECTS = frozenset({"direct_open_world", "policy_proxy", "synthetic_only", "none"})
_LIFECYCLE = frozenset({"persistent", "resettable", "disposable"})
_OBSERVER = frozenset({"self_reported", "same_trust_domain", "independent"})


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return "sha256:" + sha256(payload).hexdigest()


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty canonical text")
    return value


def _digest(value: str, label: str) -> str:
    _text(value, label)
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def _member(value: str, allowed: frozenset[str], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"{label} must be one of {sorted(allowed)}")
    return value


@dataclass(frozen=True, slots=True)
class ResourceBudget:
    max_wall_seconds: int
    max_cpu_seconds: int
    max_memory_mib: int
    max_disk_mib: int
    max_processes: int
    max_network_bytes: int

    def __post_init__(self) -> None:
        values = asdict(self)
        for key, value in values.items():
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{key} must be a non-negative integer")
        if self.max_wall_seconds == 0 or self.max_memory_mib == 0 or self.max_processes == 0:
            raise ValueError("wall time, memory, and process budgets must be bounded above zero")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IsolationVector:
    process: str
    kernel: str
    filesystem: str
    network: str
    credentials: str
    devices: str
    external_effects: str
    lifecycle: str
    observer: str

    def __post_init__(self) -> None:
        _member(self.process, _PROCESS, "process isolation")
        _member(self.kernel, _KERNEL, "kernel isolation")
        _member(self.filesystem, _FILESYSTEM, "filesystem isolation")
        _member(self.network, _NETWORK, "network policy")
        _member(self.credentials, _CREDENTIALS, "credential exposure")
        _member(self.devices, _DEVICES, "device exposure")
        _member(self.external_effects, _EFFECTS, "external effect policy")
        _member(self.lifecycle, _LIFECYCLE, "lifecycle")
        _member(self.observer, _OBSERVER, "observer independence")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SandboxProviderBinding:
    provider_id: str
    provider_revision: str
    provider_kind: str
    provider_evidence_digest: str

    def __post_init__(self) -> None:
        _text(self.provider_id, "provider id")
        _text(self.provider_revision, "provider revision")
        _text(self.provider_kind, "provider kind")
        _digest(self.provider_evidence_digest, "provider evidence digest")

    def to_dict(self) -> dict[str, str]:
        return {
            "providerId": self.provider_id,
            "providerRevision": self.provider_revision,
            "providerKind": self.provider_kind,
            "providerEvidenceDigest": self.provider_evidence_digest,
        }


@dataclass(frozen=True, slots=True)
class ExperimentEnvironmentSpec:
    environment_id: str
    threat_class: str
    base_image_digest: str
    synthetic_world_digest: str
    tool_surface_digest: str
    observer_spec_digest: str
    isolation: IsolationVector
    budget: ResourceBudget
    provider: SandboxProviderBinding

    def __post_init__(self) -> None:
        _text(self.environment_id, "environment id")
        _member(self.threat_class, _THREAT_CLASSES, "threat class")
        for value, label in (
            (self.base_image_digest, "base image digest"),
            (self.synthetic_world_digest, "synthetic world digest"),
            (self.tool_surface_digest, "tool surface digest"),
            (self.observer_spec_digest, "observer spec digest"),
        ):
            _digest(value, label)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-experiment-environment",
            "environmentId": self.environment_id,
            "threatClass": self.threat_class,
            "baseImageDigest": self.base_image_digest,
            "syntheticWorldDigest": self.synthetic_world_digest,
            "toolSurfaceDigest": self.tool_surface_digest,
            "observerSpecDigest": self.observer_spec_digest,
            "isolation": self.isolation.to_dict(),
            "budget": self.budget.to_dict(),
            "provider": self.provider.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class SandboxAdmission:
    environment_digest: str
    admitted: bool
    reasons: tuple[str, ...]
    required_dimensions: tuple[str, ...]

    def __post_init__(self) -> None:
        _digest(self.environment_digest, "environment digest")
        if self.admitted and self.reasons:
            raise ValueError("an admitted environment cannot carry rejection reasons")
        if not self.admitted and not self.reasons:
            raise ValueError("a rejected environment must explain why")

    def to_dict(self) -> dict[str, object]:
        return {
            "environmentDigest": self.environment_digest,
            "admitted": self.admitted,
            "reasons": list(self.reasons),
            "requiredDimensions": list(self.required_dimensions),
        }


HOSTILE_REQUIRED = (
    "process=vm",
    "kernel=separate_guest_kernel",
    "filesystem=disposable_overlay",
    "network!=full_egress",
    "credentials in {none,synthetic_only}",
    "devices in {none,explicit_allowlist}",
    "external_effects in {none,synthetic_only,policy_proxy}",
    "lifecycle=disposable",
    "observer=independent",
    "bounded resources",
)


def admit_environment(spec: ExperimentEnvironmentSpec) -> SandboxAdmission:
    iso = spec.isolation
    reasons: list[str] = []
    required: tuple[str, ...]

    if spec.threat_class == "semantic_only":
        required = ("external_effects=none",)
        if iso.external_effects != "none":
            reasons.append("semantic-only experiment unexpectedly exposes external effects")
    elif spec.threat_class == "synthetic_agent":
        required = (
            "credentials in {none,synthetic_only}",
            "external_effects in {none,synthetic_only,policy_proxy}",
            "network!=full_egress",
        )
        if iso.credentials not in {"none", "synthetic_only"}:
            reasons.append("synthetic-agent experiment exposes non-synthetic credentials")
        if iso.external_effects == "direct_open_world":
            reasons.append("synthetic-agent experiment has a direct open-world effect path")
        if iso.network == "full_egress":
            reasons.append("synthetic-agent experiment has unrestricted network egress")
    else:
        required = HOSTILE_REQUIRED
        if iso.process != "vm":
            reasons.append("hostile code requires a VM process boundary")
        if iso.kernel != "separate_guest_kernel":
            reasons.append("hostile code requires a separate guest kernel")
        if iso.filesystem != "disposable_overlay":
            reasons.append("hostile code requires a disposable filesystem overlay")
        if iso.network == "full_egress":
            reasons.append("hostile code cannot have unrestricted network egress")
        if iso.credentials not in {"none", "synthetic_only"}:
            reasons.append("hostile code cannot receive host/provider credentials")
        if iso.devices not in {"none", "explicit_allowlist"}:
            reasons.append("hostile code cannot inherit the host default device surface")
        if iso.external_effects == "direct_open_world":
            reasons.append("hostile code external effects must be absent, synthetic, or mediated")
        if iso.lifecycle != "disposable":
            reasons.append("hostile code environment must be disposable")
        if iso.observer != "independent":
            reasons.append("hostile code cannot self-verify experiment consequences")
        if spec.budget.max_network_bytes == 0 and iso.network in {"allowlist_egress", "simulated_internet"}:
            reasons.append("network-enabled hostile experiment requires an explicit positive network-byte budget")

    return SandboxAdmission(
        environment_digest=spec.digest,
        admitted=not reasons,
        reasons=tuple(reasons),
        required_dimensions=required,
    )


@dataclass(frozen=True, slots=True)
class SandboxRealizationReceipt:
    requested_environment_digest: str
    realized_provider_id: str
    realized_provider_revision: str
    realized_base_image_digest: str
    realized_isolation_digest: str
    realization_evidence_digest: str
    disposable_instance_id: str

    def __post_init__(self) -> None:
        _digest(self.requested_environment_digest, "requested environment digest")
        _text(self.realized_provider_id, "realized provider id")
        _text(self.realized_provider_revision, "realized provider revision")
        _digest(self.realized_base_image_digest, "realized base image digest")
        _digest(self.realized_isolation_digest, "realized isolation digest")
        _digest(self.realization_evidence_digest, "realization evidence digest")
        _text(self.disposable_instance_id, "disposable instance id")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-sandbox-realization-receipt",
            "requestedEnvironmentDigest": self.requested_environment_digest,
            "realizedProviderId": self.realized_provider_id,
            "realizedProviderRevision": self.realized_provider_revision,
            "realizedBaseImageDigest": self.realized_base_image_digest,
            "realizedIsolationDigest": self.realized_isolation_digest,
            "realizationEvidenceDigest": self.realization_evidence_digest,
            "disposableInstanceId": self.disposable_instance_id,
        }


def reconcile_realization(spec: ExperimentEnvironmentSpec, receipt: SandboxRealizationReceipt) -> SandboxRealizationReceipt:
    admission = admit_environment(spec)
    if not admission.admitted:
        raise ValueError("cannot realize an environment that fails the declared threat-class contract")
    if receipt.requested_environment_digest != spec.digest:
        raise ValueError("sandbox receipt belongs to a different requested environment")
    if receipt.realized_provider_id != spec.provider.provider_id:
        raise ValueError("sandbox provider id drifted")
    if receipt.realized_provider_revision != spec.provider.provider_revision:
        raise ValueError("sandbox provider revision drifted")
    if receipt.realized_base_image_digest != spec.base_image_digest:
        raise ValueError("sandbox base image drifted")
    expected_isolation = canonical_digest(spec.isolation.to_dict())
    if receipt.realized_isolation_digest != expected_isolation:
        raise ValueError("sandbox isolation vector drifted")
    return receipt
