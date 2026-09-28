from __future__ import annotations

import importlib.util
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve()
RUNNER = HERE.parents[1] / "run_factorial_pilot_r1.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("oef_pilot_r1", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_schedule_is_balanced_unique_and_seeded() -> None:
    module = load_runner()
    first = module.build_schedule()
    second = module.build_schedule()
    assert first == second
    assert len(first["trials"]) == 12
    assert len({row["trialId"] for row in first["trials"]}) == 12
    cells = {(row["taskId"], row["model"], row["codec"]) for row in first["trials"]}
    assert len(cells) == 12
    for task in module.TASK_IDS:
        assert sum(row["taskId"] == task for row in first["trials"]) == 4
    for model in module.MODELS:
        assert sum(row["model"] == model for row in first["trials"]) == 6
    for codec in module.CODECS:
        assert sum(row["codec"] == codec for row in first["trials"]) == 6


def test_preregistration_contracts_validate_without_provider_calls() -> None:
    module = load_runner()
    prereg = module.build_preregistration()
    assert prereg["design"]["randomness"]["assignmentSeedPolicy"] == "fixed"
    assert prereg["design"]["randomness"]["executionRandomnessPolicy"] == "provider-owned"
    assert prereg["primaryMetricId"] == "metric:hidden-pass"
    assert len(prereg["schedule"]["trials"]) == 12
    assert len(prereg["metricSpecs"]) == 6
    for name in (
        "experimental-design-contract-r1.schema.json",
        "experimental-intervention-contract-r1.schema.json",
        "experimental-fork-manifest-r1.schema.json",
    ):
        Draft202012Validator.check_schema(module.schema(name))


def test_preregistration_is_byte_semantically_stable_before_live_execution() -> None:
    module = load_runner()
    first = module.build_preregistration()
    second = module.build_preregistration(source_revision=first["gitRevision"])
    assert first == second
    assert first["preregistrationDigest"] == second["preregistrationDigest"]


def test_frozen_preregistration_reopens_without_rebinding_head(tmp_path) -> None:
    module = load_runner()
    first = module.resolve_preregistration(tmp_path)
    second = module.resolve_preregistration(tmp_path)
    assert first == second
    assert first["pilotRunnerBinding"]["digest"] == module.file_digest(module.Path(module.__file__))
