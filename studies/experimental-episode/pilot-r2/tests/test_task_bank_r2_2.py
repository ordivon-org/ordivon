from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE = HERE.parent / "task_bank_r2_2.py"
spec = importlib.util.spec_from_file_location("task_bank_r2_2", MODULE)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def test_r22_bank_counts_and_disjointness():
    cal = m.generate_bank(cohort="calibration")
    inf = m.generate_bank(cohort="inferential")
    assert len(cal) == 6 and len(inf) == 24
    assert {t.task_id for t in cal}.isdisjoint({t.task_id for t in inf})
    assert {t.definition()["taskDigest"] for t in cal}.isdisjoint(
        {t.definition()["taskDigest"] for t in inf}
    )
    for family in m.FAMILIES:
        assert (
            sum(t.family == family for t in cal) == 2
            and sum(t.family == family for t in inf) == 8
        )


def test_r22_structural_pressure_invariants():
    for cohort in ("calibration", "inferential"):
        for task in m.generate_bank(cohort=cohort):
            m.validate_structure(task)


def test_r22_all_tasks_pass_deterministic_qa():
    for cohort in ("calibration", "inferential"):
        for task in m.generate_bank(cohort=cohort):
            assert m.verify_task(task)["standing"] == "PASS_TASK_QA"


def test_r22_bundle_is_deterministic():
    first = m.build_bundle(cohort="calibration")
    second = m.build_bundle(cohort="calibration")
    assert first == second and first["bundleDigest"] == second["bundleDigest"]
