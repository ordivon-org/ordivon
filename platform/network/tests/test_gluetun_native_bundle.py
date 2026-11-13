"""Systemd reuses one installed native Gluetun recovery consumer."""
import importlib.util
from pathlib import Path
import sys

import pytest

DIR=Path(__file__).resolve().parents[1]/"providers/gluetun"
spec=importlib.util.spec_from_file_location("native_bundle",DIR/"native_bundle.py")
bundle=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=bundle
spec.loader.exec_module(bundle)


def test_reconciler_keeps_original_native_owner_and_one_recovery_consumer():
    result=bundle.validate_source()
    assert result["nonsecretFileCount"]==7
    data=bundle.SOURCE_SVC.read_text()
    assert "ExecStartPost=/usr/bin/python3 " in data
    assert "native_switch.py --recover" in data
    assert "TimeoutStartSec=3min" in data
    assert "new WireGuard" not in data
    assert "ExecStart=/usr/bin/systemctl start network-v2-gluetun-owned.service" in data


def test_source_payload_is_installable_without_credentials_or_live_effect(tmp_path):
    assert all("auth/config.toml" not in name for name in bundle.FILES)
    assert all("private_key" not in name for name in bundle.FILES)
    dest=tmp_path/"gluetun-native"
    bundle.copy_payload(dest)
    assert bundle.verify(dest=dest,verify_systemd=False)["nonsecretFileCount"]==7
    assert (dest/"native_switch.py").is_file()
    assert (dest/"config/exit-allowlist.json").is_file()


def test_runtime_observer_reuses_neighbor_provider_contract_in_source_and_install():
    script=(DIR/"observe_active.py").read_text()
    assert 'NATIVE_PROFILE = Path(__file__).resolve().with_name("native_profile.py")' in script
    assert "parents[2]" not in script
