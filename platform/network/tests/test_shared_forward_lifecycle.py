"""Source-bound forwarding convergence and non-destructive counterexamples."""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "substrates/shared-egress/forward.py"
UNIT = ROOT / "substrates/shared-egress/systemd/network-v2-browserless-forward.service"


def load():
    spec = importlib.util.spec_from_file_location("shared_egress_forward_test", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KernelRules:
    def __init__(self, owned):
        self.owned = set(owned)
        self.insertions = []
        self.listed_other = []
        self.fail_next_insert = False

    def __call__(self, *args):
        op = args[0]
        if op == "-S":
            lines = ["-A FORWARD " + " ".join(rule) for rule in self.owned]
            return subprocess.CompletedProcess(args, 0, "\n".join(lines + self.listed_other), "")
        if op == "-C":
            return subprocess.CompletedProcess(args, 0 if tuple(args[2:]) in self.owned else 1, "", "")
        if op == "-I":
            if self.fail_next_insert:
                self.fail_next_insert = False
                return subprocess.CompletedProcess(args, 2, "", "injected failure")
            rule = tuple(args[3:])
            self.insertions.append(rule)
            self.owned.add(rule)
            return subprocess.CompletedProcess(args, 0, "", "")
        pytest.fail(f"destructive or unsupported firewall operation: {args}")


def expected(forward):
    return forward.rules("nv2blph", "10.252.246.0/30")


def test_systemd_forward_service_never_deletes_shared_live_rules():
    service = UNIT.read_text()
    assert "PartOf=network-v2-shared-egress.target" in service
    assert "ExecStart=/usr/bin/python3 /usr/local/libexec/network-v2/shared-egress-forward ensure" in service
    assert "ExecStop=" not in service
    assert "ExecStartPre=" not in service
    assert "iptables-legacy -D" not in service
    assert "EnvironmentFile=/etc/network-v2/browserless/provider.env" in service


def test_cold_insert_only_missing_rules_and_repeated_start_is_noop(monkeypatch):
    forward = load()
    fake = KernelRules([])
    monkeypatch.setattr(forward, "command", fake)
    forward.ensure(expected(forward))
    assert fake.owned == set(expected(forward))
    assert len(fake.insertions) == 2
    forward.ensure(expected(forward))
    assert len(fake.insertions) == 2
    forward.verify(expected(forward))


def test_existing_partial_rules_repair_only_missing_without_deletion(monkeypatch):
    forward = load()
    fake = KernelRules([expected(forward)[0]])
    monkeypatch.setattr(forward, "command", fake)
    forward.ensure(expected(forward))
    assert fake.insertions == [expected(forward)[1]]


def test_unrecognized_owner_marker_fails_closed_without_mutation(monkeypatch):
    forward = load()
    fake = KernelRules([expected(forward)[0]])
    fake.listed_other.append(
        "-A FORWARD -s 0.0.0.0/0 -m comment --comment "
        + forward.MARKER + " -j ACCEPT"
    )
    monkeypatch.setattr(forward, "command", fake)
    with pytest.raises(forward.ForwardError, match="unrecognized or duplicated"):
        forward.ensure(expected(forward))
    assert fake.insertions == []


def test_insert_failure_preserves_partial_evidence_for_recovery(monkeypatch):
    forward = load()
    fake = KernelRules([expected(forward)[0]])
    fake.fail_next_insert = True
    monkeypatch.setattr(forward, "command", fake)
    with pytest.raises(forward.ForwardError, match="iptables -I"):
        forward.ensure(expected(forward))
    assert fake.owned == {expected(forward)[0]}
    forward.ensure(expected(forward))
    assert fake.owned == set(expected(forward))


def test_read_only_verify_never_inserts_rules(monkeypatch):
    forward = load()
    fake = KernelRules([])
    monkeypatch.setattr(forward, "command", fake)
    with pytest.raises(forward.ForwardError, match="incomplete"):
        forward.verify(expected(forward))
    assert fake.insertions == []


def test_native_kernel_task_calls_source_forward_verifier_read_only():
    task = (ROOT / "substrates/shared-egress/Taskfile.yml").read_text()
    kernel_task = task.split("  substrate:shared-egress:kernel:verify:", 1)[1].split(
        "  substrate:shared-egress:verify:", 1
    )[0]
    assert 'HOST_IF="$HOST_IF" NS_CIDR="$NS_CIDR" /usr/bin/python3 substrates/shared-egress/forward.py verify' in kernel_task
    assert "forward.py ensure" not in kernel_task


def test_native_verify_checks_loaded_systemd_not_only_installed_bytes():
    task = (ROOT / "substrates/shared-egress/Taskfile.yml").read_text()
    verify = task.split("  substrate:shared-egress:verify:", 1)[1]
    assert "--property=NeedDaemonReload --value" in verify
    assert "--property=Wants --value" in verify
    assert "--property=After --value" in verify
    assert "--property=ExecStart --value" in verify
    assert "--property=ExecStop --value" in verify
    assert "/usr/local/libexec/network-v2/shared-egress-forward ensure" in verify
    assert "SHARED_EGRESS_LOADED_UNITS=PASS" in verify


def test_owner_materializes_helper_before_unit_and_verifies_installed_bytes():
    text = (ROOT / "substrates/shared-egress/Taskfile.yml").read_text()
    helper = "install -m 0755 substrates/shared-egress/forward.py /usr/local/libexec/network-v2/shared-egress-forward"
    unit = ("install -m 0644 substrates/shared-egress/systemd/network-v2-browserless-forward.service "
            "/etc/systemd/system/network-v2-browserless-forward.service")
    assert text.count(helper) == 1
    assert text.index(helper) < text.index(unit)
    byte_check = "cmp -s substrates/shared-egress/forward.py /usr/local/libexec/network-v2/shared-egress-forward"
    assert text.count(byte_check) == 2
