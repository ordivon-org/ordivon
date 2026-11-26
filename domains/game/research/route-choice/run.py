"""Native fork search and full scene replay, with private source staging."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[1]
SOURCE=GAME/"examples/room-encounter"
sys.path.insert(0,str(GAME/"scripts"))
from native_process import verify_process
from rendered_product_acceptance import require,digest

ORIGINAL=("encounter_rules.gd","encounter_tuning.gd","configs/default.tres",
          "configs/tactical_trial.tres","room_theme.tres","export_presets.cfg")
LOCAL=("route_rules.gd","route_scene.gd","main.tscn","route_probe.gd")
ROUTES={"direct":[1,3,4],"gradual":[1,2,2,3]}

def inputs():
    return {**{SOURCE/f:f for f in ORIGINAL},
            **{HERE/f:f for f in LOCAL},
            HERE.parent/"mechanic-search/native_search.gd":"native_search.gd"}

def stage(root):
    for src,dst in inputs().items():
        p=root/dst;p.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,p)
    (root/"project.godot").write_text('config_version=5\n[application]\nconfig/name="Room Encounter"\nrun/main_scene="res://main.tscn"\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="OrdivonRoomRoute/R22"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\nenvironment/defaults/default_clear_color=Color(0.045, 0.073, 0.105, 1)\n')
    # Do not export the private search/probe script into the playable product.
    p=root/"export_presets.cfg"
    p.write_text(p.read_text().replace('exclude_filter="assert.gd,assert_process_restart.gd,agent_episode.gd,narrative/acceptance.gd"', 'exclude_filter="route_probe.gd,native_search.gd"'))

def native(*args,timeout=60):
    r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    verify_process(r.returncode,r.stdout,r.stderr)
    return r.stdout

def validate(rows):
    require([r["route"] for r in rows]==list(ROUTES),"route inventory")
    for r in rows:
        route=r["route"]; rooms=ROUTES[route]
        require(r["rooms"]==rooms and sum(rooms)==8,"route representation")
        exact,reduced=r["exact"],r["reduced"]
        for k,x in (("exact",exact),("reduced",reduced)):
            require(x["exact"] is (k=="exact") and x["horizon"]==48 and 0<x["states"]<=100000
                    and x["transitions"]>=x["states"]-1,"bounded search")
        sig=lambda x:[(p["health"],p["actions"]) for p in x["frontier"]]
        require(sig(exact)==sig(reduced) and bool(exact["frontier"]),"frontier mismatch")
        w=exact["frontier"][-1]; path=w["path"].copy();path[path.index("advance")]=route
        require(r["witness"]==path and len(path)==w["actions"] and path.count(route)==1
                and set(path)<={"attack","guard","advance",route},"route witness")
        f=r["fork"];b,a=f["before"],f["after"]
        require(f["state_events"]==1 and b["route"]=="undecided" and b["state"]["phase"]=="cleared"
                and b["state"]["room"]==1 and a["route"]==route and a["state"]["room"]==2
                and a["state"]["foes"]==rooms[1] and a["state"]["total_rooms"]==len(rooms),"fork transition")
        require(all(b["state"][k]==a["state"][k] for k in ("player_health","stamina","turn")),"fork resource effect")
        require(b["enabled"]["direct"] and b["enabled"]["gradual"] and not b["enabled"]["advance"]
                and not a["enabled"]["direct"] and not a["enabled"]["gradual"],"fork projection")
        s=r["terminal"]["state"]
        require((s["phase"],s["room"],s["player_health"],s["turn"])==("won",len(rooms),w["health"],w["turns"])
                and r["terminal"]["encounter"].startswith("VICTORY"),"terminal projection")
    require(rows[0]["fork"]["before"]==rows[1]["fork"]["before"],"common prefix differs")
    # Design hypothesis is a real trade-off, not a hidden scalar rank.
    a,b=(r["exact"]["frontier"][-1] for r in rows)
    require(a["actions"]<b["actions"] and a["health"]<b["health"],"route trade-off absent")

def probe(root):
    args=("godot","--headless","--path",str(root),"--script","res://route_probe.gd")
    native(*args,"--check-only",timeout=15)
    out=native(*args,timeout=60)
    values=[s.removeprefix("ROUTE_SEARCH=") for s in out.splitlines() if s.startswith("ROUTE_SEARCH=")]
    require(len(values)==1,"missing native observation")
    rows=json.loads(values[0]);validate(rows)
    return rows

def main():
    hashes={name:digest(src) for src,name in inputs().items()}
    with tempfile.TemporaryDirectory(prefix="route-choice-") as tmp:
        root=Path(tmp);stage(root);start=time.monotonic()
        rows=probe(root);elapsed=time.monotonic()-start
    require(hashes=={name:digest(src) for src,name in inputs().items()},"inputs changed")
    print(json.dumps({"scope":"native_route_fork_prototype","inputs":hashes,"elapsed_seconds":elapsed,"rows":rows},sort_keys=True))

if __name__=="__main__":
    main()
