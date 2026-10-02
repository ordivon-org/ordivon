import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "browser_control_port.py"
spec = importlib.util.spec_from_file_location("browser_control_port", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


def test_contract_has_no_raw_cdp_domain_operations():
    contract = mod.load_contract()
    ids = [item["operationId"] for item in contract["operations"]]
    assert all(not item.lower().startswith("cdp.") for item in ids)
    assert "raw-cdp-is-not-the-browser-domain-api" in contract["nonClaims"]


def test_real_chrome_adapter_qualifies_read_only_baseline_only():
    contract = mod.load_contract()
    adapter = next(
        item
        for item in contract["adapters"]
        if item["adapterId"] == "browser-harness-real-chrome-v1"
    )
    assert set(adapter["qualifiedOperations"]) == {
        "readiness",
        "tabs.list",
        "page.observe-structured",
    }
    effect_by_op = {item["operationId"]: item["effectClass"] for item in contract["operations"]}
    assert all(effect_by_op[item] == "observation" for item in adapter["qualifiedOperations"])


def test_real_chrome_route_binds_to_control_port_adapter():
    routes = mod.load_browser_routes()
    route = routes["browser-harness-windows-real-chrome-v1"]
    assert route["controlPortAdapter"] == "browser-harness-real-chrome-v1"


def test_real_chrome_observation_is_qualified_but_authority_remains_false():
    value = mod.check_route_binding(
        "browser-harness-windows-real-chrome-v1",
        operation="page.observe-structured",
    )
    assert value["standing"] == "QUALIFIED_OPERATION"
    assert value["operationQualified"] is True
    assert value["authorityGranted"] is False
    assert value["browserEffectAuthorized"] is False
    assert value["providerEffectAuthorized"] is False
    assert value["executionDispatched"] is False


def test_real_chrome_click_is_not_promoted_from_upstream_capability():
    value = mod.check_route_binding(
        "browser-harness-windows-real-chrome-v1",
        operation="page.click",
    )
    assert value["standing"] == "HOLD_OPERATION_UNSUPPORTED"
    assert value["operationQualified"] is False


def test_browserless_effectful_route_contract_is_not_independent_f6_qualification():
    value = mod.check_route_binding(
        "browser-use-browserless-v1",
        operation="page.click",
    )
    assert value["implementationSupported"] is True
    assert value["standing"] == "HOLD_OPERATION_UNQUALIFIED"
    assert value["operationQualified"] is False


def test_route_feature_bindings_are_implementation_compatible():
    value = mod.validate_route_feature_bindings()
    assert value["healthy"] is True
    assert value["authorityGranted"] is False
    assert all(row["bindingValid"] for row in value["rows"])
    assert all(row["missingImplementationOperations"] == [] for row in value["rows"])


def test_future_bidi_adapter_is_not_materialized():
    contract = mod.load_contract()
    adapter = next(
        item for item in contract["adapters"] if item["adapterId"] == "webdriver-bidi-future-v1"
    )
    assert adapter["qualificationStanding"] == "NOT_MATERIALIZED"
    assert adapter["routeIds"] == []
    assert adapter["qualifiedOperations"] == []


def test_browser_router_selected_route_projects_control_port_adapter():
    # Static policy check: Browser Router must carry the adapter binding through selected route.
    source = (ROOT / "scripts" / "browser_capability_router.py").read_text()
    assert 'selected_route["controlPortAdapter"] = selected["controlPortAdapter"]' in source
