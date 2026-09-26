#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
FILES={
  HERE/'d_drive_compact_gate_r3.py': Path('/mnt/d/OrdivonStudio/d-drive-compact-gate-r3.py'),
  HERE/'DDriveOfflineCompactR3.ps1': Path('/mnt/d/OrdivonStudio/d-drive-offline-compact-r3.ps1'),
  HERE/'DDriveCompactAuthorizeR4.ps1': Path('/mnt/d/OrdivonStudio/d-drive-compact-authorize-r4.ps1'),
  HERE/'DDriveCompactRunR3.ps1': Path('/mnt/d/OrdivonStudio/d-drive-compact-run-r3.ps1'),
}
RECEIPT=Path('/mnt/c/ProgramData/Ordivon/Workstation/Providers/receipts/d-drive-compact-r3.json')

def digest(path:Path)->str:
    return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()

def atomic_json(path:Path,payload:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8');tmp.replace(path)

def materialize()->dict:
    rows=[]
    for src,dst in FILES.items():
        dst.parent.mkdir(parents=True,exist_ok=True)
        data=src.read_bytes(); tmp=dst.with_name(dst.name+'.tmp'); tmp.write_bytes(data); tmp.replace(dst)
        if dst.suffix=='.py': dst.chmod(0o755)
        rows.append({'source':str(src),'sourceSha256':digest(src),'target':str(dst),'targetSha256':digest(dst)})
    payload={'schemaVersion':1,'kind':'ordivon.workstation.d-drive-compact-r3-materialization','files':rows}
    atomic_json(RECEIPT,payload);return payload

def status()->dict:
    rows=[]
    for src,dst in FILES.items(): rows.append({'source':str(src),'sourceSha256':digest(src),'target':str(dst),'present':dst.is_file(),'matches':dst.is_file() and digest(dst)==digest(src)})
    return {'schemaVersion':1,'kind':'ordivon.workstation.d-drive-compact-r3-materialization-status','files':rows}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument('command',choices=('materialize','status'));a=p.parse_args();print(json.dumps(materialize() if a.command=='materialize' else status(),indent=2,sort_keys=True));return 0
if __name__=='__main__': raise SystemExit(main())
