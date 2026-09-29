from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable, Mapping

R8_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = R8_ROOT.parents[2]
R1_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r1"
R4_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r4"
R7_ROOT = REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r7"
for root in (R1_ROOT, R4_ROOT, R7_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from foundry.providers import ProviderArtifactRef, ProviderFindingProjection  # noqa: E402
from foundry_r4 import ExperimentEnvironmentSpec, admit_environment, canonical_digest  # noqa: E402
from foundry_r7 import ConsequenceObservation, ObserverBinding  # noqa: E402

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_THREAT_CLASSES = frozenset({"semantic_only", "synthetic_agent", "hostile_code"})
_ADAPTIVITY = frozenset({"fixed_sequence", "provider_adaptive", "observer_adaptive"})


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty canonical text")
    return value


def _digest(value: str, label: str) -> str:
    _text(value, label)
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


@dataclass(frozen=True, slots=True)
class SearchBudget:
    max_candidates: int
    max_rounds: int
    max_target_calls: int
    max_wall_time_ms: int

    def __post_init__(self) -> None:
        for label, value in (
            ("max candidates", self.max_candidates),
            ("max rounds", self.max_rounds),
            ("max target calls", self.max_target_calls),
            ("max wall time ms", self.max_wall_time_ms),
        ):
            if not isinstance(value, int) or value < 1:
                raise ValueError(f"{label} must be a positive integer")
        if self.max_target_calls < self.max_candidates:
            raise ValueError("target-call budget cannot be smaller than candidate budget")

    def to_dict(self) -> dict[str, int]:
        return {
            "maxCandidates": self.max_candidates,
            "maxRounds": self.max_rounds,
            "maxTargetCalls": self.max_target_calls,
            "maxWallTimeMs": self.max_wall_time_ms,
        }


@dataclass(frozen=True, slots=True)
class SearchControl:
    random_seed: int
    adaptivity: str
    feedback_source: str

    def __post_init__(self) -> None:
        if not isinstance(self.random_seed, int) or self.random_seed < 0 or self.random_seed >= 2**63:
            raise ValueError("random seed must be an integer in [0, 2^63)")
        if self.adaptivity not in _ADAPTIVITY:
            raise ValueError(f"adaptivity must be one of {sorted(_ADAPTIVITY)}")
        _text(self.feedback_source, "feedback source")
        if self.adaptivity == "fixed_sequence" and self.feedback_source != "none":
            raise ValueError("fixed-sequence search cannot declare adaptive feedback")
        if self.adaptivity == "provider_adaptive" and not self.feedback_source.startswith("provider:"):
            raise ValueError("provider-adaptive search must bind a provider-owned feedback source")
        if self.adaptivity == "observer_adaptive" and not self.feedback_source.startswith("observer:"):
            raise ValueError("observer-adaptive search must bind an observer-owned feedback source")

    def to_dict(self) -> dict[str, object]:
        return {
            "randomSeed": self.random_seed,
            "adaptivity": self.adaptivity,
            "feedbackSource": self.feedback_source,
        }


@dataclass(frozen=True, slots=True)
class AttackSearchRunSpec:
    search_id: str
    provider: str
    provider_version: str
    provider_engine: str
    provider_run_id: str
    target_id: str
    threat_class: str
    environment_digest: str
    world_spec_digest: str
    observer_binding_digest: str
    seed_artifact_digest: str
    provider_config_digest: str
    budget: SearchBudget
    control: SearchControl

    def __post_init__(self) -> None:
        for value, label in (
            (self.search_id, "search id"),
            (self.provider, "provider"),
            (self.provider_version, "provider version"),
            (self.provider_engine, "provider engine"),
            (self.provider_run_id, "provider run id"),
            (self.target_id, "target id"),
        ):
            _text(value, label)
        if self.threat_class not in _THREAT_CLASSES:
            raise ValueError(f"threat class must be one of {sorted(_THREAT_CLASSES)}")
        for value, label in (
            (self.environment_digest, "environment digest"),
            (self.world_spec_digest, "world spec digest"),
            (self.observer_binding_digest, "observer binding digest"),
            (self.seed_artifact_digest, "seed artifact digest"),
            (self.provider_config_digest, "provider config digest"),
        ):
            _digest(value, label)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-attack-search-run",
            "searchId": self.search_id,
            "provider": self.provider,
            "providerVersion": self.provider_version,
            "providerEngine": self.provider_engine,
            "providerRunId": self.provider_run_id,
            "targetId": self.target_id,
            "threatClass": self.threat_class,
            "environmentDigest": self.environment_digest,
            "worldSpecDigest": self.world_spec_digest,
            "observerBindingDigest": self.observer_binding_digest,
            "seedArtifactDigest": self.seed_artifact_digest,
            "providerConfigDigest": self.provider_config_digest,
            "budget": self.budget.to_dict(),
            "control": self.control.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class SearchCandidateRef:
    search_run_digest: str
    sequence: int
    provider: str
    provider_version: str
    provider_run_id: str
    provider_case_id: str
    attack_family: str
    target_id: str
    provider_projection_digest: str
    candidate_identity_digest: str
    artifact_ref: ProviderArtifactRef

    def __post_init__(self) -> None:
        _digest(self.search_run_digest, "search run digest")
        if not isinstance(self.sequence, int) or self.sequence < 1:
            raise ValueError("candidate sequence must be >= 1")
        for value, label in (
            (self.provider, "provider"),
            (self.provider_version, "provider version"),
            (self.provider_run_id, "provider run id"),
            (self.provider_case_id, "provider case id"),
            (self.attack_family, "attack family"),
            (self.target_id, "target id"),
        ):
            _text(value, label)
        _digest(self.provider_projection_digest, "provider projection digest")
        _digest(self.candidate_identity_digest, "candidate identity digest")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-search-candidate-ref",
            "searchRunDigest": self.search_run_digest,
            "sequence": self.sequence,
            "provider": self.provider,
            "providerVersion": self.provider_version,
            "providerRunId": self.provider_run_id,
            "providerCaseId": self.provider_case_id,
            "attackFamily": self.attack_family,
            "targetId": self.target_id,
            "providerProjectionDigest": self.provider_projection_digest,
            "candidateIdentityDigest": self.candidate_identity_digest,
            "artifactRef": {
                "provider": self.artifact_ref.provider,
                "providerVersion": self.artifact_ref.provider_version,
                "artifactKind": self.artifact_ref.artifact_kind,
                "artifactDigest": self.artifact_ref.artifact_digest,
                "byteLength": self.artifact_ref.byte_length,
                "sourcePath": self.artifact_ref.source_path,
            },
        }


