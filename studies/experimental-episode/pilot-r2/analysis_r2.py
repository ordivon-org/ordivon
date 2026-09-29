from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import random
from fractions import Fraction
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
DESIGN_PATH = HERE.with_name("design_r2.py")
CALIBRATION_SEED = 2026092901
BOOTSTRAP_SEED = 2026092902
BOOTSTRAP_REPLICATES = 10_000
CALIBRATION_MIN_SUCCESSES = 4
CALIBRATION_MAX_SUCCESSES = 20
CALIBRATION_MIN_MIXED_TASKS = 2
CALIBRATION_MIN_MIXED_FAMILIES = 2


def load_design():
    spec = importlib.util.spec_from_file_location("pilot_r2_design_analysis", DESIGN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load R2 design: {DESIGN_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fraction(value: dict[str, int]) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def compile_calibration_schedule(manifest: dict[str, Any], *, seed: int = CALIBRATION_SEED) -> dict[str, Any]:
    design = load_design()
    if manifest.get("kind") != "ordivon.experimental-task-bank-manifest" or manifest.get("cohort") != "calibration":
        raise ValueError("calibration schedule requires calibration task-bank manifest")
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 6:
        raise ValueError("R2 calibration requires exactly six disjoint tasks")
    family_counts = {family: 0 for family in design.FAMILIES}
    ids = set()
    for task in tasks:
        if not isinstance(task, dict) or task.get("qaStanding") != "PASS":
            raise ValueError("all calibration tasks must have PASS QA")
        task_id = task.get("taskId")
        family = task.get("family")
        if not isinstance(task_id, str) or task_id in ids:
            raise ValueError("calibration task IDs must be unique")
        if family not in family_counts:
            raise ValueError(f"unknown calibration family: {family}")
        ids.add(task_id)
        family_counts[family] += 1
    if any(count != 2 for count in family_counts.values()):
        raise ValueError(f"calibration requires two tasks per family: {family_counts}")

    rng = random.Random(seed)
    task_rows = list(tasks)
    rng.shuffle(task_rows)
    trials = []
    ordinal = 0
    for task in task_rows:
        cells = [(model, codec) for model in design.MODELS for codec in design.CODECS]
        rng.shuffle(cells)
        for model, codec in cells:
            ordinal += 1
            trials.append(
                {
                    "trialId": f"trial:r2:cal:{ordinal:02d}",
                    "ordinal": ordinal,
                    "taskId": task["taskId"],
                    "taskFamily": task["family"],
                    "model": model,
                    "codec": codec,
                    "providerReplicate": 1,
                }
            )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-schedule",
        "experimentId": design.EXPERIMENT_ID,
        "assignmentSeed": seed,
        "taskManifestDigest": manifest["manifestDigest"],
        "taskCount": 6,
        "trialCount": 24,
        "trials": trials,
        "nonClaims": [
            "Calibration trials are disjoint from the inferential bank and never enter inferential effect estimates.",
            "The calibration gate is a preregistered difficulty/admission heuristic, not a hypothesis test.",
        ],
    }
    value["scheduleDigest"] = design.canonical_digest(value)
    return value


def calibration_gate(records: list[dict[str, Any]]) -> dict[str, Any]:
    design = load_design()
    if len(records) != 24:
        raise ValueError(f"calibration gate requires exactly 24 completed cell records, got {len(records)}")
    expected_cells = {(model, codec) for model in design.MODELS for codec in design.CODECS}
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        task_id = row.get("taskId")
        if not isinstance(task_id, str):
            raise ValueError("calibration record lacks taskId")
        by_task.setdefault(task_id, []).append(row)
    if len(by_task) != 6:
        raise ValueError(f"calibration gate requires six task blocks, got {len(by_task)}")

    successes = 0
    mixed_tasks = []
    mixed_families = set()
    family_task_counts = {family: 0 for family in design.FAMILIES}
    for task_id, rows in sorted(by_task.items()):
        cells = {(row.get("model"), row.get("codec")) for row in rows}
        if cells != expected_cells or len(rows) != 4:
            raise ValueError(f"calibration task block has incomplete/duplicate cells: {task_id}")
        family_values = {row.get("taskFamily") for row in rows}
        if len(family_values) != 1:
            raise ValueError(f"calibration task family drift: {task_id}")
        family = next(iter(family_values))
        if family not in family_task_counts:
            raise ValueError(f"unknown calibration family: {family}")
        family_task_counts[family] += 1
        outcomes = []
        for row in rows:
            outcome = row.get("hiddenPassed")
            if not isinstance(outcome, bool):
                raise ValueError(f"calibration hiddenPassed missing/non-boolean: {row.get('trialId')}")
            outcomes.append(outcome)
            successes += int(outcome)
        if any(outcomes) and not all(outcomes):
            mixed_tasks.append(task_id)
            mixed_families.add(family)
    if any(count != 2 for count in family_task_counts.values()):
        raise ValueError(f"calibration requires two completed tasks per family: {family_task_counts}")

    range_pass = CALIBRATION_MIN_SUCCESSES <= successes <= CALIBRATION_MAX_SUCCESSES
    mixed_pass = len(mixed_tasks) >= CALIBRATION_MIN_MIXED_TASKS and len(mixed_families) >= CALIBRATION_MIN_MIXED_FAMILIES
    standing = "PASS_CALIBRATION_DIFFICULTY" if range_pass and mixed_pass else "REJECT_TASK_BANK_DIFFICULTY"
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-gate",
        "experimentId": design.EXPERIMENT_ID,
        "standing": standing,
        "trialCount": 24,
        "successCount": successes,
        "failureCount": 24 - successes,
        "successRate": design.rational(Fraction(successes, 24)),
        "admissionRange": {
            "minimumSuccessesInclusive": CALIBRATION_MIN_SUCCESSES,
            "maximumSuccessesInclusive": CALIBRATION_MAX_SUCCESSES,
        },
        "mixedTaskCount": len(mixed_tasks),
        "mixedTaskIds": mixed_tasks,
        "mixedFamilyCount": len(mixed_families),
        "mixedFamilies": sorted(mixed_families),
        "mixedRequirements": {
            "minimumMixedTasks": CALIBRATION_MIN_MIXED_TASKS,
            "minimumMixedFamilies": CALIBRATION_MIN_MIXED_FAMILIES,
        },
        "nonClaims": [
            "Calibration outcomes are used only to admit/reject task-bank difficulty and are excluded from the inferential sample.",
            "Passing this gate does not establish statistical power or treatment efficacy.",
        ],
    }
    value["gateDigest"] = design.canonical_digest(value)
    return value


