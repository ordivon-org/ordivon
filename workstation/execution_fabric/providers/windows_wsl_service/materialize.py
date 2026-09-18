#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

SOURCE=Path(__file__).with_name("WindowsWslServiceControlProvider.ps1")
ROOT=Path("/mnt/c/ProgramData/Ordivon/ExecutionFabric/WindowsWslServiceControlProvider")
RECEIPT=Path("/mnt/c/ProgramData/Ordivon/ExecutionFabric/receipts/windows-wsl-service-control-provider.json")

def digest(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def materialize()->dict:
    d=digest(SOURCE); target=ROOT/d/SOURCE.name
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if digest(target)!=d: raise RuntimeError("materialized provider digest mismatch")
    else:
        shutil.copyfile(SOURCE,target)
    payload={
      "schemaVersion":1,
      "kind":"ordivon.workstation.windows-wsl-service-control-provider-materialization",
      "sourceSha256":"sha256:"+d,
      "target":str(target),
      "targetSha256":"sha256:"+digest(target),
      "targetNodeIds":["linux-local"]
    }
    RECEIPT.parent.mkdir(parents=True,exist_ok=True)
    tmp=RECEIPT.with_suffix(".tmp"); tmp.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); tmp.replace(RECEIPT)
    return payload

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=("materialize","status")); args=parser.parse_args()
    if args.command=="materialize": payload=materialize()
    else:
        d=digest(SOURCE); target=ROOT/d/SOURCE.name
        payload={"schemaVersion":1,"sourceSha256":"sha256:"+d,"target":str(target),"present":target.is_file(),"matches":target.is_file() and digest(target)==d}
    print(json.dumps(payload,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
