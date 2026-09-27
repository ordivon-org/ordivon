from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re
from typing import Any


_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ALLOWED_TARGET_KINDS = frozenset({"model", "agent", "monitor", "system"})


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    if value != value.strip():
        raise ValueError(f"{label} must not contain leading/trailing whitespace")
    return value


def _digest(value: str, label: str) -> str:
    _text(value, label)
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be an exact sha256 digest")
    return value


def _optional_digest(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _digest(value, label)


def canonical_digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + sha256(data).hexdigest()


def _canonical_json(value: dict[str, Any], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a JSON object")
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain canonical JSON-compatible values") from exc
    decoded = json.loads(encoded)
    if not isinstance(decoded, dict):
        raise AssertionError("canonical JSON object unexpectedly changed type")
    return decoded


@dataclass(frozen=True, slots=True)
class ModelRequestBinding:
    provider: str
    requested_model_id: str
    provider_model_revision: str | None = None
    model_artifact_digest: str | None = None

    def __post_init__(self) -> None:
        _text(self.provider, "model provider")
        _text(self.requested_model_id, "requested model id")
        if self.provider_model_revision is not None:
            _text(self.provider_model_revision, "provider model revision")
        _optional_digest(self.model_artifact_digest, "model artifact digest")

    @property
    def pre_run_identity_strength(self) -> str:
        if self.model_artifact_digest is not None:
            return "content_digest"
        if self.provider_model_revision is not None:
            return "provider_revision"
        return "request_only"

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "requestedModelId": self.requested_model_id,
            "providerModelRevision": self.provider_model_revision,
            "modelArtifactDigest": self.model_artifact_digest,
        }


@dataclass(frozen=True, slots=True)
class EvaluationTargetBinding:
    security_subject_ref: str
    security_subject_revision: str
    target_kind: str
    model: ModelRequestBinding
    harness_revision: str
    harness_config_digest: str
    instruction_bundle_digest: str
    tool_catalog_digest: str
    authority_surface_digest: str
    monitor_bundle_digest: str
    environment_digest: str
    adapter_id: str
    adapter_revision: str
    generation: dict[str, Any]

    def __post_init__(self) -> None:
        _text(self.security_subject_ref, "Security subject ref")
        _text(self.security_subject_revision, "Security subject revision")
        if self.target_kind not in _ALLOWED_TARGET_KINDS:
            raise ValueError(f"target_kind must be one of {sorted(_ALLOWED_TARGET_KINDS)}")
        _text(self.harness_revision, "Harness revision")
        _digest(self.harness_config_digest, "Harness config digest")
        _digest(self.instruction_bundle_digest, "instruction bundle digest")
        _digest(self.tool_catalog_digest, "tool catalog digest")
        _digest(self.authority_surface_digest, "authority surface digest")
        _digest(self.monitor_bundle_digest, "monitor bundle digest")
        _digest(self.environment_digest, "environment digest")
        _text(self.adapter_id, "adapter id")
        _text(self.adapter_revision, "adapter revision")
        canonical = _canonical_json(self.generation, "generation configuration")
        object.__setattr__(self, "generation", canonical)

    @property
    def generation_digest(self) -> str:
        return canonical_digest(self.generation)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    @property
    def target_ref(self) -> str:
        return "eval-target:" + self.digest.split(":", 1)[1]

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-evaluation-target-binding",
            "securitySubjectRef": self.security_subject_ref,
            "securitySubjectRevision": self.security_subject_revision,
            "targetKind": self.target_kind,
            "model": self.model.to_dict(),
            "harnessRevision": self.harness_revision,
            "harnessConfigDigest": self.harness_config_digest,
            "instructionBundleDigest": self.instruction_bundle_digest,
            "toolCatalogDigest": self.tool_catalog_digest,
            "authoritySurfaceDigest": self.authority_surface_digest,
            "monitorBundleDigest": self.monitor_bundle_digest,
            "environmentDigest": self.environment_digest,
            "adapterId": self.adapter_id,
            "adapterRevision": self.adapter_revision,
            "generation": self.generation,
            "generationDigest": self.generation_digest,
        }