@dataclass(frozen=True, slots=True)
class SearchResultRef:
    candidate: SearchCandidateRef
    judge_id: str
    provider_outcome: str
    provider_positive: bool | None
    score: float | None
    observation_digest: str | None
    observed_effect_id: str | None
    observed_effect_request_digest: str | None

    def __post_init__(self) -> None:
        _text(self.judge_id, "judge id")
        _text(self.provider_outcome, "provider outcome")
        if self.provider_positive is not None and not isinstance(self.provider_positive, bool):
            raise TypeError("provider positive must be bool or null")
        if self.score is not None and not isinstance(self.score, (int, float)):
            raise TypeError("score must be numeric or null")
        observation_fields = (self.observation_digest, self.observed_effect_id, self.observed_effect_request_digest)
        if any(value is not None for value in observation_fields) and not all(value is not None for value in observation_fields):
            raise ValueError("observation binding fields must be supplied together")
        if self.observation_digest is not None:
            _digest(self.observation_digest, "observation digest")
            _text(self.observed_effect_id or "", "observed effect id")
            _digest(self.observed_effect_request_digest or "", "observed effect request digest")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.ai-redteam-search-result-ref",
            "candidate": self.candidate.to_dict(),
            "judgeId": self.judge_id,
            "providerOutcome": self.provider_outcome,
            "providerPositive": self.provider_positive,
            "score": self.score,
            "observationDigest": self.observation_digest,
            "observedEffectId": self.observed_effect_id,
            "observedEffectRequestDigest": self.observed_effect_request_digest,
        }


def bind_search_run(
    *,
    search_id: str,
    provider: str,
    provider_version: str,
    provider_engine: str,
    provider_run_id: str,
    target_id: str,
    environment: ExperimentEnvironmentSpec,
    observer_binding: ObserverBinding,
    seed_artifact_digest: str,
    provider_config_digest: str,
    budget: SearchBudget,
    control: SearchControl,
) -> AttackSearchRunSpec:
    admission = admit_environment(environment)
    if not admission.admitted:
        raise ValueError("attack search cannot bind an environment rejected by the R4 contract")
    if environment.threat_class not in observer_binding.applicable_threat_classes:
        raise ValueError("observer binding is not applicable to the environment threat class")
    observer_digest = canonical_digest(observer_binding.to_dict())
    if environment.observer_spec_digest != observer_digest:
        raise ValueError("R4 environment observer digest does not match the R7 observer binding")
    return AttackSearchRunSpec(
        search_id=search_id,
        provider=provider,
        provider_version=provider_version,
        provider_engine=provider_engine,
        provider_run_id=provider_run_id,
        target_id=target_id,
        threat_class=environment.threat_class,
        environment_digest=environment.digest,
        world_spec_digest=environment.synthetic_world_digest,
        observer_binding_digest=observer_digest,
        seed_artifact_digest=seed_artifact_digest,
        provider_config_digest=provider_config_digest,
        budget=budget,
        control=control,
    )


