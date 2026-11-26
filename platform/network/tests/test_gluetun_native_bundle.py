"""Systemd reuses one installed native Gluetun recovery consumer."""
import importlib.util
from pathlib import Path
import sys

import pytest

DIR=Path(__file__).resolve().parents[1]/"providers/gluetun"
sys.path.insert(0,str(DIR))
spec=importlib.util.spec_from_file_location("native_bundle",DIR/"native_bundle.py")
bundle=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=bundle
spec.loader.exec_module(bundle)


def test_reconciler_keeps_original_native_owner_and_one_recovery_consumer():
    result=bundle.validate_source()
    assert result["nonsecretFileCount"]==10
    data=bundle.SOURCE_SVC.read_text()
    assert "ExecStartPost=/usr/bin/python3 " in data
    assert "native_switch.py --recover" in data
    assert "TimeoutStartSec=4min" in data
    assert "new WireGuard" not in data
    assert "ExecStart=/usr/bin/systemctl start network-v2-gluetun-owned.service" in data


def test_source_payload_is_installable_without_credentials_or_live_effect(tmp_path):
    assert all("auth/config.toml" not in name for name in bundle.FILES)
    assert all("private_key" not in name for name in bundle.FILES)
    dest=tmp_path/"gluetun-native"
    bundle.copy_payload(dest)
    assert bundle.verify(dest=dest,verify_systemd=False)["nonsecretFileCount"]==10
    assert (dest/"native_switch.py").is_file()
    assert (dest/"historical_observation.py").is_file()
    assert (dest/"native_selection.py").is_file()
    assert (dest/"config/exit-allowlist.json").is_file()


def test_runtime_observer_reuses_neighbor_provider_contract_in_source_and_install():
    script=(DIR/"observe_active.py").read_text()
    assert 'NATIVE_PROFILE = Path(__file__).resolve().with_name("native_profile.py")' in script
    assert "parents[2]" not in script


def test_loaded_timer_source_keeps_single_native_unit_and_minute_cadence():
    data=bundle.SOURCE_TIMER.read_text()
    assert data.count("OnCalendar=*-*-* *:*:00")==1
    assert "RandomizedDelaySec=5s" in data
    assert "AccuracySec=5s" in data
    assert "Unit=network-v2-gluetun-owned-reconcile.service" in data
    assert "OnCalendar=*-*-* *:0/2:00" not in data
    assert bundle.TIMER_NAME=="network-v2-gluetun-owned-reconcile.timer"


def test_repeated_readback_rejects_same_size_same_mtime_corruption(tmp_path):
    import os
    dest = tmp_path / "bundle"
    bundle.copy_payload(dest)
    bundle.verify(dest=dest, verify_systemd=False)
    path = dest / "quality_history.py"
    before = path.stat()
    original = path.read_bytes()
    path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(ValueError, match="mismatch"):
        bundle.verify(dest=dest, verify_systemd=False)


@pytest.mark.parametrize("relative", ["quality_history.py", "config"])
def test_readback_rejects_symlinked_payload_even_if_bytes_match(tmp_path, relative):
    import shutil
    dest = tmp_path / "bundle"
    bundle.copy_payload(dest)
    path = dest / relative
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    path.symlink_to(bundle.SOURCE / relative, target_is_directory=relative=="config")
    with pytest.raises(ValueError):
        bundle.verify(dest=dest, verify_systemd=False)


