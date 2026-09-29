from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from fractions import Fraction
from typing import Any

from anc_canonical import canonical_digest

EXPERIMENT_ID = "experiment:experimental-fabric-model-harness-pilot-r2-20260929"
MODELS = ("deepseek-flash", "deepseek-v4-pro")
CODECS = ("exact-replacement-v1", "anchored-line-v1")
FAMILIES = ("repository_repair", "edit_addressing", "edit_multiregion")
TASKS_PER_FAMILY = 8
INDEPENDENT_TASK_BLOCKS = len(FAMILIES) * TASKS_PER_FAMILY
SENTINELS_PER_FAMILY = 1
ASSIGNMENT_SEED = 20260929


def rational(value: Fraction | int) -> dict[str, int]:
    exact = value if isinstance(value, Fraction) else Fraction(value)
    return {"numerator": exact.numerator, "denominator": exact.denominator}


def _sha(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def validate_provider_identity_preflight(value: dict[str, Any]) -> None:
    if value.get("kind") != "ordivon.experimental-provider-model-identity-preflight":
        raise ValueError("provider identity preflight kind differs")
    if value.get("provider") != "deepseek":
        raise ValueError("R2 currently requires DeepSeek provider identity evidence")
    rows = value.get("models")
    if not isinstance(rows, list):
        raise ValueError("provider preflight models must be a list")
    by_requested = {row.get("requestedModelId"): row for row in rows if isinstance(row, dict)}
    if set(by_requested) != set(MODELS):
        raise ValueError(f"provider preflight must bind exactly {MODELS}")
    effective = []
    for requested in MODELS:
        row = by_requested[requested]
        if row.get("standing") != "PASS_DISTINCT_EFFECTIVE_IDENTITY":
            raise ValueError(f"model identity preflight did not pass for {requested}")
        observed = row.get("effectiveModelIds")
        if not isinstance(observed, list) or len(observed) != 1 or not isinstance(observed[0], str):
            raise ValueError(f"{requested} must have exactly one observed effective model identity")
        effective.append(observed[0])
    if len(set(effective)) != len(MODELS):
        raise ValueError(f"requested model factor collapsed to effective identities: {effective}")
    if value.get("standing") != "PASS_DISTINCT_EFFECTIVE_IDENTITIES":
        raise ValueError("provider identity preflight overall standing is not PASS")


def validate_task_manifest(value: dict[str, Any]) -> list[dict[str, Any]]:
    if value.get("kind") != "ordivon.experimental-task-bank-manifest":
        raise ValueError("task manifest kind differs")
    tasks = value.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("task manifest tasks must be a list")
    if len(tasks) != INDEPENDENT_TASK_BLOCKS:
        raise ValueError(f"R2 requires exactly {INDEPENDENT_TASK_BLOCKS} independent task blocks")
    ids: set[str] = set()
    digests: set[str] = set()
    family_counts: Counter[str] = Counter()
    sentinel_counts: Counter[str] = Counter()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("task entry must be an object")
        task_id = task.get("taskId")
        family = task.get("family")
        task_digest = task.get("taskDigest")
        qa_digest = task.get("qaDigest")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("taskId missing")
        if task_id in ids:
            raise ValueError(f"duplicate taskId: {task_id}")
        ids.add(task_id)
        if family not in FAMILIES:
            raise ValueError(f"unexpected task family: {family}")
        family_counts[family] += 1
        if not isinstance(task_digest, str) or not task_digest.startswith("sha256:"):
            raise ValueError(f"taskDigest missing for {task_id}")
        if task_digest in digests:
            raise ValueError(f"duplicate task payload digest: {task_digest}")
        digests.add(task_digest)
        if not isinstance(qa_digest, str) or not qa_digest.startswith("sha256:"):
            raise ValueError(f"qaDigest missing for {task_id}")
        if task.get("qaStanding") != "PASS":
            raise ValueError(f"task QA did not pass: {task_id}")
        if task.get("sentinel") is True:
            sentinel_counts[family] += 1
    expected_counts = {family: TASKS_PER_FAMILY for family in FAMILIES}
    if dict(family_counts) != expected_counts:
        raise ValueError(f"task family counts differ: {dict(family_counts)} != {expected_counts}")
    expected_sentinels = {family: SENTINELS_PER_FAMILY for family in FAMILIES}
    if dict(sentinel_counts) != expected_sentinels:
        raise ValueError(
            f"sentinel counts differ: {dict(sentinel_counts)} != {expected_sentinels}"
        )
    return sorted(tasks, key=lambda row: row["taskId"])


def compile_schedule(
    task_manifest: dict[str, Any],
    provider_preflight: dict[str, Any],
    *,
    seed: int = ASSIGNMENT_SEED,
) -> dict[str, Any]:
    validate_provider_identity_preflight(provider_preflight)
    tasks = validate_task_manifest(task_manifest)
    rng = random.Random(seed)
    randomized_tasks = list(tasks)
    rng.shuffle(randomized_tasks)
    trials: list[dict[str, Any]] = []
    ordinal = 0
    for task in randomized_tasks:
        cells = [(model, codec) for model in MODELS for codec in CODECS]
        rng.shuffle(cells)
        for model, codec in cells:
            ordinal += 1
            trials.append(
                {
                    "trialId": f"trial:r2:{ordinal:03d}",
                    "ordinal": ordinal,
                    "taskId": task["taskId"],
                    "taskFamily": task["family"],
                    "model": model,
                    "codec": codec,
                    "providerReplicate": 1,
                    "independentTaskBlock": task["taskId"],
                    "sentinel": bool(task.get("sentinel")),
                }
            )
    sentinel_tasks = [task for task in randomized_tasks if task.get("sentinel") is True]
    rng.shuffle(sentinel_tasks)
    for task in sentinel_tasks:
        cells = [(model, codec) for model in MODELS for codec in CODECS]
        rng.shuffle(cells)
        for model, codec in cells:
            ordinal += 1
            trials.append(
                {
                    "trialId": f"trial:r2:{ordinal:03d}",
                    "ordinal": ordinal,
                    "taskId": task["taskId"],
                    "taskFamily": task["family"],
                    "model": model,
                    "codec": codec,
                    "providerReplicate": 2,
                    "independentTaskBlock": task["taskId"],
                    "sentinel": True,
                }
            )
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-blocked-factorial-schedule",
        "experimentId": EXPERIMENT_ID,
        "assignmentSeed": seed,
        "models": list(MODELS),
        "codecs": list(CODECS),
        "taskFamilies": list(FAMILIES),
        "independentTaskBlockCount": INDEPENDENT_TASK_BLOCKS,
        "coreTrialCount": INDEPENDENT_TASK_BLOCKS * len(MODELS) * len(CODECS),
        "nestedSentinelTrialCount": len(FAMILIES) * SENTINELS_PER_FAMILY * len(MODELS) * len(CODECS),
        "totalTrialCount": len(trials),
        "replicationLaw": "task-instance-is-independent; providerReplicate>1 is nested stochasticity evidence and does not increase independentTaskBlockCount",
        "taskManifestDigest": task_manifest["manifestDigest"],
        "providerIdentityPreflightDigest": provider_preflight["preflightDigest"],
        "trials": trials,
    }
    result["scheduleDigest"] = canonical_digest(result)
    return result


