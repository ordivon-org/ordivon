from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
X = ROOT / "consumers" / "x-reality"

def test_authority_is_transport_only_and_exact():
    a = json.loads((X / "config" / "authority.json").read_text())
    assert a["listen"] == {"host":"127.0.0.1","port":19681,"protocol":"http"}
    assert a["allowedHttpsDomains"] == ["api.x.com"]
    assert a["directFallback"] is False
    assert a["authenticationAuthority"] == {"separate": True, "transportConsumerOwnsCredential": False, "userContextProven": False}

def test_egress_uses_shared_carrier_and_rejects_unknown():
    e = json.loads((X / "config" / "egress.json").read_text())
    assert e["outbounds"] == [{"type":"http","tag":"provider-carrier","server":"10.252.246.2","server_port":19680}]
    route = e["route"]["rules"][0]
    assert route["domain"] == ["api.x.com"]
    assert route["port"] == 443
    assert e["route"]["rules"][-1]["action"] == "reject"

def test_semantic_service_soft_depends_on_carrier():
    u = (X / "systemd" / "network-v2-x-reality-egress.service").read_text()
    assert "Wants=network-v2-browserless-provider-carrier.service" in u
    assert "Requires=network-v2-browserless-provider-carrier.service" not in u
    assert "After=network-v2-browserless-provider-carrier.service" in u

def test_readiness_has_no_credential_surface():
    r = (X / "ready.sh").read_text()
    assert "api.x.com/2/users/me" in r
    assert '[ "$code" = 401 ]' in r
    assert 'authenticationAttempted":false' in r
    assert 'credentialMaterialized":false' in r
    assert 'userContextProven":false' in r
    lowered = (X / "README.md").read_text().lower()
    assert "does not read" in lowered