@pytest.mark.parametrize("target", ["service", "timer"])
@pytest.mark.parametrize("field,value", [
    ("LoadState","not-found"),
    ("FragmentPath","/tmp/unrelated.service"),
    ("DropInPaths","/tmp/override.conf"),
    ("NeedDaemonReload","yes"),
    ("NeedDaemonReload",None),
    ("LoadState","loaded\nLoadState=loaded"),
])
def test_loaded_identity_does_not_accept_unqualified_metadata(tmp_path, monkeypatch, field, value, target):
    dest = tmp_path / "bundle"
    bundle.copy_payload(dest)
    monkeypatch.setattr(bundle,"INSTALLED_SVC",bundle.SOURCE_SVC)
    monkeypatch.setattr(bundle,"INSTALLED_TIMER",bundle.SOURCE_TIMER)
    def fake_run(*args, **kwargs):
        unit = args[2]
        if args[-1] == "ExecStartPost":
            return "ExecStartPost=" + bundle.EFFECT + " --recover"
        if args[-1] == "TimersCalendar":
            return "TimersCalendar=OnCalendar=*-*-* *:*:00"
        fields = {"LoadState":"loaded",
                  "FragmentPath":str(bundle.INSTALLED_SVC if unit==bundle.SVC_NAME else bundle.INSTALLED_TIMER),
                  "DropInPaths":"","NeedDaemonReload":"no"}
        if unit == (bundle.SVC_NAME if target == "service" else bundle.TIMER_NAME):
            if value is None:
                del fields[field]
            else:
                fields[field]=value
        return "\n".join(f"{k}={v}" for k,v in fields.items())
    monkeypatch.setattr(bundle,"run",fake_run)
    with pytest.raises(ValueError):
        bundle.verify(dest=dest)

def test_native_loaded_identity_accepts_exact_metadata_without_claiming_execution(tmp_path, monkeypatch):
    dest = tmp_path / "bundle"
    bundle.copy_payload(dest)
    monkeypatch.setattr(bundle, "INSTALLED_SVC", bundle.SOURCE_SVC)
    monkeypatch.setattr(bundle, "INSTALLED_TIMER", bundle.SOURCE_TIMER)
    def fake_run(*args, **kwargs):
        if args[-1] == "ExecStartPost":
            return "ExecStartPost=" + bundle.EFFECT + " --recover"
        if args[-1] == "TimersCalendar":
            return "TimersCalendar=OnCalendar=*-*-* *:*:00"
        fragment = bundle.INSTALLED_SVC if args[2] == bundle.SVC_NAME else bundle.INSTALLED_TIMER
        return f"NeedDaemonReload=no\nDropInPaths=\nFragmentPath={fragment}\nLoadState=loaded"
    monkeypatch.setattr(bundle, "run", fake_run)
    receipt = bundle.verify(dest=dest)
    assert receipt["loadedIdentityChecked"] is True
    assert receipt["consumerExecutionProved"] is False
    assert bundle.verify(dest=dest, verify_systemd=False)["loadedIdentityChecked"] is False


@pytest.mark.parametrize("cut", range(len(bundle.FILES)+1))
def test_native_copy_interruption_is_not_complete_readback(tmp_path, monkeypatch, cut):
    """Native copy fault cut, not power-loss or atomicity proof."""
    import subprocess
    dest = tmp_path / "bundle"
    bundle.copy_payload(dest)
    for relative in bundle.FILES:
        path = dest / relative
        path.write_bytes(b"old-generation\n" + path.read_bytes())
    original_run = subprocess.run
    completed = 0
    def interrupted(*args, **kwargs):
        nonlocal completed
        if completed == cut:
            raise subprocess.CalledProcessError(1, args[0])
        result = original_run(*args, **kwargs)
        completed += 1
        return result
    with monkeypatch.context() as m:
        m.setattr(bundle.subprocess, "run", interrupted)
        if cut < len(bundle.FILES):
            with pytest.raises(subprocess.CalledProcessError):
                bundle.copy_payload(dest)
        else:
            bundle.copy_payload(dest)
    matched = sum((dest / r).read_bytes() == (bundle.SOURCE / r).read_bytes()
                  for r in bundle.FILES)
    assert matched == cut
    if cut < len(bundle.FILES):
        with pytest.raises(ValueError):
            bundle.verify(dest=dest, verify_systemd=False)
    else:
        assert bundle.verify(dest=dest, verify_systemd=False)["consumerExecutionProved"] is False