def _validate_projection(run: AttackSearchRunSpec, projection: ProviderFindingProjection) -> None:
    if projection.provider != run.provider:
        raise ValueError("provider projection belongs to a different provider")
    if projection.provider_version != run.provider_version:
        raise ValueError("provider projection version drifted")
    if projection.provider_run_id != run.provider_run_id:
        raise ValueError("provider projection belongs to a different provider run")
    if projection.target_id != run.target_id:
        raise ValueError("provider projection belongs to a different target")
    if projection.artifact_ref.provider != run.provider or projection.artifact_ref.provider_version != run.provider_version:
        raise ValueError("provider artifact identity disagrees with the search run")
    _digest(projection.projection_digest, "provider projection digest")
    _digest(projection.artifact_ref.artifact_digest, "provider artifact digest")


def _validate_observation(run: AttackSearchRunSpec, observation: ConsequenceObservation) -> None:
    if observation.environment_digest != run.environment_digest:
        raise ValueError("R7 observation belongs to a different R4 environment")
    if observation.world_spec_digest != run.world_spec_digest:
        raise ValueError("R7 observation belongs to a different synthetic world")
    if canonical_digest(observation.binding.to_dict()) != run.observer_binding_digest:
        raise ValueError("R7 observation binding drifted from the search run")
    if run.threat_class not in observation.binding.applicable_threat_classes:
        raise ValueError("R7 observation is not applicable to the search threat class")


def normalize_provider_projection(
    run: AttackSearchRunSpec,
    projection: ProviderFindingProjection,
    *,
    sequence: int,
    observation: ConsequenceObservation | None = None,
) -> SearchResultRef:
    _validate_projection(run, projection)
    if sequence < 1 or sequence > run.budget.max_candidates:
        raise ValueError("candidate sequence exceeds the bound search budget")
    if observation is not None:
        _validate_observation(run, observation)

    candidate_identity = canonical_digest(
        {
            "searchRunDigest": run.digest,
            "sequence": sequence,
            "provider": projection.provider,
            "providerVersion": projection.provider_version,
            "providerRunId": projection.provider_run_id,
            "providerCaseId": projection.provider_case_id,
            "attackFamily": projection.attack_family,
            "targetId": projection.target_id,
            "providerProjectionDigest": projection.projection_digest,
            "providerArtifactDigest": projection.artifact_ref.artifact_digest,
        }
    )
    candidate = SearchCandidateRef(
        search_run_digest=run.digest,
        sequence=sequence,
        provider=projection.provider,
        provider_version=projection.provider_version,
        provider_run_id=projection.provider_run_id,
        provider_case_id=projection.provider_case_id,
        attack_family=projection.attack_family,
        target_id=projection.target_id,
        provider_projection_digest=projection.projection_digest,
        candidate_identity_digest=candidate_identity,
        artifact_ref=projection.artifact_ref,
    )
    return SearchResultRef(
        candidate=candidate,
        judge_id=projection.judge_id,
        provider_outcome=projection.provider_outcome,
        provider_positive=projection.provider_positive,
        score=projection.score,
        observation_digest=observation.digest if observation is not None else None,
        observed_effect_id=observation.effect_id if observation is not None else None,
        observed_effect_request_digest=observation.effect_request_digest if observation is not None else None,
    )


def normalize_provider_batch(
    run: AttackSearchRunSpec,
    projections: Iterable[ProviderFindingProjection],
    *,
    observations_by_case: Mapping[str, ConsequenceObservation] | None = None,
) -> tuple[SearchResultRef, ...]:
    rows = tuple(projections)
    if len(rows) > run.budget.max_candidates:
        raise ValueError("provider produced more normalized cases than the committed candidate budget")
    case_ids = [item.provider_case_id for item in rows]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("provider case ids must be unique within one normalized search run")
    observations = observations_by_case or {}
    unknown_observations = set(observations) - set(case_ids)
    if unknown_observations:
        raise ValueError("observation map contains provider case ids absent from the provider result set")
    return tuple(
        normalize_provider_projection(
            run,
            projection,
            sequence=index,
            observation=observations.get(projection.provider_case_id),
        )
        for index, projection in enumerate(rows, start=1)
    )
