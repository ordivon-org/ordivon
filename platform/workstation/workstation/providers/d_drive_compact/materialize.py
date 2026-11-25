#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
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

def _observe_regular(path: Path) -> dict:
    """Read-only, bounded, exact-file observation; aliases are not duplicates.

    The observations describe one open file, not an atomic deletion fence.
    No evidence of the file's runtime consumers is implied by equal bytes.
    """
    try:
        before = path.lstat()
    except FileNotFoundError:
        return {"standing": "ABSENT", "present": False}
    except OSError:
        return {"standing": "UNKNOWN", "present": None}
    if not stat.S_ISREG(before.st_mode) or before.st_size > 8 * 1024 * 1024:
        return {"standing": "UNKNOWN", "present": True}
    def identity(info):
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)
    try:
        # An aliased ancestor may point outside the declared carrier. This
        # comparison is observational, not an atomic path-resolution fence.
        if path.resolve(strict=True) != path.absolute():
            return {"standing": "UNKNOWN", "present": True}
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(before):
                return {"standing": "UNKNOWN", "present": True}
            payload = stream.read(8 * 1024 * 1024 + 1)
            after = os.fstat(stream.fileno())
        if (len(payload) != before.st_size or identity(after) != identity(before)
                or identity(path.lstat()) != identity(before)):
            return {"standing": "UNKNOWN", "present": True}
    except OSError:
        return {"standing": "UNKNOWN", "present": True}
    return {
        "standing": "OBSERVED", "present": True, "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
        "logicalBytes": before.st_size, "allocatedBytes": before.st_blocks * 512,
        "fileIdentity": (before.st_dev, before.st_ino), "linkCount": before.st_nlink,
    }


def status() -> dict:
    """Expose redundant representations and unresolved retention roots.

    I: existing source/target mapping, O: per-path observation and standing.
    Equal current bytes identify a review candidate, never consumer release.
    Missing/ambiguous evidence keeps the object; no physical effect occurs.
    Source, target and runtime consumer observations remain independent.
    """
    rows = []
    for src, dst in FILES.items():
        source = _observe_regular(src)
        target = _observe_regular(dst)
        same = (source["standing"] == target["standing"] == "OBSERVED"
                and source["sha256"] == target["sha256"])
        if target["standing"] == "ABSENT":
            standing = "ABSENT"
        elif same:
            standing = "EXACT_COPY_REVIEW"
        elif source["standing"] == target["standing"] == "OBSERVED":
            standing = "DIVERGENT_RETAIN"
        else:
            standing = "UNKNOWN_RETAIN"
        if same:
            relation = ("SAME_INODE" if source["fileIdentity"] == target["fileIdentity"]
                        else "DISTINCT_INODES")
        else:
            relation = "NOT_QUALIFIED"
        rows.append({
            "source": str(src), "sourceSha256": source.get("sha256"),
            "target": str(dst), "present": target["present"],
            "matches": same, "targetSha256": target.get("sha256"),
            "logicalBytes": target.get("logicalBytes"),
            "allocatedBytes": target.get("allocatedBytes"),
            "linkCount": target.get("linkCount"), "physicalRelation": relation,
            "sourceObservation": source["standing"],
            "targetObservation": target["standing"], "retentionStanding": standing,
        })
    return {
        "schemaVersion": 1, "kind": "ordivon.workstation.d-drive-compact-r3-materialization-status",
        "files": rows, "consumerCoverage": "UNKNOWN", "deleteAuthority": False,
        "allocatedBytesMeaning": "per-path observation, not exclusive reclaimable bytes",
    }


def main()->int:
    p=argparse.ArgumentParser();p.add_argument('command',choices=('materialize','status'));a=p.parse_args();print(json.dumps(materialize() if a.command=='materialize' else status(),indent=2,sort_keys=True));return 0
if __name__=='__main__': raise SystemExit(main())
