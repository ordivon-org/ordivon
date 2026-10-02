from __future__ import annotations

import pytest

from ordivon_composition import (
    BrowserNetworkBindingError,
    canonical_digest,
    compile_browser_network_binding,
    require_ready_browser_network_binding,
    validate_browser_network_binding,
)


def ref(label: str) -> dict[str, str]:
    return {"id": label, "digest": canonical_digest({"fixture": label})}


def browser_route() -> dict[str, str]:
    return {
        "routeId": "browser-harness-windows-real-chrome-v1",
        "executor": "browser_harness_windows_real_chrome",
        "substrate": "windows_real_chrome",
        "providerFlow": "generic",
    }


def network_route() -> dict:
    return {
        "routeId": "windows-real-chrome-projected-v1",
        "providerProfileId": "surfshark:th-bkk",
        "provides": [
            "windows",
            "cross-os",
            "browser-egress",
            "provider-egress",
            "mixed-proxy",
            "fail-closed",
        ],
        "readinessStanding": "READY",
    }


def compile(**overrides):
    values = {
        "browser_plan_ref": ref("browser-plan:real-chrome"),
        "network_plan_ref": ref("network-plan:windows-real-chrome"),
        "browser_route": browser_route(),
        "network_route": network_route(),
        "required_network_features": (
            "windows",
            "browser-egress",
            "provider-egress",
            "fail-closed",
        ),
    }
    values.update(overrides)
    return compile_browser_network_binding(**values)


def test_ready_binding_preserves_network_requirement_without_granting_authority():
    value = compile()
    assert value["readyForExecution"] is True
    assert value["missingNetworkFeatures"] == []
    assert value["authorityGranted"] is False
    assert value["browserEffectAuthorized"] is False
    assert value["providerEffectAuthorized"] is False
    assert value["executionDispatched"] is False


def test_missing_network_feature_fails_ready_gate():
    value = compile(required_network_features=("windows", "full-ip"))
    assert value["readyForExecution"] is False
    assert value["missingNetworkFeatures"] == ["full-ip"]
    with pytest.raises(BrowserNetworkBindingError) as exc:
        require_ready_browser_network_binding(value)
    assert exc.value.code == "BINDING_NOT_READY"


def test_unresolved_input_fails_ready_gate():
    value = compile(unresolved_inputs=("chrome-network-binding",))
    assert value["readyForExecution"] is False
    with pytest.raises(BrowserNetworkBindingError) as exc:
        require_ready_browser_network_binding(value)
    assert exc.value.code == "BINDING_NOT_READY"


def test_non_ready_network_route_is_rejected_before_binding():
    route = network_route()
    route["readinessStanding"] = "QUALIFICATION_STALE"
    with pytest.raises(BrowserNetworkBindingError) as exc:
        compile(network_route=route)
    assert exc.value.code == "NETWORK_ROUTE_NOT_READY"


def test_digest_tampering_fails_closed():
    value = compile()
    value["claimBoundary"] = "widened"
    with pytest.raises(BrowserNetworkBindingError) as exc:
        validate_browser_network_binding(value)
    assert exc.value.code == "BINDING_DIGEST_MISMATCH"


def test_route_summaries_are_copied_not_shared():
    browser = browser_route()
    network = network_route()
    value = compile(browser_route=browser, network_route=network)
    browser["substrate"] = "mutated"
    network["provides"].append("full-ip")
    assert value["browserRoute"]["substrate"] == "windows_real_chrome"
    assert "full-ip" not in value["networkRoute"]["provides"]


def test_unknown_authority_payload_is_rejected_by_schema():
    value = compile()
    value["permissions"] = ["browser.click"]
    with pytest.raises(BrowserNetworkBindingError) as exc:
        validate_browser_network_binding(value)
    assert exc.value.code == "INVALID_BINDING"


def test_module_does_not_import_browser_or_network_owner_internals():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "ordivon_composition"
        / "browser_network_binding_r1.py"
    ).read_text()
    for forbidden in (
        "browser_capability_router",
        "network_capability_router",
        "ordivon_harness",
        "ordivon_runtime",
        "ordivon_gateway",
    ):
        assert forbidden not in source
