from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from anc_canonical import canonical_digest
from jsonschema import Draft202012Validator
from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter

EXPERIMENT_ID = "experiment:experimental-fabric-model-harness-pilot-r1-20260928"
PROTOCOL_ID = "protocol:experimental-fabric-r1"
SEED = 20260928
MODELS = ("deepseek-flash", "deepseek-v4-flash")
CODECS = ("exact-replacement-v1", "anchored-line-v1")
TASK_IDS = (
    "HARNESS-REPO-REPAIR-001",
    "HARNESS-EDIT-ADDRESSING-002",
    "HARNESS-EDIT-MULTIREGION-003",
)
MAX_TOTAL_TOKENS = 48_000


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def harness_root() -> Path:
    return repo_root() / "services" / "harness"


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def journal_append(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def seal(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result[field] = canonical_digest({key: item for key, item in result.items() if key != field})
    return result


def binding(owner: str, object_kind: str, object_id: str, digest: str) -> dict[str, Any]:
    return {
        "ownerId": owner,
        "objectKind": object_kind,
        "objectId": object_id,
        "digest": digest,
    }


def file_binding(path: Path, *, owner: str = "git") -> dict[str, Any]:
    root = repo_root()
    return binding(owner, "file", str(path.relative_to(root)), file_digest(path))


def schema(name: str) -> dict[str, Any]:
    path = repo_root() / "profiles" / "experimental-episode" / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate(name: str, value: dict[str, Any]) -> None:
    Draft202012Validator(schema(name)).validate(value)


def load_live_runner():
    path = harness_root() / "scripts" / "run_adaptive_edit_r2_live_ab.py"
    spec = importlib.util.spec_from_file_location("adaptive_live", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load live runner: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_schedule() -> dict[str, Any]:
    trials: list[dict[str, Any]] = []
    for task_id in TASK_IDS:
        for model in MODELS:
            for codec in CODECS:
                trials.append(
                    {
                        "taskId": task_id,
                        "model": model,
                        "codec": codec,
                    }
                )
    random.Random(SEED).shuffle(trials)
    scheduled = []
    for ordinal, row in enumerate(trials, 1):
        scheduled.append(
            {
                "ordinal": ordinal,
                "trialId": f"trial:{ordinal:03d}",
                **row,
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factorial-allocation",
        "experimentId": EXPERIMENT_ID,
        "seed": SEED,
        "design": "balanced-2x2-randomized-complete-block-pilot",
        "blockingFactor": "taskId",
        "trials": scheduled,
    }


def metric_spec(
    metric_id: str,
    metric_class: str,
    construct: str,
    value_shape: str,
    owner_inputs: list[dict[str, Any]],
    *,
    unit: str | None = None,
) -> dict[str, Any]:
    limitation = (
        "Pilot has three deterministic task blocks and one live run per Model×Harness×task cell; "
        "cell effects are descriptive and do not establish broad model or Harness superiority."
    )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-metric-spec",
        "metricId": metric_id,
        "metricClass": metric_class,
        "construct": construct,
        "computationMode": "deterministic",
        "evidenceMinimum": "deterministic-observation",
        "valueShape": value_shape,
        "unitOfAnalysis": "live-harness-run",
        "replicationUnit": "live-harness-run",
        "aggregationPolicy": (
            "Report each Model×Harness cell across the three blocked task families; preserve task-level rows. "
            "Do not count repeated reads, verifier assertions, or Provider turns as independent replicates."
        ),
        "missingDataPolicy": "exclude-with-reason",
        "ownerInputs": owner_inputs,
        "knownLimitations": [limitation],
        "nonClaims": [
            "Metric does not establish Provider, Runtime, Harness, Git, or domain authority.",
            "This small pilot does not license a general model ranking.",
        ],
    }
    if unit is not None:
        value["knownLimitations"].append(f"Reported unit: {unit}.")
    return seal(value, "specDigest")


def build_preregistration() -> dict[str, Any]:
    root = repo_root()
    live_script = harness_root() / "scripts" / "run_adaptive_edit_r2_live_ab.py"
    deepseek_file = harness_root() / "src" / "ordivon_harness" / "ordivon" / "deepseek.py"
    observation_file = harness_root() / "src" / "ordivon_harness" / "agent_tool_observation.py"
    action_file = harness_root() / "src" / "ordivon_harness" / "ordivon" / "adaptive_edit_bridge.py"
    schedule = build_schedule()
    schedule_digest = canonical_digest(schedule)
    git_revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    # TASK_SPECS are the current natural mapping; bind their exact task/verifier files below.
    live = load_live_runner()
    task_owner_inputs: list[dict[str, Any]] = []
    task_digest_rows: list[dict[str, str]] = []
    for task_id in TASK_IDS:
        task = live.TASK_SPECS[task_id]
        task_owner_inputs.append(file_binding(task.task_path))
        task_owner_inputs.append(file_binding(task.hidden_verifier))
        task_digest_rows.append(
            {
                "taskId": task_id,
                "taskDigest": file_digest(task.task_path),
                "hiddenVerifierDigest": file_digest(task.hidden_verifier),
                "fixtureDigest": canonical_digest(
                    [
                        {"path": relative_path, "digest": digest}
                        for relative_path, digest in sorted(
                            (
                                str(path.relative_to(task.fixture)),
                                file_digest(path),
                            )
                            for path in task.fixture.rglob("*")
                            if path.is_file()
                        )
                    ]
                ),
            }
        )

    runner_ref = file_binding(live_script, owner="harness")
    adapter_ref = binding(
        "harness",
        "provider-adapter",
        DeepSeekTurnAdapter.adapter_id,
        file_digest(deepseek_file),
    )
    metrics = [
        metric_spec(
            "metric:hidden-pass",
            "outcome",
            "Whether the task-specific hidden verifier accepts the final edited source.",
            "binary",
            task_owner_inputs,
        ),
        metric_spec(
            "metric:candidate-completed",
            "outcome",
            "Whether the Harness run reached candidate_completed under its completion contract.",
            "binary",
            [runner_ref],
        ),
        metric_spec(
            "metric:total-tokens",
            "process",
            "Total Provider token usage reported by the Harness run.",
            "scalar",
            [runner_ref, adapter_ref],
            unit="tokens",
        ),
        metric_spec(
            "metric:tool-calls",
            "behavior",
            "Number of Harness Tool calls used to complete or stop the run.",
            "scalar",
            [runner_ref],
            unit="calls",
        ),
        metric_spec(
            "metric:elapsed-ms",
            "process",
            "Wall-clock elapsed time observed by the live runner.",
            "scalar",
            [runner_ref],
            unit="milliseconds",
        ),
        metric_spec(
            "metric:rejected-observations",
            "robustness",
            "Number of Tool observations rejected by the Harness during the run.",
            "scalar",
            [runner_ref],
            unit="observations",
        ),
    ]
    for item in metrics:
        validate("experimental-metric-spec-r1.schema.json", item)

    resource_contract = {
        "maxModelCalls": 6,
        "maxToolCalls": 8,
        "maxObservationBytes": 262_144,
        "maxWallTimeMs": 90_000,
        "maxTotalTokens": MAX_TOTAL_TOKENS,
        "maxModelRetries": 1,
        "maxToolCorrections": 3,
        "maxConclusionCorrections": 2,
        "maxObservationOnlyTurns": 5,
        "maxNoProgressTurns": 4,
        "maxModelObservationBytes": 64_000,
    }
    design = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-design-contract",
            "experimentId": EXPERIMENT_ID,
            "protocolId": PROTOCOL_ID,
            "environmentBinding": binding(
                "git", "revision", git_revision, canonical_digest({"gitRevision": git_revision})
            ),
            "seats": [
                {
                    "seatId": "seat:adaptive-edit-agent",
                    "role": "repository-edit-agent",
                    "occupantKind": "agent",
                    "occupantRef": "provider:deepseek:model-assigned-by-intervention",
                    "parityGroup": "parity:adaptive-edit-agent",
                    "observationContract": file_binding(observation_file, owner="harness"),
                    "actionContract": file_binding(action_file, owner="harness"),
                    "resourceContract": binding(
                        "study",
                        "run-budget",
                        "budget:experimental-fabric-pilot-r1",
                        canonical_digest(resource_contract),
                    ),
                    "authorityContract": runner_ref,
                    "adapterBinding": adapter_ref,
                }
            ],
            "factors": [
                {"factorId": "factor:model", "factorRole": "treatment", "value": "assigned-by-model-intervention"},
                {"factorId": "factor:harness-codec", "factorRole": "treatment", "value": "assigned-by-codec-intervention"},
                {"factorId": "factor:task", "factorRole": "blocking", "value": "three-frozen-deterministic-task-families"},
                {"factorId": "factor:run-order", "factorRole": "nuisance", "value": f"seeded-shuffle:{SEED}"},
            ],
            "metricSpecs": [
                {
                    "metricId": item["metricId"],
                    "specRef": f"metrics/{item['metricId'].split(':', 1)[1]}.json",
                    "specDigest": item["specDigest"],
                }
                for item in metrics
            ],
            "randomness": {
                "seedPolicy": "provider-owned",
                "seedManifestDigest": schedule_digest,
                "assignmentSeedPolicy": "fixed",
                "executionRandomnessPolicy": "provider-owned",
            },
            "dataClassPolicy": ["EXPERIENCE", "DERIVED"],
            "nonClaims": [
                "Experimental assignment seed does not control DeepSeek generation randomness.",
                "The in-memory Runtime-shaped edit fixture is not durable Runtime owner truth.",
                "This pilot does not establish general model or Harness superiority.",
            ],
        },
        "contractDigest",
    )
    validate("experimental-design-contract-r1.schema.json", design)

    allocation_ref = binding(
        "study",
        "allocation-manifest",
        "allocation:experimental-fabric-pilot-r1",
        schedule_digest,
    )
    model_intervention = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-intervention-contract",
            "contractId": "intervention:model-selection-r1",
            "experimentId": EXPERIMENT_ID,
            "frozenBaseDigest": design["contractDigest"],
            "unitOfAssignment": "run",
            "assignmentPolicy": "blocked",
            "treatmentFactor": {
                "factorId": "factor:model",
                "levels": [{"levelId": model, "value": model} for model in MODELS],
            },
            "assignments": [
                {"unitRef": trial["trialId"], "levelId": trial["model"], "blockRef": trial["taskId"]}
                for trial in schedule["trials"]
            ],
            "assignmentEvidenceRef": allocation_ref,
            "nonClaims": ["Model assignment does not grant Provider effect authority."],
        },
        "contractDigest",
    )
    codec_intervention = seal(
        {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-intervention-contract",
            "contractId": "intervention:harness-codec-r1",
            "experimentId": EXPERIMENT_ID,
            "frozenBaseDigest": design["contractDigest"],
            "unitOfAssignment": "run",
            "assignmentPolicy": "blocked",
            "treatmentFactor": {
                "factorId": "factor:harness-codec",
                "levels": [{"levelId": codec, "value": codec} for codec in CODECS],
            },
            "assignments": [
                {"unitRef": trial["trialId"], "levelId": trial["codec"], "blockRef": trial["taskId"]}
                for trial in schedule["trials"]
            ],
            "assignmentEvidenceRef": allocation_ref,
            "nonClaims": ["Codec assignment does not expand Tool or Runtime authority."],
        },
        "contractDigest",
    )
    validate("experimental-intervention-contract-r1.schema.json", model_intervention)
    validate("experimental-intervention-contract-r1.schema.json", codec_intervention)

    prereg = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factorial-preregistration",
        "experimentId": EXPERIMENT_ID,
        "gitRevision": git_revision,
        "design": design,
        "modelIntervention": model_intervention,
        "codecIntervention": codec_intervention,
        "schedule": schedule,
        "taskBindings": task_digest_rows,
        "metricSpecs": metrics,
        "primaryMetricId": "metric:hidden-pass",
        "analysisPlan": {
            "primary": "descriptive balanced 2x2 Model×Harness cell rates, blocked by task family",
            "continuous": ["metric:total-tokens", "metric:tool-calls", "metric:elapsed-ms"],
            "interaction": "difference-in-differences of cell means/rates",
            "significanceClaim": False,
            "reason": "three task blocks and one live run per cell are pilot-scale",
        },
        "stopRules": [
            "Run each of the 12 preregistered trials at most once.",
            "Do not retry a completed or exception trial based on its outcome.",
            "If the process stops after trial_started but before trial_completed, fail closed and reconcile before any replay.",
            "Do not expand the campaign based on observed treatment performance in this pilot.",
        ],
        "nonClaims": [
            "Provider-owned generation randomness is not controlled by the allocation seed.",
            "The pilot is not a model leaderboard or production default-selection authority.",
        ],
    }
    prereg["preregistrationDigest"] = canonical_digest(prereg)
    return prereg


