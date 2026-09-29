from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
PILOT_ROOT = HERE.parents[1]
RUNNER = PILOT_ROOT / "run_calibration_r2.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("experimental_fabric_r2_calibration_test", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_calibration_preregistration_binds_frozen_inputs_and_24_cells() -> None:
    module = load_runner()
    value = module.build_preregistration()
    assert value["kind"] == "ordivon.experimental-calibration-preregistration"
    assert value["schedule"]["trialCount"] == 24
    assert value["schedule"]["taskCount"] == 6
    assert value["resourceEnvelope"]["maxTotalTokens"] == 64_000
    assert value["providerIdentityPreflightBinding"]["effectiveIdentityMap"] == {"deepseek-flash": "deepseek-flash", "deepseek-v4-pro": "deepseek-v4-pro"}
    assert value["preregistrationDigest"] == module.canonical_digest({key: item for key, item in value.items() if key != "preregistrationDigest"})


def test_uncertain_started_trial_fails_before_loading_provider_secret(tmp_path: Path, monkeypatch) -> None:
    module = load_runner()
    prereg = module.build_preregistration()
    trial = prereg["schedule"]["trials"][0]
    module.journal_append(tmp_path / "journal.jsonl", {"event": "trial_started", "trialId": trial["trialId"]})
    def provider_secret_must_not_load(*args, **kwargs):
        raise AssertionError("Provider secret loaded before reconciliation fence")
    monkeypatch.setattr(module.DeepSeekSettings, "from_secret_file", provider_secret_must_not_load)
    with pytest.raises(RuntimeError, match="require reconciliation before dispatch"):
        module.execute_trials(tmp_path, prereg)


def test_materialized_generated_task_preserves_hidden_verifier_semantics(tmp_path: Path) -> None:
    module = load_runner()
    bundle = module.verify_bundle()
    live = module.load_live_runner()
    payload = bundle["tasks"][0]
    spec = module.materialize_task(payload, live, tmp_path)
    baseline = (spec.fixture / spec.target_path).read_text()
    assert live.verify(baseline, spec)["hiddenPassed"] is False
    assert live.verify(payload["oracleSource"], spec) == {"visiblePassed": True, "hiddenPassed": True}


def test_provider_identity_drift_fails_closed() -> None:
    module = load_runner()
    preflight = module.verify_preflight()
    good = {"usage": {"requestedModelId": "deepseek-v4-pro", "effectiveModelIds": ["deepseek-v4-pro"], "providerUsage": [{"requestedModelId": "deepseek-v4-pro", "effectiveModelId": "deepseek-v4-pro", "providerModel": "deepseek-v4-pro", "systemFingerprint": "fixture"}]}}
    assert module.assess_provider_identity(good, "deepseek-v4-pro", preflight)["standing"] == "PASS_EFFECTIVE_IDENTITY"
    drifted = json.loads(json.dumps(good))
    drifted["usage"]["effectiveModelIds"] = ["deepseek-flash"]
    drifted["usage"]["providerUsage"][0]["effectiveModelId"] = "deepseek-flash"
    drifted["usage"]["providerUsage"][0]["providerModel"] = "deepseek-flash"
    assert module.assess_provider_identity(drifted, "deepseek-v4-pro", preflight)["standing"] == "FAIL_EFFECTIVE_IDENTITY_DRIFT"
