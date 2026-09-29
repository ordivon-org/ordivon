from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "design_r2.py"
MODULE = ROOT / "design_r2_1.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calibration_manifest():
    base = load(BASE, "r2_base_cal_manifest")
    tasks = []
    for family in base.FAMILIES:
        for index in range(2):
            tasks.append({"taskId": f"CAL-{family}-{index}", "family": family, "qaStanding": "PASS"})
    value = {"kind": "ordivon.experimental-task-bank-manifest", "cohort": "calibration", "tasks": tasks}
    value["manifestDigest"] = base.canonical_digest(value)
    return value


def test_calibration_schedule_has_two_family_balanced_rounds_and_atomic_blocks() -> None:
    m = load(MODULE, "r2_1_design_cal")
    schedule = m.compile_balanced_calibration_schedule(calibration_manifest())
    assert schedule["trialCount"] == 24
    assert schedule["taskBlockCount"] == 6
    assert schedule["atomicExecutionUnit"] == "complete-four-cell-task-block"
    families = [block["taskFamily"] for block in schedule["blocks"]]
    base = load(BASE, "r2_base_cal_family")
    assert set(families[:3]) == set(base.FAMILIES)
    assert set(families[3:]) == set(base.FAMILIES)
    for block in schedule["blocks"]:
        rows = [row for row in schedule["trials"] if row["blockId"] == block["blockId"]]
        assert len(rows) == 4
        assert len({(row["model"], row["codec"]) for row in rows}) == 4


def test_inferential_schedule_has_four_balanced_waves_and_dispersed_sentinels() -> None:
    base = load(BASE, "r2_base_wave")
    m = load(MODULE, "r2_1_design_wave")
    schedule = m.compile_balanced_inferential_schedule(base.synthetic_task_manifest(), base.synthetic_provider_preflight())
    assert schedule["totalTrialCount"] == 108
    assert schedule["coreTrialCount"] == 96
    assert schedule["nestedSentinelTrialCount"] == 12
    assert len(schedule["waves"]) == 4
    core = [block for block in schedule["blocks"] if block["providerReplicate"] == 1]
    repeats = [block for block in schedule["blocks"] if block["providerReplicate"] == 2]
    assert len(core) == 24
    assert len(repeats) == 3
    for wave in range(1, 5):
        wave_core = [block for block in core if block["wave"] == wave]
        assert len(wave_core) == 6
        assert Counter(block["taskFamily"] for block in wave_core) == Counter({family: 2 for family in base.FAMILIES})
    assert {block["wave"] for block in repeats} == {2, 3, 4}
    assert {block["taskFamily"] for block in repeats} == set(base.FAMILIES)
    sentinel_core = [block for block in core if any(row["sentinel"] and row["blockId"] == block["blockId"] for row in schedule["trials"])]
    assert len(sentinel_core) == 3
    assert {block["wave"] for block in sentinel_core} == {1}
    for repeat in repeats:
        matching_core = next(block for block in sentinel_core if block["taskId"] == repeat["taskId"])
        assert repeat["wave"] > matching_core["wave"]
