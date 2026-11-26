"""Private native Route Fork product, with full exported Linux keyboard replay."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile

from run import GAME,HERE,inputs,stage,probe,require,digest,native
sys.path.insert(0,str(GAME/"scripts"))
from native_export_identity import capture as export_identity

def git(*args):
    return subprocess.check_output(["git","-C",str(GAME),*args],text=True).strip()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    require(a.output.is_absolute() and a.output.parent.is_dir() and not a.output.exists(),"fresh output required")
    require(not git("status","--porcelain","--untracked-files=normal"),"dirty source")
    source=git("rev-parse","HEAD")
    hashes={name:digest(src) for src,name in inputs().items()}
    with tempfile.TemporaryDirectory(prefix="game-route-fork-",dir=a.output.parent) as tmp:
        root=Path(tmp);project=root/"project";project.mkdir()
        stage(project); rows=probe(project)
        print("NATIVE_FORK_SCENE_PASS",[(r["route"],r["terminal"]["status"]) for r in rows],file=sys.stderr,flush=True)
        # Remove research-only script inputs from actual product source.
        (project/"route_probe.gd").unlink();(project/"native_search.gd").unlink()
        identity=export_identity(project)
        native("godot","--headless","--path",str(project),"--editor","--import",timeout=60)
        executables=root/"native";executables.mkdir()
        linux=executables/"room-encounter.x86_64"; win=executables/"room-encounter.exe"
        for preset,exe in (("Linux x86_64",linux),("Windows x86_64",win)):
            native("godot","--headless","--path",str(project),"--export-release",preset,str(exe),timeout=100)
            require(exe.is_file() and exe.stat().st_size>0,"export missing")
        linux.chmod(0o700)
        (executables/"route_plan.json").write_text(json.dumps(rows,sort_keys=True))
        observed=json.loads(native(sys.executable,str(HERE/"route_x11.py"),"--executable",str(linux),"--sha256",digest(linux),timeout=115))
        require(observed["status"]=="PASS","actual product failed")
        require(export_identity(project)==identity,"export inputs changed")
        output=root/"ready";output.mkdir()
        tar=output/"route-fork-linux.tar.gz"; z=output/"route-fork-windows.zip"
        with tarfile.open(tar,"w:gz") as f: f.add(linux,arcname=linux.name,recursive=False)
        with zipfile.ZipFile(z,"w",compression=zipfile.ZIP_DEFLATED) as f:f.write(win,arcname=win.name)
        receipt={"status":"PASS","scope":"route_fork_technical_preview","source_commit":source,
                 "source_inputs":hashes,"engine_inputs":identity,"native_scene":rows,
                 "linux_native":observed,"linux_executable_sha256":digest(linux),"windows_executable_sha256":digest(win),
                 "windows_scope":"export_only","human_quality":"NOT_EVALUATED","persistence":"NOT_SUPPORTED",
                 "archives":{f.name:digest(f) for f in (tar,z)}}
        (output/"ROUTE_RECEIPT.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
        (output/"PLAY.md").write_text("# Route Fork — technical preview\n\n"
             "Extract one archive and start room-encounter. A attacks, G guards, N continues. "
             "Clear the opening encounter; select 1 Direct or 2 Gradual. R restarts the entire expedition, "
             "Escape quits. Both routes have eight foes and distinct room schedules. "
             "No save or load in this prototype. This is a separate native game experiment, not a release.\n")
        (output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.name}\n" for f in sorted(output.iterdir())))
        require(git("rev-parse","HEAD")==source and not git("status","--porcelain","--untracked-files=normal")
                and hashes=={name:digest(src) for src,name in inputs().items()},"source changed")
        output.rename(a.output)
        print(json.dumps(receipt,sort_keys=True))
if __name__=="__main__":
    main()
