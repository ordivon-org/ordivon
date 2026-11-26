"""Guard Gluetun official HTTP control against unapproved/unknown actions."""
import importlib.util
from pathlib import Path
import sys
import pytest

DIR=Path(__file__).resolve().parents[1]/"providers/gluetun"
sys.path.insert(0,str(DIR))
spec=importlib.util.spec_from_file_location("gluetun_switch",DIR/"native_switch.py")
switch=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=switch
spec.loader.exec_module(switch)

def test_patch_must_be_provider_native_and_permitted():
    x=switch.country_patch("Japan",{"Japan","Croatia"})
    assert x == {"provider":{"server_selection":{"countries":["Japan"]}}}
    for name in ("Hong Kong","Not In Catalog",""):
        with pytest.raises(ValueError):
            switch.country_patch(name,{"Japan","Hong Kong","Croatia"})

def test_snapshot_requires_active_wireguard_surfshark_and_bounded_countries():
    model={"type":"wireguard","provider":{"name":"surfshark",
      "server_selection":{"countries":["Japan","Croatia"],"regions":[],"cities":[],"hostnames":[]}}}
    assert switch.selected_snapshot(model,{"Japan","Croatia"})["countries"]==["Japan","Croatia"]
    # Physical upstream authenticated GET normalizes all configured names.
    lower={**model,"provider":{**model["provider"],"server_selection":{
      **model["provider"]["server_selection"],"countries":["japan","croatia"]}}}
    assert switch.selected_snapshot(lower,{"Japan","Croatia"})["countries"]==["Japan","Croatia"]
    mixed={**model,"provider":{**model["provider"],"server_selection":{
      **model["provider"]["server_selection"],"countries":["JaPaN","croatia"]}}}
    assert switch.selected_snapshot(mixed,{"Japan","Croatia"})["countries"]==["Japan","Croatia"]
    variants=[
      ({"type":"openvpn"},"different_vpn"),
      ({"provider":{"name":"other"}},"provider"),
      ({"provider":{"server_selection":{"countries":["Hong Kong"]}}},"forbidden"),
      ({"provider":{"server_selection":{"countries":[]}}},"empty"),
      ({"provider":{"server_selection":{"countries":["Japan","Japan"]}}},"duplicate"),
      ({"provider":{"server_selection":{"regions":["Asia Pacific"]}}},"region"),
    ]
    for updates,_ in variants:
        x={**model,"provider":{**model["provider"],"server_selection":{**model["provider"]["server_selection"]}}}
        for key, value in updates.items():
            if key=="provider":
                x["provider"].update({k:v for k,v in value.items() if k!="server_selection"})
                if "server_selection" in value:
                    x["provider"]["server_selection"].update(value["server_selection"])
            else:x[key]=value
        with pytest.raises(ValueError):
            switch.selected_snapshot(x,{"Japan","Croatia"})

