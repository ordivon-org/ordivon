"""Persistent M4 provider mode must survive reboot semantics."""
from __future__ import annotations
import configparser
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]/"capabilities/gluetun/m4-source"
MODE="/etc/network-v2/gluetun/m4-owned-mode.selected"

def ini(name):
    p=configparser.ConfigParser(interpolation=None, strict=False)
    p.read(ROOT/name)
    return p

def test_owned_boot_selection_is_durable_not_run_volatile():
    for name in (
        "network-v2-gluetun-owned.container",
        "network-v2-gluetun-owned-adapter.service",
        "network-v2-gluetun-owned.target",
        "network-v2-gluetun-legacy-restore.service",
    ):
        assert ini(name)["Unit"].get("ConditionPathExists")==MODE, name
    helper=(ROOT/"m4-owned-restore-legacy").read_text()
    assert "M4_PROVIDER_MODE_MARKER" in helper and MODE in helper
    assert "/run/network-v2-gluetun/ownership-admitted" not in "\n".join(
        (ROOT/name).read_text() for name in (
            "network-v2-gluetun-owned.container",
            "network-v2-gluetun-owned-adapter.service",
            "network-v2-gluetun-owned.target",
            "network-v2-gluetun-legacy-restore.service",
            "m4-owned-restore-legacy",
        )
    )

def test_fallback_changes_durable_mode_only_after_candidate_absence():
    helper=(ROOT/"m4-owned-restore-legacy").read_text()
    absent=helper.index('test "$absent_rc" = 1')
    remove=helper.index('rm -f "$MARKER"')
    enable_legacy=helper.index('systemctl enable "$LEGACY_TARGET"')
    assert absent < enable_legacy < remove

def test_no_source_task_creates_or_enables_owned_mode():
    task=(Path(__file__).resolve().parents[1]/"Taskfile.yml").read_text()
    assert MODE not in task
    assert "systemctl enable network-v2-gluetun-owned.target" not in task
    assert "systemctl start network-v2-gluetun-owned.target" not in task

def test_native_generator_preserves_durable_gate():
    env={**os.environ,"QUADLET_UNIT_DIRS":str(ROOT)}
    r=subprocess.run(
        ["/usr/lib/systemd/system-generators/podman-system-generator","--dryrun"],
        env=env,text=True,capture_output=True,timeout=15,check=False,
    )
    assert r.returncode==0,r.stderr
    assert f"ConditionPathExists={MODE}" in r.stdout
    assert "--pull never" in r.stdout
    assert "--publish 10.252.246.1:19682:8888/tcp" in r.stdout