def validate_complete_core_cells(records: list[dict[str, Any]]) -> None:
    core = [row for row in records if row.get("providerReplicate") == 1]
    by_task: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in core:
        by_task[str(row["taskId"])].add((str(row["model"]), str(row["codec"])))
    expected = {(model, codec) for model in MODELS for codec in CODECS}
    if len(by_task) != INDEPENDENT_TASK_BLOCKS:
        raise ValueError(f"expected {INDEPENDENT_TASK_BLOCKS} task blocks, got {len(by_task)}")
    missing = {task: sorted(expected - cells) for task, cells in by_task.items() if cells != expected}
    if missing:
        raise ValueError(f"incomplete Model×Harness cells within task blocks: {missing}")


def task_block_contrasts(records: list[dict[str, Any]], outcome_key: str) -> dict[str, Any]:
    validate_complete_core_cells(records)
    core = [row for row in records if row.get("providerReplicate") == 1]
    by_task: dict[str, dict[tuple[str, str], int]] = defaultdict(dict)
    for row in core:
        value = row.get(outcome_key)
        if isinstance(value, bool):
            numeric = int(value)
        elif isinstance(value, int) and value in (0, 1):
            numeric = value
        else:
            raise ValueError(f"{outcome_key} must be binary for {row.get('trialId')}")
        by_task[str(row["taskId"])][(str(row["model"]), str(row["codec"]))] = numeric

    model_task: list[Fraction] = []
    harness_task: list[Fraction] = []
    interaction_task: list[Fraction] = []
    for task_id in sorted(by_task):
        cell = by_task[task_id]
        flash_exact = cell[(MODELS[0], CODECS[0])]
        flash_anchored = cell[(MODELS[0], CODECS[1])]
        pro_exact = cell[(MODELS[1], CODECS[0])]
        pro_anchored = cell[(MODELS[1], CODECS[1])]
        model_task.append(Fraction((pro_exact - flash_exact) + (pro_anchored - flash_anchored), 2))
        harness_task.append(Fraction((flash_exact - flash_anchored) + (pro_exact - pro_anchored), 2))
        interaction_task.append(Fraction((pro_exact - pro_anchored) - (flash_exact - flash_anchored), 1))

    def average(values: list[Fraction]) -> Fraction:
        return sum(values, Fraction(0, 1)) / len(values)

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-task-block-binary-contrasts",
        "experimentId": EXPERIMENT_ID,
        "outcome": outcome_key,
        "independentTaskBlockCount": len(by_task),
        "modelMarginalDifferenceProMinusFlash": rational(average(model_task)),
        "harnessMarginalDifferenceExactMinusAnchored": rational(average(harness_task)),
        "modelByHarnessDifferenceInDifferences": rational(average(interaction_task)),
        "perTask": [
            {
                "taskId": task_id,
                "modelContrast": rational(model_task[index]),
                "harnessContrast": rational(harness_task[index]),
                "interaction": rational(interaction_task[index]),
            }
            for index, task_id in enumerate(sorted(by_task))
        ],
        "nonClaims": [
            "Nested Provider replicates are excluded from the independent task-block estimand.",
            "These exact contrasts are descriptive until the preregistered uncertainty method and task-population scope are applied.",
        ],
    }
    result["contrastDigest"] = canonical_digest(result)
    return result


