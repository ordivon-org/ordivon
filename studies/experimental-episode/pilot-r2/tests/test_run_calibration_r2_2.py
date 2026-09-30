from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATH = HERE.parent / "run_calibration_r2_2.py"
spec = importlib.util.spec_from_file_location("run_calibration_r2_2", PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def test_r22_prereg_binds_rejected_predecessor_and_both_new_banks():
    v = m.build_preregistration()
    assert v["designRevision"] == "r2.2"
    assert (
        v["supersedesAfterRejectedCalibration"]["standing"]
        == "REJECT_TASK_BANK_DIFFICULTY"
    )
    assert v["taskBankRepairSpecBinding"]["repairSpecDigest"].startswith("sha256:")
    assert v["taskBundleBinding"]["bundleDigest"].startswith("sha256:")
    assert v["inferentialTaskBundleBinding"]["bundleDigest"].startswith("sha256:")
    assert v["fullGate"]["maximumSuccessesInclusive"] == 20
    assert v["schedule"]["trialCount"] == 24
    assert v["plannedInferentialSchedule"]["totalTrialCount"] == 108


def test_r22_prereg_preserves_treatments_and_revision_scoped_ids():
    v = m.build_preregistration()
    assert all("r2.2" in r["trialId"] for r in v["schedule"]["trials"])
    assert {r["model"] for r in v["schedule"]["trials"]} == {
        "deepseek-flash",
        "deepseek-v4-pro",
    }
    assert {r["codec"] for r in v["schedule"]["trials"]} == {
        "exact-replacement-v1",
        "anchored-line-v1",
    }
