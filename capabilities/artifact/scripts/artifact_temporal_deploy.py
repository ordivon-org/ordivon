#!/usr/bin/env python3
"""Plan/apply the Artifact Temporal worker on the existing Temporal server."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
def temporal_sdk_version()->str|None:
    if not TEMPORAL_PY.is_file():return None
    p=subprocess.run([str(TEMPORAL_PY),'-c','from importlib.metadata import version;print(version("temporalio"))'],text=True,capture_output=True,check=False,timeout=15)
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
    return {'schemaVersion':1,'kind':'artifact-temporal-worker-deployment-plan','sourceRoot':str(ROOT),'mainSourceAuthority':main_source,'temporalServerActive':active(SERVER_UNIT),'temporalSdkVersion':sdk,'temporalSdkPinned':sdk=='1.32.0','sourceUnitSha256':sha(SOURCE_UNIT) if source_ok else None,'unitInstalledExact':installed,'workerActive':active(UNIT),'stateRoot':str(STATE),'applyEligible':main_source and active(SERVER_UNIT) and sdk=='1.32.0' and source_ok}
def apply()->dict:
    current=plan()
    if not current['applyEligible']:raise RuntimeError('Artifact Temporal worker deployment is not eligible from this source/runtime cut')
    ensure_no_running_artifact_workflows()
    STATE.mkdir(parents=True,exist_ok=True);SYSTEM_UNIT.write_bytes(SOURCE_UNIT.read_bytes());os.chmod(SYSTEM_UNIT,0o644)
    subprocess.run(['/usr/bin/systemctl','daemon-reload'],check=True);subprocess.run(['/usr/bin/systemctl','enable',UNIT],check=True);subprocess.run(['/usr/bin/systemctl','reset-failed',UNIT],check=False);subprocess.run(['/usr/bin/systemctl','restart',UNIT],check=True)
    return plan()
def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();r=apply() if a.apply else plan();print(json.dumps(r,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
