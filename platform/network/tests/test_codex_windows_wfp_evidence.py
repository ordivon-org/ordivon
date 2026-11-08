"""WFP event refinement uses actual Microsoft Security event fields."""
import importlib.util
import json
from pathlib import Path
import pytest

SOURCE = Path(__file__).resolve().parents[1] / "consumers/codex/windows_wfp_evidence.py"


def module():
    spec = importlib.util.spec_from_file_location("network_win_wfp", SOURCE)
    obj = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(obj)
    return obj


def event(record=1, *, pid=42, name="chatgpt.exe", eid=5157,
          protocol=17, direction="%%14592", dest="224.0.0.251",
          port=5353, at="2026-11-08T10:00:01Z"):
    return (f'<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">'
            f'<System><Provider Name="Microsoft-Windows-Security-Auditing"/>'
            f'<EventID>{eid}</EventID><TimeCreated SystemTime="{at}"/>'
            f'<EventRecordID>{record}</EventRecordID><Channel>Security</Channel></System>'
            f'<EventData><Data Name="ProcessID">{pid}</Data>'
            f'<Data Name="Application">\\device\\harddiskvolume2\\{name}</Data>'
            f'<Data Name="Direction">{direction}</Data>'
            f'<Data Name="DestAddress">{dest}</Data><Data Name="DestPort">{port}</Data>'
            f'<Data Name="Protocol">{protocol}</Data></EventData></Event>')


def envelope(items, **more):
    return {"windowStartUtc": "2026-11-08T10:00:00Z",
            "windowEndUtc": "2026-11-08T10:00:09Z",
            "auditEnabledDuringWindow": True,
            "captureComplete": True, "events": items, **more}


@pytest.mark.parametrize("ip,expected", [
    ("224.0.0.251", "MULTICAST"),
    ("ff02::fb", "MULTICAST"),
    ("255.255.255.255", "BROADCAST"),
    ("127.0.0.1", "LOOPBACK"),
    ("::ffff:127.0.0.1", "LOOPBACK"),
    ("192.168.0.1", "PRIVATE_UNICAST"),
    ("fe80::1", "LINK_LOCAL"),
    ("1.1.1.1", "PUBLIC_UNICAST"),
    ("2606:4700:4700::1111", "PUBLIC_UNICAST"),
    ("bad-address", "UNKNOWN"),
])
def test_exact_address_semantics(ip, expected):
    assert module().address_class(ip) == expected


def test_wfp_native_direction_codes_are_not_reversed():
    ref = module()
    assert ref.decode_event(event(direction="%%14592"))["direction"] == "INBOUND"
    assert ref.decode_event(event(direction="%%14593"))["direction"] == "OUTBOUND"


def test_actual_mdnsv4_v6_blocked_are_not_public_egress():
    ref = module()
    result = ref.summarize(envelope([
        event(1), event(2, dest="ff02::fb"), event(3, dest="224.0.0.251"),
        event(4, dest="ff02::fb")
    ]))
    item = result["perProcess"]["chatgpt.exe"]
    assert result["standing"] == "SAMPLED_EVENTS"
    assert item["NON_OUTBOUND"] == 4
    assert item["BLOCKED_MULTICAST"] == 4
    assert "PUBLIC_UNICAST_CONNECTION_ALLOWED" not in item


def test_real_process_proxy_and_public_connection_are_distinct():
    ref = module()
    result = ref.summarize(envelope([
        event(1, eid=5156, protocol=6, direction="%%14593",
              dest="127.0.0.1", port=19781, name="codex.exe"),
        event(2, eid=5156, protocol=6, direction="%%14593",
              dest="1.1.1.1", port=443, name="codex.exe"),
        event(3, eid=5157, protocol=17, direction="%%14593",
              dest="1.1.1.1", port=443, name="codex.exe"),
    ]))
    item = result["perProcess"]["codex.exe"]
    assert item["PROXY_CONNECTION_ALLOWED"] == 1
    assert item["PUBLIC_UNICAST_CONNECTION_ALLOWED"] == 1
    assert item["BLOCKED_OUTBOUND"] == 1
    assert item["PUBLIC_ADDRESS_EVENTS"] == 2
    assert result["standing"] == "SAMPLED_EVENTS"


def test_empty_or_audit_disabled_remains_unknown():
    ref = module()
    assert ref.summarize(envelope([]))["standing"] == "UNKNOWN"
    assert ref.summarize(envelope([event()], auditEnabledDuringWindow=False))["standing"] == "UNKNOWN"
    assert ref.summarize(envelope([event()], captureComplete=False))["standing"] == "UNKNOWN"


@pytest.mark.parametrize("broken", [
    event(at="2026-11-08T10:10:00Z"),
    event(eid=5158),
    event(record=0),
    "<Event/>",
])
def test_incomplete_or_out_of_scope_event_fails_closed(broken):
    with pytest.raises((ValueError, TypeError)):
        module().summarize(envelope([broken]))


def test_no_raw_ip_pid_or_paths_leak_into_observation():
    ref = module()
    output = json.dumps(ref.summarize(envelope([event()])))
    assert "224.0.0.251" not in output
    assert "harddiskvolume" not in output
    assert "5353" not in output
    assert '"pid"' not in output