def write_preregistration(output_dir: Path, prereg: dict[str, Any]) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        existing = output_dir / "preregistration.json"
        if not existing.is_file():
            raise RuntimeError("non-empty output directory lacks preregistration; refuse overwrite")
        current = json.loads(existing.read_text(encoding="utf-8"))
        if current.get("preregistrationDigest") != prereg["preregistrationDigest"]:
            raise RuntimeError("existing preregistration differs; refuse mixed campaign")
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    json_write(output_dir / "preregistration.json", prereg)
    json_write(output_dir / "allocation.json", prereg["schedule"])
    json_write(output_dir / "design.json", prereg["design"])
    json_write(output_dir / "intervention-model.json", prereg["modelIntervention"])
    json_write(output_dir / "intervention-codec.json", prereg["codecIntervention"])
    metrics_dir = output_dir / "metrics"
    for item in prereg["metricSpecs"]:
        json_write(metrics_dir / f"{item['metricId'].split(':', 1)[1]}.json", item)


def read_journal(path: Path) -> tuple[set[str], set[str]]:
    started: set[str] = set()
    completed: set[str] = set()
    if not path.exists():
        return started, completed
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("event") == "trial_started":
            started.add(row["trialId"])
        elif row.get("event") == "trial_completed":
            completed.add(row["trialId"])
    return started, completed


