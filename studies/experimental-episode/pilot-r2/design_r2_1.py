from __future__ import annotations

import importlib.util
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from anc_canonical import canonical_digest

HERE = Path(__file__).resolve()
BASE_DESIGN_PATH = HERE.with_name("design_r2.py")
DESIGN_REVISION = "r2.1"
CALIBRATION_ASSIGNMENT_SEED = 2026092903
INFERENTIAL_ASSIGNMENT_SEED = 2026092904
WAVE_COUNT = 4


def load_base_design():
    spec = importlib.util.spec_from_file_location("pilot_r2_base_design_r2_1", BASE_DESIGN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load R2 base design: {BASE_DESIGN_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cell_rows(rng: random.Random) -> list[tuple[str, str]]:
    base = load_base_design()
    cells = [(model, codec) for model in base.MODELS for codec in base.CODECS]
    rng.shuffle(cells)
    return cells


def _validate_calibration_manifest(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    base = load_base_design()
    if manifest.get("kind") != "ordivon.experimental-task-bank-manifest" or manifest.get("cohort") != "calibration":
        raise ValueError("calibration schedule requires calibration task-bank manifest")
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 6:
        raise ValueError("R2.1 calibration requires exactly six disjoint tasks")
    by_family: dict[str, list[dict[str, Any]]] = {family: [] for family in base.FAMILIES}
    seen: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict) or task.get("qaStanding") != "PASS":
            raise ValueError("all calibration tasks must have PASS QA")
        task_id = task.get("taskId")
        family = task.get("family")
        if not isinstance(task_id, str) or not task_id or task_id in seen:
            raise ValueError("calibration task IDs must be unique")
        if family not in by_family:
            raise ValueError(f"unknown calibration family: {family}")
        seen.add(task_id)
        by_family[family].append(task)
    if any(len(rows) != 2 for rows in by_family.values()):
        raise ValueError("R2.1 calibration requires exactly two tasks per family")
    return by_family


def compile_balanced_calibration_schedule(
    manifest: dict[str, Any], *, seed: int = CALIBRATION_ASSIGNMENT_SEED
) -> dict[str, Any]:
    base = load_base_design()
    by_family = _validate_calibration_manifest(manifest)
    rng = random.Random(seed)
    for rows in by_family.values():
        rng.shuffle(rows)

    # Two complete family-balanced rounds. The second round rotates the family order so
    # the campaign is not A,B,C,A,B,C at identical within-round positions forever.
    round_orders = [list(base.FAMILIES), [base.FAMILIES[1], base.FAMILIES[2], base.FAMILIES[0]]]
    trials: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    ordinal = 0
    block_ordinal = 0
    for round_index, family_order in enumerate(round_orders, start=1):
        for family in family_order:
            block_ordinal += 1
            task = by_family[family][round_index - 1]
            block_id = f"block:r2.1:cal:{block_ordinal:02d}"
            block_trial_ids: list[str] = []
            for model, codec in _cell_rows(rng):
                ordinal += 1
                trial_id = f"trial:r2.1:cal:{ordinal:02d}"
                block_trial_ids.append(trial_id)
                trials.append(
                    {
                        "trialId": trial_id,
                        "ordinal": ordinal,
                        "blockId": block_id,
                        "blockOrdinal": block_ordinal,
                        "familyRound": round_index,
                        "taskId": task["taskId"],
                        "taskFamily": family,
                        "model": model,
                        "codec": codec,
                        "providerReplicate": 1,
                    }
                )
            blocks.append(
                {
                    "blockId": block_id,
                    "blockOrdinal": block_ordinal,
                    "familyRound": round_index,
                    "taskId": task["taskId"],
                    "taskFamily": family,
                    "trialIds": block_trial_ids,
                }
            )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-schedule",
        "designRevision": DESIGN_REVISION,
        "experimentId": base.EXPERIMENT_ID,
        "assignmentSeed": seed,
        "taskManifestDigest": manifest["manifestDigest"],
        "taskCount": 6,
        "taskBlockCount": 6,
        "trialCount": 24,
        "atomicExecutionUnit": "complete-four-cell-task-block",
        "familyRoundOrders": round_orders,
        "blocks": blocks,
        "trials": trials,
        "nonClaims": [
            "Calibration trials are disjoint from the inferential bank and never enter inferential effect estimates.",
            "The balanced order changes execution order only; it does not change the full 24-cell calibration gate semantics.",
        ],
    }
    value["scheduleDigest"] = canonical_digest(value)
    return value


def _wave_core_assignments(tasks: list[dict[str, Any]], rng: random.Random) -> dict[int, list[dict[str, Any]]]:
    base = load_base_design()
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        by_family[str(task["family"])].append(task)
    assignments: dict[int, list[dict[str, Any]]] = {wave: [] for wave in range(1, WAVE_COUNT + 1)}
    for family in base.FAMILIES:
        rows = list(by_family[family])
        sentinels = [row for row in rows if row.get("sentinel") is True]
        ordinary = [row for row in rows if row.get("sentinel") is not True]
        if len(sentinels) != 1 or len(ordinary) != 7:
            raise ValueError(f"R2.1 requires one sentinel and seven ordinary tasks for {family}")
        rng.shuffle(ordinary)
        assignments[1].extend([sentinels[0], ordinary[0]])
        assignments[2].extend(ordinary[1:3])
        assignments[3].extend(ordinary[3:5])
        assignments[4].extend(ordinary[5:7])
    return assignments


def compile_balanced_inferential_schedule(
    task_manifest: dict[str, Any],
    provider_preflight: dict[str, Any],
    *,
    seed: int = INFERENTIAL_ASSIGNMENT_SEED,
) -> dict[str, Any]:
    base = load_base_design()
    base.validate_provider_identity_preflight(provider_preflight)
    tasks = base.validate_task_manifest(task_manifest)
    rng = random.Random(seed)
    wave_tasks = _wave_core_assignments(tasks, rng)

    sentinel_by_family = {str(task["family"]): task for task in tasks if task.get("sentinel") is True}
    repeat_families = list(base.FAMILIES)
    rng.shuffle(repeat_families)
    repeat_wave_by_family = {family: wave for family, wave in zip(repeat_families, (2, 3, 4), strict=True)}

    trials: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    ordinal = 0
    block_ordinal = 0
    wave_summaries = []
    for wave in range(1, WAVE_COUNT + 1):
        per_family: dict[str, list[dict[str, Any]]] = {family: [] for family in base.FAMILIES}
        for task in wave_tasks[wave]:
            per_family[str(task["family"])].append(task)
        if any(len(rows) != 2 for rows in per_family.values()):
            raise ValueError(f"wave {wave} does not contain exactly two tasks per family")
        for rows in per_family.values():
            rng.shuffle(rows)
        family_order = list(base.FAMILIES)
        rotation = (wave - 1) % len(family_order)
        family_order = family_order[rotation:] + family_order[:rotation]
        ordered_core = [per_family[family][slot] for slot in range(2) for family in family_order]

        wave_block_ids: list[str] = []
        for task in ordered_core:
            block_ordinal += 1
            block_id = f"block:r2.1:inf:{block_ordinal:03d}"
            wave_block_ids.append(block_id)
            block_trial_ids = []
            for model, codec in _cell_rows(rng):
                ordinal += 1
                trial_id = f"trial:r2.1:{ordinal:03d}"
                block_trial_ids.append(trial_id)
                trials.append(
                    {
                        "trialId": trial_id,
                        "ordinal": ordinal,
                        "blockId": block_id,
                        "blockOrdinal": block_ordinal,
                        "wave": wave,
                        "taskId": task["taskId"],
                        "taskFamily": task["family"],
                        "model": model,
                        "codec": codec,
                        "providerReplicate": 1,
                        "independentTaskBlock": task["taskId"],
                        "sentinel": bool(task.get("sentinel")),
                    }
                )
            blocks.append(
                {
                    "blockId": block_id,
                    "blockOrdinal": block_ordinal,
                    "wave": wave,
                    "blockRole": "core-independent-task",
                    "taskId": task["taskId"],
                    "taskFamily": task["family"],
                    "providerReplicate": 1,
                    "trialIds": block_trial_ids,
                }
            )

        repeat_family = next((family for family, repeat_wave in repeat_wave_by_family.items() if repeat_wave == wave), None)
        if repeat_family is not None:
            task = sentinel_by_family[repeat_family]
            block_ordinal += 1
            block_id = f"block:r2.1:inf:{block_ordinal:03d}"
            wave_block_ids.append(block_id)
            block_trial_ids = []
            for model, codec in _cell_rows(rng):
                ordinal += 1
                trial_id = f"trial:r2.1:{ordinal:03d}"
                block_trial_ids.append(trial_id)
                trials.append(
                    {
                        "trialId": trial_id,
                        "ordinal": ordinal,
                        "blockId": block_id,
                        "blockOrdinal": block_ordinal,
                        "wave": wave,
                        "taskId": task["taskId"],
                        "taskFamily": task["family"],
                        "model": model,
                        "codec": codec,
                        "providerReplicate": 2,
                        "independentTaskBlock": task["taskId"],
                        "sentinel": True,
                    }
                )
            blocks.append(
                {
                    "blockId": block_id,
                    "blockOrdinal": block_ordinal,
                    "wave": wave,
                    "blockRole": "nested-sentinel-repeat",
                    "taskId": task["taskId"],
                    "taskFamily": task["family"],
                    "providerReplicate": 2,
                    "trialIds": block_trial_ids,
                }
            )
        wave_summaries.append(
            {
                "wave": wave,
                "coreIndependentTaskCount": 6,
                "coreTrialCount": 24,
                "nestedSentinelBlockCount": 0 if repeat_family is None else 1,
                "nestedSentinelFamily": repeat_family,
                "blockIds": wave_block_ids,
            }
        )

    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-blocked-factorial-wave-schedule",
        "designRevision": DESIGN_REVISION,
        "experimentId": base.EXPERIMENT_ID,
        "assignmentSeed": seed,
        "models": list(base.MODELS),
        "codecs": list(base.CODECS),
        "taskFamilies": list(base.FAMILIES),
        "waveCount": WAVE_COUNT,
        "independentTaskBlockCount": base.INDEPENDENT_TASK_BLOCKS,
        "coreTrialCount": 96,
        "nestedSentinelTrialCount": 12,
        "totalTrialCount": len(trials),
        "atomicExecutionUnit": "complete-four-cell-task-block",
        "replicationLaw": "task-instance-is-independent; providerReplicate>1 is nested stochasticity/time-sensitive diagnostic evidence and does not increase independentTaskBlockCount",
        "taskManifestDigest": task_manifest["manifestDigest"],
        "providerIdentityPreflightDigest": provider_preflight["preflightDigest"],
        "sentinelRepeatWaveByFamily": repeat_wave_by_family,
        "waves": wave_summaries,
        "blocks": blocks,
        "trials": trials,
    }
    value["scheduleDigest"] = canonical_digest(value)
    return value