def test_current_healthy_never_authorizes_switch(monkeypatch):
    class NoApi:
        pass
    monkeypatch.setattr(switch.quality,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(switch.quality,"observe",
        lambda hours: {"recommended":{"decision":"HOLD_WORKING_ACTIVE","trialCountry":None}})
    monkeypatch.setattr(switch,"api_call",lambda *a,**kw: (_ for _ in ()).throw(AssertionError("API should not be called")))
    assert switch.guarded_recover()["standing"]=="HOLD_WORKING_ACTIVE"


def test_api_roundtrip_sanitizes_secret_and_requires_key(monkeypatch,capsys):
    from http.server import BaseHTTPRequestHandler,HTTPServer
    from io import StringIO
    import json,threading
    seen=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.headers.get("X-API-Key")!="synthetic-test-key":
                self.send_response(401);self.end_headers();return
            self.send_response(200);self.end_headers()
            self.wfile.write(json.dumps({
                "type":"wireguard",
                "provider":{"name":"surfshark","server_selection":{"countries":["Japan"],"regions":[]}},
                "wireguard":{"private_key":"NEVER_PRINT_THIS_KEY"}
            }).encode())
        def do_PUT(self):
            payload=self.rfile.read(int(self.headers.get("Content-Length","0")))
            seen.append(json.loads(payload))
            self.send_response(200);self.end_headers()
            self.wfile.write(b"settings updated")
    server=HTTPServer(("127.0.0.1",0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        monkeypatch.setattr(switch,"API_URL",f"http://127.0.0.1:{server.server_port}/v1/vpn/settings")
        monkeypatch.setattr(switch,"protected_key",lambda:"synthetic-test-key")
        assert switch.internal_http("GET")==0
        result=capsys.readouterr().out
        assert "NEVER_PRINT_THIS_KEY" not in result
        safe=json.loads(result)
        assert safe["provider"]["server_selection"]["countries"]==["Japan"]
        patch=switch.country_patch("Croatia",{"Croatia","Japan"})
        monkeypatch.setattr(sys,"stdin",StringIO(json.dumps(patch)))
        assert switch.internal_http("PUT")==0
        capsys.readouterr()
        assert seen==[patch]
    finally:server.shutdown();server.server_close()


def test_cooldown_state_roundtrip(monkeypatch,tmp_path):
    f=tmp_path/"last"
    monkeypatch.setattr(switch,"LAST_SWITCH",f)
    assert switch.last_attempt() is None
    switch.mark_attempt()
    assert switch.last_attempt() is not None
    assert not (f.stat().st_mode&0o077)


def test_guarded_native_switch_success_only_after_real_consumer_receipt(monkeypatch):
    from datetime import datetime,timezone
    calls=[]
    before={"type":"wireguard","provider":{"name":"surfshark",
        "server_selection":{"countries":["Singapore"],"regions":[],"cities":[],"hostnames":[]}}}
    after={"type":"wireguard","provider":{"name":"surfshark",
        "server_selection":{"countries":["Japan"],"regions":[],"cities":[],"hostnames":[]}}}
    active=[{"standing":"NOT_QUALIFIED"},
            {"standing":"QUALIFIED_ACTIVE_SAMPLE","currentCatalogCountry":"Japan"}]
    monkeypatch.setattr(switch.quality,"observe",lambda hours:{
        "recommended":{"decision":"TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF",
                       "trialCountry":"Japan"}})
    monkeypatch.setattr(switch.quality,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(switch,"initial_preflight",lambda:{"standing":"NATIVE_API_AUTHORIZED_READONLY"})
    monkeypatch.setattr(switch,"last_attempt",lambda:None)
    monkeypatch.setattr(switch,"mark_attempt",lambda:None)
    monkeypatch.setattr(switch,"bounded_consumer_observe",lambda seconds=25:active.pop(0))
    monkeypatch.setattr(switch.time,"monotonic",lambda:100.0)
    def api(method,payload=None):
        calls.append((method,payload))
        if method=="GET":
            return before if len([c for c in calls if c[0]=="GET"])==1 else after
        return {"status":200,"outcome":"settings updated"}
    monkeypatch.setattr(switch,"api_call",api)
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_CONSUMED"
    assert result["country"]=="Japan"
    assert [c for c in calls if c[0]=="PUT"]==[
        ("PUT",{"provider":{"server_selection":{"countries":["Japan"]}}})]


def test_guarded_native_switch_rolls_back_if_trial_never_qualifies(monkeypatch):
    calls=[]
    before={"type":"wireguard","provider":{"name":"surfshark",
        "server_selection":{"countries":["Singapore"],"regions":[]}}}
    after={"type":"wireguard","provider":{"name":"surfshark",
        "server_selection":{"countries":["Japan"],"regions":[]}}}
    monkeypatch.setattr(switch.quality,"observe",lambda hours:{
        "recommended":{"decision":"TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF",
                       "trialCountry":"Japan"}})
    monkeypatch.setattr(switch.quality,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(switch,"initial_preflight",lambda:{})
    monkeypatch.setattr(switch,"last_attempt",lambda:None)
    monkeypatch.setattr(switch,"mark_attempt",lambda:None)
    monkeypatch.setattr(switch,"bounded_consumer_observe",lambda seconds=25:{"standing":"NOT_QUALIFIED"})
    monkeypatch.setattr(switch.time,"monotonic",
                        iter((100.0,100.0,100.0,200.0)).__next__)
    def api(method,payload=None):
        calls.append((method,payload))
        if method=="GET":
            return before if len([c for c in calls if c[0]=="GET"]) in (1,3) else after
        return {"status":200}
    monkeypatch.setattr(switch,"api_call",api)
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_FAILED"
    assert result["rollback"]=="SELECTION_READBACK_VERIFIED"
    assert [c[1] for c in calls if c[0]=="PUT"]==[
        {"provider":{"server_selection":{"countries":["Japan"]}}},
        {"provider":{"server_selection":{"countries":["Singapore"]}}},
    ]


def test_recover_benign_policy_hold_is_process_success_but_auth_unknown_is_failure(monkeypatch,capsys,tmp_path):
    # Non-root GitHub CI must never open the production /run lock path.
    monkeypatch.setattr(switch,"LOCK",tmp_path/"native-recover.lock")
    monkeypatch.setattr(sys,"argv",["native_switch.py","--recover"])
    monkeypatch.setattr(switch,"guarded_recover",
      lambda:{"standing":"HOLD_WORKING_ACTIVE","effectAttempted":False})
    assert switch.main()==0
    assert "HOLD_WORKING_ACTIVE" in capsys.readouterr().out
    monkeypatch.setattr(switch,"guarded_recover",
      lambda:{"standing":"HOLD_NATIVE_API_NOT_READY","effectAttempted":False})
    assert switch.main()==1
    assert "HOLD_NATIVE_API_NOT_READY" in capsys.readouterr().out
    monkeypatch.setattr(switch,"guarded_recover",
      lambda:{"standing":"NATIVE_SWITCH_FAILED","effectAttempted":True})
    assert switch.main()==1
    monkeypatch.setattr(switch,"guarded_recover",
      lambda:{"standing":"NATIVE_SWITCH_RESTART_CONSUMED",
              "effectAttempted":True,"recoveryProved":True})
    assert switch.main()==0

def test_systemd_health_gate_does_not_collect_full_history_when_green(monkeypatch):
    monkeypatch.setattr(switch.quality, "recent_failure_witness", lambda now: False)
    monkeypatch.setattr(switch, "native_health_state", lambda: True)
    monkeypatch.setattr(switch.quality, "observe",
        lambda **kw: (_ for _ in ()).throw(AssertionError("history should not load")))
    monkeypatch.setattr(switch, "api_call",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("API should not open")))
    result=switch.guarded_recover()
    assert result["standing"] == "HOLD_CONSUMER_HEALTHY_OR_PARTIAL"
    assert result["effectAttempted"] is False


def test_systemd_blackbox_missing_is_hold_unknown_not_vpn_failure(monkeypatch):
    monkeypatch.setattr(switch.quality, "recent_failure_witness",
        lambda now: (_ for _ in ()).throw(OSError("PROMETHEUS_TEMPORARILY_DOWN")))
    monkeypatch.setattr(switch.quality, "observe",
        lambda **kw: (_ for _ in ()).throw(AssertionError("history should not load")))
    monkeypatch.setattr(switch, "api_call",
        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("API should not open")))
    result=switch.guarded_recover()
    assert result["standing"] == "HOLD_CONSUMER_OBSERVATION_UNKNOWN"
    assert result["effectAttempted"] is False


def test_recovery_next_distinct_historical_country_after_first_fails(monkeypatch):
    calls=[]
    original={"type":"wireguard","provider":{"name":"surfshark",
      "server_selection":{"countries":["Malaysia"],"regions":[]}}}
    first={"type":"wireguard","provider":{"name":"surfshark",
      "server_selection":{"countries":["Singapore"],"regions":[]}}}
    second={"type":"wireguard","provider":{"name":"surfshark",
      "server_selection":{"countries":["Japan"],"regions":[]}}}
    selection=[original]
    monkeypatch.setattr(switch.quality,"observe",lambda hours:{
        "recommended":{"decision":"TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF",
          "trialCountry":"Singapore","trialCountries":["Singapore","Japan"]}})
    monkeypatch.setattr(switch.quality,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(switch,"initial_preflight",lambda:{})
    monkeypatch.setattr(switch,"last_attempt",lambda:None)
    monkeypatch.setattr(switch,"mark_attempt",lambda:None)
    monkeypatch.setattr(switch,"bounded_consumer_observe",
        lambda seconds=25:{"standing":"QUALIFIED_ACTIVE_SAMPLE","currentCatalogCountry":"Japan"}
              if len([c for c in calls if c[0]=="PUT"])>=2
              else {"standing":"NOT_QUALIFIED"})
    # First trial passes readback but fails the consumer timeout. Second
    # remains within the original one-shot, and passes real consumer proof.
    monkeypatch.setattr(switch.time,"monotonic",
        iter((100.0,100.0,100.0,160.0,160.0,160.0,170.0,172.0)).__next__)
    def api(method,payload=None):
        calls.append((method,payload))
        if method=="GET":return selection[0]
        country=payload["provider"]["server_selection"]["countries"][0]
        selection[0] = first if country=="Singapore" else second
        return {"status":200}
    monkeypatch.setattr(switch,"api_call",api)
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_CONSUMED"
    assert result["country"]=="Japan"
    assert result["countriesTried"]==["Singapore","Japan"]
    assert [c[1]["provider"]["server_selection"]["countries"] for c in calls if c[0]=="PUT"]==[
        ["Singapore"],["Japan"]]


def test_bounded_consumer_probe_timeout_is_unknown_and_not_success(monkeypatch):
    import subprocess
    def timeout(*args,**kw):
        assert kw["timeout"] in (20,25)
        raise subprocess.TimeoutExpired(cmd=args[0],timeout=kw["timeout"])
    monkeypatch.setattr(switch.subprocess,"run",timeout)
    assert switch.bounded_consumer_observe(20)["standing"]=="UNKNOWN_BOUNDED_CONSUMER_OBSERVATION"


def test_expired_quality_plus_native_catalog_cold_candidates_reaches_second_business_success(monkeypatch):
    """Integrated policy -> official catalog -> 2 tried API candidates -> origin acceptance.

    All API and physical effects are fixtures; this never changes production.
    """
    import json
    from itertools import count
    class Result:
        returncode=0
        def __init__(self,text): self.stdout=text
    stored=json.dumps({"surfshark":{"servers":[
        {"country":"Malaysia","vpn":"wireguard","ips":["192.0.2.1"]},
        {"country":"Singapore","vpn":"wireguard","ips":["192.0.2.2"]},
        {"country":"Japan","vpn":"wireguard","ips":["192.0.2.3"]},
        {"country":"Hong Kong","vpn":"wireguard","ips":["192.0.2.4"]},
    ]}})
    def native_run(args,**kw):
        if args[:2]==["/usr/bin/podman","exec"]: return Result(stored)
        if args[0]=="/usr/bin/journalctl": return Result("")
        if args[0]=="/usr/bin/curl":return Result("200")
        raise AssertionError("Unexpected external subprocess")
    monkeypatch.setattr(switch.quality.subprocess,"run",native_run)
    monkeypatch.setattr(switch.quality,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(switch.quality,"current_catalog_country",lambda catalog:"Malaysia")
    # The previous verified quality hint has expired and grants no quality.
    monkeypatch.setattr(switch.quality,"source_trial_hints",lambda *a,**kw:[])
    monkeypatch.setattr(switch,"initial_preflight",lambda:{"standing":"NATIVE_API_AUTHORIZED_READONLY"})
    monkeypatch.setattr(switch,"last_attempt",lambda:None)
    monkeypatch.setattr(switch,"mark_attempt",lambda:None)
    selection=["Malaysia"]
    puts=[]
    def api(method,payload=None):
        if method=="PUT":
            chosen=payload["provider"]["server_selection"]["countries"]
            puts.append(chosen)
            selection[:]=chosen
            return {"status":200}
        return {"type":"wireguard","provider":{"name":"surfshark",
            "server_selection":{"countries":selection[:],"regions":[]}}}
    monkeypatch.setattr(switch,"api_call",api)
    def consumer(seconds=25):
        return {"standing":"QUALIFIED_ACTIVE_SAMPLE","currentCatalogCountry":"Japan"} if (
            len(puts)>1) else {"standing":"NOT_QUALIFIED"}
    monkeypatch.setattr(switch,"bounded_consumer_observe",consumer)
    monkeypatch.setattr(switch.time,"monotonic",count(start=0,step=10).__next__)
    monkeypatch.setattr(switch.time,"sleep",lambda s:None)
    outcome=switch.guarded_recover()
    assert puts==[["Singapore"],["Japan"]]
    assert outcome["standing"]=="NATIVE_SWITCH_CONSUMED"
    assert outcome["country"]=="Japan"
    assert outcome["countriesTried"]==["Singapore","Japan"]
    assert outcome["effectAttempted"] is True
    assert selection==["Japan"]


def test_catalog_cold_preference_never_overrides_shared_underlay_failure(monkeypatch):
    """The verified physical outage must not cause a futile country switch."""
    import json
    class Result:
        returncode=28
        def __init__(self,text):self.stdout=text
    catalog=json.dumps({"surfshark":{"servers":[
        {"vpn":"wireguard","country":"Singapore","ips":["192.0.2.2"]},
    ]}})
    def native_run(args,**kw):
        if args[:2]==["/usr/bin/podman","exec"]:return Result(catalog)
        if args[0]=="/usr/bin/journalctl":return Result("")
        if args[0]=="/usr/bin/curl":return Result("")
        raise AssertionError("Unexpected subprocess")
    monkeypatch.setattr(switch.quality.subprocess,"run",native_run)
    monkeypatch.setattr(switch.quality,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(switch.quality,"source_trial_hints",
        lambda *a,**kw: (_ for _ in ()).throw(AssertionError("Must not read hints when WAN fails")))
    monkeypatch.setattr(switch.quality,"catalog_cold_trials",
        lambda *a,**kw: (_ for _ in ()).throw(AssertionError("No cold catalog reads when WAN fails")))
    monkeypatch.setattr(switch.quality,"current_catalog_country",lambda x:"Malaysia")
    monkeypatch.setattr(switch,"api_call",
        lambda *a,**kw: (_ for _ in ()).throw(AssertionError("No API may be opened")))
    result=switch.guarded_recover()
    assert result["standing"]=="HOLD_SHARED_UNDERLAY_OR_UNKNOWN"
    assert result["effectAttempted"] is False


def test_partial_consumer_native_health_stuck_restarts_only_existing_service(monkeypatch):
    # Production counterexample 2026-11-15: three consumer jobs still had
    # healthy samples, while native Gluetun health was 500 and mobile failed.
    import subprocess
    from types import SimpleNamespace
    calls = []
    states = iter([False, False, False, True])
    monkeypatch.setattr(switch.quality, "recent_failure_witness", lambda now: False)
    monkeypatch.setattr(switch, "native_health_state", lambda: next(states), raising=False)
    monkeypatch.setattr(switch.quality, "direct_underlay_witness", lambda: True)
    monkeypatch.setattr(switch, "last_attempt", lambda: None)
    monkeypatch.setattr(switch, "mark_attempt", lambda: calls.append("cooldown"))
    monkeypatch.setattr(switch.time, "sleep", lambda sec: None)
    monkeypatch.setattr(switch, "bounded_consumer_observe", lambda seconds=25: {
        "standing": "QUALIFIED_ACTIVE_SAMPLE"
    })
    def native_run(args, **kwargs):
        calls.append(tuple(args))
        assert args == ["/usr/bin/systemctl", "restart", "network-v2-gluetun-owned.service"]
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(switch.subprocess, "run", native_run)
    result = switch.guarded_recover()
    assert result["standing"] == "NATIVE_HEALTH_RESTART_CONSUMED"
    assert result["effectAttempted"] is True
    assert calls == ["cooldown", (
        "/usr/bin/systemctl", "restart", "network-v2-gluetun-owned.service"
    )]


def test_native_health_one_bad_sample_does_not_restart(monkeypatch):
    calls = iter([False, True])
    monkeypatch.setattr(switch.quality, "recent_failure_witness", lambda now: False)
    monkeypatch.setattr(switch, "native_health_state", lambda: next(calls), raising=False)
    monkeypatch.setattr(switch, "last_attempt", lambda: None)
    monkeypatch.setattr(switch.subprocess, "run", lambda *a, **kw:
                        (_ for _ in ()).throw(AssertionError("unexpected restart")))
    assert switch.guarded_recover()["effectAttempted"] is False


@pytest.mark.parametrize("underlay", [False, None])
def test_native_health_bad_but_underlay_not_proven_never_restarts(monkeypatch, underlay):
    monkeypatch.setattr(switch.quality, "recent_failure_witness", lambda now: False)
    monkeypatch.setattr(switch, "native_health_state", lambda: False, raising=False)
    monkeypatch.setattr(switch, "last_attempt", lambda: None)
    monkeypatch.setattr(switch.quality, "direct_underlay_witness", lambda: underlay)
    monkeypatch.setattr(switch.time, "sleep", lambda sec: None)
    monkeypatch.setattr(switch.subprocess, "run", lambda *a, **kw:
                        (_ for _ in ()).throw(AssertionError("unexpected restart")))
    result = switch.guarded_recover()
    assert result["standing"] == "HOLD_NATIVE_HEALTH_UNDERLAY_UNKNOWN_OR_DOWN"
    assert result["effectAttempted"] is False


def test_native_health_bad_but_cooldown_blocks_restart(monkeypatch):
    from datetime import datetime, timezone
    monkeypatch.setattr(switch.quality, "recent_failure_witness", lambda now: False)
    monkeypatch.setattr(switch, "native_health_state", lambda: False, raising=False)
    monkeypatch.setattr(switch, "last_attempt", lambda: datetime.now(timezone.utc))
    monkeypatch.setattr(switch.subprocess, "run", lambda *a, **kw:
                        (_ for _ in ()).throw(AssertionError("unexpected restart")))
    result = switch.guarded_recover()
    assert result["standing"] == "HOLD_COOLDOWN"
    assert result["effectAttempted"] is False


def test_native_health_unknown_does_not_restart(monkeypatch):
    monkeypatch.setattr(switch.quality, "recent_failure_witness", lambda now: False)
    monkeypatch.setattr(switch, "native_health_state", lambda: None, raising=False)
    monkeypatch.setattr(switch.subprocess, "run", lambda *a, **kw:
                        (_ for _ in ()).throw(AssertionError("unexpected restart")))
    result = switch.guarded_recover()
    assert result["standing"] == "HOLD_NATIVE_HEALTH_UNKNOWN"
    assert result["effectAttempted"] is False


@pytest.mark.parametrize("returncode,output,expected", [
    (0, "", True),
    (1, "ERROR HTTP response status is not OK: 500 500 Internal Server Error", False),
    (125, "Error: container exited", None),
    (1, "some unrecognized native failure", None),
])
def test_native_health_only_classifies_official_500(monkeypatch, returncode, output, expected):
    import subprocess
    def fake_run(args, **kwargs):
        assert args == ["/usr/bin/podman", "exec",
                        "network-v2-gluetun-owned-r1", "/gluetun-entrypoint", "healthcheck"]
        return subprocess.CompletedProcess(args, returncode, "", output)
    monkeypatch.setattr(switch.subprocess, "run", fake_run)
    assert switch.native_health_state() is expected


def test_native_health_restart_failure_is_effect_unknown_and_bounded(monkeypatch):
    import subprocess
    states=iter([False, False, False])
    monkeypatch.setattr(switch.quality, "recent_failure_witness", lambda now: False)
    monkeypatch.setattr(switch, "native_health_state", lambda: next(states), raising=False)
    monkeypatch.setattr(switch.quality, "direct_underlay_witness", lambda: True)
    monkeypatch.setattr(switch, "last_attempt", lambda: None)
    monkeypatch.setattr(switch, "mark_attempt", lambda: None)
    monkeypatch.setattr(switch.time, "sleep", lambda sec: None)
    def fail_restart(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 70)
    monkeypatch.setattr(switch.subprocess, "run", fail_restart)
    result=switch.guarded_recover()
    assert result["standing"] == "NATIVE_HEALTH_RESTART_UNQUALIFIED"
    assert result["effectAttempted"] is True


# 2026-11-15 real consumer incident: three native country trials returned
# TRIAL_UNKNOWN/rollback UNKNOWN_OR_FAILED while two host-direct origins
# remained reachable, and all scoped Claude/Codex/PyPI consumers failed.
def _failed_native_api_scenario(monkeypatch, *, direct=True, recovered=False,
                                restart_timeout=False, unknown=False):
    import subprocess
    before={"type":"wireguard","provider":{"name":"surfshark",
             "server_selection":{"countries":["Malaysia"],"regions":[]}}}
    effects=[]
    monkeypatch.setattr(switch.quality, "recent_failure_witness", lambda now: True)
    monkeypatch.setattr(switch.quality, "observe", lambda hours: {
        "recommended":{"decision":"TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF",
                       "trialCountry":"Singapore",
                       "trialCountries":["Singapore"]}})
    monkeypatch.setattr(switch.quality, "direct_underlay_witness", lambda: direct)
    monkeypatch.setattr(switch, "initial_preflight", lambda: {"standing":"NATIVE_API_AUTHORIZED_READONLY"})
    monkeypatch.setattr(switch, "last_attempt", lambda: None)
    monkeypatch.setattr(switch, "mark_attempt", lambda: effects.append("cooldown"))
    monkeypatch.setattr(switch.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(switch, "native_health_state", lambda: True)
    def api(method, payload=None):
        if method=="GET":
            return before
        effects.append("native_api_put_unknown")
        raise ValueError("NATIVE_API_UNKNOWN")
    monkeypatch.setattr(switch, "api_call", api)
    observations=[]
    def consumer(seconds=25):
        observations.append(seconds)
        if unknown:
            return {"standing":"UNKNOWN_BOUNDED_CONSUMER_OBSERVATION"}
        if "restart" in effects or (recovered and len(observations) >= 2):
            return {"standing":"QUALIFIED_ACTIVE_SAMPLE",
                    "currentCatalogCountry":"Malaysia"}
        return {"standing":"NOT_QUALIFIED"}
    monkeypatch.setattr(switch, "bounded_consumer_observe", consumer)
    def native_run(args, **kwargs):
        assert args == ["/usr/bin/systemctl","restart","network-v2-gluetun-owned.service"]
        effects.append("restart")
        if restart_timeout:
            raise subprocess.TimeoutExpired(args, kwargs.get("timeout", 60))
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(switch.subprocess, "run", native_run)
    return effects


def test_api_trial_and_rollback_unknown_recovers_via_single_native_restart(monkeypatch):
    effects=_failed_native_api_scenario(monkeypatch)
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_RESTART_CONSUMED"
    assert result["effectAttempted"] is True
    assert result["recoveryProved"] is True
    assert effects.count("restart")==1
    assert effects.count("cooldown")==1
    assert effects.count("native_api_put_unknown")==2
    assert result["trials"][0]["failureStage"]=="PUT"


@pytest.mark.parametrize("direct", [False, None])
def test_api_trial_failed_but_direct_underlay_not_proven_never_restarts(monkeypatch,direct):
    effects=_failed_native_api_scenario(monkeypatch,direct=direct)
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_FAILED"
    assert result["effectAttempted"] is True
    assert effects.count("restart")==0


def test_api_trial_unknown_but_consumer_recovered_does_not_restart(monkeypatch):
    effects=_failed_native_api_scenario(monkeypatch,recovered=True)
    result=switch.guarded_recover()
    assert result["effectAttempted"] is True
    assert effects.count("restart")==0


def test_api_trial_unknown_restart_timeout_is_not_proved(monkeypatch):
    effects=_failed_native_api_scenario(monkeypatch,restart_timeout=True)
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_RESTART_UNQUALIFIED"
    assert result["effectAttempted"] is True
    assert result["recoveryProved"] is False
    assert effects.count("restart")==1


def test_api_trial_fallback_outside_budget_is_skipped(monkeypatch):
    effects=_failed_native_api_scenario(monkeypatch)
    ticks=iter([0.0,0.0,0.0,180.0])
    monkeypatch.setattr(switch.time,"monotonic",lambda: next(ticks))
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_FAILED"
    assert effects.count("restart")==0


def test_api_trial_unknown_consumer_observation_does_not_authorize_restart(monkeypatch):
    """UNKNOWN is not a failed business receipt, even with old failure samples."""
    effects = _failed_native_api_scenario(monkeypatch, unknown=True)
    result = switch.guarded_recover()
    assert result["standing"] == "NATIVE_SWITCH_FAILED"
    assert result["effectAttempted"] is True  # Original API PUT was attempted.
    assert effects.count("restart") == 0


def test_native_subprocess_paths_remain_on_loaded_generation(tmp_path, monkeypatch):
    import json
    import os
    import shutil
    from types import SimpleNamespace

    a, b = tmp_path / "a", tmp_path / "b"
    shutil.copytree(DIR, a, ignore=shutil.ignore_patterns("__pycache__", ".venv"))
    shutil.copytree(DIR, b, ignore=shutil.ignore_patterns("__pycache__", ".venv"))
    active = tmp_path / "active"
    active.symlink_to(a, target_is_directory=True)
    spec = importlib.util.spec_from_file_location("generation_switch", active / "native_switch.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    next_link = tmp_path / "next"
    next_link.symlink_to(b, target_is_directory=True)
    os.replace(next_link, active)
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout=json.dumps({"standing":"READONLY"}))
    monkeypatch.setattr(loaded.subprocess, "run", fake_run)
    monkeypatch.setattr(loaded, "container_pid", lambda:"42")
    loaded.api_call("GET")
    monkeypatch.setattr(loaded, "protected_key", lambda:"synthetic")
    monkeypatch.setattr(loaded.native, "read_selector_policy", lambda:{"selectedCountries":["Japan"]})
    monkeypatch.setattr(loaded, "api_call", lambda method:{"type":"wireguard","provider":{"name":"surfshark","server_selection":{"countries":["Japan"]}}})
    loaded.initial_preflight()
    loaded.bounded_consumer_observe()
    children = [next(Path(x) for x in cmd if str(x).endswith(".py")) for cmd in calls]
    assert children == [a/"native_switch.py", a/"native_profile.py", a/"observe_active.py"]


@pytest.mark.parametrize("raw", [None, [], {"type":"wireguard","provider":[]},
    {"type":"wireguard","provider":{"name":"surfshark","server_selection":None}},
    {"type":"wireguard","provider":{"name":"surfshark","server_selection":{"countries":["Japan"],"regions":0}}}])
def test_malformed_native_selection_is_explicit_contract_rejection(raw):
    with pytest.raises(ValueError):
        switch.selected_snapshot(raw, {"Japan"})


@pytest.mark.parametrize("raw", [[], {"type":"wireguard","provider":[]},
    {"type":"wireguard","provider":{"name":"surfshark","server_selection":None}}])
def test_native_get_malformed_response_returns_unknown_receipt(monkeypatch, capsys, raw):
    import json
    from types import SimpleNamespace
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,*args): return json.dumps(raw).encode()
    monkeypatch.setattr(switch,"protected_key",lambda:"synthetic-test-key")
    monkeypatch.setattr(switch.urllib.request,"build_opener",
                        lambda *a:SimpleNamespace(open=lambda *a,**kw:Response()))
    assert switch.internal_http("GET") != 0
    assert json.loads(capsys.readouterr().out)["standing"] == "NATIVE_API_UNKNOWN"
