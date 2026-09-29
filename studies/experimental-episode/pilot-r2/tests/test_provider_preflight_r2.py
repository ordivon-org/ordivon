from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "provider_preflight_r2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("r2_provider_preflight", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def probes(*, collapsed: bool = False):
    rows = []
    mapping = {
        "deepseek-flash": "deepseek-flash",
        "deepseek-v4-pro": "deepseek-flash" if collapsed else "deepseek-v4-pro",
    }
    for requested, effective in mapping.items():
        for index in (1, 2):
            rows.append(
                {
                    "requestedModelId": requested,
                    "effectiveModelId": effective,
                    "providerModel": effective,
                    "probeIndex": index,
                    "requestDigest": "sha256:" + ("a" if requested == "deepseek-flash" else "b") * 64,
                    "resultDigest": "sha256:" + ("c" if index == 1 else "d") * 64,
                    "rawResponseDigest": "sha256:" + ("e" if index == 1 else "f") * 64,
                    "modelCallId": f"call:{requested}:{index}",
                    "systemFingerprint": f"fingerprint:{effective}",
                }
            )
    return rows


def test_plan_is_four_call_non_task_preflight() -> None:
    m = load_module()
    value = m.plan()
    assert value["requestedModels"] == ["deepseek-flash", "deepseek-v4-pro"]
    assert value["probesPerModel"] == 2
    assert value["totalProviderCalls"] == 4
    assert value["planDigest"] == m.canonical_digest({k: v for k, v in value.items() if k != "planDigest"})
    for model in m.MODELS:
        for index in (1, 2):
            request = m.build_request(model, index)
            assert request.tools == ()
            assert request.remaining_budget["modelCalls"] == 1
            assert request.remaining_budget["toolCalls"] == 0


def test_distinct_effective_identities_pass() -> None:
    m = load_module()
    value = m.qualify_probes(probes(), plan_value=m.plan())
    assert value["standing"] == "PASS_DISTINCT_EFFECTIVE_IDENTITIES"
    assert value["effectiveIdentityMap"] == {
        "deepseek-flash": "deepseek-flash",
        "deepseek-v4-pro": "deepseek-v4-pro",
    }


def test_alias_collapse_fails_closed() -> None:
    m = load_module()
    value = m.qualify_probes(probes(collapsed=True), plan_value=m.plan())
    assert value["standing"] == "FAIL_COLLAPSED_OR_UNSTABLE_EFFECTIVE_IDENTITIES"
