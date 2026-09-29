from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "task_bank_r2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pilot_r2_task_bank", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inferential_bank_has_24_unique_qa_qualified_tasks() -> None:
    m = load_module()
    manifest = m.build_manifest(cohort="inferential")
    assert manifest["taskCount"] == 24
    assert len({row["taskId"] for row in manifest["tasks"]}) == 24
    assert len({row["taskDigest"] for row in manifest["tasks"]}) == 24
    assert all(row["qaStanding"] == "PASS" for row in manifest["tasks"])
    for family in ("repository_repair", "edit_addressing", "edit_multiregion"):
        rows = [row for row in manifest["tasks"] if row["family"] == family]
        assert len(rows) == 8
        assert sum(row["sentinel"] for row in rows) == 1


def test_calibration_bank_is_disjoint_from_inferential_bank() -> None:
    m = load_module()
    inferential = m.build_manifest(cohort="inferential")
    calibration = m.build_manifest(cohort="calibration")
    assert calibration["taskCount"] == 6
    infer_ids = {row["taskId"] for row in inferential["tasks"]}
    cal_ids = {row["taskId"] for row in calibration["tasks"]}
    infer_digests = {row["taskDigest"] for row in inferential["tasks"]}
    cal_digests = {row["taskDigest"] for row in calibration["tasks"]}
    assert infer_ids.isdisjoint(cal_ids)
    assert infer_digests.isdisjoint(cal_digests)


def test_materialized_manifest_is_accepted_by_design_compiler(tmp_path: Path) -> None:
    m = load_module()
    design = m.load_design()
    manifest = m.materialize_bank(tmp_path / "inferential", cohort="inferential")
    design.validate_task_manifest(manifest)
    schedule = design.compile_schedule(manifest, design.synthetic_provider_preflight())
    assert schedule["totalTrialCount"] == 108
    assert schedule["independentTaskBlockCount"] == 24


def test_canonical_bundles_freeze_exact_task_bytes_and_qa() -> None:
    m = load_module()
    inferential = m.build_bundle(cohort="inferential")
    calibration = m.build_bundle(cohort="calibration")
    assert inferential["manifest"]["taskCount"] == 24
    assert calibration["manifest"]["taskCount"] == 6
    assert len(inferential["tasks"]) == 24
    assert len(calibration["tasks"]) == 6
    assert all(row["qa"]["standing"] == "PASS" for row in inferential["tasks"] + calibration["tasks"])
    assert inferential["bundleDigest"] != calibration["bundleDigest"]
    infer_task_digests = {row["definition"]["taskDigest"] for row in inferential["tasks"]}
    cal_task_digests = {row["definition"]["taskDigest"] for row in calibration["tasks"]}
    assert infer_task_digests.isdisjoint(cal_task_digests)
