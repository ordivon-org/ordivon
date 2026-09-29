from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve()
MODULE = HERE.parents[1] / "prospective_r1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("lego_r21_prospective", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_task_banks_are_disjoint_and_balanced() -> None:
    m = load_module()
    cal = m.build_bank("calibration")
    inf = m.build_bank("inferential")
    assert cal["taskCount"] == 12
    assert inf["taskCount"] == 24
    cal_ids = {row["visible"]["taskId"] for row in cal["tasks"]}
    inf_ids = {row["visible"]["taskId"] for row in inf["tasks"]}
    assert cal_ids.isdisjoint(inf_ids)
    for bank, count in ((cal, 2), (inf, 4)):
        families = {family: 0 for family in m.FAMILIES}
        for row in bank["tasks"]:
            families[row["visible"]["family"]] += 1
            option_ids = {item["id"] for item in row["visible"]["options"]}
            assert row["goldChoice"] in option_ids
            assert "goldChoice" not in row["visible"]
            assert "goldDigest" not in row["visible"]
        assert set(families.values()) == {count}


def test_schedule_is_paired_and_reproducible() -> None:
    m = load_module()
    bank = m.build_bank("calibration")
    a = m.build_schedule(bank, seed=m.CALIBRATION_SEED)
    b = m.build_schedule(bank, seed=m.CALIBRATION_SEED)
    assert a == b
    assert a["trialCount"] == 24
    by_task = {}
    for row in a["trials"]:
        by_task.setdefault(row["taskId"], set()).add(row["arm"])
    assert len(by_task) == 12
    assert all(arms == set(m.ARMS) for arms in by_task.values())


def test_choice_parser_is_fail_closed() -> None:
    m = load_module()
    assert m.parse_choice('{"choice":"OPT_2"}', {"OPT_1", "OPT_2"}) == (True, "OPT_2")
    assert m.parse_choice('```json\n{"choice":"OPT_1"}\n```', {"OPT_1"}) == (True, "OPT_1")
    assert m.parse_choice('{"choice":"OPT_9"}', {"OPT_1"}) == (False, None)
    assert m.parse_choice('{"choice":"OPT_1","reason":"x"}', {"OPT_1"}) == (False, None)
    assert m.parse_choice('not json', {"OPT_1"}) == (False, None)


def test_calibration_gate_rejects_floor_ceiling_and_accepts_mixed() -> None:
    m = load_module()
    bank = m.build_bank("calibration")
    schedule = m.build_schedule(bank, seed=m.CALIBRATION_SEED)
    all_true = [{**row, "kind": "ordivon.recursive-lego-prospective-trial", "exactChoiceCorrect": True} for row in schedule["trials"]]
    assert m.calibration_gate(all_true)["standing"] == "REJECT_TASK_BANK_DIFFICULTY"
    mixed = []
    for row in schedule["trials"]:
        # Arm-sensitive synthetic fixture yields one success per task and therefore 12/24 successes.
        mixed.append({**row, "kind": "ordivon.recursive-lego-prospective-trial", "exactChoiceCorrect": row["arm"] == "r2_1"})
    gate = m.calibration_gate(mixed)
    assert gate["standing"] == "PASS_CALIBRATION_DIFFICULTY"
    assert gate["successCount"] == 12
    assert gate["mixedTaskCount"] == 12
    assert gate["mixedFamilyCount"] == 6


def test_mcnemar_analysis_uses_task_pairs() -> None:
    m = load_module()
    bank = m.build_bank("inferential")
    schedule = m.build_schedule(bank, seed=m.INFERENTIAL_SEED)
    rows = []
    for row in schedule["trials"]:
        rows.append({**row, "trialId": row["trialId"], "exactChoiceCorrect": row["arm"] == "r2_1"})
    analysis = m.analyze_inferential(rows)
    assert analysis["independentTaskBlockCount"] == 24
    assert analysis["discordant"]["r2_1OnlyCorrect"] == 24
    assert analysis["discordant"]["controlOnlyCorrect"] == 0
    assert analysis["r2_1MinusControlAccuracyDifference"] == {"numerator": 1, "denominator": 1}
    p = analysis["mcnemarExactTwoSidedP"]
    assert p["numerator"] * 1_000_000 < p["denominator"]
