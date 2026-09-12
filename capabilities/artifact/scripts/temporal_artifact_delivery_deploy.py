#!/usr/bin/env python3
"""Plan/apply the Artifact Delivery Temporal worker on the existing Temporal server."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAIN=Path('/root/workstation-lab')
UNIT='ordivon-artifact-temporal-worker.service'
SOURCE_UNIT=ROOT/'systemd'/UNIT
SYSTEM_UNIT=Path('/etc/systemd/system')/UNIT
TEMPORAL_PY=Path('/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python')
ARTIFACT_PY=Path('/root/.local/share/ordivon-workstation/artifact-delivery-python-v1/current/bin/python')
STATE=Path('/root/.local/state/ordivon-workstation/artifact-delivery-temporal')
SERVER_UNIT='ordivon-temporal-agent-dev.service'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def active(unit:str)->bool:return subprocess.run(['/usr/bin/systemctl','is-active','--quiet',unit],check=False).returncode==0
def temporal_sdk_version()->str|None:
    if not TEMPORAL_PY.is_file():return None
    p=subprocess.run([str(TEMPORAL_PY),'-c','from importlib.metadata import version;print(version("temporalio"))'],text=True,capture_output=True,check=False,timeout=15)
    return p.stdout.strip() if p.returncode==0 else None
def artifact_python_probe()->dict:
    if not ARTIFACT_PY.is_file():return {'present':False,'ready':False,'detail':'stable Artifact Python carrier absent'}
    p=subprocess.run([str(ARTIFACT_PY),'-c','import json,lxml.etree,pptx,PIL,jsonschema,xlsxwriter,opentelemetry.sdk;print(json.dumps({"status":"PASS","libxslt":lxml.etree.LIBXSLT_VERSION}))'],text=True,capture_output=True,check=False,timeout=30)
    detail=(p.stdout.strip() if p.returncode==0 else p.stderr[-2000:].strip())
    return {'present':True,'ready':p.returncode==0,'returnCode':p.returncode,'detail':detail}
def plan()->dict:
    main_source=ROOT.resolve()==MAIN.resolve()
    source_ok=SOURCE_UNIT.is_file(); installed=SYSTEM_UNIT.is_file() and source_ok and SYSTEM_UNIT.read_bytes()==SOURCE_UNIT.read_bytes()
    sdk=temporal_sdk_version(); artifact_python=artifact_python_probe()
    return {'schemaVersion':1,'kind':'artifact-delivery-temporal-worker-deployment-plan','sourceRoot':str(ROOT),'mainSourceAuthority':main_source,'temporalServerActive':active(SERVER_UNIT),'temporalSdkVersion':sdk,'temporalSdkPinned':sdk=='1.32.0','artifactPythonPresent':artifact_python['present'],'artifactPythonReady':artifact_python['ready'],'artifactPythonProbe':artifact_python,'sourceUnitSha256':sha(SOURCE_UNIT) if source_ok else None,'unitInstalledExact':installed,'workerActive':active(UNIT),'stateRoot':str(STATE),'applyEligible':main_source and active(SERVER_UNIT) and sdk=='1.32.0' and artifact_python['ready'] and source_ok}
def apply()->dict:
    current=plan()
    if not current['applyEligible']:raise RuntimeError('Artifact Temporal worker deployment is not eligible from this source/runtime cut')
    STATE.mkdir(parents=True,exist_ok=True);SYSTEM_UNIT.write_bytes(SOURCE_UNIT.read_bytes());os.chmod(SYSTEM_UNIT,0o644)
    subprocess.run(['/usr/bin/systemctl','daemon-reload'],check=True);subprocess.run(['/usr/bin/systemctl','enable',UNIT],check=True);subprocess.run(['/usr/bin/systemctl','reset-failed',UNIT],check=False);subprocess.run(['/usr/bin/systemctl','restart',UNIT],check=True)
    return plan()
def main()->int:
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();r=apply() if a.apply else plan();print(json.dumps(r,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
