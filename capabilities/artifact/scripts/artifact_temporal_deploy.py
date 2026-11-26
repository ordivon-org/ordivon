#!/usr/bin/env python3
"""Plan/apply the Artifact Temporal worker on the existing Temporal server."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAIN=Path('/root/projects/ordivon/capabilities/artifact')
UNIT='ordivon-artifact-temporal-worker.service'
SOURCE_UNIT=ROOT/'systemd'/UNIT
SYSTEM_UNIT=Path('/etc/systemd/system')/UNIT
TEMPORAL_PY=Path('/root/.local/share/ordivon-workstation/artifact-python-v1/current/bin/python')
STATE=Path('/root/.local/state/ordivon-workstation/artifact-temporal')
SERVER_UNIT='temporal.service'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def active(unit:str)->bool:return subprocess.run(['/usr/bin/systemctl','is-active','--quiet',unit],check=False).returncode==0
def temporal_sdk_version(carrier: Path | None = None)->str|None:
    carrier = TEMPORAL_PY if carrier is None else carrier
    if not carrier.is_file():return None
    p=subprocess.run([str(carrier),'-c','from importlib.metadata import version;print(version("temporalio"))'],text=True,capture_output=True,check=False,timeout=15)
    return p.stdout.strip() if p.returncode==0 else None
def ensure_no_running_artifact_workflows()->None:
    # Consume the canonical workflow type from the Worker module itself:
    # a hand-typed visibility name can silently return zero false matches.
    # Run through the pinned, already-installed Artifact carrier SDK; this
    # stdlib deployment CLI does not need its own Temporal environment.
    code = """
import asyncio
import sys
sys.path.insert(0,sys.argv[1])
sys.path.insert(0,sys.argv[4])
from artifact_temporal_workflow import ARTIFACT_WORKFLOW
from temporalio.client import Client

async def main():
    client=await Client.connect(sys.argv[2], namespace=sys.argv[3])
    query=f'ExecutionStatus="Running" AND WorkflowType="{ARTIFACT_WORKFLOW}"'
    async for _ in client.list_workflows(query=query, page_size=1):
        print("1")
        return
    print("0")

