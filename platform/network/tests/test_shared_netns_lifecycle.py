"""Source-bound, unprivileged regression for the shared netns one-shot lifecycle."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "substrates/shared-egress/netns.py"
UNIT = ROOT / "substrates/shared-egress/systemd/network-v2-browserless-netns.service"


def load():
    spec = importlib.util.spec_from_file_location("shared_egress_netns_test", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakePath:
    present: set[str] = set()

    def __init__(self, name: str):
        self.name = name

    def exists(self) -> bool:
        return self.name in self.present


def test_installed_systemd_unit_cannot_delete_live_namespace():
    contents = UNIT.read_text()
    assert "ExecStart=/usr/bin/python3 /usr/local/libexec/network-v2/shared-egress-netns ensure" in contents
    assert "ExecStartPre=" not in contents
    assert "ExecStop=" not in contents
    assert "ExecStopPost=" not in contents
    assert "EnvironmentFile=/etc/network-v2/browserless/provider.env" in contents


def test_local_namespace_creation_never_depends_on_external_network_online():
    unit = UNIT.read_text()
    assert "network-online.target" not in "\n".join(
        line for line in unit.splitlines() if not line.lstrip().startswith("#")
    )
    assert "PartOf=network-v2-shared-egress.target" in unit
    assert "ExecStart=/usr/bin/python3 /usr/local/libexec/network-v2/shared-egress-netns ensure" in unit


def test_existing_topology_is_reused_without_any_ip_mutation(monkeypatch, capsys):
    netns = load()
    FakePath.present = {"/run/netns/nv2-browserless-prod", "/sys/class/net/vethHost"}
    monkeypatch.setattr(netns, "Path", FakePath)
    observed = []
    monkeypatch.setattr(netns, "verify", lambda *args: observed.append(args))
    monkeypatch.setattr(netns, "command", lambda *args, **kwargs: pytest.fail(f"unexpected ip mutation: {args}"))
    netns.ensure("vethHost", "vethPeer", "10.230.1.1/30", "10.230.1.2/30")
    assert observed == [("vethHost", "vethPeer", "10.230.1.1/30", "10.230.1.2/30")]
    assert "REUSED=PASS" in capsys.readouterr().out


def test_partial_topology_fails_closed_without_deleting(monkeypatch):
    netns = load()
    FakePath.present = {"/run/netns/nv2-browserless-prod"}
    monkeypatch.setattr(netns, "Path", FakePath)
    monkeypatch.setattr(netns, "command", lambda *args, **kwargs: pytest.fail(f"unexpected mutation: {args}"))
    with pytest.raises(netns.TopologyError, match="partial"):
        netns.ensure("vethHost", "vethPeer", "10.230.1.1/30", "10.230.1.2/30")


def test_cold_start_uses_only_native_iproute2_and_verifies(monkeypatch, capsys):
    netns = load()
    FakePath.present = set()
    monkeypatch.setattr(netns, "Path", FakePath)
    actions = []
    monkeypatch.setattr(netns, "command", lambda *args, **kwargs: actions.append(args))
    observed = []
    monkeypatch.setattr(netns, "verify", lambda *args: observed.append(args))
    arguments = ("vethHost", "vethPeer", "10.230.1.1/30", "10.230.1.2/30")
    netns.ensure(*arguments)
    assert len(actions) == 8
    assert actions[0] == ("netns", "add", "nv2-browserless-prod")
    assert actions[1] == ("link", "add", "vethHost", "type", "veth", "peer", "name", "vethPeer")
    assert not any("del" in action for action in actions)
    assert observed == [arguments]
    assert "CREATED=PASS" in capsys.readouterr().out


def test_unpaired_veth_detected_before_route_or_address_check(monkeypatch):
    netns = load()
    FakePath.present = {"/run/netns/nv2-browserless-prod"}
    monkeypatch.setattr(netns, "Path", FakePath)
    monkeypatch.setattr(netns, "link", lambda name, ns=None: {
        "ifindex": 6 if ns is None else 8,
        "link_index": 42 if ns is None else 6,
        "linkinfo": {"info_kind": "veth"},
        "flags": ["UP"],
    })
    monkeypatch.setattr(netns, "command", lambda *args, **kwargs: pytest.fail("should reject before any further observation"))
    with pytest.raises(netns.TopologyError, match="do not form"):
        netns.verify("vethHost", "vethPeer", "10.230.1.1/30", "10.230.1.2/30")


def test_namespace_default_route_is_refuted(monkeypatch):
    netns = load()
    FakePath.present = {"/run/netns/nv2-browserless-prod"}
    monkeypatch.setattr(netns, "Path", FakePath)

    def fake_link(name, ns=None):
        if name == "lo":
            return {"flags": ["UP"]}
        return {
            "ifindex": 11 if ns is None else 10,
            "link_index": 10 if ns is None else 11,
            "linkinfo": {"info_kind": "veth"},
            "flags": ["UP"],
        }

    monkeypatch.setattr(netns, "link", fake_link)
    monkeypatch.setattr(netns, "ipv4", lambda name, ns=None: {("10.230.1.1", 30)} if ns is None else {("10.230.1.2", 30)})
    monkeypatch.setattr(netns, "command", lambda *args, **kwargs: subprocess.CompletedProcess(
        args, 0, json.dumps([{"dst": "default"}] if "-4" in args else []), "",
    ))
    with pytest.raises(netns.TopologyError, match="default route"):
        netns.verify("vethHost", "vethPeer", "10.230.1.1/30", "10.230.1.2/30")
