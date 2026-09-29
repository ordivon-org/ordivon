from __future__ import annotations

import hashlib
import importlib.util
import itertools
import math
from fractions import Fraction
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
BASE_ANALYSIS_PATH = HERE.with_name("analysis_r2.py")
BASE_DESIGN_PATH = HERE.with_name("design_r2.py")
DESIGN_R2_1_PATH = HERE.with_name("design_r2_1.py")
STRATIFIED_BOOTSTRAP_SEED = 2026092905
STRATIFIED_BOOTSTRAP_REPLICATES = 10_000


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_base_analysis():
    return _load(BASE_ANALYSIS_PATH, "pilot_r2_base_analysis_r2_1")


def load_base_design():
    return _load(BASE_DESIGN_PATH, "pilot_r2_base_design_analysis_r2_1")


def load_design_r2_1():
    return _load(DESIGN_R2_1_PATH, "pilot_r2_successor_design_analysis_r2_1")


def _full_standing_from_block_counts(counts: list[int], families: list[str]) -> str:
    base = load_base_analysis()
    if len(counts) != 6 or len(families) != 6:
        raise ValueError("full calibration summary requires six task blocks")
    if any(not isinstance(value, int) or value < 0 or value > 4 for value in counts):
        raise ValueError("task-block success count must be an integer in [0,4]")
    successes = sum(counts)
    mixed_indices = [index for index, value in enumerate(counts) if 0 < value < 4]
    mixed_families = {families[index] for index in mixed_indices}
    range_pass = base.CALIBRATION_MIN_SUCCESSES <= successes <= base.CALIBRATION_MAX_SUCCESSES
    mixed_pass = (
        len(mixed_indices) >= base.CALIBRATION_MIN_MIXED_TASKS
        and len(mixed_families) >= base.CALIBRATION_MIN_MIXED_FAMILIES
    )
    return "PASS_CALIBRATION_DIFFICULTY" if range_pass and mixed_pass else "REJECT_TASK_BANK_DIFFICULTY"


def decision_frontier_from_block_summaries(
    observed_counts: list[int], families: list[str]
) -> dict[str, Any]:
    design = load_base_design()
    if len(families) != 6:
        raise ValueError("decision frontier requires the full six-block family schedule")
    if not 0 <= len(observed_counts) <= 6:
        raise ValueError("observed block count outside calibration schedule")
    if any(value < 0 or value > 4 for value in observed_counts):
        raise ValueError("observed task-block success count outside [0,4]")
    remaining = 6 - len(observed_counts)
    possible = {
        _full_standing_from_block_counts(observed_counts + list(completion), families)
        for completion in itertools.product(range(5), repeat=remaining)
    }
    if possible == {"PASS_CALIBRATION_DIFFICULTY"}:
        frontier = "DECISIVE_PASS_CALIBRATION_DIFFICULTY"
    elif possible == {"REJECT_TASK_BANK_DIFFICULTY"}:
        frontier = "DECISIVE_REJECT_TASK_BANK_DIFFICULTY"
    else:
        frontier = "UNDECIDED"
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-calibration-decision-frontier-summary",
        "experimentId": design.EXPERIMENT_ID,
        "observedBlockCount": len(observed_counts),
        "remainingBlockCount": remaining,
        "observedSuccessCountByBlock": observed_counts,
        "fullScheduleFamilies": families,
        "possibleFinalStandings": sorted(possible),
        "standing": frontier,
        "bridge": "A decisive standing is emitted only when every legal completion of unobserved complete task blocks yields the same original full 24-cell calibration-gate standing.",
    }
    value["certificateDigest"] = design.canonical_digest(value)
    return value


def decision_frontier_certificate(records: list[dict[str, Any]], schedule: dict[str, Any]) -> dict[str, Any]:
    design = load_base_design()
    blocks = schedule.get("blocks")
    if not isinstance(blocks, list) or len(blocks) != 6:
        raise ValueError("R2.1 decision frontier requires six declared schedule blocks")
    by_trial = {str(row["trialId"]): row for row in records}
    observed_counts: list[int] = []
    observed_task_ids: list[str] = []
    expected_observed_trials: set[str] = set()
    stopped = False
    for block in blocks:
        trial_ids = list(block["trialIds"])
        present = [trial_id in by_trial for trial_id in trial_ids]
        if any(present) and not all(present):
            raise ValueError(f"partial task block cannot enter decision frontier: {block['blockId']}")
        if all(present):
            if stopped:
                raise ValueError("observed calibration blocks must form a schedule prefix")
            expected_observed_trials.update(trial_ids)
            rows = [by_trial[trial_id] for trial_id in trial_ids]
            cells = {(row.get("model"), row.get("codec")) for row in rows}
            expected_cells = {(model, codec) for model in design.MODELS for codec in design.CODECS}
            if cells != expected_cells:
                raise ValueError(f"task block cell set differs: {block['blockId']}")
            if {row.get("taskId") for row in rows} != {block["taskId"]}:
                raise ValueError(f"task identity drift in block: {block['blockId']}")
            outcomes = [row.get("hiddenPassed") for row in rows]
            if any(not isinstance(value, bool) for value in outcomes):
                raise ValueError(f"hiddenPassed missing/non-boolean in block: {block['blockId']}")
            observed_counts.append(sum(int(value) for value in outcomes))
            observed_task_ids.append(str(block["taskId"]))
        else:
            stopped = True
    if set(by_trial) != expected_observed_trials:
        raise ValueError("records contain trials outside the completed schedule prefix")
    families = [str(block["taskFamily"]) for block in blocks]
    summary = decision_frontier_from_block_summaries(observed_counts, families)
    value = {
        **summary,
        "kind": "ordivon.experimental-calibration-decision-frontier-certificate",
        "scheduleDigest": schedule["scheduleDigest"],
        "observedTaskIds": observed_task_ids,
        "observedTrialCount": len(records),
        "unobservedTaskIds": [str(block["taskId"]) for block in blocks[len(observed_counts):]],
    }
    value.pop("certificateDigest", None)
    value["certificateDigest"] = design.canonical_digest(value)
    return value


