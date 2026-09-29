from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "design_r2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pilot_r2_design", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_schedule_has_24_independent_blocks_and_12_nested_sentinel_runs() -> None:
    m = load_module()
    manifest = m.synthetic_task_manifest()
    preflight = m.synthetic_provider_preflight()
    schedule = m.compile_schedule(manifest, preflight)
    assert schedule["independentTaskBlockCount"] == 24
    assert schedule["coreTrialCount"] == 96
    assert schedule["nestedSentinelTrialCount"] == 12
    assert schedule["totalTrialCount"] == 108
    core = [row for row in schedule["trials"] if row["providerReplicate"] == 1]
    nested = [row for row in schedule["trials"] if row["providerReplicate"] == 2]
    assert len(core) == 96
    assert len(nested) == 12
    assert len({row["independentTaskBlock"] for row in schedule["trials"]}) == 24
    for family in m.FAMILIES:
        assert sum(task["family"] == family for task in manifest["tasks"]) == 8
        assert sum(task["family"] == family and task["sentinel"] for task in manifest["tasks"]) == 1
    for model in m.MODELS:
        for codec in m.CODECS:
            assert sum(row["model"] == model and row["codec"] == codec for row in schedule["trials"]) == 27


def test_schedule_is_seeded_and_reproducible() -> None:
    m = load_module()
    manifest = m.synthetic_task_manifest()
    preflight = m.synthetic_provider_preflight()
    first = m.compile_schedule(manifest, preflight, seed=20260929)
    second = m.compile_schedule(manifest, preflight, seed=20260929)
    other = m.compile_schedule(manifest, preflight, seed=20260930)
    assert first["scheduleDigest"] == second["scheduleDigest"]
    assert first["trials"] == second["trials"]
    assert first["scheduleDigest"] != other["scheduleDigest"]


def test_provider_identity_alias_collapse_fails_closed() -> None:
    m = load_module()
    manifest = m.synthetic_task_manifest()
    collapsed = m.synthetic_provider_preflight(collapsed=True)
    with pytest.raises(ValueError, match="collapsed"):
        m.compile_schedule(manifest, collapsed)


def test_task_manifest_rejects_pseudoreplication_by_duplicate_task_digest() -> None:
    m = load_module()
    manifest = m.synthetic_task_manifest()
    manifest["tasks"][1]["taskDigest"] = manifest["tasks"][0]["taskDigest"]
    with pytest.raises(ValueError, match="duplicate task payload digest"):
        m.validate_task_manifest(manifest)


def test_task_block_contrasts_exclude_nested_provider_replicates() -> None:
    m = load_module()
    schedule = m.compile_schedule(m.synthetic_task_manifest(), m.synthetic_provider_preflight())
    records = []
    for trial in schedule["trials"]:
        row = dict(trial)
        row["hiddenPassed"] = trial["codec"] == "exact-replacement-v1"
        records.append(row)
    contrasts = m.task_block_contrasts(records, "hiddenPassed")
    assert contrasts["independentTaskBlockCount"] == 24
    assert contrasts["modelMarginalDifferenceProMinusFlash"] == {"numerator": 0, "denominator": 1}
    assert contrasts["harnessMarginalDifferenceExactMinusAnchored"] == {"numerator": 1, "denominator": 1}
    assert contrasts["modelByHarnessDifferenceInDifferences"] == {"numerator": 0, "denominator": 1}
    assert len(contrasts["perTask"]) == 24


def test_missing_core_cell_fails_closed() -> None:
    m = load_module()
    schedule = m.compile_schedule(m.synthetic_task_manifest(), m.synthetic_provider_preflight())
    records = [dict(row, hiddenPassed=True) for row in schedule["trials"]]
    first_core_index = next(index for index, row in enumerate(records) if row["providerReplicate"] == 1)
    del records[first_core_index]
    with pytest.raises(ValueError, match="incomplete Model×Harness cells"):
        m.task_block_contrasts(records, "hiddenPassed")