def trial_record_path(output_dir: Path, trial_id: str) -> Path:
    return output_dir / "trials" / f"{trial_id.replace(':', '-')}.json"


def execute_trials(output_dir: Path, prereg: dict[str, Any]) -> list[dict[str, Any]]:
    live = load_live_runner()
    base = DeepSeekSettings.from_secret_file(
        timeout_seconds=60.0,
        max_response_bytes=2_097_152,
        max_output_tokens=2048,
    )
    journal = output_dir / "journal.jsonl"
    started, completed = read_journal(journal)
    uncertain = sorted(started - completed)
    if uncertain:
        raise RuntimeError(f"uncertain previously-started trials require reconciliation: {uncertain}")

    records: list[dict[str, Any]] = []
    for trial in prereg["schedule"]["trials"]:
        trial_id = trial["trialId"]
        path = trial_record_path(output_dir, trial_id)
        if trial_id in completed:
            if not path.is_file():
                raise RuntimeError(f"completed journal entry lacks trial artifact: {trial_id}")
            records.append(json.loads(path.read_text(encoding="utf-8")))
            continue
        journal_append(
            journal,
            {
                "event": "trial_started",
                "trialId": trial_id,
                "ordinal": trial["ordinal"],
                "taskId": trial["taskId"],
                "model": trial["model"],
                "codec": trial["codec"],
                "observedAtUnixMs": int(time.time() * 1000),
            },
        )
        settings = replace(base, model=trial["model"])
        result = live.run_one(
            trial["codec"],
            trial["ordinal"],
            settings,
            task_spec=live.TASK_SPECS[trial["taskId"]],
            max_total_tokens=MAX_TOTAL_TOKENS,
        )
        record = {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-factorial-live-trial",
            "experimentId": EXPERIMENT_ID,
            **trial,
            "provider": "deepseek",
            "providerRandomness": "provider-owned",
            "result": result,
        }
        record["recordDigest"] = canonical_digest(record)
        json_write(path, record)
        journal_append(
            journal,
            {
                "event": "trial_completed",
                "trialId": trial_id,
                "recordDigest": record["recordDigest"],
                "status": result.get("status"),
                "observedAtUnixMs": int(time.time() * 1000),
            },
        )
        print(
            json.dumps(
                {
                    "trial": trial_id,
                    "ordinal": trial["ordinal"],
                    "task": trial["taskId"],
                    "model": trial["model"],
                    "codec": trial["codec"],
                    "status": result.get("status"),
                    "hiddenPassed": result.get("hiddenPassed"),
                    "candidateCompleted": result.get("candidateCompleted"),
                    "totalTokens": (result.get("usage") or {}).get("totalTokens") if isinstance(result.get("usage"), dict) else None,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        records.append(record)
    return records


def make_episode(record: dict[str, Any], prereg: dict[str, Any]) -> dict[str, Any]:
    result = record["result"]
    source_digest = record["recordDigest"]
    task_binding = next(item for item in prereg["taskBindings"] if item["taskId"] == record["taskId"])
    owner_refs = [
        {
            "ownerId": "git",
            "objectKind": "revision",
            "objectId": prereg["gitRevision"],
            "relation": "source-revision",
            "digest": canonical_digest({"gitRevision": prereg["gitRevision"]}),
        },
        {
            "ownerId": "provider:deepseek",
            "objectKind": "model",
            "objectId": record["model"],
            "relation": "requested-model",
            "digest": canonical_digest({"provider": "deepseek", "model": record["model"]}),
        },
        {
            "ownerId": "harness",
            "objectKind": "treatment-codec",
            "objectId": record["codec"],
            "relation": "harness-treatment",
            "digest": canonical_digest({"codec": record["codec"]}),
        },
        {
            "ownerId": "git",
            "objectKind": "evaluation-task",
            "objectId": record["taskId"],
            "relation": "blocked-task",
            "digest": task_binding["taskDigest"],
        },
    ]
    measures: list[dict[str, Any]] = []
    usage = result.get("usage") if isinstance(result, dict) else None
    values = {
        "pilot.hidden_pass": int(bool(result.get("hiddenPassed"))),
        "pilot.candidate_completed": int(bool(result.get("candidateCompleted"))),
        "pilot.total_tokens": int(usage.get("totalTokens", 0)) if isinstance(usage, dict) else 0,
        "pilot.tool_calls": int(result.get("toolCalls", 0) or 0),
        "pilot.elapsed_ms": int(result.get("elapsedMs", 0) or 0),
        "pilot.rejected_observations": int(result.get("rejectedObservations", 0) or 0),
    }
    units = {
        "pilot.hidden_pass": "boolean-as-0-or-1",
        "pilot.candidate_completed": "boolean-as-0-or-1",
        "pilot.total_tokens": "tokens",
        "pilot.tool_calls": "calls",
        "pilot.elapsed_ms": "milliseconds",
        "pilot.rejected_observations": "observations",
    }
    for name, value in values.items():
        measures.append({"name": name, "value": value, "unit": units[name]})
    episode = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-episode-binding",
        "profileId": "experimental-fabric-model-harness-pilot-r1",
        "episodeId": f"episode:{record['trialId']}",
        "dataClass": "EXPERIENCE",
        "anchor": {
            "ownerId": "study:experimental-fabric-pilot-r1",
            "objectKind": "live-trial-record",
            "objectId": record["trialId"],
            "sourceRecordDigest": source_digest,
        },
        "ownerRefs": owner_refs,
        "evidenceBindings": [
            {"kind": "trial-record", "count": 1, "setDigest": source_digest},
            {
                "kind": "runtime-operations",
                "count": len(result.get("runtimeOperations", [])),
                "setDigest": canonical_digest(result.get("runtimeOperations", [])),
            },
        ],
        "dimensions": [
            {"name": "pilot.model", "value": record["model"]},
            {"name": "pilot.codec", "value": record["codec"]},
            {"name": "pilot.task", "value": record["taskId"]},
            {"name": "pilot.ordinal", "value": record["ordinal"]},
            {"name": "pilot.status", "value": result.get("status")},
            {"name": "pilot.stop_code", "value": result.get("stopCode")},
        ],
        "measures": measures,
        "unresolved": (
            ["Provider generation randomness is provider-owned and not seed-addressable by this study."]
            + (["Trial ended with an exception; semantic outcome is incomplete."] if result.get("status") == "exception" else [])
        ),
        "nonClaims": [
            "Episode is a study projection, not Provider or Harness owner truth.",
            "The live edit workspace is an isolated in-memory Runtime-shaped fixture, not durable Runtime state.",
            "One pilot Episode does not establish general model capability.",
        ],
    }
    episode["projectionDigest"] = canonical_digest(episode)
    validate("experimental-episode-binding-r1.schema.json", episode)
    return episode


def metric_value(metric_id: str, result: dict[str, Any]) -> Any | None:
    if metric_id == "metric:hidden-pass":
        return bool(result.get("hiddenPassed"))
    if metric_id == "metric:candidate-completed":
        return bool(result.get("candidateCompleted"))
    if metric_id == "metric:total-tokens":
        usage = result.get("usage")
        return int(usage.get("totalTokens")) if isinstance(usage, dict) and isinstance(usage.get("totalTokens"), int) else None
    if metric_id == "metric:tool-calls":
        return int(result["toolCalls"]) if isinstance(result.get("toolCalls"), int) else None
    if metric_id == "metric:elapsed-ms":
        return int(result["elapsedMs"]) if isinstance(result.get("elapsedMs"), int) else None
    if metric_id == "metric:rejected-observations":
        return int(result["rejectedObservations"]) if isinstance(result.get("rejectedObservations"), int) else None
    raise KeyError(metric_id)


def make_evaluations(records: list[dict[str, Any]], episodes: dict[str, dict[str, Any]], prereg: dict[str, Any]) -> list[dict[str, Any]]:
    evaluator = binding(
        "study",
        "deterministic-evaluator",
        "experimental-fabric-pilot-r1-evaluator",
        file_digest(Path(__file__)),
    )
    evaluations: list[dict[str, Any]] = []
    for record in records:
        result = record["result"]
        episode = episodes[record["trialId"]]
        evidence_binding = binding(
            "study:experimental-fabric-pilot-r1",
            "live-trial-record",
            record["trialId"],
            record["recordDigest"],
        )
        for metric in prereg["metricSpecs"]:
            value = metric_value(metric["metricId"], result)
            if value is None:
                continue
            evaluation = {
                "schemaVersion": 1,
                "kind": "ordivon.experimental-evaluation-record",
                "evaluationId": f"evaluation:{record['trialId']}:{metric['metricId'].split(':', 1)[1]}",
                "experimentId": EXPERIMENT_ID,
                "metricSpec": {"metricId": metric["metricId"], "specDigest": metric["specDigest"]},
                "subjects": [{"episodeId": episode["episodeId"], "projectionDigest": episode["projectionDigest"]}],
                "value": value,
                "claimEvidenceLevel": "deterministic-derived",
                "evidenceInputs": [{"evidenceLevel": "deterministic-observation", "binding": evidence_binding}],
                "providerBinding": evaluator,
                "limitations": list(metric["knownLimitations"]),
                "nonClaims": [
                    "Evaluation is derived from the observed trial record and does not replace natural-owner truth.",
                    "Pilot result is not a production routing or model-selection decision.",
                ],
            }
            evaluation["recordDigest"] = canonical_digest(evaluation)
            validate("experimental-evaluation-record-r1.schema.json", evaluation)
            evaluations.append(evaluation)
    return evaluations


def mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def effect_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    def result_rows(model: str | None = None, codec: str | None = None) -> list[dict[str, Any]]:
        rows = records
        if model is not None:
            rows = [row for row in rows if row["model"] == model]
        if codec is not None:
            rows = [row for row in rows if row["codec"] == codec]
        return rows

    cells: dict[str, Any] = {}
    for model in MODELS:
        for codec in CODECS:
            subset = result_rows(model, codec)
            hidden = [1.0 if row["result"].get("hiddenPassed") else 0.0 for row in subset]
            completed = [1.0 if row["result"].get("candidateCompleted") else 0.0 for row in subset]
            tokens = [
                float(row["result"]["usage"]["totalTokens"])
                for row in subset
                if isinstance(row["result"].get("usage"), dict)
                and isinstance(row["result"]["usage"].get("totalTokens"), int)
            ]
            tool_calls = [float(row["result"]["toolCalls"]) for row in subset if isinstance(row["result"].get("toolCalls"), int)]
            elapsed = [float(row["result"]["elapsedMs"]) for row in subset if isinstance(row["result"].get("elapsedMs"), int)]
            cells[f"{model}|{codec}"] = {
                "runs": len(subset),
                "hiddenPassRate": mean(hidden),
                "candidateCompletionRate": mean(completed),
                "meanTotalTokens": mean(tokens),
                "meanToolCalls": mean(tool_calls),
                "meanElapsedMs": mean(elapsed),
                "exceptions": sum(row["result"].get("status") == "exception" for row in subset),
            }

    def avg_rate(rows: list[dict[str, Any]], key: str) -> float | None:
        vals = [1.0 if row["result"].get(key) else 0.0 for row in rows]
        return mean(vals)

    flash_rate = avg_rate(result_rows(MODELS[0]), "hiddenPassed")
    v4_rate = avg_rate(result_rows(MODELS[1]), "hiddenPassed")
    exact_rate = avg_rate(result_rows(codec=CODECS[0]), "hiddenPassed")
    anchored_rate = avg_rate(result_rows(codec=CODECS[1]), "hiddenPassed")
    def cell(model: str, codec: str) -> float | None:
        return cells[f"{model}|{codec}"]["hiddenPassRate"]

    interaction = None
    if all(cell(m, c) is not None for m in MODELS for c in CODECS):
        interaction = (
            (cell(MODELS[1], CODECS[0]) - cell(MODELS[1], CODECS[1]))
            - (cell(MODELS[0], CODECS[0]) - cell(MODELS[0], CODECS[1]))
        )

    by_task = []
    for task in TASK_IDS:
        rows = [row for row in records if row["taskId"] == task]
        by_task.append(
            {
                "taskId": task,
                "rows": [
                    {
                        "model": row["model"],
                        "codec": row["codec"],
                        "hiddenPassed": bool(row["result"].get("hiddenPassed")),
                        "candidateCompleted": bool(row["result"].get("candidateCompleted")),
                        "status": row["result"].get("status"),
                    }
                    for row in sorted(rows, key=lambda item: (item["model"], item["codec"]))
                ],
            }
        )

    analysis = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factorial-pilot-analysis",
        "experimentId": EXPERIMENT_ID,
        "analysisClass": "pilot-descriptive-blocked-factorial",
        "cells": cells,
        "primaryEffects": {
            "modelHiddenPassDifference": None if flash_rate is None or v4_rate is None else v4_rate - flash_rate,
            "codecHiddenPassDifferenceExactMinusAnchored": None if exact_rate is None or anchored_rate is None else exact_rate - anchored_rate,
            "modelByCodecHiddenPassInteraction": interaction,
        },
        "taskBlocks": by_task,
        "nonClaims": [
            "No p-value, ranking, or broad capability claim is admitted from this 12-run pilot.",
            "Provider-owned stochasticity and temporal drift remain nuisance variation despite randomized order.",
        ],
    }
    analysis["analysisDigest"] = canonical_digest(analysis)
    return analysis


def binding_for_value(owner: str, kind: str, object_id: str, value: str) -> dict[str, Any]:
    return binding(owner, kind, object_id, canonical_digest({"value": value}))


def make_forks(records: list[dict[str, Any]], episodes: dict[str, dict[str, Any]], prereg: dict[str, Any]) -> dict[str, Any]:
    def select(task: str, model: str, codec: str) -> dict[str, Any]:
        return next(row for row in records if row["taskId"] == task and row["model"] == model and row["codec"] == codec)

    task = TASK_IDS[0]
    parent = select(task, MODELS[0], CODECS[0])
    declared_child = select(task, MODELS[0], CODECS[1])
    contaminated_child = select(task, MODELS[1], CODECS[1])
    parent_episode = episodes[parent["trialId"]]

    frozen = [
        {"name": "model", "binding": binding_for_value("provider:deepseek", "model", parent["model"], parent["model"])},
        {"name": "task", "binding": binding_for_value("study", "task", parent["taskId"], parent["taskId"])},
        {"name": "git-revision", "binding": binding_for_value("git", "revision", prereg["gitRevision"], prereg["gitRevision"])},
    ]
    codec_before = binding_for_value("harness", "codec", parent["codec"], parent["codec"])
    codec_after = binding_for_value("harness", "codec", declared_child["codec"], declared_child["codec"])
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-fork-manifest",
        "forkId": "fork:pilot-r1:declared-codec-change",
        "experimentId": EXPERIMENT_ID,
        "parentEpisode": {"episodeId": parent_episode["episodeId"], "projectionDigest": parent_episode["projectionDigest"]},
        "forkMode": "policy",
        "externalWorldMode": "live",
        "frozenBindings": frozen,
        "changedBindings": [{"name": "harness-codec", "before": codec_before, "after": codec_after}],
        "interventionRefs": [
            {
                "contractId": prereg["codecIntervention"]["contractId"],
                "contractDigest": prereg["codecIntervention"]["contractDigest"],
            }
        ],
        "randomness": {"strategy": "provider-owned"},
        "nonClaims": [
            "Live Provider reruns are comparative observations, not strict same-randomness counterfactuals.",
            "PASS_DECLARED_DIFFERENCE below means declared observable bindings matched, not that all latent variables were identical.",
        ],
    }
    manifest["manifestDigest"] = canonical_digest(manifest)
    validate("experimental-fork-manifest-r1.schema.json", manifest)
    declared_assessment = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-fork-assessment",
        "forkId": manifest["forkId"],
        "manifestDigest": manifest["manifestDigest"],
        "standing": "PASS_DECLARED_DIFFERENCE",
        "observedFrozenBindings": frozen,
        "observedChangedBindings": [
            {"name": "harness-codec", "beforeDigest": codec_before["digest"], "afterDigest": codec_after["digest"]}
        ],
        "undeclaredDifferences": [],
        "nonClaims": ["Assessment covers declared observable bindings only; provider-owned randomness remains uncontrolled."],
    }
    declared_assessment["assessmentDigest"] = canonical_digest(declared_assessment)
    validate("experimental-fork-assessment-r1.schema.json", declared_assessment)

    contaminated_manifest = dict(manifest)
    contaminated_manifest["forkId"] = "fork:pilot-r1:contaminated-codec-change"
    contaminated_manifest["nonClaims"] = list(manifest["nonClaims"]) + [
        "The paired observed child intentionally changes model as well as codec to pressure contamination detection."
    ]
    contaminated_manifest.pop("manifestDigest", None)
    contaminated_manifest["manifestDigest"] = canonical_digest(contaminated_manifest)
    validate("experimental-fork-manifest-r1.schema.json", contaminated_manifest)
    model_after = binding_for_value("provider:deepseek", "model", contaminated_child["model"], contaminated_child["model"])
    contaminated_assessment = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-fork-assessment",
        "forkId": contaminated_manifest["forkId"],
        "manifestDigest": contaminated_manifest["manifestDigest"],
        "standing": "CONTAMINATED",
        "observedFrozenBindings": frozen,
        "observedChangedBindings": [
            {"name": "harness-codec", "beforeDigest": codec_before["digest"], "afterDigest": codec_after["digest"]}
        ],
        "undeclaredDifferences": [
            {"name": "model", "beforeDigest": frozen[0]["binding"]["digest"], "afterDigest": model_after["digest"]}
        ],
        "nonClaims": ["Contamination standing identifies an undeclared observable factor change; it makes no claim about latent Provider randomness."],
    }
    contaminated_assessment["assessmentDigest"] = canonical_digest(contaminated_assessment)
    validate("experimental-fork-assessment-r1.schema.json", contaminated_assessment)
    return {
        "declared": {
            "parentTrialId": parent["trialId"],
            "childTrialId": declared_child["trialId"],
            "manifest": manifest,
            "assessment": declared_assessment,
        },
        "contaminated": {
            "parentTrialId": parent["trialId"],
            "childTrialId": contaminated_child["trialId"],
            "manifest": contaminated_manifest,
            "assessment": contaminated_assessment,
        },
    }


