import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "network_capability_router.py"
spec = importlib.util.spec_from_file_location("network_capability_router", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


def fake(readiness_by_route):
    def probe(route):
        standing = readiness_by_route.get(route["routeId"], "READY")
        return {"ready": standing == "READY", "standing": standing}
    return probe


def request(**overrides):
    value = {
        "schemaVersion": 1,
        "requestId": "req-1",
        "requiredFeatures": ["linux"],
        "preferredFeatures": [],
    }
    value.update(overrides)
    return value


def test_policy_has_semantic_provider_egress_and_no_browserless_route_identity():
    policy = mod.load_policy()
    route = next(r for r in policy["routes"] if r["routeId"] == "provider-egress-v1")
    assert route["providerProfileId"] == "surfshark:th-bkk"
    assert "provider-egress" in route["provides"]
    assert "browserless" not in route["routeId"]


def test_selects_ready_route_by_preference_then_priority():
    result = mod.plan(
        request(preferredFeatures=["provider-egress"]),
        readiness_provider=fake({
            "direct-linux-v1": "READY",
            "provider-egress-v1": "READY",
            "isolated-tun-v1": "QUALIFICATION_STALE",
        }),
    )
    assert result["standing"] == "SELECTED_ROUTE"
    assert result["selectedRoute"]["routeId"] == "provider-egress-v1"


def test_required_provider_profile_selects_exact_provider_route():
    result = mod.plan(
        request(requiredFeatures=["linux", "provider-egress"], providerProfileId="surfshark:th-bkk"),
        readiness_provider=fake({"provider-egress-v1": "READY"}),
    )
    assert result["selectedRoute"]["routeId"] == "provider-egress-v1"


def test_holds_when_only_compatible_route_is_not_ready():
    result = mod.plan(
        request(requiredFeatures=["linux", "full-ip", "quic"]),
        readiness_provider=fake({"isolated-tun-v1": "QUALIFICATION_STALE"}),
    )
    assert result["standing"] == "HOLD_NO_READY_ROUTE"
    assert result["selectedRoute"] is None
    assert result["candidates"][0]["readiness"]["standing"] == "QUALIFICATION_STALE"


def test_stale_kernel_qualification_is_not_promoted_to_ready(tmp_path, monkeypatch):
    evidence = {
        "platformEvidence": {"kernelRelease": "old-kernel"},
        "generic": {"udpQuicIsolatedTun": "PASS", "netnsTopology": "PASS"},
    }
    p = tmp_path / "evidence.json"
    p.write_text(json.dumps(evidence))
    monkeypatch.setattr(mod, "NETWORK_ROOT", tmp_path)
    route = {
        "readiness": {
            "kind": "evidence-current-kernel",
            "evidencePath": "evidence.json",
            "requiredClaims": {
                "generic.udpQuicIsolatedTun": "PASS",
                "generic.netnsTopology": "PASS",
            },
        }
    }
    result = mod.probe_route(route, current_kernel="new-kernel")
    assert result["ready"] is False
    assert result["standing"] == "QUALIFICATION_STALE"
    assert result["claimsSatisfied"] is True


def test_unknown_features_are_rejected():
    try:
        mod.plan(request(requiredFeatures=["not-a-network-feature"]), readiness_provider=fake({}))
    except ValueError as exc:
        assert "unknown network routing features" in str(exc)
    else:
        raise AssertionError("unknown feature was accepted")


def test_plan_is_projection_only():
    result = mod.plan(request(), readiness_provider=fake({
        "direct-linux-v1": "READY",
        "provider-egress-v1": "READY",
        "isolated-tun-v1": "QUALIFICATION_STALE",
    }))
    assert "plan-is-not-network-authority" in result["nonClaims"]
    assert "plan-does-not-mutate-network-state" in result["nonClaims"]


def test_windows_real_chrome_projection_is_catalogued_as_network_only_route():
    policy = mod.load_policy()
    route = next(r for r in policy["routes"] if r["routeId"] == "windows-real-chrome-projected-v1")
    assert route["providerProfileId"] == "surfshark:th-bkk"
    assert set(["windows", "cross-os", "browser-egress", "provider-egress", "fail-closed"]).issubset(route["provides"])
    assert "browser-control" not in route["provides"]