def synthetic_task_manifest() -> dict[str, Any]:
    tasks = []
    for family in FAMILIES:
        for index in range(1, TASKS_PER_FAMILY + 1):
            task_id = f"R2-{family.upper().replace('_', '-')}-{index:02d}"
            tasks.append(
                {
                    "taskId": task_id,
                    "family": family,
                    "taskDigest": _sha(f"task:{task_id}"),
                    "qaDigest": _sha(f"qa:{task_id}"),
                    "qaStanding": "PASS",
                    "sentinel": index == 1,
                }
            )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-task-bank-manifest",
        "experimentId": EXPERIMENT_ID,
        "tasks": tasks,
    }
    value["manifestDigest"] = canonical_digest(value)
    return value


def synthetic_provider_preflight(*, collapsed: bool = False) -> dict[str, Any]:
    effective = {
        "deepseek-flash": "deepseek-flash",
        "deepseek-v4-pro": "deepseek-flash" if collapsed else "deepseek-v4-pro",
    }
    rows = [
        {
            "requestedModelId": requested,
            "effectiveModelIds": [effective[requested]],
            "standing": "PASS_DISTINCT_EFFECTIVE_IDENTITY",
        }
        for requested in MODELS
    ]
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-provider-model-identity-preflight",
        "experimentId": EXPERIMENT_ID,
        "provider": "deepseek",
        "models": rows,
        "standing": "PASS_DISTINCT_EFFECTIVE_IDENTITIES",
    }
    value["preflightDigest"] = canonical_digest(value)
    return value


def main() -> int:
    manifest = synthetic_task_manifest()
    preflight = synthetic_provider_preflight()
    schedule = compile_schedule(manifest, preflight)
    print(json.dumps(schedule, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