@dataclass(frozen=True, slots=True)
class RealizedTargetBinding:
    requested_binding_digest: str
    effective_model_id: str
    realization_evidence_digest: str
    provider_model_revision: str | None = None
    model_artifact_digest: str | None = None
    provider_system_fingerprint: str | None = None

    def __post_init__(self) -> None:
        _digest(self.requested_binding_digest, "requested binding digest")
        _text(self.effective_model_id, "effective model id")
        _digest(self.realization_evidence_digest, "realization evidence digest")
        if self.provider_model_revision is not None:
            _text(self.provider_model_revision, "provider model revision")
        _optional_digest(self.model_artifact_digest, "realized model artifact digest")
        if self.provider_system_fingerprint is not None:
            _text(self.provider_system_fingerprint, "provider system fingerprint")

    @property
    def identity_strength(self) -> str:
        if self.model_artifact_digest is not None:
            return "content_digest"
        if self.provider_model_revision is not None:
            return "provider_revision"
        if self.provider_system_fingerprint is not None:
            return "provider_observation"
        return "request_only"

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    @property
    def claim_scope(self) -> str:
        return {
            "content_digest": "byte_exact_model_artifact_with_bound_evaluation_configuration",
            "provider_revision": "provider_revision_bound_with_bound_evaluation_configuration",
            "provider_observation": "provider_observation_bound_not_byte_exact_model_identity",
            "request_only": "requested_model_alias_only_no_realized_model_revision_claim",
        }[self.identity_strength]

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-realized-target-binding",
            "requestedBindingDigest": self.requested_binding_digest,
            "effectiveModelId": self.effective_model_id,
            "providerModelRevision": self.provider_model_revision,
            "modelArtifactDigest": self.model_artifact_digest,
            "providerSystemFingerprint": self.provider_system_fingerprint,
            "realizationEvidenceDigest": self.realization_evidence_digest,
            "identityStrength": self.identity_strength,
            "claimScope": self.claim_scope,
        }


@dataclass(frozen=True, slots=True)
class TargetBindingDiff:
    left_digest: str
    right_digest: str
    changed_fields: tuple[str, ...]

    @property
    def same_target_binding(self) -> bool:
        return not self.changed_fields

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def diff_target_bindings(left: EvaluationTargetBinding, right: EvaluationTargetBinding) -> TargetBindingDiff:
    left_value = left.to_dict()
    right_value = right.to_dict()
    changed = tuple(sorted(key for key in left_value if left_value[key] != right_value[key]))
    return TargetBindingDiff(left.digest, right.digest, changed)


def reconcile_realization(
    requested: EvaluationTargetBinding,
    realized: RealizedTargetBinding,
) -> RealizedTargetBinding:
    """Fail closed when a realization drifts from an exact pre-run model commitment.

    Closed providers may legitimately improve a request-only binding with later revision/fingerprint evidence.
    What they may not do is silently replace an already-bound exact artifact or provider revision while the
    experiment continues to claim the original requested target.
    """

    if realized.requested_binding_digest != requested.digest:
        raise ValueError("realized target belongs to a different requested binding")

    expected_artifact = requested.model.model_artifact_digest
    if expected_artifact is not None and realized.model_artifact_digest != expected_artifact:
        raise ValueError("realized model artifact does not match the exact requested model artifact")

    expected_revision = requested.model.provider_model_revision
    if expected_revision is not None and realized.provider_model_revision != expected_revision:
        raise ValueError("realized provider model revision does not match the requested revision")

    return realized


@dataclass(frozen=True, slots=True)
class TargetBoundObservation:
    """Bind one experiment observation to the exact realized target and evaluation contracts.

    This is a study-local relationship object. The referenced provider artifact remains provider-native and
    Security remains the owner of production EvidenceRef/standing semantics.
    """

    realized_target_digest: str
    attack_spec_digest: str
    provider_artifact_digest: str
    judge_spec_digest: str
    observation_digest: str

    def __post_init__(self) -> None:
        _digest(self.realized_target_digest, "realized target digest")
        _digest(self.attack_spec_digest, "attack spec digest")
        _digest(self.provider_artifact_digest, "provider artifact digest")
        _digest(self.judge_spec_digest, "judge spec digest")
        _digest(self.observation_digest, "observation digest")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def require_target(self, realized: RealizedTargetBinding) -> None:
        if self.realized_target_digest != realized.digest:
            raise ValueError("observation is bound to a different realized target")

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-target-bound-observation",
            "realizedTargetDigest": self.realized_target_digest,
            "attackSpecDigest": self.attack_spec_digest,
            "providerArtifactDigest": self.provider_artifact_digest,
            "judgeSpecDigest": self.judge_spec_digest,
            "observationDigest": self.observation_digest,
        }