asyncio.run(main())
"""
    observed = subprocess.run(
        [str(TEMPORAL_PY), '-c', code, str(ROOT/'scripts'),
         '127.0.0.1:17233', 'default', str(ROOT)],
        capture_output=True, text=True, check=False, timeout=25,
    )
    if observed.returncode or observed.stdout.strip() not in ('0','1'):
        raise RuntimeError('Artifact Temporal workflow visibility unavailable; refusing restart')
    if observed.stdout.strip() == '1':
        raise RuntimeError('running Artifact workflows block Worker restart')


def plan()->dict:
    main_source=ROOT.resolve()==MAIN.resolve()
    source_ok=SOURCE_UNIT.is_file(); installed=SYSTEM_UNIT.is_file() and source_ok and SYSTEM_UNIT.read_bytes()==SOURCE_UNIT.read_bytes()
    sdk=temporal_sdk_version()
    # Consume the Artifact Python carrier lock instead of a second SDK pin.
    pinned=json.loads((ROOT/'artifact-delivery/artifact-python-runtime-v1.lock.json').read_text())['pythonPackages']['temporalio']
    return {'schemaVersion':1,'kind':'artifact-temporal-worker-deployment-plan','sourceRoot':str(ROOT),'mainSourceAuthority':main_source,'temporalServerActive':active(SERVER_UNIT),'temporalSdkVersion':sdk,'temporalSdkPinned':sdk==pinned,'sourceUnitSha256':sha(SOURCE_UNIT) if source_ok else None,'unitInstalledExact':installed,'workerActive':active(UNIT),'stateRoot':str(STATE),'applyEligible':main_source and active(SERVER_UNIT) and sdk==pinned and source_ok}
def apply()->dict:
    current=plan()
    if not current['applyEligible']:raise RuntimeError('Artifact Temporal worker deployment is not eligible from this source/runtime cut')
    ensure_no_running_artifact_workflows()
    STATE.mkdir(parents=True,exist_ok=True);SYSTEM_UNIT.write_bytes(SOURCE_UNIT.read_bytes());os.chmod(SYSTEM_UNIT,0o644)
    subprocess.run(['/usr/bin/systemctl','daemon-reload'],check=True);subprocess.run(['/usr/bin/systemctl','enable',UNIT],check=True);subprocess.run(['/usr/bin/systemctl','reset-failed',UNIT],check=False);subprocess.run(['/usr/bin/systemctl','restart',UNIT],check=True)
    return plan()
def qualify_source_tree(repo: Path, commit: str, source: Path) -> int:
    """Verify the complete regular-file Git subtree, not a mutable checkout."""
    git = ["/usr/bin/git", "--no-replace-objects", "-C", str(repo)]
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["GIT_NO_LAZY_FETCH"] = "1"

    def read(*args: str) -> bytes:
        return subprocess.check_output([*git, *args], env=env, timeout=30)

    fmt = read("rev-parse", "--show-object-format").decode().strip()
    width = {"sha1": 40, "sha256": 64}.get(fmt)
    if width is None or not re.fullmatch(r"[0-9a-f]{"+str(width)+r"}", commit):
        raise RuntimeError("source must be an exact Git commit")
    if read("cat-file", "-t", commit).strip() != b"commit":
        raise RuntimeError("source must be a Git commit object")
    expected = {}
    for row in read("ls-tree", "--full-tree", "-r", "-z", commit+":capabilities/artifact").split(b"\0"):
        if not row:
            continue
        meta, name = row.split(b"\t", 1)
        mode, kind, oid = meta.split()
        path = os.fsdecode(name)
        if kind != b"blob" or mode not in (b"100644", b"100755"):
            raise RuntimeError("unsupported Git source node: "+path)
        expected[path] = (mode, oid.decode())
    if not expected:
        raise RuntimeError("empty Artifact source")
    actual = {}
    for path in source.rglob("*"):
        name = path.relative_to(source).as_posix()
        if path.is_symlink():
            raise RuntimeError("source symlink: "+name)
        if path.is_dir():
            continue
        if not path.is_file():
            raise RuntimeError("unsupported installed source node: "+name)
        data = path.read_bytes()
        digest = hashlib.new(fmt, b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        mode = b"100755" if path.stat().st_mode & 0o111 else b"100644"
        actual[name] = (mode, digest)
    if actual != expected:
        raise RuntimeError("installed source tree differs from exact Git commit")
    return len(expected)


def render_immutable_unit(template: str, source: Path, carrier: Path) -> str:
    """Project the existing service contract; preserve state and hardening."""
    source_path = str(source)
    carrier_path = str(carrier)
    for path in (source_path, carrier_path):
        if not re.fullmatch(r"/[A-Za-z0-9._/-]+", path):
            raise RuntimeError("unsupported systemd executable/source path")
    old_cwd = "WorkingDirectory=" + str(MAIN)
    old_exec = "ExecStart=" + str(TEMPORAL_PY) + " " + str(MAIN / "scripts/artifact_temporal_worker.py") + " "
    if template.count(old_cwd+"\n") != 1 or template.count(old_exec) != 1:
        raise RuntimeError("unexpected Worker service template")
    if any(sum(line.startswith(key) for line in template.splitlines()) != 1 for key in ("ExecStart=", "WorkingDirectory=")):
        raise RuntimeError("ambiguous Worker service entry")
    return template.replace(old_cwd+"\n", "WorkingDirectory="+source_path+"\n").replace(
        old_exec, "ExecStart="+carrier_path+" "+str(source/"scripts/artifact_temporal_worker.py")+" "
    )


def prepare_immutable(commit: str, source: Path, gc_root: Path) -> dict:
    """Read-only preparation; activation requires a separate owner drain fence."""
    if source.parent != Path("/nix/store") or source.resolve(strict=True) != source:
        raise RuntimeError("source must be a direct native Nix store path")
    root = gc_root.parent.resolve(strict=True) / gc_root.name
    if not root.is_symlink() or os.readlink(root) != str(source):
        raise RuntimeError("source GC root mismatch")
    roots = subprocess.check_output(
        ["/usr/bin/nix-store", "--query", "--roots", str(source)], text=True, timeout=60
    )
    if f"{root} -> {source}" not in roots.splitlines():
        raise RuntimeError("source GC root is not registered")
    files = qualify_source_tree(ROOT, commit, source)
    carrier = TEMPORAL_PY.resolve(strict=True)
    generations = TEMPORAL_PY.parents[2] / "generations"
    if (carrier.parent.name != "bin" or carrier.name != "python"
            or carrier.parents[2] != generations
            or not re.fullmatch(r"[0-9a-f]{64}", carrier.parents[1].name)):
        raise RuntimeError("carrier must resolve to an existing qualified generation")
    pinned = json.loads((source/"artifact-delivery/artifact-python-runtime-v1.lock.json").read_text())["pythonPackages"]["temporalio"]
    sdk = temporal_sdk_version(carrier)
    if sdk != pinned:
        raise RuntimeError("immutable source and installed carrier SDK differ")
    unit = render_immutable_unit((source/"systemd"/UNIT).read_text(), source, carrier)
    return {
        "schemaVersion": 1, "kind": "artifact-temporal-immutable-candidate",
        "sourceCommit": commit, "sourceRoot": str(source), "sourceFileCount": files,
        "sourceGcRoot": str(root), "pythonCarrier": str(carrier),
        "temporalSdkVersion": sdk, "unit": unit,
        "unitSha256": hashlib.sha256(unit.encode()).hexdigest(),
        "activationEligible": False,
        "activationObligation": "owner drain/admission fence, carrier retention, workflow compatibility and rollback",
    }


def main()->int:
    p=argparse.ArgumentParser()
    modes=p.add_mutually_exclusive_group()
    modes.add_argument('--apply',action='store_true')
    modes.add_argument('--prepare-store',type=Path)
    p.add_argument('--source-commit')
    p.add_argument('--gc-root',type=Path)
    a=p.parse_args()
    if a.prepare_store is not None:
        if a.source_commit is None or a.gc_root is None:
            p.error('--prepare-store requires --source-commit and --gc-root')
        r=prepare_immutable(a.source_commit,a.prepare_store,a.gc_root)
    else:
        if a.source_commit is not None or a.gc_root is not None:
            p.error('source commit and GC root require --prepare-store')
        r=apply() if a.apply else plan()
    print(json.dumps(r,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
