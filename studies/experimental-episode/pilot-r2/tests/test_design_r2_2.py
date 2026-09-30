from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE.parent / file)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def test_r22_schedule_revisions_ids_without_changing_balance():
    d = load("d22", "design_r2_2.py")
    b = json.loads(
        (HERE.parent / "evidence/design/r2_2/calibration-task-bank.json").read_text()
    )
    s = d.compile_balanced_calibration_schedule(b["manifest"])
    assert (
        s["designRevision"] == "r2.2"
        and s["trialCount"] == 24
        and s["taskBlockCount"] == 6
    )
    assert all(
        "r2.2" in row["trialId"] and "r2.2" in row["blockId"] for row in s["trials"]
    )
    for block in s["blocks"]:
        rows = [r for r in s["trials"] if r["blockId"] == block["blockId"]]
        assert len(rows) == 4 and len({(r["model"], r["codec"]) for r in rows}) == 4


def test_r22_inferential_schedule_preserves_108_trial_contract():
    d = load("d22i", "design_r2_2.py")
    b = json.loads(
        (HERE.parent / "evidence/design/r2_2/inferential-task-bank.json").read_text()
    )
    pf = json.loads(
        (
            HERE.parent
            / "evidence/preflight/20260929-r1/provider-identity-preflight.json"
        ).read_text()
    )
    s = d.compile_balanced_inferential_schedule(b["manifest"], pf)
    assert (
        s["designRevision"] == "r2.2"
        and s["totalTrialCount"] == 108
        and s["coreTrialCount"] == 96
        and s["nestedSentinelTrialCount"] == 12
        and len(s["waves"]) == 4
    )
