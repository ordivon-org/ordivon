#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path

ERROR_RE = re.compile(r"EXT4-fs error|JBD2.*(?:error|abort)|I/O error|checksum.*error|Remounting filesystem read-only", re.I)

def run(*args: str) -> str:
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    p = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return p.stdout

def d_states() -> int:
    count = 0
    for stat in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = stat.read_text(errors="replace").split()
            if len(fields) > 2 and fields[2] == "D":
                count += 1
        except (OSError, PermissionError):
            continue
    return count

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mount", default="/")
    ap.add_argument("--host-storage", default="/mnt/d")
    args = ap.parse_args()
    findmnt = run("/usr/bin/findmnt", "-n", "-T", args.mount, "-o", "SOURCE,FSTYPE,OPTIONS").strip()
    parts = findmnt.split(None, 2)
    if len(parts) != 3:
        raise RuntimeError("unexpected findmnt projection")
    source, fstype, options = parts
    tune = run("/usr/bin/tune2fs", "-l", source)
    state = None
    for line in tune.splitlines():
        if line.startswith("Filesystem state:"):
            state = line.split(":", 1)[1].strip()
            break
    if state is None:
        raise RuntimeError("filesystem state not found")
    try:
        dmesg = run("/usr/bin/dmesg", "--color=never")
        errors = [line for line in dmesg.splitlines() if ERROR_RE.search(line)][-20:]
        kernel_observable = True
    except subprocess.CalledProcessError:
        errors = []
        kernel_observable = False
    st = os.statvfs(args.host_storage)
    host_free = st.f_bavail * st.f_frsize
    rw = "rw" in options.split(",") and "ro" not in options.split(",")
    ds = d_states()
    if not rw or errors:
        standing = "SPARSE_INCIDENT"
    elif state.lower() != "clean" or not kernel_observable:
        standing = "INTEGRITY_UNKNOWN"
    elif ds:
        standing = "SPARSE_DEGRADED"
    else:
        standing = "SPARSE_HEALTHY"
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.wsl-sparse-guest-health",
        "observedAtMs": int(time.time() * 1000),
        "standing": standing,
        "guest": {
            "mount": args.mount, "source": source, "fstype": fstype, "options": options,
            "readWrite": rw, "filesystemState": state, "kernelErrorObservable": kernel_observable,
            "relevantKernelErrorCount": len(errors), "relevantKernelErrorTail": errors, "dStateCount": ds,
        },
        "hostProjection": {"path": args.host_storage, "freeBytes": host_free},
        "truthBoundary": "cheap guest filesystem/kernel/host-free observation only; Windows sparse allocation is a separate owner projection",
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if standing == "SPARSE_HEALTHY" else 2

if __name__ == "__main__":
    raise SystemExit(main())
