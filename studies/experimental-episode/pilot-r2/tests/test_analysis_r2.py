from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis_r2.py"
DESIGN = ROOT / "design_r2.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calibration_records(*, successes: int, mixed: bool = True):
    d = load(DESIGN, "r2_design_for_cal")
    rows = []
    index = 0
    protected_mixed_tasks = set()
    for family_index, family in enumerate(d.FAMILIES):
        for local in range(2):
            task_id = f"CAL-{family}-{local}"
            is_mixed = mixed and local == 0 and family_index < 2
            if is_mixed:
                protected_mixed_tasks.add(task_id)
            cell_number = 0
            for model in d.MODELS:
                for codec in d.CODECS:
                    index += 1
                    cell_number += 1
                    outcome = is_mixed and cell_number <= 2
                    rows.append({"trialId": f"cal-{index}", "taskId": task_id, "taskFamily": family, "model": model, "codec": codec, "hiddenPassed": outcome})
    current = sum(int(row["hiddenPassed"]) for row in rows)
    if not mixed:
        for row in rows:
            row["hiddenPassed"] = int(row["trialId"].split("-")[-1]) <= successes
        return rows
    if successes < current:
        raise ValueError("mixed fixture requires at least four successes")
    for row in rows:
        if current >= successes:
            break
        if row["taskId"] not in protected_mixed_tasks and not row["hiddenPassed"]:
            row["hiddenPassed"] = True
            current += 1
    assert current == successes
    return rows


def inferential_records():
    d = load(DESIGN, "r2_design_for_bootstrap")
    schedule = d.compile_schedule(d.synthetic_task_manifest(), d.synthetic_provider_preflight())
    rows = []
    for trial in schedule["trials"]:
        outcome = trial["codec"] == d.CODECS[0]
        rows.append(dict(trial, hiddenPassed=outcome))
    return rows


def test_calibration_gate_passes_non_ceiling_mixed_bank() -> None:
    a = load(ANALYSIS, "r2_analysis_pass")
    gate = a.calibration_gate(calibration_records(successes=12, mixed=True))
    assert gate["standing"] == "PASS_CALIBRATION_DIFFICULTY"
    assert gate["successRate"] == {"numerator": 1, "denominator": 2}
    assert gate["mixedTaskCount"] >= 2
    assert gate["mixedFamilyCount"] >= 2


def test_calibration_gate_rejects_ceiling_even_with_complete_cells() -> None:
    a = load(ANALYSIS, "r2_analysis_ceiling")
    gate = a.calibration_gate(calibration_records(successes=24, mixed=False))
    assert gate["standing"] == "REJECT_TASK_BANK_DIFFICULTY"
    assert gate["successCount"] == 24


def test_task_block_bootstrap_is_deterministic_exact_and_excludes_nested_repeats() -> None:
    a = load(ANALYSIS, "r2_analysis_bootstrap")
    first = a.task_block_bootstrap(inferential_records(), "hiddenPassed", replicates=500)
    second = a.task_block_bootstrap(inferential_records(), "hiddenPassed", replicates=500)
    assert first["bootstrapDigest"] == second["bootstrapDigest"]
    assert first["independentTaskBlockCount"] == 24
    assert first["nestedProviderReplicatesIncluded"] is False
    harness = first["estimates"]["harnessMarginalDifferenceExactMinusAnchored"]
    assert harness["pointEstimate"] == {"numerator": 1, "denominator": 1}
    assert harness["percentile95"]["lower"] == {"numerator": 1, "denominator": 1}
    assert harness["percentile95"]["upper"] == {"numerator": 1, "denominator": 1}
    model = first["estimates"]["modelMarginalDifferenceProMinusFlash"]
    assert model["pointEstimate"] == {"numerator": 0, "denominator": 1}
