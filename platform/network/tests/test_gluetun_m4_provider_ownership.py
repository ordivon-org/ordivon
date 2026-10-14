from __future__ import annotations
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
M4=ROOT/"capabilities/gluetun/m4-source"

def ini_text(name): return (M4/name).read_text()
def load(rel): return json.loads((ROOT/rel).read_text())

def test_legacy_boot_target_remains_current_and_never_wants_gluetun():
    current=(ROOT/"consumers/browserless/systemd/network-v2-browserless.target").read_text()
    assert "network-v2-browserless-dns.service" in current
    assert "network-v2-browserless-forward.service" in current
    assert "network-v2-browserless-provider-carrier.service" in current
    assert "gluetun" not in current.lower()
    dns=(ROOT/"consumers/browserless/systemd/network-v2-browserless-dns.service").read_text()
    assert "Requires=network-v2-browserless-wireguard.service" in dns

def test_owned_mode_is_explicit_staged_and_cannot_implicitly_stop_legacy():
    ctr=ini_text("network-v2-gluetun-owned.container")
    owned=ini_text("network-v2-gluetun-owned.target")
    assert "sha256:1baa76576dea1dfbafbd62bb635daf40fd87171f63273c2fdfe630418783011e" in ctr
    assert "Pull=never" in ctr
    assert "PublishPort=10.252.246.1:19682:8888/tcp" in ctr
    assert "ConditionPathExists=/etc/network-v2/gluetun/m4-owned-mode.selected" in ctr
    assert "OnFailure=" not in ctr
    assert "Restart=on-failure" in ctr
    assert "provider-identity-exclusive gluetun" in ctr
    assert "Conflicts=network-v2-browserless-wireguard.service" not in ctr
    assert "ConditionPathExists=/etc/network-v2/gluetun/m4-owned-mode.selected" in owned
    assert "OnFailure=" not in owned
    assert "Conflicts=network-v2-browserless" not in owned

def test_provider_modes_split_substrate_from_physical_realization():
    substrate=ini_text("network-v2-browserless.target")
    legacy=ini_text("network-v2-browserless-legacy-provider.target")
    owned=ini_text("network-v2-gluetun-owned.target")
    for token in ("network-v2-browserless-netns.service","network-v2-browserless-forward.service"):
        assert token in substrate
    for token in ("wireguard.service","browserless-dns.service","provider-carrier.service","gluetun"):
        assert token not in substrate
    for token in ("network-v2-browserless-wireguard.service","network-v2-browserless-dns.service","network-v2-browserless-provider-carrier.service"):
        assert token in legacy
    assert "network-v2-gluetun-owned.service" in owned
    assert "network-v2-gluetun-owned-adapter.service" in owned
    assert "WantedBy=multi-user.target" in owned

def test_owned_adapter_preserves_exact_consumer_seam_and_has_no_direct():
    svc=ini_text("network-v2-gluetun-owned-adapter.service")
    cfg=load("consumers/browserless/config/provider-carrier-gluetun-candidate.json")
    assert "NetworkNamespacePath=/run/netns/nv2-browserless-prod" in svc
    assert "BindsTo=network-v2-gluetun-owned.service" in svc
    assert cfg["inbounds"]==[{"type":"http","tag":"shared-provider-carrier","listen":"10.252.246.2","listen_port":19680}]
    assert cfg["outbounds"]==[{"type":"http","tag":"gluetun-upstream","server":"10.252.246.1","server_port":19682}]
    assert not any(o.get("type")=="direct" for o in cfg["outbounds"])

def test_provider_bound_consumers_do_not_start_a_physical_carrier():
    for p in (ROOT/"consumers").rglob("*.service"):
        text=p.read_text()
        if "provider-carrier.service" in text:
            assert p.name=="network-v2-browserless-provider-carrier.service", p
    cases=("claude","chat-ingress","windows-real-chrome")
    for name in cases:
        cfg=load(f"consumers/{name}/config/sing-box.json")
        assert "dns" not in cfg
        assert cfg["outbounds"]==[{"type":"http","tag":"provider-carrier","server":"10.252.246.2","server_port":19680}]

def test_m4_source_has_no_unmediated_direct_except_explicit_legacy_and_finance_macro():
    observed=set()
    for p in (ROOT/"consumers").rglob("*.json"):
        try:v=json.loads(p.read_text())
        except Exception:continue
        if any(o.get("type")=="direct" for o in v.get("outbounds",[])):
            observed.add(str(p.relative_to(ROOT)))
    assert observed=={"consumers/browserless/config/provider-carrier.json","consumers/finance/config/egress.json"}

def test_taskfile_only_stages_m4_and_never_installs_or_starts_it():
    task=(ROOT/"Taskfile.yml").read_text()
    lines=task.splitlines()
    start=lines.index("  capability:gluetun:m4:materialize:")
    end=len(lines)
    for i in range(start+1,len(lines)):
        if lines[i].startswith("  ") and not lines[i].startswith("    "):
            end=i
            break
    block="\n".join(lines[start:end])
    assert "/var/lib/network-v2/m4-stage" in block
    for bad in ("/etc/systemd/system","/etc/containers/systemd","systemctl daemon-reload","systemctl start","systemctl enable","--now"):
        assert bad not in block
    assert "capability:gluetun:m4:validate" in task

def _guard(tmp_path,mode,state):
    b=tmp_path/"bin"; b.mkdir(parents=True)
    sf=tmp_path/"state.json"; sf.write_text(json.dumps(state))
    shim="""#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
s=json.loads(Path(os.environ["S"]).read_text()); n=Path(sys.argv[0]).name; a=sys.argv[1:]
if n=="systemctl":
 u=a[-1]; active=(u=="network-v2-browserless-wireguard.service" and s.get("legacy")) or (u=="network-v2-gluetun-owned.service" and s.get("owned")); raise SystemExit(0 if active else 3)
if n=="ip": raise SystemExit(0 if s.get("wg") else 1)
if n=="podman": raise SystemExit(0 if a[-1] in s.get("containers",[]) else 1)
raise SystemExit(90)
"""
    for n in ("systemctl","ip","podman"):
        f=b/n; f.write_text(shim); f.chmod(0o755)
    marker=tmp_path/"owned-mode.selected"
    if state.get("selector"):
        marker.write_text("owned\n")
    env={**os.environ,"PATH":str(b)+":"+os.environ["PATH"],"S":str(sf),
         "M4_PROVIDER_MODE_MARKER":str(marker)}
    return subprocess.run([str(M4/"provider-identity-exclusive"),mode],env=env,capture_output=True,text=True,check=False)

def test_identity_guard_blocks_dual_physical_session(tmp_path):
    assert _guard(tmp_path/"a","gluetun",{"selector":True}).returncode==0
    assert _guard(tmp_path/"b","gluetun",{"selector":True,"legacy":True}).returncode==42
    assert _guard(tmp_path/"c","gluetun",{"selector":True,"wg":True}).returncode==42
    assert _guard(tmp_path/"d","legacy",{}).returncode==0
    assert _guard(tmp_path/"d2","legacy",{"selector":True}).returncode==42
    assert _guard(tmp_path/"e","legacy",{"owned":True}).returncode==42
    assert _guard(tmp_path/"f","legacy",{"containers":["network-v2-gluetun-owned-r1"]}).returncode==42
