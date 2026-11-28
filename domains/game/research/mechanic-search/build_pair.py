"""Manufacture a separate playable study pair from a clean tracked source cut."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[1]
sys.path.insert(0, str(GAME / "scripts"))
from native_process import verify_process
from native_export_identity import capture as export_identity, digest
from product_acceptance_contract import require

SOURCE = GAME / "examples/room-encounter"
TREATMENT = HERE / "conditions/trial_block2_hp53.tres"
CONDITIONS = {"A": (48, 3), "B": (53, 2)}
LICENSES = {"DIALOGUE_MANAGER_LICENSE.txt": "addons/dialogue_manager/LICENSE",
            "KENNEY_ASSETS_LICENSE.txt": "assets/LICENSE.txt"}


def cmd(*args, timeout=180):
    r = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=timeout)
    verify_process(r.returncode, r.stdout, r.stderr)
    return r.stdout


def observation(stdout, prefix):
    rows = [x.removeprefix(prefix) for x in stdout.splitlines() if x.startswith(prefix)]
    require(len(rows) == 1, f"expected one {prefix} observation")
    return json.loads(rows[0])


def git(*args):
    return subprocess.check_output(["git", "-C", str(GAME), *args], text=True).strip()


def stage_project(root, source_commit, condition):
    repo = Path(git("rev-parse", "--show-toplevel"))
    relative = SOURCE.relative_to(repo)
    raw = subprocess.check_output(["git", "-C", str(repo), "archive", source_commit, str(relative)])
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(root, filter="data")
    project = root / relative
    original = project / "configs/tactical_trial.tres"
    old = original.read_text()
    expected = old.replace("player_health = 48", "player_health = 53").replace("guard_block = 3", "guard_block = 2")
    require(old.count("player_health = 48") == old.count("guard_block = 3") == 1
            and TREATMENT.read_text() == expected, "condition is not exact two-parameter intervention")
    if condition == "B":
        shutil.copyfile(TREATMENT, original)
    config = project / "project.godot"
    s = config.read_text()
    require(s.count('config/name="Room Encounter"') == 1 and "custom_user_dir" not in s,
            "unexpected storage settings")
    config.write_text(s.replace('config/name="Room Encounter"', 'config/name="Room Encounter"\n'
        'config/use_custom_user_dir=true\n'
        f'config/custom_user_dir_name="OrdivonRoomStudy/{condition}"'))
    return project


def verify_source(project, hp, block):
    r = observation(cmd("godot", "--headless", "--path", str(project), "--script",
                        "res://agent_episode.gd", "--", "--actions", "trial,guard,guard,guard",
                        "--observation", "debug"), "GAME_AGENT_EPISODE_JSON=")
    steps = r["steps"]
    require([s["action"] for s in steps] == ["trial","guard","guard","guard"]
            and all(s["accepted"] for s in steps), "source actions failed")
    expected = [hp, hp - (3-block), hp - 2*(3-block), hp - 2*(3-block)]
    require([s["after"]["player_health"] for s in steps] == expected, "source treatment differs")
    require([s["after"]["turn"] for s in steps] == [0,1,2,3], "source turn differs")
    view = observation(cmd("godot", "--headless", "--path", str(project), "--script",
                           "res://agent_episode.gd", "--", "--actions", "trial,guard,guard,guard"),
                       "GAME_AGENT_EPISODE_JSON=")
    require(f"HP {hp}" in view["steps"][0]["after"]["status"] and
            f"you lost {3-block} HP" in view["steps"][1]["after"]["outcome"] and
            "PERFECT PARRY" in view["final"]["outcome"], "source UI projection differs")
    return {"health": expected, "final_player": view["final"]}


def decode_save(root, raw):
    mini = root / "decode"
    mini.mkdir()
    (mini / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Study checkpoint reader"\n')
    shutil.copyfile(HERE / "read_checkpoint.gd", mini / "read_checkpoint.gd")
    save = mini / "capture.cfg"
    save.write_text(raw)
    return observation(cmd("godot","--headless","--path",str(mini),"--script",
                           "res://read_checkpoint.gd","--",str(save)), "STUDY_CHECKPOINT=")


def pack_condition(root, output, source_commit, condition):
    hp, block = CONDITIONS[condition]
    project = stage_project(root, source_commit, condition)
    inputs = export_identity(project)
    cmd("godot", "--headless", "--path", str(project), "--editor", "--import")
    source = verify_source(project, hp, block)
    native = root / "native"
    native.mkdir()
    linux = native / "room-encounter.x86_64"
    windows = native / "room-encounter.exe"
    for name, exe in (("Linux x86_64",linux),("Windows x86_64",windows)):
        cmd("godot","--headless","--path",str(project),"--export-release",name,str(exe))
        require(exe.is_file() and exe.stat().st_size > 0, "export missing")
    linux.chmod(0o700)
    observed = json.loads(cmd(sys.executable,str(HERE/"paired_x11.py"),
                              "--executable",str(linux),"--sha256",digest(linux),timeout=90))
    raw = observed.pop("save_text")
    cp = decode_save(root, raw)
    require(observed["save_path"] == f"OrdivonRoomStudy/{condition}/room_encounter_run.cfg",
            "save isolation failed")
    require(cp["tuning"]["player_health"] == hp and cp["tuning"]["guard_block"] == block
            and cp["tuning"]["tactical_trial"] is True and cp["state"]["turn"] == 1
            and cp["state"]["player_health"] == hp-(3-block), "exported saved treatment differs")
    require(export_identity(project) == inputs, "native input identity changed")
    for name, relative in LICENSES.items():
        shutil.copyfile(project / relative, native / name)
    tar = output / f"condition-{condition}-linux.tar.gz"
    win = output / f"condition-{condition}-windows.zip"
    with tarfile.open(tar, "w:gz") as f:
        for name in (linux.name, *LICENSES):
            f.add(native/name, arcname=name, recursive=False)
    with zipfile.ZipFile(win, "w", compression=zipfile.ZIP_DEFLATED) as f:
        for name in (windows.name, *LICENSES):
            f.write(native/name, arcname=name)
    return {"condition":condition, "initial_health":hp, "guard_block":block,
            "resource_sha256":digest(project/"configs/tactical_trial.tres"),
            "project_settings_sha256":digest(project/"project.godot"),
            "export_inputs":inputs, "source_observation":source,
            "linux_executable_sha256":digest(linux), "windows_executable_sha256":digest(windows),
            "linux_native":observed, "native_checkpoint":cp,
            "archives":{p.name:digest(p) for p in (tar,win)}, "windows_scope":"export_only"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    require(a.output.is_absolute() and a.output.parent.is_dir() and not a.output.exists(), "fresh absolute output required")
    require(not git("status","--porcelain","--untracked-files=normal"), "dirty source")
    source = git("rev-parse","HEAD")
    with tempfile.TemporaryDirectory(prefix="room-pair-",dir=a.output.parent) as tmp:
        stage = Path(tmp)
        output = stage / "ready"
        output.mkdir()
        rows = []
        for condition in CONDITIONS:
            work = stage / condition
            work.mkdir()
            rows.append(pack_condition(work,output,source,condition))
        require(rows[0]["export_inputs"] == rows[1]["export_inputs"], "pair toolchain differs")
        require(rows[0]["linux_native"]["frames"]["classic"] == rows[1]["linux_native"]["frames"]["classic"]
                and rows[0]["linux_native"]["frames"]["trial"] != rows[1]["linux_native"]["frames"]["trial"],
                "pair visual relation differs")
        receipt = {"status":"PASS","scope":"paired_mechanic_study_technical_preview",
                   "source_commit":source,"conditions":rows,"human_quality":"NOT_EVALUATED",
                   "release_published":False}
        (output/"STUDY_RECEIPT.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
        shutil.copyfile(HERE/"PLAYTEST.md",output/"PLAYTEST.md")
        (output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.name}\n" for f in sorted(output.iterdir())))
        require(git("rev-parse","HEAD")==source and not git("status","--porcelain","--untracked-files=normal"),
                "source changed during study build")
        output.rename(a.output)
        print(json.dumps(receipt,sort_keys=True))


if __name__ == "__main__":
    main()
