from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable


def digest_bytes(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def digest_json(value: object) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


@dataclass(frozen=True)
class ProviderArtifactRef:
    provider: str
    provider_version: str
    artifact_kind: str
    artifact_digest: str
    byte_length: int
    source_path: str

    def to_security_evidence_ref_projection(self) -> dict[str, object]:
        """Project onto Security v2's existing mechanical EvidenceRef waist without importing its internals."""
        return {
            "provider": self.provider,
            "format": self.artifact_kind,
            "path": self.source_path,
            "sha256": self.artifact_digest,
            "byte_length": self.byte_length,
        }


@dataclass(frozen=True)
class ProviderFindingProjection:
    provider: str
    provider_version: str
    provider_run_id: str
    provider_case_id: str
    attack_family: str
    target_id: str
    judge_id: str
    provider_outcome: str
    provider_positive: bool | None
    score: float | None
    artifact_ref: ProviderArtifactRef
    projection_digest: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["artifact_ref"] = asdict(self.artifact_ref)
        value["notes"] = list(self.notes)
        return value


class PyritScenarioResultsAdapter:
    """Normalize PyRIT's documented `scenario-results --view attacks --format json` surface.

    The current PyRIT scanner documentation describes this view as one row per attack containing id,
    technique, objective, outcome, turns, and score. R1 intentionally consumes only that stable documented
    output surface; it does not inspect PyRIT's internal memory database schema.
    """

    provider = "pyrit"

    def __init__(self, provider_version: str) -> None:
        self.provider_version = provider_version

    def parse_bytes(self, data: bytes, source_path: str, *, scenario_result_id: str, target_id: str) -> list[ProviderFindingProjection]:
        payload = json.loads(data)
        if not isinstance(payload, list):
            raise ValueError("PyRIT attacks-view fixture must be a JSON array")
        artifact_ref = ProviderArtifactRef(
            provider=self.provider,
            provider_version=self.provider_version,
            artifact_kind="scenario-results.attacks.json",
            artifact_digest=digest_bytes(data),
            byte_length=len(data),
            source_path=source_path,
        )
        projections: list[ProviderFindingProjection] = []
        for index, row in enumerate(payload):
            if not isinstance(row, dict):
                raise ValueError(f"PyRIT attack row {index} must be an object")
            missing = [name for name in ("id", "technique", "outcome", "turns", "score") if name not in row]
            if missing:
                raise ValueError(f"PyRIT attack row {index} missing documented fields: {missing}")
            score_raw = row["score"]
            if score_raw is not None and not isinstance(score_raw, (int, float)):
                raise ValueError(f"PyRIT attack row {index} score must be numeric or null")
            identity = {
                "provider": self.provider,
                "provider_version": self.provider_version,
                "scenario_result_id": scenario_result_id,
                "row": row,
                "artifact_digest": artifact_ref.artifact_digest,
                "target_id": target_id,
            }
            projections.append(
                ProviderFindingProjection(
                    provider=self.provider,
                    provider_version=self.provider_version,
                    provider_run_id=scenario_result_id,
                    provider_case_id=str(row["id"]),
                    attack_family=str(row["technique"]),
                    target_id=target_id,
                    judge_id="pyrit-provider-scorer",
                    provider_outcome=str(row["outcome"]),
                    provider_positive=(True if str(row["outcome"]).upper() == "SUCCESS" else False if str(row["outcome"]).upper() == "FAILURE" else None),
                    score=float(score_raw) if score_raw is not None else None,
                    artifact_ref=artifact_ref,
                    projection_digest=digest_json(identity),
                    notes=(
                        f"turns={row['turns']}",
                        "provider outcome retained as provider judgment, not Ordivon world-state truth",
                    ),
                )
            )
        return projections


class GarakReportAdapter:
    """Normalize garak JSONL config/eval records without flattening raw attempts.

    garak documents report.jsonl as the canonical run report. Current analyzer code consumes `config`
    records containing target_type/target_name and `eval` records containing probe, detector, passed, and
    total_evaluated. The adapter preserves the complete provider artifact digest and treats the eval result as
    a provider-native detector/evaluator judgment.
    """

    provider = "garak"

    def __init__(self, provider_version: str) -> None:
        self.provider_version = provider_version

    def parse_bytes(self, data: bytes, source_path: str, *, provider_run_id: str) -> list[ProviderFindingProjection]:
        artifact_ref = ProviderArtifactRef(
            provider=self.provider,
            provider_version=self.provider_version,
            artifact_kind="report.jsonl",
            artifact_digest=digest_bytes(data),
            byte_length=len(data),
            source_path=source_path,
        )
        records: list[dict[str, object]] = []
        for line_number, line in enumerate(data.decode("utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"garak line {line_number} must be a JSON object")
            records.append(record)

        configs = [record for record in records if record.get("entry_type") == "config"]
        if len(configs) != 1:
            raise ValueError(f"garak fixture must contain exactly one config record, found {len(configs)}")
        config = configs[0]
        if not isinstance(config.get("target_type"), str) or not isinstance(config.get("target_name"), str):
            raise ValueError("garak config must bind target_type and target_name")
        target_id = f"{config['target_type']}:{config['target_name']}"

        projections: list[ProviderFindingProjection] = []
        eval_index = 0
        for record in records:
            if record.get("entry_type") != "eval":
                continue
            for field in ("probe", "detector", "passed", "total_evaluated"):
                if field not in record:
                    raise ValueError(f"garak eval record missing field {field}")
            passed = record["passed"]
            total = record["total_evaluated"]
            if not isinstance(passed, int) or not isinstance(total, int) or total < 0 or passed < 0 or passed > total:
                raise ValueError("garak eval passed/total_evaluated must be bounded integers")
            eval_index += 1
            pass_rate = (passed / total) if total else None
            hit_rate = (1.0 - pass_rate) if pass_rate is not None else None
            case_id = f"eval-{eval_index}:{record['probe']}:{record['detector']}"
            identity = {
                "provider": self.provider,
                "provider_version": self.provider_version,
                "provider_run_id": provider_run_id,
                "case_id": case_id,
                "record": record,
                "artifact_digest": artifact_ref.artifact_digest,
                "target_id": target_id,
            }
            projections.append(
                ProviderFindingProjection(
                    provider=self.provider,
                    provider_version=self.provider_version,
                    provider_run_id=provider_run_id,
                    provider_case_id=case_id,
                    attack_family=str(record["probe"]),
                    target_id=target_id,
                    judge_id=f"garak:{record['detector']}",
                    provider_outcome="provider_hit_rate" if total else "provider_undetermined_zero_evaluated",
                    provider_positive=(hit_rate > 0.0) if hit_rate is not None else None,
                    score=hit_rate,
                    artifact_ref=artifact_ref,
                    projection_digest=digest_json(identity),
                    notes=(
                        f"passed={passed}",
                        f"total_evaluated={total}",
                        "garak scores are provider-specific and are not normalized across probes",
                    ),
                )
            )
        if not projections:
            raise ValueError("garak fixture contains no eval records; absence is not evidence of zero findings")
        return projections


def load_fixture(path: Path) -> bytes:
    return path.read_bytes()


def discovery_frontier(projections: Iterable[ProviderFindingProjection], budget: int) -> dict[str, object]:
    if budget < 1:
        raise ValueError("budget must be >= 1")
    selected = list(projections)[:budget]
    families = sorted({projection.attack_family for projection in selected})
    positive = [projection for projection in selected if projection.provider_positive is True]
    positive_families = sorted({projection.attack_family for projection in positive})
    return {
        "budget": budget,
        "casesObserved": len(selected),
        "attackFamiliesObserved": families,
        "positiveProviderFamilies": positive_families,
        "positiveProviderFamilyCount": len(positive_families),
        "note": "Provider-positive families are discovery signals, not root-cause families until independently clustered/verified.",
    }


@dataclass(frozen=True)
class AgentDojoCaseProjection:
    provider: str
    provider_version: str
    provider_case_id: str
    suite_name: str
    pipeline_name: str
    user_task_id: str
    injection_task_id: str
    attack_type: str
    utility_flag: bool
    security_flag: bool
    benchmark_version: str | None
    package_version: str | None
    artifact_ref: ProviderArtifactRef
    projection_digest: str
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["artifact_ref"] = asdict(self.artifact_ref)
        return value


class AgentDojoRunAdapter:
    """Normalize one AgentDojo run artifact while preserving provider semantics.

    Current AgentDojo run artifacts contain suite/pipeline/task identifiers plus boolean `utility` and
    `security` fields. R1 deliberately does *not* reinterpret the `security` boolean as a universal ASR or
    safety bit: task-specific checks and error paths determine it, and provider semantics have changed over
    time. The adapter keeps both booleans verbatim and requires downstream experiments to bind benchmark
    version plus the task implementation before interpreting them.
    """

    provider = "agentdojo"

    def __init__(self, provider_version: str) -> None:
        self.provider_version = provider_version

    def parse_bytes(self, data: bytes, source_path: str) -> AgentDojoCaseProjection:
        row = json.loads(data)
        if not isinstance(row, dict):
            raise ValueError("AgentDojo run artifact must be a JSON object")
        required = (
            "suite_name",
            "pipeline_name",
            "user_task_id",
            "injection_task_id",
            "attack_type",
            "utility",
            "security",
        )
        missing = [field for field in required if field not in row]
        if missing:
            raise ValueError(f"AgentDojo run artifact missing fields: {missing}")
        if not isinstance(row["utility"], bool) or not isinstance(row["security"], bool):
            raise ValueError("AgentDojo utility/security fields must remain booleans")
        artifact_ref = ProviderArtifactRef(
            provider=self.provider,
            provider_version=self.provider_version,
            artifact_kind="agentdojo.run.json",
            artifact_digest=digest_bytes(data),
            byte_length=len(data),
            source_path=source_path,
        )
        case_id = ":".join(
            [
                str(row["suite_name"]),
                str(row["user_task_id"]),
                str(row["injection_task_id"]),
                str(row["attack_type"]),
            ]
        )
        identity = {
            "provider": self.provider,
            "provider_version": self.provider_version,
            "case_id": case_id,
            "artifact_digest": artifact_ref.artifact_digest,
            "utility": row["utility"],
            "security": row["security"],
            "benchmark_version": row.get("benchmark_version"),
            "package_version": row.get("agentdojo_package_version"),
        }
        return AgentDojoCaseProjection(
            provider=self.provider,
            provider_version=self.provider_version,
            provider_case_id=case_id,
            suite_name=str(row["suite_name"]),
            pipeline_name=str(row["pipeline_name"]),
            user_task_id=str(row["user_task_id"]),
            injection_task_id=str(row["injection_task_id"]),
            attack_type=str(row["attack_type"]),
            utility_flag=row["utility"],
            security_flag=row["security"],
            benchmark_version=str(row["benchmark_version"]) if row.get("benchmark_version") is not None else None,
            package_version=str(row["agentdojo_package_version"]) if row.get("agentdojo_package_version") is not None else None,
            artifact_ref=artifact_ref,
            projection_digest=digest_json(identity),
            interpretation=(
                "utility/security booleans retained verbatim; downstream interpretation requires the exact "
                "AgentDojo benchmark/task implementation and must not infer production security standing"
            ),
        )


@dataclass(frozen=True)
class InspectEvalProjection:
    provider: str
    provider_version: str
    eval_id: str
    run_id: str
    task: str
    task_id: str
    task_version: str
    model: str
    status: str
    sample_count: int
    scorer_names: tuple[str, ...]
    package_versions: tuple[tuple[str, str], ...]
    artifact_ref: ProviderArtifactRef
    projection_digest: str
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["scorer_names"] = list(self.scorer_names)
        value["package_versions"] = [list(pair) for pair in self.package_versions]
        value["artifact_ref"] = asdict(self.artifact_ref)
        return value


class InspectEvalLogAdapter:
    """Project Inspect AI JSON eval logs into the Foundry evidence seam.

    Inspect is treated as an evaluation/logging substrate, not as Ordivon-owned orchestration. The adapter
    consumes only documented EvalLog/EvalSpec fields and keeps scores provider/task-owned. It does not infer
    that a score named `security`, `harm`, or `utility` has universal meaning across benchmarks.
    """

    provider = "inspect_ai"

    def __init__(self, provider_version: str) -> None:
        self.provider_version = provider_version

    def parse_bytes(self, data: bytes, source_path: str) -> InspectEvalProjection:
        payload = json.loads(data)
        if not isinstance(payload, dict):
            raise ValueError("Inspect eval log must be a JSON object")
        for field in ("version", "status", "eval", "samples"):
            if field not in payload:
                raise ValueError(f"Inspect eval log missing documented field {field}")
        spec = payload["eval"]
        if not isinstance(spec, dict):
            raise ValueError("Inspect eval field must be an object")
        required_spec = ("eval_id", "run_id", "task", "task_id", "task_version", "model")
        missing = [field for field in required_spec if field not in spec]
        if missing:
            raise ValueError(f"Inspect EvalSpec missing documented fields: {missing}")
        samples = payload["samples"]
        if samples is None:
            samples = []
        if not isinstance(samples, list):
            raise ValueError("Inspect samples must be an array or null")

        scorer_names: set[str] = set()
        for index, sample in enumerate(samples):
            if not isinstance(sample, dict):
                raise ValueError(f"Inspect sample {index} must be an object")
            scores = sample.get("scores")
            if scores is None:
                continue
            if not isinstance(scores, dict):
                raise ValueError(f"Inspect sample {index} scores must be an object or null")
            scorer_names.update(str(name) for name in scores)

        packages_raw = spec.get("packages") or {}
        if not isinstance(packages_raw, dict):
            raise ValueError("Inspect EvalSpec packages must be an object")
        package_versions = tuple(sorted((str(k), str(v)) for k, v in packages_raw.items()))
        artifact_ref = ProviderArtifactRef(
            provider=self.provider,
            provider_version=self.provider_version,
            artifact_kind="inspect.eval-log.json",
            artifact_digest=digest_bytes(data),
            byte_length=len(data),
            source_path=source_path,
        )
        identity = {
            "provider": self.provider,
            "provider_version": self.provider_version,
            "artifact_digest": artifact_ref.artifact_digest,
            "eval_id": spec["eval_id"],
            "run_id": spec["run_id"],
            "task": spec["task"],
            "task_id": spec["task_id"],
            "task_version": spec["task_version"],
            "model": spec["model"],
            "status": payload["status"],
            "scorers": sorted(scorer_names),
            "packages": package_versions,
        }
        return InspectEvalProjection(
            provider=self.provider,
            provider_version=self.provider_version,
            eval_id=str(spec["eval_id"]),
            run_id=str(spec["run_id"]),
            task=str(spec["task"]),
            task_id=str(spec["task_id"]),
            task_version=str(spec["task_version"]),
            model=str(spec["model"]),
            status=str(payload["status"]),
            sample_count=len(samples),
            scorer_names=tuple(sorted(scorer_names)),
            package_versions=package_versions,
            artifact_ref=artifact_ref,
            projection_digest=digest_json(identity),
            interpretation=(
                "Inspect owns task/scorer semantics and the complete eval transcript. Ordivon consumes the "
                "digest-bound log identity; individual score names/values require task-version-specific interpretation."
            ),
        )
