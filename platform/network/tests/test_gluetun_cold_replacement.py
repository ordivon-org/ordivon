from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
M4=ROOT/"capabilities/gluetun/m4-source"
MODE="/etc/network-v2/gluetun/m4-owned-mode.selected"

def text(name): return (M4/name).read_text()

def test_physical_services_enforce_mode_at_service_boundary():
    legacy=text("network-v2-browserless-wireguard.service")
    owned=text("network-v2-gluetun-owned.container")
    guard=text("provider-identity-exclusive")
    assert f"ConditionPathExists=!{MODE}" in legacy
    assert "provider-identity-exclusive legacy" in legacy
    assert f"ConditionPathExists={MODE}" in owned
    assert "provider-identity-exclusive gluetun" in owned
    assert ("MODE_MARKER=" + "$" + "{M4_PROVIDER_MODE_MARKER:-" + MODE + "}") in guard
    assert 'test ! -e "$MODE_MARKER"' in guard

def test_cold_replacement_does_not_auto_fallback_or_cross_conflict_targets():
    owned_target=text("network-v2-gluetun-owned.target")
    legacy_target=text("network-v2-browserless-legacy-provider.target")
    owned_container=text("network-v2-gluetun-owned.container")
    assert "OnFailure=" not in owned_target
    assert "OnFailure=" not in owned_container
    assert "Conflicts=network-v2-gluetun-owned.target" not in legacy_target
    assert "Restart=on-failure" in owned_container

def test_shared_provider_ready_is_mechanism_neutral():
    ready=(ROOT/"consumers/browserless/provider-carrier-ready.sh").read_text()
    assert "network-v2-gluetun-owned-adapter.service" in ready
    assert "legacy-wireguard" in ready
    assert "gluetun" in ready
    assert "candidate-consequence.sh" not in ready
    assert "--noproxy" in ready
    assert "network-v2-browserless-wireguard.service network-v2-browserless-dns.service" not in ready

def test_cold_replacement_is_one_transaction_with_rollback():
    script=ROOT/"capabilities/gluetun/acceptance/cold-replacement.sh"
    assert script.exists()
    s=script.read_text()
    for token in (
        "--preflight","--execute","rollback","backup.tar",
        "network-v2-browserless-provider-carrier.service",
        "network-v2-browserless-wireguard.service",
        "m4-owned-mode.selected",
        "network-v2-gluetun-owned.target",
        "candidate-consequence.sh",
    ):
        assert token in s
    assert s.index('systemctl stop "$LEGACY_CARRIER"') < s.index('systemctl stop "$LEGACY_WG"')
    assert s.index('systemctl stop "$LEGACY_WG"') < s.index('install -m 0644 /dev/null "$MODE_MARKER"')
    assert s.index('install -m 0644 /dev/null "$MODE_MARKER"') < s.index('systemctl start "$OWNED_TARGET"')
    assert 'ip netns exec nv2-browserless-prod curl' in s
    assert '-x http://10.252.246.1:19682' in s
    assert 'case "$code" in 401|403)' in s
