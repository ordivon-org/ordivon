"""Independent counterexamples for the read-only ZTE MU5358 adapter."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import pytest

P = Path(__file__).resolve().parents[1] / "providers" / "zte-u30pro" / "observe.py"
spec = spec_from_file_location("zte_obs", P)
m = module_from_spec(spec)
spec.loader.exec_module(m)


@pytest.mark.parametrize("ip", ["example.com", "8.8.8.8", "127.0.0.1", "169.254.1.1", "localhost"])
def test_must_use_private_numeric_router(ip):
    with pytest.raises(ValueError):
        m.validate_gateway(ip)


def test_known_gateway_is_valid():
    assert m.validate_gateway("192.168.0.1") == "192.168.0.1"


def test_sensitive_fields_fail_closed():
    raw = {"model_name": "MU5358", "Password": "SECRET", "imei": "SECRET",
           "ssid": "SECRET", "sim_iccid": "SECRET", "wa_inner_version": "B24"}
    safe = m.project("identity", raw)
    assert safe["model_name"] == "MU5358"
    assert "SECRET" not in json.dumps(safe)
    assert "Password" not in safe


def test_unknown_is_not_false():
    x = m.project("wifi", {"wifi6_mode": "", "wifi_onoff_state": "0"})
    assert x["wifi6_mode"] is None
    assert x["wifi_onoff_state"] == "0"


def test_reject_unavailable_backend():
    with pytest.raises(ValueError):
        m.project("identity", {"Error": "none secure connection"})


def test_no_active_probes_when_disabled():
    def fake(gateway, group):
        return {"model_name": "MU5358"} if group == "identity" else {}
    x = m.observe("192.168.0.1", active=False, fetch=fake)
    assert x["device_identity"] == "MU5358_CONFIRMED"
    assert x["local_probes"]["standing"] == "NOT_RUN"
    assert x["constraints"]["mutated_device"] is False


def test_wrong_model_never_certified():
    def fake(gateway, group):
        return {"model_name": "U30Air"} if group == "identity" else {}
    x = m.observe("192.168.0.1", active=False, fetch=fake)
    assert x["device_identity"] == "UNKNOWN_OR_DIFFERENT"


def test_vendor_transport_is_get_only_and_whitelisted(monkeypatch):
    import subprocess
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps({
            "model_name": "MU5358", "Password": "DO_NOT_EMIT",
        }), "")

    monkeypatch.setattr(m.subprocess, "run", run)
    fields = m.read_group("192.168.0.1", "identity")
    assert fields["model_name"] == "MU5358"
    assert "DO_NOT_EMIT" not in json.dumps(fields)
    args = calls[0]
    assert args[0] == "curl" and "--get" in args
    assert "goform_get_cmd_process" in " ".join(args)
    assert "goform_set_cmd_process" not in " ".join(args)
    assert "queryAccessPointInfo" not in " ".join(args)


def test_timeout_remains_unknown(monkeypatch):
    import subprocess

    def fail(gateway, group):
        raise subprocess.TimeoutExpired(["curl"], 9)

    x = m.observe("192.168.0.1", active=False, fetch=fail)
    assert x["device_identity"] == "UNKNOWN_OR_DIFFERENT"
    assert all(v["standing"] == "UNKNOWN" for v in x["device"].values())