def _bootstrap_index(seed: int, replicate: int, draw: int, n: int) -> int:
    material = f"ordivon-r2-task-bootstrap-v1|{seed}|{replicate}|{draw}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") % n


def _nearest_rank(values: list[Fraction], numerator: int, denominator: int) -> Fraction:
    if not values:
        raise ValueError("cannot take quantile of empty values")
    rank = math.ceil(Fraction(numerator, denominator) * len(values))
    rank = max(1, min(rank, len(values)))
    return sorted(values)[rank - 1]


def task_block_bootstrap(
    records: list[dict[str, Any]],
    outcome_key: str,
    *,
    seed: int = BOOTSTRAP_SEED,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> dict[str, Any]:
    if replicates < 100:
        raise ValueError("bootstrap replicates must be >= 100")
    design = load_design()
    contrasts = design.task_block_contrasts(records, outcome_key)
    per_task = contrasts["perTask"]
    n = contrasts["independentTaskBlockCount"]
    if n != design.INDEPENDENT_TASK_BLOCKS or len(per_task) != n:
        raise ValueError("bootstrap must operate on the 24 independent task-block contrasts")

    fields = {
        "modelMarginalDifferenceProMinusFlash": "modelContrast",
        "harnessMarginalDifferenceExactMinusAnchored": "harnessContrast",
        "modelByHarnessDifferenceInDifferences": "interaction",
    }
    by_field = {
        output: [_fraction(row[source]) for row in per_task]
        for output, source in fields.items()
    }
    distributions: dict[str, list[Fraction]] = {name: [] for name in fields}
    for replicate in range(replicates):
        indices = [_bootstrap_index(seed, replicate, draw, n) for draw in range(n)]
        for name, task_values in by_field.items():
            distributions[name].append(sum((task_values[index] for index in indices), Fraction(0, 1)) / n)

    estimates = {}
    for name, values in distributions.items():
        point = _fraction(contrasts[name])
        estimates[name] = {
            "pointEstimate": design.rational(point),
            "percentile95": {
                "lower": design.rational(_nearest_rank(values, 1, 40)),
                "upper": design.rational(_nearest_rank(values, 39, 40)),
            },
        }
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-task-block-bootstrap",
        "experimentId": design.EXPERIMENT_ID,
        "outcome": outcome_key,
        "independentTaskBlockCount": n,
        "replicates": replicates,
        "seed": seed,
        "resamplingAlgorithm": "sha256-index-v1-with-replacement-over-independent-task-blocks",
        "interval": "nearest-rank-percentile-95",
        "estimates": estimates,
        "nestedProviderReplicatesIncluded": False,
        "nonClaims": [
            "The interval summarizes variation over the frozen task-block sample under the preregistered resampling rule; it does not create a broader task population than the study defines.",
            "No post-hoc observed power or p-value is derived from this bootstrap artifact.",
        ],
    }
    value["bootstrapDigest"] = design.canonical_digest(value)
    return value


def main() -> int:
    print(json.dumps({"calibrationSeed": CALIBRATION_SEED, "bootstrapSeed": BOOTSTRAP_SEED}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
