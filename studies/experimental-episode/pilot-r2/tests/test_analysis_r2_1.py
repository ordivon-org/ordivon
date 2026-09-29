from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_ANALYSIS = ROOT / "analysis_r2.py"
BASE_DESIGN = ROOT / "design_r2.py"
DESIGN = ROOT / "design_r2_1.py"
ANALYSIS = ROOT / "analysis_r2_1.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calibration_manifest():
    base = load(BASE_DESIGN, "r2_base_analysis_cal_manifest")
    tasks = []
    for family in base.FAMILIES:
        for index in range(2):
            tasks.append({"taskId": f"CAL-{family}-{index}", "family": family, "qaStanding": "PASS"})
    value = {"kind": "ordivon.experimental-task-bank-manifest", "cohort": "calibration", "tasks": tasks}
    value["manifestDigest"] = base.canonical_digest(value)
    return value


def concrete_records(schedule, block_counts):
    rows = []
    for block, success_count in zip(schedule["blocks"], block_counts, strict=True):
        trials = [row for row in schedule["trials"] if row["blockId"] == block["blockId"]]
        for index, trial in enumerate(trials):
            rows.append({**trial, "hiddenPassed": index < success_count})
    return rows


def test_decision_frontier_can_pass_after_two_distinct_family_blocks() -> None:
    d = load(DESIGN, "r2_1_frontier_design")
    a = load(ANALYSIS, "r2_1_frontier_analysis")
    schedule = d.compile_balanced_calibration_schedule(calibration_manifest())
    records = concrete_records(schedule, [1, 3, 0, 0, 0, 0])[:8]
    certificate = a.decision_frontier_certificate(records, schedule)
    assert certificate["observedBlockCount"] == 2
    assert certificate["observedTrialCount"] == 8
    assert certificate["standing"] == "DECISIVE_PASS_CALIBRATION_DIFFICULTY"
    assert certificate["possibleFinalStandings"] == ["PASS_CALIBRATION_DIFFICULTY"]


def test_decision_frontier_preserves_original_full_gate_for_all_block_count_states() -> None:
    d = load(DESIGN, "r2_1_bridge_design")
    a = load(ANALYSIS, "r2_1_bridge_analysis")
    old = load(BASE_ANALYSIS, "r2_1_bridge_old_analysis")
    schedule = d.compile_balanced_calibration_schedule(calibration_manifest())
    families = [block["taskFamily"] for block in schedule["blocks"]]
    for counts in itertools.product(range(5), repeat=6):
        rows = concrete_records(schedule, list(counts))
        old_gate = old.calibration_gate(rows)
        assert a._full_standing_from_block_counts(list(counts), families) == old_gate["standing"]


def inferential_records():
    base = load(BASE_DESIGN, "r2_1_boot_base")
    design = load(DESIGN, "r2_1_boot_design")
    schedule = design.compile_balanced_inferential_schedule(base.synthetic_task_manifest(), base.synthetic_provider_preflight())
    rows = []
    for trial in schedule["trials"]:
        family_bias = trial["taskFamily"] == base.FAMILIES[0]
        outcome = trial["codec"] == base.CODECS[0] if not family_bias else trial["model"] == base.MODELS[1]
        rows.append({**trial, "hiddenPassed": outcome})
    return rows


def test_family_stratified_bootstrap_is_exact_deterministic_and_preserves_family_counts() -> None:
    a = load(ANALYSIS, "r2_1_boot_analysis")
    first = a.family_stratified_task_block_bootstrap(inferential_records(), "hiddenPassed", replicates=500)
    second = a.family_stratified_task_block_bootstrap(inferential_records(), "hiddenPassed", replicates=500)
    assert first["bootstrapDigest"] == second["bootstrapDigest"]
    assert first["familyTaskCounts"] == {"repository_repair": 8, "edit_addressing": 8, "edit_multiregion": 8}
    assert first["independentTaskBlockCount"] == 24
    assert first["nestedProviderReplicatesIncluded"] is False
    for estimate in first["estimates"].values():
        assert set(estimate["familyPointEstimates"]) == {"repository_repair", "edit_addressing", "edit_multiregion"}
        assert isinstance(estimate["pointEstimate"]["numerator"], int)
        assert isinstance(estimate["pointEstimate"]["denominator"], int)
