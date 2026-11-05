from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT / "consumers" / "codex"
MOBILE = ROOT / "consumers" / "mobile-tailnet-exit"


def test_codex_policy_admits_only_bounded_provider_https():
    policy = json.loads((CODEX / "config" / "sing-box.json").read_text())
    ins = policy["inbounds"]
    assert len(ins) == 1
    assert (ins[0]["type"], ins[0]["listen"], ins[0]["listen_port"]) == (
        "http", "127.0.0.1", 19980
    )
    assert len(policy["outbounds"]) == 1
    upstream = policy["outbounds"][0]
    assert (upstream["type"], upstream["server"], upstream["server_port"]) == (
        "http", "10.252.246.2", 19680
    )
    rules = policy["route"]["rules"]
    assert rules[0]["port"] == [443]
    assert rules[0]["network"] == ["tcp"]
    assert rules[0]["outbound"] == upstream["tag"]
    assert {"chatgpt.com", "auth.openai.com", "persistent.oaistatic.com"} <= set(rules[0]["domain"])
    assert rules[-1] == {"action": "reject"}


def test_codex_relay_and_denial_path_wiring():
    relay = (CODEX / "systemd" / "network-v2-codex-relay.service").read_text()
    proxy = (CODEX / "systemd" / "network-v2-codex-proxy.service").read_text()
    ready = (CODEX / "ready.sh").read_text()
    assert "-l 127.0.0.1:19982" in relay
    assert "127.0.0.1:19980" in relay
    assert "NetworkNamespacePath=/run/netns/nv2-browserless-prod" in proxy
    assert "unknown_rc" in ready


def test_mobile_tracks_provider_network_identity_and_exit_advertisement():
    runner = (MOBILE / "run.sh").read_text()
    assert "network-v2-gluetun-owned-r1" in runner
    assert 'nsenter -t "$provider_pid" -n' in runner
    assert "--tun=userspace-networking" in runner
    assert "set --advertise-exit-node" in runner
    assert 'current_provider_pid" != "$provider_pid"' in runner
    assert "trap cleanup EXIT INT TERM" in runner


def test_mobile_ready_requires_admin_approval_and_upstream():
    ready = (MOBILE / "ready.py").read_text()
    for word in (
        "ADVERTISED_PENDING_ADMIN_APPROVAL",
        "PROVIDER_EGRESS_NOT_READY",
        "NAMESPACE_MISMATCH",
        "network-v2-gluetun-owned-r1",
        "browserless-provider-carrier-ready",
    ):
        assert word in ready


def test_mobile_systemd_uses_bounded_native_backoff():
    unit = (MOBILE / "systemd" / "network-v2-mobile-tailnet-exit.service").read_text()
    for setting in (
        "Restart=always", "RestartSec=3s", "RestartSteps=5",
        "RestartMaxDelaySec=2min", "BindReadOnlyPaths=",
        "ExecStart=/usr/local/libexec/network-v2/mobile-tailnet-exit-run",
    ):
        assert setting in unit
