"""Official Gluetun auth role shape and safe root-only materialization source."""
import sys
from pathlib import Path
import importlib.util

import pytest

DIR=Path(__file__).resolve().parents[1]/"providers/gluetun"
sys.path.insert(0,str(DIR))
spec=importlib.util.spec_from_file_location("native_auth_profile",DIR/"auth_profile.py")
a=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=a
spec.loader.exec_module(a)

def test_auth_source_never_opens_native_write_to_unauthenticated_clients():
    source=a.rendered("unit_test_synthetic_api_key_abcdefghijklmnopqrstuvwxyz")
    result=a.assert_role_contract(source)
    assert result["authenticatedWriteRouteCount"]==1
    assert "PUT /v1/vpn/settings" in source
    assert 'auth = "apikey"' in source
    assert a.READ_ROUTES and set(a.READ_ROUTES).isdisjoint(a.CHANGE_ROUTES)

def test_native_auth_roles_reject_unexpected_routes():
    text=a.rendered("unit_test_synthetic_api_key_abcdefghijklmnopqrstuvwxyz")
    bad=text.replace('"GET /v1/vpn/status"', '"PUT /v1/vpn/settings"')
    with pytest.raises(ValueError):
        a.assert_role_contract(bad)
    with pytest.raises(ValueError):
        a.rendered("short")

def test_auth_materialize_never_overwrites_existing_secrets(monkeypatch,tmp_path):
    target=tmp_path/"auth"/"config.toml"
    assert a.install(target,require_root=False)["standing"]=="NATIVE_AUTH_PREPARED_NOT_LOADED"
    before=target.read_bytes()
    assert a.verify(target,require_root=False)["authenticatedWriteRouteCount"]==1
    assert a.install(target,require_root=False)["standing"]=="PRESENT_UNCHANGED"
    assert target.read_bytes()==before
    assert not (target.stat().st_mode & 0o077)
