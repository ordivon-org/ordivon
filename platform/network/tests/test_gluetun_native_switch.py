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
        "server_selection":{"countries":["North Macedonia"],"regions":[],"cities":[],"hostnames":[]}}}
    after={"type":"wireguard","provider":{"name":"surfshark",
        "server_selection":{"countries":["Mexico"],"regions":[],"cities":[],"hostnames":[]}}}
    active=[{"standing":"NOT_QUALIFIED"},
            {"standing":"QUALIFIED_ACTIVE_SAMPLE","currentCatalogCountry":"Mexico"}]
    monkeypatch.setattr(switch.quality,"observe",lambda hours:{
        "recommended":{"decision":"TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF",
                       "trialCountry":"Mexico"}})
    monkeypatch.setattr(switch.quality,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(switch,"initial_preflight",lambda:{"standing":"NATIVE_API_AUTHORIZED_READONLY"})
    monkeypatch.setattr(switch,"last_attempt",lambda:None)
    monkeypatch.setattr(switch,"mark_attempt",lambda:None)
    monkeypatch.setattr(switch.observer,"observe",lambda:active.pop(0))
    monkeypatch.setattr(switch.time,"monotonic",lambda:100.0)
    def api(method,payload=None):
        calls.append((method,payload))
        if method=="GET":
            return before if len([c for c in calls if c[0]=="GET"])==1 else after
        return {"status":200,"outcome":"settings updated"}
    monkeypatch.setattr(switch,"api_call",api)
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_CONSUMED"
    assert result["country"]=="Mexico"
    assert [c for c in calls if c[0]=="PUT"]==[
        ("PUT",{"provider":{"server_selection":{"countries":["Mexico"]}}})]


def test_guarded_native_switch_rolls_back_if_trial_never_qualifies(monkeypatch):
    calls=[]
    before={"type":"wireguard","provider":{"name":"surfshark",
        "server_selection":{"countries":["North Macedonia"],"regions":[]}}}
    after={"type":"wireguard","provider":{"name":"surfshark",
        "server_selection":{"countries":["Mexico"],"regions":[]}}}
    monkeypatch.setattr(switch.quality,"observe",lambda hours:{
        "recommended":{"decision":"TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF",
                       "trialCountry":"Mexico"}})
    monkeypatch.setattr(switch.quality,"recent_failure_witness",lambda now:True)
    monkeypatch.setattr(switch,"initial_preflight",lambda:{})
    monkeypatch.setattr(switch,"last_attempt",lambda:None)
    monkeypatch.setattr(switch,"mark_attempt",lambda:None)
    monkeypatch.setattr(switch.observer,"observe",lambda:{"standing":"NOT_QUALIFIED"})
    monkeypatch.setattr(switch.time,"monotonic",iter((100.0,200.0)).__next__)
    def api(method,payload=None):
        calls.append((method,payload))
        if method=="GET":
            return before if len([c for c in calls if c[0]=="GET"])==1 else after
        return {"status":200}
    monkeypatch.setattr(switch,"api_call",api)
    result=switch.guarded_recover()
    assert result["standing"]=="NATIVE_SWITCH_FAILED"
    assert result["rollback"]=="REQUESTED"
    assert [c[1] for c in calls if c[0]=="PUT"]==[
        {"provider":{"server_selection":{"countries":["Mexico"]}}},
        {"provider":{"server_selection":{"countries":["North Macedonia"]}}},
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
