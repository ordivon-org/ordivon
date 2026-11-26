"""Drive both complete exported routes by real private XTEST key events."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from x11_interaction_acceptance import (WIDTH,HEIGHT,XTest,capture,digest,require,
                                       require_private_display,run_private,sha)
from native_process import verify_process
from run import validate

KEY={"attack":"a","guard":"g","advance":"n","direct":"1","gradual":"2","restart":"r"}

def verify_events(events,plan):
    expected=[]
    for row in plan:
        route=row["route"]; path=row["witness"]; fork=path.index(route)
        # Attempt early choose; at fork attempt bypass; after choose attempt both choices.
        expected.extend([(route,False),*( (a,True) for a in path[:fork]),
                         ("advance",False),(route,True),("direct",False),("gradual",False),
                         *((a,True) for a in path[fork+1:]),("restart",True)])
    require([(e["action"],e["accepted"]) for e in events]==expected,"actual input inventory differs")
    at=0; restarts=[]
    for row in plan:
        path=row["witness"];route=row["route"];fork=path.index(route)
        n=len(path)+5
        es=events[at:at+n];at+=n
        require(es[0]["after"]["route"]=="undecided" and es[0]["after"]["state"]["turn"]==0,
                "early route accepted")
        require(es[fork+1]["after"]==es[fork]["after"]==row["fork"]["before"],"fork bypass changed state")
        require(es[fork+2]["after"]==es[fork+3]["after"]==es[fork+4]["after"]==row["fork"]["after"],
                "branch state or rejection differs")
        require(es[-2]["after"]==row["terminal"],"exported terminal differs")
        require(es[-1]["after"]["route"]=="undecided" and es[-1]["after"]["state"]["player_health"]==48
                and es[-1]["after"]["state"]["turn"]==0,"restart differs")
        restarts.append(es[-1]["after"])
    require(at==len(events) and restarts[0]==restarts[1]==events[0]["after"],"restart identity differs")

def observe(executable,root):
    require_private_display(root)
    plan=json.loads((executable.parent/"route_plan.json").read_text())
    validate(plan)
    x=XTest();p=None
    with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
        try:
            p=subprocess.Popen([str(executable),"--resolution",f"{WIDTH}x{HEIGHT}","--position","0,0",
                "--audio-driver","Dummy","--max-fps","30","--quit-after","2400","--","--route-witness"],
                cwd=executable.parent,stdout=out,stderr=err)
            window=None
            for _ in range(50):
                require(p.poll() is None,"early exit")
                window=x.target(p.pid)
                if window is not None: break
                time.sleep(0.2)
            require(window is not None,"missing window")
            x.check_geometry(window);x.focus(x.display,window,2,0);x.sync(x.display,0);time.sleep(.5)
            frames={"initial":capture(x,window,p.pid)}
            for row in plan:
                route=row["route"];path=row["witness"]
                x.press(window,KEY[route])
                for action in path:
                    if action==route:
                        frames[route+"_fork"]=capture(x,window,p.pid)
                        x.press(window,"n")
                    x.press(window,KEY[action])
                    if action==route:
                        frames[route+"_selected"]=capture(x,window,p.pid)
                        x.press(window,"1");x.press(window,"2")
                frames[route+"_won"]=capture(x,window,p.pid)
                x.press(window,"r")
                frames[route+"_restart"]=capture(x,window,p.pid)
            x.press(window,"Escape");p.wait(timeout=10)
            out.seek(0);err.seek(0)
            stdout=out.read().decode(errors="replace");stderr=err.read().decode(errors="replace")
            verify_process(p.returncode,stdout,stderr)
            events=[json.loads(s.removeprefix("ROUTE_EVENT=")) for s in stdout.splitlines() if s.startswith("ROUTE_EVENT=")]
            verify_events(events,plan)
            require(frames["direct_fork"]==frames["gradual_fork"] and
                    frames["direct_selected"]!=frames["gradual_selected"] and
                    frames["direct_won"]!=frames["gradual_won"] and
                    frames["direct_restart"]==frames["gradual_restart"]==frames["initial"],
                    "native raster relations differ")
            require(all(len(set(f))>1 for f in frames.values()),"blank frame")
            renderer=[s for s in stdout.splitlines() if "Using Device:" in s]
            require(len(renderer)==1,"renderer witness")
            return {"status":"PASS","pid":p.pid,"window_id":window,"renderer":renderer[0],
                    "event_count":len(events),"frames":{k:sha(v) for k,v in frames.items()},
                    "terminal":{r["route"]:r["terminal"] for r in plan}}
        finally:
            if p is not None and p.poll() is None:
                p.kill();p.wait()
            x.close(x.display)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--executable",type=Path,required=True)
    p.add_argument("--sha256",required=True)
    p.add_argument("--private-child",type=Path)
    a=p.parse_args()
    require(digest(a.executable)==a.sha256,"executable differs")
    r=observe(a.executable,a.private_child) if a.private_child else run_private(a.executable,a.sha256,Path(__file__),timeout=100)
    print(json.dumps(r,sort_keys=True))

if __name__=="__main__":
    main()