def _fraction(value: dict[str, int]) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


def _nearest_rank(values: list[Fraction], numerator: int, denominator: int) -> Fraction:
    if not values:
        raise ValueError("cannot take quantile of empty values")
    rank = math.ceil(Fraction(numerator, denominator) * len(values))
    rank = max(1, min(rank, len(values)))
    return sorted(values)[rank - 1]


def _stratified_index(seed: int, family: str, replicate: int, draw: int, n: int) -> int:
    material = f"ordivon-r2.1-family-bootstrap-v1|{seed}|{family}|{replicate}|{draw}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") % n


def family_stratified_task_block_bootstrap(
    records: list[dict[str, Any]],
    outcome_key: str,
    *,
    seed: int = STRATIFIED_BOOTSTRAP_SEED,
    replicates: int = STRATIFIED_BOOTSTRAP_REPLICATES,
) -> dict[str, Any]:
    if replicates < 100:
        raise ValueError("bootstrap replicates must be >= 100")
    base = load_base_design()
    base.validate_complete_core_cells(records)
    core = [row for row in records if row.get("providerReplicate") == 1]
    by_task_family: dict[str, str] = {}
    for row in core:
        task_id = str(row["taskId"])
        family = str(row["taskFamily"])
        prior = by_task_family.setdefault(task_id, family)
        if prior != family:
            raise ValueError(f"task family drift for {task_id}")
    contrasts = base.task_block_contrasts(records, outcome_key)
    per_task = contrasts["perTask"]
    by_family: dict[str, list[dict[str, Any]]] = {family: [] for family in base.FAMILIES}
    for row in per_task:
        family = by_task_family[row["taskId"]]
        by_family[family].append(row)
    if any(len(rows) != base.TASKS_PER_FAMILY for rows in by_family.values()):
        raise ValueError("family-stratified bootstrap requires exactly eight independent tasks per family")

    fields = {
        "modelMarginalDifferenceProMinusFlash": "modelContrast",
        "harnessMarginalDifferenceExactMinusAnchored": "harnessContrast",
        "modelByHarnessDifferenceInDifferences": "interaction",
    }
    family_points: dict[str, dict[str, Fraction]] = {}
    for family, rows in by_family.items():
        family_points[family] = {
            output: sum((_fraction(row[source]) for row in rows), Fraction(0, 1)) / len(rows)
            for output, source in fields.items()
        }
    pooled_points = {
        output: sum((family_points[family][output] for family in base.FAMILIES), Fraction(0, 1)) / len(base.FAMILIES)
        for output in fields
    }
    distributions: dict[str, list[Fraction]] = {output: [] for output in fields}
    for replicate in range(replicates):
        replicate_family_means: dict[str, dict[str, Fraction]] = {}
        for family in base.FAMILIES:
            rows = by_family[family]
            indices = [_stratified_index(seed, family, replicate, draw, len(rows)) for draw in range(len(rows))]
            replicate_family_means[family] = {
                output: sum((_fraction(rows[index][source]) for index in indices), Fraction(0, 1)) / len(rows)
                for output, source in fields.items()
            }
        for output in fields:
            distributions[output].append(
                sum((replicate_family_means[family][output] for family in base.FAMILIES), Fraction(0, 1))
                / len(base.FAMILIES)
            )

    estimates = {
        output: {
            "pointEstimate": base.rational(pooled_points[output]),
            "percentile95": {
                "lower": base.rational(_nearest_rank(values, 1, 40)),
                "upper": base.rational(_nearest_rank(values, 39, 40)),
            },
            "familyPointEstimates": {
                family: base.rational(family_points[family][output]) for family in base.FAMILIES
            },
        }
        for output, values in distributions.items()
    }
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-family-stratified-task-block-bootstrap",
        "experimentId": base.EXPERIMENT_ID,
        "outcome": outcome_key,
        "estimand": "equal-weight mean of the three frozen QA-qualified task-family mean contrasts",
        "independentTaskBlockCount": base.INDEPENDENT_TASK_BLOCKS,
        "familyTaskCounts": {family: len(by_family[family]) for family in base.FAMILIES},
        "replicates": replicates,
        "seed": seed,
        "resamplingAlgorithm": "sha256-index-v1-with-replacement-within-each-frozen-task-family",
        "interval": "nearest-rank-percentile-95",
        "estimates": estimates,
        "nestedProviderReplicatesIncluded": False,
        "nonClaims": [
            "The bootstrap preserves the frozen 8/8/8 family composition and does not create a broader task population than the declared three-family estimand.",
            "Nested Provider repeats remain stochasticity/time-sensitive diagnostics and do not increase independent n.",
            "No post-hoc observed power or p-value is derived from this bootstrap artifact.",
        ],
    }
    value["bootstrapDigest"] = base.canonical_digest(value)
    return value
