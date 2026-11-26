"""Native finite content census; optional generated Resource, not a release."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[1]
SOURCE = GAME / "examples/room-encounter"
MECHANICS = HERE.parent / "mechanic-search"
sys.path.insert(0, str(GAME / "scripts"))
from native_process import verify_process
from rendered_product_acceptance import require

BASELINE = (2, 3, 3)
SELECTED = (1, 2, 2, 3)
INPUTS = {SOURCE / "encounter_rules.gd": "encounter_rules.gd",
          SOURCE / "encounter_tuning.gd": "encounter_tuning.gd",
          SOURCE / "configs/tactical_trial.tres": "configs/tactical_trial.tres",
          SOURCE / "configs/default.tres": "configs/default.tres",
          MECHANICS / "native_search.gd": "native_search.gd",
          HERE / "probe.gd": "probe.gd"}


def inventory():
    return [BASELINE, *(x for x in itertools.product(range(1,4), repeat=4) if sum(x)==8)]


def validate(rows):
    require([tuple(r["rooms"]) for r in rows] == inventory(), "content census incomplete or reordered")
    for r in rows:
        rooms = tuple(r["rooms"])
        for kind in ("reduced", "exact") if rooms in (BASELINE, SELECTED) else ("reduced",):
            result = r[kind]
            require(result["horizon"] == 48 and result["exact"] is (kind == "exact"), "search scope")
            require(0 < result["states"] <= 100000 and result["transitions"] >= result["states"]-1,
                    "state census")
            prev_hp, prev_actions = 49,49
            for p in result["frontier"]:
                require(0 < p["health"] < prev_hp and 0 < p["actions"] < prev_actions,
                        "frontier ordering")
                require(len(p["path"]) == p["actions"] and p["path"].count("advance")==len(rooms)
                        and set(p["path"]) <= {"attack","guard","advance"}, "witness path")
                require(p["turns"] == p["actions"]-len(rooms), "witness turn count")
                prev_hp,prev_actions = p["health"],p["actions"]
        if rooms in (BASELINE,SELECTED):
            sig=lambda result: [(p["health"],p["actions"]) for p in result["frontier"]]
            require(sig(r["reduced"])==sig(r["exact"]), "reference mismatch")
        else:
            require("exact" not in r,"unexpected reference")
        for key in ("attack_first","forecast_aware"):
            p=r[key]
            require(len(p["path"])==p["actions"]<=48 and
                    (p["phase"] in ("won","lost") or p["actions"]==48), "policy scope")
            if p["phase"]=="won":
                require(any(q["health"]>=p["health"] and q["actions"]<=p["actions"]
                            for q in r["reduced"]["frontier"]), "policy not dominated by frontier")
    chosen=next(r for r in rows if tuple(r["rooms"])==SELECTED)
    require([x for x in inventory()[1:] if x[0]==1 and x[-1]==3 and all(0<=b-a<=1 for a,b in zip(x,x[1:]))]==[SELECTED],
            "selection constraint differs")
    return chosen


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-output",type=Path)
    a=p.parse_args()
    if a.resource_output is not None:
        require(not a.resource_output.exists() and a.resource_output.parent.is_dir(),"fresh resource output")
    hashes={dst:hashlib.sha256(src.read_bytes()).hexdigest() for src,dst in INPUTS.items()}
    with tempfile.TemporaryDirectory(prefix="game-content-search-") as tmp:
        root=Path(tmp)
        for src,dst in INPUTS.items():
            target=root/dst; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(src,target)
        (root/"project.godot").write_text('config_version=5\n[application]\nconfig/name="Content search"\n')
        args=["godot","--headless","--path",str(root),"--script","res://probe.gd"]
        check=subprocess.run([*args,"--check-only"],capture_output=True,text=True,timeout=15)
        verify_process(check.returncode,check.stdout,check.stderr)
        start=time.monotonic()
        try:
            native=subprocess.run(args,capture_output=True,text=True,timeout=60)
        except subprocess.TimeoutExpired as exc:
            raise ValueError(f"native search timed out: stdout={str(exc.stdout)[-2000:]} stderr={str(exc.stderr)[-4000:]}") from exc
        elapsed=time.monotonic()-start
        verify_process(native.returncode,native.stdout,native.stderr)
        records=[x.removeprefix("CONTENT_SEARCH=") for x in native.stdout.splitlines() if x.startswith("CONTENT_SEARCH=")]
        require(len(records)==1,"native census missing")
        rows=json.loads(records[0]); chosen=validate(rows)
        generated=root/"selected.tres"
        resource_sha=None
        if chosen["reduced"]["frontier"]:
            require(generated.is_file(),"generated resource missing")
            resource_sha=hashlib.sha256(generated.read_bytes()).hexdigest()
            if a.resource_output is not None:
                with a.resource_output.open("xb") as f: f.write(generated.read_bytes())
        else:
            require(not generated.exists(),"unwinnable candidate emitted")
    require(hashes=={dst:hashlib.sha256(src.read_bytes()).hexdigest() for src,dst in INPUTS.items()},
            "input changed")
    print(json.dumps({"scope":"finite_native_content_census","source_sha256":hashes,
                      "elapsed_seconds":elapsed,"selected":list(SELECTED),"resource_sha256":resource_sha,
                      "rows":rows},sort_keys=True))


if __name__=="__main__":
    main()
