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
