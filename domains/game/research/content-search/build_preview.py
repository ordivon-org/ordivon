"""Produce a separately scoped generated Room campaign, not a regular release."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[1]
from run import INPUTS, SELECTED, require
sys.path.insert(0,str(HERE.parent/"mechanic-search"))
from build_pair import (cmd, observation, git, stage_native_project, isolate_storage,
                        pack_native_archives, decode_save, export_identity, digest)

STORAGE = "OrdivonRoomContent/ProgressiveR21"
RESOURCE = HERE/"progressive_trial.tres"
WITNESS = HERE/"witness.json"

def check_witness():
    w=json.loads(WITNESS.read_text())
    require(w["source_sha256"]=={dst:digest(src) for src,dst in INPUTS.items()},
            "witness source identity differs")
    require(tuple(w["rooms"])==SELECTED and len(w["actions"])==30 and w["health"]==12 and
            w["turns"]==26 and w["actions"].count("advance")==4,"witness contract")
    return w

def stage_content(root, source):
    project=stage_native_project(root,source)
    shutil.copyfile(RESOURCE,project/"configs/tactical_trial.tres")
    isolate_storage(project,STORAGE)
    return project

def verify_scene(project,w):
    def play(mode):
        return observation(cmd("godot","--headless","--path",str(project),"--script",
            "res://agent_episode.gd","--","--actions",",".join(["trial",*w["actions"]]),
            "--observation",mode), "GAME_AGENT_EPISODE_JSON=")
    r=play("debug")
    require([s["action"] for s in r["steps"]]==["trial",*w["actions"]]
            and all(s["accepted"] for s in r["steps"]),"native scene rejected witness")
    first=r["steps"][0]["after"]
    require((first["total_rooms"],first["foes"],first["player_health"])==(4,1,48),
            "initial generated scene differs")
    gates=[s for s in r["steps"] if s["action"]=="advance"]
    require(all(s["control_path"]=="dialogue.unlock_choice" for s in gates),
            "native passage bypass")
    require([s["after"]["foes"] for s in gates[:-1]]==list(SELECTED[1:]),"room content differs")
    final=r["final"]
    require((final["phase"],final["player_health"],final["turn"],final["room"])==
            ("won",w["health"],w["turns"],4),"full scene terminal differs")
    v=play("player")
    require("VICTORY" in v["final"]["encounter"] and "ROOM 4/4" in v["final"]["status"]
            and "HP 12" in v["final"]["status"] and
            v["final"]["outcome"] == "EXPEDITION COMPLETE: All rooms cleared.",
            "visible victory differs")
    return {"initial":first,"gate_count":len(gates),"room_foes":[first["foes"],*[s["after"]["foes"] for s in gates[:-1]]],
            "final":final,"visible_final":v["final"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    require(a.output.is_absolute() and a.output.parent.is_dir() and not a.output.exists(),"fresh absolute output required")
    require(not git("status","--porcelain","--untracked-files=normal"),"dirty source")
    source=git("rev-parse","HEAD")
    w=check_witness()
    with tempfile.TemporaryDirectory(prefix="room-content-",dir=a.output.parent) as tmp:
        root=Path(tmp)
        project=stage_content(root,source)
        inputs=export_identity(project)
        cmd("godot","--headless","--path",str(project),"--editor","--import")
        scene=verify_scene(project,w)
        print("FULL_SCENE_VICTORY",json.dumps(scene,sort_keys=True),file=sys.stderr,flush=True)
        native=root/"native"; native.mkdir()
        linux=native/"room-encounter.x86_64"; win=native/"room-encounter.exe"
        for preset,exe in (("Linux x86_64",linux),("Windows x86_64",win)):
            cmd("godot","--headless","--path",str(project),"--export-release",preset,str(exe))
            require(exe.is_file() and exe.stat().st_size>0,"export missing")
        linux.chmod(0o700)
        x11=json.loads(cmd(sys.executable,str(HERE.parent/"mechanic-search/paired_x11.py"),
                          "--executable",str(linux),"--sha256",digest(linux),timeout=90))
        cp=decode_save(root,x11.pop("save_text"))
        expected={"enemies_per_room":list(SELECTED),"player_health":48,"enemy_health":5,
                  "attack_damage":3,"enemy_damage":3,"stamina_capacity":6,"attack_cost":2,
                  "guard_restore":3,"guard_block":3,"tactical_trial":True}
        require(cp["tuning"]==expected and cp["state"]["total_rooms"]==4 and
                cp["state"]["foes"]==1 and cp["state"]["player_health"]==48 and
                cp["state"]["turn"]==1,"exported generated content checkpoint differs")
        require(x11["save_path"]==STORAGE+"/room_encounter_run.cfg","storage identity differs")
        require(export_identity(project)==inputs,"export inputs changed")
        output=root/"ready";output.mkdir()
        archives=pack_native_archives(project,native,output,"progressive-trial")
        receipt={"status":"PASS","scope":"generated_encounter_content_technical_preview",
                 "source_commit":source,"resource_sha256":digest(RESOURCE),
                 "witness_sha256":digest(WITNESS),"native_inputs":inputs,"scene":scene,
                 "linux_native":x11,"native_checkpoint":cp,"linux_executable_sha256":digest(linux),
                 "windows_executable_sha256":digest(win),"windows_scope":"export_only",
                 "human_quality":"NOT_EVALUATED","release_published":False,
                 "archives":{f.name:digest(f) for f in archives}}
        (output/"CONTENT_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        (output/"PLAY.md").write_text("# Progressive Trial — generated encounter preview\n\n"
              "Extract one native archive. Start the game, press T to enter the generated four-room "
              "campaign (1,2,2,3 foes). A/Space attacks, G guards, N requests the door; choose Unlock. "
              "R restarts, S/L save/load. Storage is separate from regular Trial and R20 A/B. "
              "Classic remains unchanged. This is a technical preview, not a commercial release or "
              "a validated Human preference. Verify SHA256SUMS before use.\n")
        (output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.name}\n" for f in sorted(output.iterdir())))
        require(git("rev-parse","HEAD")==source and not git("status","--porcelain","--untracked-files=normal"),
                "source changed during build")
        output.rename(a.output)
        print(json.dumps(receipt,sort_keys=True))

if __name__=="__main__":
    main()