def finalize(output_dir: Path, prereg: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    records = sorted(records, key=lambda row: row["ordinal"])
    raw = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factorial-live-results",
        "experimentId": EXPERIMENT_ID,
        "preregistrationDigest": prereg["preregistrationDigest"],
        "records": records,
    }
    raw["resultSetDigest"] = canonical_digest(raw)
    json_write(output_dir / "results.json", raw)

    episode_list = [make_episode(record, prereg) for record in records]
    episodes = {record["trialId"]: episode for record, episode in zip(records, episode_list, strict=True)}
    with (output_dir / "episodes.jsonl").open("w", encoding="utf-8") as handle:
        for episode in episode_list:
            handle.write(json.dumps(episode, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")

    evaluations = make_evaluations(records, episodes, prereg)
    with (output_dir / "evaluations.jsonl").open("w", encoding="utf-8") as handle:
        for evaluation in evaluations:
            handle.write(json.dumps(evaluation, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")

    analysis = effect_analysis(records)
    json_write(output_dir / "analysis.json", analysis)
    forks = make_forks(records, episodes, prereg)
    json_write(output_dir / "forks.json", forks)

    acceptance = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factorial-pilot-acceptance",
        "experimentId": EXPERIMENT_ID,
        "gitRevision": prereg["gitRevision"],
        "preregistrationDigest": prereg["preregistrationDigest"],
        "resultSetDigest": raw["resultSetDigest"],
        "analysisDigest": analysis["analysisDigest"],
        "plannedTrials": len(prereg["schedule"]["trials"]),
        "observedTrials": len(records),
        "exceptionTrials": sum(row["result"].get("status") == "exception" for row in records),
        "episodeCount": len(episode_list),
        "evaluationCount": len(evaluations),
        "declaredForkStanding": forks["declared"]["assessment"]["standing"],
        "contaminatedForkStanding": forks["contaminated"]["assessment"]["standing"],
        "standing": "PASS_PILOT_MECHANICS" if len(records) == 12 else "FAIL_INCOMPLETE_CAMPAIGN",
        "nonClaims": [
            "PASS_PILOT_MECHANICS is protocol/execution acceptance, not a model or Harness winner declaration.",
            "Any observed treatment differences remain pilot-scale descriptive evidence.",
        ],
    }
    acceptance["acceptanceDigest"] = canonical_digest(acceptance)
    json_write(output_dir / "acceptance.json", acceptance)
    return acceptance


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preregister-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    prereg = build_preregistration()
    write_preregistration(output_dir, prereg)
    print(f"PREREGISTRATION_DIGEST={prereg['preregistrationDigest']}", flush=True)
    if args.preregister_only:
        return 0
    records = execute_trials(output_dir, prereg)
    acceptance = finalize(output_dir, prereg, records)
    print("FINAL_ACCEPTANCE=" + json.dumps(acceptance, sort_keys=True), flush=True)
    return 0 if acceptance["standing"] == "PASS_PILOT_MECHANICS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
